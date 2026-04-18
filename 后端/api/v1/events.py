"""Events API — 批量上报 + 管理查询"""
import re

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query

from domains.events.store import enqueue_events
from domains.access.audit import write_audit_log
from infrastructure.database import async_session
from sqlalchemy import text

router = APIRouter(prefix="/events", tags=["events"])

_TENANT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


def _validate_tenant_id(tenant_id: str) -> bool:
    """校验 tenant_id 格式 — 防止 SQL 注入"""
    return bool(_TENANT_ID_PATTERN.match(tenant_id))


@router.post("/batch")
async def batch_report(request: Request, events: list[dict], background_tasks: BackgroundTasks):
    """批量上报事件 — 放入内存队列（毫秒级返回）"""
    if len(events) > 100:
        raise HTTPException(status_code=400, detail=f"批量上报上限 100 条，当前 {len(events)} 条")
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
    """查询事件列表 — 从 events 分区表按 tenant_id 过滤"""
    if not _validate_tenant_id(tenant_id):
        raise HTTPException(status_code=400, detail="Invalid tenant_id format")
    async with async_session() as db:
        conditions = ["tenant_id = :tenant_id"]
        params: dict = {"tenant_id": tenant_id, "limit": limit}
        if event_type:
            conditions.append("event_type = :event_type")
            params["event_type"] = event_type
        where = " AND ".join(conditions)
        sql = f"SELECT * FROM events WHERE {where} ORDER BY timestamp DESC LIMIT :limit"
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
