import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password import hash_password
from src.auth.token import create_access_token
from src.locations.models import City, District
from src.masters.models import Master
from src.users.models import User, UserRole
from tests.fixtures.users import TEST_USER_PASSWORD


@pytest.fixture
async def master_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="master@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Anna",
        last_name="Petrova",
        phone="+37120000001",
        role=UserRole.MASTER,
        is_active=True,
        avatar_storage_key="avatars/master.png",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def master_auth_headers(
    master_user: User,
) -> dict[str, str]:
    token = create_access_token(user_id=master_user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
async def master_without_profile_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="master-no-profile@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Olga",
        last_name="Ivanova",
        role=UserRole.MASTER,
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def master_without_profile_headers(
    master_without_profile_user: User,
) -> dict[str, str]:
    token = create_access_token(user_id=master_without_profile_user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
async def master(
    db_session: AsyncSession,
    master_user: User,
    city: City,
    district: District,
) -> Master:
    master = Master(
        user_id=master_user.id,
        first_name=master_user.first_name,
        last_name=master_user.last_name,
        description="Professional beauty master.",
        experience=5,
        education="Beauty Academy",
        city_id=city.id,
        district_id=district.id,
        city=city.name,
        district=district.name,
        address="Main Street 10",
        is_active=True,
    )

    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    return master


@pytest.fixture
async def inactive_master(
    db_session: AsyncSession,
) -> Master:
    user = User(
        email="inactive-master@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Maria",
        last_name="Sidorova",
        role=UserRole.MASTER,
        is_active=True,
    )

    db_session.add(user)
    await db_session.flush()

    master = Master(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        description="Inactive master profile.",
        experience=3,
        education="Beauty School",
        is_active=False,
    )

    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    return master


@pytest.fixture
async def second_master(
    db_session: AsyncSession,
) -> Master:
    user = User(
        email="second-master@example.com",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        first_name="Irina",
        last_name="Andersone",
        role=UserRole.MASTER,
        is_active=True,
    )

    db_session.add(user)
    await db_session.flush()

    master = Master(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        description="Second active master.",
        experience=7,
        education="Professional School",
        is_active=True,
    )

    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    return master


@pytest.fixture
async def inactive_city_district(
    db_session: AsyncSession,
    inactive_city: City,
) -> District:
    district = District(
        city_id=inactive_city.id,
        name="Inactive District",
        is_active=True,
    )

    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)

    return district
