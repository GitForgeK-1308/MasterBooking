from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.database.session import get_async_session
from src.main import app


@pytest.fixture
async def ac(
    db_session,
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(
            get_async_session,
            None,
        )
