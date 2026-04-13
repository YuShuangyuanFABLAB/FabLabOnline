"""Phase 4D 测试 — C4 SQL注入 + M1 JSON重构 + M2 心跳去重 + M9 默认值"""
import json
import re
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════════
# C4: SQL 注入防护 — tenant_id 白名单校验
# ═══════════════════════════════════════════════════════════════


class TestSQLInjectionProtection:
    """动态表名必须校验 tenant_id 格式"""

    def test_validate_tenant_id_accepts_alphanumeric(self):
        """合法 tenant_id 通过"""
        from api.v1.events import _validate_tenant_id
        assert _validate_tenant_id("default") is True
        assert _validate_tenant_id("tenant_123") is True
        assert _validate_tenant_id("my-tenant") is True

    def test_validate_tenant_id_rejects_injection(self):
        """SQL 注入字符被拒绝"""
        from api.v1.events import _validate_tenant_id
        assert _validate_tenant_id("'; DROP TABLE users;--") is False
        assert _validate_tenant_id("tenant\" OR 1=1") is False
        assert _validate_tenant_id("t; DELETE FROM events") is False
        assert _validate_tenant_id("tenant id") is False  # 空格

    @pytest.mark.asyncio
    async def test_get_events_rejects_invalid_tenant_id(self):
        """get_events 拒绝非法 tenant_id"""
        from api.v1.events import get_events
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_events("'; DROP TABLE users;--")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_user_activity_rejects_invalid_tenant_id(self):
        """get_user_activity 拒绝非法 tenant_id"""
        from api.v1.analytics import get_user_activity
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_user_activity("evil'; DROP TABLE", "user_001")
        assert exc_info.value.status_code == 400


# ═══════════════════════════════════════════════════════════════
# M1: 登录/登出响应使用 json.dumps 而非字符串拼接
# ═══════════════════════════════════════════════════════════════


class TestLoginResponseSafety:
    """登录响应必须用 json.dumps 构造，不能字符串拼接"""

    @pytest.mark.asyncio
    async def test_login_response_is_valid_json(self):
        """含特殊字符的用户名不破坏 JSON 结构"""
        from api.v1.auth import password_login

        mock_user = MagicMock()
        mock_user.id = 'user"with"quotes'
        mock_user.name = 'name\\with\\backslash'
        mock_user.tenant_id = "default"
        mock_user.deleted_at = None

        with patch("api.v1.auth.async_session") as mock_session, \
             patch("api.v1.auth.redis_client") as mock_redis, \
             patch("api.v1.auth.verify_password", return_value=True), \
             patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.session_mgr") as mock_sm, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[]):

            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.delete = AsyncMock()
            mock_tm.create_token.return_value = "jwt-token"
            mock_sm.cache_user_status = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            # 第一次 execute 返回用户，第二次返回密码
            user_result = MagicMock()
            user_result.scalar_one_or_none.return_value = mock_user
            pw_result = MagicMock()
            pw_config = MagicMock()
            pw_config.value = json.dumps({"hash": "x"})
            pw_result.scalar_one_or_none.return_value = pw_config
            mock_db.execute.side_effect = [user_result, pw_result]

            result = await password_login(
                body=MagicMock(user_id='user"with"quotes', password="pass")
            )

        # 响应体必须是合法 JSON
        parsed = json.loads(result.body.decode())
        assert parsed["data"]["user"]["id"] == 'user"with"quotes'
        assert parsed["data"]["user"]["name"] == 'name\\with\\backslash'


# ═══════════════════════════════════════════════════════════════
# M2: 心跳续签逻辑去重 — _maybe_renew_token 提取
# ═══════════════════════════════════════════════════════════════


class TestHeartbeatDedup:
    """心跳续签逻辑应提取为独立函数"""

    def test_maybe_renew_token_function_exists(self):
        """_maybe_renew_token 函数存在"""
        from api.v1.auth import _maybe_renew_token
        assert callable(_maybe_renew_token)

    def test_maybe_renew_returns_none_when_far_from_expiry(self):
        """Token 远未过期时不续签"""
        from api.v1.auth import _maybe_renew_token

        with patch("api.v1.auth.token_mgr") as mock_tm:
            mock_tm.verify_token.return_value = {
                "exp": int(__import__("time").time()) + 6 * 86400,
            }
            result = _maybe_renew_token("valid-token", "user_001", "default")
            assert result is None
            mock_tm.create_token.assert_not_called()

    def test_maybe_renew_returns_new_token_near_expiry(self):
        """Token 即将过期时续签"""
        from api.v1.auth import _maybe_renew_token

        with patch("api.v1.auth.token_mgr") as mock_tm:
            mock_tm.verify_token.return_value = {
                "exp": int(__import__("time").time()) + 3600,
            }
            mock_tm.create_token.return_value = "new-token"
            result = _maybe_renew_token("old-token", "user_001", "default")
            assert result == "new-token"
            mock_tm.create_token.assert_called_once()

    def test_maybe_renew_returns_none_for_invalid_token(self):
        """无效 token 不续签"""
        from api.v1.auth import _maybe_renew_token

        with patch("api.v1.auth.token_mgr") as mock_tm:
            mock_tm.verify_token.return_value = None
            result = _maybe_renew_token("invalid", "user_001", "default")
            assert result is None


# ═══════════════════════════════════════════════════════════════
# M9: Role._INIT_DEFAULTS 与 server_default 一致性
# ═══════════════════════════════════════════════════════════════


class TestRoleDefaultsConsistency:
    """Role 模型的 _INIT_DEFAULTS 必须与 server_default 一致"""

    def test_role_is_system_defaults_to_false(self):
        """is_system 默认值应为 False（与 server_default='false' 一致）"""
        from models.role import Role
        assert Role._INIT_DEFAULTS.get("is_system") is False
