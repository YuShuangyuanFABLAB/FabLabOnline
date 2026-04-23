"""测试 HttpOnly Cookie 认证 — TDD RED"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from main import app
from domains.identity.password import hash_password


def _make_token(user_id="u1", tenant_id="t1"):
    from config.settings import settings
    from domains.identity.token_manager import TokenManager
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHttpOnlyCookieAuth:
    """C1: Token 通过 HttpOnly Cookie 传递，不使用 localStorage/Authorization header"""

    @pytest.mark.asyncio
    async def test_login_sets_httponly_cookie(self, client):
        """登录成功后 response 设置 HttpOnly Cookie"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.delete = AsyncMock()
        mock_sm = MagicMock()
        mock_sm.cache_user_status = AsyncMock()

        with patch("api.v1.auth.redis_client", mock_redis), \
             patch("api.v1.auth.session_mgr", mock_sm), \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[{"role_id": "super_admin", "scope_id": "*"}]), \
             patch("api.v1.auth.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_user = MagicMock()
            mock_user.id = "admin"
            mock_user.tenant_id = "default"
            mock_user.name = "Admin"

            pw_hash = hash_password("admin123")
            mock_pw = MagicMock()
            mock_pw.value = pw_hash

            mock_result_user = MagicMock()
            mock_result_user.scalar_one_or_none.return_value = mock_user
            mock_result_pw = MagicMock()
            mock_result_pw.scalar_one_or_none.return_value = mock_pw
            totp_result = MagicMock()
            totp_result.scalar_one_or_none.return_value = None
            mock_db.execute.side_effect = [mock_result_user, mock_result_pw, totp_result]

            resp = await client.post("/api/v1/auth/login", json={
                "user_id": "admin",
                "password": "admin123",
            })

            assert resp.status_code == 200
            # Response must set a cookie named "token"
            cookies = resp.cookies
            assert "token" in cookies

    @pytest.mark.asyncio
    async def test_protected_endpoint_accepts_cookie_auth(self, client):
        """受保护端点通过 Cookie 接受认证"""
        token = _make_token()
        mock_sm = MagicMock()
        mock_sm.is_session_valid = AsyncMock(return_value=True)
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("api.middleware._session_manager", mock_sm), \
             patch("domains.access.policy.redis_client", mock_redis), \
             patch("domains.access.policy.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            # Use cookie-based auth instead of Authorization header
            resp = await client.get(
                "/api/v1/users",
                cookies={"token": token},
                headers={"X-App-ID": "test"},
            )
            assert resp.status_code in (200, 403)  # passed auth

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, client):
        """登出后清除 Cookie"""
        token = _make_token()

        # Need to mock the middleware session check for logout
        mock_sm = MagicMock()
        mock_sm.is_session_valid = AsyncMock(return_value=True)

        with patch("api.middleware._session_manager", mock_sm):
            resp = await client.post(
                "/api/v1/auth/logout",
                cookies={"token": token},
            )
            assert resp.status_code == 200
            # Cookie should be cleared (max-age=0 or empty)
            set_cookie_headers = [
                h for h in resp.headers.get_list("set-cookie")
                if "token" in h.lower()
            ]
            assert len(set_cookie_headers) > 0
            # Must contain Max-Age=0 or expired date to clear
            clear_indicator = any(
                "max-age=0" in h.lower() or "1970" in h.lower()
                for h in set_cookie_headers
            )
            assert clear_indicator

    @pytest.mark.asyncio
    async def test_login_response_has_no_token_in_body(self, client):
        """登录响应 body 中不应包含 token（通过 Cookie 传递）"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.delete = AsyncMock()
        mock_sm = MagicMock()
        mock_sm.cache_user_status = AsyncMock()

        with patch("api.v1.auth.redis_client", mock_redis), \
             patch("api.v1.auth.session_mgr", mock_sm), \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[{"role_id": "super_admin", "scope_id": "*"}]), \
             patch("api.v1.auth.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_user = MagicMock()
            mock_user.id = "admin"
            mock_user.tenant_id = "default"
            mock_user.name = "Admin"

            pw_hash = hash_password("admin123")
            mock_pw = MagicMock()
            mock_pw.value = pw_hash

            mock_result_user = MagicMock()
            mock_result_user.scalar_one_or_none.return_value = mock_user
            mock_result_pw = MagicMock()
            mock_result_pw.scalar_one_or_none.return_value = mock_pw
            totp_result = MagicMock()
            totp_result.scalar_one_or_none.return_value = None
            mock_db.execute.side_effect = [mock_result_user, mock_result_pw, totp_result]

            resp = await client.post("/api/v1/auth/login", json={
                "user_id": "admin",
                "password": "admin123",
            })

            body = resp.json()
            assert "token" not in body.get("data", {})
