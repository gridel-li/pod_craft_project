"""
Database models — SQLAlchemy ORM
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
    pass


class TaskStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


class PodcastTask(Base):
    """Podcast generation task。

    ORM 模型：类属性对应表列；一条 PodcastTask 实例对应 podcast_tasks 表中的一行。
    """
    __tablename__ = "podcast_tasks"

    id = Column(String(36), primary_key=True)
    topic = Column(String(500), nullable=False)
    mood = Column(String(50), default="neutral")
    style = Column(String(50), default="narrative")
    duration_min = Column(Integer, default=5)
    voice = Column(String(100), default="冰糖")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Float, default=0.0)
    current_step = Column(String(100), default="")

    # Results
    title = Column(String(200), default="")
    script_content = Column(Text, default="")
    audio_path = Column(String(500), default="")
    duration_sec = Column(Float, default=0.0)
    segments = Column(JSON, default=list)

    # Metadata
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class KnowledgeDocument(Base):
    """Knowledge base document"""
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(200), default="")
    doc_type = Column(String(50), default="text")
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserPreference(Base):
    """User preferences"""
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
    """Credit transaction log"""
    __tablename__ = "credit_logs"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # positive = add, negative = use
    reason = Column(String(200), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Engine 是到数据库的连接工厂；AsyncSession 是一次数据库工作单元（类似一次事务上下文）。
# 不要在模块里直接保存“全局 session”，应通过 get_db 为每个请求创建和释放 session。
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database (create all tables)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session；yield 后 FastAPI 会在请求结束时退出上下文并关闭会话。"""
    async with async_session() as session:
        yield session
