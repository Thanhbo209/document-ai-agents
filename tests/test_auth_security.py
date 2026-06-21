from datetime import timedelta

import pytest

from app.auth.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    password_hash = hash_password("secret-password")

    assert password_hash != "secret-password"
    assert verify_password("secret-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_round_trip() -> None:
    token = create_access_token(
        user_id="user-1",
        email="user@example.com",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user-1"
    assert payload["email"] == "user@example.com"
    assert payload["type"] == "access"


def test_expired_token_is_rejected() -> None:
    token = create_access_token(
        user_id="user-1",
        email="user@example.com",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
