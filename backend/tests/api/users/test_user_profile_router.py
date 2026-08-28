import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User, UserRole
from src.users.repository import UserRepository


@pytest.mark.anyio
async def test_get_my_profile(
    ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["first_name"] == "Ivan"
    assert data["last_name"] == "Ivanov"
    assert data["phone"] == "+79991234567"
    assert data["role"] == UserRole.CLIENT.value
    assert data["is_active"] is True
    assert "created_at" in data

    assert "hashed_password" not in data


@pytest.mark.anyio
async def test_get_my_profile_without_token(
    ac: AsyncClient,
):
    response = await ac.get("/users/me")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_my_profile_invalid_token(
    ac: AsyncClient,
):
    response = await ac.get(
        "/users/me",
        headers={
            "Authorization": ("Bearer invalid-token"),
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": ("Не удалось подтвердить пользователя!")}

    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.anyio
async def test_get_my_profile_inactive_user(
    ac: AsyncClient,
    inactive_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/users/me",
        headers=inactive_auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": ("Аккаунт пользователя отключён!")}


@pytest.mark.anyio
async def test_update_my_profile(
    ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        "/users/me",
        headers=auth_headers,
        json={
            "first_name": "Petr",
            "last_name": "Petrov",
            "phone": "+79990000000",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["first_name"] == "Petr"
    assert data["last_name"] == "Petrov"
    assert data["phone"] == "+79990000000"

    repository = UserRepository(db_session)

    user_from_database = await repository.get_by_id(user.id)

    assert user_from_database is not None
    assert user_from_database.first_name == "Petr"
    assert user_from_database.last_name == "Petrov"
    assert user_from_database.phone == "+79990000000"


@pytest.mark.anyio
async def test_update_my_profile_clear_phone(
    ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        "/users/me",
        headers=auth_headers,
        json={
            "phone": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["phone"] is None

    repository = UserRepository(db_session)

    user_from_database = await repository.get_by_id(user.id)

    assert user_from_database is not None
    assert user_from_database.phone is None


@pytest.mark.anyio
async def test_update_my_profile_invalid_data(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/users/me",
        headers=auth_headers,
        json={
            "first_name": "I",
        },
    )

    assert response.status_code == 422
