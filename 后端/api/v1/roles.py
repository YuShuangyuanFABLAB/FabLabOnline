"""Roles API — 角色与权限 CRUD"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from sqlalchemy import select, delete as sa_delete

from infrastructure.database import async_session
from models.role import Role, RolePermission
from domains.access.policy import require_permission
from domains.access.roles import get_roles, get_user_roles
from domains.access.permissions import get_role_permissions, get_roles_batch_permissions
from domains.access.audit import write_audit_log

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("")
async def list_roles(request: Request):
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "role")

    roles = await get_roles(tenant_id)
    role_ids = [r.id for r in roles]
    perms_map = await get_roles_batch_permissions(role_ids)

    return {"success": True, "data": [
        {
            "id": r.id, "name": r.name,
            "display_name": r.display_name, "level": r.level,
            "permissions": perms_map.get(r.id, []),
        }
        for r in roles
    ]}


@router.get("/{role_id}/permissions")
async def get_role_perms(role_id: str, request: Request):
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "role")

    perms = await get_role_permissions(role_id)
    return {"success": True, "data": perms}


@router.get("/user/{user_id}")
async def get_user_roles_endpoint(user_id: str, request: Request):
    tenant_id = request.state.tenant_id
    await require_permission(request, "read", "role")

    roles = await get_user_roles(user_id)
    return {"success": True, "data": roles}


@router.delete("/{role_id}")
async def delete_role(role_id: str, request: Request):
    """删除角色 — 系统角色禁止删除"""
    tenant_id = request.state.tenant_id
    await require_permission(request, "delete", "role")

    async with async_session() as db:
        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        if role.is_system:
            raise HTTPException(status_code=403, detail="系统角色禁止删除")
        await db.delete(role)
        await db.commit()

    return {"success": True}


@router.post("")
async def create_role(
    request: Request,
    background_tasks: BackgroundTasks,
    name: str,
    display_name: str,
    permission_ids: list[str],
):
    """创建自定义角色"""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="角色名不能为空")

    tenant_id = request.state.tenant_id
    await require_permission(request, "create", "role")

    async with async_session() as db:
        role = Role(
            id=name,
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            is_system=False,
        )
        db.add(role)
        for pid in permission_ids:
            db.add(RolePermission(role_id=name, permission_id=pid))
        await db.commit()

    background_tasks.add_task(
        write_audit_log,
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="create",
        resource_type="role",
        resource_id=name,
        changes={"name": name, "permissions": permission_ids},
    )

    return {"success": True, "data": {
        "id": name, "name": name, "display_name": display_name,
        "permissions": permission_ids,
    }}


@router.put("/{role_id}")
async def update_role(
    role_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    name: str,
    display_name: str,
    permission_ids: list[str],
):
    """更新角色名和权限 — 系统角色禁止修改"""
    tenant_id = request.state.tenant_id
    await require_permission(request, "update", "role")

    async with async_session() as db:
        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        if role.is_system:
            raise HTTPException(status_code=403, detail="系统角色禁止修改")

        role.name = name
        role.display_name = display_name

        # 替换权限：先删除旧的，再插入新的
        await db.execute(
            sa_delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for pid in permission_ids:
            db.add(RolePermission(role_id=role_id, permission_id=pid))
        await db.commit()

    background_tasks.add_task(
        write_audit_log,
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="update",
        resource_type="role",
        resource_id=role_id,
        changes={"name": name, "permissions": permission_ids},
    )

    return {"success": True, "data": {
        "id": role_id, "name": name, "display_name": display_name,
        "permissions": permission_ids,
    }}
