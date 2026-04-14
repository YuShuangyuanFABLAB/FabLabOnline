"""测试生产部署准备 — CORS + API 文档保护"""
import pytest
from unittest.mock import patch


class TestCORSOrigins:
    """B1: CORS_ORIGINS 配置项控制允许的域名"""

    @pytest.mark.asyncio
    async def test_cors_uses_configured_origins(self):
        """CORS 应使用 CORS_ORIGINS 配置项，而非硬编码 localhost"""
        from httpx import AsyncClient, ASGITransport

        with patch("config.settings.Settings.validate_production"):
            # 模拟生产环境配置
            with patch("config.settings.settings.CORS_ORIGINS", "https://fablab.example.com"):
                # 需要重新导入以应用新配置
                import importlib
                import main
                importlib.reload(main)

                transport = ASGITransport(app=main.app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    # 配置的域名应该被允许
                    resp = await client.options("/health", headers={
                        "Origin": "https://fablab.example.com",
                        "Access-Control-Request-Method": "GET",
                    })
                    allow_origin = resp.headers.get("access-control-allow-origin")
                    assert allow_origin == "https://fablab.example.com"

    @pytest.mark.asyncio
    async def test_cors_rejects_unknown_origin(self):
        """未配置的域名应被 CORS 拒绝"""
        from httpx import AsyncClient, ASGITransport

        with patch("config.settings.Settings.validate_production"):
            with patch("config.settings.settings.CORS_ORIGINS", "https://fablab.example.com"):
                import importlib
                import main
                importlib.reload(main)

                transport = ASGITransport(app=main.app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.options("/health", headers={
                        "Origin": "https://evil.example.com",
                        "Access-Control-Request-Method": "GET",
                    })
                    allow_origin = resp.headers.get("access-control-allow-origin")
                    assert allow_origin is None, "不应允许未配置的域名"


class TestDocsProtection:
    """B3: 生产环境应隐藏 API 文档"""

    @pytest.mark.asyncio
    async def test_docs_disabled_in_production(self):
        """DOCS_ENABLED=False 时 /docs 返回 404"""
        from httpx import AsyncClient, ASGITransport

        with patch("config.settings.Settings.validate_production"):
            with patch("config.settings.settings.DOCS_ENABLED", False):
                import importlib
                import main
                importlib.reload(main)

                transport = ASGITransport(app=main.app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/docs")
                    assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_openapi_disabled_in_production(self):
        """DOCS_ENABLED=False 时 /openapi.json 返回 404"""
        from httpx import AsyncClient, ASGITransport

        with patch("config.settings.Settings.validate_production"):
            with patch("config.settings.settings.DOCS_ENABLED", False):
                import importlib
                import main
                importlib.reload(main)

                transport = ASGITransport(app=main.app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/openapi.json")
                    assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_docs_enabled_in_dev(self):
        """DOCS_ENABLED=True 时 /docs 正常访问"""
        from httpx import AsyncClient, ASGITransport

        with patch("config.settings.Settings.validate_production"):
            with patch("config.settings.settings.DOCS_ENABLED", True):
                import importlib
                import main
                importlib.reload(main)

                transport = ASGITransport(app=main.app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    resp = await client.get("/docs")
                    assert resp.status_code == 200
