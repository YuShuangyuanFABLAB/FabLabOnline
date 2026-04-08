"""事件消费者 — poll + ack + 幂等检查"""
import structlog
from sqlalchemy import text, select

from infrastructure.database import async_session
from infrastructure.redis import redis_client
from models.event import EventConsumer

logger = structlog.get_logger()


async def poll_events(consumer_name: str, limit: int = 100) -> list[dict]:
    """获取该 consumer 尚未消费的事件（带行级锁）"""
    async with async_session() as db:
        result = await db.execute(
            select(EventConsumer).where(EventConsumer.consumer_name == consumer_name)
        )
        progress = result.scalar_one_or_none()
        last_seq = progress.last_event_seq if progress else 0

        events_result = await db.execute(
            text("""
                SELECT * FROM events
                WHERE event_seq > :last_seq
                ORDER BY event_seq LIMIT :limit
                FOR UPDATE SKIP LOCKED
            """),
            {"last_seq": last_seq, "limit": limit},
        )
        rows = events_result.mappings().all()
        return [dict(row) for row in rows]


async def ack_events(consumer_name: str, last_seq: int, current_version: int):
    """确认消费进度（带乐观锁校验 version）"""
    async with async_session() as db:
        result = await db.execute(
            text("""
                UPDATE event_consumers
                SET last_event_seq = :last_seq,
                    version = version + 1,
                    updated_at = NOW()
                WHERE consumer_name = :consumer_name AND version = :current_version
            """),
            {"last_seq": last_seq, "consumer_name": consumer_name, "current_version": current_version},
        )
        if result.rowcount == 0:
            raise ConcurrencyError(f"Consumer {consumer_name} version mismatch, retry poll")
        await db.commit()


async def is_processed(consumer_name: str, event_id: str) -> bool:
    """幂等检查：Redis Set 记录已处理的 event_id（TTL 7天）"""
    key = f"consumer:{consumer_name}:processed"
    added = await redis_client.sadd(key, event_id)
    if added:
        await redis_client.expire(key, 7 * 24 * 3600)
        return False  # 新事件
    return True  # 已处理过


class ConcurrencyError(Exception):
    pass
