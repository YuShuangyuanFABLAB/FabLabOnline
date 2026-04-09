"""Events API — 批量上报 + 管理查询"""
from fastapi import APIRouter, Request, BackgroundTasks, Query

from domains.events.store import enqueue_events
from domains.access.audit import write_audit_log
from infrastructure.database import async_session
from sqlalchemy import text

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/batch")
async def batch_report(request: Request, events: list[dict], background_tasks: BackgroundTasks):
    """批量上报事件 — 放入内存队列（毫秒级返回）"""
    tenant_id = request.state.tenant_id
    user_id = request.state.user_id
    app_id = getattr(request.state, "app_id", "unknown")

    result = await enqueue_events(events, tenant_id, user_id, app_id)

    background_tasks.add_task(
        write_audit_log,
        tenant_id=tenant_id,
        user_id=user_id,
        action="create",
        resource_type="event",
        changes={"count": len(events), "enqueued": result["enqueued"]},
    )

    if result["errors"]:
        return {"success": True, "data": result, "error": "部分事件校验失败"}
    return {"success": True, "data": result}


async def get_events(tenant_id: str, event_type: str = None, limit: int = 20):
    """查询事件列表"""
    async with async_session() as db:
        table = f"events_{tenant_id}"
        sql = f"SELECT * FROM {table}"
        params = {"limit": limit}
        if event_type:
            sql += " WHERE event_type = :event_type"
            params["event_type"] = event_type
        sql += " ORDER BY timestamp DESC LIMIT :limit"
        result = await db.execute(text(sql), params)
        rows = [dict(row._mapping) for row in result.fetchall()]
        return rows


@router.get("")
async def query_events(
    request: Request,
    event_type: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """管理查询事件列表"""
    tenant_id = request.state.tenant_id
    rows = await get_events(tenant_id, event_type, limit)
    return {"success": True, "data": rows}
