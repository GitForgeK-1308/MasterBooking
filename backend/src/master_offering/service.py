import math
import uuid
from decimal import Decimal

from src.categories.exceptions import (
    CategoryInactiveError,
    CategoryNotFoundError,
)
from src.categories.repository import CategoryRepository
from src.master_offering.exceptions import (
    OfferingAccessDeniedError,
    OfferingNotFoundError,
)
from src.master_offering.models import MasterOffering
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_offering.schemas import (
    MasterOfferingCreate,
    MasterOfferingPage,
    MasterOfferingUpdate,
    OfferingSort,
)
from src.offering_images.repository import (
    OfferingImageRepository,
)
from src.offering_images.storage import LocalImageStorage
from src.tags.exceptions import (
    TagInactiveError,
    TagNotFoundError,
)
from src.tags.models import Tag
from src.tags.repository import TagRepository


class MasterOfferingService:
    def __init__(
        self,
        repository: MasterOfferingRepository,
        category_repository: CategoryRepository,
        tag_repository: TagRepository,
        image_repository: OfferingImageRepository,
        image_storage: LocalImageStorage,
    ) -> None:
        self.repository = repository
        self.category_repository = category_repository
        self.tag_repository = tag_repository
        self.image_repository = image_repository
        self.image_storage = image_storage

    async def get_offering_by_id(
        self,
        offering_id: uuid.UUID,
    ) -> MasterOffering | None:
        return await self.repository.get_by_id(
            offering_id
        )

    async def get_public_offering_by_id(
        self,
        offering_id: uuid.UUID,
    ) -> MasterOffering:
        offering = await self.repository.get_public_by_id(
            offering_id
        )

        if offering is None:
            raise OfferingNotFoundError

        return offering

    async def get_offerings(
        self,
    ) -> list[MasterOffering]:
        return await self.repository.get_all()

    async def create_offering(
        self,
        master_id: uuid.UUID,
        data: MasterOfferingCreate,
    ) -> MasterOffering:
        category = await self.category_repository.get_by_id(
            data.category_id
        )

        if category is None:
            raise CategoryNotFoundError

        if not category.is_active:
            raise CategoryInactiveError

        tags = await self._get_valid_tags(
            data.tag_ids
        )

        new_offering = MasterOffering(
            master_id=master_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            price=data.price,
            duration_minutes=data.duration_minutes,
        )

        new_offering.tags = tags

        return await self.repository.create(
            new_offering
        )

    async def update_offering(
        self,
        offering_id: uuid.UUID,
        master_id: uuid.UUID,
        data: MasterOfferingUpdate,
    ) -> MasterOffering:
        offering = await self.repository.get_by_id(
            offering_id
        )

        if offering is None:
            raise OfferingNotFoundError

        if offering.master_id != master_id:
            raise OfferingAccessDeniedError

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        tag_ids = update_data.pop(
            "tag_ids",
            None,
        )

        if "category_id" in update_data:
            category = await self.category_repository.get_by_id(
                update_data["category_id"]
            )

            if category is None:
                raise CategoryNotFoundError

            if not category.is_active:
                raise CategoryInactiveError

        if tag_ids is not None:
            offering.tags = await self._get_valid_tags(
                tag_ids
            )

        for field, value in update_data.items():
            setattr(
                offering,
                field,
                value,
            )

        return await self.repository.update(
            offering
        )

    async def delete_offering(
        self,
        offering_id: uuid.UUID,
        master_id: uuid.UUID,
    ) -> None:
        offering = await self.repository.get_by_id(
            offering_id
        )

        if offering is None:
            raise OfferingNotFoundError

        if offering.master_id != master_id:
            raise OfferingAccessDeniedError

        has_bookings = await self.repository.has_bookings(
            offering.id
        )

        if has_bookings:
            offering.is_active = False

            await self.repository.update(
                offering
            )

            return

        images = await self.image_repository.get_by_offering_id(
            offering.id
        )

        storage_keys = [
            image.storage_key
            for image in images
        ]

        await self.repository.hard_delete(
            offering
        )

        for storage_key in storage_keys:
            await self.image_storage.delete(
                storage_key
            )

    async def get_master_offerings(
        self,
        master_id: uuid.UUID,
        active_only: bool = True,
    ) -> list[MasterOffering]:
        return await self.repository.get_by_master_id(
            master_id=master_id,
            active_only=active_only,
        )

    async def get_public_offerings(
        self,
        category_id: uuid.UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        sort: OfferingSort | None = None,
        city_id: uuid.UUID | None = None,
        district_id: uuid.UUID | None = None,
        search: str | None = None,
        exclude_master_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 12,
    ) -> MasterOfferingPage:
        offset = (
            page - 1
        ) * page_size

        offerings, total = (
            await self.repository.get_public_offerings(
                category_id=category_id,
                min_price=min_price,
                max_price=max_price,
                sort=sort,
                search=search,
                city_id=city_id,
                district_id=district_id,
                exclude_master_id=exclude_master_id,
                offset=offset,
                limit=page_size,
            )
        )

        total_pages = (
            math.ceil(
                total / page_size
            )
            if total > 0
            else 0
        )

        return MasterOfferingPage(
            items=offerings,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def _get_valid_tags(
        self,
        tag_ids: list[uuid.UUID],
    ) -> list[Tag]:
        unique_ids = list(
            dict.fromkeys(tag_ids)
        )

        tags = await self.tag_repository.get_by_ids(
            unique_ids
        )

        if len(tags) != len(unique_ids):
            raise TagNotFoundError

        if any(
            not tag.is_active
            for tag in tags
        ):
            raise TagInactiveError

        return tags