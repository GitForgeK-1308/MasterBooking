import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category


class CategoryRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_all(
        self,
    ) -> list[Category]:
        result = await self.session.scalars(
            select(Category).order_by(
                Category.name.asc()
            )
        )

        return list(result.all())

    async def get_active(
        self,
    ) -> list[Category]:
        result = await self.session.scalars(
            select(Category)
            .where(
                Category.is_active.is_(True)
            )
            .order_by(
                Category.name.asc()
            )
        )

        return list(result.all())

    async def get_by_id(
        self,
        category_id: uuid.UUID,
    ) -> Category | None:
        return await self.session.scalar(
            select(Category).where(
                Category.id == category_id
            )
        )

    async def get_by_slug(
        self,
        slug: str,
    ) -> Category | None:
        return await self.session.scalar(
            select(Category).where(
                Category.slug == slug
            )
        )

    async def get_by_name(
        self,
        name: str,
    ) -> Category | None:
        return await self.session.scalar(
            select(Category).where(
                Category.name == name
            )
        )

    async def create(
        self,
        category: Category,
    ) -> Category:
        self.session.add(category)

        await self.session.commit()
        await self.session.refresh(category)

        return category

    async def update(
        self,
        category: Category,
    ) -> Category:
        await self.session.commit()
        await self.session.refresh(category)

        return category