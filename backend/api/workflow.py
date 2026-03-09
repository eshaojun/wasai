import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.project import Project, Subtitle, ProjectStatus
from api.settings import load_settings
from services.asr import ASRService
from services.translate import TranslateService
from services.tts import TTSService
from services.video import VideoService

router = APIRouter()


class ASRRequest(BaseModel):
    language: str = "zh"


class TranslateRequest(BaseModel):
    texts: List[str]
    source_language: str = "zh"
    target_language: str = "en"


class TTSRequest(BaseModel):
    language: str = "en"


class ExportRequest(BaseModel):
    burn_subtitles: bool = True


@router.post("/{project_id}/asr")
def execute_asr(
    project_id: int,
    request: ASRRequest,
    db: Session = Depends(get_db)
):
    """执行语音识别"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.original_video_path or not os.path.exists(project.original_video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")

    # 加载设置
    settings = load_settings()

    # 提取音频
    video_service = VideoService()
    project_dir = Path(project.original_video_path).parent
    audio_path = project_dir / "audio.wav"

    try:
        video_service.extract_audio(project.original_video_path, str(audio_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频提取失败: {str(e)}")

    # 执行 ASR
    asr_service = ASRService(
        provider=settings.asr_provider,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.whisper_model
    )

    try:
        subtitles = asr_service.transcribe(str(audio_path), request.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")

    # 删除临时音频文件
    if audio_path.exists():
        audio_path.unlink()

    # 保存字幕到数据库
    # 删除旧字幕
    db.query(Subtitle).filter(Subtitle.project_id == project_id).delete()

    for i, sub_data in enumerate(subtitles):
        db_subtitle = Subtitle(
            project_id=project_id,
            start_time=sub_data.start_time,
            end_time=sub_data.end_time,
            original_text=sub_data.original_text,
            sequence=i
        )
        db.add(db_subtitle)

    # 更新项目状态
    project.status = ProjectStatus.ASR_DONE

    # 获取视频信息
    try:
        video_info = video_service.get_video_info(project.original_video_path)
        project.duration = video_info.get("duration")
        project.width = video_info.get("width")
        project.height = video_info.get("height")
        project.fps = video_info.get("fps")
    except Exception:
        pass

    db.commit()

    # 返回字幕
    db_subtitles = db.query(Subtitle).filter(Subtitle.project_id == project_id).order_by(Subtitle.sequence).all()

    return {
        "message": "语音识别完成",
        "subtitle_count": len(db_subtitles),
        "subtitles": [
            {
                "id": s.id,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "original_text": s.original_text,
                "translated_text": s.translated_text,
                "sequence": s.sequence
            }
            for s in db_subtitles
        ]
    }


@router.post("/{project_id}/translate")
def execute_translate(
    project_id: int,
    request: TranslateRequest,
    db: Session = Depends(get_db)
):
    """执行翻译"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 加载设置
    settings = load_settings()

    # 执行翻译
    translate_service = TranslateService(
        provider=settings.translate_provider,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.translate_model
    )

    try:
        translated_texts = translate_service.translate(
            request.texts,
            request.source_language,
            request.target_language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")

    # 更新项目状态
    project.status = ProjectStatus.TRANSLATED
    db.commit()

    return {
        "message": "翻译完成",
        "translated_texts": translated_texts
    }


@router.post("/{project_id}/tts")
def execute_tts(
    project_id: int,
    request: TTSRequest,
    db: Session = Depends(get_db)
):
    """执行语音合成"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取字幕
    subtitles = db.query(Subtitle).filter(Subtitle.project_id == project_id).order_by(Subtitle.sequence).all()
    if not subtitles:
        raise HTTPException(status_code=400, detail="没有字幕数据")

    # 加载设置
    settings = load_settings()

    # 创建音频目录
    project_dir = Path(project.original_video_path).parent if project.original_video_path else Path(f"uploads/project_{project_id}")
    audio_dir = project_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    # 执行 TTS
    tts_service = TTSService(
        provider=settings.tts_provider,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.tts_model,
        voice=settings.tts_voice
    )

    subtitle_dicts = [{"translated_text": s.translated_text} for s in subtitles]

    try:
        audio_paths = tts_service.synthesize_subtitles(
            subtitle_dicts,
            str(audio_dir),
            request.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")

    # 更新字幕的音频路径
    for i, subtitle in enumerate(subtitles):
        if audio_paths[i]:
            subtitle.audio_path = audio_paths[i]

    # 更新项目状态
    project.status = ProjectStatus.DUBBED
    db.commit()

    return {
        "message": "语音合成完成",
        "audio_count": len([p for p in audio_paths if p]),
        "audio_paths": audio_paths
    }


@router.post("/{project_id}/export")
def execute_export(
    project_id: int,
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """导出视频"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.original_video_path or not os.path.exists(project.original_video_path):
        raise HTTPException(status_code=400, detail="视频文件不存在")

    # 获取字幕
    subtitles = db.query(Subtitle).filter(Subtitle.project_id == project_id).order_by(Subtitle.sequence).all()

    # 创建输出目录
    project_dir = Path(project.original_video_path).parent
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "output.mp4"

    video_service = VideoService()

    # 如果有配音音频，合并音频和视频
    audio_paths = [s.audio_path for s in subtitles if s.audio_path and os.path.exists(s.audio_path)]
    subtitle_timings = [(s.start_time, s.end_time) for s in subtitles]

    if audio_paths:
        try:
            video_service.merge_audio_video(
                project.original_video_path,
                audio_paths,
                subtitle_timings,
                str(output_path)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"视频合成失败: {str(e)}")
    else:
        # 没有配音，复制原视频
        import shutil
        shutil.copy(project.original_video_path, output_path)

    # 如果需要烧录字幕
    final_output = output_path
    if request.burn_subtitles and subtitles:
        subtitle_data = [
            {
                "start_time": s.start_time,
                "end_time": s.end_time,
                "original_text": s.original_text,
                "translated_text": s.translated_text
            }
            for s in subtitles
        ]

        try:
            final_output = output_dir / "output_with_subtitles.mp4"
            video_service.add_subtitles_to_video(
                str(output_path),
                subtitle_data,
                str(final_output)
            )
        except Exception as e:
            # 烧录失败，使用未烧录的版本
            final_output = output_path

    # 更新项目状态
    project.status = ProjectStatus.EXPORTED
    project.output_video_path = str(final_output)
    db.commit()

    return {
        "message": "视频导出完成",
        "output_path": str(final_output),
        "burn_subtitles": request.burn_subtitles
    }
