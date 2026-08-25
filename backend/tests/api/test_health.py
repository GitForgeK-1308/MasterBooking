import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_healthcheck(
    ac: AsyncClient,
):
    response = await ac.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "redis": "ok",
    }