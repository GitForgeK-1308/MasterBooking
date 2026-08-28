import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.locations.models import City, District
from src.masters.models import Master
from src.masters.repository import MasterRepository
from src.users.models import User, UserRole
from src.users.repository import UserRepository

MASTER_PROFILE_DATA = {
    "description": ("Professional beauty specialist with several years of experience."),
    "experience": 5,
    "education": "Beauty Academy",
}


@pytest.mark.anyio
async def test_create_master_profile(
    ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json=MASTER_PROFILE_DATA,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == user.first_name
    assert data["last_name"] == user.last_name
    assert data["description"] == MASTER_PROFILE_DATA["description"]
    assert data["experience"] == 5
    assert data["education"] == "Beauty Academy"
    assert data["city_id"] is None
    assert data["district_id"] is None
    assert data["is_active"] is True
    assert data["phone"] == user.phone

    master_repository = MasterRepository(db_session)

    master = await master_repository.get_by_user_id(user.id)

    assert master is not None

    user_repository = UserRepository(db_session)

    user_from_database = await user_repository.get_by_id(user.id)

    assert user_from_database is not None
    assert user_from_database.role == UserRole.MASTER


@pytest.mark.anyio
async def test_create_master_profile_with_location(
    ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
    city: City,
    district: District,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(city.id),
            "district_id": str(district.id),
            "address": "Main Street 10",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["city_id"] == str(city.id)
    assert data["district_id"] == str(district.id)
    assert data["city"] == city.name
    assert data["district"] == district.name
    assert data["address"] == "Main Street 10"


@pytest.mark.anyio
async def test_create_master_profile_without_token(
    ac: AsyncClient,
):
    response = await ac.post(
        "/masters/profile",
        json=MASTER_PROFILE_DATA,
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_master_profile_inactive_user(
    ac: AsyncClient,
    inactive_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/profile",
        headers=inactive_auth_headers,
        json=MASTER_PROFILE_DATA,
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_master_profile_duplicate(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/profile",
        headers=master_auth_headers,
        json=MASTER_PROFILE_DATA,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("Профиль мастера уже существует!")}


@pytest.mark.anyio
async def test_create_master_profile_only_city(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    city: City,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(city.id),
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": ("Город и район должны быть выбраны вместе.")}


@pytest.mark.anyio
async def test_create_master_profile_city_not_found(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    district: District,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(uuid.uuid4()),
            "district_id": str(district.id),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ("Город не найден или недоступен!")}


@pytest.mark.anyio
async def test_create_master_profile_district_not_found(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    city: City,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(city.id),
            "district_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ("Район не найден или недоступен!")}


@pytest.mark.anyio
async def test_create_master_profile_location_mismatch(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    second_city: City,
    district: District,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(second_city.id),
            "district_id": str(district.id),
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": ("Выбранный район не относится к выбранному городу!")
    }


@pytest.mark.anyio
async def test_create_master_profile_inactive_city(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    inactive_city: City,
    inactive_city_district: District,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(inactive_city.id),
            "district_id": str(inactive_city_district.id),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ("Город не найден или недоступен!")}


@pytest.mark.anyio
async def test_create_master_profile_inactive_district(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    city: City,
    inactive_district: District,
):
    response = await ac.post(
        "/masters/profile",
        headers=auth_headers,
        json={
            **MASTER_PROFILE_DATA,
            "city_id": str(city.id),
            "district_id": str(inactive_district.id),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ("Район не найден или недоступен!")}


@pytest.mark.anyio
async def test_get_my_master_profile(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me",
        headers=master_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(master.id)
    assert data["first_name"] == "Anna"
    assert data["last_name"] == "Petrova"
    assert data["phone"] == "+37120000001"


@pytest.mark.anyio
async def test_get_my_master_profile_as_client(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": ("Доступ разрешён только мастерам!")}


@pytest.mark.anyio
async def test_get_my_master_profile_not_found(
    ac: AsyncClient,
    master_without_profile_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me",
        headers=master_without_profile_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ("Профиль мастера не найден!")}


@pytest.mark.anyio
async def test_update_my_master_profile(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        "/masters/me",
        headers=master_auth_headers,
        json={
            "description": ("Updated professional description."),
            "experience": 8,
            "education": "Updated Academy",
            "address": "New Street 20",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["description"] == "Updated professional description."
    assert data["experience"] == 8
    assert data["education"] == "Updated Academy"
    assert data["address"] == "New Street 20"

    repository = MasterRepository(db_session)

    master_from_database = await repository.get_by_id(master.id)

    assert master_from_database is not None
    assert master_from_database.experience == 8


@pytest.mark.anyio
async def test_update_my_master_location(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    second_city: City,
    db_session: AsyncSession,
):
    second_district = District(
        city_id=second_city.id,
        name="Second District",
    )

    db_session.add(second_district)
    await db_session.commit()
    await db_session.refresh(second_district)

    response = await ac.patch(
        "/masters/me",
        headers=master_auth_headers,
        json={
            "city_id": str(second_city.id),
            "district_id": str(second_district.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["city_id"] == str(second_city.id)
    assert data["district_id"] == str(second_district.id)
    assert data["city"] == second_city.name
    assert data["district"] == second_district.name


@pytest.mark.anyio
async def test_update_my_master_can_clear_location(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/masters/me",
        headers=master_auth_headers,
        json={
            "city_id": None,
            "district_id": None,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["city_id"] is None
    assert data["district_id"] is None
    assert data["city"] is None
    assert data["district"] is None


@pytest.mark.anyio
async def test_update_my_master_city_mismatch(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    second_city: City,
):
    response = await ac.patch(
        "/masters/me",
        headers=master_auth_headers,
        json={
            "city_id": str(second_city.id),
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": ("Выбранный район не относится к выбранному городу!")
    }


@pytest.mark.anyio
async def test_update_my_master_cannot_clear_only_city(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/masters/me",
        headers=master_auth_headers,
        json={
            "city_id": None,
        },
    )

    assert response.status_code == 400

    assert response.json() == {"detail": ("Город и район должны быть выбраны вместе.")}


@pytest.mark.anyio
async def test_update_my_master_invalid_experience(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/masters/me",
        headers=master_auth_headers,
        json={
            "experience": -1,
        },
    )

    assert response.status_code == 422
