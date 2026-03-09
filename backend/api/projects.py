from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.project import Project, Subtitle, ProjectStatus
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    SubtitleCreate,
    SubtitleUpdate,
    SubtitleResponse,
)

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectListResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取项目列表"""
    projects = db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    for field, value in project_update.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}


# ===== 字幕相关接口 =====

@router.post("/{project_id}/subtitles", response_model=SubtitleResponse)
def create_subtitle(project_id: int, subtitle: SubtitleCreate, db: Session = Depends(get_db)):
    """添加字幕"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db_subtitle = Subtitle(**subtitle.model_dump())
    db.add(db_subtitle)
    db.commit()
    db.refresh(db_subtitle)
    return db_subtitle


@router.get("/{project_id}/subtitles", response_model=List[SubtitleResponse])
def list_subtitles(project_id: int, db: Session = Depends(get_db)):
    """获取项目字幕列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    subtitles = db.query(Subtitle).filter(Subtitle.project_id == project_id).order_by(Subtitle.sequence).all()
    return subtitles


@router.put("/{project_id}/subtitles/{subtitle_id}", response_model=SubtitleResponse)
def update_subtitle(
    project_id: int,
    subtitle_id: int,
    subtitle_update: SubtitleUpdate,
    db: Session = Depends(get_db)
):
    """更新字幕"""
    subtitle = db.query(Subtitle).filter(
        Subtitle.id == subtitle_id,
        Subtitle.project_id == project_id
    ).first()

    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")

    for field, value in subtitle_update.model_dump(exclude_unset=True).items():
        setattr(subtitle, field, value)

    db.commit()
    db.refresh(subtitle)
    return subtitle


@router.delete("/{project_id}/subtitles/{subtitle_id}")
def delete_subtitle(project_id: int, subtitle_id: int, db: Session = Depends(get_db)):
    """删除字幕"""
    subtitle = db.query(Subtitle).filter(
        Subtitle.id == subtitle_id,
        Subtitle.project_id == project_id
    ).first()

    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")

    db.delete(subtitle)
    db.commit()
    return {"message": "字幕已删除"}


@router.post("/{project_id}/batch-update-subtitles")
def batch_update_subtitles(
    project_id: int,
    subtitles: List[SubtitleUpdate],
    db: Session = Depends(get_db)
):
    """批量更新字幕"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取现有字幕
    existing = db.query(Subtitle).filter(Subtitle.project_id == project_id).all()
    existing_map = {s.id: s for s in existing}

    updated = []
    for sub_data in subtitles:
        if sub_data.id and sub_data.id in existing_map:
            sub = existing_map[sub_data.id]
            for field, value in sub_data.model_dump(exclude_unset=True, exclude={"id"}).items():
                setattr(sub, field, value)
            updated.append(sub)

    db.commit()
    return {"message": f"已更新 {len(updated)} 条字幕"}


# ===== 字幕导入导出接口 =====

from fastapi import UploadFile, File, Query
from fastapi.responses import PlainTextResponse
from utils.subtitle import (
    parse_subtitle_file,
    to_srt,
    to_ass,
    entries_to_dicts,
    SubtitleEntry
)


@router.post("/{project_id}/subtitles/preview-import")
async def preview_import_subtitles(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """预览导入字幕文件（不保存）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查文件类型
    filename = file.filename or ""
    allowed_extensions = ['.srt', '.ass', '.ssa', '.txt']
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 SRT 或 ASS 文件")

    try:
        # 读取文件内容
        content = await file.read()

        # 解析字幕
        entries, format_type = parse_subtitle_file(content)

        if not entries:
            raise HTTPException(status_code=400, detail="未能解析出有效字幕，请检查文件格式")

        # 转换为字典
        subtitles_preview = [
            {
                "sequence": e.sequence,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "original_text": e.text if project.source_language == 'zh' else "",
                "translated_text": e.text if project.target_language != 'zh' else ""
            }
            for e in entries
        ]

        return {
            "message": f"成功解析 {len(subtitles_preview)} 条字幕",
            "format": format_type,
            "filename": filename,
            "subtitles": subtitles_preview
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析字幕失败: {str(e)}")


@router.post("/{project_id}/subtitles/import")
def import_subtitles(
    project_id: int,
    subtitles: List[SubtitleUpdate],
    mode: str = Query("replace", description="导入模式: replace=替换, append=追加"),
    db: Session = Depends(get_db)
):
    """确认导入字幕"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    try:
        if mode == "replace":
            # 删除现有字幕
            db.query(Subtitle).filter(Subtitle.project_id == project_id).delete()
            db.flush()

            # 添加新字幕
            for sub_data in subtitles:
                db_subtitle = Subtitle(
                    project_id=project_id,
                    start_time=sub_data.start_time or 0,
                    end_time=sub_data.end_time or 0,
                    original_text=sub_data.original_text or "",
                    translated_text=sub_data.translated_text or "",
                    sequence=sub_data.sequence or 0
                )
                db.add(db_subtitle)

        elif mode == "append":
            # 获取当前最大序号
            max_sequence = db.query(Subtitle).filter(
                Subtitle.project_id == project_id
            ).count()

            # 追加新字幕
            for i, sub_data in enumerate(subtitles):
                db_subtitle = Subtitle(
                    project_id=project_id,
                    start_time=sub_data.start_time or 0,
                    end_time=sub_data.end_time or 0,
                    original_text=sub_data.original_text or "",
                    translated_text=sub_data.translated_text or "",
                    sequence=max_sequence + i
                )
                db.add(db_subtitle)

        db.commit()

        # 更新项目状态
        if project.status == ProjectStatus.UPLOADED:
            project.status = ProjectStatus.ASR_DONE
            db.commit()

        return {"message": f"成功导入 {len(subtitles)} 条字幕"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入字幕失败: {str(e)}")


@router.get("/{project_id}/subtitles/export")
def export_subtitles(
    project_id: int,
    format: str = Query("srt", description="导出格式: srt 或 ass"),
    db: Session = Depends(get_db)
):
    """导出字幕文件"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取字幕
    subtitles = db.query(Subtitle).filter(
        Subtitle.project_id == project_id
    ).order_by(Subtitle.sequence).all()

    if not subtitles:
        raise HTTPException(status_code=400, detail="项目没有字幕数据")

    try:
        # 转换为字幕条目
        entries = [
            SubtitleEntry(
                sequence=s.sequence,
                start_time=s.start_time,
                end_time=s.end_time,
                text=s.translated_text or s.original_text or ""
            )
            for s in subtitles
        ]

        if format.lower() == "ass":
            content = to_ass(entries, project.name)
            filename = f"{project.name}.ass"
        else:
            content = to_srt(entries)
            filename = f"{project.name}.srt"

        # 使用 UTF-8 编码
        return PlainTextResponse(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出字幕失败: {str(e)}")
