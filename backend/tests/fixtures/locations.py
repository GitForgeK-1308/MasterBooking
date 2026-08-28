import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.locations.models import City, District


@pytest.fixture
async def city(
    db_session: AsyncSession,
) -> City:
    city = City(
        name="Riga",
    )

    db_session.add(city)
    await db_session.commit()
    await db_session.refresh(city)

    return city


@pytest.fixture
async def second_city(
    db_session: AsyncSession,
) -> City:
    city = City(
        name="Jurmala",
    )

    db_session.add(city)
    await db_session.commit()
    await db_session.refresh(city)

    return city


@pytest.fixture
async def inactive_city(
    db_session: AsyncSession,
) -> City:
    city = City(
        name="Daugavpils",
        is_active=False,
    )

    db_session.add(city)
    await db_session.commit()
    await db_session.refresh(city)

    return city


@pytest.fixture
async def district(
    db_session: AsyncSession,
    city: City,
) -> District:
    district = District(
        city_id=city.id,
        name="Centrs",
    )

    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)

    return district


@pytest.fixture
async def second_district(
    db_session: AsyncSession,
    city: City,
) -> District:
    district = District(
        city_id=city.id,
        name="Agenskalns",
    )

    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)

    return district


@pytest.fixture
async def inactive_district(
    db_session: AsyncSession,
    city: City,
) -> District:
    district = District(
        city_id=city.id,
        name="Vecpilseta",
        is_active=False,
    )

    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)

    return district
