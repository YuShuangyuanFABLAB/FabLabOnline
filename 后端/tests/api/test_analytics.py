"""测试分析 API — 认证拦截"""
import pytest

from domains.identity.token_manager import TokenManager
from config.settings import settings


def _make_token(user_id="admin", tenant_id="default"):
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


class TestAnalyticsAPI:
    @pytest.mark.asyncio
    async def test_dashboard_without_auth(self, client):
        resp = await client.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_usage_without_auth(self, client):
        resp = await client.get("/api/v1/analytics/usage?start=2026-01-01&end=2026-01-31")
        assert resp.status_code == 401
