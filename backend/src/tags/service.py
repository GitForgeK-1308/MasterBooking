import uuid

from src.tags.exceptions import (
    TagAlreadyExistsError,
    TagNotFoundError,
)
from src.tags.models import Tag
from src.tags.repository import TagRepository
from src.tags.schemas import (
    TagCreate,
    TagUpdate,
)


class TagService:
    def __init__(
        self,
        repository: TagRepository,
    ) -> None:
        self.repository = repository

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        return " ".join(
            name.strip().split()
        )

    @staticmethod
    def _normalize_slug(
        slug: str,
    ) -> str:
        return slug.strip().lower()

    async def get_tags(
        self,
    ) -> list[Tag]:
        return await self.repository.get_active()

    async def get_all_tags(
        self,
    ) -> list[Tag]:
        return await self.repository.get_all()

    async def create_tag(
        self,
        data: TagCreate,
    ) -> Tag:
        name = self._normalize_name(
            data.name
        )

        existing_by_name = await self.repository.get_by_name(
            name
        )

        if existing_by_name is not None:
            raise TagAlreadyExistsError

        slug = self._normalize_slug(
            data.slug
        )

        existing_by_slug = await self.repository.get_by_slug(
            slug
        )

        if existing_by_slug is not None:
            raise TagAlreadyExistsError

        tag = Tag(
            name=name,
            slug=slug,
        )

        return await self.repository.create(
            tag
        )

    async def update_tag(
        self,
        tag_id: uuid.UUID,
        data: TagUpdate,
    ) -> Tag:
        tag = await self.repository.get_by_id(
            tag_id
        )

        if tag is None:
            raise TagNotFoundError

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "name" in update_data:
            name = self._normalize_name(
                update_data["name"]
            )

            existing_by_name = await self.repository.get_by_name(
                name
            )

            if (
                existing_by_name is not None
                and existing_by_name.id != tag.id
            ):
                raise TagAlreadyExistsError

            tag.name = name

        if "slug" in update_data:
            slug = self._normalize_slug(
                update_data["slug"]
            )

            existing_by_slug = await self.repository.get_by_slug(
                slug
            )

            if (
                existing_by_slug is not None
                and existing_by_slug.id != tag.id
            ):
                raise TagAlreadyExistsError

            tag.slug = slug

        if "is_active" in update_data:
            tag.is_active = update_data[
                "is_active"
            ]

        return await self.repository.update(
            tag
        )