import redis.asyncio as redis

from src.config import settings
from src.redis import client


async def create_redis() -> None:
    client.redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


async def close_redis() -> None:
    if client.redis_client:
        await client.redis_client.close()