import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category


@pytest.fixture
async def category(
    db_session: AsyncSession,
) -> Category:
    category = Category(
        name="Beauty",
        slug="beauty",
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category


@pytest.fixture
async def second_category(
    db_session: AsyncSession,
) -> Category:
    category = Category(
        name="Nails",
        slug="nails",
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category


@pytest.fixture
async def inactive_category(
    db_session: AsyncSession,
) -> Category:
    category = Category(
        name="Massage",
        slug="massage",
        is_active=False,
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category


@pytest.fixture
async def child_category(
    db_session: AsyncSession,
    category: Category,
) -> Category:
    child = Category(
        name="Hair",
        slug="hair",
        parent_id=category.id,
    )

    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    return child


@pytest.fixture
async def grandchild_category(
    db_session: AsyncSession,
    child_category: Category,
) -> Category:
    child = Category(
        name="Coloring",
        slug="coloring",
        parent_id=child_category.id,
    )

    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)

    return child