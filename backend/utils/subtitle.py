"""
字幕格式转换工具
支持 SRT 和 ASS 格式的解析和生成
"""

import re
import chardet
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SubtitleEntry:
    """字幕条目"""
    start_time: float  # 秒
    end_time: float    # 秒
    text: str
    sequence: int = 0


def detect_encoding(content: bytes) -> str:
    """检测文件编码"""
    result = chardet.detect(content)
    encoding = result['encoding']
    confidence = result['confidence']

    # 处理 GBK/GB2312/GB18030 统一为 GB18030
    if encoding and encoding.upper() in ['GB2312', 'GBK', 'GB18030']:
        return 'GB18030'

    # 如果置信度低，默认使用 UTF-8
    if confidence and confidence < 0.7:
        return 'utf-8'

    return encoding or 'utf-8'


def remove_bom(content: bytes) -> bytes:
    """移除 BOM 头"""
    # UTF-8 BOM
    if content.startswith(b'\xef\xbb\xbf'):
        return content[3:]
    # UTF-16 LE BOM
    elif content.startswith(b'\xff\xfe'):
        return content[2:]
    # UTF-16 BE BOM
    elif content.startswith(b'\xfe\xff'):
        return content[2:]
    return content


def time_to_seconds(time_str: str) -> float:
    """将时间字符串转换为秒数"""
    # 支持格式: 00:00:00,000 或 00:00:00.000
    time_str = time_str.strip().replace(',', '.')
    parts = time_str.split(':')

    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    return float(time_str)


def seconds_to_time_srt(seconds: float) -> str:
    """将秒数转换为 SRT 时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def seconds_to_time_ass(seconds: float) -> str:
    """将秒数转换为 ASS 时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def parse_srt(content: str) -> List[SubtitleEntry]:
    """
    解析 SRT 格式字幕

    Args:
        content: SRT 文件内容

    Returns:
        字幕条目列表
    """
    entries = []

    # 规范化换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # SRT 格式: 序号\n起始时间 --> 结束时间\n文本\n\n
    # 使用正则匹配每个字幕块
    pattern = r'(\d+)\s*\n(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*\n(.*?)(?=\n\n\d+\s*\n|\n\n\s*$|$)'

    matches = re.finditer(pattern, content + '\n\n', re.DOTALL)

    for match in matches:
        try:
            sequence = int(match.group(1))
            start_time = time_to_seconds(match.group(2))
            end_time = time_to_seconds(match.group(3))
            text = match.group(4).strip()

            # 处理多行文本，移除多余的空行
            text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

            if text:  # 只添加非空字幕
                entries.append(SubtitleEntry(
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    sequence=sequence
                ))
        except Exception:
            # 跳过格式错误的条目
            continue

    # 如果没有匹配到，尝试宽松的解析
    if not entries:
        entries = _parse_srt_loose(content)

    # 按开始时间排序
    entries.sort(key=lambda x: x.start_time)

    # 重新编号
    for i, entry in enumerate(entries):
        entry.sequence = i

    return entries


def _parse_srt_loose(content: str) -> List[SubtitleEntry]:
    """宽松的 SRT 解析，处理不规范格式"""
    entries = []

    # 按空行分割
    blocks = re.split(r'\n\s*\n', content.strip())

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 2:
            continue

        # 尝试找到时间行
        time_line = None
        time_idx = -1

        for i, line in enumerate(lines):
            if '-->' in line and ':' in line:
                time_line = line
                time_idx = i
                break

        if not time_line:
            continue

        # 解析时间
        time_match = re.search(r'(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})', time_line)
        if not time_match:
            continue

        try:
            start_time = time_to_seconds(time_match.group(1))
            end_time = time_to_seconds(time_match.group(2))

            # 时间行之后的都是文本
            text_lines = lines[time_idx + 1:]
            text = '\n'.join(text_lines)

            if text:
                entries.append(SubtitleEntry(
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    sequence=len(entries)
                ))
        except Exception:
            continue

    return entries


