import time
import uuid

import jwt
import pytest

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token

SECRET = "test-jwt-secret-0123456789abcdef0123456789abcdef"
USER_ID = str(uuid.uuid4())


def make_token(
    *,
    secret: str = SECRET,
    sub: str = USER_ID,
    aud: str = "authenticated",
    exp_offset: int = 3600,
    email: str | None = "user@example.com",
) -> str:
    payload = {"sub": sub, "aud": aud, "exp": int(time.time()) + exp_offset}
    if email is not None:
        payload["email"] = email
    return jwt.encode(payload, secret, algorithm="HS256")


def test_valid_token_yields_user():
    user = decode_access_token(make_token(), SECRET)
    assert str(user.id) == USER_ID
    assert user.email == "user@example.com"


def test_token_without_email_is_fine():
    user = decode_access_token(make_token(email=None), SECRET)
    assert user.email is None


def test_expired_token_rejected():
    with pytest.raises(UnauthorizedError, match="expired"):
        decode_access_token(make_token(exp_offset=-10), SECRET)


def test_wrong_signature_rejected():
    with pytest.raises(UnauthorizedError):
        decode_access_token(make_token(secret="a" * 40), SECRET)


def test_wrong_audience_rejected():
    with pytest.raises(UnauthorizedError):
        decode_access_token(make_token(aud="anon"), SECRET)


def test_garbage_token_rejected():
    with pytest.raises(UnauthorizedError):
        decode_access_token("not-a-jwt", SECRET)


def test_non_uuid_subject_rejected():
    with pytest.raises(UnauthorizedError):
        decode_access_token(make_token(sub="admin"), SECRET)
