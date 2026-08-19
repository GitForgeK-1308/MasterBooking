import uuid

from src.locations.service import LocationService
from src.masters.exceptions import (
    MasterProfileAlreadyExistsError,
)
from src.masters.models import Master
from src.masters.repository import MasterRepository
from src.masters.schemas import (
    MasterCreate,
    MasterProfileCreate,
    MasterUpdate,
)
from src.users.models import User, UserRole


class MasterService:
    def __init__(
        self,
        repository: MasterRepository,
        location_service: LocationService,
    ) -> None:
        self.repository = repository
        self.location_service = location_service

    async def get_master_by_id(
        self,
        master_id: uuid.UUID,
    ) -> Master | None:
        return await self.repository.get_by_id(
            master_id
        )

    async def get_masters(
        self,
    ) -> list[Master]:
        return await self.repository.get_active()

    async def create_master(
        self,
        data: MasterCreate,
    ) -> Master:
        city_name, district_name = (
            await self._resolve_location(
                city_id=data.city_id,
                district_id=data.district_id,
            )
        )

        master = Master(
            first_name=data.first_name,
            last_name=data.last_name,
            description=data.description,
            experience=data.experience,
            education=data.education,
            city_id=data.city_id,
            district_id=data.district_id,
            city=city_name,
            district=district_name,
            address=data.address,
        )

        return await self.repository.create(
            master
        )

    async def update_master(
        self,
        master_id: uuid.UUID,
        data: MasterUpdate,
    ) -> Master | None:
        master = await self.repository.get_by_id(
            master_id
        )

        if master is None:
            return None

        update_data = data.model_dump(
            exclude_unset=True
        )

        required_fields = {
            "first_name",
            "last_name",
            "description",
            "experience",
            "education",
        }

        for field in required_fields:
            if update_data.get(field) is None:
                update_data.pop(
                    field,
                    None,
                )

        city_id_provided = (
            "city_id" in update_data
        )
        district_id_provided = (
            "district_id" in update_data
        )

        if (
            city_id_provided
            or district_id_provided
        ):
            city_id = update_data.get(
                "city_id",
                master.city_id,
            )

            district_id = update_data.get(
                "district_id",
                master.district_id,
            )

            if (
                city_id is None
                and district_id is None
            ):
                update_data["city_id"] = None
                update_data["district_id"] = None
                update_data["city"] = None
                update_data["district"] = None

            elif (
                city_id is None
                or district_id is None
            ):
                raise ValueError(
                    "Город и район должны быть "
                    "выбраны вместе."
                )

            else:
                city, district = (
                    await self.location_service.validate_location(
                        city_id=city_id,
                        district_id=district_id,
                    )
                )

                update_data["city_id"] = city.id
                update_data["district_id"] = district.id
                update_data["city"] = city.name
                update_data["district"] = district.name

        for field, value in update_data.items():
            setattr(
                master,
                field,
                value,
            )

        return await self.repository.update(
            master
        )

    async def delete_master(
        self,
        master_id: uuid.UUID,
    ) -> bool | None:
        master = await self.repository.get_by_id(
            master_id
        )

        if master is None:
            return None

        await self.repository.delete(
            master
        )

        return True

    async def create_master_profile(
        self,
        current_user: User,
        data: MasterProfileCreate,
    ) -> Master:
        existing_master = (
            await self.repository.get_by_user_id(
                current_user.id
            )
        )

        if existing_master is not None:
            raise MasterProfileAlreadyExistsError

        city_name, district_name = (
            await self._resolve_location(
                city_id=data.city_id,
                district_id=data.district_id,
            )
        )

        master = Master(
            user_id=current_user.id,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            description=data.description,
            experience=data.experience,
            education=data.education,
            city_id=data.city_id,
            district_id=data.district_id,
            city=city_name,
            district=district_name,
            address=data.address,
        )

        current_user.role = UserRole.MASTER

        return await self.repository.create(
            master
        )

    async def _resolve_location(
        self,
        city_id: uuid.UUID | None,
        district_id: uuid.UUID | None,
    ) -> tuple[str | None, str | None]:
        if (
            city_id is None
            and district_id is None
        ):
            return None, None

        if (
            city_id is None
            or district_id is None
        ):
            raise ValueError(
                "Город и район должны быть "
                "выбраны вместе."
            )

        city, district = (
            await self.location_service.validate_location(
                city_id=city_id,
                district_id=district_id,
            )
        )

        return city.name, district.name