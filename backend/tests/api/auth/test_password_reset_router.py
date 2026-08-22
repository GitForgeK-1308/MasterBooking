from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from src.auth.dependencies import (
    get_password_reset_service,
)
from src.auth.exceptions import (
    InvalidPasswordResetTokenError,
)
from src.main import app


@pytest.mark.anyio
async def test_forgot_password(
    ac: AsyncClient,
):
    service = AsyncMock()
    service.request_password_reset = AsyncMock(
        return_value="reset-token"
    )

    app.dependency_overrides[
        get_password_reset_service
    ] = lambda: service

    try:
        response = await ac.post(
            "/auth/forgot-password",
            json={
                "email": "USER@example.com",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_password_reset_service,
            None,
        )

    assert response.status_code == 200

    assert response.json() == {
        "message": (
            "Если аккаунт с таким email существует, "
            "письмо для восстановления пароля отправлено."
        )
    }

    service.request_password_reset.assert_awaited_once_with(
        "USER@example.com"
    )


@pytest.mark.anyio
async def test_forgot_password_user_not_found(
    ac: AsyncClient,
):
    service = AsyncMock()
    service.request_password_reset = AsyncMock(
        return_value=None
    )

    app.dependency_overrides[
        get_password_reset_service
    ] = lambda: service

    try:
        response = await ac.post(
            "/auth/forgot-password",
            json={
                "email": "unknown@example.com",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_password_reset_service,
            None,
        )

    assert response.status_code == 200

    assert response.json() == {
        "message": (
            "Если аккаунт с таким email существует, "
            "письмо для восстановления пароля отправлено."
        )
    }

    service.request_password_reset.assert_awaited_once_with(
        "unknown@example.com"
    )


@pytest.mark.anyio
async def test_reset_password(
    ac: AsyncClient,
):
    service = AsyncMock()
    service.reset_password = AsyncMock(
        return_value=None
    )

    app.dependency_overrides[
        get_password_reset_service
    ] = lambda: service

    try:
        response = await ac.post(
            "/auth/reset-password",
            json={
                "token": "a" * 32,
                "new_password": "new-password-123",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_password_reset_service,
            None,
        )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Пароль успешно изменён."
    }

    service.reset_password.assert_awaited_once_with(
        token="a" * 32,
        new_password="new-password-123",
    )


@pytest.mark.anyio
async def test_reset_password_invalid_token(
    ac: AsyncClient,
):
    service = AsyncMock()
    service.reset_password = AsyncMock(
        side_effect=InvalidPasswordResetTokenError
    )

    app.dependency_overrides[
        get_password_reset_service
    ] = lambda: service

    try:
        response = await ac.post(
            "/auth/reset-password",
            json={
                "token": "a" * 32,
                "new_password": "new-password-123",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_password_reset_service,
            None,
        )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Токен восстановления пароля "
            "недействителен или истёк."
        )
    }