import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

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
    MasterOfferingUpdate,
    OfferingSort,
)
from src.master_offering.service import (
    MasterOfferingService,
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


def make_offering(
    *,
    master_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> MasterOffering:
    return MasterOffering(
        id=uuid.uuid4(),
        master_id=master_id or uuid.uuid4(),
        category_id=category_id or uuid.uuid4(),
        title="Classic Cut",
        description="Professional service.",
        price=Decimal("25.00"),
        duration_minutes=60,
        is_active=is_active,
    )


def make_category(
    *,
    category_id: uuid.UUID | None = None,
    is_active: bool = True,
):
    return SimpleNamespace(
        id=category_id or uuid.uuid4(),
        is_active=is_active,
    )


def make_tag(
    *,
    tag_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> Tag:
    return Tag(
        id=tag_id or uuid.uuid4(),
        name="Hair",
        slug="hair",
        is_active=is_active,
    )


@pytest.fixture
def offering_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterOfferingRepository
    )


@pytest.fixture
def category_repository() -> AsyncMock:
    return AsyncMock(
        spec=CategoryRepository
    )


@pytest.fixture
def tag_repository() -> AsyncMock:
    return AsyncMock(
        spec=TagRepository
    )


@pytest.fixture
def image_repository() -> AsyncMock:
    repository = AsyncMock(
        spec=OfferingImageRepository
    )

    repository.get_by_offering_id.return_value = []

    return repository


@pytest.fixture
def image_storage() -> AsyncMock:
    return AsyncMock(
        spec=LocalImageStorage
    )


@pytest.fixture
def offering_service(
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
    image_repository: AsyncMock,
    image_storage: AsyncMock,
) -> MasterOfferingService:
    return MasterOfferingService(
        repository=offering_repository,
        category_repository=category_repository,
        tag_repository=tag_repository,
        image_repository=image_repository,
        image_storage=image_storage,
    )


@pytest.mark.anyio
async def test_get_offering_by_id(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering = make_offering()

    offering_repository.get_by_id.return_value = offering

    result = await offering_service.get_offering_by_id(
        offering.id
    )

    assert result is offering

    offering_repository.get_by_id.assert_awaited_once_with(
        offering.id
    )


@pytest.mark.anyio
async def test_get_public_offering_by_id(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering = make_offering()

    offering_repository.get_public_by_id.return_value = (
        offering
    )

    result = (
        await offering_service.get_public_offering_by_id(
            offering.id
        )
    )

    assert result is offering

    offering_repository.get_public_by_id.assert_awaited_once_with(
        offering.id
    )


@pytest.mark.anyio
async def test_get_public_offering_by_id_not_found(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering_id = uuid.uuid4()

    offering_repository.get_public_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await offering_service.get_public_offering_by_id(
            offering_id
        )


@pytest.mark.anyio
async def test_get_offerings(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offerings = [
        make_offering(),
        make_offering(),
    ]

    offering_repository.get_all.return_value = offerings

    result = await offering_service.get_offerings()

    assert result == offerings

    offering_repository.get_all.assert_awaited_once_with()


@pytest.mark.anyio
async def test_create_offering(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    category_id = uuid.uuid4()
    tag_id = uuid.uuid4()

    category = make_category(
        category_id=category_id
    )

    tag = make_tag(
        tag_id=tag_id
    )

    category_repository.get_by_id.return_value = (
        category
    )

    tag_repository.get_by_ids.return_value = [
        tag,
    ]

    offering_repository.create.side_effect = (
        lambda offering: offering
    )

    data = MasterOfferingCreate(
        category_id=category_id,
        title="Hair Styling",
        description="Professional styling.",
        price=Decimal("35.50"),
        duration_minutes=60,
        tag_ids=[
            tag_id,
        ],
    )

    result = await offering_service.create_offering(
        master_id=master_id,
        data=data,
    )

    assert result.master_id == master_id
    assert result.category_id == category_id
    assert result.title == "Hair Styling"
    assert (
        result.description
        == "Professional styling."
    )
    assert result.price == Decimal("35.50")
    assert result.duration_minutes == 60
    assert result.tags == [
        tag,
    ]

    category_repository.get_by_id.assert_awaited_once_with(
        category_id
    )

    tag_repository.get_by_ids.assert_awaited_once_with(
        [
            tag_id,
        ]
    )

    offering_repository.create.assert_awaited_once_with(
        result
    )


@pytest.mark.anyio
async def test_create_offering_category_not_found(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    category_id = uuid.uuid4()

    category_repository.get_by_id.return_value = None

    data = MasterOfferingCreate(
        category_id=category_id,
        title="Hair Styling",
        description="Professional styling.",
        price=Decimal("35.50"),
        duration_minutes=60,
    )

    with pytest.raises(
        CategoryNotFoundError
    ):
        await offering_service.create_offering(
            master_id=uuid.uuid4(),
            data=data,
        )

    tag_repository.get_by_ids.assert_not_awaited()
    offering_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_offering_inactive_category(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    category_id = uuid.uuid4()

    category_repository.get_by_id.return_value = (
        make_category(
            category_id=category_id,
            is_active=False,
        )
    )

    data = MasterOfferingCreate(
        category_id=category_id,
        title="Hair Styling",
        description="Professional styling.",
        price=Decimal("35.50"),
        duration_minutes=60,
    )

    with pytest.raises(
        CategoryInactiveError
    ):
        await offering_service.create_offering(
            master_id=uuid.uuid4(),
            data=data,
        )

    tag_repository.get_by_ids.assert_not_awaited()
    offering_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_offering_tag_not_found(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    category_id = uuid.uuid4()
    tag_id = uuid.uuid4()

    category_repository.get_by_id.return_value = (
        make_category(
            category_id=category_id
        )
    )

    tag_repository.get_by_ids.return_value = []

    data = MasterOfferingCreate(
        category_id=category_id,
        title="Hair Styling",
        description="Professional styling.",
        price=Decimal("35.50"),
        duration_minutes=60,
        tag_ids=[
            tag_id,
        ],
    )

    with pytest.raises(
        TagNotFoundError
    ):
        await offering_service.create_offering(
            master_id=uuid.uuid4(),
            data=data,
        )

    offering_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_offering_inactive_tag(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    category_id = uuid.uuid4()
    tag_id = uuid.uuid4()

    category_repository.get_by_id.return_value = (
        make_category(
            category_id=category_id
        )
    )

    tag_repository.get_by_ids.return_value = [
        make_tag(
            tag_id=tag_id,
            is_active=False,
        ),
    ]

    data = MasterOfferingCreate(
        category_id=category_id,
        title="Hair Styling",
        description="Professional styling.",
        price=Decimal("35.50"),
        duration_minutes=60,
        tag_ids=[
            tag_id,
        ],
    )

    with pytest.raises(
        TagInactiveError
    ):
        await offering_service.create_offering(
            master_id=uuid.uuid4(),
            data=data,
        )

    offering_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_offering_deduplicates_tag_ids(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    category_id = uuid.uuid4()
    tag_id = uuid.uuid4()

    category_repository.get_by_id.return_value = (
        make_category(
            category_id=category_id
        )
    )

    tag = make_tag(
        tag_id=tag_id
    )

    tag_repository.get_by_ids.return_value = [
        tag,
    ]

    offering_repository.create.side_effect = (
        lambda offering: offering
    )

    data = MasterOfferingCreate(
        category_id=category_id,
        title="Hair Styling",
        description="Professional styling.",
        price=Decimal("35.50"),
        duration_minutes=60,
        tag_ids=[
            tag_id,
            tag_id,
        ],
    )

    result = await offering_service.create_offering(
        master_id=uuid.uuid4(),
        data=data,
    )

    tag_repository.get_by_ids.assert_awaited_once_with(
        [
            tag_id,
        ]
    )

    assert result.tags == [
        tag,
    ]


@pytest.mark.anyio
async def test_update_offering_not_found(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering_id = uuid.uuid4()

    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await offering_service.update_offering(
            offering_id=offering_id,
            master_id=uuid.uuid4(),
            data=MasterOfferingUpdate(
                title="Updated Service"
            ),
        )

    offering_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_offering_access_denied(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering = make_offering()

    offering_repository.get_by_id.return_value = offering

    with pytest.raises(
        OfferingAccessDeniedError
    ):
        await offering_service.update_offering(
            offering_id=offering.id,
            master_id=uuid.uuid4(),
            data=MasterOfferingUpdate(
                title="Updated Service"
            ),
        )

    offering_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_offering(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    offering_repository.update.side_effect = (
        lambda offering: offering
    )

    data = MasterOfferingUpdate(
        title="Updated Service",
        description="Updated description.",
        price=Decimal("45.75"),
        duration_minutes=90,
    )

    result = await offering_service.update_offering(
        offering_id=offering.id,
        master_id=master_id,
        data=data,
    )

    assert result is offering
    assert offering.title == "Updated Service"
    assert (
        offering.description
        == "Updated description."
    )
    assert offering.price == Decimal("45.75")
    assert offering.duration_minutes == 90

    category_repository.get_by_id.assert_not_awaited()
    tag_repository.get_by_ids.assert_not_awaited()

    offering_repository.update.assert_awaited_once_with(
        offering
    )


@pytest.mark.anyio
async def test_update_offering_category_not_found(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    category_id = uuid.uuid4()

    offering_repository.get_by_id.return_value = (
        offering
    )

    category_repository.get_by_id.return_value = None

    with pytest.raises(
        CategoryNotFoundError
    ):
        await offering_service.update_offering(
            offering_id=offering.id,
            master_id=master_id,
            data=MasterOfferingUpdate(
                category_id=category_id
            ),
        )

    offering_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_offering_inactive_category(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    category_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    category_id = uuid.uuid4()

    offering_repository.get_by_id.return_value = (
        offering
    )

    category_repository.get_by_id.return_value = (
        make_category(
            category_id=category_id,
            is_active=False,
        )
    )

    with pytest.raises(
        CategoryInactiveError
    ):
        await offering_service.update_offering(
            offering_id=offering.id,
            master_id=master_id,
            data=MasterOfferingUpdate(
                category_id=category_id
            ),
        )

    offering_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_offering_tags(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    tag_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    tag_id = uuid.uuid4()

    tag = make_tag(
        tag_id=tag_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    offering_repository.update.side_effect = (
        lambda offering: offering
    )

    tag_repository.get_by_ids.return_value = [
        tag,
    ]

    result = await offering_service.update_offering(
        offering_id=offering.id,
        master_id=master_id,
        data=MasterOfferingUpdate(
            tag_ids=[
                tag_id,
            ]
        ),
    )

    assert result.tags == [
        tag,
    ]

    tag_repository.get_by_ids.assert_awaited_once_with(
        [
            tag_id,
        ]
    )

    offering_repository.update.assert_awaited_once_with(
        offering
    )


@pytest.mark.anyio
async def test_delete_offering_not_found(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await offering_service.delete_offering(
            offering_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
        )

    offering_repository.has_bookings.assert_not_awaited()
    offering_repository.hard_delete.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_offering_access_denied(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering = make_offering()

    offering_repository.get_by_id.return_value = offering

    with pytest.raises(
        OfferingAccessDeniedError
    ):
        await offering_service.delete_offering(
            offering_id=offering.id,
            master_id=uuid.uuid4(),
        )

    offering_repository.has_bookings.assert_not_awaited()
    offering_repository.hard_delete.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_offering_without_bookings_hard_deletes(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
    image_repository: AsyncMock,
    image_storage: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    first_image = SimpleNamespace(
        storage_key="offerings/first.jpg"
    )

    second_image = SimpleNamespace(
        storage_key="offerings/second.webp"
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    offering_repository.has_bookings.return_value = False

    image_repository.get_by_offering_id.return_value = [
        first_image,
        second_image,
    ]

    result = await offering_service.delete_offering(
        offering_id=offering.id,
        master_id=master_id,
    )

    assert result is None

    offering_repository.has_bookings.assert_awaited_once_with(
        offering.id
    )

    image_repository.get_by_offering_id.assert_awaited_once_with(
        offering.id
    )

    offering_repository.hard_delete.assert_awaited_once_with(
        offering
    )

    assert image_storage.delete.await_count == 2

    image_storage.delete.assert_any_await(
        "offerings/first.jpg"
    )

    image_storage.delete.assert_any_await(
        "offerings/second.webp"
    )

    offering_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_offering_with_bookings_deactivates(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    offering_repository.has_bookings.return_value = True

    await offering_service.delete_offering(
        offering_id=offering.id,
        master_id=master_id,
    )

    assert offering.is_active is False

    offering_repository.update.assert_awaited_once_with(
        offering
    )

    offering_repository.hard_delete.assert_not_awaited()


@pytest.mark.anyio
async def test_get_master_offerings(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offerings = [
        make_offering(
            master_id=master_id
        ),
    ]

    offering_repository.get_by_master_id.return_value = (
        offerings
    )

    result = await offering_service.get_master_offerings(
        master_id=master_id,
        active_only=False,
    )

    assert result == offerings

    offering_repository.get_by_master_id.assert_awaited_once_with(
        master_id=master_id,
        active_only=False,
    )


@pytest.mark.anyio
async def test_get_public_offerings_builds_page(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    category_id = uuid.uuid4()
    city_id = uuid.uuid4()
    district_id = uuid.uuid4()

    offering_repository.get_public_offerings.return_value = (
        [],
        25,
    )

    result = await offering_service.get_public_offerings(
        category_id=category_id,
        min_price=Decimal("10.00"),
        max_price=Decimal("100.00"),
        discounted_only=False,
        sort=OfferingSort.PRICE_ASC,
        city_id=city_id,
        district_id=district_id,
        search="hair",
        page=2,
        page_size=10,
    )

    assert result.items == []
    assert result.total == 25
    assert result.page == 2
    assert result.page_size == 10
    assert result.total_pages == 3

    offering_repository.get_public_offerings.assert_awaited_once_with(
        category_id=category_id,
        min_price=Decimal("10.00"),
        max_price=Decimal("100.00"),
        sort=OfferingSort.PRICE_ASC,
        search="hair",
        city_id=city_id,
        district_id=district_id,
        discounted_only=False,
        exclude_master_id=None,
        offset=10,
        limit=10,
    )


@pytest.mark.anyio
async def test_get_public_offerings_empty_page(
    offering_service: MasterOfferingService,
    offering_repository: AsyncMock,
):
    offering_repository.get_public_offerings.return_value = (
        [],
        0,
    )

    result = await offering_service.get_public_offerings(
        page=1,
        page_size=12,
    )

    assert result.items == []
    assert result.total == 0
    assert result.total_pages == 0

    offering_repository.get_public_offerings.assert_awaited_once_with(
        category_id=None,
        min_price=None,
        max_price=None,
        discounted_only=False,
        sort=None,
        search=None,
        city_id=None,
        district_id=None,
        exclude_master_id=None,
        offset=0,
        limit=12,
    )