"""测试 TokenManager — JWT 签发与验证"""
import time
import pytest


class TestTokenManagerCreate:
    def test_create_token_contains_user_id_and_tenant_id(self):
        from domains.identity.token_manager import TokenManager
        mgr = TokenManager(secret="test-secret")
        token = mgr.create_token(user_id="user_001", tenant_id="fablab")
        payload = mgr.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user_001"
        assert payload["tenant_id"] == "fablab"

    def test_create_token_with_extra_claims(self):
        from domains.identity.token_manager import TokenManager
        mgr = TokenManager(secret="test-secret")
        token = mgr.create_token(user_id="u1", tenant_id="t1", extra={"role": "admin"})
        payload = mgr.verify_token(token)
        assert payload["role"] == "admin"

    def test_create_token_has_iat_and_exp(self):
        from domains.identity.token_manager import TokenManager
        mgr = TokenManager(secret="test-secret")
        token = mgr.create_token(user_id="u1", tenant_id="t1")
        payload = mgr.verify_token(token)
        assert "iat" in payload
        assert "exp" in payload


class TestTokenManagerVerify:
    def test_verify_invalid_token_returns_none(self):
        from domains.identity.token_manager import TokenManager
        mgr = TokenManager(secret="test-secret")
        result = mgr.verify_token("invalid.token.here")
        assert result is None

    def test_verify_empty_string_returns_none(self):
        from domains.identity.token_manager import TokenManager
        mgr = TokenManager(secret="test-secret")
        result = mgr.verify_token("")
        assert result is None

    def test_expired_token_returns_none(self):
        from domains.identity.token_manager import TokenManager
        mgr = TokenManager(secret="test-secret", expire_seconds=1)
        token = mgr.create_token(user_id="user_001", tenant_id="fablab")
        time.sleep(2)
        result = mgr.verify_token(token)
        assert result is None

    def test_wrong_secret_returns_none(self):
        from domains.identity.token_manager import TokenManager
        mgr_a = TokenManager(secret="secret-a")
        mgr_b = TokenManager(secret="secret-b")
        token = mgr_a.create_token(user_id="u1", tenant_id="t1")
        result = mgr_b.verify_token(token)
        assert result is None
