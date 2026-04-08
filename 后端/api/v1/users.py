"""Users API — 用户管理"""
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from infrastructure.database import async_session
from models.user import User
from domains.access.policy import get_policy, PermissionContext
from domains.access.audit import write_audit_log
from domains.access.roles import assign_role, get_user_roles
from domains.identity.session_manager import SessionManager

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(request: Request, page: int = 1, size: int = 20):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "user", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        result = await db.execute(
            select(User)
            .where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
            .offset((page - 1) * size)
            .limit(size)
        )
        users = result.scalars().all()
        return {"success": True, "data": [
            {"id": u.id, "name": u.name, "status": u.status, "campus_id": u.campus_id}
            for u in users
        ]}


@router.get("/{user_id}")
async def get_user(user_id: str, request: Request):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "user", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "data": {
            "id": user.id, "name": user.name, "status": user.status,
            "campus_id": user.campus_id, "tenant_id": user.tenant_id,
        }}


@router.put("/{user_id}/status")
async def update_user_status(user_id: str, request: Request, status: str):
    """启用/禁用用户"""
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "update", "user", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_status = user.status
        user.status = status
        await db.commit()

        # 写时主动失效 Redis 缓存
        session_mgr = SessionManager()
        await session_mgr.invalidate_user_status(user_id)

        await write_audit_log(
            tenant_id=tenant_id,
            user_id=request.state.user_id,
            action="update",
            resource_type="user",
            resource_id=user_id,
            changes={"status": {"old": old_status, "new": status}},
        )

        return {"success": True, "data": {"id": user.id, "status": user.status}}


@router.post("/{user_id}/roles")
async def assign_user_role(user_id: str, request: Request, role_id: str, scope_id: str = "*"):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "update", "role", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    ur = await assign_role(user_id, role_id, scope_id)

    await write_audit_log(
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="update",
        resource_type="user",
        resource_id=user_id,
        changes={"role_assigned": {"role_id": role_id, "scope_id": scope_id}},
    )

    return {"success": True, "data": {"user_id": ur.user_id, "role_id": ur.role_id, "scope_id": ur.scope_id}}
