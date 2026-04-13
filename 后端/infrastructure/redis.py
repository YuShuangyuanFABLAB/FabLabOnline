import redis.asyncio as aioredis
from config.settings import settings

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
)


async def get_redis() -> aioredis.Redis:
    return redis_client
