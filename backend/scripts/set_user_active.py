"""Активировать или деактивировать аккаунт пользователя."""

import argparse
import asyncio

from sqlalchemy import select

from src.database.models import User
from src.database.session import AsyncSessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Активировать или деактивировать аккаунт пользователя.")
    )

    parser.add_argument(
        "email",
        help="Email пользователя",
    )

    parser.add_argument(
        "action",
        choices=[
            "activate",
            "deactivate",
        ],
        help=("activate — включить аккаунт, deactivate — отключить."),
    )

    return parser.parse_args()


async def main(
    email: str,
    action: str,
) -> None:
    normalized_email = email.strip().lower()

    target_state = action == "activate"

    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == normalized_email))

        if user is None:
            print(f"Пользователь {normalized_email} не найден.")
            return

        if user.is_active == target_state:
            state = "активен" if target_state else "деактивирован"

            print(f"Пользователь {user.email} уже {state}.")
            return

        user.is_active = target_state

        await session.commit()

        state = "активирован" if target_state else "деактивирован"

        print(f"Пользователь {user.email} {state}.")


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            email=args.email,
            action=args.action,
        )
    )
