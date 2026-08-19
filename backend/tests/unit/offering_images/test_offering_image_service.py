import uuid
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    create_autospec,
)

import pytest
from fastapi import UploadFile
from PIL import Image

from src.master_offering.exceptions import (
    OfferingNotFoundError,
)
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.offering_images.exceptions import (
    InvalidOfferingImageTypeError,
    OfferingImageAccessDeniedError,
    OfferingImageLimitExceededError,
    OfferingImageNotFoundError,
    OfferingImageTooLargeError,
)
from src.offering_images.models import OfferingImage
from src.offering_images.repository import (
    OfferingImageRepository,
)
from src.offering_images.service import (
    MAX_IMAGE_SIZE,
    OfferingImageService,
)
from src.offering_images.storage import (
    LocalImageStorage,
)


def make_image_bytes(
    image_format: str,
) -> bytes:
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
        format=image_format,
    )

    image.close()

    return buffer.getvalue()


def make_upload_file(
    content: bytes,
    filename: str = "image.png",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
    )


def make_offering(
    *,
    offering_id: uuid.UUID | None = None,
    master_id: uuid.UUID | None = None,
):
    return SimpleNamespace(
        id=offering_id or uuid.uuid4(),
        master_id=master_id or uuid.uuid4(),
    )


def make_offering_image(
    *,
    offering_id: uuid.UUID | None = None,
    storage_key: str = "offerings/image.png",
    is_primary: bool = False,
    sort_order: int = 0,
) -> OfferingImage:
    return OfferingImage(
        id=uuid.uuid4(),
        offering_id=offering_id or uuid.uuid4(),
        storage_key=storage_key,
        is_primary=is_primary,
        sort_order=sort_order,
    )


@pytest.fixture
def image_repository() -> AsyncMock:
    return AsyncMock(
        spec=OfferingImageRepository
    )


@pytest.fixture
def offering_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterOfferingRepository
    )


@pytest.fixture
def image_storage():
    return create_autospec(
        LocalImageStorage,
        instance=True,
    )


@pytest.fixture
def image_service(
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
) -> OfferingImageService:
    return OfferingImageService(
        repository=image_repository,
        offering_repository=offering_repository,
        storage=image_storage,
    )


def test_get_image_url(
    image_service: OfferingImageService,
    image_storage,
):
    image_storage.get_url.return_value = (
        "/uploads/offerings/image.png"
    )

    result = image_service.get_image_url(
        "offerings/image.png"
    )

    assert (
        result
        == "/uploads/offerings/image.png"
    )

    image_storage.get_url.assert_called_once_with(
        "offerings/image.png"
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "image_format",
        "expected_extension",
    ),
    [
        (
            "JPEG",
            "jpg",
        ),
        (
            "PNG",
            "png",
        ),
        (
            "WEBP",
            "webp",
        ),
    ],
)
async def test_upload_first_image_supported_formats(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
    image_format: str,
    expected_extension: str,
):
    master_id = uuid.uuid4()
    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 0

    image_storage.save.return_value = (
        f"offerings/image.{expected_extension}"
    )

    image_repository.create.side_effect = (
        lambda image: image
    )

    file = make_upload_file(
        make_image_bytes(
            image_format
        )
    )

    result = await image_service.upload_image(
        offering_id=offering.id,
        master_id=master_id,
        file=file,
    )

    assert result.offering_id == offering.id
    assert (
        result.storage_key
        == f"offerings/image.{expected_extension}"
    )
    assert result.is_primary is True
    assert result.sort_order == 0

    image_repository.count_by_offering_id.assert_awaited_once_with(
        offering.id
    )

    image_storage.save.assert_awaited_once()

    save_kwargs = (
        image_storage.save.await_args.kwargs
    )

    assert (
        save_kwargs["extension"]
        == expected_extension
    )

    image_repository.create.assert_awaited_once_with(
        result
    )


