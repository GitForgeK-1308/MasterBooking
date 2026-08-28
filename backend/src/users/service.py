import uuid

from src.auth.password import hash_password, verify_password
from src.masters.repository import MasterRepository
from src.users.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import UserProfileUpdate, UserRegister


class UserService:
    def __init__(
        self,
        repository: UserRepository,
        master_repository: MasterRepository,
    ) -> None:
        self.repository = repository
        self.master_repository = master_repository

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User:
        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError

        return user

    async def register_user(
        self,
        data: UserRegister,
    ) -> User:
        normalized_email = str(data.email).strip().lower()

        existing_user = await self.repository.get_by_email(normalized_email)

        if existing_user is not None:
            raise EmailAlreadyExistsError

        hashed_password = hash_password(data.password)

        new_user = User(
            email=normalized_email,
            hashed_password=hashed_password,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
        )

        return await self.repository.create(new_user)

    async def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:
        normalized_email = email.strip().lower()

        user = await self.repository.get_by_email(normalized_email)

        if user is None:
            raise InvalidCredentialsError

        password_is_valid = verify_password(
            plain_password=password,
            hashed_password=user.hashed_password,
        )

        if not password_is_valid:
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveUserError

        return user

    async def update_profile(
        self,
        user: User,
        data: UserProfileUpdate,
    ) -> User:
        data_dict = data.model_dump(
            exclude_unset=True,
        )

        first_name = data_dict.get("first_name")
        last_name = data_dict.get("last_name")

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        if "phone" in data_dict:
            user.phone = data_dict["phone"]

        master = await self.master_repository.get_by_user_id(user.id)

        if master is not None:
            if first_name is not None:
                master.first_name = first_name

            if last_name is not None:
                master.last_name = last_name

        return await self.repository.update(user)
