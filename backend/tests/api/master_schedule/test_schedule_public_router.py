import uuid

import pytest
from httpx import AsyncClient

from src.master_schedule.models import (
    MasterSchedule,
)
from src.masters.models import Master


@pytest.mark.anyio
async def test_get_master_schedules(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    tuesday_schedule: MasterSchedule,
    day_off_schedule: MasterSchedule,
):
    response = await ac.get(
        f"/masters/{master.id}/schedules"
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["day_of_week"]
        for item in data
    ] == [
        "monday",
        "tuesday",
        "sunday",
    ]

    assert all(
        item["master_id"]
        == str(master.id)
        for item in data
    )


@pytest.mark.anyio
async def test_get_schedule_by_id(
    ac: AsyncClient,
    monday_schedule: MasterSchedule,
):
    response = await ac.get(
        f"/schedules/{monday_schedule.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["id"]
        == str(monday_schedule.id)
    )
    assert data["day_of_week"] == "monday"
    assert data["start_time"] == "09:00:00"
    assert data["end_time"] == "17:00:00"
    assert data["is_working"] is True


@pytest.mark.anyio
async def test_get_schedule_not_found(
    ac: AsyncClient,
):
    response = await ac.get(
        f"/schedules/{uuid.uuid4()}"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Расписание не найдено!"
    }


@pytest.mark.anyio
async def test_get_schedule_invalid_uuid(
    ac: AsyncClient,
):
    response = await ac.get(
        "/schedules/not-a-uuid"
    )

    assert response.status_code == 422