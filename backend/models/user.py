"""
User model + authentication helpers
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Column, String, Integer, DateTime, Boolean
from passlib.context import CryptContext
from jose import JWTError, jwt

from models.database import Base
from config.settings import settings

# Password hashing (bcrypt preferred, sha256_crypt as fallback)
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pwd_context.hash("test")  # verify bcrypt is available
except Exception:
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


class User(Base):
    """User table"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    credits = Column(Integer, default=5)
    plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def hash_password(password: str) -> str:
    # bcrypt limits to 72 bytes, truncate
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_expire_days)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
