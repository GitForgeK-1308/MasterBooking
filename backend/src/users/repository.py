import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User


class UserRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        return await self.session.scalar(
            select(User).where(
                User.id == user_id
            )
        )

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        return await self.session.scalar(
            select(User).where(
                User.email == email
            )
        )

    async def create(
        self,
        user: User,
    ) -> User:
        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def update(
        self,
        user: User,
    ) -> User:
        await self.session.commit()
        await self.session.refresh(user)

        return user