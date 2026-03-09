import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter

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
    tts_provider: str = "openai"  # openai, azure, coqui
    azure_api_key: Optional[str] = None
    azure_region: Optional[str] = None
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"

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
    }
