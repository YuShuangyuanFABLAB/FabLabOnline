"""微信开放平台 OAuth 对接 — 扫码登录"""
import json
import secrets

import httpx

from infrastructure.redis import redis_client


class WechatOAuth:
    """微信扫码登录流程。

    所有扫码会话状态存储在 Redis（TTL 5 分钟），支持多实例部署。
    回调地址配置在微信开放平台：https://<domain>/api/v1/auth/wechat/callback
    """

    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"

    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        redirect_uri: str | None = None,
    ):
        from config.settings import settings
        self.app_id = app_id or settings.WECHAT_APP_ID
        self.app_secret = app_secret or settings.WECHAT_APP_SECRET
        self.redirect_uri = redirect_uri or settings.WECHAT_REDIRECT_URI
        self.redis = redis_client

    async def create_qr_session(self) -> dict:
        """创建扫码会话，返回二维码 URL 和 state"""
        state = secrets.token_urlsafe(32)
        url = (
            f"{self.AUTHORIZE_URL}"
            f"?appid={self.app_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=snsapi_login"
            f"&state={state}"
        )
        # 存入 Redis（TTL 5 分钟 = 二维码有效期）
        await self.redis.setex(
            f"wx_qr_state:{state}", 300,
            json.dumps({"status": "pending"}),
        )
        return {"url": url, "state": state}

    async def handle_callback(self, code: str, state: str) -> dict:
        """处理微信回调，用 code 换 token，返回 openid"""
        # CSRF 防护：验证 state 参数
        state_key = f"wx_qr_state:{state}"
        state_data = await self.redis.get(state_key)
        if not state_data or json.loads(state_data).get("status") != "pending":
            raise ValueError("Invalid or expired state parameter")
        # 标记为 consumed（一次性使用）
        await self.redis.setex(state_key, 300, json.dumps({"status": "consumed"}))

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.TOKEN_URL,
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            data = resp.json()

        if "openid" not in data:
            raise ValueError(f"WeChat OAuth failed: {data}")

        result = {
            "status": "confirmed",
            "openid": data["openid"],
            "unionid": data.get("unionid"),
            "access_token": data["access_token"],
        }
        await self.redis.setex(
            f"wx_qr_state:{state}", 300,
            json.dumps(result),
        )
        return result

    async def get_session_status(self, state: str) -> dict:
        """查询扫码会话状态"""
        raw = await self.redis.get(f"wx_qr_state:{state}")
        if raw is None:
            return {"status": "not_found"}
        return json.loads(raw)

    async def set_session_token(self, state: str, token: str, user: dict):
        """扫码成功后写入 JWT + 用户信息"""
        await self.redis.setex(
            f"wx_qr_state:{state}", 300,
            json.dumps({"status": "authenticated", "token": token, "user": user}),
        )
