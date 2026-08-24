from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from src.users.avatar_storage import LocalAvatarStorage
from src.users.exceptions import (
    AvatarTooLargeError,
    InvalidAvatarTypeError,
)
from src.users.models import User
from src.users.repository import UserRepository

MAX_AVATAR_SIZE = 5 * 1024 * 1024

ALLOWED_AVATAR_FORMATS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}


class UserAvatarService:
    def __init__(
        self,
        repository: UserRepository,
        storage: LocalAvatarStorage,
    ) -> None:
        self.repository = repository
        self.storage = storage

    async def upload_avatar(
        self,
        user: User,
        file: UploadFile,
    ) -> User:
        content = await file.read(
            MAX_AVATAR_SIZE + 1
        )

        if len(content) > MAX_AVATAR_SIZE:
            raise AvatarTooLargeError

        try:
            image = Image.open(
                BytesIO(content)
            )

            image_format = image.format

            image.verify()

        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
        ):
            raise InvalidAvatarTypeError

        if image_format not in ALLOWED_AVATAR_FORMATS:
            raise InvalidAvatarTypeError

        extension = ALLOWED_AVATAR_FORMATS[
            image_format
        ]

        old_avatar = user.avatar_storage_key

        new_storage_key = await self.storage.save(
            content=content,
            extension=extension,
        )

        try:
            user.avatar_storage_key = new_storage_key

            updated_user = await self.repository.update(
                user
            )

        except Exception:
            user.avatar_storage_key = old_avatar

            await self.storage.delete(
                new_storage_key
            )

            raise

        if old_avatar is not None:
            await self.storage.delete(
                old_avatar
            )

        return updated_user

    async def delete_avatar(
        self,
        user: User,
    ) -> None:
        old_avatar = user.avatar_storage_key

        if old_avatar is None:
            return

        user.avatar_storage_key = None

        try:
            await self.repository.update(
                user
            )
        except Exception:
            user.avatar_storage_key = old_avatar
            raise

        await self.storage.delete(
            old_avatar
        )

    def get_avatar_url(
        self,
        storage_key: str,
    ) -> str:
        return self.storage.get_url(
            storage_key
        )