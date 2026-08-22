from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import (
    get_password_reset_service,
)
from src.auth.exceptions import (
    InvalidPasswordResetTokenError,
)
from src.auth.password_reset_service import (
    PasswordResetService,
)
from src.auth.schemas import (
    ForgotPasswordRequest,
    PasswordResetMessage,
    ResetPasswordRequest,
)
from src.auth.token import create_access_token
from src.users.dependencies import get_user_service
from src.users.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
)
from src.users.schemas import (
    TokenResponse,
    UserRegister,
    UserResponse,
)
from src.users.service import UserService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    data: UserRegister,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    try:
        return await service.register_user(
            data
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует!",
        ) from None


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(
        get_user_service
    ),
) -> TokenResponse:
    try:
        user = await service.authenticate_user(
            email=form_data.username,
            password=form_data.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль!",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from None
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт пользователя отключён!",
        ) from None

    access_token = create_access_token(
        user_id=user.id
    )

    return TokenResponse(
        access_token=access_token
    )

@router.post(
    "/forgot-password",
    response_model=PasswordResetMessage,
)
async def forgot_password(
    data: ForgotPasswordRequest,
    service: PasswordResetService = Depends(
        get_password_reset_service
    ),
) -> PasswordResetMessage:
    await service.request_password_reset(
        str(data.email)
    )

    return PasswordResetMessage(
        message=(
            "Если аккаунт с таким email существует, "
            "письмо для восстановления пароля отправлено."
        )
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetMessage,
)
async def reset_password(
    data: ResetPasswordRequest,
    service: PasswordResetService = Depends(
        get_password_reset_service
    ),
) -> PasswordResetMessage:
    try:
        await service.reset_password(
            token=data.token,
            new_password=data.new_password,
        )
    except InvalidPasswordResetTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Токен восстановления пароля "
                "недействителен или истёк."
            ),
        ) from None

    return PasswordResetMessage(
        message="Пароль успешно изменён."
    )