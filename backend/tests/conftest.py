from unittest.mock import AsyncMock

import pytest

from src.main import app
from src.redis.dependencies import get_redis

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.client",
    "tests.fixtures.users",
    "tests.fixtures.locations",
    "tests.fixtures.categories",
    "tests.fixtures.tags",
    "tests.fixtures.masters",
    "tests.fixtures.offerings",
    "tests.fixtures.offering_images",
    "tests.fixtures.master_schedule",
    "tests.fixtures.bookings",
    "tests.fixtures.reviews",
]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def redis_client_mock() -> AsyncMock:
    redis = AsyncMock()

    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.ping = AsyncMock(return_value=True)

    return redis


@pytest.fixture(autouse=True)
def override_redis_dependency(
    redis_client_mock: AsyncMock,
):
    async def get_test_redis():
        return redis_client_mock

    app.dependency_overrides[get_redis] = get_test_redis

    yield

    app.dependency_overrides.pop(
        get_redis,
        None,
    )