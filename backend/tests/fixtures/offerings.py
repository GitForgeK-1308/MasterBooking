from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.token import create_access_token
from src.categories.models import Category
from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.tags.models import Tag


@pytest.fixture
def second_master_auth_headers(
    second_master: Master,
) -> dict[str, str]:
    assert second_master.user_id is not None

    token = create_access_token(
        user_id=second_master.user_id
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
async def offering(
    db_session: AsyncSession,
    master: Master,
    category: Category,
    tag: Tag,
) -> MasterOffering:
    offering = MasterOffering(
        master_id=master.id,
        category_id=category.id,
        title="Classic Cut",
        description="Professional service.",
        price=Decimal("25.00"),
        duration_minutes=60,
        is_active=True,
    )

    offering.tags = [
        tag,
    ]

    db_session.add(offering)
    await db_session.commit()
    await db_session.refresh(offering)

    return offering


@pytest.fixture
async def inactive_offering(
    db_session: AsyncSession,
    master: Master,
    category: Category,
) -> MasterOffering:
    offering = MasterOffering(
        master_id=master.id,
        category_id=category.id,
        title="Inactive Service",
        description="Inactive service.",
        price=Decimal("30.00"),
        duration_minutes=45,
        is_active=False,
    )

    db_session.add(offering)
    await db_session.commit()
    await db_session.refresh(offering)

    return offering


@pytest.fixture
async def second_master_offering(
    db_session: AsyncSession,
    second_master: Master,
    category: Category,
) -> MasterOffering:
    offering = MasterOffering(
        master_id=second_master.id,
        category_id=category.id,
        title="Nail Care",
        description="Professional nail service.",
        price=Decimal("40.00"),
        duration_minutes=90,
        is_active=True,
    )

    db_session.add(offering)
    await db_session.commit()
    await db_session.refresh(offering)

    return offering


@pytest.fixture
async def child_category_offering(
    db_session: AsyncSession,
    master: Master,
    child_category: Category,
) -> MasterOffering:
    offering = MasterOffering(
        master_id=master.id,
        category_id=child_category.id,
        title="Coloring Service",
        description="Professional coloring.",
        price=Decimal("55.00"),
        duration_minutes=120,
        is_active=True,
    )

    db_session.add(offering)
    await db_session.commit()
    await db_session.refresh(offering)

    return offering