"""
Database models — SQLAlchemy ORM
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column, DateTime, Enum as SAEnum, Float, ForeignKey,
    Integer, String, Text, JSON, Boolean, create_engine,
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
    """Podcast generation task"""
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    """User preferences"""
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), default="default")
    preferred_voice = Column(String(100), default="冰糖")
    preferred_style = Column(String(50), default="narrative")
    preferred_mood = Column(String(50), default="neutral")
    tts_speed = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditLog(Base):
    """Credit transaction log"""
    __tablename__ = "credit_logs"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # positive = add, negative = use
    reason = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# Database engine and session
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database (create all tables)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        yield session
