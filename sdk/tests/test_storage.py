"""测试 TokenStorage — keyring Token 存储"""
from unittest.mock import patch


class TestTokenStorage:
    def test_save_and_get_token(self):
        """保存后可以读取 token"""
        with patch("keyring.set_password") as mock_set, \
             patch("keyring.get_password") as mock_get:
            mock_get.return_value = "jwt-token-123"

            from fablab_sdk.storage import TokenStorage
            storage = TokenStorage()

            storage.save_token("user_001", "jwt-token-123")
            mock_set.assert_called_once_with("fablab-platform", "user_001", "jwt-token-123")

            result = storage.get_token("user_001")
            assert result == "jwt-token-123"
            mock_get.assert_called_once_with("fablab-platform", "user_001")

    def test_get_token_returns_none_when_not_found(self):
        """未存储的 token 返回 None"""
        with patch("keyring.get_password", return_value=None):
            from fablab_sdk.storage import TokenStorage
            storage = TokenStorage()
            assert storage.get_token("unknown_user") is None

    def test_delete_token(self):
        """删除 token"""
        with patch("keyring.delete_password") as mock_del:
            from fablab_sdk.storage import TokenStorage
            storage = TokenStorage()
            storage.delete_token("user_001")
            mock_del.assert_called_once_with("fablab-platform", "user_001")
