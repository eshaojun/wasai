from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from models.project import ProjectStatus


# ===== 字幕相关 Schema =====

class SubtitleBase(BaseModel):
    start_time: float
    end_time: float
    original_text: str
    translated_text: Optional[str] = None
    audio_path: Optional[str] = None
    sequence: int = 0


class SubtitleCreate(SubtitleBase):
    project_id: int


class SubtitleUpdate(BaseModel):
    id: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None
    audio_path: Optional[str] = None
    sequence: Optional[int] = None


class SubtitleResponse(SubtitleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int


# ===== 项目相关 Schema =====

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_language: str = "zh"
    target_language: str = "en"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    status: Optional[ProjectStatus] = None
    original_video_path: Optional[str] = None
    output_video_path: Optional[str] = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_video_path: Optional[str] = None
    output_video_path: Optional[str] = None
    status: ProjectStatus
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    subtitles: List[SubtitleResponse] = []


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    source_language: str
    target_language: str
    duration: Optional[float] = None
    created_at: datetime
    updated_at: datetime
