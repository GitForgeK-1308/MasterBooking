import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

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
from src.users.service import UserService


@pytest.fixture
def user_repository() -> AsyncMock:
    return AsyncMock(
        spec=UserRepository
    )


@pytest.fixture
def master_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterRepository
    )


@pytest.fixture
def user_service(
    user_repository: AsyncMock,
    master_repository: AsyncMock,
) -> UserService:
    return UserService(
        repository=user_repository,
        master_repository=master_repository,
    )


def make_user(
    *,
    is_active: bool = True,
) -> User:
    return User(
        id=uuid.uuid4(),
        email="user@example.com",
        hashed_password="hashed-password",
        first_name="Ivan",
        last_name="Ivanov",
        phone="+79991234567",
        is_active=is_active,
    )


@pytest.mark.anyio
async def test_get_user_by_id(
    user_service: UserService,
    user_repository: AsyncMock,
):
    user = make_user()

    user_repository.get_by_id.return_value = user

    result = await user_service.get_user_by_id(
        user.id
    )

    assert result is user

    user_repository.get_by_id.assert_awaited_once_with(
        user.id
    )


@pytest.mark.anyio
async def test_get_user_by_id_not_found(
    user_service: UserService,
    user_repository: AsyncMock,
):
    user_id = uuid.uuid4()

    user_repository.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await user_service.get_user_by_id(
            user_id
        )

    user_repository.get_by_id.assert_awaited_once_with(
        user_id
    )


@pytest.mark.anyio
async def test_register_user(
    user_service: UserService,
    user_repository: AsyncMock,
):
    data = UserRegister(
        email="USER@example.com",
        password="StrongPassword123!",
        first_name="Ivan",
        last_name="Ivanov",
        phone="+79991234567",
    )

    user_repository.get_by_email.return_value = None

    async def return_created_user(
        user: User,
    ) -> User:
        return user

    user_repository.create.side_effect = (
        return_created_user
    )

    with patch(
        "src.users.service.hash_password",
        return_value="hashed-password",
    ) as hash_password_mock:
        result = await user_service.register_user(
            data
        )

    assert result.email == "user@example.com"
    assert result.hashed_password == "hashed-password"
    assert result.first_name == "Ivan"
    assert result.last_name == "Ivanov"
    assert result.phone == "+79991234567"

    user_repository.get_by_email.assert_awaited_once_with(
        "user@example.com"
    )

    hash_password_mock.assert_called_once_with(
        "StrongPassword123!"
    )

    user_repository.create.assert_awaited_once()

    created_user = (
        user_repository.create.await_args.args[0]
    )

    assert created_user is result


@pytest.mark.anyio
async def test_register_user_duplicate_email(
    user_service: UserService,
    user_repository: AsyncMock,
):
    existing_user = make_user()

    user_repository.get_by_email.return_value = (
        existing_user
    )

    data = UserRegister(
        email="USER@example.com",
        password="StrongPassword123!",
        first_name="Ivan",
        last_name="Ivanov",
    )

    with pytest.raises(
        EmailAlreadyExistsError
    ):
        await user_service.register_user(
            data
        )

    user_repository.get_by_email.assert_awaited_once_with(
        "user@example.com"
    )

    user_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_authenticate_user(
    user_service: UserService,
    user_repository: AsyncMock,
):
    user = make_user()

    user_repository.get_by_email.return_value = user

    with patch(
        "src.users.service.verify_password",
        return_value=True,
    ) as verify_password_mock:
        result = await user_service.authenticate_user(
            email=" USER@EXAMPLE.COM ",
            password="StrongPassword123!",
        )

    assert result is user

    user_repository.get_by_email.assert_awaited_once_with(
        "user@example.com"
    )

    verify_password_mock.assert_called_once_with(
        plain_password="StrongPassword123!",
        hashed_password=user.hashed_password,
    )


@pytest.mark.anyio
async def test_authenticate_user_not_found(
    user_service: UserService,
    user_repository: AsyncMock,
):
    user_repository.get_by_email.return_value = None

    with pytest.raises(
        InvalidCredentialsError
    ):
        await user_service.authenticate_user(
            email="missing@example.com",
            password="StrongPassword123!",
        )

    user_repository.get_by_email.assert_awaited_once_with(
        "missing@example.com"
    )


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(
    user_service: UserService,
    user_repository: AsyncMock,
):
    user = make_user()

    user_repository.get_by_email.return_value = user

    with patch(
        "src.users.service.verify_password",
        return_value=False,
    ):
        with pytest.raises(
            InvalidCredentialsError
        ):
            await user_service.authenticate_user(
                email=user.email,
                password="WrongPassword123!",
            )


@pytest.mark.anyio
async def test_authenticate_inactive_user(
    user_service: UserService,
    user_repository: AsyncMock,
):
    user = make_user(
        is_active=False
    )

    user_repository.get_by_email.return_value = user

    with patch(
        "src.users.service.verify_password",
        return_value=True,
    ):
        with pytest.raises(
            InactiveUserError
        ):
            await user_service.authenticate_user(
                email=user.email,
                password="StrongPassword123!",
            )


@pytest.mark.anyio
async def test_update_profile(
    user_service: UserService,
    user_repository: AsyncMock,
    master_repository: AsyncMock,
):
    user = make_user()

    master = SimpleNamespace(
        first_name="Ivan",
        last_name="Ivanov",
    )

    master_repository.get_by_user_id.return_value = (
        master
    )

    async def return_updated_user(
        user: User,
    ) -> User:
        return user

    user_repository.update.side_effect = (
        return_updated_user
    )

    data = UserProfileUpdate(
        first_name="Petr",
        last_name="Petrov",
        phone="+79990000000",
    )

    result = await user_service.update_profile(
        user=user,
        data=data,
    )

    assert result is user

    assert user.first_name == "Petr"
    assert user.last_name == "Petrov"
    assert user.phone == "+79990000000"

    assert master.first_name == "Petr"
    assert master.last_name == "Petrov"

    master_repository.get_by_user_id.assert_awaited_once_with(
        user.id
    )

    user_repository.update.assert_awaited_once_with(
        user
    )


@pytest.mark.anyio
async def test_update_profile_without_master(
    user_service: UserService,
    user_repository: AsyncMock,
    master_repository: AsyncMock,
):
    user = make_user()

    master_repository.get_by_user_id.return_value = (
        None
    )

    async def return_updated_user(
        user: User,
    ) -> User:
        return user

    user_repository.update.side_effect = (
        return_updated_user
    )

    data = UserProfileUpdate(
        first_name="Petr",
    )

    result = await user_service.update_profile(
        user=user,
        data=data,
    )

    assert result.first_name == "Petr"
    assert result.last_name == "Ivanov"

    master_repository.get_by_user_id.assert_awaited_once_with(
        user.id
    )

    user_repository.update.assert_awaited_once_with(
        user
    )


@pytest.mark.anyio
async def test_update_profile_clear_phone(
    user_service: UserService,
    user_repository: AsyncMock,
    master_repository: AsyncMock,
):
    user = make_user()

    master_repository.get_by_user_id.return_value = (
        None
    )

    async def return_updated_user(
        user: User,
    ) -> User:
        return user

    user_repository.update.side_effect = (
        return_updated_user
    )

    data = UserProfileUpdate(
        phone=None,
    )

    result = await user_service.update_profile(
        user=user,
        data=data,
    )

    assert result.phone is None

    user_repository.update.assert_awaited_once_with(
        user
    )