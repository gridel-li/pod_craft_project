"""
API routes — PodCraft RESTful endpoints
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db, PodcastTask, KnowledgeDocument, TaskStatus, async_session
from models.schemas import (
    GenerateRequest, TaskResponse, TaskListResponse,
    DocumentUploadRequest, DocumentResponse, SearchResponse,
    HealthResponse, SegmentResponse,
)
from models.user import User, decode_access_token
from workflow.orchestrator import WorkflowOrchestrator
from rag.service import RAGService
from services.tts_client import TTSClient
from services.credit_service import use_credits
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
orchestrator = WorkflowOrchestrator()
rag_service = RAGService()


# ============================================================
# Optional auth dependency
# ============================================================

async def get_optional_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Try to extract user from token; return None if not logged in."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ============================================================
# Health check
# ============================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        database="connected",
        llm="configured" if settings.llm_api_key else "not configured",
        tts="configured" if settings.tts_api_key or settings.llm_api_key else "not configured",
    )


# ============================================================
# Podcast generation
# ============================================================

@router.post("/podcasts/generate", response_model=TaskResponse)
async def generate_podcast(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Create a podcast generation task"""
    task_id = uuid.uuid4().hex[:8]

    # If user is logged in, deduct 1 credit
    if user:
        success = await use_credits(db, user.id, amount=1, reason=f"Generate: {request.topic[:50]}")
        if not success:
            raise HTTPException(status_code=402, detail="积分不足，请充值")

    task = PodcastTask(
        id=task_id,
        topic=request.topic,
        mood=request.mood,
        style=request.style,
        duration_min=request.duration_min,
        voice=request.voice,
        user_id=user.id if user else None,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.commit()

    background_tasks.add_task(
        _run_generation, task_id, request
    )

    return _task_to_response(task)


async def _run_generation(task_id: str, request: GenerateRequest):
    """Run podcast generation in the background"""
    async with async_session() as session:
        try:
            # Update status
            task = await session.get(PodcastTask, task_id)
            task.status = TaskStatus.ANALYZING
            task.current_step = "分析心情..."
            await session.commit()

            # Execute Workflow
            result = await orchestrator.execute(
                topic=request.topic,
                mood=request.mood,
                style=request.style,
                duration_min=request.duration_min,
                voice=request.voice,
                use_rag=request.use_rag,
                custom_prompt=request.custom_prompt,
                progress_callback=lambda step, status, p: _update_progress(session, task_id, step, status, p),
            )

            # Update results
            task = await session.get(PodcastTask, task_id)
            if result["success"]:
                task.status = TaskStatus.COMPLETED
                task.title = result["title"]
                task.segments = result["segments"]
                task.audio_path = result["audio_path"]
                task.duration_sec = result["duration_sec"]
                task.progress = 100.0
                task.completed_at = datetime.utcnow()
            else:
                task.status = TaskStatus.FAILED
                task.error_message = result.get("error", "未知错误")

            task.current_step = ""
            await session.commit()

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            task = await session.get(PodcastTask, task_id)
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await session.commit()


async def _update_progress(session, task_id: str, step: str, status: str, progress: int):
    """Update task progress"""
    try:
        task = await session.get(PodcastTask, task_id)
        if task:
            task.progress = float(progress)
            task.current_step = step
            status_map = {
                "rag": TaskStatus.ANALYZING,
                "mood_analysis": TaskStatus.ANALYZING,
                "planning": TaskStatus.PLANNING,
                "writing": TaskStatus.GENERATING,
                "reviewing": TaskStatus.REVIEWING,
                "synthesizing": TaskStatus.SYNTHESIZING,
                "merging": TaskStatus.SYNTHESIZING,
            }
            task.status = status_map.get(step, task.status)
            await session.commit()
    except Exception:
        pass


# ============================================================
# Task queries
# ============================================================

@router.get("/podcasts", response_model=TaskListResponse)
async def list_podcasts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List podcast tasks"""
    result = await db.execute(
        select(PodcastTask).order_by(desc(PodcastTask.created_at)).offset(offset).limit(limit)
    )
    tasks = result.scalars().all()
    count_result = await db.execute(select(PodcastTask))
    total = len(count_result.scalars().all())
    return TaskListResponse(tasks=[_task_to_response(t) for t in tasks], total=total)


@router.get("/podcasts/{task_id}", response_model=TaskResponse)
async def get_podcast(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific podcast task"""
    task = await db.get(PodcastTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _task_to_response(task)


@router.delete("/podcasts/{task_id}")
async def delete_podcast(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a podcast task"""
    task = await db.get(PodcastTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await db.delete(task)
    await db.commit()
    return {"message": "已删除"}


# ============================================================
# Knowledge base
# ============================================================

@router.post("/knowledge", response_model=DocumentResponse)
async def upload_document(request: DocumentUploadRequest, db: AsyncSession = Depends(get_db)):
    """Upload a knowledge document"""
    chunk_count = rag_service.add_document(
        content=request.content, title=request.title, source=request.source
    )
    doc = KnowledgeDocument(
        id=uuid.uuid4().hex[:12],
        title=request.title,
        content=request.content,
        source=request.source,
        chunk_count=chunk_count,
    )
    db.add(doc)
    await db.commit()
    return DocumentResponse(id=doc.id, title=doc.title, source=doc.source, chunk_count=chunk_count, created_at=doc.created_at)


@router.get("/knowledge/search", response_model=SearchResponse)
async def search_knowledge(query: str, top_k: int = 5):
    """Search the knowledge base"""
    results = rag_service.search(query, top_k=top_k)
    return SearchResponse(query=query, results=results, count=len(results))


@router.get("/knowledge/stats")
async def knowledge_stats():
    """Knowledge base statistics"""
    return {"document_count": rag_service.get_doc_count()}


# ============================================================
# Configuration endpoints
# ============================================================

@router.get("/voices")
async def list_voices():
    """List available voices"""
    return {"voices": list(TTSClient.VOICES.keys()), "default": settings.tts_voice}


@router.get("/moods")
async def list_moods():
    """List available moods"""
    return {
        "moods": [
            {"id": "neutral", "name": "自然", "description": "娓娓道来，像朋友聊天"},
            {"id": "excited", "name": "兴奋", "description": "充满活力，热情洋溢"},
            {"id": "calm", "name": "平静", "description": "平和舒缓，温暖治愈"},
            {"id": "humorous", "name": "幽默", "description": "幽默风趣，轻松活泼"},
            {"id": "serious", "name": "严肃", "description": "严肃专业，逻辑清晰"},
        ]
    }


@router.get("/styles")
async def list_styles():
    """List available styles"""
    return {
        "styles": [
            {"id": "narrative", "name": "叙述", "description": "娓娓道来，像讲故事"},
            {"id": "conversational", "name": "对话", "description": "两人对谈，轻松自然"},
            {"id": "educational", "name": "教育", "description": "知识讲解，深入浅出"},
            {"id": "storytelling", "name": "故事", "description": "故事化叙述，引人入胜"},
        ]
    }


# ============================================================
# Helpers
# ============================================================

def _task_to_response(task: PodcastTask) -> TaskResponse:
    segments = []
    for seg in (task.segments or []):
        segments.append(SegmentResponse(
            type=seg.get("type", ""),
            content=seg.get("content", ""),
            duration_sec=seg.get("duration_sec", 0),
        ))
    return TaskResponse(
        id=task.id, topic=task.topic, mood=task.mood, style=task.style,
        status=task.status.value if isinstance(task.status, TaskStatus) else task.status,
        progress=task.progress, current_step=task.current_step,
        title=task.title, segments=segments,
        audio_path=task.audio_path, duration_sec=task.duration_sec,
        error_message=task.error_message,
        created_at=task.created_at, updated_at=task.updated_at,
    )
