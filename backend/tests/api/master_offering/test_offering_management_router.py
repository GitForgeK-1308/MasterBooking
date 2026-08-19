import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.categories.models import Category
from src.master_offering.models import MasterOffering
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.masters.models import Master
from src.tags.models import Tag


def offering_payload(
    *,
    category_id: uuid.UUID,
    tag_ids: list[uuid.UUID] | None = None,
) -> dict:
    return {
        "category_id": str(
            category_id
        ),
        "title": "Hair Styling",
        "description": (
            "Professional hair styling."
        ),
        "price": "35.50",
        "duration_minutes": 60,
        "tag_ids": [
            str(tag_id)
            for tag_id in (tag_ids or [])
        ],
    }


@pytest.mark.anyio
async def test_create_offering(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    category: Category,
    tag: Tag,
    second_tag: Tag,
    db_session: AsyncSession,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=offering_payload(
            category_id=category.id,
            tag_ids=[
                tag.id,
                second_tag.id,
            ],
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["master_id"] == str(
        master.id
    )
    assert data["category_id"] == str(
        category.id
    )
    assert data["title"] == "Hair Styling"
    assert (
        Decimal(data["price"])
        == Decimal("35.50")
    )
    assert data["duration_minutes"] == 60
    assert data["is_active"] is True

    assert {
        item["id"]
        for item in data["tags"]
    } == {
        str(tag.id),
        str(second_tag.id),
    }

    assert (
        data["master"]["id"]
        == str(master.id)
    )

    repository = MasterOfferingRepository(
        db_session
    )

    offering = await repository.get_by_id(
        uuid.UUID(
            data["id"]
        )
    )

    assert offering is not None
    assert offering.master_id == master.id
    assert offering.category_id == category.id


@pytest.mark.anyio
async def test_create_offering_without_token(
    ac: AsyncClient,
    category: Category,
):
    response = await ac.post(
        "/masters/me/offerings",
        json=offering_payload(
            category_id=category.id
        ),
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_offering_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
    category: Category,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=auth_headers,
        json=offering_payload(
            category_id=category.id
        ),
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_offering_master_without_profile(
    ac: AsyncClient,
    master_without_profile_headers: dict[str, str],
    category: Category,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_without_profile_headers,
        json=offering_payload(
            category_id=category.id
        ),
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_offering_category_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=offering_payload(
            category_id=uuid.uuid4()
        ),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Категория не найдена!"
    }


@pytest.mark.anyio
async def test_create_offering_inactive_category(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    inactive_category: Category,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=offering_payload(
            category_id=inactive_category.id
        ),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Выбранная категория "
            "недоступна!"
        )
    }


@pytest.mark.anyio
async def test_create_offering_tag_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    category: Category,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=offering_payload(
            category_id=category.id,
            tag_ids=[
                uuid.uuid4(),
            ],
        ),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Один или несколько тегов "
            "не найдены!"
        )
    }


@pytest.mark.anyio
async def test_create_offering_inactive_tag(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    category: Category,
    inactive_tag: Tag,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=offering_payload(
            category_id=category.id,
            tag_ids=[
                inactive_tag.id,
            ],
        ),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Один или несколько тегов "
            "неактивны!"
        )
    }


