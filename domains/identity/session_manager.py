"""会话管理 — Redis 缓存 + DB fallback"""
from sqlalchemy import select

from infrastructure.database import async_session
from infrastructure.redis import redis_client
from models.user import User


class SessionManager:
    """用户状态缓存（Redis TTL 5 分钟）。

    - cache_user_status: 写入 Redis
    - get_user_status: 从 Redis 读
    - invalidate_user_status: 写时主动失效（禁用用户时调用）
    - is_session_valid: 检查用户是否仍被授权
    """

    CACHE_TTL = 300  # 5 分钟

    def __init__(self):
        self.redis = redis_client

    async def cache_user_status(self, user_id: str, status: str):
        """缓存用户状态到 Redis"""
        await self.redis.setex(f"user_status:{user_id}", self.CACHE_TTL, status)

    async def get_user_status(self, user_id: str) -> str | None:
        return await self.redis.get(f"user_status:{user_id}")

    async def invalidate_user_status(self, user_id: str):
        """写时主动失效缓存（用户禁用时调用）"""
        await self.redis.delete(f"user_status:{user_id}")

    async def is_session_valid(self, user_id: str) -> bool:
        """检查用户是否仍被授权（Redis 缓存 → DB fallback）"""
        cached = await self.get_user_status(user_id)
        if cached is not None:
            return cached == "active"
        # 缓存未命中（Redis 重启或 key 过期）→ 回源 DB
        async with async_session() as session:
            result = await session.execute(
                select(User.status).where(
                    User.id == user_id,
                    User.deleted_at.is_(None),
                )
            )
            status = result.scalar_one_or_none()
            if status is None:
                return False
            # 回填缓存
            await self.cache_user_status(user_id, status)
            return status == "active"
