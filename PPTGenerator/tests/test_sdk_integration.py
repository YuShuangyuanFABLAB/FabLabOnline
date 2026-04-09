"""测试 SdkIntegration — SDK 登录认证 + 离线缓存逻辑"""
import time
import json
from unittest.mock import MagicMock, AsyncMock


class TestCheckAuth:
    """check_auth() 检查本地 token 有效性"""

    def test_returns_true_when_valid_token(self, tmp_path):
        """本地有 token 且服务端验证通过 → 返回 True"""
        from src.core.sdk_integration import SdkIntegration

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.check_auth = AsyncMock(return_value=True)
        mock_client.auth.get_saved_user = MagicMock(return_value=("user_001", "valid-token"))

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        result = integration.check_auth()

        assert result is True

    def test_returns_false_when_no_token(self, tmp_path):
        """本地无 token → 返回 False"""
        from src.core.sdk_integration import SdkIntegration

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.get_saved_user = MagicMock(return_value=None)

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        result = integration.check_auth()

        assert result is False

    def test_returns_false_when_token_invalid(self, tmp_path):
        """本地有 token 但服务端验证失败 → 返回 False"""
        from src.core.sdk_integration import SdkIntegration

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.check_auth = AsyncMock(return_value=False)
        mock_client.auth.get_saved_user = MagicMock(return_value=("user_001", "expired-token"))

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        result = integration.check_auth()

        assert result is False


class TestOfflineCache:
    """离线授权缓存 — 7 天有效期"""

    def test_offline_cache_allows_start_within_7_days(self, tmp_path):
        """7 天内的缓存允许离线启动"""
        from src.core.sdk_integration import SdkIntegration

        cache_file = tmp_path / "auth_cache.json"
        cache_data = {
            "user_id": "user_001",
            "timestamp": time.time(),  # 刚刚
        }
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.check_auth = AsyncMock(side_effect=Exception("Network error"))
        mock_client.auth.get_saved_user = MagicMock(return_value=("user_001", "valid-token"))

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        result = integration.check_auth()

        assert result is True  # 离线缓存有效

    def test_offline_cache_expired_after_7_days(self, tmp_path):
        """超过 7 天的缓存不允许离线启动"""
        from src.core.sdk_integration import SdkIntegration

        cache_file = tmp_path / "auth_cache.json"
        cache_data = {
            "user_id": "user_001",
            "timestamp": time.time() - 8 * 86400,  # 8 天前
        }
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.check_auth = AsyncMock(side_effect=Exception("Network error"))
        mock_client.auth.get_saved_user = MagicMock(return_value=("user_001", "valid-token"))

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        result = integration.check_auth()

        assert result is False  # 缓存过期

    def test_auth_success_updates_cache(self, tmp_path):
        """认证成功后更新离线缓存"""
        from src.core.sdk_integration import SdkIntegration

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.check_auth = AsyncMock(return_value=True)
        mock_client.auth.get_saved_user = MagicMock(return_value=("user_001", "valid-token"))

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        integration.check_auth()

        cache_file = tmp_path / "auth_cache.json"
        assert cache_file.exists()
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["user_id"] == "user_001"
        assert time.time() - data["timestamp"] < 5  # 刚刚写入


class TestLoginFlow:
    """login() 登录流程 — 获取二维码 + 轮询状态"""

    def test_get_qrcode_url(self, tmp_path):
        """login() 获取二维码 URL"""
        from src.core.sdk_integration import SdkIntegration

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.get_qrcode_url = MagicMock(return_value="https://wx.qq.com/qr?state=abc")

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        result = integration.get_qrcode_url()

        assert result == "https://wx.qq.com/qr?state=abc"
        mock_client.auth.get_qrcode_url.assert_called_once()

    def test_login_saves_token_on_success(self, tmp_path):
        """登录成功后保存 token"""
        from src.core.sdk_integration import SdkIntegration

        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.auth.save_login = MagicMock()

        integration = SdkIntegration(client=mock_client, cache_dir=tmp_path)
        integration.on_login_success("user_001", "new-token")

        mock_client.auth.save_login.assert_called_once_with("user_001", "new-token")

        # Should also update offline cache
        cache_file = tmp_path / "auth_cache.json"
        assert cache_file.exists()
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["user_id"] == "user_001"
