import uuid

import pytest
from httpx import AsyncClient

from src.masters.models import Master
from src.reviews.models import Review


@pytest.mark.anyio
async def test_get_public_master_reviews(
    ac: AsyncClient,
    master: Master,
    review: Review,
    second_review: Review,
):
    response = await ac.get(f"/masters/{master.id}/reviews")

    assert response.status_code == 200

    data = response.json()

    assert [item["id"] for item in data] == [
        str(second_review.id),
        str(review.id),
    ]

    assert [item["rating"] for item in data] == [
        4,
        5,
    ]

    assert all(item["client_name"] == "Ivan Ivanov" for item in data)


@pytest.mark.anyio
async def test_get_public_master_reviews_empty(
    ac: AsyncClient,
):
    response = await ac.get(f"/masters/{uuid.uuid4()}/reviews")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_public_review_deleted_user_name(
    ac: AsyncClient,
    master: Master,
    deleted_user_review: Review,
):
    response = await ac.get(f"/masters/{master.id}/reviews")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["id"] == str(deleted_user_review.id)

    assert data[0]["client_name"] == "Удалённый пользователь"


@pytest.mark.anyio
async def test_get_master_review_stats(
    ac: AsyncClient,
    master: Master,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
):
    response = await ac.get((f"/masters/{master.id}/reviews/stats"))

    assert response.status_code == 200

    assert response.json() == {
        "average_rating": 4.0,
        "reviews_count": 3,
    }


@pytest.mark.anyio
async def test_get_master_review_stats_empty(
    ac: AsyncClient,
):
    response = await ac.get((f"/masters/{uuid.uuid4()}/reviews/stats"))

    assert response.status_code == 200

    assert response.json() == {
        "average_rating": 0.0,
        "reviews_count": 0,
    }


@pytest.mark.anyio
async def test_get_master_reviews_full(
    ac: AsyncClient,
    master: Master,
    review: Review,
    second_review: Review,
    deleted_user_review: Review,
):
    response = await ac.get((f"/masters/{master.id}/reviews/full"))

    assert response.status_code == 200

    data = response.json()

    assert data["average_rating"] == 4.0
    assert data["reviews_count"] == 3

    assert data["rating_distribution"] == {
        "1": 0,
        "2": 0,
        "3": 1,
        "4": 1,
        "5": 1,
    }

    assert [item["id"] for item in data["reviews"]] == [
        str(deleted_user_review.id),
        str(second_review.id),
        str(review.id),
    ]


@pytest.mark.anyio
async def test_get_master_reviews_full_empty(
    ac: AsyncClient,
):
    response = await ac.get((f"/masters/{uuid.uuid4()}/reviews/full"))

    assert response.status_code == 200

    assert response.json() == {
        "average_rating": 0.0,
        "reviews_count": 0,
        "rating_distribution": {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0,
        },
        "reviews": [],
    }


@pytest.mark.anyio
async def test_get_master_reviews_invalid_uuid(
    ac: AsyncClient,
):
    response = await ac.get("/masters/not-a-uuid/reviews")

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_master_review_stats_invalid_uuid(
    ac: AsyncClient,
):
    response = await ac.get("/masters/not-a-uuid/reviews/stats")

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_master_reviews_full_invalid_uuid(
    ac: AsyncClient,
):
    response = await ac.get("/masters/not-a-uuid/reviews/full")

    assert response.status_code == 422
