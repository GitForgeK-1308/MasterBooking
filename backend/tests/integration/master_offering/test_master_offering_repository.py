import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import Booking, BookingStatus
from src.categories.models import Category
from src.locations.models import City, District
from src.master_offering.models import MasterOffering
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_offering.schemas import OfferingSort
from src.masters.models import Master
from src.tags.models import Tag


def make_offering(
    *,
    master_id: uuid.UUID,
    category_id: uuid.UUID,
    title: str = "Classic Cut",
    description: str = "Professional service.",
    price: Decimal = Decimal("25.00"),
    duration_minutes: int = 60,
    is_active: bool = True,
) -> MasterOffering:
    return MasterOffering(
        master_id=master_id,
        category_id=category_id,
        title=title,
        description=description,
        price=price,
        duration_minutes=duration_minutes,
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_create_offering(
    db_session: AsyncSession,
    master: Master,
    category: Category,
    tag: Tag,
):
    repository = MasterOfferingRepository(db_session)

    offering = make_offering(
        master_id=master.id,
        category_id=category.id,
    )

    offering.tags = [
        tag,
    ]

    result = await repository.create(offering)

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )

    assert result.master_id == master.id
    assert result.category_id == category.id
    assert result.title == "Classic Cut"
    assert result.price == Decimal("25.00")

    assert {item.id for item in result.tags} == {
        tag.id,
    }

    assert result.master.id == master.id


