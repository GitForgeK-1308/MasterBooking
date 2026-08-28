import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password import hash_password
from src.auth.token import create_access_token
from src.users.models import User, UserRole

TEST_USER_PASSWORD = "StrongPassword123!"


@pytest.fixture
async def user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="user@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Ivan",
        last_name="Ivanov",
        phone="+79991234567",
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def inactive_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Petr",
        last_name="Petrov",
        phone="+79997654321",
        is_active=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="admin@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(
    user: User,
) -> dict[str, str]:
    token = create_access_token(user_id=user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def inactive_auth_headers(
    inactive_user: User,
) -> dict[str, str]:
    token = create_access_token(user_id=inactive_user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def admin_auth_headers(
    admin_user: User,
) -> dict[str, str]:
    token = create_access_token(user_id=admin_user.id)

    return {
        "Authorization": f"Bearer {token}",
    }
