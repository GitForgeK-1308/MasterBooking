import pytest
from httpx import AsyncClient

from src.categories.models import Category


@pytest.mark.anyio
async def test_get_categories_returns_only_active_sorted(
    ac: AsyncClient,
    category: Category,
    second_category: Category,
    inactive_category: Category,
):
    response = await ac.get(
        "/categories"
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["name"]
        for item in data
    ] == [
        "Beauty",
        "Nails",
    ]

    assert all(
        item["is_active"]
        for item in data
    )

    assert str(
        inactive_category.id
    ) not in {
        item["id"]
        for item in data
    }


@pytest.mark.anyio
async def test_get_category_tree(
    ac: AsyncClient,
    category: Category,
    child_category: Category,
    grandchild_category: Category,
):
    response = await ac.get(
        "/categories/tree"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    root = data[0]

    assert root["id"] == str(
        category.id
    )
    assert root["name"] == "Beauty"
    assert root["slug"] == "beauty"
    assert root["parent_id"] is None

    assert len(
        root["children"]
    ) == 1

    child = root["children"][0]

    assert child["id"] == str(
        child_category.id
    )
    assert child["name"] == "Hair"
    assert child["parent_id"] == str(
        category.id
    )

    assert len(
        child["children"]
    ) == 1

    grandchild = child["children"][0]

    assert grandchild["id"] == str(
        grandchild_category.id
    )
    assert grandchild["name"] == "Coloring"
    assert grandchild["parent_id"] == str(
        child_category.id
    )