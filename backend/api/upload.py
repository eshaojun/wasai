import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.project import Project, ProjectStatus

router = APIRouter()

# 上传目录
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/video/{project_id}")
async def upload_video(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传视频文件"""
    # 检查项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查文件类型
    allowed_types = ["video/mp4", "video/avi", "video/mov", "video/mkv", "video/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 创建项目专属目录
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(exist_ok=True)

    # 保存文件
    file_ext = Path(file.filename).suffix
    file_name = f"original{file_ext}"
    file_path = project_dir / file_name

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()

    # 更新项目信息
    project.original_video_path = str(file_path)
    project.status = ProjectStatus.UPLOADED
    db.commit()

    return {
        "message": "视频上传成功",
        "file_path": str(file_path),
        "file_name": file.filename,
    }


@router.get("/video/{project_id}")
async def get_video_info(project_id: int, db: Session = Depends(get_db)):
    """获取项目视频信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.original_video_path:
        return {"has_video": False}

    # 将文件系统路径转换为HTTP URL
    # 路径格式: uploads/project_1/original.mp4 -> /uploads/project_1/original.mp4
    try:
        video_path = Path(project.original_video_path)
        # 获取相对于uploads目录的相对路径
        relative_path = video_path.relative_to(UPLOAD_DIR.absolute())
        video_url = f"/uploads/{relative_path.as_posix()}"
    except ValueError:
        # 如果路径不在uploads目录下，使用原路径（兼容旧数据）
        video_url = None

    return {
        "has_video": True,
        "video_url": video_url,
        "video_path": project.original_video_path,
        "duration": project.duration,
        "width": project.width,
        "height": project.height,
        "fps": project.fps,
    }


@router.delete("/video/{project_id}")
async def delete_video(project_id: int, db: Session = Depends(get_db)):
    """删除项目视频"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if project.original_video_path and os.path.exists(project.original_video_path):
        os.remove(project.original_video_path)

    project.original_video_path = None
    project.status = ProjectStatus.DRAFT
    db.commit()

    return {"message": "视频已删除"}
