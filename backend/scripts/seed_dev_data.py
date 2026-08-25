"""Наполнить локальную БД demo-данными для разработки."""

import asyncio
from datetime import time
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password import hash_password
from src.categories.models import Category
from src.database.session import AsyncSessionLocal
from src.locations.models import City, District
from src.master_offering.models import MasterOffering
from src.master_schedule.models import MasterSchedule, WeekDay
from src.masters.models import Master
from src.tags.models import Tag
from src.users.models import User, UserRole

DEMO_PASSWORD = "Demo12345!"

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
        print(f"[skip] Категория: {name}")
        return category

    category = Category(
        name=name,
        slug=slug,
        parent_id=parent_id,
    )

    session.add(category)
    await session.flush()

    print(f"[create] Категория: {name}")

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
            print(f"[skip] Тег: {tag_data['name']}")
            continue

        session.add(
            Tag(
                name=tag_data["name"],
                slug=tag_data["slug"],
            )
        )

        print(f"[create] Тег: {tag_data['name']}")


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

            session.add(city)
            await session.flush()

            print(f"[create] Город: {city.name}")

        else:
            print(f"[skip] Город: {city.name}")

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


async def get_or_create_user(
    session: AsyncSession,
    *,
    email: str,
    first_name: str,
    last_name: str,
    phone: str,
    role: UserRole,
) -> User:
    user = await session.scalar(
        select(User).where(
            User.email == email
        )
    )

    if user is not None:
        print(f"[skip] Пользователь: {email}")
        return user

    user = User(
        email=email,
        hashed_password=hash_password(
            DEMO_PASSWORD
        ),
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        is_active=True,
    )

    session.add(user)
    await session.flush()

    print(f"[create] Пользователь: {email}")

    return user


async def seed_users(
    session: AsyncSession,
) -> dict[str, User]:
    client = await get_or_create_user(
        session,
        email="demo.client@example.com",
        first_name="Алексей",
        last_name="Смирнов",
        phone="+79990000001",
        role=UserRole.CLIENT,
    )

    admin = await get_or_create_user(
        session,
        email="demo.admin@example.com",
        first_name="Администратор",
        last_name="MasterBooking",
        phone="+79990000002",
        role=UserRole.ADMIN,
    )

    barber = await get_or_create_user(
        session,
        email="demo.barber@example.com",
        first_name="Анна",
        last_name="Волкова",
        phone="+79990000003",
        role=UserRole.MASTER,
    )

    massage = await get_or_create_user(
        session,
        email="demo.massage@example.com",
        first_name="Максим",
        last_name="Орлов",
        phone="+79990000004",
        role=UserRole.MASTER,
    )

    return {
        "client": client,
        "admin": admin,
        "barber": barber,
        "massage": massage,
    }


async def get_location(
    session: AsyncSession,
    *,
    city_name: str,
    district_name: str,
) -> tuple[City, District]:
    city = await session.scalar(
        select(City).where(
            City.name == city_name
        )
    )

    if city is None:
        raise RuntimeError(
            f"Город {city_name} не найден"
        )

    district = await session.scalar(
        select(District).where(
            District.city_id == city.id,
            District.name == district_name,
        )
    )

    if district is None:
        raise RuntimeError(
            f"Район {district_name} не найден"
        )

    return city, district


async def get_or_create_master(
    session: AsyncSession,
    *,
    user: User,
    description: str,
    experience: int,
    education: str,
    district_name: str,
    address: str,
) -> Master:
    master = await session.scalar(
        select(Master).where(
            Master.user_id == user.id
        )
    )

    if master is not None:
        print(
            f"[skip] Мастер: "
            f"{user.first_name} {user.last_name}"
        )
        return master

    city, district = await get_location(
        session,
        city_name="Омск",
        district_name=district_name,
    )

    master = Master(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        description=description,
        experience=experience,
        education=education,
        city=city.name,
        district=district.name,
        address=address,
        city_id=city.id,
        district_id=district.id,
        is_active=True,
    )

    session.add(master)
    await session.flush()

    print(
        f"[create] Мастер: "
        f"{user.first_name} {user.last_name}"
    )

    return master


async def seed_masters(
    session: AsyncSession,
    users: dict[str, User],
) -> dict[str, Master]:
    barber = await get_or_create_master(
        session,
        user=users["barber"],
        description=(
            "Парикмахер-стилист. "
            "Специализируется на современных "
            "мужских и женских стрижках."
        ),
        experience=6,
        education=(
            "Профессиональная подготовка "
            "по парикмахерскому искусству."
        ),
        district_name="Центральный",
        address="ул. Ленина, 10",
    )

    massage = await get_or_create_master(
        session,
        user=users["massage"],
        description=(
            "Массажист с опытом работы "
            "со спортивными и "
            "восстановительными программами."
        ),
        experience=5,
        education=(
            "Профессиональная подготовка "
            "по классическому и "
            "спортивному массажу."
        ),
        district_name="Советский",
        address="пр. Мира, 25",
    )

    return {
        "barber": barber,
        "massage": massage,
    }


