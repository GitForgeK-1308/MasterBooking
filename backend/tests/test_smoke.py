import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_cities_empty(
    ac: AsyncClient,
):
    response = await ac.get(
        "/locations/cities"
    )

    assert response.status_code == 200
    assert response.json() == []