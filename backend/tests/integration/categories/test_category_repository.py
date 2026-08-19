import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category
from src.categories.repository import CategoryRepository


def make_category(
    *,
    name: str = "Beauty",
    slug: str = "beauty",
    parent_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> Category:
    return Category(
        name=name,
        slug=slug,
        parent_id=parent_id,
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_create_category(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    category = make_category()

    result = await repository.create(
        category
    )

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )
    assert result.name == "Beauty"
    assert result.slug == "beauty"
    assert result.parent_id is None
    assert result.is_active is True


@pytest.mark.anyio
async def test_get_all_categories_sorted(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    await repository.create(
        make_category(
            name="Nails",
            slug="nails",
        )
    )

    await repository.create(
        make_category(
            name="Beauty",
            slug="beauty",
        )
    )

    await repository.create(
        make_category(
            name="Massage",
            slug="massage",
            is_active=False,
        )
    )

    result = await repository.get_all()

    assert [
        category.name
        for category in result
    ] == [
        "Beauty",
        "Massage",
        "Nails",
    ]


@pytest.mark.anyio
async def test_get_active_categories(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    await repository.create(
        make_category(
            name="Nails",
            slug="nails",
        )
    )

    await repository.create(
        make_category(
            name="Beauty",
            slug="beauty",
        )
    )

    await repository.create(
        make_category(
            name="Massage",
            slug="massage",
            is_active=False,
        )
    )

    result = await repository.get_active()

    assert [
        category.name
        for category in result
    ] == [
        "Beauty",
        "Nails",
    ]

    assert all(
        category.is_active
        for category in result
    )


@pytest.mark.anyio
async def test_get_category_by_id(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    category = await repository.create(
        make_category()
    )

    result = await repository.get_by_id(
        category.id
    )

    assert result is not None
    assert result.id == category.id
    assert result.name == "Beauty"


@pytest.mark.anyio
async def test_get_category_by_id_not_found(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    result = await repository.get_by_id(
        uuid.uuid4()
    )

    assert result is None


@pytest.mark.anyio
async def test_get_category_by_slug(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    category = await repository.create(
        make_category()
    )

    result = await repository.get_by_slug(
        "beauty"
    )

    assert result is not None
    assert result.id == category.id
    assert result.slug == "beauty"


@pytest.mark.anyio
async def test_get_category_by_slug_not_found(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    result = await repository.get_by_slug(
        "missing"
    )

    assert result is None


@pytest.mark.anyio
async def test_get_category_by_name(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    category = await repository.create(
        make_category()
    )

    result = await repository.get_by_name(
        "Beauty"
    )

    assert result is not None
    assert result.id == category.id
    assert result.name == "Beauty"


@pytest.mark.anyio
async def test_get_category_by_name_not_found(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    result = await repository.get_by_name(
        "Missing"
    )

    assert result is None


@pytest.mark.anyio
async def test_create_child_category(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    parent = await repository.create(
        make_category()
    )

    child = await repository.create(
        make_category(
            name="Hair",
            slug="hair",
            parent_id=parent.id,
        )
    )

    child_id = child.id

    db_session.expunge(
        child
    )

    result = await repository.get_by_id(
        child_id
    )

    assert result is not None
    assert result.parent_id == parent.id


@pytest.mark.anyio
async def test_update_category(
    db_session: AsyncSession,
):
    repository = CategoryRepository(
        db_session
    )

    category = await repository.create(
        make_category()
    )

    category.name = "New Beauty"
    category.slug = "new-beauty"
    category.is_active = False

    result = await repository.update(
        category
    )

    assert result.name == "New Beauty"
    assert result.slug == "new-beauty"
    assert result.is_active is False

    category_id = result.id

    db_session.expunge(
        result
    )

    category_from_database = (
        await repository.get_by_id(
            category_id
        )
    )

    assert category_from_database is not None
    assert (
        category_from_database.name
        == "New Beauty"
    )
    assert (
        category_from_database.slug
        == "new-beauty"
    )
    assert (
        category_from_database.is_active
        is False
    )