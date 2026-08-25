import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependencies import get_current_admin
from src.tags.dependencies import get_tag_service
from src.tags.exceptions import (
    TagAlreadyExistsError,
    TagInUseError,
    TagNotFoundError,
)
from src.tags.schemas import (
    TagCreate,
    TagResponse,
    TagUpdate,
)
from src.tags.service import TagService
from src.users.models import User

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


@router.get(
    "",
    response_model=list[TagResponse],
)
async def get_tags(
    service: TagService = Depends(get_tag_service),
):
    return await service.get_tags()


@router.get(
    "/admin",
    response_model=list[TagResponse],
)
async def get_all_tags(
    _: User = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
):
    return await service.get_all_tags()


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    data: TagCreate,
    _: User = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
):
    try:
        return await service.create_tag(data=data)
    except TagAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Тег с таким названием или slug уже существует!",
        ) from None


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
)
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    _: User = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
):
    try:
        return await service.update_tag(
            tag_id=tag_id,
            data=data,
        )
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден!",
        ) from None
    except TagAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Тег с таким названием или slug уже существует!",
        ) from None


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag(
    tag_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    service: TagService = Depends(get_tag_service),
) -> None:
    try:
        await service.delete_tag(tag_id=tag_id)

    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден!",
        ) from None

    except TagInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Тег используется услугами. Скройте его вместо удаления!"),
        ) from None
