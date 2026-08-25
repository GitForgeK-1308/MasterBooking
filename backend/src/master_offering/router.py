import uuid
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from src.auth.dependencies import get_current_master_profile
from src.categories.exceptions import (
    CategoryInactiveError,
    CategoryNotFoundError,
)
from src.master_offering.dependencies import (
    get_offering_service,
)
from src.master_offering.exceptions import (
    OfferingAccessDeniedError,
    OfferingNotFoundError,
)
from src.master_offering.schemas import (
    MasterOfferingCreate,
    MasterOfferingPage,
    MasterOfferingResponse,
    MasterOfferingUpdate,
    OfferingSort,
)
from src.master_offering.service import (
    MasterOfferingService,
)
from src.masters.models import Master
from src.tags.exceptions import (
    TagInactiveError,
    TagNotFoundError,
)

router = APIRouter(tags=["Offerings"])


@router.post(
    "/masters/me/offerings",
    response_model=MasterOfferingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offering(
    data: MasterOfferingCreate,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterOfferingService = Depends(get_offering_service),
):
    try:
        return await service.create_offering(
            master_id=current_master.id,
            data=data,
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена!",
        ) from None
    except CategoryInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Выбранная категория недоступна!",
        ) from None
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Один или несколько тегов не найдены!",
        ) from None
    except TagInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Один или несколько тегов неактивны!",
        ) from None


@router.get(
    "/masters/me/offerings",
    response_model=list[MasterOfferingResponse],
)
async def get_my_offerings(
    current_master: Master = Depends(get_current_master_profile),
    service: MasterOfferingService = Depends(get_offering_service),
):
    return await service.get_master_offerings(
        master_id=current_master.id,
        active_only=False,
    )


@router.get(
    "/masters/{master_id}/offerings",
    response_model=list[MasterOfferingResponse],
)
async def get_master_offerings(
    master_id: uuid.UUID,
    service: MasterOfferingService = Depends(get_offering_service),
):
    return await service.get_master_offerings(
        master_id=master_id,
        active_only=True,
    )


@router.get(
    "/offerings",
    response_model=MasterOfferingPage,
)
async def get_public_offerings(
    category_id: uuid.UUID | None = None,
    min_price: Decimal | None = Query(
        default=None,
        gt=0,
    ),
    max_price: Decimal | None = Query(
        default=None,
        gt=0,
    ),
    discounted_only: bool = Query(
        default=False,
    ),
    sort: OfferingSort | None = None,
    search: str | None = Query(
        default=None,
        min_length=2,
        max_length=100,
    ),
    city_id: uuid.UUID | None = None,
    district_id: uuid.UUID | None = None,
    exclude_master_id: uuid.UUID | None = None,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=12,
        ge=1,
        le=50,
    ),
    service: MasterOfferingService = Depends(get_offering_service),
):
    return await service.get_public_offerings(
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        discounted_only=discounted_only,
        sort=sort,
        search=search,
        city_id=city_id,
        district_id=district_id,
        exclude_master_id=exclude_master_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/offerings/{offering_id}",
    response_model=MasterOfferingResponse,
)
async def get_offering_by_id(
    offering_id: uuid.UUID,
    service: MasterOfferingService = Depends(get_offering_service),
):
    try:
        return await service.get_public_offering_by_id(offering_id)
    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None


@router.patch(
    "/offerings/{offering_id}",
    response_model=MasterOfferingResponse,
)
async def patch_offering(
    offering_id: uuid.UUID,
    data: MasterOfferingUpdate,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterOfferingService = Depends(get_offering_service),
):
    try:
        return await service.update_offering(
            offering_id=offering_id,
            master_id=current_master.id,
            data=data,
        )
    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена!",
        ) from None
    except CategoryInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Выбранная категория недоступна!",
        ) from None
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Один или несколько тегов не найдены!",
        ) from None
    except TagInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Один или несколько тегов неактивны!",
        ) from None
    except OfferingAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете изменять чужую услугу!",
        ) from None


@router.delete(
    "/offerings/{offering_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_offering(
    offering_id: uuid.UUID,
    current_master: Master = Depends(get_current_master_profile),
    service: MasterOfferingService = Depends(get_offering_service),
) -> None:
    try:
        await service.delete_offering(
            offering_id=offering_id,
            master_id=current_master.id,
        )
    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None
    except OfferingAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете удалять чужую услугу!",
        ) from None
