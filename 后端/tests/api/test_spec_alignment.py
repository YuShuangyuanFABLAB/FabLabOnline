"""测试中间件提取 X-App-ID + 心跳滑动过期 + 事件查询端点 + 分区预创建"""
import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestMiddlewareAppId:
    """中间件应提取 X-App-ID 头并写入 request.state"""

    @pytest.mark.asyncio
    async def test_app_id_written_to_state(self):
        """携带 X-App-ID 的请求 → request.state.app_id 被设置"""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from starlette.responses import JSONResponse

        call_result = {}

        app = FastAPI()
        from api.middleware import AuthMiddleware
        app.add_middleware(AuthMiddleware)

        @app.get("/api/v1/test")
        async def test_route(request: Request):
            call_result["app_id"] = getattr(request.state, "app_id", "unknown")
            return JSONResponse({"app_id": call_result["app_id"]})

        with patch("api.middleware._token_manager") as mock_tm, \
             patch("api.middleware._session_manager") as mock_sm:
            mock_tm.verify_token.return_value = {"sub": "u1", "tenant_id": "t1"}
            mock_sm.is_session_valid = AsyncMock(return_value=True)

            client = TestClient(app)
            client.get("/api/v1/test", headers={
                "Authorization": "Bearer fake",
                "X-App-ID": "ppt-generator",
            })

        assert call_result.get("app_id") == "ppt-generator"

    @pytest.mark.asyncio
    async def test_missing_app_id_defaults_unknown(self):
        """未携带 X-App-ID → app_id 默认 unknown"""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from starlette.responses import JSONResponse

        call_result = {}

        app = FastAPI()
        from api.middleware import AuthMiddleware
        app.add_middleware(AuthMiddleware)

        @app.get("/api/v1/test")
        async def test_route(request: Request):
            call_result["app_id"] = getattr(request.state, "app_id", "unknown")
            return JSONResponse({"app_id": call_result["app_id"]})

        with patch("api.middleware._token_manager") as mock_tm, \
             patch("api.middleware._session_manager") as mock_sm:
            mock_tm.verify_token.return_value = {"sub": "u1", "tenant_id": "t1"}
            mock_sm.is_session_valid = AsyncMock(return_value=True)

            client = TestClient(app)
            client.get("/api/v1/test", headers={
                "Authorization": "Bearer fake",
            })

        assert call_result.get("app_id") == "unknown"


class TestHeartbeatSlidingExpiration:
    """心跳滑动过期 — 距过期 < 1 天时自动签发新 Token"""

    @pytest.mark.asyncio
    async def test_heartbeat_returns_new_token_near_expiry(self):
        """Token 即将过期时，心跳返回新 token"""
        from api.v1.auth import heartbeat

        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "user_001"
        request.state.tenant_id = "default"
        request.headers = {"Authorization": "Bearer old-token"}
        request.cookies = {}

        with patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.async_session") as mock_session, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[{"role_id": "super_admin", "scope_id": "*"}]):
            mock_tm.verify_token.return_value = {
                "sub": "user_001",
                "tenant_id": "default",
                "exp": int(time.time()) + 36000,  # ~10 小时后过期
            }
            mock_tm.create_token.return_value = "new-jwt-token"

            # Mock DB for user name lookup
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            result = await heartbeat(request)

            assert result.body is not None  # Response object with cookie
            mock_tm.create_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_heartbeat_no_renew_when_far_from_expiry(self):
        """Token 还有很长时间过期时，心跳不签发新 token"""
        from api.v1.auth import heartbeat

        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "user_001"
        request.state.tenant_id = "default"
        request.headers = {"Authorization": "Bearer valid-token"}
        request.cookies = {}

        with patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.async_session") as mock_session, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[]):
            mock_tm.verify_token.return_value = {
                "sub": "user_001",
                "tenant_id": "default",
                "exp": int(time.time()) + 6 * 86400,
            }
            mock_tm.create_token.return_value = "should-not-be-called"

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            result = await heartbeat(request)

            assert result["data"]["alive"] is True
            assert "token" not in result["data"]
            mock_tm.create_token.assert_not_called()


class TestEventsQueryEndpoint:
    """GET /api/v1/events — 管理查询端点"""

    @pytest.mark.asyncio
    async def test_events_query_returns_list(self):
        """GET /events 返回事件列表"""
        from api.v1.events import query_events

        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"

        with patch("api.v1.events.get_events", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"event_type": "app.start"}]
            result = await query_events(request, event_type="app.start", limit=20)
            assert result["success"] is True


class TestUserActivityEndpoint:
    """GET /api/v1/analytics/users/{id}/activity — 单用户活动日志"""

    @pytest.mark.asyncio
    async def test_user_activity_returns_data(self):
        """返回指定用户的活动日志"""
        from api.v1.analytics import user_activity

        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"

        with patch("api.v1.analytics.get_user_activity", new_callable=AsyncMock) as mock_get, \
             patch("api.v1.analytics.get_policy") as mock_policy:
            mock_get.return_value = {"events": []}
            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy
            result = await user_activity("user_001", request)
            assert result["success"] is True


class TestPartitionPreCreation:
    """启动时预创建未来 3 个月分区"""

    @pytest.mark.asyncio
    async def test_ensure_partitions_on_startup(self):
        """ensure_future_partitions 创建未来 3 个月分区"""
        from domains.events.store import ensure_future_partitions

        with patch("domains.events.store.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            await ensure_future_partitions()

            # 应该执行 CREATE TABLE IF NOT EXISTS（至少调用一次 execute）
            assert mock_db.execute.called
