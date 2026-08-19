import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependencies import get_current_admin
from src.locations.dependencies import get_location_service
from src.locations.exceptions import (
    CityAlreadyExistsError,
    CityNotFoundError,
    DistrictAlreadyExistsError,
    DistrictNotFoundError,
)
from src.locations.schemas import (
    CityCreate,
    CityResponse,
    CityUpdate,
    DistrictCreate,
    DistrictResponse,
    DistrictUpdate,
)
from src.locations.service import LocationService
from src.users.models import User

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


@router.get(
    "/cities",
    response_model=list[CityResponse],
)
async def get_cities(
    service: LocationService = Depends(
        get_location_service
    ),
):
    return await service.get_cities(
        active_only=True
    )


@router.get(
    "/cities/{city_id}/districts",
    response_model=list[DistrictResponse],
)
async def get_districts(
    city_id: uuid.UUID,
    service: LocationService = Depends(
        get_location_service
    ),
):
    try:
        return await service.get_districts_by_city(
            city_id=city_id,
            active_only=True,
        )
    except CityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Город не найден!",
        ) from None


@router.post(
    "/cities",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_city(
    data: CityCreate,
    _: User = Depends(
        get_current_admin
    ),
    service: LocationService = Depends(
        get_location_service
    ),
):
    try:
        return await service.create_city(
            data
        )
    except CityAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой город уже существует!",
        ) from None


@router.patch(
    "/cities/{city_id}",
    response_model=CityResponse,
)
async def update_city(
    city_id: uuid.UUID,
    data: CityUpdate,
    _: User = Depends(
        get_current_admin
    ),
    service: LocationService = Depends(
        get_location_service
    ),
):
    try:
        return await service.update_city(
            city_id=city_id,
            data=data,
        )
    except CityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Город не найден!",
        ) from None
    except CityAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой город уже существует!",
        ) from None


@router.post(
    "/districts",
    response_model=DistrictResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_district(
    data: DistrictCreate,
    _: User = Depends(
        get_current_admin
    ),
    service: LocationService = Depends(
        get_location_service
    ),
):
    try:
        return await service.create_district(
            data
        )
    except CityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Город не найден!",
        ) from None
    except DistrictAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой район уже существует в этом городе!",
        ) from None


@router.patch(
    "/districts/{district_id}",
    response_model=DistrictResponse,
)
async def update_district(
    district_id: uuid.UUID,
    data: DistrictUpdate,
    _: User = Depends(
        get_current_admin
    ),
    service: LocationService = Depends(
        get_location_service
    ),
):
    try:
        return await service.update_district(
            district_id=district_id,
            data=data,
        )
    except DistrictNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Район не найден!",
        ) from None
    except DistrictAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такой район уже существует в этом городе!",
        ) from None