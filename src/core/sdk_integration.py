# -*- coding: utf-8 -*-
"""
SDK 集成模块
处理 FabLab SDK 的登录认证、离线缓存逻辑
"""

import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 离线缓存有效期：7 天
OFFLINE_CACHE_SECONDS = 7 * 86400


class SdkIntegration:
    """SDK 集成管理器 — 处理认证和离线缓存"""

    def __init__(self, client, cache_dir: Path):
        """
        Args:
            client: FablabClient 实例
            cache_dir: 缓存目录路径
        """
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def check_auth(self) -> bool:
        """
        检查认证状态

        1. 检查本地 token
        2. 向服务端验证
        3. 服务端不可达时检查离线缓存（7 天有效期）

        Returns:
            True = 已认证，False = 需要登录
        """
        saved = self.client.auth.get_saved_user()
        if saved is None:
            return False

        user_id, token = saved
        try:
            valid = asyncio.run(self.client.auth.check_auth())
            if valid:
                self._update_cache(user_id)
            return valid
        except Exception as e:
            logger.warning(f"服务端验证失败，检查离线缓存: {e}")
            return self._check_offline_cache(user_id)

    def get_qrcode_url(self) -> Optional[str]:
        """获取微信扫码登录二维码 URL"""
        return self.client.auth.get_qrcode_url()

    def on_login_success(self, user_id: str, token: str) -> None:
        """登录成功后保存 token 并更新缓存"""
        self.client.auth.save_login(user_id, token)
        self._update_cache(user_id)

    def _update_cache(self, user_id: str) -> None:
        """更新离线缓存"""
        cache_file = self.cache_dir / "auth_cache.json"
        data = {
            "user_id": user_id,
            "timestamp": time.time(),
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")

    def _check_offline_cache(self, user_id: str) -> bool:
        """检查离线缓存是否在有效期内"""
        cache_file = self.cache_dir / "auth_cache.json"
        if not cache_file.exists():
            return False

        data = json.loads(cache_file.read_text(encoding="utf-8"))
        if data.get("user_id") != user_id:
            return False

        elapsed = time.time() - data.get("timestamp", 0)
        return elapsed < OFFLINE_CACHE_SECONDS
