from fastapi import APIRouter

from .projects import router as projects_router
from .upload import router as upload_router
from .settings import router as settings_router
from .workflow import router as workflow_router

api_router = APIRouter()
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(workflow_router, prefix="/projects", tags=["workflow"])
