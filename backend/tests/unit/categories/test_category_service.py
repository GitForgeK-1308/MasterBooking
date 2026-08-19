import uuid
from unittest.mock import AsyncMock

import pytest

from src.categories.exceptions import (
    CategoryAlreadyExistsError,
    CategoryInvalidParentError,
    CategoryNotFoundError,
)
from src.categories.models import Category
from src.categories.repository import CategoryRepository
from src.categories.schemas import (
    CategoryCreate,
    CategoryUpdate,
)
from src.categories.service import CategoryService


def make_category(
    *,
    name: str = "Beauty",
    slug: str = "beauty",
    parent_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> Category:
    return Category(
        id=uuid.uuid4(),
        name=name,
        slug=slug,
        parent_id=parent_id,
        is_active=is_active,
    )


@pytest.fixture
def category_repository() -> AsyncMock:
    return AsyncMock(
        spec=CategoryRepository
    )


@pytest.fixture
def category_service(
    category_repository: AsyncMock,
) -> CategoryService:
    return CategoryService(
        repository=category_repository
    )


@pytest.mark.anyio
async def test_get_categories(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    categories = [
        make_category(),
        make_category(
            name="Nails",
            slug="nails",
        ),
    ]

    category_repository.get_active.return_value = (
        categories
    )

    result = await category_service.get_categories()

    assert result == categories

    category_repository.get_active.assert_awaited_once_with()


@pytest.mark.anyio
async def test_get_all_categories(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    categories = [
        make_category(),
        make_category(
            name="Inactive",
            slug="inactive",
            is_active=False,
        ),
    ]

    category_repository.get_all.return_value = (
        categories
    )

    result = (
        await category_service.get_all_categories()
    )

    assert result == categories

    category_repository.get_all.assert_awaited_once_with()


@pytest.mark.anyio
async def test_get_category_by_id(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()

    category_repository.get_by_id.return_value = (
        category
    )

    result = (
        await category_service.get_category_by_id(
            category.id
        )
    )

    assert result is category

    category_repository.get_by_id.assert_awaited_once_with(
        category.id
    )


@pytest.mark.anyio
async def test_get_category_by_id_not_found(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category_id = uuid.uuid4()

    category_repository.get_by_id.return_value = (
        None
    )

    with pytest.raises(
        CategoryNotFoundError
    ):
        await category_service.get_category_by_id(
            category_id
        )

    category_repository.get_by_id.assert_awaited_once_with(
        category_id
    )


@pytest.mark.anyio
async def test_create_category(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    data = CategoryCreate(
        name="  Hair   Styling  ",
        slug=" HAIR-STYLING ",
    )

    category_repository.get_by_name.return_value = (
        None
    )
    category_repository.get_by_slug.return_value = (
        None
    )
    category_repository.create.side_effect = (
        lambda category: category
    )

    result = await category_service.create_category(
        data
    )

    assert result.name == "Hair Styling"
    assert result.slug == "hair-styling"
    assert result.parent_id is None

    category_repository.get_by_name.assert_awaited_once_with(
        "Hair Styling"
    )
    category_repository.get_by_slug.assert_awaited_once_with(
        "hair-styling"
    )
    category_repository.create.assert_awaited_once_with(
        result
    )


@pytest.mark.anyio
async def test_create_category_duplicate_name(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    existing_category = make_category()

    category_repository.get_by_name.return_value = (
        existing_category
    )

    data = CategoryCreate(
        name="Beauty",
        slug="other",
    )

    with pytest.raises(
        CategoryAlreadyExistsError
    ):
        await category_service.create_category(
            data
        )

    category_repository.get_by_slug.assert_not_awaited()
    category_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_category_duplicate_slug(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    existing_category = make_category()

    category_repository.get_by_name.return_value = (
        None
    )
    category_repository.get_by_slug.return_value = (
        existing_category
    )

    data = CategoryCreate(
        name="Other",
        slug=" BEAUTY ",
    )

    with pytest.raises(
        CategoryAlreadyExistsError
    ):
        await category_service.create_category(
            data
        )

    category_repository.get_by_slug.assert_awaited_once_with(
        "beauty"
    )
    category_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_category_with_parent(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    parent = make_category()

    category_repository.get_by_name.return_value = (
        None
    )
    category_repository.get_by_slug.return_value = (
        None
    )
    category_repository.get_by_id.return_value = (
        parent
    )
    category_repository.create.side_effect = (
        lambda category: category
    )

    data = CategoryCreate(
        name="Hair",
        slug="hair",
        parent_id=parent.id,
    )

    result = await category_service.create_category(
        data
    )

    assert result.parent_id == parent.id

    category_repository.get_by_id.assert_awaited_once_with(
        parent.id
    )
    category_repository.create.assert_awaited_once_with(
        result
    )


@pytest.mark.anyio
async def test_create_category_parent_not_found(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    parent_id = uuid.uuid4()

    category_repository.get_by_name.return_value = (
        None
    )
    category_repository.get_by_slug.return_value = (
        None
    )
    category_repository.get_by_id.return_value = (
        None
    )

    data = CategoryCreate(
        name="Hair",
        slug="hair",
        parent_id=parent_id,
    )

    with pytest.raises(
        CategoryNotFoundError
    ):
        await category_service.create_category(
            data
        )

    category_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_update_category(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()

    category_repository.get_by_id.return_value = (
        category
    )
    category_repository.get_by_name.return_value = (
        None
    )
    category_repository.get_by_slug.return_value = (
        None
    )
    category_repository.update.side_effect = (
        lambda category: category
    )

    data = CategoryUpdate(
        name="  New   Beauty ",
        slug=" NEW-BEAUTY ",
        is_active=False,
    )

    result = await category_service.update_category(
        category_id=category.id,
        data=data,
    )

    assert result is category
    assert category.name == "New Beauty"
    assert category.slug == "new-beauty"
    assert category.is_active is False

    category_repository.update.assert_awaited_once_with(
        category
    )


@pytest.mark.anyio
async def test_update_category_duplicate_name(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()

    existing_category = make_category(
        name="Nails",
        slug="nails",
    )

    category_repository.get_by_id.return_value = (
        category
    )
    category_repository.get_by_name.return_value = (
        existing_category
    )

    data = CategoryUpdate(
        name="Nails"
    )

    with pytest.raises(
        CategoryAlreadyExistsError
    ):
        await category_service.update_category(
            category_id=category.id,
            data=data,
        )

    category_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_category_duplicate_slug(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()

    existing_category = make_category(
        name="Nails",
        slug="nails",
    )

    category_repository.get_by_id.return_value = (
        category
    )
    category_repository.get_by_slug.return_value = (
        existing_category
    )

    data = CategoryUpdate(
        slug="nails"
    )

    with pytest.raises(
        CategoryAlreadyExistsError
    ):
        await category_service.update_category(
            category_id=category.id,
            data=data,
        )

    category_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_category_cannot_be_own_parent(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()

    category_repository.get_by_id.return_value = (
        category
    )

    data = CategoryUpdate(
        parent_id=category.id
    )

    with pytest.raises(
        CategoryInvalidParentError
    ):
        await category_service.update_category(
            category_id=category.id,
            data=data,
        )

    category_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_category_parent_not_found(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()
    parent_id = uuid.uuid4()

    category_repository.get_by_id.side_effect = [
        category,
        None,
    ]

    data = CategoryUpdate(
        parent_id=parent_id
    )

    with pytest.raises(
        CategoryNotFoundError
    ):
        await category_service.update_category(
            category_id=category.id,
            data=data,
        )

    category_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_category_prevents_cycle(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    category = make_category()

    child = make_category(
        name="Hair",
        slug="hair",
        parent_id=category.id,
    )

    category_repository.get_by_id.side_effect = [
        category,
        child,
        category,
    ]

    data = CategoryUpdate(
        parent_id=child.id
    )

    with pytest.raises(
        CategoryInvalidParentError
    ):
        await category_service.update_category(
            category_id=category.id,
            data=data,
        )

    category_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_category_can_remove_parent(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    parent_id = uuid.uuid4()

    category = make_category(
        parent_id=parent_id
    )

    category_repository.get_by_id.return_value = (
        category
    )
    category_repository.update.side_effect = (
        lambda category: category
    )

    data = CategoryUpdate(
        parent_id=None
    )

    result = await category_service.update_category(
        category_id=category.id,
        data=data,
    )

    assert result.parent_id is None

    category_repository.update.assert_awaited_once_with(
        category
    )


@pytest.mark.anyio
async def test_get_category_tree(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    root = make_category(
        name="Beauty",
        slug="beauty",
    )

    child = make_category(
        name="Hair",
        slug="hair",
        parent_id=root.id,
    )

    grandchild = make_category(
        name="Coloring",
        slug="coloring",
        parent_id=child.id,
    )

    category_repository.get_active.return_value = [
        root,
        child,
        grandchild,
    ]

    result = (
        await category_service.get_category_tree()
    )

    assert len(result) == 1

    root_node = result[0]

    assert root_node.id == root.id
    assert root_node.name == "Beauty"
    assert root_node.parent_id is None

    assert len(root_node.children) == 1

    child_node = root_node.children[0]

    assert child_node.id == child.id
    assert child_node.parent_id == root.id

    assert len(child_node.children) == 1

    grandchild_node = child_node.children[0]

    assert grandchild_node.id == grandchild.id
    assert grandchild_node.parent_id == child.id


@pytest.mark.anyio
async def test_get_category_tree_treats_category_with_missing_parent_as_root(
    category_service: CategoryService,
    category_repository: AsyncMock,
):
    missing_parent_id = uuid.uuid4()

    category = make_category(
        name="Hair",
        slug="hair",
        parent_id=missing_parent_id,
    )

    category_repository.get_active.return_value = [
        category
    ]

    result = (
        await category_service.get_category_tree()
    )

    assert len(result) == 1
    assert result[0].id == category.id
    assert (
        result[0].parent_id
        == missing_parent_id
    )
    assert result[0].children == []