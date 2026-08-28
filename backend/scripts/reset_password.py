"""Принудительно изменить пароль существующего пользователя."""

import argparse
import asyncio
from getpass import getpass

from sqlalchemy import select

from src.auth.password import hash_password
from src.database.models import User
from src.database.session import AsyncSessionLocal

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Изменить пароль существующего пользователя.")
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

    new_password = getpass("Новый пароль: ")

    password_confirmation = getpass("Повторите пароль: ")

    if new_password != password_confirmation:
        print("Пароли не совпадают.")
        return

    if not (MIN_PASSWORD_LENGTH <= len(new_password) <= MAX_PASSWORD_LENGTH):
        print(
            "Пароль должен содержать "
            f"от {MIN_PASSWORD_LENGTH} "
            f"до {MAX_PASSWORD_LENGTH} символов."
        )
        return

    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == normalized_email))

        if user is None:
            print(f"Пользователь {normalized_email} не найден.")
            return

        user.hashed_password = hash_password(new_password)

        await session.commit()

        print(f"Пароль пользователя {user.email} изменён.")


if __name__ == "__main__":
    args = parse_args()

    asyncio.run(
        main(
            email=args.email,
        )
    )
