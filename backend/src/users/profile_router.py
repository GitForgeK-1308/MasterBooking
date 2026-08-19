from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from src.auth.dependencies import get_current_user
from src.users.avatar_service import UserAvatarService
from src.users.dependencies import (
    get_user_avatar_service,
    get_user_service,
)
from src.users.exceptions import (
    AvatarTooLargeError,
    InvalidAvatarTypeError,
)
from src.users.models import User
from src.users.schemas import (
    UserAvatarResponse,
    UserProfileUpdate,
    UserResponse,
)
from src.users.service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_my_profile(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
)
async def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    service: UserService = Depends(
        get_user_service
    ),
) -> User:
    return await service.update_profile(
        user=current_user,
        data=data,
    )


@router.post(
    "/me/avatar",
    response_model=UserAvatarResponse,
)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user
    ),
    service: UserAvatarService = Depends(
        get_user_avatar_service
    ),
) -> UserAvatarResponse:
    try:
        user = await service.upload_avatar(
            user=current_user,
            file=file,
        )
    except AvatarTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Файл слишком большой. Максимальный размер — 5 МБ.",
        ) from None
    except InvalidAvatarTypeError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Разрешены только JPEG, PNG и WEBP.",
        ) from None

    return UserAvatarResponse(
        avatar_url=service.get_avatar_url(
            user.avatar_storage_key
        )
    )