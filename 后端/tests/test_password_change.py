"""Task F: PUT /api/v1/auth/password — 密码修改"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from domains.identity.password import hash_password


def _patch_auth():
    """修补认证中间件，使请求通过"""
    return (
        patch("api.middleware._token_manager.verify_token",
              return_value={"sub": "admin", "tenant_id": "default"}),
        patch("api.middleware._session_manager.is_session_valid",
              new_callable=AsyncMock, return_value=True),
        patch("api.v1.auth.redis_client", new_callable=AsyncMock),
    )


class TestPasswordChange:
    """密码修改端点测试"""

    @pytest.fixture
    def mock_db_session(self):
        with patch("api.v1.auth.async_session") as mock_session_ctx:
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            yield mock_db

    def _make_request(self, client, old_pw: str, new_pw: str):
        return client.put(
            "/api/v1/auth/password",
            json={"old_password": old_pw, "new_password": new_pw},
            cookies={"token": "valid_token"},
        )

    def test_change_password_success(self, mock_db_session):
        """正确旧密码 → 200 + success"""
        from fastapi.testclient import TestClient
        from main import app

        pw_hash = json.dumps(hash_password("oldPass123"))

        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.value = pw_hash
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()

        auth_patches = _patch_auth()
        with contextlib.ExitStack() as stack:
            for p in auth_patches:
                stack.enter_context(p)
            client = TestClient(app, raise_server_exceptions=False)
            resp = self._make_request(client, "oldPass123", "newPass45678")

        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_wrong_old_password_rejected(self, mock_db_session):
        """错误旧密码 → 401"""
        from fastapi.testclient import TestClient
        from main import app

        pw_hash = json.dumps(hash_password("correctPass"))

        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.value = pw_hash
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        auth_patches = _patch_auth()
        with contextlib.ExitStack() as stack:
            for p in auth_patches:
                stack.enter_context(p)
            client = TestClient(app, raise_server_exceptions=False)
            resp = self._make_request(client, "wrongPass", "newPass45678")

        assert resp.status_code == 401

    def test_no_token_rejected(self):
        """无 token → 401"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.put(
            "/api/v1/auth/password",
            json={"old_password": "old", "new_password": "newnewnew"},
        )
        assert resp.status_code in (401, 403)

    def test_new_password_too_short_rejected(self, mock_db_session):
        """新密码 < 8 字符 → 422"""
        from fastapi.testclient import TestClient
        from main import app

        auth_patches = _patch_auth()
        with contextlib.ExitStack() as stack:
            for p in auth_patches:
                stack.enter_context(p)
            client = TestClient(app, raise_server_exceptions=False)
            resp = self._make_request(client, "oldPass123", "short")

        assert resp.status_code == 422


import contextlib
