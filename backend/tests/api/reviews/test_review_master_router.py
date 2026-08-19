import pytest
from httpx import AsyncClient

from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.reviews.models import Review


@pytest.mark.anyio
async def test_get_my_reviews(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
    foreign_master_review: Review,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/reviews",
        headers=master_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["id"]
        for item in data
    ] == [
        str(deleted_user_review.id),
        str(second_review.id),
        str(review.id),
    ]

    assert all(
        item["offering_id"]
        == str(offering.id)
        for item in data
    )

    assert all(
        item["offering_title"]
        == "Classic Cut"
        for item in data
    )

    assert (
        data[0]["client_name"]
        == "Удалённый пользователь"
    )

    assert (
        data[1]["client_name"]
        == "Ivan Ivanov"
    )

    assert (
        data[2]["client_name"]
        == "Ivan Ivanov"
    )

    assert str(
        foreign_master_review.id
    ) not in {
        item["id"]
        for item in data
    }


@pytest.mark.anyio
async def test_get_my_reviews_scoped_to_current_master(
    ac: AsyncClient,
    review: Review,
    second_master: Master,
    second_master_offering: MasterOffering,
    foreign_master_review: Review,
    second_master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/reviews",
        headers=second_master_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert (
        data[0]["id"]
        == str(foreign_master_review.id)
    )

    assert (
        data[0]["offering_id"]
        == str(second_master_offering.id)
    )

    assert (
        data[0]["offering_title"]
        == "Nail Care"
    )

    assert str(review.id) not in {
        item["id"]
        for item in data
    }


@pytest.mark.anyio
async def test_get_my_reviews_empty(
    ac: AsyncClient,
    second_master: Master,
    second_master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/reviews",
        headers=second_master_auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_my_reviews_without_token(
    ac: AsyncClient,
):
    response = await ac.get(
        "/masters/me/reviews"
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_my_reviews_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/reviews",
        headers=auth_headers,
    )

    assert response.status_code == 403