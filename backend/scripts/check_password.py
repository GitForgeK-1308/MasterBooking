"""Проверить пароль существующего пользователя."""

import argparse
import asyncio
from getpass import getpass

from sqlalchemy import select

from src.auth.password import verify_password
from src.database.models import User
from src.database.session import AsyncSessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Проверить пароль существующего пользователя."
        )
    )

    parser.add_argument(
        "email",
        help="Email пользователя",
    )

    return parser.parse_args()


async def main(
    email: str,
) -> None:
    normalized_email = email.strip().lower()

    password = getpass(
        "Пароль: "
    )

    async with AsyncSessionLocal() as session:
        user = await session.scalar(
            select(User).where(
                User.email == normalized_email
            )
        )

        if user is None:
            print(
                f"Пользователь {normalized_email} не найден."
            )
            return

        password_is_valid = verify_password(
            plain_password=password,
            hashed_password=user.hashed_password,
        )

        print(
            f"Email: {user.email}"
        )
        print(
            f"Роль: {user.role.value}"
        )
        print(
            f"Активен: {user.is_active}"
        )
        print(
            "Пароль совпадает: "
            f"{'Да' if password_is_valid else 'Нет'}"
        )


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            email=args.email,
        )
    )