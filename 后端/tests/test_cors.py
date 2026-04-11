"""测试 CORS 配置 — TDD"""
import pytest


class TestCORS:
    """H5: FastAPI 必须配置 CORS 限制"""

    def test_cors_allows_same_origin(self):
        """CORS 中间件已添加到 app"""
        from main import app
        # Check that CORSMiddleware is in the middleware stack
        middleware_classes = [m.cls.__name__ if hasattr(m, 'cls') else str(m) for m in app.user_middleware]
        has_cors = any('CORSMiddleware' in str(c) for c in middleware_classes)
        assert has_cors, "CORSMiddleware not found in app middleware stack"

    @pytest.mark.asyncio
    async def test_cors_preflight_returns_correct_headers(self):
        """OPTIONS 预检请求返回正确的 CORS 头"""
        from httpx import AsyncClient, ASGITransport
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.options("/health", headers={
                "Origin": "http://localhost",
                "Access-Control-Request-Method": "GET",
            })
            # CORS should add these headers
            assert resp.headers.get("access-control-allow-origin") is not None
