from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from models.base import Base


class Config(Base):
    __tablename__ = "configs"
    __table_args__ = (
        UniqueConstraint("scope", "scope_id", "key"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String(16), nullable=False)
    scope_id = Column(String(64))
    key = Column(String(128), nullable=False)
    value = Column(JSONB, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
