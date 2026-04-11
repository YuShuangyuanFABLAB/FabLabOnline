"""Campuses API — 校区管理"""
from fastapi import APIRouter, HTTPException, Request

from domains.access.policy import get_policy, PermissionContext
from domains.access.audit import write_audit_log
from domains.organization.campus import (
    get_campuses, create_campus, update_campus, soft_delete_campus,
)

router = APIRouter(prefix="/campuses", tags=["campuses"])


@router.get("")
async def list_campuses(request: Request, page: int = 1, size: int = 20):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "campus", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    campuses = await get_campuses(tenant_id, page, size)
    return {"success": True, "data": [
        {"id": c.id, "name": c.name, "status": c.status, "campus_level": c.campus_level}
        for c in campuses
    ]}


@router.post("")
async def create_campus_endpoint(request: Request, campus_id: str, name: str):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "create", "campus", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    campus = await create_campus(tenant_id, campus_id, name)

    await write_audit_log(
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="create",
        resource_type="campus",
        resource_id=campus.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True, "data": {"id": campus.id, "name": campus.name}}


@router.put("/{campus_id}")
async def update_campus_endpoint(campus_id: str, request: Request, name: str | None = None):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "update", "campus", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    campus = await update_campus(campus_id, tenant_id, **kwargs)
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")

    await write_audit_log(
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="update",
        resource_type="campus",
        resource_id=campus_id,
        changes=kwargs,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True, "data": {"id": campus.id, "name": campus.name}}


@router.delete("/{campus_id}")
async def delete_campus_endpoint(campus_id: str, request: Request):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "delete", "campus", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    ok = await soft_delete_campus(campus_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Campus not found")

    await write_audit_log(
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="delete",
        resource_type="campus",
        resource_id=campus_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True}
