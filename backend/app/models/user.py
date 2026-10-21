from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class RevokedToken(Base):
    """JWT blacklist used by logout."""
    __tablename__ = "revoked_tokens"
    jti = Column(String(64), primary_key=True)
    expires_at = Column(DateTime(timezone=True))
