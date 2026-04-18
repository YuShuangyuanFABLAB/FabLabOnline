"""权限策略 — RBAC deny-by-default + Redis 缓存"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from infrastructure.database import async_session
from infrastructure.redis import redis_client
from models.role import UserRole, RolePermission
from sqlalchemy import select


@dataclass
class PermissionContext:
    """权限上下文 — 明确定义必须包含的字段"""
    tenant_id: str
    campus_id: str | None = None
    resource_owner: str | None = None
    action_level: str = "read"


class PermissionPolicy(ABC):
    """权限策略接口 — Phase 1 用 RBAC 实现，未来可替换为 ABAC"""

    @abstractmethod
    async def check_permission(
        self,
        user_id: str,
        action: str,
        resource: str,
        context: PermissionContext,
    ) -> bool:
        pass


class RBACPolicy(PermissionPolicy):
    """Phase 1 实现：基于角色的权限检查（deny-by-default）+ Redis 权限缓存"""

    CACHE_TTL = 300  # 5 分钟

    async def check_permission(
        self, user_id: str, action: str, resource: str, context: PermissionContext
    ) -> bool:
        perms, roles = await self._get_user_permissions_cached(user_id)

        if not roles:
            return False  # 无角色 = 拒绝

        perm_key = f"{resource}:{action}"

        for ur in roles:
            if perm_key not in perms.get(ur["role_id"], set()):
                continue

            # 校区级角色限定 scope_id
            if ur["scope_id"] != "*" and context.campus_id:
                if ur["scope_id"] != context.campus_id:
                    continue

            return True

        return False  # deny-by-default

    async def _get_user_permissions_cached(
        self, user_id: str
    ) -> tuple[dict, list[dict]]:
        """Redis 缓存 → DB fallback → 回填缓存"""
        cache_key = f"user_permissions:{user_id}"

        # 尝试 Redis 缓存
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            perms = {k: set(v) for k, v in data["perms"].items()}
            return perms, data["roles"]

        # 缓存未命中 → 查 DB
        async with async_session() as db:
            result = await db.execute(
                select(UserRole).where(UserRole.user_id == user_id)
            )
            user_roles = result.scalars().all()
            if not user_roles:
                return {}, []

            roles = [{"role_id": ur.role_id, "scope_id": ur.scope_id} for ur in user_roles]
            perms: dict[str, set[str]] = {}
            for ur in user_roles:
                perm_result = await db.execute(
                    select(RolePermission).where(RolePermission.role_id == ur.role_id)
                )
                role_perms = perm_result.scalars().all()
                perms[ur.role_id] = {rp.permission_id for rp in role_perms}

        # 回填缓存
        perms_serializable = {k: list(v) for k, v in perms.items()}
        await redis_client.setex(
            cache_key,
            self.CACHE_TTL,
            json.dumps({"perms": perms_serializable, "roles": roles}),
        )
        return perms, roles


async def invalidate_permission_cache(user_id: str):
    """角色/权限变更时主动失效缓存"""
    await redis_client.delete(f"user_permissions:{user_id}")


# 全局策略实例
_policy: PermissionPolicy | None = None


def get_policy() -> PermissionPolicy:
    global _policy
    if _policy is None:
        _policy = RBACPolicy()
    return _policy


async def require_permission(request, action: str, resource: str):
    """权限检查快捷方法 — 封装重复的 get_policy + check_permission + 403 样板代码"""
    from fastapi import HTTPException

    tenant_id = request.state.tenant_id
    user_id = request.state.user_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(user_id, action, resource, ctx):
        raise HTTPException(status_code=403, detail="Permission denied")
