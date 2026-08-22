from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password_reset_service import PasswordResetService
from src.auth.token import decode_access_token
from src.database.session import get_async_session
from src.masters.models import Master
from src.masters.repository import MasterRepository
from src.redis.dependencies import get_redis
from src.users.dependencies import get_user_service
from src.users.exceptions import UserNotFoundError
from src.users.models import User, UserRole
from src.users.repository import UserRepository
from src.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(
        get_user_service
    ),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить пользователя!",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        user_id = decode_access_token(
            token
        )
    except InvalidTokenError:
        raise credentials_exception from None

    try:
        user = await service.get_user_by_id(
            user_id
        )
    except UserNotFoundError:
        raise credentials_exception from None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт пользователя отключён!",
        )

    return user


async def get_current_client(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только клиентам!",
        )

    return current_user


async def get_current_master_user(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только мастерам!",
        )

    return current_user


async def get_current_admin(
    current_user: User = Depends(
        get_current_user
    ),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только администраторам!",
        )

    return current_user


async def get_current_master_profile(
    current_user: User = Depends(
        get_current_master_user
    ),
    session: AsyncSession = Depends(
        get_async_session
    ),
) -> Master:
    repository = MasterRepository(
        session
    )

    master = await repository.get_by_user_id(
        current_user.id
    )

    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль мастера не найден!",
        )

    return master

def get_password_reset_service(
    session: AsyncSession = Depends(
        get_async_session
    ),
    redis: Redis = Depends(
        get_redis
    ),
) -> PasswordResetService:
    user_repository = UserRepository(
        session
    )

    return PasswordResetService(
        user_repository=user_repository,
        redis_client=redis,
    )