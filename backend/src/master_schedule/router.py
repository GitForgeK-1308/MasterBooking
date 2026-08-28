import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependencies import get_current_master_profile
from src.master_schedule.dependencies import get_schedule_service
from src.master_schedule.exceptions import (
    MasterNotFoundError,
    ScheduleAccessDeniedError,
    ScheduleAlreadyExistsError,
)
from src.master_schedule.schemas import (
    MasterScheduleCreate,
    MasterScheduleResponse,
    MasterScheduleUpdate,
)
from src.master_schedule.service import MasterScheduleService
from src.masters.models import Master

router = APIRouter(tags=["Master schedules"])


@router.post(
    "/masters/me/schedules",
    response_model=MasterScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    data: MasterScheduleCreate,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterScheduleService = Depends(get_schedule_service),
):
    try:
        return await service.create_schedule(
            master_id=current_master.id,
            data=data,
        )

    except MasterNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мастер не найден!",
        ) from None

    except ScheduleAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Расписание на этот день уже существует!",
        ) from None


@router.get(
    "/masters/me/schedules",
    response_model=list[MasterScheduleResponse],
)
async def get_my_schedules(
    current_master: Master = Depends(get_current_master_profile),
    service: MasterScheduleService = Depends(get_schedule_service),
):
    return await service.get_master_schedules(master_id=current_master.id)


@router.get(
    "/masters/{master_id}/schedules",
    response_model=list[MasterScheduleResponse],
)
async def get_master_schedules(
    master_id: uuid.UUID,
    service: MasterScheduleService = Depends(get_schedule_service),
):
    return await service.get_master_schedules(master_id=master_id)


@router.get(
    "/schedules/{schedule_id}",
    response_model=MasterScheduleResponse,
)
async def get_schedule_by_id(
    schedule_id: uuid.UUID,
    service: MasterScheduleService = Depends(get_schedule_service),
):
    schedule = await service.get_schedule_by_id(schedule_id)

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Расписание не найдено!",
        )

    return schedule


@router.patch(
    "/schedules/{schedule_id}",
    response_model=MasterScheduleResponse,
)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: MasterScheduleUpdate,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterScheduleService = Depends(get_schedule_service),
):
    try:
        schedule = await service.update_schedule(
            schedule_id=schedule_id,
            master_id=current_master.id,
            data=data,
        )

        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Расписание не найдено!",
            )

        return schedule

    except ScheduleAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете изменять чужое расписание!",
        ) from None

    except ScheduleAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Расписание на этот день уже существует!",
        ) from None

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from None


@router.delete(
    "/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_schedule(
    schedule_id: uuid.UUID,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterScheduleService = Depends(get_schedule_service),
) -> None:
    try:
        deleted = await service.delete_schedule(
            schedule_id=schedule_id,
            master_id=current_master.id,
        )

        if deleted is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Расписание не найдено!",
            )

    except ScheduleAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете удалять чужое расписание!",
        ) from None
