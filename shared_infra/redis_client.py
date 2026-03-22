"""Shared Redis client for caching and pub/sub."""

import redis.asyncio as aioredis
from shared_infra.config import get_settings

settings = get_settings()

redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> aioredis.Redis:
    return redis_client
