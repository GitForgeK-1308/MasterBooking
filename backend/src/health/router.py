from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.redis.dependencies import get_redis

router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
async def healthcheck(
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
):
    try:
        await session.execute(text("SELECT 1"))

        await redis.ping()

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис временно недоступен",
        ) from error

    return {
        "status": "ok",
        "database": "ok",
        "redis": "ok",
    }
