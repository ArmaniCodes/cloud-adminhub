"""Focused unit tests for authentication and authorization helpers.

These tests intentionally use an in-memory SQLite URL only to allow application
modules that configure the SQLAlchemy engine at import time to load. The tests
below do not open a database connection or run database integration tests.
"""
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

# Set test-only configuration before importing app modules that read the
# environment during import. These values are local to the pytest process.
os.environ["SECRET_KEY"] = "test-only-secret-key-never-use-outside-tests"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import jwt
import pytest
from fastapi import HTTPException

from app.security.auth import require_role
from app.security.password import hash_password, verify_password
from app.security.token import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_refresh_token,
    secret_key,
)


def test_access_token_round_trip_preserves_user_id_and_role():
    token = create_access_token(user_id=42, user_role="admin")

    assert decode_access_token(token) == {"id": "42", "role": "admin"}


@pytest.mark.parametrize("token", ["not-a-jwt", "", "abc.def.ghi"])
def test_malformed_access_tokens_are_rejected(token):
    assert decode_access_token(token) is None


def test_expired_access_token_is_rejected():
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "sub": "42",
            "role": "admin",
            "iat": now - timedelta(minutes=5),
            "exp": now - timedelta(minutes=1),
        },
        secret_key,
        algorithm=ALGORITHM,
    )

    assert decode_access_token(expired_token) is None


def test_refresh_tokens_are_random_and_hashing_is_stable():
    token = create_refresh_token()
    other_token = create_refresh_token()

    assert token != other_token
    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != token
    assert len(hash_refresh_token(token)) == 64


def test_password_hash_verifies_only_the_original_password():
    raw_password = "sample-password-for-unit-tests-only"
    stored_hash = hash_password(raw_password)

    assert stored_hash != raw_password
    assert verify_password(raw_password, stored_hash)
    assert not verify_password("a-different-password", stored_hash)


def test_admin_role_is_allowed_for_admin_action():
    admin = SimpleNamespace(role="admin")
    checker = require_role("admin")

    assert checker(admin) is admin


def test_non_admin_role_is_forbidden_from_admin_action():
    support_user = SimpleNamespace(role="support")
    checker = require_role("admin")

    with pytest.raises(HTTPException) as exc_info:
        checker(support_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"
