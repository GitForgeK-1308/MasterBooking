import uuid

from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.offering_images.models import OfferingImage


class OfferingImageRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        image_id: uuid.UUID,
    ) -> OfferingImage | None:
        return await self.session.scalar(
            select(OfferingImage).where(
                OfferingImage.id == image_id
            )
        )

    async def get_by_offering_id(
        self,
        offering_id: uuid.UUID,
    ) -> list[OfferingImage]:
        result = await self.session.scalars(
            select(OfferingImage)
            .where(
                OfferingImage.offering_id
                == offering_id
            )
            .order_by(
                OfferingImage.is_primary.desc(),
                OfferingImage.sort_order.asc(),
                OfferingImage.created_at.asc(),
            )
        )

        return list(result.all())

    async def count_by_offering_id(
        self,
        offering_id: uuid.UUID,
    ) -> int:
        count = await self.session.scalar(
            select(
                func.count(
                    OfferingImage.id
                )
            ).where(
                OfferingImage.offering_id
                == offering_id
            )
        )

        return count or 0

    async def get_primary(
        self,
        offering_id: uuid.UUID,
    ) -> OfferingImage | None:
        return await self.session.scalar(
            select(OfferingImage).where(
                OfferingImage.offering_id
                == offering_id,
                OfferingImage.is_primary.is_(True),
            )
        )

    async def create(
        self,
        image: OfferingImage,
    ) -> OfferingImage:
        self.session.add(
            image
        )

        await self.session.commit()
        await self.session.refresh(
            image
        )

        return image

    async def update(
        self,
        image: OfferingImage,
    ) -> OfferingImage:
        await self.session.commit()
        await self.session.refresh(
            image
        )

        return image

    async def delete(
        self,
        image: OfferingImage,
    ) -> None:
        await self.session.delete(
            image
        )

        await self.session.commit()

    async def set_primary(
        self,
        offering_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> OfferingImage | None:
        image = await self.session.scalar(
            select(OfferingImage).where(
                OfferingImage.id == image_id,
                OfferingImage.offering_id
                == offering_id,
            )
        )

        if image is None:
            return None

        await self.session.execute(
            update(OfferingImage)
            .where(
                OfferingImage.offering_id
                == offering_id,
                OfferingImage.is_primary.is_(True),
            )
            .values(
                is_primary=False
            )
        )

        await self.session.execute(
            update(OfferingImage)
            .where(
                OfferingImage.id == image_id,
                OfferingImage.offering_id
                == offering_id,
            )
            .values(
                is_primary=True
            )
        )

        await self.session.commit()
        await self.session.refresh(
            image
        )

        return image

    async def delete_with_primary_fallback(
        self,
        image: OfferingImage,
    ) -> None:
        was_primary = image.is_primary
        offering_id = image.offering_id

        await self.session.delete(
            image
        )

        await self.session.flush()

        if was_primary:
            next_image = await self.session.scalar(
                select(OfferingImage)
                .where(
                    OfferingImage.offering_id
                    == offering_id
                )
                .order_by(
                    OfferingImage.sort_order.asc(),
                    OfferingImage.created_at.asc(),
                )
                .limit(1)
            )

            if next_image is not None:
                next_image.is_primary = True

        await self.session.commit()