import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.tags.models import Tag
from src.tags.repository import TagRepository


@pytest.mark.anyio
async def test_get_tags_returns_only_active_sorted(
    ac: AsyncClient,
    tag: Tag,
    second_tag: Tag,
    inactive_tag: Tag,
):
    response = await ac.get("/tags")

    assert response.status_code == 200

    data = response.json()

    assert [item["name"] for item in data] == [
        "Hair",
        "Nails",
    ]

    assert all(item["is_active"] for item in data)

    assert str(inactive_tag.id) not in {item["id"] for item in data}


@pytest.mark.anyio
async def test_get_all_tags_as_admin(
    ac: AsyncClient,
    tag: Tag,
    second_tag: Tag,
    inactive_tag: Tag,
    admin_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/tags/admin",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200

    assert [item["name"] for item in response.json()] == [
        "Hair",
        "Massage",
        "Nails",
    ]


@pytest.mark.anyio
async def test_get_all_tags_without_token(
    ac: AsyncClient,
):
    response = await ac.get("/tags/admin")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_all_tags_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/tags/admin",
        headers=auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {"detail": ("Доступ разрешён только администраторам!")}


@pytest.mark.anyio
async def test_create_tag(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        "/tags",
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
    assert data["is_active"] is True

    repository = TagRepository(db_session)

    tag = await repository.get_by_slug("hair-styling")

    assert tag is not None
    assert tag.id == uuid.UUID(data["id"])


@pytest.mark.anyio
async def test_create_tag_without_token(
    ac: AsyncClient,
):
    response = await ac.post(
        "/tags",
        json={
            "name": "Hair",
            "slug": "hair",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_tag_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        "/tags",
        headers=auth_headers,
        json={
            "name": "Hair",
            "slug": "hair",
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_tag_duplicate_name(
    ac: AsyncClient,
    tag: Tag,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/tags",
        headers=admin_auth_headers,
        json={
            "name": "  Hair  ",
            "slug": "other-slug",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": ("Тег с таким названием или slug уже существует!")
    }


@pytest.mark.anyio
async def test_create_tag_duplicate_slug(
    ac: AsyncClient,
    tag: Tag,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/tags",
        headers=admin_auth_headers,
        json={
            "name": "Other",
            "slug": " HAIR ",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": ("Тег с таким названием или slug уже существует!")
    }


@pytest.mark.anyio
async def test_create_tag_invalid_name(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/tags",
        headers=admin_auth_headers,
        json={
            "name": "A",
            "slug": "valid-slug",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_tag(
    ac: AsyncClient,
    tag: Tag,
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        f"/tags/{tag.id}",
        headers=admin_auth_headers,
        json={
            "name": "  Hair   Design ",
            "slug": " HAIR-DESIGN ",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(tag.id)
    assert data["name"] == "Hair Design"
    assert data["slug"] == "hair-design"
    assert data["is_active"] is False

    repository = TagRepository(db_session)

    tag_from_database = await repository.get_by_id(tag.id)

    assert tag_from_database is not None
    assert tag_from_database.name == "Hair Design"
    assert tag_from_database.slug == "hair-design"
    assert tag_from_database.is_active is False


@pytest.mark.anyio
async def test_update_tag_not_found(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    tag_id = uuid.uuid4()

    response = await ac.patch(
        f"/tags/{tag_id}",
        headers=admin_auth_headers,
        json={
            "name": "Hair",
        },
    )

    assert response.status_code == 404

    assert response.json() == {"detail": "Тег не найден!"}


@pytest.mark.anyio
async def test_update_tag_duplicate_name(
    ac: AsyncClient,
    tag: Tag,
    second_tag: Tag,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/tags/{second_tag.id}",
        headers=admin_auth_headers,
        json={
            "name": tag.name,
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_update_tag_duplicate_slug(
    ac: AsyncClient,
    tag: Tag,
    second_tag: Tag,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/tags/{second_tag.id}",
        headers=admin_auth_headers,
        json={
            "slug": tag.slug,
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_update_tag_invalid_uuid(
    ac: AsyncClient,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/tags/not-a-uuid",
        headers=admin_auth_headers,
        json={
            "name": "Hair",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_deactivate_tag_hides_it_from_public_list(
    ac: AsyncClient,
    tag: Tag,
    admin_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/tags/{tag.id}",
        headers=admin_auth_headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    public_response = await ac.get("/tags")

    assert public_response.status_code == 200

    assert str(tag.id) not in {item["id"] for item in public_response.json()}

    admin_response = await ac.get(
        "/tags/admin",
        headers=admin_auth_headers,
    )

    assert admin_response.status_code == 200

    assert str(tag.id) in {item["id"] for item in admin_response.json()}
