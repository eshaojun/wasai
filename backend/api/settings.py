import json
import base64
import requests
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "data" / "settings.json"


class Settings(BaseModel):
    """设置模型"""
    # ASR 设置
    asr_provider: str = "openai"  # openai, local
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    whisper_model: str = "whisper-1"

    # 翻译设置
    translate_provider: str = "openai"  # openai, deepl
    deepl_api_key: Optional[str] = None
    translate_model: str = "gpt-4o-mini"

    # TTS 设置
    tts_provider: str = "openai"  # openai, azure, coqui, local
    azure_api_key: Optional[str] = None
    azure_region: Optional[str] = None
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    
    # 本地 TTS (Qwen3-TTS) 设置
    local_tts_base_url: Optional[str] = "http://localhost:8003"  # 本地TTS服务地址
    local_tts_speaker: str = "vivian"  # 默认说话人
    local_tts_language: str = "auto"  # 默认语言

    # 默认语言
    default_source_language: str = "zh"
    default_target_language: str = "en"


def load_settings() -> Settings:
    """加载设置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Settings(**data)
    return Settings()


def save_settings(settings: Settings):
    """保存设置"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)


@router.get("/")
def get_settings():
    """获取所有设置"""
    return load_settings()


@router.put("/")
def update_settings(settings: Settings):
    """更新设置"""
    save_settings(settings)
    return {"message": "设置已保存"}


@router.get("/asr")
def get_asr_settings():
    """获取 ASR 设置"""
    settings = load_settings()
    return {
        "provider": settings.asr_provider,
        "api_key": settings.openai_api_key,
        "base_url": settings.openai_base_url,
        "model": settings.whisper_model,
    }


@router.get("/translate")
def get_translate_settings():
    """获取翻译设置"""
    settings = load_settings()
    return {
        "provider": settings.translate_provider,
        "api_key": settings.deepl_api_key,
        "model": settings.translate_model,
    }


@router.get("/tts")
def get_tts_settings():
    """获取 TTS 设置"""
    settings = load_settings()
    return {
        "provider": settings.tts_provider,
        "azure_key": settings.azure_api_key,
        "azure_region": settings.azure_region,
        "model": settings.tts_model,
        "voice": settings.tts_voice,
        "local_base_url": settings.local_tts_base_url,
        "local_speaker": settings.local_tts_speaker,
        "local_language": settings.local_tts_language,
    }


class TTSTestRequest(BaseModel):
    """TTS 测试请求"""
    text: str = "你好，这是Qwen3-TTS的测试语音。"
    speaker: str = "vivian"
    language: str = "auto"
    base_url: str = "http://localhost:8003"


@router.post("/tts/test")
def test_tts_synthesis(request: TTSTestRequest):
    """
    测试本地 TTS 合成
    
    根据提供的参数调用本地 Qwen3-TTS 服务生成音频并返回文件流
    """
    # 构建本地TTS服务URL
    url = f"{request.base_url.rstrip('/')}/tts/custom-voice"
    
    # 语言映射
    language_mapping = {
        "zh": "Chinese",
        "en": "English",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "pt": "Portuguese",
        "ru": "Russian",
        "es": "Spanish",
        "auto": "Auto"
    }
    
    mapped_language = language_mapping.get(request.language, request.language.capitalize())
    
    # 构建请求体
    payload = {
        "text": request.text,
        "speaker": request.speaker.capitalize(),
        "language": mapped_language,
        "instruct": ""
    }
    
    try:
        # 调用本地TTS服务
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success") or not result.get("audio_base64"):
            raise HTTPException(status_code=500, detail=result.get("message", "TTS合成失败"))
        
        # 解码base64音频
        audio_data = base64.b64decode(result["audio_base64"])
        
        # 返回音频流
        from io import BytesIO
        audio_stream = BytesIO(audio_data)
        
        return StreamingResponse(
            audio_stream,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=tts_test_{request.speaker}.wav",
                "Content-Length": str(len(audio_data))
            }
        )
        
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"无法连接到本地TTS服务: {request.base_url}")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="TTS服务响应超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS合成失败: {str(e)}")
