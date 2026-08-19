import uuid
from decimal import Decimal

from sqlalchemy import (
    and_,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    aliased,
    selectinload,
)

from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.categories.models import Category
from src.master_offering.models import MasterOffering
from src.master_offering.schemas import OfferingSort
from src.masters.models import Master
from src.tags.models import (
    Tag,
    master_offering_tags,
)


class MasterOfferingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_all(
        self,
    ) -> list[MasterOffering]:
        result = await self.session.scalars(
            select(MasterOffering)
            .options(
                selectinload(
                    MasterOffering.tags
                ),
                selectinload(
                    MasterOffering.master
                ).selectinload(
                    Master.user
                ),
            )
            .order_by(
                MasterOffering.title.asc()
            )
        )

        return list(result.all())

    async def get_by_id(
        self,
        offering_id: uuid.UUID,
    ) -> MasterOffering | None:
        return await self.session.scalar(
            select(MasterOffering)
            .options(
                selectinload(
                    MasterOffering.tags
                ),
                selectinload(
                    MasterOffering.master
                ).selectinload(
                    Master.user
                ),
            )
            .where(
                MasterOffering.id == offering_id
            )
        )

    async def get_public_by_id(
        self,
        offering_id: uuid.UUID,
    ) -> MasterOffering | None:
        return await self.session.scalar(
            select(MasterOffering)
            .join(
                Master,
                Master.id
                == MasterOffering.master_id,
            )
            .join(
                Category,
                Category.id
                == MasterOffering.category_id,
            )
            .options(
                selectinload(
                    MasterOffering.tags
                ),
                selectinload(
                    MasterOffering.master
                ).selectinload(
                    Master.user
                ),
            )
            .where(
                MasterOffering.id == offering_id,
                MasterOffering.is_active.is_(True),
                Master.is_active.is_(True),
                Category.is_active.is_(True),
            )
        )

    async def get_by_master_id(
        self,
        master_id: uuid.UUID,
        active_only: bool = True,
    ) -> list[MasterOffering]:
        query = (
            select(MasterOffering)
            .options(
                selectinload(
                    MasterOffering.tags
                ),
                selectinload(
                    MasterOffering.master
                ).selectinload(
                    Master.user
                ),
            )
            .where(
                MasterOffering.master_id == master_id
            )
        )

        if active_only:
            query = (
                query
                .join(
                    Master,
                    Master.id
                    == MasterOffering.master_id,
                )
                .join(
                    Category,
                    Category.id
                    == MasterOffering.category_id,
                )
                .where(
                    MasterOffering.is_active.is_(True),
                    Master.is_active.is_(True),
                    Category.is_active.is_(True),
                )
            )

        query = query.order_by(
            MasterOffering.title.asc(),
            MasterOffering.id.asc(),
        )

        result = await self.session.scalars(
            query
        )

        return list(result.all())

    async def create(
        self,
        offering: MasterOffering,
    ) -> MasterOffering:
        self.session.add(
            offering
        )

        await self.session.commit()

        created_offering = await self.get_by_id(
            offering.id
        )

        if created_offering is None:
            raise RuntimeError(
                "Не удалось получить созданную услугу."
            )

        return created_offering

    async def update(
        self,
        offering: MasterOffering,
    ) -> MasterOffering:
        await self.session.commit()

        updated_offering = await self.get_by_id(
            offering.id
        )

        if updated_offering is None:
            raise RuntimeError(
                "Не удалось получить обновлённую услугу."
            )

        return updated_offering

    async def has_bookings(
        self,
        offering_id: uuid.UUID,
    ) -> bool:
        booking_id = await self.session.scalar(
            select(
                Booking.id
            )
            .where(
                Booking.offering_id == offering_id
            )
            .limit(1)
        )

        return booking_id is not None

    async def hard_delete(
        self,
        offering: MasterOffering,
    ) -> None:
        await self.session.delete(
            offering
        )

        await self.session.commit()

    async def get_public_offerings(
        self,
        category_id: uuid.UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        sort: OfferingSort | None = None,
        search: str | None = None,
        city_id: uuid.UUID | None = None,
        district_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 12,
    ) -> tuple[list[MasterOffering], int]:
        query = (
            select(MasterOffering)
            .join(
                Master,
                Master.id
                == MasterOffering.master_id,
            )
            .join(
                Category,
                Category.id
                == MasterOffering.category_id,
            )
            .options(
                selectinload(
                    MasterOffering.tags
                ),
                selectinload(
                    MasterOffering.master
                ).selectinload(
                    Master.user
                ),
            )
            .where(
                MasterOffering.is_active.is_(True),
                Master.is_active.is_(True),
                Category.is_active.is_(True),
            )
        )

        count_query = (
            select(
                func.count(
                    MasterOffering.id
                )
            )
            .join(
                Master,
                Master.id
                == MasterOffering.master_id,
            )
            .join(
                Category,
                Category.id
                == MasterOffering.category_id,
            )
            .where(
                MasterOffering.is_active.is_(True),
                Master.is_active.is_(True),
                Category.is_active.is_(True),
            )
        )

        if city_id is not None:
            query = query.where(
                Master.city_id == city_id
            )

            count_query = count_query.where(
                Master.city_id == city_id
            )

        if district_id is not None:
            query = query.where(
                Master.district_id == district_id
            )

            count_query = count_query.where(
                Master.district_id == district_id
            )

        if category_id is not None:
            category_ids = self._get_category_tree_ids(
                category_id
            )

            query = query.where(
                MasterOffering.category_id.in_(
                    category_ids
                )
            )

            count_query = count_query.where(
                MasterOffering.category_id.in_(
                    category_ids
                )
            )

        if min_price is not None:
            query = query.where(
                MasterOffering.price >= min_price
            )

            count_query = count_query.where(
                MasterOffering.price >= min_price
            )

        if max_price is not None:
            query = query.where(
                MasterOffering.price <= max_price
            )

            count_query = count_query.where(
                MasterOffering.price <= max_price
            )

        if search is not None:
            search = search.strip()

            if search:
                search_pattern = f"%{search}%"

                tag_match = (
                    select(1)
                    .select_from(
                        master_offering_tags.join(
                            Tag,
                            Tag.id
                            == master_offering_tags.c.tag_id,
                        )
                    )
                    .where(
                        master_offering_tags.c.offering_id
                        == MasterOffering.id,
                        Tag.is_active.is_(True),
                        or_(
                            Tag.name.ilike(
                                search_pattern
                            ),
                            Tag.slug.ilike(
                                search_pattern
                            ),
                        ),
                    )
                    .exists()
                )

                search_condition = or_(
                    MasterOffering.title.ilike(
                        search_pattern
                    ),
                    MasterOffering.description.ilike(
                        search_pattern
                    ),
                    Category.name.ilike(
                        search_pattern
                    ),
                    Category.slug.ilike(
                        search_pattern
                    ),
                    tag_match,
                )

                query = query.where(
                    search_condition
                )

                count_query = count_query.where(
                    search_condition
                )

        if sort == OfferingSort.PRICE_ASC:
            query = query.order_by(
                MasterOffering.price.asc(),
                MasterOffering.title.asc(),
                MasterOffering.id.asc(),
            )

        elif sort == OfferingSort.PRICE_DESC:
            query = query.order_by(
                MasterOffering.price.desc(),
                MasterOffering.title.asc(),
                MasterOffering.id.asc(),
            )

        elif sort == OfferingSort.POPULAR:
            query = (
                query
                .outerjoin(
                    Booking,
                    and_(
                        Booking.offering_id
                        == MasterOffering.id,
                        Booking.status
                        != BookingStatus.CANCELLED,
                    ),
                )
                .group_by(
                    MasterOffering.id
                )
                .order_by(
                    func.count(
                        Booking.id
                    ).desc(),
                    MasterOffering.title.asc(),
                    MasterOffering.id.asc(),
                )
            )

        else:
            query = query.order_by(
                MasterOffering.title.asc(),
                MasterOffering.id.asc(),
            )

        total = await self.session.scalar(
            count_query
        )

        query = (
            query
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.scalars(
            query
        )

        return (
            list(result.all()),
            total or 0,
        )

    def _get_category_tree_ids(
        self,
        category_id: uuid.UUID,
    ):
        category_tree = (
            select(
                Category.id
            )
            .where(
                Category.id == category_id
            )
            .cte(
                name="category_tree",
                recursive=True,
            )
        )

        child_category = aliased(
            Category
        )

        category_tree = category_tree.union_all(
            select(
                child_category.id
            ).where(
                child_category.parent_id
                == category_tree.c.id
            )
        )

        return select(
            category_tree.c.id
        )