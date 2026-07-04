"""Supabase JWT verification.

The frontend obtains an access token from Supabase Auth; every protected API
call carries it as a bearer token. Verification is local — no network hop to
Supabase per request:

- New Supabase projects sign tokens asymmetrically (ES256 with a ``kid``);
  we verify against the project's public JWKS, cached by ``PyJWKClient``.
- HS256 with the shared JWT secret remains supported for legacy projects,
  self-hosted setups, and tests.
"""

import uuid
from dataclasses import dataclass

import jwt

from app.core.errors import UnauthorizedError

_ASYMMETRIC_ALGS = ("ES256", "RS256")


@dataclass(frozen=True)
class AuthenticatedUser:
    id: uuid.UUID
    email: str | None


def decode_access_token(
    token: str,
    secret: str,
    jwks_client: jwt.PyJWKClient | None = None,
) -> AuthenticatedUser:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc

    alg = str(header.get("alg", "HS256"))
    try:
        if alg in _ASYMMETRIC_ALGS and jwks_client is not None:
            signing_key = jwks_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=list(_ASYMMETRIC_ALGS),
                audience="authenticated",
                options={"require": ["sub", "exp"]},
            )
        else:
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["sub", "exp"]},
            )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Session expired — please sign in again.") from exc
    except jwt.PyJWKClientError as exc:
        # Unknown kid or JWKS fetch failure — the token can't be trusted.
        raise UnauthorizedError("Invalid authentication token.") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc

    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc

    email = claims.get("email")
    return AuthenticatedUser(id=user_id, email=email if isinstance(email, str) else None)
