import uuid

from src.locations.exceptions import (
    CityAlreadyExistsError,
    CityHasDistrictsError,
    CityInUseError,
    CityNotFoundError,
    DistrictAlreadyExistsError,
    DistrictCityMismatchError,
    DistrictInUseError,
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


class LocationService:
    def __init__(
        self,
        repository: LocationRepository,
    ) -> None:
        self.repository = repository

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        return " ".join(name.strip().split()).title()

    async def get_cities(
        self,
        active_only: bool = False,
    ) -> list[City]:
        return await self.repository.get_cities(active_only=active_only)

    async def get_city_by_id(
        self,
        city_id: uuid.UUID,
    ) -> City:
        city = await self.repository.get_city_by_id(city_id)

        if city is None:
            raise CityNotFoundError

        return city

    async def create_city(
        self,
        data: CityCreate,
    ) -> City:
        name = self._normalize_name(data.name)

        existing_city = await self.repository.get_city_by_name(name)

        if existing_city is not None:
            raise CityAlreadyExistsError

        city = City(
            name=name,
        )

        return await self.repository.create_city(city)

    async def update_city(
        self,
        city_id: uuid.UUID,
        data: CityUpdate,
    ) -> City:
        city = await self.get_city_by_id(city_id)

        data_dict = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "name" in data_dict:
            name = self._normalize_name(data_dict["name"])

            existing_city = await self.repository.get_city_by_name(name)

            if existing_city is not None and existing_city.id != city.id:
                raise CityAlreadyExistsError

            city.name = name

        if "is_active" in data_dict:
            city.is_active = data_dict["is_active"]

        return await self.repository.update_city(city)

    async def get_districts_by_city(
        self,
        city_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[District]:
        city = await self.get_city_by_id(city_id)

        if active_only and not city.is_active:
            raise CityNotFoundError

        return await self.repository.get_districts_by_city(
            city_id=city_id,
            active_only=active_only,
        )

    async def get_district_by_id(
        self,
        district_id: uuid.UUID,
    ) -> District:
        district = await self.repository.get_district_by_id(district_id)

        if district is None:
            raise DistrictNotFoundError

        return district

    async def create_district(
        self,
        data: DistrictCreate,
    ) -> District:
        await self.get_city_by_id(data.city_id)

        name = self._normalize_name(data.name)

        existing_district = await self.repository.get_district_by_name(
            city_id=data.city_id,
            name=name,
        )

        if existing_district is not None:
            raise DistrictAlreadyExistsError

        district = District(
            city_id=data.city_id,
            name=name,
        )

        return await self.repository.create_district(district)

    async def update_district(
        self,
        district_id: uuid.UUID,
        data: DistrictUpdate,
    ) -> District:
        district = await self.get_district_by_id(district_id)

        data_dict = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "name" in data_dict:
            name = self._normalize_name(data_dict["name"])

            existing_district = await self.repository.get_district_by_name(
                city_id=district.city_id,
                name=name,
            )

            if existing_district is not None and existing_district.id != district.id:
                raise DistrictAlreadyExistsError

            district.name = name

        if "is_active" in data_dict:
            district.is_active = data_dict["is_active"]

        return await self.repository.update_district(district)

    async def validate_location(
        self,
        city_id: uuid.UUID,
        district_id: uuid.UUID,
    ) -> tuple[City, District]:
        city = await self.get_city_by_id(city_id)

        district = await self.get_district_by_id(district_id)

        if district.city_id != city.id:
            raise DistrictCityMismatchError

        if not city.is_active:
            raise CityNotFoundError

        if not district.is_active:
            raise DistrictNotFoundError

        return city, district

    async def delete_city(
        self,
        city_id: uuid.UUID,
    ) -> None:
        city = await self.repository.get_city_by_id(city_id)

        if city is None:
            raise CityNotFoundError

        if await self.repository.city_has_districts(city_id):
            raise CityHasDistrictsError

        if await self.repository.city_is_used_by_masters(city_id):
            raise CityInUseError

        await self.repository.delete_city(city)

    async def delete_district(
        self,
        district_id: uuid.UUID,
    ) -> None:
        district = await self.repository.get_district_by_id(district_id)

        if district is None:
            raise DistrictNotFoundError

        if await self.repository.district_is_used_by_masters(district_id):
            raise DistrictInUseError

        await self.repository.delete_district(district)
