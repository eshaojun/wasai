import os
import tempfile
from pathlib import Path
from typing import Optional, List
import openai


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
        azure_region: Optional[str] = None
    ):
        self.provider = provider
        self.model = model
        self.voice = voice
        self.azure_key = azure_key
        self.azure_region = azure_region
        self.client = None

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

            output_path = output_dir / f"subtitle_{i:04d}.mp3"
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
        return []
