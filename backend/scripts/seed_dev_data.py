"""Наполнить локальную БД начальными данными для разработки."""

import asyncio

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Category,
    City,
    District,
    Tag,
)
from src.database.session import AsyncSessionLocal

CATEGORIES = [
    {
        "name": "Стрижки",
        "slug": "haircuts",
        "children": [
            {
                "name": "Мужская стрижка",
                "slug": "mens-haircut",
            },
            {
                "name": "Женская стрижка",
                "slug": "womens-haircut",
            },
        ],
    },
    {
        "name": "Ногтевой сервис",
        "slug": "nails",
        "children": [
            {
                "name": "Маникюр",
                "slug": "manicure",
            },
            {
                "name": "Педикюр",
                "slug": "pedicure",
            },
        ],
    },
    {
        "name": "Массаж",
        "slug": "massage",
        "children": [
            {
                "name": "Спортивный массаж",
                "slug": "sports-massage",
            },
            {
                "name": "Расслабляющий массаж",
                "slug": "relaxing-massage",
            },
        ],
    },
]

TAGS = [
    {
        "name": "На дому",
        "slug": "at-home",
    },
    {
        "name": "С выездом",
        "slug": "mobile-service",
    },
    {
        "name": "Экспресс",
        "slug": "express",
    },
]

LOCATIONS = [
    {
        "city": "Омск",
        "districts": [
            "Центральный",
            "Советский",
            "Кировский",
        ],
    },
]


async def get_or_create_category(
    session: AsyncSession,
    name: str,
    slug: str,
    parent_id=None,
) -> Category:
    category = await session.scalar(
        select(Category).where(
            or_(
                Category.name == name,
                Category.slug == slug,
            )
        )
    )

    if category is not None:
        print(
            f"[skip] Категория: {name}"
        )
        return category

    category = Category(
        name=name,
        slug=slug,
        parent_id=parent_id,
    )

    session.add(
        category
    )

    await session.flush()

    print(
        f"[create] Категория: {name}"
    )

    return category


async def seed_categories(
    session: AsyncSession,
) -> None:
    for category_data in CATEGORIES:
        parent = await get_or_create_category(
            session=session,
            name=category_data["name"],
            slug=category_data["slug"],
        )

        for child_data in category_data["children"]:
            await get_or_create_category(
                session=session,
                name=child_data["name"],
                slug=child_data["slug"],
                parent_id=parent.id,
            )


async def seed_tags(
    session: AsyncSession,
) -> None:
    for tag_data in TAGS:
        tag = await session.scalar(
            select(Tag).where(
                or_(
                    Tag.name == tag_data["name"],
                    Tag.slug == tag_data["slug"],
                )
            )
        )

        if tag is not None:
            print(
                f"[skip] Тег: {tag_data['name']}"
            )
            continue

        session.add(
            Tag(
                name=tag_data["name"],
                slug=tag_data["slug"],
            )
        )

        print(
            f"[create] Тег: {tag_data['name']}"
        )


async def seed_locations(
    session: AsyncSession,
) -> None:
    for location_data in LOCATIONS:
        city = await session.scalar(
            select(City).where(
                City.name == location_data["city"]
            )
        )

        if city is None:
            city = City(
                name=location_data["city"]
            )

            session.add(
                city
            )

            await session.flush()

            print(
                f"[create] Город: {city.name}"
            )
        else:
            print(
                f"[skip] Город: {city.name}"
            )

        for district_name in location_data["districts"]:
            district = await session.scalar(
                select(District).where(
                    District.city_id == city.id,
                    District.name == district_name,
                )
            )

            if district is not None:
                print(
                    f"[skip] Район: {district_name}"
                )
                continue

            session.add(
                District(
                    city_id=city.id,
                    name=district_name,
                )
            )

            print(
                f"[create] Район: {district_name}"
            )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        try:
            await seed_categories(
                session
            )

            await seed_tags(
                session
            )

            await seed_locations(
                session
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    print()
    print(
        "Dev-данные успешно подготовлены."
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )