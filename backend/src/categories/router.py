import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependencies import get_current_admin
from src.categories.dependencies import get_category_service
from src.categories.exceptions import (
    CategoryAlreadyExistsError,
    CategoryHasChildrenError,
    CategoryInUseError,
    CategoryInvalidParentError,
    CategoryNotFoundError,
)
from src.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryUpdate,
)
from src.categories.service import CategoryService
from src.users.models import User

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.get(
    "",
    response_model=list[CategoryResponse],
)
async def get_categories(
    service: CategoryService = Depends(get_category_service),
):
    return await service.get_categories()


@router.get(
    "/admin",
    response_model=list[CategoryResponse],
)
async def get_all_categories(
    _: User = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    return await service.get_all_categories()


@router.get(
    "/tree",
    response_model=list[CategoryTreeResponse],
)
async def get_category_tree(
    service: CategoryService = Depends(get_category_service),
):
    return await service.get_category_tree()


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    data: CategoryCreate,
    _: User = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    try:
        return await service.create_category(data=data)
    except CategoryAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категория с таким названием или slug уже существует!",
        ) from None
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Родительская категория не найдена!",
        ) from None


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    _: User = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
):
    try:
        return await service.update_category(
            category_id=category_id,
            data=data,
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена!",
        ) from None
    except CategoryAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категория с таким названием или slug уже существует!",
        ) from None
    except CategoryInvalidParentError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя создать циклическую иерархию категорий!",
        ) from None


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_category(
    category_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    service: CategoryService = Depends(get_category_service),
) -> None:
    try:
        await service.delete_category(category_id=category_id)

    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена!",
        ) from None

    except CategoryHasChildrenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Нельзя удалить категорию, пока у неё есть подкатегории!"),
        ) from None

    except CategoryInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Категория используется услугами. Скройте её вместо удаления!"),
        ) from None
