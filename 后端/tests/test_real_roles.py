"""测试登录和心跳返回真实角色 — H4 TDD"""
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLoginReturnsRealRoles:
    """密码登录应返回 user_roles 表中的真实角色"""

    @pytest.mark.asyncio
    async def test_login_returns_roles_from_db(self):
        """有角色的用户 → 返回真实角色列表"""
        from api.v1.auth import password_login, LoginRequest

        body = LoginRequest(user_id="admin", password="admin123")

        mock_user = MagicMock()
        mock_user.id = "admin"
        mock_user.name = "系统管理员"
        mock_user.tenant_id = "default"

        mock_pw_config = MagicMock()
        mock_pw_config.value = {"algorithm": "pbkdf2_sha256", "hash": "any"}

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_pw_config)),
        ])
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch("api.v1.auth.async_session", return_value=mock_db), \
             patch("api.v1.auth.redis_client") as mock_redis, \
             patch("api.v1.auth.verify_password", return_value=True), \
             patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.session_mgr") as mock_sm, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock) as mock_roles:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.delete = AsyncMock()
            mock_tm.create_token.return_value = "jwt-token"
            mock_sm.cache_user_status = AsyncMock()
            mock_roles.return_value = [
                {"role_id": "super_admin", "scope_id": "*"},
            ]

            response = await password_login(body)

            # 验证调用了 get_user_roles
            mock_roles.assert_called_once_with("admin")

            # 验证响应包含真实角色
            body_data = json.loads(response.body)
            roles = body_data["data"]["user"]["roles"]
            assert roles == ["super_admin"]

    @pytest.mark.asyncio
    async def test_login_user_with_no_roles(self):
        """无角色的用户 → 返回空数组"""
        from api.v1.auth import password_login, LoginRequest

        body = LoginRequest(user_id="newuser", password="pass123")

        mock_user = MagicMock()
        mock_user.id = "newuser"
        mock_user.name = "新用户"
        mock_user.tenant_id = "default"

        mock_pw_config = MagicMock()
        mock_pw_config.value = {"algorithm": "pbkdf2_sha256", "hash": "any"}

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_pw_config)),
        ])
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch("api.v1.auth.async_session", return_value=mock_db), \
             patch("api.v1.auth.redis_client") as mock_redis, \
             patch("api.v1.auth.verify_password", return_value=True), \
             patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.session_mgr") as mock_sm, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock) as mock_roles:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.delete = AsyncMock()
            mock_tm.create_token.return_value = "jwt-token"
            mock_sm.cache_user_status = AsyncMock()
            mock_roles.return_value = []

            response = await password_login(body)

            body_data = json.loads(response.body)
            roles = body_data["data"]["user"]["roles"]
            assert roles == []


class TestHeartbeatReturnsRealRoles:
    """心跳应返回 user_roles 表中的真实角色"""

    @pytest.mark.asyncio
    async def test_heartbeat_returns_roles_from_db(self):
        """心跳返回真实角色"""
        from api.v1.auth import heartbeat

        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"
        request.headers = {"Authorization": "Bearer valid-token"}
        request.cookies = {}

        with patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.async_session") as mock_session, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock) as mock_roles:
            mock_tm.verify_token.return_value = {
                "sub": "admin_001",
                "tenant_id": "default",
                "exp": int(time.time()) + 6 * 86400,
            }
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = MagicMock(name="管理员")
            mock_db.execute.return_value = mock_result

            mock_roles.return_value = [
                {"role_id": "super_admin", "scope_id": "*"},
                {"role_id": "admin", "scope_id": "hq"},
            ]

            result = await heartbeat(request)

            assert set(result["data"]["roles"]) == {"super_admin", "admin"}
            mock_roles.assert_called_once_with("admin_001")

    @pytest.mark.asyncio
    async def test_heartbeat_user_with_no_roles(self):
        """无角色的用户 → 心跳返回空角色"""
        from api.v1.auth import heartbeat

        request = MagicMock()
        request.state = MagicMock()
        request.state.user_id = "nobody"
        request.state.tenant_id = "default"
        request.headers = {"Authorization": "Bearer valid-token"}
        request.cookies = {}

        with patch("api.v1.auth.token_mgr") as mock_tm, \
             patch("api.v1.auth.async_session") as mock_session, \
             patch("api.v1.auth.get_user_roles", new_callable=AsyncMock) as mock_roles:
            mock_tm.verify_token.return_value = {
                "sub": "nobody",
                "tenant_id": "default",
                "exp": int(time.time()) + 6 * 86400,
            }
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            mock_roles.return_value = []

            result = await heartbeat(request)

            assert result["data"]["roles"] == []
