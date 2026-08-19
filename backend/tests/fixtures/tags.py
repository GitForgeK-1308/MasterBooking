import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.tags.models import Tag


@pytest.fixture
async def tag(
    db_session: AsyncSession,
) -> Tag:
    tag = Tag(
        name="Hair",
        slug="hair",
    )

    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    return tag


@pytest.fixture
async def second_tag(
    db_session: AsyncSession,
) -> Tag:
    tag = Tag(
        name="Nails",
        slug="nails",
    )

    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    return tag


@pytest.fixture
async def inactive_tag(
    db_session: AsyncSession,
) -> Tag:
    tag = Tag(
        name="Massage",
        slug="massage",
        is_active=False,
    )

    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    return tag