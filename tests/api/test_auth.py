"""测试 AuthMiddleware — JWT 校验 + 豁免路径"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock

from main import app
from domains.identity.token_manager import TokenManager


def _make_token(user_id="u1", tenant_id="t1"):
    """使用与 settings 一致的默认 secret 签发 token"""
    from config.settings import settings
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAuthMiddlewareExemptPaths:
    @pytest.mark.asyncio
    async def test_health_is_exempt(self, client):
        """health 端点不需要认证"""
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_docs_is_exempt(self, client):
        """docs 端点不需要认证"""
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_qrcode_is_exempt(self, client):
        """获取二维码不需要认证"""
        with patch("api.v1.auth.oauth") as mock_oauth:
            mock_oauth.create_qr_session = AsyncMock(return_value={"url": "https://wx.example.com", "state": "abc"})
            resp = await client.post("/api/v1/auth/qrcode")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_qrcode_status_is_exempt(self, client):
        """轮询扫码状态不需要认证"""
        with patch("api.v1.auth.oauth") as mock_oauth:
            mock_oauth.get_session_status = AsyncMock(return_value={"status": "pending"})
            resp = await client.get("/api/v1/auth/qrcode/test-state/status")
            assert resp.status_code == 200


class TestAuthMiddlewareProtectedPaths:
    @pytest.mark.asyncio
    async def test_protected_without_token_returns_401(self, client):
        """受保护路径无 token 返回 401"""
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_with_invalid_token_returns_401(self, client):
        """无效 token 返回 401"""
        resp = await client.get("/api/v1/users", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_with_valid_token_passes_auth(self, client):
        """有效 token 通过认证层（不会返回 401）"""
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

            resp = await client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {token}", "X-App-ID": "test"},
            )
            # 通过了认证层（不会返回 401），可能是 403（无权限）
            assert resp.status_code in (200, 403)
