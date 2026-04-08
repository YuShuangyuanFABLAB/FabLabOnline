"""Events API — 批量上报"""
from fastapi import APIRouter, Request, BackgroundTasks

from domains.events.store import enqueue_events
from domains.access.audit import write_audit_log

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
