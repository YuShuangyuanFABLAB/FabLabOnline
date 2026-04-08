"""角色分配与查询 domain 逻辑"""
from infrastructure.database import async_session
from models.role import Role, RolePermission, UserRole
from sqlalchemy import select


async def assign_role(user_id: str, role_id: str, scope_id: str = "*") -> UserRole:
    async with async_session() as db:
        ur = UserRole(user_id=user_id, role_id=role_id, scope_id=scope_id)
        db.add(ur)
        await db.commit()
        await db.refresh(ur)

    # 角色变更 → 主动失效 Redis 权限缓存
    from domains.access.policy import invalidate_permission_cache
    await invalidate_permission_cache(user_id)

    return ur


async def revoke_role(user_id: str, role_id: str, scope_id: str = "*") -> bool:
    async with async_session() as db:
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.scope_id == scope_id,
            )
        )
        ur = result.scalar_one_or_none()
        if not ur:
            return False
        await db.delete(ur)
        await db.commit()

    # 角色变更 → 主动失效 Redis 权限缓存
    from domains.access.policy import invalidate_permission_cache
    await invalidate_permission_cache(user_id)

    return True


async def get_user_roles(user_id: str) -> list[dict]:
    async with async_session() as db:
        result = await db.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        return [{"role_id": ur.role_id, "scope_id": ur.scope_id} for ur in result.scalars().all()]


async def get_roles(tenant_id: str | None = None) -> list[Role]:
    async with async_session() as db:
        query = select(Role)
        if tenant_id:
            query = query.where((Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None)))
        result = await db.execute(query)
        return list(result.scalars().all())
