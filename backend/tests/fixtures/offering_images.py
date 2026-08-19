from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_offering.models import MasterOffering
from src.offering_images import (
    dependencies as offering_image_dependencies,
)
from src.offering_images.models import OfferingImage
from src.offering_images.storage import LocalImageStorage


@pytest.fixture
def image_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> LocalImageStorage:
    storage = LocalImageStorage.__new__(
        LocalImageStorage
    )

    storage.uploads_dir = (
        tmp_path / "uploads"
    )

    storage.offerings_dir = (
        storage.uploads_dir / "offerings"
    )

    storage.offerings_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    monkeypatch.setattr(
        offering_image_dependencies,
        "LocalImageStorage",
        lambda: storage,
    )

    return storage


@pytest.fixture
def png_bytes() -> bytes:
    buffer = BytesIO()

    image = Image.new(
        "RGB",
        (
            8,
            8,
        ),
    )

    image.save(
        buffer,
        format="PNG",
    )

    image.close()

    return buffer.getvalue()


@pytest.fixture
async def offering_image(
    db_session: AsyncSession,
    offering: MasterOffering,
) -> OfferingImage:
    image = OfferingImage(
        offering_id=offering.id,
        storage_key=(
            "offerings/primary.png"
        ),
        is_primary=True,
        sort_order=10,
    )

    db_session.add(image)
    await db_session.commit()
    await db_session.refresh(image)

    return image


@pytest.fixture
async def second_offering_image(
    db_session: AsyncSession,
    offering: MasterOffering,
) -> OfferingImage:
    image = OfferingImage(
        offering_id=offering.id,
        storage_key=(
            "offerings/secondary.png"
        ),
        is_primary=False,
        sort_order=0,
    )

    db_session.add(image)
    await db_session.commit()
    await db_session.refresh(image)

    return image


@pytest.fixture
async def foreign_offering_image(
    db_session: AsyncSession,
    second_master_offering: MasterOffering,
) -> OfferingImage:
    image = OfferingImage(
        offering_id=second_master_offering.id,
        storage_key=(
            "offerings/foreign.png"
        ),
        is_primary=True,
        sort_order=0,
    )

    db_session.add(image)
    await db_session.commit()
    await db_session.refresh(image)

    return image


@pytest.fixture
async def stored_offering_image(
    db_session: AsyncSession,
    offering: MasterOffering,
    image_storage: LocalImageStorage,
    png_bytes: bytes,
) -> OfferingImage:
    storage_key = await image_storage.save(
        content=png_bytes,
        extension="png",
    )

    image = OfferingImage(
        offering_id=offering.id,
        storage_key=storage_key,
        is_primary=True,
        sort_order=0,
    )

    db_session.add(image)
    await db_session.commit()
    await db_session.refresh(image)

    return image