"""测试 PermissionPolicy — RBAC deny-by-default + Redis 缓存"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from domains.access.policy import RBACPolicy, PermissionContext


@pytest.fixture
def policy():
    return RBACPolicy()


class TestRBACPolicy:
    @pytest.mark.asyncio
    async def test_no_roles_user_is_denied(self, policy):
        """无角色用户 → deny"""
        with patch("domains.access.policy.async_session") as mock_session, \
             patch("domains.access.policy.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            ctx = PermissionContext(tenant_id="t1")
            result = await policy.check_permission("user_no_role", "read", "user", ctx)
            assert result is False

    @pytest.mark.asyncio
    async def test_user_with_permission_is_allowed(self, policy):
        """有权限用户 → allow"""
        with patch("domains.access.policy.async_session") as mock_session, \
             patch("domains.access.policy.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_ur = MagicMock()
            mock_ur.role_id = "super_admin"
            mock_ur.scope_id = "*"
            mock_result_roles = MagicMock()
            mock_result_roles.scalars.return_value.all.return_value = [mock_ur]

            mock_rp = MagicMock()
            mock_rp.permission_id = "user:read"
            mock_result_perms = MagicMock()
            mock_result_perms.scalars.return_value.all.return_value = [mock_rp]

            mock_db.execute.side_effect = [mock_result_roles, mock_result_perms]

            ctx = PermissionContext(tenant_id="t1")
            result = await policy.check_permission("admin_user", "read", "user", ctx)
            assert result is True

    @pytest.mark.asyncio
    async def test_campus_admin_only_own_campus(self, policy):
        """校区管理员只能操作本校区"""
        # 操作本校区 → allow
        with patch("domains.access.policy.async_session") as mock_session, \
             patch("domains.access.policy.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_ur = MagicMock()
            mock_ur.role_id = "campus_admin"
            mock_ur.scope_id = "campus_A"
            mock_result_roles = MagicMock()
            mock_result_roles.scalars.return_value.all.return_value = [mock_ur]

            mock_rp = MagicMock()
            mock_rp.permission_id = "user:read"
            mock_result_perms = MagicMock()
            mock_result_perms.scalars.return_value.all.return_value = [mock_rp]

            mock_db.execute.side_effect = [mock_result_roles, mock_result_perms]

            ctx_own = PermissionContext(tenant_id="t1", campus_id="campus_A")
            assert await policy.check_permission("ca", "read", "user", ctx_own) is True

        # 操作其他校区 → deny（scope_id 不匹配）
        with patch("domains.access.policy.async_session") as mock_session, \
             patch("domains.access.policy.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_ur = MagicMock()
            mock_ur.role_id = "campus_admin"
            mock_ur.scope_id = "campus_A"
            mock_result_roles = MagicMock()
            mock_result_roles.scalars.return_value.all.return_value = [mock_ur]

            mock_rp = MagicMock()
            mock_rp.permission_id = "user:read"
            mock_result_perms = MagicMock()
            mock_result_perms.scalars.return_value.all.return_value = [mock_rp]

            mock_db.execute.side_effect = [mock_result_roles, mock_result_perms]

            ctx_other = PermissionContext(tenant_id="t1", campus_id="campus_B")
            assert await policy.check_permission("ca", "read", "user", ctx_other) is False

    @pytest.mark.asyncio
    async def test_unknown_permission_is_denied(self, policy):
        """权限不存在 → deny-by-default"""
        with patch("domains.access.policy.async_session") as mock_session, \
             patch("domains.access.policy.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_ur = MagicMock()
            mock_ur.role_id = "teacher"
            mock_ur.scope_id = "*"
            mock_result_roles = MagicMock()
            mock_result_roles.scalars.return_value.all.return_value = [mock_ur]

            mock_result_perms = MagicMock()
            mock_result_perms.scalars.return_value.all.return_value = []

            mock_db.execute.side_effect = [mock_result_roles, mock_result_perms]

            ctx = PermissionContext(tenant_id="t1")
            result = await policy.check_permission("teacher1", "create", "user", ctx)
            assert result is False

    @pytest.mark.asyncio
    async def test_cached_permissions_are_used(self, policy):
        """Redis 缓存命中时直接返回，不查 DB"""
        with patch("domains.access.policy.redis_client") as mock_redis:
            cached_data = {
                "perms": {"super_admin": ["user:read", "user:create"]},
                "roles": [{"role_id": "super_admin", "scope_id": "*"}],
            }
            mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

            ctx = PermissionContext(tenant_id="t1")
            result = await policy.check_permission("admin", "read", "user", ctx)
            assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_permission_cache_deletes_key(self):
        """失效权限缓存应删除 Redis key"""
        with patch("domains.access.policy.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock()
            from domains.access.policy import invalidate_permission_cache
            await invalidate_permission_cache("user_1")
            mock_redis.delete.assert_called_once_with("user_permissions:user_1")
