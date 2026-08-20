from redis.asyncio import Redis

from src.redis import client


async def get_redis() -> Redis:
    assert client.redis_client is not None

    return client.redis_client