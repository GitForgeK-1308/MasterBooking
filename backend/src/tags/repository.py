import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.tags.models import Tag, master_offering_tags


class TagRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_all(
        self,
    ) -> list[Tag]:
        result = await self.session.scalars(select(Tag).order_by(Tag.name.asc()))

        return list(result.all())

    async def get_active(
        self,
    ) -> list[Tag]:
        result = await self.session.scalars(
            select(Tag).where(Tag.is_active.is_(True)).order_by(Tag.name.asc())
        )

        return list(result.all())

    async def get_by_id(
        self,
        tag_id: uuid.UUID,
    ) -> Tag | None:
        return await self.session.scalar(select(Tag).where(Tag.id == tag_id))

    async def get_by_name(
        self,
        name: str,
    ) -> Tag | None:
        return await self.session.scalar(select(Tag).where(Tag.name == name))

    async def get_by_slug(
        self,
        slug: str,
    ) -> Tag | None:
        return await self.session.scalar(select(Tag).where(Tag.slug == slug))

    async def get_by_ids(
        self,
        tag_ids: list[uuid.UUID],
    ) -> list[Tag]:
        if not tag_ids:
            return []

        result = await self.session.scalars(select(Tag).where(Tag.id.in_(tag_ids)))

        return list(result.all())

    async def create(
        self,
        tag: Tag,
    ) -> Tag:
        self.session.add(tag)

        await self.session.commit()
        await self.session.refresh(tag)

        return tag

    async def update(
        self,
        tag: Tag,
    ) -> Tag:
        await self.session.commit()
        await self.session.refresh(tag)

        return tag

    async def is_used_by_offerings(
        self,
        tag_id: uuid.UUID,
    ) -> bool:
        offering_id = await self.session.scalar(
            select(master_offering_tags.c.offering_id)
            .where(master_offering_tags.c.tag_id == tag_id)
            .limit(1)
        )

        return offering_id is not None

    async def delete(
        self,
        tag: Tag,
    ) -> None:
        await self.session.delete(tag)
        await self.session.commit()
