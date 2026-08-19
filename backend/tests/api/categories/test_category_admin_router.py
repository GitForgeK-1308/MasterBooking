import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category
from src.categories.repository import CategoryRepository


@pytest.mark.anyio
async def test_get_all_categories_as_admin(
    ac: AsyncClient,
    category: Category,
    second_category: Category,
    inactive_category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/categories/admin",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200

    assert [
        item["name"]
        for item in response.json()
    ] == [
        "Beauty",
        "Massage",
        "Nails",
    ]


@pytest.mark.anyio
async def test_get_all_categories_without_token(
    ac: AsyncClient,
):
    response = await ac.get(
        "/categories/admin"
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_all_categories_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/categories/admin",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            "Доступ разрешён только "
            "администраторам!"
        )
    }


@pytest.mark.anyio
async def test_create_category(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        "/categories",
        headers=admin_auth_headers,
        json={
            "name": "  Hair   Styling  ",
            "slug": " HAIR-STYLING ",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Hair Styling"
    assert data["slug"] == "hair-styling"
    assert data["parent_id"] is None
    assert data["is_active"] is True

    repository = CategoryRepository(
        db_session
    )

    category = await repository.get_by_slug(
        "hair-styling"
    )

    assert category is not None
    assert category.id == uuid.UUID(
        data["id"]
    )


@pytest.mark.anyio
async def test_create_category_without_token(
    ac: AsyncClient,
):
    response = await ac.post(
        "/categories",
        json={
            "name": "Hair",
            "slug": "hair",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_category_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        "/categories",
        headers=auth_headers,
        json={
            "name": "Hair",
            "slug": "hair",
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_category_duplicate_name(
    ac: AsyncClient,
    category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/categories",
        headers=admin_auth_headers,
        json={
            "name": "  Beauty  ",
            "slug": "other-slug",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Категория с таким названием "
            "или slug уже существует!"
        )
    }


@pytest.mark.anyio
async def test_create_category_duplicate_slug(
    ac: AsyncClient,
    category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/categories",
        headers=admin_auth_headers,
        json={
            "name": "Other",
            "slug": " BEAUTY ",
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_create_category_parent_not_found(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    parent_id = uuid.uuid4()

    response = await ac.post(
        "/categories",
        headers=admin_auth_headers,
        json={
            "name": "Hair",
            "slug": "hair",
            "parent_id": str(
                parent_id
            ),
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Родительская категория "
            "не найдена!"
        )
    }


@pytest.mark.anyio
async def test_create_child_category(
    ac: AsyncClient,
    category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/categories",
        headers=admin_auth_headers,
        json={
            "name": "Hair",
            "slug": "hair",
            "parent_id": str(
                category.id
            ),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Hair"
    assert data["slug"] == "hair"
    assert data["parent_id"] == str(
        category.id
    )


@pytest.mark.anyio
async def test_create_category_invalid_name(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/categories",
        headers=admin_auth_headers,
        json={
            "name": "A",
            "slug": "valid-slug",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_category(
    ac: AsyncClient,
    category: Category,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        f"/categories/{category.id}",
        headers=admin_auth_headers,
        json={
            "name": "  New   Beauty ",
            "slug": " NEW-BEAUTY ",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Beauty"
    assert data["slug"] == "new-beauty"
    assert data["is_active"] is False

    repository = CategoryRepository(
        db_session
    )

    category_from_database = (
        await repository.get_by_id(
            category.id
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


@pytest.mark.anyio
async def test_update_category_not_found(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    category_id = uuid.uuid4()

    response = await ac.patch(
        f"/categories/{category_id}",
        headers=admin_auth_headers,
        json={
            "name": "Beauty",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Категория не найдена!"
    }


@pytest.mark.anyio
async def test_update_category_duplicate_name(
    ac: AsyncClient,
    category: Category,
    second_category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/categories/{second_category.id}",
        headers=admin_auth_headers,
        json={
            "name": category.name,
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_update_category_duplicate_slug(
    ac: AsyncClient,
    category: Category,
    second_category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/categories/{second_category.id}",
        headers=admin_auth_headers,
        json={
            "slug": category.slug,
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_update_category_cannot_be_own_parent(
    ac: AsyncClient,
    category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/categories/{category.id}",
        headers=admin_auth_headers,
        json={
            "parent_id": str(
                category.id
            ),
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Нельзя создать циклическую "
            "иерархию категорий!"
        )
    }


@pytest.mark.anyio
async def test_update_category_prevents_cycle(
    ac: AsyncClient,
    category: Category,
    child_category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/categories/{category.id}",
        headers=admin_auth_headers,
        json={
            "parent_id": str(
                child_category.id
            ),
        },
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_update_category_can_remove_parent(
    ac: AsyncClient,
    child_category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/categories/{child_category.id}",
        headers=admin_auth_headers,
        json={
            "parent_id": None,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["parent_id"]
        is None
    )


@pytest.mark.anyio
async def test_deactivate_category_hides_it_from_public_list(
    ac: AsyncClient,
    category: Category,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/categories/{category.id}",
        headers=admin_auth_headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    public_response = await ac.get(
        "/categories"
    )

    assert public_response.status_code == 200

    assert str(
        category.id
    ) not in {
        item["id"]
        for item in public_response.json()
    }

    admin_response = await ac.get(
        "/categories/admin",
        headers=admin_auth_headers,
    )

    assert admin_response.status_code == 200

    assert str(
        category.id
    ) in {
        item["id"]
        for item in admin_response.json()
    }