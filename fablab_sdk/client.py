"""FabLab Platform 客户端 — 统一接入层"""
from fablab_sdk.auth import AuthManager
from fablab_sdk.tracking import EventReporter


class _APIWrapper:
    """API 调用封装"""

    def __init__(self, client: "FablabClient"):
        self._client = client

    async def batch_report(self, events: list[dict]) -> dict:
        """批量上报事件"""
        import httpx
        token = self._client.auth._storage.get_token(
            self._client.auth._current_user_id or ""
        )
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        headers["X-App-ID"] = self._client.app_key

        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self._client.server_url}/api/v1/events/batch",
                json=events,
                headers=headers,
            )
            return resp.json()


class FablabClient:
    """FabLab Platform 客户端"""

    def __init__(self, app_key: str, server_url: str):
        self.app_key = app_key
        self.server_url = server_url
        self.api = _APIWrapper(self)
        self.auth = AuthManager(self)
        self.tracking = EventReporter(client=self)

    def get_user(self) -> dict | None:
        """获取当前登录用户信息"""
        user_id = self.auth.get_current_user_id()
        if not user_id:
            return None
        return {"id": user_id}

    def login(self) -> dict | None:
        """微信扫码登录（需桌面端 UI 配合）"""
        # 登录流程需要 UI 层（PyQt5）配合
        # SDK 只提供 API 调用，不直接弹出对话框
        # Task 8 中由 PPT 软件集成
        return None
