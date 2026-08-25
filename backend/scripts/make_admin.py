"""Назначить существующему пользователю роль администратора."""

import argparse
import asyncio

from sqlalchemy import select

from src.database.models import User
from src.database.session import AsyncSessionLocal
from src.users.models import UserRole


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Назначить существующему пользователю роль администратора."
    )
    parser.add_argument(
        "email",
        help="Email пользователя",
    )
    return parser.parse_args()


async def main(email: str) -> None:
    normalized_email = email.strip().lower()

    async with AsyncSessionLocal() as session:
        user = await session.scalar(
            select(User).where(
                User.email == normalized_email
            )
        )

        if user is None:
            print(
                f"Пользователь {normalized_email} не найден"
            )
            return

        user.role = UserRole.ADMIN

        await session.commit()

        print(
            f"Пользователь {user.email} теперь администратор"
        )


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args.email))