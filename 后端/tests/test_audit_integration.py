"""测试审计日志补全 — H2 TDD（已迁移至 BackgroundTasks）"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.background import BackgroundTasks


def _make_bg():
    return BackgroundTasks()


class TestConfigAuditLog:
    """config.py update_config 必须通过 BackgroundTasks 调度审计日志"""

    @pytest.mark.asyncio
    async def test_update_config_calls_audit_log(self):
        """PUT /config 写操作通过 BackgroundTasks 调度审计日志"""
        from api.v1.config import update_config

        request = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "TestClient/1.0"}

        mock_config = MagicMock()
        mock_config.value = {"old": "data"}

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_config)
        ))
        mock_db.commit = AsyncMock()

        with patch("api.v1.config.async_session") as mock_session, \
             patch("api.v1.config.redis_client") as mock_redis, \
             patch("api.v1.config.require_permission", new_callable=AsyncMock) as mock_perm, \
             patch("api.v1.config.write_audit_log", new_callable=AsyncMock) as mock_audit:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_redis.delete = AsyncMock()

            bg = _make_bg()
            result = await update_config(
                request, body=MagicMock(
                    scope="global", scope_id=None, key="test_key",
                    value={"new": "data"},
                ), background_tasks=bg,
            )

            assert result["success"] is True
            mock_audit.assert_not_awaited()
            assert len(bg.tasks) == 1


class TestAppAuditLog:
    """apps.py register_app 必须通过 BackgroundTasks 调度审计日志"""

    @pytest.mark.asyncio
    async def test_register_app_calls_audit_log(self):
        """POST /apps 写操作通过 BackgroundTasks 调度审计日志"""
        from api.v1.apps import register_app

        request = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "TestClient/1.0"}

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("api.v1.apps.async_session") as mock_session, \
             patch("api.v1.apps.require_permission", new_callable=AsyncMock) as mock_perm, \
             patch("api.v1.apps.write_audit_log", new_callable=AsyncMock) as mock_audit:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            async def fake_refresh(obj):
                pass
            mock_db.refresh = AsyncMock(side_effect=fake_refresh)

            bg = _make_bg()
            result = await register_app(
                request, body=MagicMock(
                    app_id="test-app", name="Test App", app_key="test_key",
                ), background_tasks=bg,
            )

            assert result["success"] is True
            mock_audit.assert_not_awaited()
            assert len(bg.tasks) == 1


class TestAuditIncludesIpAddress:
    """BackgroundTasks 调度的审计日志必须包含 ip_address"""

    @pytest.mark.asyncio
    async def test_all_audit_calls_include_ip(self):
        """验证 BackgroundTasks 中调度的审计参数包含客户端 IP"""
        from api.v1.users import update_user_status

        request = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "10.0.0.5"
        request.headers = {"user-agent": "Mozilla/5.0"}

        mock_user = MagicMock()
        mock_user.id = "user_001"
        mock_user.status = "active"
        mock_user.tenant_id = "default"

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        ))
        mock_db.commit = AsyncMock()

        with patch("api.v1.users.async_session") as mock_session, \
             patch("api.v1.users.require_permission", new_callable=AsyncMock) as mock_perm, \
             patch("api.v1.users.write_audit_log", new_callable=AsyncMock) as mock_audit, \
             patch("api.v1.users.SessionManager") as mock_sm_cls:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_sm_inst = MagicMock()
            mock_sm_inst.invalidate_user_status = AsyncMock()
            mock_sm_cls.return_value = mock_sm_inst

            bg = _make_bg()
            result = await update_user_status(
                "user_001", request, body=MagicMock(status="inactive"),
                background_tasks=bg,
            )

            assert result["success"] is True
            mock_audit.assert_not_awaited()
            assert len(bg.tasks) == 1
            task = bg.tasks[0]
            assert task.func is mock_audit
            call_kwargs = task.kwargs
            assert call_kwargs.get("ip_address") == "10.0.0.5"
            assert call_kwargs.get("user_agent") == "Mozilla/5.0"
