"""
Credit service — manage user credits (consume / add / query logs)
"""

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import CreditLog
from models.user import User

logger = logging.getLogger(__name__)


async def use_credits(
    db: AsyncSession,
    user_id: str,
    amount: int = 1,
    reason: str = "Generate podcast",
) -> bool:
    """
    Deduct credits from a user.
    Returns True if successful, False if insufficient balance.
    """
    # 先读取用户，再修改 ORM 对象，commit 时 SQLAlchemy 会生成 UPDATE/INSERT。
    # 高并发生产环境应改为带条件的原子 UPDATE 或行锁，避免同时扣成负数。
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.credits < amount:
        return False

    user.credits -= amount
    log = CreditLog(
        id=uuid.uuid4().hex,
        user_id=user_id,
        amount=-amount,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    logger.info(f"User {user_id} used {amount} credit(s): {reason}")
    return True


async def add_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    reason: str = "Admin recharge",
) -> None:
    """Add credits to a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"User {user_id} not found")

    user.credits += amount
    log = CreditLog(
        id=uuid.uuid4().hex,
        user_id=user_id,
        amount=amount,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    logger.info(f"Added {amount} credit(s) to user {user_id}: {reason}")


async def get_credit_logs(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
) -> list[dict]:
    """Get recent credit transaction logs for a user."""
    result = await db.execute(
        select(CreditLog)
        .where(CreditLog.user_id == user_id)
        .order_by(desc(CreditLog.created_at))
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "amount": log.amount,
            "reason": log.reason,
            "created_at": log.created_at.isoformat() if log.created_at else "",
        }
        for log in logs
    ]
