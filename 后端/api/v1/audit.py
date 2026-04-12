"""Audit API — 审计日志查询"""
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select, func

from infrastructure.database import async_session
from models.audit import AuditLog
from domains.access.policy import get_policy, PermissionContext

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def query_audit_logs(request: Request, page: int = 1, size: int = 20):
    """分页查询审计日志"""
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "audit", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        # Count total
        count_result = await db.execute(
            select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == tenant_id)
        )
        total = count_result.scalar() or 0

        # Query page
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.timestamp.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        logs = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": str(log.id) if log.id else None,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "changes": log.changes,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ],
        "total": total,
    }
