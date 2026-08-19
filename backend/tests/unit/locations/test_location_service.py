import uuid
from unittest.mock import AsyncMock

import pytest

from src.locations.exceptions import (
    CityAlreadyExistsError,
    CityNotFoundError,
    DistrictAlreadyExistsError,
    DistrictCityMismatchError,
    DistrictNotFoundError,
)
from src.locations.models import City, District
from src.locations.repository import LocationRepository
from src.locations.schemas import (
    CityCreate,
    CityUpdate,
    DistrictCreate,
    DistrictUpdate,
)
from src.locations.service import LocationService


def make_city(
    *,
    name: str = "Riga",
    is_active: bool = True,
) -> City:
    return City(
        id=uuid.uuid4(),
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
        id=uuid.uuid4(),
        city_id=city_id,
        name=name,
        is_active=is_active,
    )


@pytest.fixture
def location_repository() -> AsyncMock:
    return AsyncMock(
        spec=LocationRepository
    )


@pytest.fixture
def location_service(
    location_repository: AsyncMock,
) -> LocationService:
    return LocationService(
        repository=location_repository
    )


@pytest.mark.anyio
async def test_get_cities(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    cities = [
        make_city(name="Jurmala"),
        make_city(name="Riga"),
    ]

    location_repository.get_cities.return_value = (
        cities
    )

    result = await location_service.get_cities(
        active_only=True
    )

    assert result == cities

    location_repository.get_cities.assert_awaited_once_with(
        active_only=True
    )


@pytest.mark.anyio
async def test_get_city_by_id(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    location_repository.get_city_by_id.return_value = (
        city
    )

    result = await location_service.get_city_by_id(
        city.id
    )

    assert result is city

    location_repository.get_city_by_id.assert_awaited_once_with(
        city.id
    )


@pytest.mark.anyio
async def test_get_city_by_id_not_found(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city_id = uuid.uuid4()

    location_repository.get_city_by_id.return_value = (
        None
    )

    with pytest.raises(
        CityNotFoundError
    ):
        await location_service.get_city_by_id(
            city_id
        )

    location_repository.get_city_by_id.assert_awaited_once_with(
        city_id
    )


@pytest.mark.anyio
async def test_create_city(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    data = CityCreate(
        name="  rIGA   cITY "
    )

    location_repository.get_city_by_name.return_value = (
        None
    )

    location_repository.create_city.side_effect = (
        lambda city: city
    )

    result = await location_service.create_city(
        data
    )

    assert result.name == "Riga City"

    location_repository.get_city_by_name.assert_awaited_once_with(
        "Riga City"
    )

    location_repository.create_city.assert_awaited_once()

    created_city = (
        location_repository.create_city.await_args.args[
            0
        ]
    )

    assert created_city is result
    assert created_city.name == "Riga City"


@pytest.mark.anyio
async def test_create_city_duplicate(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    existing_city = make_city()

    location_repository.get_city_by_name.return_value = (
        existing_city
    )

    data = CityCreate(
        name="  rIGA "
    )

    with pytest.raises(
        CityAlreadyExistsError
    ):
        await location_service.create_city(
            data
        )

    location_repository.get_city_by_name.assert_awaited_once_with(
        "Riga"
    )

    location_repository.create_city.assert_not_awaited()


@pytest.mark.anyio
async def test_update_city(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_city_by_name.return_value = (
        None
    )

    location_repository.update_city.side_effect = (
        lambda city: city
    )

    data = CityUpdate(
        name="  new   rIGA ",
        is_active=False,
    )

    result = await location_service.update_city(
        city_id=city.id,
        data=data,
    )

    assert result is city
    assert city.name == "New Riga"
    assert city.is_active is False

    location_repository.get_city_by_name.assert_awaited_once_with(
        "New Riga"
    )

    location_repository.update_city.assert_awaited_once_with(
        city
    )


@pytest.mark.anyio
async def test_update_city_duplicate(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city(
        name="Riga"
    )

    existing_city = make_city(
        name="Jurmala"
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_city_by_name.return_value = (
        existing_city
    )

    data = CityUpdate(
        name="Jurmala"
    )

    with pytest.raises(
        CityAlreadyExistsError
    ):
        await location_service.update_city(
            city_id=city.id,
            data=data,
        )

    location_repository.update_city.assert_not_awaited()


@pytest.mark.anyio
async def test_get_districts_by_city(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    districts = [
        make_district(
            city_id=city.id,
            name="Centrs",
        ),
        make_district(
            city_id=city.id,
            name="Agenskalns",
        ),
    ]

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_districts_by_city.return_value = (
        districts
    )

    result = (
        await location_service.get_districts_by_city(
            city_id=city.id,
            active_only=True,
        )
    )

    assert result == districts

    location_repository.get_districts_by_city.assert_awaited_once_with(
        city_id=city.id,
        active_only=True,
    )


@pytest.mark.anyio
async def test_get_districts_by_inactive_city(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city(
        is_active=False
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    with pytest.raises(
        CityNotFoundError
    ):
        await location_service.get_districts_by_city(
            city_id=city.id,
            active_only=True,
        )

    location_repository.get_districts_by_city.assert_not_awaited()


@pytest.mark.anyio
async def test_get_district_by_id(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    district = make_district(
        city_id=city.id
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    result = (
        await location_service.get_district_by_id(
            district.id
        )
    )

    assert result is district

    location_repository.get_district_by_id.assert_awaited_once_with(
        district.id
    )


@pytest.mark.anyio
async def test_get_district_by_id_not_found(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    district_id = uuid.uuid4()

    location_repository.get_district_by_id.return_value = (
        None
    )

    with pytest.raises(
        DistrictNotFoundError
    ):
        await location_service.get_district_by_id(
            district_id
        )


@pytest.mark.anyio
async def test_create_district(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_district_by_name.return_value = (
        None
    )

    location_repository.create_district.side_effect = (
        lambda district: district
    )

    data = DistrictCreate(
        city_id=city.id,
        name="  old   town ",
    )

    result = (
        await location_service.create_district(
            data
        )
    )

    assert result.city_id == city.id
    assert result.name == "Old Town"

    location_repository.get_district_by_name.assert_awaited_once_with(
        city_id=city.id,
        name="Old Town",
    )

    location_repository.create_district.assert_awaited_once()

    created_district = (
        location_repository.create_district.await_args.args[
            0
        ]
    )

    assert created_district is result


@pytest.mark.anyio
async def test_create_district_duplicate(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    existing_district = make_district(
        city_id=city.id
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_district_by_name.return_value = (
        existing_district
    )

    data = DistrictCreate(
        city_id=city.id,
        name="  cENTRS ",
    )

    with pytest.raises(
        DistrictAlreadyExistsError
    ):
        await location_service.create_district(
            data
        )

    location_repository.create_district.assert_not_awaited()


@pytest.mark.anyio
async def test_update_district(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    district = make_district(
        city_id=city.id
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    location_repository.get_district_by_name.return_value = (
        None
    )

    location_repository.update_district.side_effect = (
        lambda district: district
    )

    data = DistrictUpdate(
        name="  old   cENTRS ",
        is_active=False,
    )

    result = (
        await location_service.update_district(
            district_id=district.id,
            data=data,
        )
    )

    assert result is district
    assert district.name == "Old Centrs"
    assert district.is_active is False

    location_repository.get_district_by_name.assert_awaited_once_with(
        city_id=city.id,
        name="Old Centrs",
    )

    location_repository.update_district.assert_awaited_once_with(
        district
    )


@pytest.mark.anyio
async def test_update_district_duplicate(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    district = make_district(
        city_id=city.id,
        name="Centrs",
    )

    existing_district = make_district(
        city_id=city.id,
        name="Agenskalns",
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    location_repository.get_district_by_name.return_value = (
        existing_district
    )

    data = DistrictUpdate(
        name="Agenskalns"
    )

    with pytest.raises(
        DistrictAlreadyExistsError
    ):
        await location_service.update_district(
            district_id=district.id,
            data=data,
        )

    location_repository.update_district.assert_not_awaited()


@pytest.mark.anyio
async def test_validate_location(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    district = make_district(
        city_id=city.id
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    result = await location_service.validate_location(
        city_id=city.id,
        district_id=district.id,
    )

    assert result == (
        city,
        district,
    )


@pytest.mark.anyio
async def test_validate_location_city_mismatch(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    district = make_district(
        city_id=uuid.uuid4()
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    with pytest.raises(
        DistrictCityMismatchError
    ):
        await location_service.validate_location(
            city_id=city.id,
            district_id=district.id,
        )


@pytest.mark.anyio
async def test_validate_location_inactive_city(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city(
        is_active=False
    )

    district = make_district(
        city_id=city.id
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    with pytest.raises(
        CityNotFoundError
    ):
        await location_service.validate_location(
            city_id=city.id,
            district_id=district.id,
        )


@pytest.mark.anyio
async def test_validate_location_inactive_district(
    location_service: LocationService,
    location_repository: AsyncMock,
):
    city = make_city()

    district = make_district(
        city_id=city.id,
        is_active=False,
    )

    location_repository.get_city_by_id.return_value = (
        city
    )

    location_repository.get_district_by_id.return_value = (
        district
    )

    with pytest.raises(
        DistrictNotFoundError
    ):
        await location_service.validate_location(
            city_id=city.id,
            district_id=district.id,
        )