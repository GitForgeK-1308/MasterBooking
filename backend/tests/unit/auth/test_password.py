from src.auth.password import (
    hash_password,
    verify_password,
)


def test_hash_password():
    password = "StrongPassword123!"

    hashed_password = hash_password(password)

    assert isinstance(
        hashed_password,
        str,
    )

    assert hashed_password != password

    assert (
        verify_password(
            plain_password=password,
            hashed_password=hashed_password,
        )
        is True
    )


def test_verify_wrong_password():
    hashed_password = hash_password("StrongPassword123!")

    result = verify_password(
        plain_password="WrongPassword123!",
        hashed_password=hashed_password,
    )

    assert result is False
