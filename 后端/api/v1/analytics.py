"""Analytics API — 看板 + 校区统计 + 用户活动"""
import re
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from domains.access.policy import require_permission
from domains.analytics.dashboard import get_dashboard_data, get_usage_by_campus
from infrastructure.database import async_session

_TENANT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(request: Request, days: int = 7):
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "analytics")

    data = await get_dashboard_data(tenant_id, days)
    return {"success": True, "data": data}


@router.get("/usage")
async def usage_by_campus(request: Request, start: date, end: date):
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "analytics")

    data = await get_usage_by_campus(tenant_id, start, end)
    return {"success": True, "data": data}


async def get_user_activity(tenant_id: str, user_id: str):
    """查询单用户活动日志 — 从 events 分区表按 tenant_id 过滤"""
    if not _TENANT_ID_PATTERN.match(tenant_id):
        raise HTTPException(status_code=400, detail="Invalid tenant_id format")
    async with async_session() as db:
        sql = text(
            "SELECT event_type, payload, timestamp FROM events "
            "WHERE tenant_id = :tenant_id AND user_id = :uid "
            "ORDER BY timestamp DESC LIMIT 50"
        )
        result = await db.execute(sql, {"tenant_id": tenant_id, "uid": user_id})
        events = [dict(row._mapping) for row in result.fetchall()]
        return {"user_id": user_id, "events": events}


@router.get("/users/{user_id}/activity")
async def user_activity(user_id: str, request: Request):
    """单用户活动日志"""
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "analytics")

    data = await get_user_activity(tenant_id, user_id)
    return {"success": True, "data": data}
