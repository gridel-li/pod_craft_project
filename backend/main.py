"""
PodCraft 后端服务入口

启动命令：
    uv run uvicorn main:app --reload --port 8000

本文件职责：
1. 配置全局日志格式与级别
2. 通过 lifespan 钩子在服务启动前创建数据库表，在服务关闭时输出日志
3. 注册 CORS 中间件，允许浏览器的跨域请求
4. 把本地 output 目录挂载为 /files 静态资源，使前端 <audio> 能直接播放生成的音频
5. 注册三组路由：任务/知识库、认证、管理员
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


# @asynccontextmanager 把一个含 yield 的异步函数转成异步上下文管理器。
# FastAPI 收到 lifespan 参数后，会在服务启动时执行 yield 之前的代码，
# 在服务关闭时执行 yield 之后的代码。
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表，关闭时记录日志"""
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

# CORS 决定哪些网页来源可以调用本 API。
# allow_origins=["*"] 只适合本地开发；生产环境必须改为前端实际域名，
# 否则任意网站都能带着用户凭证调用接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# StaticFiles 把磁盘上的 output 目录映射成 URL 前缀 /files。
# 例如 output/ab12cd34.wav 可以通过 http://localhost:8000/files/ab12cd34.wav 下载或播放。
os.makedirs(settings.output_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.output_dir), name="files")

# 注册路由，统一加 /api 前缀
app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root():
    """健康检查与文档入口提示"""
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