@pytest.mark.anyio
async def test_get_all_offerings(
    db_session: AsyncSession,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
    second_master_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.get_all()

    assert {item.id for item in result} == {
        offering.id,
        inactive_offering.id,
        second_master_offering.id,
    }


@pytest.mark.anyio
async def test_get_offering_by_id(
    db_session: AsyncSession,
    offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    offering_id = offering.id

    db_session.expunge(offering)

    result = await repository.get_by_id(offering_id)

    assert result is not None
    assert result.id == offering_id
    assert result.title == "Classic Cut"

    assert result.master is not None

    assert len(result.tags) == 1


@pytest.mark.anyio
async def test_get_offering_by_id_not_found(
    db_session: AsyncSession,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_get_public_offering_by_id(
    db_session: AsyncSession,
    offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.get_public_by_id(offering.id)

    assert result is not None
    assert result.id == offering.id


@pytest.mark.anyio
async def test_get_public_offering_by_id_excludes_inactive(
    db_session: AsyncSession,
    inactive_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.get_public_by_id(inactive_offering.id)

    assert result is None


@pytest.mark.anyio
async def test_get_by_master_id_active_only(
    db_session: AsyncSession,
    master: Master,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.get_by_master_id(
        master_id=master.id,
        active_only=True,
    )

    ids = {item.id for item in result}

    assert offering.id in ids
    assert inactive_offering.id not in ids


@pytest.mark.anyio
async def test_get_by_master_id_includes_inactive(
    db_session: AsyncSession,
    master: Master,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.get_by_master_id(
        master_id=master.id,
        active_only=False,
    )

    ids = {item.id for item in result}

    assert offering.id in ids
    assert inactive_offering.id in ids


@pytest.mark.anyio
async def test_update_offering(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_category: Category,
    second_tag: Tag,
):
    repository = MasterOfferingRepository(db_session)

    await db_session.refresh(
        offering,
        attribute_names=["tags"],
    )

    offering.title = "Updated Service"
    offering.description = "Updated description."
    offering.price = Decimal("45.75")
    offering.duration_minutes = 90
    offering.category_id = second_category.id
    offering.tags = [
        second_tag,
    ]

    result = await repository.update(offering)

    assert result.title == "Updated Service"
    assert result.description == "Updated description."
    assert result.price == Decimal("45.75")
    assert result.duration_minutes == 90
    assert result.category_id == second_category.id

    assert {tag.id for tag in result.tags} == {
        second_tag.id,
    }

    offering_id = result.id

    db_session.expunge(result)

    offering_from_database = await repository.get_by_id(offering_id)

    assert offering_from_database is not None
    assert offering_from_database.title == "Updated Service"
    assert offering_from_database.price == Decimal("45.75")

    assert {tag.id for tag in offering_from_database.tags} == {
        second_tag.id,
    }


@pytest.mark.anyio
async def test_hard_delete_offering(
    db_session: AsyncSession,
    offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    offering_id = offering.id

    await repository.hard_delete(offering)

    result = await repository.get_by_id(offering_id)

    assert result is None


@pytest.mark.anyio
async def test_has_bookings_false(
    db_session: AsyncSession,
    offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.has_bookings(offering.id)

    assert result is False


@pytest.mark.anyio
async def test_has_bookings_true(
    db_session: AsyncSession,
    offering: MasterOffering,
    booking: Booking,
):
    repository = MasterOfferingRepository(db_session)

    result = await repository.has_bookings(offering.id)

    assert result is True


@pytest.mark.anyio
async def test_public_offerings_exclude_inactive_entities(
    db_session: AsyncSession,
    master: Master,
    inactive_master: Master,
    category: Category,
    inactive_category: Category,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    inactive_master_offering = make_offering(
        master_id=inactive_master.id,
        category_id=category.id,
        title="Inactive Master Service",
    )

    await repository.create(inactive_master_offering)

    inactive_category_offering = make_offering(
        master_id=master.id,
        category_id=inactive_category.id,
        title="Inactive Category Service",
    )

    await repository.create(inactive_category_offering)

    result, total = await repository.get_public_offerings()

    ids = {item.id for item in result}

    assert total == 1

    assert ids == {
        offering.id,
    }

    assert inactive_offering.id not in ids
    assert inactive_master_offering.id not in ids
    assert inactive_category_offering.id not in ids


@pytest.mark.anyio
async def test_public_offerings_category_filter_includes_children(
    db_session: AsyncSession,
    category: Category,
    offering: MasterOffering,
    child_category_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result, total = await repository.get_public_offerings(
        category_id=category.id,
    )

    assert total == 2

    assert {item.id for item in result} == {
        offering.id,
        child_category_offering.id,
    }


@pytest.mark.anyio
async def test_public_offerings_price_filter(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_master_offering: MasterOffering,
    child_category_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result, total = await repository.get_public_offerings(
        min_price=Decimal("30.00"),
        max_price=Decimal("50.00"),
    )

    assert total == 1

    assert [item.id for item in result] == [second_master_offering.id]

    assert offering.id not in {item.id for item in result}

    assert child_category_offering.id not in {item.id for item in result}


@pytest.mark.anyio
async def test_public_offerings_location_filter(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_master_offering: MasterOffering,
    city: City,
    district: District,
):
    repository = MasterOfferingRepository(db_session)

    result, total = await repository.get_public_offerings(
        city_id=city.id,
        district_id=district.id,
    )

    assert total == 1

    assert [item.id for item in result] == [offering.id]

    assert second_master_offering.id not in {item.id for item in result}


@pytest.mark.anyio
async def test_public_offerings_search_by_tag(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_master_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result, total = await repository.get_public_offerings(
        search="hair",
    )

    assert total == 1

    assert [item.id for item in result] == [offering.id]

    assert second_master_offering.id not in {item.id for item in result}


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "sort",
        "expected_order",
    ),
    [
        (
            OfferingSort.PRICE_ASC,
            [
                "Classic Cut",
                "Nail Care",
                "Coloring Service",
            ],
        ),
        (
            OfferingSort.PRICE_DESC,
            [
                "Coloring Service",
                "Nail Care",
                "Classic Cut",
            ],
        ),
    ],
)
async def test_public_offerings_price_sort(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_master_offering: MasterOffering,
    child_category_offering: MasterOffering,
    sort: OfferingSort,
    expected_order: list[str],
):
    repository = MasterOfferingRepository(db_session)

    result, total = await repository.get_public_offerings(
        sort=sort,
    )

    assert total == 3

    assert [item.title for item in result] == expected_order


@pytest.mark.anyio
async def test_public_offerings_popular_sort_excludes_cancelled_bookings(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_master_offering: MasterOffering,
    child_category_offering: MasterOffering,
    booking: Booking,
    second_booking: Booking,
    future_booking_date: date,
):
    repository = MasterOfferingRepository(db_session)

    booking.status = BookingStatus.CANCELLED
    second_booking.status = BookingStatus.CANCELLED

    active_booking = Booking(
        client_id=booking.client_id,
        master_id=second_master_offering.master_id,
        offering_id=second_master_offering.id,
        booking_date=future_booking_date,
        start_time=time(
            10,
            0,
        ),
        end_time=time(
            11,
            30,
        ),
        client_name="Test Client",
        client_phone="+79990000000",
        client_email="client@example.com",
        status=BookingStatus.PENDING,
    )

    db_session.add(active_booking)

    await db_session.commit()

    result, total = await repository.get_public_offerings(
        sort=OfferingSort.POPULAR,
    )

    assert total == 3

    assert result[0].id == second_master_offering.id

    assert {item.id for item in result} == {
        offering.id,
        second_master_offering.id,
        child_category_offering.id,
    }


@pytest.mark.anyio
async def test_public_offerings_pagination(
    db_session: AsyncSession,
    offering: MasterOffering,
    second_master_offering: MasterOffering,
    child_category_offering: MasterOffering,
):
    repository = MasterOfferingRepository(db_session)

    result, total = await repository.get_public_offerings(
        offset=1,
        limit=1,
    )

    assert total == 3

    assert len(result) == 1

    assert result[0].id == child_category_offering.id
