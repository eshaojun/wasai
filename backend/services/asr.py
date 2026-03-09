import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
import openai


class ASRService:
    """语音识别服务"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "whisper-1"
    ):
        self.provider = provider
        self.model = model
        self.client = None

        if provider == "openai":
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url or "https://api.openai.com/v1"
            )

    def transcribe(self, audio_path: str, language: str = "zh") -> List[Dict[str, Any]]:
        """
        转录音频文件为字幕

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            字幕列表
        """
        if self.provider == "openai":
            return self._transcribe_openai(audio_path, language)
        else:
            raise NotImplementedError(f"不支持的 ASR 提供商: {self.provider}")

    def _transcribe_openai(self, audio_path: str, language: str) -> List[Dict[str, Any]]:
        """使用 OpenAI Whisper 进行转录"""
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        subtitles = []
        for i, segment in enumerate(transcript.segments):
            subtitle = {
                "project_id": 0,  # 由调用者设置
                "start_time": segment.start,
                "end_time": segment.end,
                "original_text": segment.text.strip(),
                "sequence": i
            }
            subtitles.append(subtitle)

        return subtitles

    def transcribe_with_word_timestamps(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> List[dict]:
        """
        转录音频，返回带词级时间戳的结果

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            包含词级时间戳的转录结果
        """
        if self.provider != "openai":
            raise NotImplementedError("词级时间戳仅支持 OpenAI Whisper")

        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"]
            )

        return [
            {
                "text": segment.text.strip(),
                "start": segment.start,
                "end": segment.end,
                "words": [
                    {"word": w.word, "start": w.start, "end": w.end}
                    for w in (getattr(segment, 'words', []) or [])
                ]
            }
            for segment in transcript.segments
        ]
