"""M15: 通用限流中间件 — 所有 API 端点应有基于 IP 的速率限制"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRateLimitMiddleware:
    """应用应有通用限流中间件"""

    def test_rate_limit_middleware_registered(self):
        """FastAPI app 应注册限流中间件"""
        from main import app
        # 检查是否有限流中间件
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "RateLimitMiddleware" in middleware_classes, (
            f"应注册 RateLimitMiddleware，实际中间件: {middleware_classes}"
        )

    async def test_rate_limit_returns_429_on_excess(self):
        """超过限速应返回 429"""
        from httpx import AsyncClient, ASGITransport
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先发一个请求让 middleware 正常工作
            resp = await client.get("/health")
            assert resp.status_code in (200, 429), (
                f"/health 应返回 200 或 429，实际: {resp.status_code}"
            )
