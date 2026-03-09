import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship

from database import Base


class ProjectStatus(str, enum.Enum):
    """项目状态"""
    DRAFT = "draft"           # 草稿
    UPLOADED = "uploaded"     # 已上传
    ASR_DONE = "asr_done"     # 语音识别完成
    TRANSLATED = "translated" # 翻译完成
    DUBBED = "dubbed"         # 配音完成
    EXPORTED = "exported"     # 导出完成


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_video_path = Column(String(500), nullable=True)
    output_video_path = Column(String(500), nullable=True)
    source_language = Column(String(10), default="zh")
    target_language = Column(String(10), default="en")
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)

    # 视频信息
    duration = Column(Float, nullable=True)  # 视频时长（秒）
    width = Column(Integer, nullable=True)   # 视频宽度
    height = Column(Integer, nullable=True)  # 视频高度
    fps = Column(Float, nullable=True)       # 帧率

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联字幕
    subtitles = relationship("Subtitle", back_populates="project", cascade="all, delete-orphan")


class Subtitle(Base):
    """字幕模型"""
    __tablename__ = "subtitles"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # 时间信息
    start_time = Column(Float, nullable=False)  # 开始时间（秒）
    end_time = Column(Float, nullable=False)    # 结束时间（秒）

    # 文本内容
    original_text = Column(Text, nullable=False)    # 原文
    translated_text = Column(Text, nullable=True)   # 译文

    # 音频
    audio_path = Column(String(500), nullable=True)  # TTS 生成的音频路径

    # 排序
    sequence = Column(Integer, default=0)

    # 关联项目
    project = relationship("Project", back_populates="subtitles")
