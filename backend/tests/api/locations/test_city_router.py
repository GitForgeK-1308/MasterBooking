import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.locations.models import City
from src.locations.repository import LocationRepository


@pytest.mark.anyio
async def test_get_cities_returns_only_active_sorted(
    ac: AsyncClient,
    city: City,
    second_city: City,
    inactive_city: City,
):
    response = await ac.get(
        "/locations/cities"
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["name"]
        for item in data
    ] == [
        "Jurmala",
        "Riga",
    ]

    assert all(
        item["is_active"]
        for item in data
    )

    assert str(
        inactive_city.id
    ) not in {
        item["id"]
        for item in data
    }


@pytest.mark.anyio
async def test_create_city_as_admin(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        "/locations/cities",
        headers=admin_auth_headers,
        json={
            "name": "  rIGA   cITY  ",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Riga City"
    assert data["is_active"] is True
    assert "id" in data

    repository = LocationRepository(
        db_session
    )

    city = await repository.get_city_by_name(
        "Riga City"
    )

    assert city is not None
    assert city.id == uuid.UUID(
        data["id"]
    )


@pytest.mark.anyio
async def test_create_city_without_token(
    ac: AsyncClient,
):
    response = await ac.post(
        "/locations/cities",
        json={
            "name": "Riga",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_city_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        "/locations/cities",
        headers=auth_headers,
        json={
            "name": "Riga",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            "Доступ разрешён только "
            "администраторам!"
        )
    }


@pytest.mark.anyio
async def test_create_city_duplicate(
    ac: AsyncClient,
    city: City,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/locations/cities",
        headers=admin_auth_headers,
        json={
            "name": "  rIGA  ",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Такой город уже существует!"
        )
    }


@pytest.mark.anyio
async def test_create_city_invalid_name(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/locations/cities",
        headers=admin_auth_headers,
        json={
            "name": "R",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_city(
    ac: AsyncClient,
    city: City,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        f"/locations/cities/{city.id}",
        headers=admin_auth_headers,
        json={
            "name": "  new   rIGA ",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(
        city.id
    )
    assert data["name"] == "New Riga"
    assert data["is_active"] is False

    repository = LocationRepository(
        db_session
    )

    city_from_database = (
        await repository.get_city_by_id(
            city.id
        )
    )

    assert city_from_database is not None
    assert (
        city_from_database.name
        == "New Riga"
    )
    assert (
        city_from_database.is_active
        is False
    )

    public_response = await ac.get(
        "/locations/cities"
    )

    assert public_response.status_code == 200

    assert str(
        city.id
    ) not in {
        item["id"]
        for item in public_response.json()
    }


@pytest.mark.anyio
async def test_update_city_not_found(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    city_id = uuid.uuid4()

    response = await ac.patch(
        f"/locations/cities/{city_id}",
        headers=admin_auth_headers,
        json={
            "name": "Riga",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Город не найден!"
    }


@pytest.mark.anyio
async def test_update_city_duplicate_name(
    ac: AsyncClient,
    city: City,
    second_city: City,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/locations/cities/{second_city.id}",
        headers=admin_auth_headers,
        json={
            "name": "  rIGA ",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Такой город уже существует!"
        )
    }


@pytest.mark.anyio
async def test_update_city_invalid_uuid(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/locations/cities/not-a-uuid",
        headers=admin_auth_headers,
        json={
            "name": "Riga",
        },
    )

    assert response.status_code == 422