@pytest.mark.anyio
async def test_upload_next_image_is_not_primary(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()
    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 3

    image_storage.save.return_value = (
        "offerings/image.png"
    )

    image_repository.create.side_effect = (
        lambda image: image
    )

    file = make_upload_file(
        make_image_bytes(
            "PNG"
        )
    )

    result = await image_service.upload_image(
        offering_id=offering.id,
        master_id=master_id,
        file=file,
    )

    assert result.is_primary is False
    assert result.sort_order == 3


@pytest.mark.anyio
async def test_upload_image_offering_not_found(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await image_service.upload_image(
            offering_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
            file=make_upload_file(
                make_image_bytes(
                    "PNG"
                )
            ),
        )

    image_repository.count_by_offering_id.assert_not_awaited()
    image_storage.save.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_image_access_denied(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    offering = make_offering()

    offering_repository.get_by_id.return_value = (
        offering
    )

    with pytest.raises(
        OfferingImageAccessDeniedError
    ):
        await image_service.upload_image(
            offering_id=offering.id,
            master_id=uuid.uuid4(),
            file=make_upload_file(
                make_image_bytes(
                    "PNG"
                )
            ),
        )

    image_repository.count_by_offering_id.assert_not_awaited()
    image_storage.save.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_image_limit_exceeded(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 20

    with pytest.raises(
        OfferingImageLimitExceededError
    ):
        await image_service.upload_image(
            offering_id=offering.id,
            master_id=master_id,
            file=make_upload_file(
                make_image_bytes(
                    "PNG"
                )
            ),
        )

    image_storage.save.assert_not_awaited()
    image_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_image_too_large(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 0

    file = make_upload_file(
        b"x" * (
            MAX_IMAGE_SIZE + 1
        )
    )

    with pytest.raises(
        OfferingImageTooLargeError
    ):
        await image_service.upload_image(
            offering_id=offering.id,
            master_id=master_id,
            file=file,
        )

    image_storage.save.assert_not_awaited()
    image_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_invalid_image_content(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 0

    with pytest.raises(
        InvalidOfferingImageTypeError
    ):
        await image_service.upload_image(
            offering_id=offering.id,
            master_id=master_id,
            file=make_upload_file(
                b"not-an-image"
            ),
        )

    image_storage.save.assert_not_awaited()
    image_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_unsupported_image_format(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 0

    with pytest.raises(
        InvalidOfferingImageTypeError
    ):
        await image_service.upload_image(
            offering_id=offering.id,
            master_id=master_id,
            file=make_upload_file(
                make_image_bytes(
                    "GIF"
                )
            ),
        )

    image_storage.save.assert_not_awaited()
    image_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_image_removes_file_when_repository_fails(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.count_by_offering_id.return_value = 0

    image_storage.save.return_value = (
        "offerings/image.png"
    )

    image_repository.create.side_effect = (
        RuntimeError("database error")
    )

    with pytest.raises(
        RuntimeError,
        match="database error",
    ):
        await image_service.upload_image(
            offering_id=offering.id,
            master_id=master_id,
            file=make_upload_file(
                make_image_bytes(
                    "PNG"
                )
            ),
        )

    image_storage.delete.assert_awaited_once_with(
        "offerings/image.png"
    )


@pytest.mark.anyio
async def test_get_offering_images(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    offering = make_offering()

    images = [
        make_offering_image(
            offering_id=offering.id
        ),
        make_offering_image(
            offering_id=offering.id
        ),
    ]

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_offering_id.return_value = (
        images
    )

    result = await image_service.get_offering_images(
        offering.id
    )

    assert result == images

    image_repository.get_by_offering_id.assert_awaited_once_with(
        offering.id
    )


@pytest.mark.anyio
async def test_get_offering_images_offering_not_found(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await image_service.get_offering_images(
            uuid.uuid4()
        )

    image_repository.get_by_offering_id.assert_not_awaited()


@pytest.mark.anyio
async def test_set_primary_image(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    image = make_offering_image(
        offering_id=offering.id
    )

    updated_image = make_offering_image(
        offering_id=offering.id,
        is_primary=True,
    )

    updated_image.id = image.id

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = (
        image
    )

    image_repository.set_primary.return_value = (
        updated_image
    )

    result = await image_service.set_primary_image(
        offering_id=offering.id,
        image_id=image.id,
        master_id=master_id,
    )

    assert result is updated_image

    image_repository.set_primary.assert_awaited_once_with(
        offering_id=offering.id,
        image_id=image.id,
    )


@pytest.mark.anyio
async def test_set_primary_offering_not_found(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await image_service.set_primary_image(
            offering_id=uuid.uuid4(),
            image_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
        )

    image_repository.get_by_id.assert_not_awaited()


@pytest.mark.anyio
async def test_set_primary_access_denied(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    offering = make_offering()

    offering_repository.get_by_id.return_value = (
        offering
    )

    with pytest.raises(
        OfferingImageAccessDeniedError
    ):
        await image_service.set_primary_image(
            offering_id=offering.id,
            image_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
        )

    image_repository.get_by_id.assert_not_awaited()


@pytest.mark.anyio
async def test_set_primary_image_not_found(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingImageNotFoundError
    ):
        await image_service.set_primary_image(
            offering_id=offering.id,
            image_id=uuid.uuid4(),
            master_id=master_id,
        )

    image_repository.set_primary.assert_not_awaited()


@pytest.mark.anyio
async def test_set_primary_image_from_other_offering(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    image = make_offering_image(
        offering_id=uuid.uuid4()
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = (
        image
    )

    with pytest.raises(
        OfferingImageNotFoundError
    ):
        await image_service.set_primary_image(
            offering_id=offering.id,
            image_id=image.id,
            master_id=master_id,
        )

    image_repository.set_primary.assert_not_awaited()


@pytest.mark.anyio
async def test_set_primary_repository_returns_none(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    image = make_offering_image(
        offering_id=offering.id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = (
        image
    )

    image_repository.set_primary.return_value = None

    with pytest.raises(
        OfferingImageNotFoundError
    ):
        await image_service.set_primary_image(
            offering_id=offering.id,
            image_id=image.id,
            master_id=master_id,
        )


@pytest.mark.anyio
async def test_delete_image(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    image = make_offering_image(
        offering_id=offering.id,
        storage_key="offerings/image.png",
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = (
        image
    )

    result = await image_service.delete_image(
        offering_id=offering.id,
        image_id=image.id,
        master_id=master_id,
    )

    assert result is None

    image_repository.delete_with_primary_fallback.assert_awaited_once_with(
        image
    )

    image_storage.delete.assert_awaited_once_with(
        "offerings/image.png"
    )


@pytest.mark.anyio
async def test_delete_image_offering_not_found(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await image_service.delete_image(
            offering_id=uuid.uuid4(),
            image_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
        )

    image_repository.get_by_id.assert_not_awaited()
    image_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_image_access_denied(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    offering = make_offering()

    offering_repository.get_by_id.return_value = (
        offering
    )

    with pytest.raises(
        OfferingImageAccessDeniedError
    ):
        await image_service.delete_image(
            offering_id=offering.id,
            image_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
        )

    image_repository.get_by_id.assert_not_awaited()
    image_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_image_not_found(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingImageNotFoundError
    ):
        await image_service.delete_image(
            offering_id=offering.id,
            image_id=uuid.uuid4(),
            master_id=master_id,
        )

    image_repository.delete_with_primary_fallback.assert_not_awaited()
    image_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_image_from_other_offering(
    image_service: OfferingImageService,
    image_repository: AsyncMock,
    offering_repository: AsyncMock,
    image_storage,
):
    master_id = uuid.uuid4()

    offering = make_offering(
        master_id=master_id
    )

    image = make_offering_image(
        offering_id=uuid.uuid4()
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    image_repository.get_by_id.return_value = (
        image
    )

    with pytest.raises(
        OfferingImageNotFoundError
    ):
        await image_service.delete_image(
            offering_id=offering.id,
            image_id=image.id,
            master_id=master_id,
        )

    image_repository.delete_with_primary_fallback.assert_not_awaited()
    image_storage.delete.assert_not_awaited()