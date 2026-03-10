import json
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter()

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent / "data" / "settings.json"

# 预设翻译提示词模板
TRANSLATE_PROMPTS = {
    "standard": "你是一个专业的翻译助手，擅长将短剧对话翻译成自然流畅的目标语言。请保持原文的语气和情感色彩。",
    "colloquial": "你是一个专业的剧本翻译专家。请将以下台词翻译成自然、口语化的目标语言，符合演员的口吻和情感。避免直译，要意译。",
    "preserve_style": "你是一个翻译专家。请在保持原文风格、语气和情感的基础上，进行准确的翻译。"
}


class TranslateSettings(BaseModel):
    """翻译设置"""
    # 提供商类型: openai, custom
    provider: str = "custom"

    # 自定义接口配置
    custom_base_url: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_model: str = "gpt-4o-mini"

    # OpenAI官方配置（当provider=openai时使用）
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # 翻译提示词
    translate_prompt: str = TRANSLATE_PROMPTS["standard"]

    # 批量翻译设置
    translate_batch_size: int = 50


class Settings(BaseModel):
    """设置模型"""
    # ASR 设置
    asr_provider: str = "openai"  # openai, local
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    whisper_model: str = "whisper-1"

    # 翻译设置
    translate: TranslateSettings = TranslateSettings()

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

        # 兼容旧版本设置格式
        if "translate" not in data:
            # 从旧格式迁移
            data["translate"] = {
                "provider": data.get("translate_provider", "custom"),
                "custom_base_url": data.get("openai_base_url"),
                "custom_api_key": data.get("deepl_api_key"),
                "custom_model": data.get("translate_model", "gpt-4o-mini"),
                "openai_api_key": data.get("openai_api_key"),
                "openai_model": data.get("translate_model", "gpt-4o-mini"),
                "translate_prompt": TRANSLATE_PROMPTS["standard"],
                "translate_batch_size": data.get("translate_batch_size", 50)
            }

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
        "provider": settings.translate.provider,
        "custom_base_url": settings.translate.custom_base_url,
        "custom_api_key": settings.translate.custom_api_key,
        "custom_model": settings.translate.custom_model,
        "openai_api_key": settings.translate.openai_api_key,
        "openai_model": settings.translate.openai_model,
        "translate_prompt": settings.translate.translate_prompt,
        "translate_batch_size": settings.translate.translate_batch_size,
    }


@router.get("/translate/prompts")
def get_translate_prompts():
    """获取预设翻译提示词模板"""
    return TRANSLATE_PROMPTS


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
