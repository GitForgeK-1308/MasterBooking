import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.locations.models import City, District


class LocationRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_cities(
        self,
        active_only: bool = False,
    ) -> list[City]:
        query = select(City)

        if active_only:
            query = query.where(
                City.is_active.is_(True)
            )

        query = query.order_by(
            City.name.asc()
        )

        result = await self.session.scalars(
            query
        )

        return list(result.all())

    async def get_city_by_id(
        self,
        city_id: uuid.UUID,
    ) -> City | None:
        return await self.session.scalar(
            select(City).where(
                City.id == city_id
            )
        )

    async def get_city_by_name(
        self,
        name: str,
    ) -> City | None:
        return await self.session.scalar(
            select(City).where(
                City.name == name
            )
        )

    async def create_city(
        self,
        city: City,
    ) -> City:
        self.session.add(city)

        await self.session.commit()
        await self.session.refresh(city)

        return city

    async def update_city(
        self,
        city: City,
    ) -> City:
        await self.session.commit()
        await self.session.refresh(city)

        return city

    async def get_districts_by_city(
        self,
        city_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[District]:
        query = select(District).where(
            District.city_id == city_id
        )

        if active_only:
            query = query.where(
                District.is_active.is_(True)
            )

        query = query.order_by(
            District.name.asc()
        )

        result = await self.session.scalars(
            query
        )

        return list(result.all())

    async def get_district_by_id(
        self,
        district_id: uuid.UUID,
    ) -> District | None:
        return await self.session.scalar(
            select(District).where(
                District.id == district_id
            )
        )

    async def get_district_by_name(
        self,
        city_id: uuid.UUID,
        name: str,
    ) -> District | None:
        return await self.session.scalar(
            select(District).where(
                District.city_id == city_id,
                District.name == name,
            )
        )

    async def create_district(
        self,
        district: District,
    ) -> District:
        self.session.add(district)

        await self.session.commit()
        await self.session.refresh(district)

        return district

    async def update_district(
        self,
        district: District,
    ) -> District:
        await self.session.commit()
        await self.session.refresh(district)

        return district