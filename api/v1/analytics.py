"""Analytics API — 看板 + 校区统计"""
from datetime import date

from fastapi import APIRouter, HTTPException, Request

from domains.access.policy import get_policy, PermissionContext
from domains.analytics.dashboard import get_dashboard_data, get_usage_by_campus

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(request: Request, days: int = 7):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "analytics", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    data = await get_dashboard_data(tenant_id, days)
    return {"success": True, "data": data}


@router.get("/usage")
async def usage_by_campus(request: Request, start: date, end: date):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "analytics", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    data = await get_usage_by_campus(tenant_id, start, end)
    return {"success": True, "data": data}
