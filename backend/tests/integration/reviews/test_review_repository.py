import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import Booking
from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.reviews.models import Review
from src.reviews.repository import ReviewRepository
from src.users.models import User


@pytest.mark.anyio
async def test_create_review(
    db_session: AsyncSession,
    user: User,
    master: Master,
    completed_booking: Booking,
):
    repository = ReviewRepository(
        db_session
    )

    review = Review(
        booking_id=completed_booking.id,
        master_id=master.id,
        client_id=user.id,
        rating=5,
        comment="Отличный мастер!",
    )

    result = await repository.create(
        review
    )

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )

    assert (
        result.booking_id
        == completed_booking.id
    )

    assert result.master_id == master.id
    assert result.client_id == user.id
    assert result.rating == 5

    assert (
        result.comment
        == "Отличный мастер!"
    )

    assert result.created_at is not None


@pytest.mark.anyio
async def test_get_review_by_id(
    db_session: AsyncSession,
    review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    review_id = review.id

    db_session.expunge(
        review
    )

    result = await repository.get_by_id(
        review_id
    )

    assert result is not None
    assert result.id == review_id
    assert result.rating == 5

    assert (
        result.comment
        == "Отличная работа!"
    )


@pytest.mark.anyio
async def test_get_review_by_id_not_found(
    db_session: AsyncSession,
):
    repository = ReviewRepository(
        db_session
    )

    result = await repository.get_by_id(
        uuid.uuid4()
    )

    assert result is None


@pytest.mark.anyio
async def test_get_review_by_booking_id(
    db_session: AsyncSession,
    completed_booking: Booking,
    review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    result = (
        await repository.get_by_booking_id(
            completed_booking.id
        )
    )

    assert result is not None
    assert result.id == review.id

    assert (
        result.booking_id
        == completed_booking.id
    )


@pytest.mark.anyio
async def test_get_review_by_booking_id_not_found(
    db_session: AsyncSession,
):
    repository = ReviewRepository(
        db_session
    )

    result = (
        await repository.get_by_booking_id(
            uuid.uuid4()
        )
    )

    assert result is None


@pytest.mark.anyio
async def test_get_reviews_by_master_id_sorted_and_scoped(
    db_session: AsyncSession,
    master: Master,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
    foreign_master_review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    result = (
        await repository.get_by_master_id(
            master.id
        )
    )

    assert [
        item.id
        for item in result
    ] == [
        deleted_user_review.id,
        second_review.id,
        review.id,
    ]

    assert all(
        item.master_id == master.id
        for item in result
    )

    assert foreign_master_review.id not in {
        item.id
        for item in result
    }


@pytest.mark.anyio
async def test_get_reviews_by_master_id_empty(
    db_session: AsyncSession,
):
    repository = ReviewRepository(
        db_session
    )

    result = (
        await repository.get_by_master_id(
            uuid.uuid4()
        )
    )

    assert result == []


@pytest.mark.anyio
async def test_get_master_stats(
    db_session: AsyncSession,
    master: Master,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    average_rating, reviews_count = (
        await repository.get_master_stats(
            master.id
        )
    )

    assert average_rating == 4.0
    assert reviews_count == 3


@pytest.mark.anyio
async def test_get_master_stats_empty(
    db_session: AsyncSession,
):
    repository = ReviewRepository(
        db_session
    )

    average_rating, reviews_count = (
        await repository.get_master_stats(
            uuid.uuid4()
        )
    )

    assert average_rating == 0.0
    assert reviews_count == 0


@pytest.mark.anyio
async def test_get_public_reviews_by_master_id(
    db_session: AsyncSession,
    master: Master,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
    foreign_master_review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    rows = (
        await repository.get_public_by_master_id(
            master.id
        )
    )

    assert [
        item[0].id
        for item in rows
    ] == [
        deleted_user_review.id,
        second_review.id,
        review.id,
    ]

    (
        deleted_review,
        deleted_first_name,
        deleted_last_name,
    ) = rows[0]

    assert (
        deleted_review.id
        == deleted_user_review.id
    )

    assert deleted_first_name is None
    assert deleted_last_name is None

    (
        second_result,
        second_first_name,
        second_last_name,
    ) = rows[1]

    assert second_result.id == second_review.id

    assert (
        second_first_name
        == "Ivan"
    )

    assert (
        second_last_name
        == "Ivanov"
    )

    assert foreign_master_review.id not in {
        item[0].id
        for item in rows
    }


@pytest.mark.anyio
async def test_get_rating_distribution(
    db_session: AsyncSession,
    master: Master,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    result = (
        await repository.get_rating_distribution(
            master.id
        )
    )

    assert result == {
        1: 0,
        2: 0,
        3: 1,
        4: 1,
        5: 1,
    }


@pytest.mark.anyio
async def test_get_rating_distribution_empty(
    db_session: AsyncSession,
):
    repository = ReviewRepository(
        db_session
    )

    result = (
        await repository.get_rating_distribution(
            uuid.uuid4()
        )
    )

    assert result == {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
    }


@pytest.mark.anyio
async def test_get_reviews_for_master_dashboard(
    db_session: AsyncSession,
    master: Master,
    offering: MasterOffering,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
    foreign_master_review: Review,
):
    repository = ReviewRepository(
        db_session
    )

    rows = (
        await repository.get_for_master_dashboard(
            master.id
        )
    )

    assert [
        item[0].id
        for item in rows
    ] == [
        deleted_user_review.id,
        second_review.id,
        review.id,
    ]

    (
        deleted_review,
        deleted_offering_id,
        deleted_offering_title,
        deleted_first_name,
        deleted_last_name,
    ) = rows[0]

    assert (
        deleted_review.id
        == deleted_user_review.id
    )

    assert (
        deleted_offering_id
        == offering.id
    )

    assert (
        deleted_offering_title
        == "Classic Cut"
    )

    assert deleted_first_name is None
    assert deleted_last_name is None

    (
        normal_review,
        normal_offering_id,
        normal_offering_title,
        first_name,
        last_name,
    ) = rows[1]

    assert (
        normal_review.id
        == second_review.id
    )

    assert (
        normal_offering_id
        == offering.id
    )

    assert (
        normal_offering_title
        == "Classic Cut"
    )

    assert first_name == "Ivan"
    assert last_name == "Ivanov"

    assert foreign_master_review.id not in {
        item[0].id
        for item in rows
    }