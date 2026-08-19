import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User, UserRole
from src.users.repository import UserRepository
from tests.fixtures.users import TEST_USER_PASSWORD


@pytest.mark.anyio
async def test_register_user(
    ac: AsyncClient,
    db_session: AsyncSession,
):
    response = await ac.post(
        "/auth/register",
        json={
            "email": "USER@example.com",
            "password": TEST_USER_PASSWORD,
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "phone": "+79991234567",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["first_name"] == "Ivan"
    assert data["last_name"] == "Ivanov"
    assert data["phone"] == "+79991234567"
    assert data["role"] == UserRole.CLIENT.value
    assert data["is_active"] is True

    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data

    repository = UserRepository(
        db_session
    )

    user = await repository.get_by_email(
        "user@example.com"
    )

    assert user is not None
    assert user.email == "user@example.com"
    assert user.hashed_password != TEST_USER_PASSWORD


@pytest.mark.anyio
async def test_register_duplicate_email(
    ac: AsyncClient,
    user: User,
):
    response = await ac.post(
        "/auth/register",
        json={
            "email": "USER@example.com",
            "password": TEST_USER_PASSWORD,
            "first_name": "Ivan",
            "last_name": "Ivanov",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Пользователь с таким email "
            "уже существует!"
        )
    }


@pytest.mark.anyio
async def test_register_invalid_email(
    ac: AsyncClient,
):
    response = await ac.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": TEST_USER_PASSWORD,
            "first_name": "Ivan",
            "last_name": "Ivanov",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_register_short_password(
    ac: AsyncClient,
):
    response = await ac.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "1234567",
            "first_name": "Ivan",
            "last_name": "Ivanov",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_login_user(
    ac: AsyncClient,
    user: User,
):
    response = await ac.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": TEST_USER_PASSWORD,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(
        data["access_token"],
        str,
    )
    assert data["access_token"]


@pytest.mark.anyio
async def test_login_wrong_password(
    ac: AsyncClient,
    user: User,
):
    response = await ac.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Неверный email или пароль!"
    }
    assert response.headers[
        "www-authenticate"
    ] == "Bearer"


@pytest.mark.anyio
async def test_login_user_not_found(
    ac: AsyncClient,
):
    response = await ac.post(
        "/auth/login",
        data={
            "username": "missing@example.com",
            "password": TEST_USER_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Неверный email или пароль!"
    }


@pytest.mark.anyio
async def test_login_inactive_user(
    ac: AsyncClient,
    inactive_user: User,
):
    response = await ac.post(
        "/auth/login",
        data={
            "username": inactive_user.email,
            "password": TEST_USER_PASSWORD,
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Аккаунт пользователя отключён!"
    }