async def get_category(
    session: AsyncSession,
    slug: str,
) -> Category:
    category = await session.scalar(
        select(Category).where(
            Category.slug == slug
        )
    )

    if category is None:
        raise RuntimeError(
            f"Категория {slug} не найдена"
        )

    return category


async def get_tags(
    session: AsyncSession,
    slugs: list[str],
) -> list[Tag]:
    result = await session.scalars(
        select(Tag).where(
            Tag.slug.in_(slugs)
        )
    )

    return list(result.all())


async def get_or_create_offering(
    session: AsyncSession,
    *,
    master: Master,
    category_slug: str,
    title: str,
    description: str,
    price: str,
    discount_percent: int,
    duration_minutes: int,
    tag_slugs: list[str],
) -> MasterOffering:
    offering = await session.scalar(
        select(MasterOffering).where(
            MasterOffering.master_id == master.id,
            MasterOffering.title == title,
        )
    )

    if offering is not None:
        print(f"[skip] Услуга: {title}")
        return offering

    category = await get_category(
        session,
        category_slug,
    )

    tags = await get_tags(
        session,
        tag_slugs,
    )

    offering = MasterOffering(
        master_id=master.id,
        category_id=category.id,
        title=title,
        description=description,
        price=Decimal(price),
        discount_percent=discount_percent,
        duration_minutes=duration_minutes,
        is_active=True,
        tags=tags,
    )

    session.add(offering)
    await session.flush()

    print(f"[create] Услуга: {title}")

    return offering


async def seed_offerings(
    session: AsyncSession,
    masters: dict[str, Master],
) -> None:
    await get_or_create_offering(
        session,
        master=masters["barber"],
        category_slug="mens-haircut",
        title="Мужская стрижка",
        description=(
            "Подбор формы, стрижка и укладка."
        ),
        price="1500.00",
        discount_percent=10,
        duration_minutes=60,
        tag_slugs=["express"],
    )

    await get_or_create_offering(
        session,
        master=masters["barber"],
        category_slug="womens-haircut",
        title="Женская стрижка",
        description=(
            "Консультация, стрижка и "
            "финальная укладка."
        ),
        price="2200.00",
        discount_percent=0,
        duration_minutes=90,
        tag_slugs=[],
    )

    await get_or_create_offering(
        session,
        master=masters["massage"],
        category_slug="sports-massage",
        title="Спортивный массаж",
        description=(
            "Массаж для восстановления "
            "после физических нагрузок."
        ),
        price="2500.00",
        discount_percent=15,
        duration_minutes=60,
        tag_slugs=["at-home"],
    )

    await get_or_create_offering(
        session,
        master=masters["massage"],
        category_slug="relaxing-massage",
        title="Расслабляющий массаж",
        description=(
            "Мягкая техника для снятия "
            "напряжения и восстановления."
        ),
        price="2200.00",
        discount_percent=0,
        duration_minutes=60,
        tag_slugs=["mobile-service"],
    )


async def seed_schedules(
    session: AsyncSession,
    masters: dict[str, Master],
) -> None:
    working_days = [
        WeekDay.MONDAY,
        WeekDay.TUESDAY,
        WeekDay.WEDNESDAY,
        WeekDay.THURSDAY,
        WeekDay.FRIDAY,
    ]

    for master in masters.values():
        for day in working_days:
            schedule = await session.scalar(
                select(MasterSchedule).where(
                    MasterSchedule.master_id
                    == master.id,
                    MasterSchedule.day_of_week
                    == day,
                )
            )

            if schedule is not None:
                print(
                    f"[skip] Расписание: "
                    f"{master.first_name} "
                    f"{day.value}"
                )
                continue

            session.add(
                MasterSchedule(
                    master_id=master.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                    is_working=True,
                )
            )

            print(
                f"[create] Расписание: "
                f"{master.first_name} "
                f"{day.value}"
            )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        try:
            await seed_categories(session)
            await seed_tags(session)
            await seed_locations(session)

            users = await seed_users(session)

            masters = await seed_masters(
                session,
                users,
            )

            await seed_offerings(
                session,
                masters,
            )

            await seed_schedules(
                session,
                masters,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    print()
    print("Demo-данные успешно подготовлены.")
    print()
    print("Demo-аккаунты:")
    print(
        "Клиент: "
        "demo.client@example.com"
    )
    print(
        "Мастер: "
        "demo.barber@example.com"
    )
    print(
        "Мастер: "
        "demo.massage@example.com"
    )
    print(
        "Админ: "
        "demo.admin@example.com"
    )
    print(
        f"Пароль для всех: {DEMO_PASSWORD}"
    )


if __name__ == "__main__":
    asyncio.run(main())