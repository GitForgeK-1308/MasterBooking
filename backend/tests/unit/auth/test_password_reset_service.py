import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.auth.exceptions import (
    InvalidPasswordResetTokenError,
)
from src.auth.password_reset_service import (
    PasswordResetService,
)


@pytest.mark.anyio
async def test_request_password_reset():
    user_id = uuid.uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
        is_active=True,
    )

    user_repository = AsyncMock()
    user_repository.get_by_email = AsyncMock(return_value=user)

    redis_client = AsyncMock()
    redis_client.set = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    with patch(
        "src.auth.password_reset_service.send_password_reset_email.delay"
    ) as send_email:
        token = await service.request_password_reset("USER@example.com")

    assert token is not None

    user_repository.get_by_email.assert_awaited_once_with("user@example.com")

    redis_client.set.assert_awaited_once()

    send_email.assert_called_once_with(
        "user@example.com",
        token,
    )


@pytest.mark.anyio
async def test_request_password_reset_stores_hashed_token_with_ttl():
    user_id = uuid.uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
        is_active=True,
    )

    user_repository = AsyncMock()
    user_repository.get_by_email = AsyncMock(return_value=user)

    redis_client = AsyncMock()
    redis_client.set = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    with patch("src.auth.password_reset_service.send_password_reset_email.delay"):
        token = await service.request_password_reset("user@example.com")

    assert token is not None

    token_hash = service._hash_token(token)

    redis_client.set.assert_awaited_once_with(
        f"password_reset:{token_hash}",
        str(user_id),
        ex=900,
    )


@pytest.mark.anyio
async def test_request_password_reset_user_not_found():
    user_repository = AsyncMock()
    user_repository.get_by_email = AsyncMock(return_value=None)

    redis_client = AsyncMock()
    redis_client.set = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    token = await service.request_password_reset("unknown@example.com")

    assert token is None

    user_repository.get_by_email.assert_awaited_once_with("unknown@example.com")

    redis_client.set.assert_not_awaited()


@pytest.mark.anyio
async def test_request_password_reset_inactive_user():
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="user@example.com",
        is_active=False,
    )

    user_repository = AsyncMock()
    user_repository.get_by_email = AsyncMock(return_value=user)

    redis_client = AsyncMock()
    redis_client.set = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    token = await service.request_password_reset("user@example.com")

    assert token is None

    redis_client.set.assert_not_awaited()


@pytest.mark.anyio
async def test_reset_password():
    user_id = uuid.uuid4()

    user = SimpleNamespace(
        id=user_id,
        hashed_password="old-hash",
    )

    user_repository = AsyncMock()
    user_repository.get_by_id = AsyncMock(return_value=user)
    user_repository.update = AsyncMock(return_value=user)

    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=str(user_id))
    redis_client.delete = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    old_password_hash = user.hashed_password

    token = "test-reset-token"

    await service.reset_password(
        token=token,
        new_password="new-password-123",
    )

    assert user.hashed_password != old_password_hash

    user_repository.get_by_id.assert_awaited_once_with(user_id)

    user_repository.update.assert_awaited_once_with(user)

    token_hash = service._hash_token(token)

    redis_client.delete.assert_awaited_once_with(f"password_reset:{token_hash}")


@pytest.mark.anyio
async def test_reset_password_invalid_token():
    user_repository = AsyncMock()

    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)
    redis_client.delete = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    with pytest.raises(InvalidPasswordResetTokenError):
        await service.reset_password(
            token="invalid-token",
            new_password="new-password-123",
        )

    user_repository.get_by_id.assert_not_awaited()
    user_repository.update.assert_not_awaited()
    redis_client.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_reset_password_user_not_found():
    user_id = uuid.uuid4()

    user_repository = AsyncMock()
    user_repository.get_by_id = AsyncMock(return_value=None)

    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=str(user_id))
    redis_client.delete = AsyncMock()

    service = PasswordResetService(
        user_repository=user_repository,
        redis_client=redis_client,
    )

    with pytest.raises(InvalidPasswordResetTokenError):
        await service.reset_password(
            token="valid-looking-token",
            new_password="new-password-123",
        )

    user_repository.get_by_id.assert_awaited_once_with(user_id)

    user_repository.update.assert_not_awaited()
    redis_client.delete.assert_not_awaited()
