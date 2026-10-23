"""
Database Models — SQLAlchemy ORM 数据模型与异步数据库连接

包含：
1. TaskStatus: 任务状态枚举类
2. PodcastTask: 播客任务数据表模型
3. KnowledgeDocument: 知识库文档元数据表模型
4. UserPreference: 用户偏好配置表模型
5. CreditLog: 积分变动流水表模型
6. init_db / get_db: 数据库表结构初始化与 FastAPI 依赖注入会话生成器
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column, DateTime, Enum as SAEnum, Float, ForeignKey,
    Integer, String, Text, JSON,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    """SQLAlchemy 声明式映射基类"""
    pass


class TaskStatus(str, Enum):
    """播客生成任务的状态枚举"""
    PENDING = "pending"          # 任务已创建，等待调度
    ANALYZING = "analyzing"      # 正在执行情绪与策略分析
    PLANNING = "planning"        # 正在规划大纲结构
    GENERATING = "generating"    # 正在撰写台词脚本
    REVIEWING = "reviewing"      # 正在进行质量审查
    SYNTHESIZING = "synthesizing"# 正在进行 TTS 语音合成与混音
    COMPLETED = "completed"      # 任务已全部完成
    FAILED = "failed"            # 任务执行中发生异常失败


class PodcastTask(Base):
    """播客生成任务表 (podcast_tasks)"""
    __tablename__ = "podcast_tasks"

    id = Column(String(36), primary_key=True)
    topic = Column(String(500), nullable=False)   # 播客主题
    mood = Column(String(50), default="neutral")  # 期望情绪
    style = Column(String(50), default="narrative")# 叙事风格
    duration_min = Column(Integer, default=5)     # 时长（分钟）
    voice = Column(String(100), default="冰糖")   # TTS 音色
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True) # 关联用户 ID

    # 状态与进度
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Float, default=0.0)         # 进度百分比 (0.0 ~ 100.0)
    current_step = Column(String(100), default="")# 当前步骤描述

    # 输出结果
    title = Column(String(200), default="")
    script_content = Column(Text, default="")
    audio_path = Column(String(500), default="")
    duration_sec = Column(Float, default=0.0)
    segments = Column(JSON, default=list)         # 结构化分段列表存储为 JSON

    # 时间与错误日志
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class KnowledgeDocument(Base):
    """知识库文档元数据表 (knowledge_documents)"""
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False)   # 文档标题
    content = Column(Text, nullable=False)        # 原始内容
    source = Column(String(200), default="")      # 来源
    doc_type = Column(String(50), default="text") # 类型 (text, pdf)
    chunk_count = Column(Integer, default=0)      # 切块数量
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserPreference(Base):
    """用户个性化偏好表 (user_preferences)"""
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), default="default")
    preferred_voice = Column(String(100), default="冰糖")
    preferred_style = Column(String(50), default="narrative")
    preferred_mood = Column(String(50), default="neutral")
    tts_speed = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CreditLog(Base):
    """积分流水记录表 (credit_logs)"""
    __tablename__ = "credit_logs"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)      # 正数为增加，负数为扣减
    reason = Column(String(200), default="")      # 变动原因
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# 创建异步数据库引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# 异步会话工厂
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """初始化数据库架构，创建所有未就绪的数据表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI 依赖注入函数：生成异步会话并在请求处理完毕后自动关闭"""
    async with async_session() as session:
        yield session
