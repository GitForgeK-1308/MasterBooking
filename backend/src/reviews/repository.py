import uuid

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import Booking
from src.master_offering.models import MasterOffering
from src.reviews.models import Review
from src.users.models import User


class ReviewRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        review_id: uuid.UUID,
    ) -> Review | None:
        return await self.session.scalar(select(Review).where(Review.id == review_id))

    async def get_by_booking_id(
        self,
        booking_id: uuid.UUID,
    ) -> Review | None:
        return await self.session.scalar(
            select(Review).where(Review.booking_id == booking_id)
        )

    async def get_by_master_id(
        self,
        master_id: uuid.UUID,
    ) -> list[Review]:
        result = await self.session.scalars(
            select(Review)
            .where(Review.master_id == master_id)
            .order_by(
                Review.created_at.desc(),
                Review.id.desc(),
            )
        )

        return list(result.all())

    async def create(
        self,
        review: Review,
    ) -> Review:
        self.session.add(review)

        await self.session.commit()
        await self.session.refresh(review)

        return review

    async def get_master_stats(
        self,
        master_id: uuid.UUID,
    ) -> tuple[float, int]:
        result = await self.session.execute(
            select(
                func.avg(Review.rating),
                func.count(Review.id),
            ).where(Review.master_id == master_id)
        )

        average_rating, reviews_count = result.one()

        return (
            (
                round(
                    float(average_rating),
                    1,
                )
                if average_rating is not None
                else 0.0
            ),
            reviews_count,
        )

    async def get_public_by_master_id(
        self,
        master_id: uuid.UUID,
    ):
        result = await self.session.execute(
            select(
                Review,
                User.first_name,
                User.last_name,
            )
            .outerjoin(
                User,
                User.id == Review.client_id,
            )
            .where(Review.master_id == master_id)
            .order_by(
                Review.created_at.desc(),
                Review.id.desc(),
            )
        )

        return result.all()

    async def get_rating_distribution(
        self,
        master_id: uuid.UUID,
    ) -> dict[int, int]:
        result = await self.session.execute(
            select(
                Review.rating,
                func.count(Review.id),
            )
            .where(Review.master_id == master_id)
            .group_by(Review.rating)
        )

        distribution = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
        }

        for rating, count in result.all():
            distribution[rating] = count

        return distribution

    async def get_for_master_dashboard(
        self,
        master_id: uuid.UUID,
    ):
        result = await self.session.execute(
            select(
                Review,
                MasterOffering.id,
                MasterOffering.title,
                User.first_name,
                User.last_name,
            )
            .join(
                Booking,
                Booking.id == Review.booking_id,
            )
            .join(
                MasterOffering,
                MasterOffering.id == Booking.offering_id,
            )
            .outerjoin(
                User,
                User.id == Review.client_id,
            )
            .where(Review.master_id == master_id)
            .order_by(
                Review.created_at.desc(),
                Review.id.desc(),
            )
        )

        return result.all()
