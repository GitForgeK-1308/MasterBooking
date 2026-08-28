import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependencies import (
    get_current_master_profile,
    get_current_user,
)
from src.locations.exceptions import (
    CityNotFoundError,
    DistrictCityMismatchError,
    DistrictNotFoundError,
)
from src.masters.dependencies import (
    get_master_service,
)
from src.masters.exceptions import (
    MasterProfileAlreadyExistsError,
)
from src.masters.models import Master
from src.masters.schemas import (
    MasterProfileCreate,
    MasterResponse,
    MasterUpdate,
)
from src.masters.service import MasterService
from src.users.models import User

router = APIRouter(
    prefix="/masters",
    tags=["Masters"],
)


@router.get(
    "",
    response_model=list[MasterResponse],
)
async def get_masters(
    service: MasterService = Depends(get_master_service),
):
    return await service.get_masters()


@router.post(
    "/profile",
    response_model=MasterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_master_profile(
    data: MasterProfileCreate,
    current_user: User = Depends(get_current_user),
    service: MasterService = Depends(get_master_service),
):
    try:
        return await service.create_master_profile(
            current_user=current_user,
            data=data,
        )

    except MasterProfileAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Профиль мастера уже существует!",
        ) from None

    except CityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Город не найден или недоступен!",
        ) from None

    except DistrictNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Район не найден или недоступен!",
        ) from None

    except DistrictCityMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Выбранный район не относится к выбранному городу!"),
        ) from None

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from None


@router.get(
    "/me",
    response_model=MasterResponse,
)
async def get_my_master_profile(
    current_master: Master = Depends(get_current_master_profile),
):
    return current_master


@router.patch(
    "/me",
    response_model=MasterResponse,
)
async def update_my_master_profile(
    data: MasterUpdate,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterService = Depends(get_master_service),
):
    try:
        master = await service.update_master(
            master_id=current_master.id,
            data=data,
        )

        if master is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Мастер не найден!",
            )

        return master

    except CityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Город не найден или недоступен!",
        ) from None

    except DistrictNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Район не найден или недоступен!",
        ) from None

    except DistrictCityMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Выбранный район не относится к выбранному городу!"),
        ) from None

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from None


@router.get(
    "/{master_id}",
    response_model=MasterResponse,
)
async def get_master(
    master_id: uuid.UUID,
    service: MasterService = Depends(get_master_service),
):
    master = await service.get_master_by_id(master_id)

    if master is None or not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мастер не найден!",
        )

    return master
