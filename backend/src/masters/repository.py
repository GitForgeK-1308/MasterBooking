import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.masters.models import Master


class MasterRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_all(
        self,
    ) -> list[Master]:
        result = await self.session.scalars(
            select(Master).options(
                selectinload(Master.user)
            )
        )

        return list(result.all())

    async def get_by_id(
        self,
        master_id: uuid.UUID,
    ) -> Master | None:
        return await self.session.scalar(
            select(Master)
            .options(
                selectinload(Master.user)
            )
            .where(
                Master.id == master_id
            )
        )

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> Master | None:
        return await self.session.scalar(
            select(Master).where(
                Master.user_id == user_id
            )
        )

    async def create(
        self,
        master: Master,
    ) -> Master:
        self.session.add(master)

        await self.session.commit()
        await self.session.refresh(master)

        return master

    async def update(
        self,
        master: Master,
    ) -> Master:
        await self.session.commit()
        await self.session.refresh(master)

        return master

    async def delete(
        self,
        master: Master,
    ) -> None:
        await self.session.delete(master)
        await self.session.commit()