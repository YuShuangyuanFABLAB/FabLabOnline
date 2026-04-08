"""测试校区 API — 认证拦截 + 权限"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from domains.identity.token_manager import TokenManager
from config.settings import settings


def _make_token(user_id="admin", tenant_id="default"):
    mgr = TokenManager(secret=settings.JWT_SECRET_KEY)
    return mgr.create_token(user_id=user_id, tenant_id=tenant_id)


def _mock_policy_and_session():
    """返回 context manager，mock 掉 Redis + DB + session"""
    mock_sm = MagicMock()
    mock_sm.is_session_valid = AsyncMock(return_value=True)
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    return mock_sm, mock_redis


class TestCampusesAPI:
    @pytest.mark.asyncio
    async def test_list_campuses_without_token_returns_401(self, client):
        resp = await client.get("/api/v1/campuses")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_campus_without_token_returns_401(self, client):
        resp = await client.post("/api/v1/campuses?campus_id=test&name=TestCampus")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_campus_without_token_returns_401(self, client):
        resp = await client.delete("/api/v1/campuses/nonexistent")
        assert resp.status_code == 401
