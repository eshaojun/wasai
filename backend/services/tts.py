import os
import tempfile
import base64
from pathlib import Path
from typing import Optional, List
import openai
import requests


class TTSService:
    """文本转语音服务"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "tts-1",
        voice: str = "alloy",
        azure_key: Optional[str] = None,
        azure_region: Optional[str] = None,
        local_base_url: Optional[str] = "http://localhost:8003",
        local_speaker: str = "vivian",
        local_language: str = "auto"
    ):
        self.provider = provider
        self.model = model
        self.voice = voice
        self.azure_key = azure_key
        self.azure_region = azure_region
        self.client = None
        
        # 本地TTS设置
        self.local_base_url = local_base_url
        self.local_speaker = local_speaker
        self.local_language = local_language

        if provider == "openai":
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url or "https://api.openai.com/v1"
            )

    def synthesize(self, text: str, output_path: str, language: str = "en") -> str:
        """
        合成语音

        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            language: 语言代码

        Returns:
            输出文件路径
        """
        if self.provider == "openai":
            return self._synthesize_openai(text, output_path)
        elif self.provider == "local":
            return self._synthesize_local(text, output_path, language)
        else:
            raise NotImplementedError(f"不支持的 TTS 提供商: {self.provider}")

    def _synthesize_openai(self, text: str, output_path: str) -> str:
        """使用 OpenAI TTS 合成语音"""
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text
        )

        response.stream_to_file(output_path)
        return output_path

    def _synthesize_local(self, text: str, output_path: str, language: str = None) -> str:
        """使用本地 Qwen3-TTS 合成语音"""
        # 调用本地TTS服务
        url = f"{self.local_base_url}/tts/custom-voice"
        
        # 使用传入的语言或默认语言
        tts_language = language or self.local_language
        # 将语言代码映射为Qwen3-TTS支持的语言格式
        language_mapping = {
            "zh": "chinese",
            "en": "english",
            "fr": "french",
            "de": "german",
            "it": "italian",
            "ja": "japanese",
            "ko": "korean",
            "pt": "portuguese",
            "ru": "russian",
            "es": "spanish",
            "auto": "auto"
        }
        mapped_language = language_mapping.get(tts_language, tts_language)
        
        payload = {
            "text": text,
            "speaker": self.local_speaker.capitalize(),
            "language": mapped_language.capitalize() if mapped_language != "auto" else "Auto",
            "instruct": ""
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success") and result.get("audio_base64"):
                # 解码base64音频并保存
                audio_data = base64.b64decode(result["audio_base64"])
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                return output_path
            else:
                raise Exception(f"TTS合成失败: {result.get('message', '未知错误')}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"无法连接到本地TTS服务，请确保服务在 {self.local_base_url} 运行")
        except Exception as e:
            raise Exception(f"本地TTS合成失败: {str(e)}")

    def synthesize_subtitles(
        self,
        subtitles: List[dict],
        output_dir: str,
        language: str = "en"
    ) -> List[str]:
        """
        批量合成字幕音频

        Args:
            subtitles: 字幕列表，每项包含 translated_text
            output_dir: 输出目录
            language: 语言代码

        Returns:
            音频文件路径列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_paths = []
        for i, subtitle in enumerate(subtitles):
            text = subtitle.get("translated_text", "")
            if not text:
                audio_paths.append(None)
                continue

            output_path = output_dir / f"subtitle_{i:04d}.wav"
            try:
                self.synthesize(text, str(output_path), language)
                audio_paths.append(str(output_path))
            except Exception as e:
                print(f"合成第 {i} 条字幕失败: {e}")
                audio_paths.append(None)

        return audio_paths

    def get_available_voices(self) -> List[dict]:
        """获取可用的语音列表"""
        if self.provider == "openai":
            # OpenAI TTS 支持的语音
            return [
                {"id": "alloy", "name": "Alloy", "description": "中性声音"},
                {"id": "echo", "name": "Echo", "description": "男性声音"},
                {"id": "fable", "name": "Fable", "description": "男性声音"},
                {"id": "onyx", "name": "Onyx", "description": "男性声音"},
                {"id": "nova", "name": "Nova", "description": "女性声音"},
                {"id": "shimmer", "name": "Shimmer", "description": "女性声音"},
            ]
        elif self.provider == "local":
            # Qwen3-TTS 支持的说话人
            return [
                {"id": "aiden", "name": "Aiden", "description": "阳光美式男声，中音清晰（英文）"},
                {"id": "dylan", "name": "Dylan", "description": "年轻北京男声，音色清晰自然（中文北京方言）"},
                {"id": "eric", "name": "Eric", "description": "活泼成都男声，略带沙哑的明亮感（中文四川方言）"},
                {"id": "ono_anna", "name": "Ono Anna", "description": "俏皮日本女声，音色轻快灵动（日语）"},
                {"id": "ryan", "name": "Ryan", "description": "富有节奏感的动感男声（英文）"},
                {"id": "serena", "name": "Serena", "description": "温暖、温柔的年轻女声（中文）"},
                {"id": "sohee", "name": "Sohee", "description": "温暖韩语女声，情感丰富（韩语）"},
                {"id": "uncle_fu", "name": "Uncle Fu", "description": "经验丰富、低沉醇厚的男声（中文）"},
                {"id": "vivian", "name": "Vivian", "description": "明亮、略带尖锐的年轻女声（中文）"},
            ]
        return []

    def get_supported_languages(self) -> List[dict]:
        """获取支持的语言列表（仅本地TTS）"""
        if self.provider == "local":
            return [
                {"id": "auto", "name": "自动检测", "description": "自动识别文本语言"},
                {"id": "zh", "name": "中文", "description": "Chinese"},
                {"id": "en", "name": "英文", "description": "English"},
                {"id": "fr", "name": "法语", "description": "French"},
                {"id": "de", "name": "德语", "description": "German"},
                {"id": "it", "name": "意大利语", "description": "Italian"},
                {"id": "ja", "name": "日语", "description": "Japanese"},
                {"id": "ko", "name": "韩语", "description": "Korean"},
                {"id": "pt", "name": "葡萄牙语", "description": "Portuguese"},
                {"id": "ru", "name": "俄语", "description": "Russian"},
                {"id": "es", "name": "西班牙语", "description": "Spanish"},
            ]
        return []

    def get_local_model_info(self) -> dict:
        """获取本地TTS模型信息"""
        if self.provider != "local":
            return None
        
        try:
            url = f"{self.local_base_url}/model/info"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取本地模型信息失败: {e}")
            return None
