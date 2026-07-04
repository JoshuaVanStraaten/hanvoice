import time
import uuid
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

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


# --- ES256 (new Supabase projects sign asymmetrically via JWKS) ---


def make_es256_setup(**token_kwargs):
    """An ES256-signed token plus a stub JWKS client that resolves its key."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    payload = {
        "sub": token_kwargs.get("sub", USER_ID),
        "aud": token_kwargs.get("aud", "authenticated"),
        "exp": int(time.time()) + token_kwargs.get("exp_offset", 3600),
        "email": "user@example.com",
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-key"})
    jwks_client = Mock(spec=jwt.PyJWKClient)
    jwks_client.get_signing_key_from_jwt.return_value = Mock(key=private_key.public_key())
    return token, jwks_client


def test_es256_token_verified_via_jwks():
    token, jwks_client = make_es256_setup()
    user = decode_access_token(token, SECRET, jwks_client=jwks_client)
    assert str(user.id) == USER_ID


def test_es256_expired_token_rejected():
    token, jwks_client = make_es256_setup(exp_offset=-10)
    with pytest.raises(UnauthorizedError, match="expired"):
        decode_access_token(token, SECRET, jwks_client=jwks_client)


def test_es256_wrong_key_rejected():
    token, _ = make_es256_setup()
    other_key = ec.generate_private_key(ec.SECP256R1())
    jwks_client = Mock(spec=jwt.PyJWKClient)
    jwks_client.get_signing_key_from_jwt.return_value = Mock(key=other_key.public_key())
    with pytest.raises(UnauthorizedError):
        decode_access_token(token, SECRET, jwks_client=jwks_client)


def test_es256_unknown_kid_rejected():
    token, jwks_client = make_es256_setup()
    jwks_client.get_signing_key_from_jwt.side_effect = jwt.PyJWKClientError("kid not found")
    with pytest.raises(UnauthorizedError):
        decode_access_token(token, SECRET, jwks_client=jwks_client)


def test_es256_token_without_jwks_client_rejected():
    # No JWKS configured → asymmetric tokens must not silently pass.
    token, _ = make_es256_setup()
    with pytest.raises(UnauthorizedError):
        decode_access_token(token, SECRET)
