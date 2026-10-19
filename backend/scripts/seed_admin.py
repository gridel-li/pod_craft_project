"""
Seed script — create a default admin user in the database.

Usage:
    uv run python scripts/seed_admin.py

This script is idempotent: if the admin user already exists, it prints
a message and exits without error.
"""

import asyncio
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from models.database import init_db, async_session
from models.user import User, hash_password


DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@podcraft.local",
    "password": "admin123",
}


async def seed():
    await init_db()
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.email == DEFAULT_ADMIN["email"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            if not existing.is_admin:
                existing.is_admin = True
                await db.commit()
                print(f"✅ User '{existing.username}' promoted to admin.")
            else:
                print(f"ℹ️  Admin user '{existing.username}' already exists. Skipping.")
            return

        import uuid
        user = User(
            id=uuid.uuid4().hex,
            username=DEFAULT_ADMIN["username"],
            email=DEFAULT_ADMIN["email"],
            hashed_password=hash_password(DEFAULT_ADMIN["password"]),
            credits=999,
            plan="enterprise",
            is_admin=True,
        )
        db.add(user)
        await db.commit()
        print("✅ Admin user created!")
        print(f"   Email:    {DEFAULT_ADMIN['email']}")
        print(f"   Password: {DEFAULT_ADMIN['password']}")
        print("   Credits:  999")
        print("\n⚠️  Please change the password after first login!")


if __name__ == "__main__":
    asyncio.run(seed())
