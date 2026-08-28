import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_offering.models import MasterOffering
from src.offering_images.models import OfferingImage
from src.offering_images.repository import (
    OfferingImageRepository,
)


def make_image(
    *,
    offering_id: uuid.UUID,
    storage_key: str,
    is_primary: bool = False,
    sort_order: int = 0,
) -> OfferingImage:
    return OfferingImage(
        offering_id=offering_id,
        storage_key=storage_key,
        is_primary=is_primary,
        sort_order=sort_order,
    )


@pytest.mark.anyio
async def test_create_image(
    db_session: AsyncSession,
    offering: MasterOffering,
):
    repository = OfferingImageRepository(db_session)

    image = make_image(
        offering_id=offering.id,
        storage_key="offerings/test.png",
        is_primary=True,
        sort_order=0,
    )

    result = await repository.create(image)

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )

    assert result.offering_id == offering.id
    assert result.storage_key == "offerings/test.png"
    assert result.is_primary is True
    assert result.sort_order == 0
    assert result.created_at is not None


@pytest.mark.anyio
async def test_get_image_by_id(
    db_session: AsyncSession,
    offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    image_id = offering_image.id

    db_session.expunge(offering_image)

    result = await repository.get_by_id(image_id)

    assert result is not None
    assert result.id == image_id
    assert result.storage_key == "offerings/primary.png"


@pytest.mark.anyio
async def test_get_image_by_id_not_found(
    db_session: AsyncSession,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_get_images_by_offering_id_sorted(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    third_image = make_image(
        offering_id=offering.id,
        storage_key="offerings/third.png",
        is_primary=False,
        sort_order=5,
    )

    await repository.create(third_image)

    result = await repository.get_by_offering_id(offering.id)

    assert [image.id for image in result] == [
        offering_image.id,
        second_offering_image.id,
        third_image.id,
    ]

    assert result[0].is_primary is True
    assert result[1].sort_order == 0
    assert result[2].sort_order == 5


@pytest.mark.anyio
async def test_count_images_by_offering_id(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.count_by_offering_id(offering.id)

    assert result == 2


@pytest.mark.anyio
async def test_count_images_by_offering_id_empty(
    db_session: AsyncSession,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.count_by_offering_id(uuid.uuid4())

    assert result == 0


@pytest.mark.anyio
async def test_get_primary_image(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.get_primary(offering.id)

    assert result is not None
    assert result.id == offering_image.id
    assert result.is_primary is True


@pytest.mark.anyio
async def test_get_primary_image_not_found(
    db_session: AsyncSession,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.get_primary(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_update_image(
    db_session: AsyncSession,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    second_offering_image.sort_order = 7

    result = await repository.update(second_offering_image)

    assert result.sort_order == 7

    image_id = result.id

    db_session.expunge(result)

    image_from_database = await repository.get_by_id(image_id)

    assert image_from_database is not None
    assert image_from_database.sort_order == 7


@pytest.mark.anyio
async def test_delete_image(
    db_session: AsyncSession,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    image_id = second_offering_image.id

    await repository.delete(second_offering_image)

    result = await repository.get_by_id(image_id)

    assert result is None


@pytest.mark.anyio
async def test_set_primary_image(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.set_primary(
        offering_id=offering.id,
        image_id=second_offering_image.id,
    )

    assert result is not None
    assert result.id == second_offering_image.id
    assert result.is_primary is True

    old_primary = await repository.get_by_id(offering_image.id)

    assert old_primary is not None
    assert old_primary.is_primary is False

    primary = await repository.get_primary(offering.id)

    assert primary is not None
    assert primary.id == second_offering_image.id


@pytest.mark.anyio
async def test_set_primary_image_not_found(
    db_session: AsyncSession,
    offering: MasterOffering,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.set_primary(
        offering_id=offering.id,
        image_id=uuid.uuid4(),
    )

    assert result is None


@pytest.mark.anyio
async def test_set_primary_image_from_other_offering_returns_none(
    db_session: AsyncSession,
    offering: MasterOffering,
    foreign_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    result = await repository.set_primary(
        offering_id=offering.id,
        image_id=foreign_offering_image.id,
    )

    assert result is None


@pytest.mark.anyio
async def test_delete_primary_image_promotes_next(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    primary_id = offering_image.id

    await repository.delete_with_primary_fallback(offering_image)

    deleted_image = await repository.get_by_id(primary_id)

    assert deleted_image is None

    new_primary = await repository.get_primary(offering.id)

    assert new_primary is not None
    assert new_primary.id == second_offering_image.id
    assert new_primary.is_primary is True


@pytest.mark.anyio
async def test_delete_non_primary_keeps_existing_primary(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    await repository.delete_with_primary_fallback(second_offering_image)

    primary = await repository.get_primary(offering.id)

    assert primary is not None
    assert primary.id == offering_image.id
    assert primary.is_primary is True


@pytest.mark.anyio
async def test_delete_last_primary_leaves_no_primary(
    db_session: AsyncSession,
    offering: MasterOffering,
    offering_image: OfferingImage,
):
    repository = OfferingImageRepository(db_session)

    await repository.delete_with_primary_fallback(offering_image)

    primary = await repository.get_primary(offering.id)

    assert primary is None

    count = await repository.count_by_offering_id(offering.id)

    assert count == 0
