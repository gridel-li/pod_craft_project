"""
CreditService — 用户积分与消费额度管理服务

功能说明：
管理用户账户的积分余额与变动流水，包含三个异步操作函数：
1. use_credits：消费扣除积分，余额充足时写入消费流水并持久化提交；余额不足时返回 False。
2. add_credits：账户充值积分，写入增加流水并提交；用户不存在时抛出 ValueError。
3. get_credit_logs：按时间倒序查询指定用户的积分变动明细列表。
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
    扣减用户积分
    :param db: 数据库异步会话 (AsyncSession)
    :param user_id: 用户唯一标识
    :param amount: 扣减额度（正整数）
    :param reason: 扣费原因说明
    :return: True 表示扣减成功；False 表示用户不存在或积分余额不足
    """
    # 查询当前用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 校验用户存在性与余额充足性
    if not user or user.credits < amount:
        return False

    # 内存中更新实体属性
    user.credits -= amount

    # 构造流水记录（负数表示支出）
    log = CreditLog(
        id=uuid.uuid4().hex,
        user_id=user_id,
        amount=-amount,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)

    # 提交事务至数据库
    await db.commit()
    logger.info(f"用户 {user_id} 消费了 {amount} 积分: {reason}")
    return True


async def add_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    reason: str = "Admin recharge",
) -> None:
    """
    增加用户积分（充值/发放额度）
    :param db: 数据库异步会话
    :param user_id: 用户唯一标识
    :param amount: 增加额度（正整数）
    :param reason: 充值原因说明
    """
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
    logger.info(f"为用户 {user_id} 增加了 {amount} 积分: {reason}")


async def get_credit_logs(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
) -> list[dict]:
    """
    获取指定用户的积分流水记录（按创建时间倒序）
    :param db: 数据库异步会话
    :param user_id: 用户唯一标识
    :param limit: 最大返回记录数
    :return: 流水字典列表
    """
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
