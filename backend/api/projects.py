from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.project import Project, Subtitle, ProjectStatus
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    SubtitleCreate,
    SubtitleUpdate,
    SubtitleResponse,
)

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectListResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取项目列表"""
    projects = db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    for field, value in project_update.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}


# ===== 字幕相关接口 =====

@router.post("/{project_id}/subtitles", response_model=SubtitleResponse)
def create_subtitle(project_id: int, subtitle: SubtitleCreate, db: Session = Depends(get_db)):
    """添加字幕"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    db_subtitle = Subtitle(**subtitle.model_dump())
    db.add(db_subtitle)
    db.commit()
    db.refresh(db_subtitle)
    return db_subtitle


@router.get("/{project_id}/subtitles", response_model=List[SubtitleResponse])
def list_subtitles(project_id: int, db: Session = Depends(get_db)):
    """获取项目字幕列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    subtitles = db.query(Subtitle).filter(Subtitle.project_id == project_id).order_by(Subtitle.sequence).all()
    return subtitles


@router.put("/{project_id}/subtitles/{subtitle_id}", response_model=SubtitleResponse)
def update_subtitle(
    project_id: int,
    subtitle_id: int,
    subtitle_update: SubtitleUpdate,
    db: Session = Depends(get_db)
):
    """更新字幕"""
    subtitle = db.query(Subtitle).filter(
        Subtitle.id == subtitle_id,
        Subtitle.project_id == project_id
    ).first()

    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")

    for field, value in subtitle_update.model_dump(exclude_unset=True).items():
        setattr(subtitle, field, value)

    db.commit()
    db.refresh(subtitle)
    return subtitle


@router.delete("/{project_id}/subtitles/{subtitle_id}")
def delete_subtitle(project_id: int, subtitle_id: int, db: Session = Depends(get_db)):
    """删除字幕"""
    subtitle = db.query(Subtitle).filter(
        Subtitle.id == subtitle_id,
        Subtitle.project_id == project_id
    ).first()

    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")

    db.delete(subtitle)
    db.commit()
    return {"message": "字幕已删除"}


@router.post("/{project_id}/batch-update-subtitles")
def batch_update_subtitles(
    project_id: int,
    subtitles: List[SubtitleUpdate],
    db: Session = Depends(get_db)
):
    """批量更新字幕"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取现有字幕
    existing = db.query(Subtitle).filter(Subtitle.project_id == project_id).all()
    existing_map = {s.id: s for s in existing}

    updated = []
    for sub_data in subtitles:
        if sub_data.id and sub_data.id in existing_map:
            sub = existing_map[sub_data.id]
            for field, value in sub_data.model_dump(exclude_unset=True, exclude={"id"}).items():
                setattr(sub, field, value)
            updated.append(sub)

    db.commit()
    return {"message": f"已更新 {len(updated)} 条字幕"}
