import uuid
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt
import pytest
from jwt.exceptions import InvalidTokenError

from src.auth.token import (
    create_access_token,
    decode_access_token,
)
from src.config import settings


def create_token(
    payload: dict,
    *,
    secret_key: str | None = None,
) -> str:
    return jwt.encode(
        payload,
        secret_key or settings.secret_key,
        algorithm=settings.algorithm,
    )


def test_create_and_decode_access_token():
    user_id = uuid.uuid4()

    token = create_access_token(
        user_id=user_id
    )

    result = decode_access_token(
        token
    )

    assert result == user_id


def test_access_token_contains_user_id_and_expiration():
    user_id = uuid.uuid4()

    token = create_access_token(
        user_id=user_id
    )

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[
            settings.algorithm
        ],
    )

    assert payload["sub"] == str(
        user_id
    )

    assert "exp" in payload


def test_decode_invalid_token():
    with pytest.raises(
        InvalidTokenError
    ):
        decode_access_token(
            "not-a-valid-token"
        )


def test_decode_token_without_sub():
    token = create_token(
        {
            "exp": (
                datetime.now(
                    timezone.utc
                )
                + timedelta(minutes=10)
            ),
        }
    )

    with pytest.raises(
        InvalidTokenError
    ):
        decode_access_token(
            token
        )


def test_decode_token_with_invalid_user_id():
    token = create_token(
        {
            "sub": "not-a-uuid",
            "exp": (
                datetime.now(
                    timezone.utc
                )
                + timedelta(minutes=10)
            ),
        }
    )

    with pytest.raises(
        InvalidTokenError
    ):
        decode_access_token(
            token
        )


def test_decode_expired_token():
    token = create_token(
        {
            "sub": str(
                uuid.uuid4()
            ),
            "exp": (
                datetime.now(
                    timezone.utc
                )
                - timedelta(minutes=1)
            ),
        }
    )

    with pytest.raises(
        InvalidTokenError
    ):
        decode_access_token(
            token
        )


def test_decode_token_with_wrong_secret():
    token = create_token(
        {
            "sub": str(
                uuid.uuid4()
            ),
            "exp": (
                datetime.now(
                    timezone.utc
                )
                + timedelta(minutes=10)
            ),
        },
        secret_key="wrong-secret-key-that-is-at-least-32-bytes-long",
    )

    with pytest.raises(
        InvalidTokenError
    ):
        decode_access_token(
            token
        )