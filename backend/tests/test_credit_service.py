"""
Tests for credit service — unit tests for use/add/query operations
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.database import Base
from models.user import User, hash_password
from services.credit_service import use_credits, add_credits, get_credit_logs


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def test_user(db):
    user = User(
        id="test-user-001",
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password"),
        credits=10,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


class TestUseCredits:

    @pytest.mark.asyncio
    async def test_use_credits_success(self, db, test_user):
        result = await use_credits(db, test_user.id, amount=3, reason="Test generation")
        assert result is True

        # Verify credits were deducted
        await db.refresh(test_user)
        assert test_user.credits == 7

    @pytest.mark.asyncio
    async def test_use_credits_insufficient_balance(self, db, test_user):
        result = await use_credits(db, test_user.id, amount=100, reason="Too expensive")
        assert result is False

        # Credits should remain unchanged
        await db.refresh(test_user)
        assert test_user.credits == 10

    @pytest.mark.asyncio
    async def test_use_credits_nonexistent_user(self, db):
        result = await use_credits(db, "nonexistent-id", amount=1)
        assert result is False

    @pytest.mark.asyncio
    async def test_use_credits_creates_log(self, db, test_user):
        await use_credits(db, test_user.id, amount=2, reason="Log test")
        logs = await get_credit_logs(db, test_user.id)
        assert len(logs) == 1
        assert logs[0]["amount"] == -2
        assert logs[0]["reason"] == "Log test"


class TestAddCredits:

    @pytest.mark.asyncio
    async def test_add_credits_success(self, db, test_user):
        await add_credits(db, test_user.id, amount=20, reason="Recharge")
        await db.refresh(test_user)
        assert test_user.credits == 30

    @pytest.mark.asyncio
    async def test_add_credits_nonexistent_user(self, db):
        with pytest.raises(ValueError, match="not found"):
            await add_credits(db, "nonexistent-id", amount=10)

    @pytest.mark.asyncio
    async def test_add_credits_creates_log(self, db, test_user):
        await add_credits(db, test_user.id, amount=50, reason="Bonus")
        logs = await get_credit_logs(db, test_user.id)
        assert len(logs) == 1
        assert logs[0]["amount"] == 50
        assert logs[0]["reason"] == "Bonus"


class TestGetCreditLogs:

    @pytest.mark.asyncio
    async def test_empty_logs(self, db, test_user):
        logs = await get_credit_logs(db, test_user.id)
        assert logs == []

    @pytest.mark.asyncio
    async def test_multiple_logs_ordered(self, db, test_user):
        await use_credits(db, test_user.id, amount=1, reason="First")
        await add_credits(db, test_user.id, amount=10, reason="Second")
        await use_credits(db, test_user.id, amount=2, reason="Third")

        logs = await get_credit_logs(db, test_user.id)
        assert len(logs) == 3
        # Most recent first
        assert logs[0]["reason"] == "Third"
        assert logs[1]["reason"] == "Second"
        assert logs[2]["reason"] == "First"

    @pytest.mark.asyncio
    async def test_logs_respect_limit(self, db, test_user):
        for i in range(5):
            await add_credits(db, test_user.id, amount=1, reason=f"Log {i}")

        logs = await get_credit_logs(db, test_user.id, limit=3)
        assert len(logs) == 3
