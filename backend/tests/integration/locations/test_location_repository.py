import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.locations.models import City, District
from src.locations.repository import LocationRepository


def make_city(
    *,
    name: str = "Riga",
    is_active: bool = True,
) -> City:
    return City(
        name=name,
        is_active=is_active,
    )


def make_district(
    *,
    city_id: uuid.UUID,
    name: str = "Centrs",
    is_active: bool = True,
) -> District:
    return District(
        city_id=city_id,
        name=name,
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_create_city(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = make_city()

    result = await repository.create_city(
        city
    )

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )
    assert result.name == "Riga"
    assert result.is_active is True


@pytest.mark.anyio
async def test_get_cities_sorted(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    await repository.create_city(
        make_city(
            name="Riga"
        )
    )
    await repository.create_city(
        make_city(
            name="Daugavpils",
            is_active=False,
        )
    )
    await repository.create_city(
        make_city(
            name="Jurmala"
        )
    )

    result = await repository.get_cities()

    assert [
        city.name
        for city in result
    ] == [
        "Daugavpils",
        "Jurmala",
        "Riga",
    ]


@pytest.mark.anyio
async def test_get_cities_active_only(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    await repository.create_city(
        make_city(
            name="Riga"
        )
    )
    await repository.create_city(
        make_city(
            name="Daugavpils",
            is_active=False,
        )
    )
    await repository.create_city(
        make_city(
            name="Jurmala"
        )
    )

    result = await repository.get_cities(
        active_only=True
    )

    assert [
        city.name
        for city in result
    ] == [
        "Jurmala",
        "Riga",
    ]

    assert all(
        city.is_active
        for city in result
    )


@pytest.mark.anyio
async def test_get_city_by_id(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    result = await repository.get_city_by_id(
        city.id
    )

    assert result is not None
    assert result.id == city.id
    assert result.name == city.name


@pytest.mark.anyio
async def test_get_city_by_id_not_found(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    result = await repository.get_city_by_id(
        uuid.uuid4()
    )

    assert result is None


@pytest.mark.anyio
async def test_get_city_by_name(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    result = await repository.get_city_by_name(
        "Riga"
    )

    assert result is not None
    assert result.id == city.id


@pytest.mark.anyio
async def test_get_city_by_name_not_found(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    result = await repository.get_city_by_name(
        "Missing"
    )

    assert result is None


@pytest.mark.anyio
async def test_update_city(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    city.name = "Jurmala"
    city.is_active = False

    result = await repository.update_city(
        city
    )

    assert result.name == "Jurmala"
    assert result.is_active is False

    city_id = result.id

    db_session.expunge(
        result
    )

    city_from_database = (
        await repository.get_city_by_id(
            city_id
        )
    )

    assert city_from_database is not None
    assert city_from_database.id == city_id
    assert city_from_database.name == "Jurmala"
    assert city_from_database.is_active is False


@pytest.mark.anyio
async def test_create_district(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    district = make_district(
        city_id=city.id
    )

    result = await repository.create_district(
        district
    )

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )
    assert result.city_id == city.id
    assert result.name == "Centrs"
    assert result.is_active is True


@pytest.mark.anyio
async def test_get_districts_by_city_sorted(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    await repository.create_district(
        make_district(
            city_id=city.id,
            name="Centrs",
        )
    )
    await repository.create_district(
        make_district(
            city_id=city.id,
            name="Vecpilseta",
            is_active=False,
        )
    )
    await repository.create_district(
        make_district(
            city_id=city.id,
            name="Agenskalns",
        )
    )

    result = (
        await repository.get_districts_by_city(
            city.id
        )
    )

    assert [
        district.name
        for district in result
    ] == [
        "Agenskalns",
        "Centrs",
        "Vecpilseta",
    ]


@pytest.mark.anyio
async def test_get_districts_by_city_active_only(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    await repository.create_district(
        make_district(
            city_id=city.id,
            name="Centrs",
        )
    )
    await repository.create_district(
        make_district(
            city_id=city.id,
            name="Vecpilseta",
            is_active=False,
        )
    )
    await repository.create_district(
        make_district(
            city_id=city.id,
            name="Agenskalns",
        )
    )

    result = (
        await repository.get_districts_by_city(
            city_id=city.id,
            active_only=True,
        )
    )

    assert [
        district.name
        for district in result
    ] == [
        "Agenskalns",
        "Centrs",
    ]

    assert all(
        district.is_active
        for district in result
    )


@pytest.mark.anyio
async def test_get_district_by_id(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    district = await repository.create_district(
        make_district(
            city_id=city.id
        )
    )

    result = await repository.get_district_by_id(
        district.id
    )

    assert result is not None
    assert result.id == district.id
    assert result.city_id == city.id


@pytest.mark.anyio
async def test_get_district_by_id_not_found(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    result = await repository.get_district_by_id(
        uuid.uuid4()
    )

    assert result is None


@pytest.mark.anyio
async def test_get_district_by_name(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    district = await repository.create_district(
        make_district(
            city_id=city.id
        )
    )

    result = await repository.get_district_by_name(
        city_id=city.id,
        name="Centrs",
    )

    assert result is not None
    assert result.id == district.id


@pytest.mark.anyio
async def test_get_district_by_name_not_found(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    result = await repository.get_district_by_name(
        city_id=city.id,
        name="Missing",
    )

    assert result is None


@pytest.mark.anyio
async def test_update_district(
    db_session: AsyncSession,
):
    repository = LocationRepository(
        db_session
    )

    city = await repository.create_city(
        make_city()
    )

    district = await repository.create_district(
        make_district(
            city_id=city.id
        )
    )

    district.name = "Old Town"
    district.is_active = False

    result = await repository.update_district(
        district
    )

    assert result.name == "Old Town"
    assert result.is_active is False

    district_id = result.id

    db_session.expunge(
        result
    )

    district_from_database = (
        await repository.get_district_by_id(
            district_id
        )
    )

    assert district_from_database is not None
    assert district_from_database.id == district_id
    assert district_from_database.name == "Old Town"
    assert district_from_database.is_active is False