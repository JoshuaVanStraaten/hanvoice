"""Shared FastAPI dependencies.

``Db`` and ``CurrentUser`` are the two building blocks every protected route
uses. The database and settings live in lifespan state (one instance per
process); the user is decoded from the bearer token per request.
"""

from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.core.security import AuthenticatedUser, decode_access_token
from app.db.client import Database


def get_db(request: Request) -> Database:
    db: Database = request.state.db
    return db


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.state.settings
    return settings


def get_http(request: Request) -> httpx.AsyncClient:
    http: httpx.AsyncClient = request.state.http
    return http


def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthenticatedUser:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthorizedError("Missing bearer token.")
    return decode_access_token(token.strip(), settings.supabase_jwt_secret)


Db = Annotated[Database, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Http = Annotated[httpx.AsyncClient, Depends(get_http)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
