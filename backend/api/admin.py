"""
Admin routes — user management, credit recharge, system stats
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db, PodcastTask, CreditLog
from models.user import User
from api.auth import get_current_user
from services.credit_service import add_credits, get_credit_logs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================
# Dependencies
# ============================================================

async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin；这是最简单的 RBAC（基于角色的访问控制）。"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ============================================================
# Schemas
# ============================================================

class AddCreditsRequest(BaseModel):
    amount: int = Field(..., ge=1, le=10000, description="Credits to add")
    reason: str = Field(default="Admin recharge", max_length=200)


class UserListItem(BaseModel):
    id: str
    username: str
    email: str
    credits: int
    plan: str
    is_admin: bool
    is_active: bool
    created_at: str


class SystemStats(BaseModel):
    total_users: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_credits_used: int


# ============================================================
# Routes
# ============================================================

@router.get("/users", response_model=list[UserListItem])
async def list_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserListItem(
            id=u.id,
            username=u.username,
            email=u.email,
            credits=u.credits,
            plan=u.plan,
            is_admin=u.is_admin,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else "",
        )
        for u in users
    ]


@router.post("/users/{user_id}/credits")
async def recharge_credits(
    user_id: str,
    request: AddCreditsRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Add credits to a user (admin only)"""
    try:
        await add_credits(db, user_id, request.amount, request.reason)
        return {"message": f"Added {request.amount} credits", "user_id": user_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}/credits")
async def user_credit_logs(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get credit logs for a specific user (admin only)"""
    logs = await get_credit_logs(db, user_id)
    return {"user_id": user_id, "logs": logs}


@router.get("/stats", response_model=SystemStats)
async def system_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics (admin only)"""
    user_count = await db.execute(select(func.count(User.id)))
    task_count = await db.execute(select(func.count(PodcastTask.id)))
    completed_count = await db.execute(
        select(func.count(PodcastTask.id)).where(PodcastTask.status == "completed")
    )
    failed_count = await db.execute(
        select(func.count(PodcastTask.id)).where(PodcastTask.status == "failed")
    )
    credits_used = await db.execute(
        select(func.coalesce(func.sum(CreditLog.amount), 0)).where(CreditLog.amount < 0)
    )

    return SystemStats(
        total_users=user_count.scalar() or 0,
        total_tasks=task_count.scalar() or 0,
        completed_tasks=completed_count.scalar() or 0,
        failed_tasks=failed_count.scalar() or 0,
        total_credits_used=abs(credits_used.scalar() or 0),
    )
