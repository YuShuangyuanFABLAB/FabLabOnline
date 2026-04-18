"""测试 Pydantic 请求校验 — M8 TDD"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_token(user_id="u1", tenant_id="t1"):
    from config.settings import settings
    from domains.identity.token_manager import TokenManager
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


def _mock_auth():
    """通用 auth + 权限 mock"""
    mock_sm = MagicMock()
    mock_sm.is_session_valid = AsyncMock(return_value=True)
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    return mock_sm, mock_redis


class TestCampusPydantic:
    """Campus API 请求体校验"""

    @pytest.mark.asyncio
    async def test_create_campus_empty_name_rejected(self, client):
        """创建校区时空名称被拒绝"""
        token = _make_token()
        mock_sm, mock_redis = _mock_auth()

        with patch("api.middleware._session_manager", mock_sm), \
             patch("domains.access.policy.redis_client", mock_redis), \
             patch("domains.access.policy.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            resp = await client.post(
                "/api/v1/campuses",
                json={"campus_id": "test", "name": ""},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_campus_valid_body_accepted(self, client):
        """创建校区时有效请求体被接受"""
        token = _make_token()
        mock_sm, mock_redis = _mock_auth()

        with patch("api.middleware._session_manager", mock_sm), \
             patch("domains.access.policy.redis_client", mock_redis), \
             patch("domains.access.policy.async_session") as mock_session, \
             patch("api.v1.campuses.require_permission", new_callable=AsyncMock), \
             patch("api.v1.campuses.create_campus", new_callable=AsyncMock) as mock_create, \
             patch("api.v1.campuses.write_audit_log", new_callable=AsyncMock):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            mock_campus = MagicMock()
            mock_campus.id = "test-campus"
            mock_campus.name = "测试校区"
            mock_create.return_value = mock_campus

            resp = await client.post(
                "/api/v1/campuses",
                json={"campus_id": "test-campus", "name": "测试校区"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code in (200, 201)


class TestAppPydantic:
    """Apps API 请求体校验"""

    @pytest.mark.asyncio
    async def test_register_app_empty_name_rejected(self, client):
        """注册应用时空名称被拒绝"""
        token = _make_token()
        mock_sm, mock_redis = _mock_auth()

        with patch("api.middleware._session_manager", mock_sm), \
             patch("domains.access.policy.redis_client", mock_redis), \
             patch("domains.access.policy.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            resp = await client.post(
                "/api/v1/apps",
                json={"app_id": "test", "name": "", "app_key": "key"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 422


class TestConfigPydantic:
    """Config API 请求体校验"""

    @pytest.mark.asyncio
    async def test_update_config_empty_key_rejected(self, client):
        """更新配置时空 key 被拒绝"""
        token = _make_token()
        mock_sm, mock_redis = _mock_auth()

        with patch("api.middleware._session_manager", mock_sm), \
             patch("domains.access.policy.redis_client", mock_redis), \
             patch("domains.access.policy.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            resp = await client.put(
                "/api/v1/config",
                json={"scope": "global", "scope_id": None, "key": "", "value": {}},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 422
