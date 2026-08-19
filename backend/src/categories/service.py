import uuid

from src.categories.exceptions import (
    CategoryAlreadyExistsError,
    CategoryInvalidParentError,
    CategoryNotFoundError,
)
from src.categories.models import Category
from src.categories.repository import CategoryRepository
from src.categories.schemas import (
    CategoryCreate,
    CategoryTreeResponse,
    CategoryUpdate,
)


class CategoryService:
    def __init__(
        self,
        repository: CategoryRepository,
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

    async def get_categories(
        self,
    ) -> list[Category]:
        return await self.repository.get_active()

    async def get_all_categories(
        self,
    ) -> list[Category]:
        return await self.repository.get_all()

    async def get_category_by_id(
        self,
        category_id: uuid.UUID,
    ) -> Category:
        category = await self.repository.get_by_id(
            category_id
        )

        if category is None:
            raise CategoryNotFoundError

        return category

    async def create_category(
        self,
        data: CategoryCreate,
    ) -> Category:
        name = self._normalize_name(
            data.name
        )

        existing_by_name = await self.repository.get_by_name(
            name
        )

        if existing_by_name is not None:
            raise CategoryAlreadyExistsError

        slug = self._normalize_slug(
            data.slug
        )

        existing_by_slug = await self.repository.get_by_slug(
            slug
        )

        if existing_by_slug is not None:
            raise CategoryAlreadyExistsError

        if data.parent_id is not None:
            parent = await self.repository.get_by_id(
                data.parent_id
            )

            if parent is None:
                raise CategoryNotFoundError

        category = Category(
            name=name,
            slug=slug,
            parent_id=data.parent_id,
        )

        return await self.repository.create(
            category
        )

    async def update_category(
        self,
        category_id: uuid.UUID,
        data: CategoryUpdate,
    ) -> Category:
        category = await self.get_category_by_id(
            category_id
        )

        update_data = data.model_dump(
            exclude_unset=True
        )

        name = update_data.get(
            "name"
        )

        if name is not None:
            normalized_name = self._normalize_name(
                name
            )

            existing_by_name = await self.repository.get_by_name(
                normalized_name
            )

            if (
                existing_by_name is not None
                and existing_by_name.id != category.id
            ):
                raise CategoryAlreadyExistsError

            category.name = normalized_name

        slug = update_data.get(
            "slug"
        )

        if slug is not None:
            normalized_slug = self._normalize_slug(
                slug
            )

            existing_by_slug = await self.repository.get_by_slug(
                normalized_slug
            )

            if (
                existing_by_slug is not None
                and existing_by_slug.id != category.id
            ):
                raise CategoryAlreadyExistsError

            category.slug = normalized_slug

        if "parent_id" in update_data:
            parent_id = update_data[
                "parent_id"
            ]

            if parent_id == category.id:
                raise CategoryInvalidParentError

            if parent_id is not None:
                parent = await self.repository.get_by_id(
                    parent_id
                )

                if parent is None:
                    raise CategoryNotFoundError

                current_parent = parent

                while current_parent is not None:
                    if current_parent.id == category.id:
                        raise CategoryInvalidParentError

                    if current_parent.parent_id is None:
                        break

                    current_parent = await self.repository.get_by_id(
                        current_parent.parent_id
                    )

            category.parent_id = parent_id

        is_active = update_data.get(
            "is_active"
        )

        if is_active is not None:
            category.is_active = is_active

        return await self.repository.update(
            category
        )

    async def get_category_tree(
        self,
    ) -> list[CategoryTreeResponse]:
        categories = await self.repository.get_active()

        nodes = {
            category.id: CategoryTreeResponse(
                id=category.id,
                name=category.name,
                slug=category.slug,
                parent_id=category.parent_id,
                is_active=category.is_active,
                children=[],
            )
            for category in categories
        }

        roots: list[CategoryTreeResponse] = []

        for category in categories:
            node = nodes[
                category.id
            ]

            if (
                category.parent_id is not None
                and category.parent_id in nodes
            ):
                nodes[
                    category.parent_id
                ].children.append(
                    node
                )
            else:
                roots.append(
                    node
                )

        return roots