import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from src.auth.dependencies import (
    get_current_master_profile,
)
from src.master_offering.exceptions import (
    OfferingNotFoundError,
)
from src.masters.models import Master
from src.offering_images.dependencies import (
    get_offering_image_service,
)
from src.offering_images.exceptions import (
    InvalidOfferingImageTypeError,
    OfferingImageAccessDeniedError,
    OfferingImageLimitExceededError,
    OfferingImageNotFoundError,
    OfferingImageTooLargeError,
)
from src.offering_images.models import OfferingImage
from src.offering_images.schemas import (
    OfferingImageResponse,
)
from src.offering_images.service import (
    OfferingImageService,
)

router = APIRouter(
    prefix="/offerings",
    tags=["Offering Images"],
)


def _to_response(
    image: OfferingImage,
    service: OfferingImageService,
) -> OfferingImageResponse:
    return OfferingImageResponse(
        id=image.id,
        offering_id=image.offering_id,
        image_url=service.get_image_url(
            image.storage_key
        ),
        is_primary=image.is_primary,
        sort_order=image.sort_order,
        created_at=image.created_at,
    )


@router.post(
    "/{offering_id}/images",
    response_model=OfferingImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_offering_image(
    offering_id: uuid.UUID,
    file: UploadFile = File(...),
    current_master: Master = Depends(
        get_current_master_profile
    ),
    service: OfferingImageService = Depends(
        get_offering_image_service
    ),
):
    try:
        image = await service.upload_image(
            offering_id=offering_id,
            master_id=current_master.id,
            file=file,
        )

        return _to_response(
            image=image,
            service=service,
        )

    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None

    except OfferingImageAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Вы не можете загружать фотографии "
                "для чужой услуги!"
            ),
        ) from None

    except OfferingImageLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Для одной услуги можно загрузить "
                "не более 20 фотографий!"
            ),
        ) from None

    except OfferingImageTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                "Размер фотографии не должен "
                "превышать 5 MB!"
            ),
        ) from None

    except InvalidOfferingImageTypeError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Разрешены только JPEG, PNG "
                "и WEBP изображения!"
            ),
        ) from None


@router.get(
    "/{offering_id}/images",
    response_model=list[OfferingImageResponse],
)
async def get_offering_images(
    offering_id: uuid.UUID,
    service: OfferingImageService = Depends(
        get_offering_image_service
    ),
):
    try:
        images = await service.get_offering_images(
            offering_id=offering_id
        )

        return [
            _to_response(
                image=image,
                service=service,
            )
            for image in images
        ]

    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None


@router.patch(
    "/{offering_id}/images/{image_id}/primary",
    response_model=OfferingImageResponse,
)
async def set_primary_image(
    offering_id: uuid.UUID,
    image_id: uuid.UUID,
    current_master: Master = Depends(
        get_current_master_profile
    ),
    service: OfferingImageService = Depends(
        get_offering_image_service
    ),
):
    try:
        image = await service.set_primary_image(
            offering_id=offering_id,
            image_id=image_id,
            master_id=current_master.id,
        )

        return _to_response(
            image=image,
            service=service,
        )

    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None

    except OfferingImageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена!",
        ) from None

    except OfferingImageAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Вы не можете изменять фотографии "
                "чужой услуги!"
            ),
        ) from None


@router.delete(
    "/{offering_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_offering_image(
    offering_id: uuid.UUID,
    image_id: uuid.UUID,
    current_master: Master = Depends(
        get_current_master_profile
    ),
    service: OfferingImageService = Depends(
        get_offering_image_service
    ),
) -> None:
    try:
        await service.delete_image(
            offering_id=offering_id,
            image_id=image_id,
            master_id=current_master.id,
        )

    except OfferingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Услуга не найдена!",
        ) from None

    except OfferingImageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена!",
        ) from None

    except OfferingImageAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Вы не можете удалять фотографии "
                "чужой услуги!"
            ),
        ) from None