"""测试 WechatOAuth + SessionManager — 微信OAuth与会话管理"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestWechatOAuth:
    def test_create_qr_session_returns_url_and_state(self):
        """创建扫码会话应返回 URL 和 state"""
        from domains.identity.wechat_oauth import WechatOAuth
        with patch("domains.identity.wechat_oauth.redis_client") as mock_redis:
            mock_redis.setex = AsyncMock()
            oauth = WechatOAuth(app_id="test_app_id", app_secret="test_secret", redirect_uri="https://example.com/callback")
            import asyncio
            result = asyncio.run(oauth.create_qr_session())
            assert "url" in result
            assert "state" in result
            assert "test_app_id" in result["url"]
            assert "open.weixin.qq.com" in result["url"]

    def test_handle_callback_exchanges_code_for_token(self):
        """回调应换取 openid"""
        from domains.identity.wechat_oauth import WechatOAuth
        with patch("domains.identity.wechat_oauth.redis_client") as mock_redis:
            mock_redis.setex = AsyncMock()
            oauth = WechatOAuth(app_id="test_app_id", app_secret="test_secret", redirect_uri="https://example.com/callback")

            mock_response = MagicMock()
            mock_response.json.return_value = {"openid": "wx_openid_123", "access_token": "wx_at"}

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                import asyncio
                result = asyncio.run(oauth.handle_callback("auth_code", "state_abc"))
                assert result["openid"] == "wx_openid_123"

    def test_handle_callback_raises_on_missing_openid(self):
        """微信返回错误时应抛异常"""
        from domains.identity.wechat_oauth import WechatOAuth
        with patch("domains.identity.wechat_oauth.redis_client") as mock_redis:
            oauth = WechatOAuth(app_id="test_app_id", app_secret="test_secret", redirect_uri="https://example.com/callback")

            mock_response = MagicMock()
            mock_response.json.return_value = {"errcode": 40029, "errmsg": "invalid code"}

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                import asyncio
                with pytest.raises(ValueError, match="WeChat OAuth"):
                    asyncio.run(oauth.handle_callback("bad_code", "state"))

    def test_get_session_status_returns_pending(self):
        """查询未扫码的会话应返回 pending"""
        from domains.identity.wechat_oauth import WechatOAuth
        with patch("domains.identity.wechat_oauth.redis_client") as mock_redis:
            import json
            mock_redis.get = AsyncMock(return_value=json.dumps({"status": "pending"}))
            oauth = WechatOAuth(app_id="test", app_secret="s", redirect_uri="http://x")
            import asyncio
            result = asyncio.run(oauth.get_session_status("state_123"))
            assert result["status"] == "pending"

    def test_get_session_status_not_found(self):
        """查询不存在的会话应返回 not_found"""
        from domains.identity.wechat_oauth import WechatOAuth
        with patch("domains.identity.wechat_oauth.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            oauth = WechatOAuth(app_id="test", app_secret="s", redirect_uri="http://x")
            import asyncio
            result = asyncio.run(oauth.get_session_status("nonexistent"))
            assert result["status"] == "not_found"


class TestSessionManager:
    def test_cache_and_get_user_status(self):
        """缓存用户状态后应能读取"""
        from domains.identity.session_manager import SessionManager
        with patch("domains.identity.session_manager.redis_client") as mock_redis:
            mock_redis.setex = AsyncMock()
            mock_redis.get = AsyncMock(return_value="active")
            mgr = SessionManager()
            import asyncio
            asyncio.run(mgr.cache_user_status("user_1", "active"))
            status = asyncio.run(mgr.get_user_status("user_1"))
            assert status == "active"

    def test_invalidate_user_status_deletes_key(self):
        """失效缓存应调用 delete"""
        from domains.identity.session_manager import SessionManager
        with patch("domains.identity.session_manager.redis_client") as mock_redis:
            mock_redis.delete = AsyncMock()
            mgr = SessionManager()
            import asyncio
            asyncio.run(mgr.invalidate_user_status("user_1"))
            mock_redis.delete.assert_called_once()

    def test_is_session_valid_returns_true_for_active(self):
        """活跃用户应返回 True"""
        from domains.identity.session_manager import SessionManager
        with patch("domains.identity.session_manager.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="active")
            mgr = SessionManager()
            import asyncio
            result = asyncio.run(mgr.is_session_valid("user_1"))
            assert result is True

    def test_is_session_valid_returns_false_for_disabled(self):
        """禁用用户应返回 False"""
        from domains.identity.session_manager import SessionManager
        with patch("domains.identity.session_manager.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value="disabled")
            mgr = SessionManager()
            import asyncio
            result = asyncio.run(mgr.is_session_valid("user_1"))
            assert result is False
