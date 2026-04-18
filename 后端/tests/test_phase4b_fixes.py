"""Phase 4B 安全加固测试 — C2/H2/H3/H7"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.background import BackgroundTasks


# ── C2/H7: JWT 密钥启动校验 ──


class TestJWTSecretValidation:
    """C2+H7: 生产环境 JWT 密钥必须强校验"""

    def test_default_secret_rejected_in_production(self):
        """生产环境 (DEBUG=False) 不允许默认密钥"""
        import config.settings as settings_mod
        s = settings_mod.Settings(DEBUG=False, JWT_SECRET_KEY="change-me-in-production")
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            s.validate_production()

    def test_short_secret_rejected(self):
        """密钥少于 32 字符应被拒绝"""
        import config.settings as settings_mod
        s = settings_mod.Settings(DEBUG=False, JWT_SECRET_KEY="short")
        with pytest.raises(ValueError, match="32"):
            s.validate_production()

    def test_strong_secret_accepted(self):
        """强密钥应正常通过"""
        import config.settings as settings_mod
        s = settings_mod.Settings(DEBUG=False, JWT_SECRET_KEY="a" * 64)
        s.validate_production()  # 不应抛出异常

    def test_default_secret_allowed_in_debug(self):
        """开发模式 (DEBUG=True) 允许默认密钥"""
        import config.settings as settings_mod
        s = settings_mod.Settings(DEBUG=True, JWT_SECRET_KEY="change-me-in-production")
        s.validate_production()  # 不应抛出异常


# ── H2: apps.py 注册应用应返回 app_secret ──


class TestAppsReturnSecret:
    """H2: register_app 应返回 app_secret（仅此一次）"""

    @patch("api.v1.apps.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.apps.require_permission", new_callable=AsyncMock)
    @patch("api.v1.apps.async_session")
    async def test_register_app_returns_secret(
        self, mock_db, mock_perm, mock_audit
    ):
        """注册应用后应返回 app_secret 明文（仅注册时可见）"""
        app_obj = MagicMock()
        app_obj.id = "test-app"
        app_obj.name = "测试应用"
        app_obj.app_key = "test_key"
        app_obj.app_secret_hash = "hashed_secret"

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.add = MagicMock()
        mock_ctx.commit = AsyncMock()
        mock_ctx.refresh = AsyncMock()
        mock_db.return_value = mock_ctx

        from api.v1.apps import register_app, RegisterAppRequest
        request = MagicMock()
        request.state.tenant_id = "default"
        request.state.user_id = "admin"
        request.client = MagicMock(host="127.0.0.1")
        request.headers = {"user-agent": "test"}

        body = RegisterAppRequest(app_id="test-app", name="测试应用", app_key="test_key")
        bg = BackgroundTasks()
        result = await register_app(request, body, bg)

        data = result.get("data", result) if isinstance(result, dict) else {}
        assert "app_secret" in data, (
            f"register_app 应返回 app_secret 字段，实际: {data}"
        )
        # secret 应该是明文，不是 hash
        assert data["app_secret"] != "hashed_secret", (
            "app_secret 应返回明文，不是 hash"
        )


# ── H3: analytics.py user_activity 端点需要权限校验 ──


class TestAnalyticsPermissionCheck:
    """H3: user_activity 端点必须进行权限校验"""

    @patch("api.v1.analytics.get_user_activity", new_callable=AsyncMock, return_value={"user_id": "u1", "events": []})
    @patch("api.v1.analytics.require_permission", new_callable=AsyncMock)
    async def test_user_activity_checks_permission(
        self, mock_perm, mock_get_activity
    ):
        """user_activity 必须调用 require_permission"""
        from api.v1.analytics import user_activity
        request = MagicMock()
        request.state.tenant_id = "default"
        request.state.user_id = "admin"

        await user_activity("u1", request)

        mock_perm.assert_called_once()

    @patch("api.v1.analytics.get_user_activity", new_callable=AsyncMock, return_value={"user_id": "u1", "events": []})
    @patch("api.v1.analytics.require_permission", new_callable=AsyncMock)
    async def test_user_activity_denies_without_permission(
        self, mock_perm, mock_get_activity
    ):
        """无权限时 user_activity 应返回 403"""
        from fastapi import HTTPException
        mock_perm.side_effect = HTTPException(status_code=403, detail="Permission denied")

        from api.v1.analytics import user_activity
        request = MagicMock()
        request.state.tenant_id = "default"
        request.state.user_id = "admin"

        with pytest.raises(HTTPException) as exc_info:
            await user_activity("u1", request)
        assert exc_info.value.status_code == 403
