import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.repository import UserRepository


def make_user(
    *,
    email: str = "user@example.com",
) -> User:
    return User(
        email=email,
        hashed_password="hashed-password",
        first_name="Ivan",
        last_name="Ivanov",
        phone="+79991234567",
    )


@pytest.mark.anyio
async def test_create_user(
    db_session: AsyncSession,
):
    repository = UserRepository(db_session)

    user = make_user()

    result = await repository.create(user)

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )

    assert result.email == "user@example.com"
    assert result.first_name == "Ivan"
    assert result.last_name == "Ivanov"
    assert result.phone == "+79991234567"

    assert result.role.value == "client"
    assert result.is_active is True
    assert result.created_at is not None


@pytest.mark.anyio
async def test_get_user_by_id(
    db_session: AsyncSession,
):
    repository = UserRepository(db_session)

    user = await repository.create(make_user())

    result = await repository.get_by_id(user.id)

    assert result is not None
    assert result.id == user.id
    assert result.email == user.email


@pytest.mark.anyio
async def test_get_user_by_id_not_found(
    db_session: AsyncSession,
):
    repository = UserRepository(db_session)

    result = await repository.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_get_user_by_email(
    db_session: AsyncSession,
):
    repository = UserRepository(db_session)

    user = await repository.create(make_user())

    result = await repository.get_by_email("user@example.com")

    assert result is not None
    assert result.id == user.id
    assert result.email == "user@example.com"


@pytest.mark.anyio
async def test_get_user_by_email_not_found(
    db_session: AsyncSession,
):
    repository = UserRepository(db_session)

    result = await repository.get_by_email("missing@example.com")

    assert result is None


@pytest.mark.anyio
async def test_update_user(
    db_session: AsyncSession,
):
    repository = UserRepository(db_session)

    user = await repository.create(make_user())

    user.first_name = "Petr"
    user.last_name = "Petrov"
    user.phone = None

    result = await repository.update(user)

    assert result.id == user.id
    assert result.first_name == "Petr"
    assert result.last_name == "Petrov"
    assert result.phone is None

    user_id = result.id

    db_session.expire(result)

    user_from_database = await repository.get_by_id(user_id)

    assert user_from_database is not None
    assert user_from_database.id == user_id
    assert user_from_database.first_name == "Petr"
    assert user_from_database.last_name == "Petrov"
    assert user_from_database.phone is None
