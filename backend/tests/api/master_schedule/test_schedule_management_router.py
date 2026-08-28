import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.masters.models import Master


@pytest.mark.anyio
async def test_create_schedule(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=master_auth_headers,
        json={
            "day_of_week": "wednesday",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "is_working": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["master_id"] == str(master.id)
    assert data["day_of_week"] == "wednesday"
    assert data["start_time"] == "09:00:00"
    assert data["end_time"] == "17:00:00"
    assert data["is_working"] is True

    repository = MasterScheduleRepository(db_session)

    schedule = await repository.get_by_master_and_day(
        master_id=master.id,
        day_of_week=WeekDay.WEDNESDAY,
    )

    assert schedule is not None
    assert schedule.id == uuid.UUID(data["id"])


@pytest.mark.anyio
async def test_create_day_off_schedule(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=master_auth_headers,
        json={
            "day_of_week": "sunday",
            "is_working": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["day_of_week"] == "sunday"
    assert data["start_time"] is None
    assert data["end_time"] is None
    assert data["is_working"] is False


@pytest.mark.anyio
async def test_create_schedule_without_token(
    ac: AsyncClient,
):
    response = await ac.post(
        "/masters/me/schedules",
        json={
            "day_of_week": "monday",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "is_working": True,
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_schedule_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=auth_headers,
        json={
            "day_of_week": "monday",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "is_working": True,
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_duplicate_schedule(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=master_auth_headers,
        json={
            "day_of_week": "monday",
            "start_time": "10:00:00",
            "end_time": "18:00:00",
            "is_working": True,
        },
    )

    assert response.status_code == 409

    assert response.json() == {"detail": ("Расписание на этот день уже существует!")}


@pytest.mark.anyio
async def test_create_working_schedule_without_end_time(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=master_auth_headers,
        json={
            "day_of_week": "monday",
            "start_time": "09:00:00",
            "is_working": True,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_schedule_start_must_be_before_end(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=master_auth_headers,
        json={
            "day_of_week": "monday",
            "start_time": "18:00:00",
            "end_time": "09:00:00",
            "is_working": True,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_day_off_cannot_have_time(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/me/schedules",
        headers=master_auth_headers,
        json={
            "day_of_week": "sunday",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "is_working": False,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_my_schedules(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    tuesday_schedule: MasterSchedule,
    day_off_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/schedules",
        headers=master_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert [item["day_of_week"] for item in data] == [
        "monday",
        "tuesday",
        "sunday",
    ]

    assert {item["id"] for item in data} == {
        str(monday_schedule.id),
        str(tuesday_schedule.id),
        str(day_off_schedule.id),
    }


@pytest.mark.anyio
async def test_update_schedule(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.patch(
        f"/schedules/{monday_schedule.id}",
        headers=master_auth_headers,
        json={
            "start_time": "10:00:00",
            "end_time": "19:00:00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["start_time"] == "10:00:00"
    assert data["end_time"] == "19:00:00"
    assert data["is_working"] is True

    repository = MasterScheduleRepository(db_session)

    schedule = await repository.get_by_id(monday_schedule.id)

    assert schedule is not None
    assert schedule.start_time.isoformat() == "10:00:00"
    assert schedule.end_time.isoformat() == "19:00:00"


@pytest.mark.anyio
async def test_update_schedule_to_day_off_clears_time(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/schedules/{monday_schedule.id}",
        headers=master_auth_headers,
        json={
            "is_working": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_working"] is False
    assert data["start_time"] is None
    assert data["end_time"] is None


@pytest.mark.anyio
async def test_update_day_off_to_working_requires_time(
    ac: AsyncClient,
    master: Master,
    day_off_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/schedules/{day_off_schedule.id}",
        headers=master_auth_headers,
        json={
            "is_working": True,
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": ("Для рабочего дня необходимо указать время начала и окончания")
    }


@pytest.mark.anyio
async def test_update_schedule_duplicate_day(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    tuesday_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/schedules/{monday_schedule.id}",
        headers=master_auth_headers,
        json={
            "day_of_week": "tuesday",
        },
    )

    assert response.status_code == 409

    assert response.json() == {"detail": ("Расписание на этот день уже существует!")}


@pytest.mark.anyio
async def test_update_foreign_schedule_forbidden(
    ac: AsyncClient,
    master: Master,
    foreign_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/schedules/{foreign_schedule.id}",
        headers=master_auth_headers,
        json={
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 403

    assert response.json() == {"detail": ("Вы не можете изменять чужое расписание!")}


@pytest.mark.anyio
async def test_update_schedule_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        f"/schedules/{uuid.uuid4()}",
        headers=master_auth_headers,
        json={
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 404

    assert response.json() == {"detail": "Расписание не найдено!"}


@pytest.mark.anyio
async def test_delete_schedule(
    ac: AsyncClient,
    master: Master,
    monday_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    schedule_id = monday_schedule.id

    response = await ac.delete(
        f"/schedules/{schedule_id}",
        headers=master_auth_headers,
    )

    assert response.status_code == 204
    assert response.text == ""

    repository = MasterScheduleRepository(db_session)

    schedule = await repository.get_by_id(schedule_id)

    assert schedule is None


@pytest.mark.anyio
async def test_delete_foreign_schedule_forbidden(
    ac: AsyncClient,
    master: Master,
    foreign_schedule: MasterSchedule,
    master_auth_headers: dict[str, str],
):
    response = await ac.delete(
        f"/schedules/{foreign_schedule.id}",
        headers=master_auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {"detail": ("Вы не можете удалять чужое расписание!")}


@pytest.mark.anyio
async def test_delete_schedule_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.delete(
        f"/schedules/{uuid.uuid4()}",
        headers=master_auth_headers,
    )

    assert response.status_code == 404

    assert response.json() == {"detail": "Расписание не найдено!"}
