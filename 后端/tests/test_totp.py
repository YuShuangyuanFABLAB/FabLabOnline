"""TOTP 二次验证 — super_admin 登录必须验证 TOTP 码"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from domains.identity.totp import generate_totp_secret, verify_totp_code, get_totp_uri


class TestTotpSecret:
    """TOTP 密钥生成与验证"""

    def test_generate_secret_returns_base32(self):
        """生成的密钥应为 Base32 编码字符串"""
        secret = generate_totp_secret()
        assert len(secret) == 32  # 20 bytes → 32 base32 chars
        import re
        assert re.match(r'^[A-Z2-7]+$', secret)

    def test_generate_unique_secrets(self):
        """每次生成不同的密钥"""
        a = generate_totp_secret()
        b = generate_totp_secret()
        assert a != b

    def test_verify_valid_code(self):
        """正确的 TOTP 码应通过验证"""
        secret = generate_totp_secret()
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert verify_totp_code(secret, code) is True

    def test_verify_invalid_code(self):
        """错误的 TOTP 码应被拒绝"""
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "000000") is False

    def test_get_totp_uri_contains_secret(self):
        """URI 应包含密钥和用户标识"""
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, "admin", "FabLab")
        assert secret in uri
        assert "FabLab" in uri
        assert "admin" in uri


class TestTotpSetupEndpoint:
    """POST /api/v1/auth/totp/setup — 生成 TOTP 密钥"""

    def test_setup_returns_secret_and_uri(self):
        """已认证用户请求 setup 应返回密钥和 URI"""
        from fastapi.testclient import TestClient
        from main import app

        with (
            patch("api.middleware._token_manager.verify_token",
                  return_value={"sub": "admin", "tenant_id": "default"}),
            patch("api.middleware._session_manager.is_session_valid",
                  new_callable=AsyncMock, return_value=True),
            patch("api.v1.auth.redis_client", new_callable=AsyncMock),
            patch("api.v1.auth.async_session") as mock_session,
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            # 模拟没有已有密钥
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.commit = AsyncMock()

            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/api/v1/auth/totp/setup", cookies={"token": "valid"})

        assert resp.status_code == 200
        body = resp.json()
        assert "secret" in body
        assert "uri" in body


class TestTotpLoginFlow:
    """super_admin 登录启用 TOTP 时需要二次验证"""

    def test_login_with_totp_enabled_returns_challenge(self):
        """已启用 TOTP 的用户登录应返回 challenge 而非 token"""
        from fastapi.testclient import TestClient
        from main import app

        # 准备密码 hash
        pw_hash = json.dumps(hash_password("pass1234"))
        # 准备 TOTP secret
        secret = generate_totp_secret()
        totp_hash = json.dumps({"secret": secret, "enabled": True})

        with (
            patch("api.v1.auth.redis_client", new_callable=AsyncMock) as mock_redis,
            patch("api.v1.auth.async_session") as mock_session,
        ):
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.delete = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            # 第一次查询: 用户存在
            user_result = MagicMock()
            user_row = MagicMock()
            user_row.id = "admin"
            user_row.name = "管理员"
            user_row.tenant_id = "default"
            user_result.scalar_one_or_none.return_value = user_row

            # 第二次查询: 密码 hash
            pw_result = MagicMock()
            pw_row = MagicMock()
            pw_row.value = pw_hash
            pw_result.scalar_one_or_none.return_value = pw_row

            # 第三次查询: TOTP secret
            totp_result = MagicMock()
            totp_row = MagicMock()
            totp_row.value = totp_hash
            totp_result.scalar_one_or_none.return_value = totp_row

            mock_db.execute = AsyncMock(side_effect=[user_result, pw_result, totp_result])

            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/api/v1/auth/login", json={
                "user_id": "admin", "password": "pass1234"
            })

        assert resp.status_code == 200
        body = resp.json()
        assert body.get("totp_required") is True
        assert "totp_challenge" in body

    def test_login_without_totp_returns_token(self):
        """未启用 TOTP 的用户登录应直接返回 token"""
        from fastapi.testclient import TestClient
        from main import app

        pw_hash = json.dumps(hash_password("pass1234"))

        with (
            patch("api.v1.auth.redis_client", new_callable=AsyncMock) as mock_redis,
            patch("api.v1.auth.async_session") as mock_session,
            patch("api.v1.auth.session_mgr.cache_user_status", new_callable=AsyncMock),
            patch("api.v1.auth.get_user_roles",
                  new_callable=AsyncMock, return_value=[{"role_id": "super_admin"}]),
        ):
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.delete = AsyncMock()

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            user_result = MagicMock()
            user_row = MagicMock()
            user_row.id = "user1"
            user_row.name = "教师"
            user_row.tenant_id = "default"
            user_result.scalar_one_or_none.return_value = user_row

            pw_result = MagicMock()
            pw_row = MagicMock()
            pw_row.value = pw_hash
            pw_result.scalar_one_or_none.return_value = pw_row

            # 无 TOTP
            totp_result = MagicMock()
            totp_result.scalar_one_or_none.return_value = None

            mock_db.execute = AsyncMock(side_effect=[user_result, pw_result, totp_result])

            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/api/v1/auth/login", json={
                "user_id": "user1", "password": "pass1234"
            })

        assert resp.status_code == 200
        assert "token" in resp.cookies or "data" in resp.json()


class TestTotpVerifyEndpoint:
    """POST /api/v1/auth/totp/verify — 验证 TOTP 码并签发 token"""

    def test_verify_valid_code_returns_token(self):
        """正确的 TOTP 码应返回 JWT token"""
        from fastapi.testclient import TestClient
        from main import app

        secret = generate_totp_secret()
        import pyotp
        code = pyotp.TOTP(secret).now()

        with (
            patch("api.v1.auth.redis_client", new_callable=AsyncMock) as mock_redis,
            patch("api.v1.auth.session_mgr.cache_user_status", new_callable=AsyncMock),
            patch("api.v1.auth.get_user_roles",
                  new_callable=AsyncMock, return_value=[{"role_id": "super_admin"}]),
        ):
            mock_redis.get = AsyncMock(return_value=json.dumps({
                "user_id": "admin",
                "tenant_id": "default",
                "totp_secret": secret,
            }))
            mock_redis.delete = AsyncMock()

            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/api/v1/auth/totp/verify", json={
                "challenge": "test123",
                "code": code,
            })

        assert resp.status_code == 200

    def test_verify_invalid_code_rejected(self):
        """错误的 TOTP 码应被拒绝"""
        from fastapi.testclient import TestClient
        from main import app

        secret = generate_totp_secret()

        with (
            patch("api.v1.auth.redis_client", new_callable=AsyncMock) as mock_redis,
        ):
            mock_redis.get = AsyncMock(return_value=json.dumps({
                "user_id": "admin",
                "tenant_id": "default",
                "totp_secret": secret,
            }))

            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post("/api/v1/auth/totp/verify", json={
                "challenge": "test123",
                "code": "000000",
            })

        assert resp.status_code == 401


from domains.identity.password import hash_password
