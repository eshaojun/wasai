import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from api import api_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="wasai API",
        description="短剧出海剪辑工具后端 API",
        version="0.1.0",
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 初始化数据库
    init_db()

    # 注册路由
    app.include_router(api_router, prefix="/api/v1")

    # 静态文件服务（上传的视频）
    upload_dir = Path(__file__).parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

    @app.get("/")
    def root():
        return {"message": "wasai API 服务运行中", "version": "0.1.0"}

    @app.get("/health")
    def health_check():
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
