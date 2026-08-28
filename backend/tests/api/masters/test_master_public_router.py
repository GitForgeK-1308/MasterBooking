import uuid

import pytest
from httpx import AsyncClient

from src.masters.models import Master


@pytest.mark.anyio
async def test_get_masters_returns_only_active_sorted(
    ac: AsyncClient,
    master: Master,
    second_master: Master,
    inactive_master: Master,
):
    response = await ac.get("/masters")

    assert response.status_code == 200

    data = response.json()

    assert [
        (
            item["last_name"],
            item["first_name"],
        )
        for item in data
    ] == [
        (
            "Andersone",
            "Irina",
        ),
        (
            "Petrova",
            "Anna",
        ),
    ]

    assert str(inactive_master.id) not in {item["id"] for item in data}


@pytest.mark.anyio
async def test_get_master_by_id(
    ac: AsyncClient,
    master: Master,
):
    response = await ac.get(f"/masters/{master.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(master.id)
    assert data["first_name"] == "Anna"
    assert data["last_name"] == "Petrova"
    assert data["experience"] == 5
    assert data["phone"] == "+37120000001"
    assert data["avatar_url"] == "/uploads/avatars/master.png"

    assert data["city"] == "Riga"
    assert data["district"] == "Centrs"
    assert data["address"] == "Main Street 10"


@pytest.mark.anyio
async def test_get_inactive_master_returns_404(
    ac: AsyncClient,
    inactive_master: Master,
):
    response = await ac.get(f"/masters/{inactive_master.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Мастер не найден!"}


@pytest.mark.anyio
async def test_get_master_not_found(
    ac: AsyncClient,
):
    response = await ac.get(f"/masters/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Мастер не найден!"}


@pytest.mark.anyio
async def test_get_master_invalid_uuid(
    ac: AsyncClient,
):
    response = await ac.get("/masters/not-a-uuid")

    assert response.status_code == 422
