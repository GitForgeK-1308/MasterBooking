"""Показать пользователей приложения и их основные статусы."""

import argparse
import asyncio

from sqlalchemy import select

from src.database.models import User
from src.database.session import AsyncSessionLocal
from src.users.models import UserRole


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Показать пользователей приложения.")

    parser.add_argument(
        "--role",
        choices=[role.value for role in UserRole],
        default=None,
        help="Фильтр по роли.",
    )

    parser.add_argument(
        "--active",
        choices=[
            "true",
            "false",
        ],
        default=None,
        help="Фильтр по активности аккаунта.",
    )

    return parser.parse_args()


async def main(
    role: str | None,
    active: str | None,
) -> None:
    query = select(User)

    if role is not None:
        query = query.where(User.role == UserRole(role))

    if active is not None:
        is_active = active == "true"

        query = query.where(User.is_active == is_active)

    query = query.order_by(User.created_at.asc())

    async with AsyncSessionLocal() as session:
        users = (await session.scalars(query)).all()

    if not users:
        print("Пользователи не найдены.")
        return

    print(f"Найдено пользователей: {len(users)}")
    print()

    for user in users:
        print(
            f"{user.email} | "
            f"role={user.role.value} | "
            f"active={user.is_active} | "
            f"created_at={user.created_at}"
        )


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            role=args.role,
            active=args.active,
        )
    )
