"""
PodCraft — AI Podcast Generator

Start: uv run uvicorn main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from models.database import init_db
from api.routes import router
from api.auth import router as auth_router
from api.admin import router as admin_router


logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 学习提示：lifespan 是 FastAPI 的“应用启动/关闭钩子”。
# yield 之前在服务开始接收请求前执行，yield 之后在服务停止时执行。

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Podcast Generator — from topic to full podcast audio",
    lifespan=lifespan,
)

# CORS 决定哪些网页来源可以调用本 API。开发阶段的 * 很方便；生产必须改为前端域名白名单。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# StaticFiles 把本地 output 目录映射为 /files URL，浏览器才可以用 <audio src="/files/..."></audio> 播放文件。
os.makedirs(settings.output_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.output_dir), name="files")

# Routes
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
