from decimal import Decimal

import pytest
from httpx import AsyncClient

from src.categories.models import Category
from src.locations.models import City
from src.master_offering.models import MasterOffering


@pytest.mark.anyio
async def test_get_public_offerings(
    ac: AsyncClient,
    offering: MasterOffering,
    inactive_offering: MasterOffering,
):
    response = await ac.get("/offerings")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 12
    assert data["total_pages"] == 1

    assert [item["id"] for item in data["items"]] == [str(offering.id)]

    assert str(inactive_offering.id) not in {item["id"] for item in data["items"]}


@pytest.mark.anyio
async def test_get_public_offering_by_id(
    ac: AsyncClient,
    offering: MasterOffering,
):
    response = await ac.get(f"/offerings/{offering.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(offering.id)
    assert data["title"] == "Classic Cut"
    assert Decimal(data["price"]) == Decimal("25.00")

    assert data["master"]["id"] == str(offering.master_id)


@pytest.mark.anyio
async def test_get_inactive_offering_by_id_returns_404(
    ac: AsyncClient,
    inactive_offering: MasterOffering,
):
    response = await ac.get(f"/offerings/{inactive_offering.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Услуга не найдена!"}


@pytest.mark.anyio
async def test_filter_offerings_by_parent_category(
    ac: AsyncClient,
    offering: MasterOffering,
    child_category_offering: MasterOffering,
    category: Category,
):
    response = await ac.get(
        "/offerings",
        params={
            "category_id": str(category.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert {item["id"] for item in data["items"]} == {
        str(offering.id),
        str(child_category_offering.id),
    }

    assert data["total"] == 2


@pytest.mark.anyio
async def test_search_offering_by_tag(
    ac: AsyncClient,
    offering: MasterOffering,
):
    response = await ac.get(
        "/offerings",
        params={
            "search": "hair",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0]["id"] == str(offering.id)


@pytest.mark.anyio
async def test_filter_offerings_by_city(
    ac: AsyncClient,
    offering: MasterOffering,
    city: City,
):
    response = await ac.get(
        "/offerings",
        params={
            "city_id": str(city.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == str(offering.id)


@pytest.mark.anyio
async def test_public_offerings_pagination(
    ac: AsyncClient,
    offering: MasterOffering,
    child_category_offering: MasterOffering,
    second_master_offering: MasterOffering,
):
    response = await ac.get(
        "/offerings",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2

    assert len(data["items"]) == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    "params",
    [
        {
            "min_price": 0,
        },
        {
            "search": "a",
        },
        {
            "page": 0,
        },
        {
            "page_size": 51,
        },
    ],
)
async def test_public_offerings_invalid_query(
    ac: AsyncClient,
    params: dict,
):
    response = await ac.get(
        "/offerings",
        params=params,
    )

    assert response.status_code == 422
