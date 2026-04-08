"""异步审计日志"""
from datetime import datetime, timezone

import structlog

from infrastructure.database import async_session
from models.audit import AuditLog

logger = structlog.get_logger()


async def write_audit_log(
    tenant_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    user_role: str | None = None,
    changes: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    """异步写入审计日志 — 即使 DB 写入失败也不丢记录"""
    try:
        async with async_session() as db:
            log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                user_role=user_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(log)
            await db.commit()
    except Exception as e:
        # DB 写入失败时记录到结构化日志（不丢记录）
        logger.error("audit_log_write_failed",
                     tenant_id=tenant_id, user_id=user_id,
                     action=action, resource_type=resource_type,
                     error=str(e))
