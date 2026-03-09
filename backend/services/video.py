import os
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Tuple


class VideoService:
    """视频处理服务"""

    def __init__(self):
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"

    def get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        info = {
            "width": None,
            "height": None,
            "fps": None,
            "duration": None
        }

        if "streams" in data and data["streams"]:
            stream = data["streams"][0]
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")

            # 解析帧率
            fps_str = stream.get("r_frame_rate", "0/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                info["fps"] = float(num) / float(den) if float(den) != 0 else None

            # 尝试从流获取时长
            info["duration"] = stream.get("duration")

        # 从 format 获取时长
        if "format" in data and data["format"]:
            format_duration = data["format"].get("duration")
            if format_duration:
                info["duration"] = float(format_duration)

        return info

    def extract_audio(self, video_path: str, output_path: str) -> str:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径

        Returns:
            输出文件路径
        """
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vn",  # 禁用视频
            "-acodec", "pcm_s16le",  # PCM 16bit 小端
            "-ar", "16000",  # 采样率 16kHz
            "-ac", "1",  # 单声道
            "-y",  # 覆盖输出文件
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def merge_audio_video(
        self,
        video_path: str,
        audio_paths: List[str],
        subtitle_timings: List[Tuple[float, float]],
        output_path: str
    ) -> str:
        """
        合并视频和多个音频片段

        Args:
            video_path: 原始视频路径
            audio_paths: 音频文件路径列表（可能包含 None）
            subtitle_timings: 每个音频对应的 (开始时间, 结束时间) 列表
            output_path: 输出视频路径

        Returns:
            输出文件路径
        """
        # 创建临时目录
        temp_dir = Path(output_path).parent / "temp_merge"
        temp_dir.mkdir(exist_ok=True)

        # 构建滤镜复杂字符串
        filter_parts = []
        inputs = []

        # 视频输入
        inputs.extend(["-i", video_path])

        # 音频输入和延迟处理
        audio_inputs = []
        for i, (audio_path, (start, end)) in enumerate(zip(audio_paths, subtitle_timings)):
            if audio_path and os.path.exists(audio_path):
                inputs.extend(["-i", audio_path])
                audio_idx = i + 1
                # 延迟音频到指定位置
                delay_ms = int(start * 1000)
                filter_parts.append(
                    f"[{audio_idx}:a]adelay={delay_ms}|{delay_ms}[a{i}]"
                )
                audio_inputs.append(f"[a{i}]")

        if not audio_inputs:
            # 没有音频要合并，直接复制视频
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-c", "copy",
                "-y",
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path

        # 混音
        mix_inputs = "".join(audio_inputs)
        filter_parts.append(
            f"{mix_inputs}amix=inputs={len(audio_inputs)}:duration=longest[aout]"
        )

        filter_complex = ";".join(filter_parts)

        cmd = [
            self.ffmpeg_path,
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "0:v",  # 使用原始视频
            "-map", "[aout]",  # 使用混音后的音频
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # 清理临时文件
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        return output_path

    def add_subtitles_to_video(
        self,
        video_path: str,
        subtitles: List[dict],
        output_path: str,
        font_size: int = 24,
        font_color: str = "white",
        outline_color: str = "black",
        outline_width: int = 2
    ) -> str:
        """
        将字幕烧录到视频中

        Args:
            video_path: 视频路径
            subtitles: 字幕列表
            output_path: 输出路径
            font_size: 字体大小
            font_color: 字体颜色
            outline_color: 描边颜色
            outline_width: 描边宽度

        Returns:
            输出文件路径
        """
        # 创建 ASS 字幕文件
        ass_path = Path(output_path).with_suffix(".ass")
        self._create_ass_subtitle(
            subtitles, str(ass_path),
            font_size, font_color, outline_color, outline_width
        )

        # 使用 ffmpeg 烧录字幕
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vf", f"ass={ass_path}",
            "-c:a", "copy",
            "-y",
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # 删除临时字幕文件
        if ass_path.exists():
            ass_path.unlink()

        return output_path

    def _create_ass_subtitle(
        self,
        subtitles: List[dict],
        output_path: str,
        font_size: int = 24,
        font_color: str = "white",
        outline_color: str = "black",
        outline_width: int = 2
    ):
        """创建 ASS 格式字幕文件"""
        # ASS 头部
        header = f"""[Script Info]
Title: wasai Generated Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H{self._color_to_ass(outline_color)},&H00000000,0,0,0,0,100,100,0,0,1,{outline_width},0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # 转换字幕
        lines = [header]
        for sub in subtitles:
            start = self._seconds_to_ass_time(sub["start_time"])
            end = self._seconds_to_ass_time(sub["end_time"])
            text = sub.get("translated_text", sub.get("original_text", ""))
            # 处理多行
            text = text.replace("\n", "\\N")
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """将秒数转换为 ASS 时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _color_to_ass(self, color: str) -> str:
        """将颜色名称转换为 ASS 格式"""
        colors = {
            "white": "FFFFFF",
            "black": "000000",
            "red": "FF0000",
            "green": "00FF00",
            "blue": "0000FF",
            "yellow": "FFFF00",
        }
        return colors.get(color.lower(), "FFFFFF")

    def merge_videos(self, video_paths: List[str], output_path: str) -> str:
        """
        合并多个视频

        Args:
            video_paths: 视频路径列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        # 创建文件列表
        temp_list = Path(output_path).parent / "temp_concat_list.txt"
        with open(temp_list, "w", encoding="utf-8") as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")

        # 使用 concat demuxer
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", str(temp_list),
            "-c", "copy",
            "-y",
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # 清理
        temp_list.unlink()

        return output_path
