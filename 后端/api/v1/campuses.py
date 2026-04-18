"""Campuses API — 校区管理"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from domains.access.policy import require_permission
from domains.access.audit import write_audit_log
from domains.organization.campus import (
    get_campuses, create_campus, update_campus, soft_delete_campus,
)

router = APIRouter(prefix="/campuses", tags=["campuses"])


class CreateCampusRequest(BaseModel):
    campus_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)


class UpdateCampusRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)


@router.get("")
async def list_campuses(request: Request, page: int = 1, size: int = 20):
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "campus")

    campuses = await get_campuses(tenant_id, page, size)
    return {"success": True, "data": [
        {"id": c.id, "name": c.name, "status": c.status, "campus_level": c.campus_level}
        for c in campuses
    ]}


@router.post("")
async def create_campus_endpoint(request: Request, body: CreateCampusRequest, background_tasks: BackgroundTasks):
    tenant_id = request.state.tenant_id
    await require_permission(request, "create", "campus")

    campus = await create_campus(tenant_id, body.campus_id, body.name)

    background_tasks.add_task(
        write_audit_log,
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
async def update_campus_endpoint(campus_id: str, request: Request, body: UpdateCampusRequest = None, background_tasks: BackgroundTasks = None):
    tenant_id = request.state.tenant_id
    await require_permission(request, "update", "campus")

    kwargs = {}
    if body and body.name is not None:
        kwargs["name"] = body.name
    campus = await update_campus(campus_id, tenant_id, **kwargs)
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")

    if background_tasks:
        background_tasks.add_task(
            write_audit_log,
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
async def delete_campus_endpoint(campus_id: str, request: Request, background_tasks: BackgroundTasks):
    tenant_id = request.state.tenant_id
    await require_permission(request, "delete", "campus")

    ok = await soft_delete_campus(campus_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Campus not found")

    background_tasks.add_task(
        write_audit_log,
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="delete",
        resource_type="campus",
        resource_id=campus_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True}
