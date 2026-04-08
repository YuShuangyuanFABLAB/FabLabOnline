"""测试事件 API — 认证拦截"""
import pytest

from domains.identity.token_manager import TokenManager
from config.settings import settings


def _make_token(user_id="admin", tenant_id="default"):
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


class TestEventsAPI:
    @pytest.mark.asyncio
    async def test_batch_report_without_auth(self, client):
        resp = await client.post("/api/v1/events/batch", json=[])
        assert resp.status_code == 401
