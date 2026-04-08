from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    tenant_id = Column(String(64), nullable=False)
    user_id = Column(String(64), nullable=False)
    user_role = Column(String(64))
    action = Column(String(16), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64))
    changes = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String)

    __table_args__ = (
        Index("idx_audit_tenant_time", "tenant_id", "timestamp"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_time", "timestamp"),
    )
