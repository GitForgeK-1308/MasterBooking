import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.offering_images.models import OfferingImage
from src.offering_images.repository import (
    OfferingImageRepository,
)
from src.offering_images.service import (
    MAX_IMAGE_SIZE,
)
from src.offering_images.storage import (
    LocalImageStorage,
)


@pytest.mark.anyio
async def test_upload_first_offering_image(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
    image_storage: LocalImageStorage,
    png_bytes: bytes,
    db_session: AsyncSession,
):
    response = await ac.post(
        f"/offerings/{offering.id}/images",
        headers=master_auth_headers,
        files={
            "file": (
                "image.png",
                png_bytes,
                "image/png",
            ),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["offering_id"]
        == str(offering.id)
    )
    assert data["is_primary"] is True
    assert data["sort_order"] == 0
    assert data["image_url"].startswith(
        "/uploads/offerings/"
    )

    image_id = uuid.UUID(
        data["id"]
    )

    repository = OfferingImageRepository(
        db_session
    )

    image = await repository.get_by_id(
        image_id
    )

    assert image is not None
    assert image.is_primary is True
    assert image.sort_order == 0

    storage_key = data[
        "image_url"
    ].removeprefix(
        "/uploads/"
    )

    file_path = (
        image_storage.uploads_dir
        / storage_key
    )

    assert file_path.exists()


@pytest.mark.anyio
async def test_upload_second_image_is_not_primary(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
    image_storage: LocalImageStorage,
    png_bytes: bytes,
):
    response = await ac.post(
        f"/offerings/{offering.id}/images",
        headers=master_auth_headers,
        files={
            "file": (
                "second.png",
                png_bytes,
                "image/png",
            ),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["is_primary"] is False
    assert data["sort_order"] == 1


@pytest.mark.anyio
async def test_upload_image_without_token(
    ac: AsyncClient,
    offering: MasterOffering,
    png_bytes: bytes,
):
    response = await ac.post(
        f"/offerings/{offering.id}/images",
        files={
            "file": (
                "image.png",
                png_bytes,
                "image/png",
            ),
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_upload_image_as_client_forbidden(
    ac: AsyncClient,
    offering: MasterOffering,
    auth_headers: dict[str, str],
    png_bytes: bytes,
):
    response = await ac.post(
        f"/offerings/{offering.id}/images",
        headers=auth_headers,
        files={
            "file": (
                "image.png",
                png_bytes,
                "image/png",
            ),
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_upload_image_offering_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    png_bytes: bytes,
):
    response = await ac.post(
        f"/offerings/{uuid.uuid4()}/images",
        headers=master_auth_headers,
        files={
            "file": (
                "image.png",
                png_bytes,
                "image/png",
            ),
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Услуга не найдена!"
    }


@pytest.mark.anyio
async def test_upload_image_to_foreign_offering_forbidden(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    master_auth_headers: dict[str, str],
    png_bytes: bytes,
):
    response = await ac.post(
        (
            f"/offerings/"
            f"{second_master_offering.id}/images"
        ),
        headers=master_auth_headers,
        files={
            "file": (
                "image.png",
                png_bytes,
                "image/png",
            ),
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Вы не можете загружать фотографии "
            "для чужой услуги!"
        )
    }


@pytest.mark.anyio
async def test_upload_invalid_image_type(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/offerings/{offering.id}/images",
        headers=master_auth_headers,
        files={
            "file": (
                "fake.png",
                b"this is not an image",
                "image/png",
            ),
        },
    )

    assert response.status_code == 415

    assert response.json() == {
        "detail": (
            "Разрешены только JPEG, PNG "
            "и WEBP изображения!"
        )
    }


@pytest.mark.anyio
async def test_upload_image_too_large(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/offerings/{offering.id}/images",
        headers=master_auth_headers,
        files={
            "file": (
                "large.png",
                b"x" * (
                    MAX_IMAGE_SIZE + 1
                ),
                "image/png",
            ),
        },
    )

    assert response.status_code == 413

    assert response.json() == {
        "detail": (
            "Размер фотографии не должен "
            "превышать 5 MB!"
        )
    }


@pytest.mark.anyio
async def test_get_offering_images_sorted(
    ac: AsyncClient,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
):
    response = await ac.get(
        f"/offerings/{offering.id}/images"
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["id"]
        for item in data
    ] == [
        str(offering_image.id),
        str(second_offering_image.id),
    ]

    assert (
        data[0]["is_primary"]
        is True
    )

    assert (
        data[1]["is_primary"]
        is False
    )

    assert (
        data[0]["image_url"]
        == (
            "/uploads/"
            f"{offering_image.storage_key}"
        )
    )


@pytest.mark.anyio
async def test_get_images_offering_not_found(
    ac: AsyncClient,
):
    response = await ac.get(
        (
            f"/offerings/"
            f"{uuid.uuid4()}/images"
        )
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Услуга не найдена!"
    }


@pytest.mark.anyio
async def test_set_primary_image(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        (
            f"/offerings/{offering.id}/images/"
            f"{second_offering_image.id}/primary"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["id"]
        == str(second_offering_image.id)
    )
    assert data["is_primary"] is True

    repository = OfferingImageRepository(
        db_session
    )

    primary = await repository.get_primary(
        offering.id
    )

    assert primary is not None
    assert (
        primary.id
        == second_offering_image.id
    )


@pytest.mark.anyio
async def test_set_primary_image_not_found(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            f"/offerings/{offering.id}/images/"
            f"{uuid.uuid4()}/primary"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Фотография не найдена!"
    }


@pytest.mark.anyio
async def test_set_primary_image_from_other_offering_returns_404(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    foreign_offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            f"/offerings/{offering.id}/images/"
            f"{foreign_offering_image.id}/primary"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Фотография не найдена!"
    }


@pytest.mark.anyio
async def test_set_primary_foreign_offering_forbidden(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    foreign_offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            f"/offerings/"
            f"{second_master_offering.id}/images/"
            f"{foreign_offering_image.id}/primary"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Вы не можете изменять фотографии "
            "чужой услуги!"
        )
    }


@pytest.mark.anyio
async def test_delete_image_removes_database_and_file(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    stored_offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
    image_storage: LocalImageStorage,
    db_session: AsyncSession,
):
    image_id = stored_offering_image.id

    file_path = (
        image_storage.uploads_dir
        / stored_offering_image.storage_key
    )

    assert file_path.exists()

    response = await ac.delete(
        (
            f"/offerings/{offering.id}/images/"
            f"{image_id}"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 204
    assert response.text == ""

    repository = OfferingImageRepository(
        db_session
    )

    image_from_database = (
        await repository.get_by_id(
            image_id
        )
    )

    assert image_from_database is None
    assert not file_path.exists()


@pytest.mark.anyio
async def test_delete_primary_image_promotes_next(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    offering_image: OfferingImage,
    second_offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.delete(
        (
            f"/offerings/{offering.id}/images/"
            f"{offering_image.id}"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 204

    repository = OfferingImageRepository(
        db_session
    )

    remaining_image = (
        await repository.get_by_id(
            second_offering_image.id
        )
    )

    assert remaining_image is not None
    assert remaining_image.is_primary is True


@pytest.mark.anyio
async def test_delete_image_not_found(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.delete(
        (
            f"/offerings/{offering.id}/images/"
            f"{uuid.uuid4()}"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Фотография не найдена!"
    }


@pytest.mark.anyio
async def test_delete_image_foreign_offering_forbidden(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    foreign_offering_image: OfferingImage,
    master_auth_headers: dict[str, str],
):
    response = await ac.delete(
        (
            f"/offerings/"
            f"{second_master_offering.id}/images/"
            f"{foreign_offering_image.id}"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Вы не можете удалять фотографии "
            "чужой услуги!"
        )
    }