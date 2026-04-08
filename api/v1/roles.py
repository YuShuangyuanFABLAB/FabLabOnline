"""Roles API — 角色与权限查询"""
from fastapi import APIRouter, HTTPException, Request

from domains.access.policy import get_policy, PermissionContext
from domains.access.roles import get_roles, get_user_roles
from domains.access.permissions import get_role_permissions

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
async def list_roles(request: Request):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "role", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    roles = await get_roles(tenant_id)
    return {"success": True, "data": [
        {"id": r.id, "name": r.name, "display_name": r.display_name, "level": r.level}
        for r in roles
    ]}


@router.get("/{role_id}/permissions")
async def get_role_perms(role_id: str, request: Request):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "role", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    perms = await get_role_permissions(role_id)
    return {"success": True, "data": perms}


@router.get("/user/{user_id}")
async def get_user_roles_endpoint(user_id: str, request: Request):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "role", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    roles = await get_user_roles(user_id)
    return {"success": True, "data": roles}
