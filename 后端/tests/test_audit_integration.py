"""测试审计日志补全 — H2 TDD"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestConfigAuditLog:
    """config.py update_config 必须调用 write_audit_log"""

    @pytest.mark.asyncio
    async def test_update_config_calls_audit_log(self):
        """PUT /config 写操作记录审计日志"""
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
             patch("api.v1.config.get_policy") as mock_policy, \
             patch("api.v1.config.write_audit_log", new_callable=AsyncMock) as mock_audit:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_redis.delete = AsyncMock()
            mock_policy_inst = MagicMock()
            mock_policy_inst.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = mock_policy_inst

            result = await update_config(
                request, scope="global", scope_id=None, key="test_key", value={"new": "data"}
            )

            assert result["success"] is True
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args[1]
            assert call_kwargs["action"] == "update"
            assert call_kwargs["resource_type"] == "config"
            assert call_kwargs["resource_id"] == "test_key"
            assert call_kwargs["ip_address"] == "127.0.0.1"


class TestAppAuditLog:
    """apps.py register_app 必须调用 write_audit_log"""

    @pytest.mark.asyncio
    async def test_register_app_calls_audit_log(self):
        """POST /apps 写操作记录审计日志"""
        from api.v1.apps import register_app

        request = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "TestClient/1.0"}

        mock_app = MagicMock()
        mock_app.id = "test-app"
        mock_app.name = "Test App"
        mock_app.app_key = "test_key"

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        with patch("api.v1.apps.async_session") as mock_session, \
             patch("api.v1.apps.get_policy") as mock_policy, \
             patch("api.v1.apps.write_audit_log", new_callable=AsyncMock) as mock_audit:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            # Make db.refresh set the mock_app attributes
            async def fake_refresh(obj):
                pass
            mock_db.refresh = AsyncMock(side_effect=fake_refresh)

            mock_policy_inst = MagicMock()
            mock_policy_inst.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = mock_policy_inst

            result = await register_app(
                request, app_id="test-app", name="Test App", app_key="test_key"
            )

            assert result["success"] is True
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args[1]
            assert call_kwargs["action"] == "create"
            assert call_kwargs["resource_type"] == "app"
            assert call_kwargs["ip_address"] == "192.168.1.1"


class TestAuditIncludesIpAddress:
    """所有写操作的审计日志必须包含 ip_address"""

    @pytest.mark.asyncio
    async def test_all_audit_calls_include_ip(self):
        """验证审计调用包含客户端 IP"""
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
             patch("api.v1.users.get_policy") as mock_policy, \
             patch("api.v1.users.write_audit_log", new_callable=AsyncMock) as mock_audit, \
             patch("api.v1.users.SessionManager") as mock_sm_cls:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_policy_inst = MagicMock()
            mock_policy_inst.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = mock_policy_inst

            mock_sm_inst = MagicMock()
            mock_sm_inst.invalidate_user_status = AsyncMock()
            mock_sm_cls.return_value = mock_sm_inst

            result = await update_user_status("user_001", request, status="inactive")

            assert result["success"] is True
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args[1]
            assert call_kwargs.get("ip_address") == "10.0.0.5"
            assert call_kwargs.get("user_agent") == "Mozilla/5.0"
