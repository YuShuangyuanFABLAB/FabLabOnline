"""Task D: 微信 CSRF state 验证 — handle_callback 必须校验 state"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestWechatCSRF:
    """handle_callback 必须验证 state 参数防 CSRF"""

    @pytest.fixture
    def oauth(self):
        with patch("domains.identity.wechat_oauth.redis_client", new_callable=AsyncMock):
            from domains.identity.wechat_oauth import WechatOAuth
            return WechatOAuth(
                app_id="test_id",
                app_secret="test_secret",
                redirect_uri="https://example.com/callback",
            )

    @pytest.mark.asyncio
    async def test_invalid_state_rejected(self, oauth):
        """Redis 中不存在的 state 应被拒绝"""
        oauth.redis.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="[Ii]nvalid.*state"):
            await oauth.handle_callback("some_code", "fake_state")

    @pytest.mark.asyncio
    async def test_consumed_state_rejected(self, oauth):
        """已消费的 state 应被拒绝"""
        oauth.redis.get = AsyncMock(
            return_value=json.dumps({"status": "consumed"})
        )

        with pytest.raises(ValueError, match="[Ii]nvalid.*state"):
            await oauth.handle_callback("some_code", "used_state")

    @pytest.mark.asyncio
    async def test_valid_pending_state_succeeds(self, oauth):
        """有效的 pending state 应正常处理（mock 微信 API 返回 openid）"""
        oauth.redis.get = AsyncMock(
            return_value=json.dumps({"status": "pending"})
        )
        oauth.redis.setex = AsyncMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "openid": "wx_openid_123",
            "access_token": "at_123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            result = await oauth.handle_callback("valid_code", "valid_state")

        assert result["openid"] == "wx_openid_123"
