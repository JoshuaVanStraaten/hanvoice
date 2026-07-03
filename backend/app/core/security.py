"""Supabase JWT verification.

The frontend obtains an access token from Supabase Auth; every protected API
call carries it as a bearer token. We verify it locally (HS256 with the
project's JWT secret) — no network hop to Supabase per request.
"""

import uuid
from dataclasses import dataclass

import jwt

from app.core.errors import UnauthorizedError


@dataclass(frozen=True)
class AuthenticatedUser:
    id: uuid.UUID
    email: str | None


def decode_access_token(token: str, secret: str) -> AuthenticatedUser:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Session expired — please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc

    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise UnauthorizedError("Invalid authentication token.") from exc

    email = claims.get("email")
    return AuthenticatedUser(id=user_id, email=email if isinstance(email, str) else None)