@pytest.mark.anyio
async def test_create_offering_deduplicates_tags(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    category: Category,
    tag: Tag,
):
    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=offering_payload(
            category_id=category.id,
            tag_ids=[
                tag.id,
                tag.id,
            ],
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert len(
        data["tags"]
    ) == 1

    assert (
        data["tags"][0]["id"]
        == str(tag.id)
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        (
            "title",
            "A",
        ),
        (
            "price",
            "0",
        ),
        (
            "duration_minutes",
            0,
        ),
    ],
)
async def test_create_offering_invalid_data(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    category: Category,
    field: str,
    value,
):
    payload = offering_payload(
        category_id=category.id
    )

    payload[field] = value

    response = await ac.post(
        "/masters/me/offerings",
        headers=master_auth_headers,
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_my_offerings_includes_inactive(
    ac: AsyncClient,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/offerings",
        headers=master_auth_headers,
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item in response.json()
    }

    assert str(
        offering.id
    ) in ids

    assert str(
        inactive_offering.id
    ) in ids


@pytest.mark.anyio
async def test_get_master_offerings_returns_only_active(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
):
    response = await ac.get(
        f"/masters/{master.id}/offerings"
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item in response.json()
    }

    assert str(
        offering.id
    ) in ids

    assert str(
        inactive_offering.id
    ) not in ids


@pytest.mark.anyio
async def test_update_offering(
    ac: AsyncClient,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
    second_category: Category,
    second_tag: Tag,
):
    response = await ac.patch(
        f"/offerings/{offering.id}",
        headers=master_auth_headers,
        json={
            "category_id": str(
                second_category.id
            ),
            "title": "Updated Service",
            "price": "45.75",
            "duration_minutes": 90,
            "tag_ids": [
                str(second_tag.id),
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Service"
    assert (
        Decimal(data["price"])
        == Decimal("45.75")
    )
    assert data["duration_minutes"] == 90
    assert data["category_id"] == str(
        second_category.id
    )

    assert [
        item["id"]
        for item in data["tags"]
    ] == [
        str(second_tag.id)
    ]


@pytest.mark.anyio
async def test_update_offering_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/offerings/{uuid.uuid4()}",
        headers=master_auth_headers,
        json={
            "title": "Updated Service",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Услуга не найдена!"
    }


@pytest.mark.anyio
async def test_update_foreign_offering_forbidden(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            "/offerings/"
            f"{second_master_offering.id}"
        ),
        headers=master_auth_headers,
        json={
            "title": "Updated Service",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            "Вы не можете изменять "
            "чужую услугу!"
        )
    }


@pytest.mark.anyio
async def test_update_offering_inactive_category(
    ac: AsyncClient,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
    inactive_category: Category,
):
    response = await ac.patch(
        f"/offerings/{offering.id}",
        headers=master_auth_headers,
        json={
            "category_id": str(
                inactive_category.id
            ),
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_update_offering_tag_not_found(
    ac: AsyncClient,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/offerings/{offering.id}",
        headers=master_auth_headers,
        json={
            "tag_ids": [
                str(
                    uuid.uuid4()
                ),
            ],
        },
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_offering_inactive_tag(
    ac: AsyncClient,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
    inactive_tag: Tag,
):
    response = await ac.patch(
        f"/offerings/{offering.id}",
        headers=master_auth_headers,
        json={
            "tag_ids": [
                str(
                    inactive_tag.id
                ),
            ],
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_update_offering_can_clear_tags(
    ac: AsyncClient,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/offerings/{offering.id}",
        headers=master_auth_headers,
        json={
            "tag_ids": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["tags"] == []


@pytest.mark.anyio
async def test_delete_offering_without_bookings(
    ac: AsyncClient,
    offering: MasterOffering,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    offering_id = offering.id

    response = await ac.delete(
        f"/offerings/{offering_id}",
        headers=master_auth_headers,
    )

    assert response.status_code == 204
    assert response.text == ""

    repository = MasterOfferingRepository(
        db_session
    )

    offering_from_database = (
        await repository.get_by_id(
            offering_id
        )
    )

    assert offering_from_database is None


@pytest.mark.anyio
async def test_delete_offering_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.delete(
        f"/offerings/{uuid.uuid4()}",
        headers=master_auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Услуга не найдена!"
    }


@pytest.mark.anyio
async def test_delete_foreign_offering_forbidden(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    master_auth_headers: dict[str, str],
):
    response = await ac.delete(
        (
            "/offerings/"
            f"{second_master_offering.id}"
        ),
        headers=master_auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            "Вы не можете удалять "
            "чужую услугу!"
        )
    }