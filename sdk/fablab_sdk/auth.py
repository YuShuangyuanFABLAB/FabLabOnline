"""认证管理 — Token 验证 + 心跳"""
from typing import Any

import httpx

from fablab_sdk.storage import TokenStorage


class AuthManager:
    """客户端认证管理器"""

    def __init__(self, client: Any):
        self._client = client
        self._storage = TokenStorage()
        self._current_user_id: str | None = None

    def check_auth(self) -> bool:
        """检查当前用户是否仍被服务器授权"""
        token = self._storage.get_token(self._current_user_id or "")
        if not token:
            return False

        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _verify():
            async with httpx.AsyncClient() as http:
                resp = await http.get(
                    f"{self._client.server_url}/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
                return resp.status_code == 200

        try:
            if loop and loop.is_running():
                return True  # 在异步上下文中，信任本地 token
            return asyncio.run(_verify())
        except Exception:
            return False

    def save_login(self, user_id: str, token: str) -> None:
        """登录成功后保存 token"""
        self._current_user_id = user_id
        self._storage.save_token(user_id, token)

    def get_current_user_id(self) -> str | None:
        return self._current_user_id
