import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.locations.models import City, District
from src.locations.repository import LocationRepository


@pytest.mark.anyio
async def test_get_districts_returns_only_active_sorted(
    ac: AsyncClient,
    city: City,
    district: District,
    second_district: District,
    inactive_district: District,
):
    response = await ac.get((f"/locations/cities/{city.id}/districts"))

    assert response.status_code == 200

    data = response.json()

    assert [item["name"] for item in data] == [
        "Agenskalns",
        "Centrs",
    ]

    assert all(item["is_active"] for item in data)

    assert str(inactive_district.id) not in {item["id"] for item in data}


@pytest.mark.anyio
async def test_get_districts_inactive_city(
    ac: AsyncClient,
    inactive_city: City,
):
    response = await ac.get((f"/locations/cities/{inactive_city.id}/districts"))

    assert response.status_code == 404
    assert response.json() == {"detail": "Город не найден!"}


@pytest.mark.anyio
async def test_get_districts_city_not_found(
    ac: AsyncClient,
):
    city_id = uuid.uuid4()

    response = await ac.get((f"/locations/cities/{city_id}/districts"))

    assert response.status_code == 404
    assert response.json() == {"detail": "Город не найден!"}


@pytest.mark.anyio
async def test_create_district_as_admin(
    ac: AsyncClient,
    city: City,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        "/locations/districts",
        headers=admin_auth_headers,
        json={
            "city_id": str(city.id),
            "name": "  old   town ",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["city_id"] == str(city.id)
    assert data["name"] == "Old Town"
    assert data["is_active"] is True

    repository = LocationRepository(db_session)

    district = await repository.get_district_by_name(
        city_id=city.id,
        name="Old Town",
    )

    assert district is not None
    assert district.id == uuid.UUID(data["id"])


@pytest.mark.anyio
async def test_create_district_city_not_found(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    city_id = uuid.uuid4()

    response = await ac.post(
        "/locations/districts",
        headers=admin_auth_headers,
        json={
            "city_id": str(city_id),
            "name": "Centrs",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Город не найден!"}


@pytest.mark.anyio
async def test_create_district_as_client_forbidden(
    ac: AsyncClient,
    city: City,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        "/locations/districts",
        headers=auth_headers,
        json={
            "city_id": str(city.id),
            "name": "Centrs",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": ("Доступ разрешён только администраторам!")}


@pytest.mark.anyio
async def test_create_district_duplicate(
    ac: AsyncClient,
    city: City,
    district: District,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/locations/districts",
        headers=admin_auth_headers,
        json={
            "city_id": str(city.id),
            "name": "  cENTRS ",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("Такой район уже существует в этом городе!")}


@pytest.mark.anyio
async def test_create_district_invalid_name(
    ac: AsyncClient,
    city: City,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/locations/districts",
        headers=admin_auth_headers,
        json={
            "city_id": str(city.id),
            "name": "A",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_district(
    ac: AsyncClient,
    city: City,
    district: District,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        (f"/locations/districts/{district.id}"),
        headers=admin_auth_headers,
        json={
            "name": "  old   centrs ",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(district.id)
    assert data["name"] == "Old Centrs"
    assert data["is_active"] is False

    repository = LocationRepository(db_session)

    district_from_database = await repository.get_district_by_id(district.id)

    assert district_from_database is not None
    assert district_from_database.name == "Old Centrs"
    assert district_from_database.is_active is False

    public_response = await ac.get((f"/locations/cities/{city.id}/districts"))

    assert public_response.status_code == 200

    assert str(district.id) not in {item["id"] for item in public_response.json()}


@pytest.mark.anyio
async def test_update_district_not_found(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    district_id = uuid.uuid4()

    response = await ac.patch(
        (f"/locations/districts/{district_id}"),
        headers=admin_auth_headers,
        json={
            "name": "Centrs",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Район не найден!"}


@pytest.mark.anyio
async def test_update_district_duplicate_name(
    ac: AsyncClient,
    city: City,
    district: District,
    second_district: District,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (f"/locations/districts/{second_district.id}"),
        headers=admin_auth_headers,
        json={
            "name": "  cENTRS ",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("Такой район уже существует в этом городе!")}
