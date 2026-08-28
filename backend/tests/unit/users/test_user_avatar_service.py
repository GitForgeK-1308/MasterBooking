from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from PIL import Image

from src.users.avatar_service import (
    MAX_AVATAR_SIZE,
    UserAvatarService,
)
from src.users.avatar_storage import LocalAvatarStorage
from src.users.exceptions import (
    AvatarTooLargeError,
    InvalidAvatarTypeError,
)
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


def make_user(
    *,
    avatar_storage_key: str | None = None,
) -> User:
    return User(
        email="user@example.com",
        hashed_password="hashed-password",
        first_name="Ivan",
        last_name="Ivanov",
        avatar_storage_key=avatar_storage_key,
    )


@pytest.fixture
def user_repository() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def avatar_storage() -> MagicMock:
    return MagicMock(spec=LocalAvatarStorage)


@pytest.fixture
def avatar_service(
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
) -> UserAvatarService:
    return UserAvatarService(
        repository=user_repository,
        storage=avatar_storage,
    )


@pytest.mark.anyio
async def test_upload_avatar(
    avatar_service: UserAvatarService,
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
):
    user = make_user()

    content = make_image_bytes("PNG")

    file = AsyncMock()
    file.read.return_value = content

    avatar_storage.save.return_value = "avatars/new-avatar.png"

    user_repository.update.return_value = user

    result = await avatar_service.upload_avatar(
        user=user,
        file=file,
    )

    assert result is user
    assert user.avatar_storage_key == "avatars/new-avatar.png"

    file.read.assert_awaited_once_with(MAX_AVATAR_SIZE + 1)

    avatar_storage.save.assert_awaited_once_with(
        content=content,
        extension="png",
    )

    user_repository.update.assert_awaited_once_with(user)

    avatar_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_avatar_replaces_old_avatar(
    avatar_service: UserAvatarService,
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
):
    user = make_user(avatar_storage_key="avatars/old.png")

    content = make_image_bytes("JPEG")

    file = AsyncMock()
    file.read.return_value = content

    avatar_storage.save.return_value = "avatars/new.jpg"

    user_repository.update.return_value = user

    result = await avatar_service.upload_avatar(
        user=user,
        file=file,
    )

    assert result is user
    assert user.avatar_storage_key == "avatars/new.jpg"

    avatar_storage.save.assert_awaited_once_with(
        content=content,
        extension="jpg",
    )

    user_repository.update.assert_awaited_once_with(user)

    avatar_storage.delete.assert_awaited_once_with("avatars/old.png")


@pytest.mark.anyio
async def test_upload_avatar_invalid_file(
    avatar_service: UserAvatarService,
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
):
    file = AsyncMock()
    file.read.return_value = b"not-an-image"

    with pytest.raises(InvalidAvatarTypeError):
        await avatar_service.upload_avatar(
            user=make_user(),
            file=file,
        )

    avatar_storage.save.assert_not_awaited()
    user_repository.update.assert_not_awaited()
    avatar_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_avatar_unsupported_format(
    avatar_service: UserAvatarService,
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
):
    content = make_image_bytes("GIF")

    file = AsyncMock()
    file.read.return_value = content

    with pytest.raises(InvalidAvatarTypeError):
        await avatar_service.upload_avatar(
            user=make_user(),
            file=file,
        )

    avatar_storage.save.assert_not_awaited()
    user_repository.update.assert_not_awaited()
    avatar_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_avatar_too_large(
    avatar_service: UserAvatarService,
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
):
    file = AsyncMock()
    file.read.return_value = b"x" * (MAX_AVATAR_SIZE + 1)

    with pytest.raises(AvatarTooLargeError):
        await avatar_service.upload_avatar(
            user=make_user(),
            file=file,
        )

    file.read.assert_awaited_once_with(MAX_AVATAR_SIZE + 1)

    avatar_storage.save.assert_not_awaited()
    user_repository.update.assert_not_awaited()
    avatar_storage.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_upload_avatar_cleans_new_file_when_update_fails(
    avatar_service: UserAvatarService,
    user_repository: AsyncMock,
    avatar_storage: MagicMock,
):
    old_storage_key = "avatars/old.png"
    new_storage_key = "avatars/new.png"

    user = make_user(avatar_storage_key=old_storage_key)

    content = make_image_bytes("PNG")

    file = AsyncMock()
    file.read.return_value = content

    avatar_storage.save.return_value = new_storage_key

    user_repository.update.side_effect = RuntimeError("database error")

    with pytest.raises(
        RuntimeError,
        match="database error",
    ):
        await avatar_service.upload_avatar(
            user=user,
            file=file,
        )

    avatar_storage.delete.assert_awaited_once_with(new_storage_key)

    assert user.avatar_storage_key == old_storage_key


def test_get_avatar_url(
    avatar_service: UserAvatarService,
    avatar_storage: MagicMock,
):
    storage_key = "avatars/avatar.png"

    avatar_storage.get_url.return_value = "/uploads/avatars/avatar.png"

    result = avatar_service.get_avatar_url(storage_key)

    assert result == "/uploads/avatars/avatar.png"

    avatar_storage.get_url.assert_called_once_with(storage_key)