def parse_ass(content: str) -> List[SubtitleEntry]:
    """
    解析 ASS 格式字幕

    Args:
        content: ASS 文件内容

    Returns:
        字幕条目列表
    """
    entries = []

    # 规范化换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # 找到 Events 部分
    events_match = re.search(r'\[Events\].*?\n(.*)', content, re.DOTALL)
    if not events_match:
        return entries

    events_section = events_match.group(1)

    # 解析 Format 行获取字段顺序
    format_match = re.search(r'Format:\s*(.+)', events_section)
    if not format_match:
        return entries

    format_fields = [f.strip() for f in format_match.group(1).split(',')]

    # 找到 Start 和 End 的索引
    try:
        start_idx = format_fields.index('Start')
        end_idx = format_fields.index('End')
        text_idx = format_fields.index('Text')
    except ValueError:
        return entries

    # 解析 Dialogue 行
    dialogue_pattern = r'Dialogue:\s*(.+)'

    for match in re.finditer(dialogue_pattern, events_section):
        try:
            fields = match.group(1).split(',', len(format_fields) - 1)

            if len(fields) <= text_idx:
                continue

            start_time = time_to_seconds(fields[start_idx])
            end_time = time_to_seconds(fields[end_idx])
            text = fields[text_idx].strip()

            # 移除 ASS 标签
            text = remove_ass_tags(text)

            # 处理 \N 换行符
            text = text.replace('\\N', '\n')

            if text:
                entries.append(SubtitleEntry(
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    sequence=len(entries)
                ))
        except Exception:
            continue

    # 按开始时间排序
    entries.sort(key=lambda x: x.start_time)

    # 重新编号
    for i, entry in enumerate(entries):
        entry.sequence = i

    return entries


def remove_ass_tags(text: str) -> str:
    """移除 ASS 格式标签"""
    # 移除 {\...} 标签
    text = re.sub(r'\{[^}]*\}', '', text)
    return text.strip()


def to_srt(entries: List[SubtitleEntry]) -> str:
    """
    生成 SRT 格式字幕

    Args:
        entries: 字幕条目列表

    Returns:
        SRT 格式字符串
    """
    lines = []

    for entry in entries:
        lines.append(str(entry.sequence + 1))
        lines.append(f"{seconds_to_time_srt(entry.start_time)} --> {seconds_to_time_srt(entry.end_time)}")
        lines.append(entry.text)
        lines.append('')

    return '\n'.join(lines)


def to_ass(entries: List[SubtitleEntry], title: str = "Generated Subtitles") -> str:
    """
    生成 ASS 格式字幕

    Args:
        entries: 字幕条目列表
        title: 字幕标题

    Returns:
        ASS 格式字符串
    """
    # ASS 头部
    header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]

    for entry in entries:
        start = seconds_to_time_ass(entry.start_time)
        end = seconds_to_time_ass(entry.end_time)
        # 转义特殊字符
        text = entry.text.replace('\n', '\\N')
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return '\n'.join(lines)


def parse_subtitle_file(file_content: bytes) -> Tuple[List[SubtitleEntry], str]:
    """
    自动检测并解析字幕文件

    Args:
        file_content: 文件字节内容

    Returns:
        (字幕条目列表, 检测到的格式)
    """
    # 移除 BOM
    content_bytes = remove_bom(file_content)

    # 检测编码
    encoding = detect_encoding(content_bytes)

    try:
        content = content_bytes.decode(encoding)
    except UnicodeDecodeError:
        # 如果解码失败，尝试 UTF-8
        content = content_bytes.decode('utf-8', errors='ignore')

    # 检测格式
    content_upper = content.upper()

    if '[Script Info]' in content or '[Events]' in content or 'Dialogue:' in content:
        # ASS 格式
        return parse_ass(content), 'ass'
    elif '-->' in content:
        # SRT 格式
        return parse_srt(content), 'srt'
    else:
        # 默认尝试 SRT
        return parse_srt(content), 'srt'


def entries_to_dicts(entries: List[SubtitleEntry]) -> List[Dict]:
    """转换为字典列表，用于 JSON 序列化"""
    return [
        {
            'sequence': e.sequence,
            'start_time': e.start_time,
            'end_time': e.end_time,
            'text': e.text
        }
        for e in entries
    ]


def dicts_to_entries(dicts: List[Dict]) -> List[SubtitleEntry]:
    """从字典列表转换为字幕条目"""
    return [
        SubtitleEntry(
            sequence=d.get('sequence', i),
            start_time=d.get('start_time', 0),
            end_time=d.get('end_time', 0),
            text=d.get('text', '')
        )
        for i, d in enumerate(dicts)
    ]
