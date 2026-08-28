from collections.abc import AsyncGenerator
from io import BytesIO
from pathlib import Path

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.users.avatar_service import (
    MAX_AVATAR_SIZE,
    UserAvatarService,
)
from src.users.avatar_storage import LocalAvatarStorage
from src.users.dependencies import get_user_avatar_service
from src.users.models import User
from src.users.repository import UserRepository


def make_image_bytes(
    image_format: str,
) -> bytes:
    buffer = BytesIO()

    image = Image.new(
        "RGB",
        (10, 10),
    )

    image.save(
        buffer,
        format=image_format,
    )

    return buffer.getvalue()


@pytest.fixture
def avatar_storage(
    tmp_path: Path,
) -> LocalAvatarStorage:
    storage = LocalAvatarStorage()

    storage.uploads_dir = tmp_path / "uploads"

    storage.avatars_dir = storage.uploads_dir / "avatars"

    storage.avatars_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return storage


@pytest.fixture
async def avatar_ac(
    ac: AsyncClient,
    db_session: AsyncSession,
    avatar_storage: LocalAvatarStorage,
) -> AsyncGenerator[AsyncClient, None]:
    service = UserAvatarService(
        repository=UserRepository(db_session),
        storage=avatar_storage,
    )

    def override_get_user_avatar_service():
        return service

    app.dependency_overrides[get_user_avatar_service] = override_get_user_avatar_service

    try:
        yield ac
    finally:
        app.dependency_overrides.pop(
            get_user_avatar_service,
            None,
        )


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "image_format",
        "extension",
        "content_type",
    ),
    [
        (
            "JPEG",
            "jpg",
            "image/jpeg",
        ),
        (
            "PNG",
            "png",
            "image/png",
        ),
        (
            "WEBP",
            "webp",
            "image/webp",
        ),
    ],
)
async def test_upload_avatar_allowed_formats(
    avatar_ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    avatar_storage: LocalAvatarStorage,
    image_format: str,
    extension: str,
    content_type: str,
):
    content = make_image_bytes(image_format)

    response = await avatar_ac.post(
        "/users/me/avatar",
        headers=auth_headers,
        files={
            "file": (
                f"avatar.{extension}",
                content,
                content_type,
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["avatar_url"].startswith("/uploads/avatars/")

    assert data["avatar_url"].endswith(f".{extension}")

    repository = UserRepository(db_session)

    user_from_database = await repository.get_by_id(user.id)

    assert user_from_database is not None
    assert user_from_database.avatar_storage_key is not None

    avatar_path = avatar_storage.uploads_dir / user_from_database.avatar_storage_key

    assert avatar_path.exists()
    assert avatar_path.read_bytes() == content


@pytest.mark.anyio
async def test_upload_avatar_without_token(
    ac: AsyncClient,
):
    content = make_image_bytes("PNG")

    response = await ac.post(
        "/users/me/avatar",
        files={
            "file": (
                "avatar.png",
                content,
                "image/png",
            ),
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_upload_avatar_invalid_file(
    avatar_ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await avatar_ac.post(
        "/users/me/avatar",
        headers=auth_headers,
        files={
            "file": (
                "avatar.png",
                b"not-an-image",
                "image/png",
            ),
        },
    )

    assert response.status_code == 415
    assert response.json() == {"detail": ("Разрешены только JPEG, PNG и WEBP.")}


@pytest.mark.anyio
async def test_upload_avatar_unsupported_format(
    avatar_ac: AsyncClient,
    auth_headers: dict[str, str],
):
    content = make_image_bytes("GIF")

    response = await avatar_ac.post(
        "/users/me/avatar",
        headers=auth_headers,
        files={
            "file": (
                "avatar.gif",
                content,
                "image/gif",
            ),
        },
    )

    assert response.status_code == 415
    assert response.json() == {"detail": ("Разрешены только JPEG, PNG и WEBP.")}


@pytest.mark.anyio
async def test_upload_avatar_too_large(
    avatar_ac: AsyncClient,
    auth_headers: dict[str, str],
):
    content = b"x" * (MAX_AVATAR_SIZE + 1)

    response = await avatar_ac.post(
        "/users/me/avatar",
        headers=auth_headers,
        files={
            "file": (
                "avatar.png",
                content,
                "image/png",
            ),
        },
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": ("Файл слишком большой. Максимальный размер — 5 МБ.")
    }


@pytest.mark.anyio
async def test_upload_avatar_replaces_old_avatar(
    avatar_ac: AsyncClient,
    user: User,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
    avatar_storage: LocalAvatarStorage,
):
    first_content = make_image_bytes("PNG")

    first_response = await avatar_ac.post(
        "/users/me/avatar",
        headers=auth_headers,
        files={
            "file": (
                "first.png",
                first_content,
                "image/png",
            ),
        },
    )

    assert first_response.status_code == 200

    repository = UserRepository(db_session)

    user_after_first_upload = await repository.get_by_id(user.id)

    assert user_after_first_upload is not None
    assert user_after_first_upload.avatar_storage_key is not None

    old_storage_key = user_after_first_upload.avatar_storage_key

    old_avatar_path = avatar_storage.uploads_dir / old_storage_key

    assert old_avatar_path.exists()

    second_content = make_image_bytes("JPEG")

    second_response = await avatar_ac.post(
        "/users/me/avatar",
        headers=auth_headers,
        files={
            "file": (
                "second.jpg",
                second_content,
                "image/jpeg",
            ),
        },
    )

    assert second_response.status_code == 200

    user_after_second_upload = await repository.get_by_id(user.id)

    assert user_after_second_upload is not None
    assert user_after_second_upload.avatar_storage_key is not None

    new_storage_key = user_after_second_upload.avatar_storage_key

    assert new_storage_key != old_storage_key
    assert not old_avatar_path.exists()

    new_avatar_path = avatar_storage.uploads_dir / new_storage_key

    assert new_avatar_path.exists()
    assert new_avatar_path.read_bytes() == second_content
