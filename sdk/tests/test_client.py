"""测试 FablabClient + AuthManager — 主客户端 + 认证"""
from unittest.mock import MagicMock, patch, AsyncMock


class TestFablabClientInit:
    def test_client_creates_sub_components(self):
        """FablabClient 初始化后包含 auth 和 tracking"""
        from fablab_sdk.client import FablabClient
        client = FablabClient(app_key="test-app", server_url="http://localhost:8000")

        assert client.app_key == "test-app"
        assert client.server_url == "http://localhost:8000"
        assert client.auth is not None
        assert client.tracking is not None

    def test_client_has_api_with_base_url(self):
        """客户端 API 使用正确的 base_url"""
        from fablab_sdk.client import FablabClient
        client = FablabClient(app_key="test-app", server_url="http://localhost:8000")
        assert client.api is not None


class TestAuthManager:
    def test_check_auth_returns_false_when_no_token(self):
        """无本地 token 时 check_auth 返回 False"""
        from fablab_sdk.client import FablabClient

        with patch("fablab_sdk.auth.TokenStorage") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage.get_token.return_value = None
            mock_storage_cls.return_value = mock_storage

            client = FablabClient(app_key="test-app", server_url="http://localhost:8000")
            assert client.auth.check_auth() is False

    def test_check_auth_returns_true_with_valid_token(self):
        """有本地 token 且服务器验证通过时返回 True"""
        from fablab_sdk.client import FablabClient

        with patch("fablab_sdk.auth.TokenStorage") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage.get_token.return_value = "valid-jwt-token"
            mock_storage_cls.return_value = mock_storage

            with patch("fablab_sdk.auth.httpx.AsyncClient") as mock_httpx:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_httpx_instance = AsyncMock()
                mock_httpx_instance.get = AsyncMock(return_value=mock_resp)
                mock_httpx.return_value.__aenter__ = AsyncMock(return_value=mock_httpx_instance)
                mock_httpx.return_value.__aexit__ = AsyncMock(return_value=False)

                client = FablabClient(app_key="test-app", server_url="http://localhost:8000")
                assert client.auth.check_auth() is True

    def test_get_user_returns_none_when_not_authenticated(self):
        """未认证时 get_user 返回 None"""
        from fablab_sdk.client import FablabClient

        with patch("fablab_sdk.auth.TokenStorage") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage.get_token.return_value = None
            mock_storage_cls.return_value = mock_storage

            client = FablabClient(app_key="test-app", server_url="http://localhost:8000")
            assert client.get_user() is None
