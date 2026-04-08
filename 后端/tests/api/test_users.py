"""测试 users / campuses / roles API 路由 — 认证 + 权限拦截"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from domains.identity.token_manager import TokenManager
from config.settings import settings


def _make_token(user_id="admin", tenant_id="default"):
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


class TestUsersAPI:
    @pytest.mark.asyncio
    async def test_list_users_without_token_returns_401(self, client):
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_users_with_token_returns_403_or_200(self, client):
        """有 token 但可能无权限 → 403，或 DB mock 返回 200"""
        token = _make_token()
        mock_sm = MagicMock()
        mock_sm.is_session_valid = AsyncMock(return_value=True)
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        with patch("api.middleware._session_manager", mock_sm), \
             patch("domains.access.policy.redis_client", mock_redis), \
             patch("domains.access.policy.async_session") as mock_session:
            # 无角色 → policy 返回 False → 403
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            resp = await client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 403


class TestCampusesAPI:
    @pytest.mark.asyncio
    async def test_create_campus_without_token_returns_401(self, client):
        resp = await client.post("/api/v1/campuses?campus_id=test&name=TestCampus")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_campus_without_token_returns_401(self, client):
        resp = await client.delete("/api/v1/campuses/nonexistent")
        assert resp.status_code == 401


class TestRolesAPI:
    @pytest.mark.asyncio
    async def test_list_roles_without_token_returns_401(self, client):
        resp = await client.get("/api/v1/roles")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_roles_without_token_returns_401(self, client):
        resp = await client.get("/api/v1/roles/user/u1")
        assert resp.status_code == 401
