"""Application factory.

``create_app()`` wires settings, logging, middleware, error handlers, and
routers. A single shared ``httpx.AsyncClient`` is created per process in the
lifespan and reused by the database client and every AI service client —
connection pooling matters when each conversation turn fans out to three
providers.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import RequestContextMiddleware, configure_logging
from app.db.client import Database


class AppState(TypedDict):
    http: httpx.AsyncClient
    db: Database
    settings: Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[AppState]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as http:
        db = Database(
            http=http,
            base_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
        )
        yield {"http": http, "db": db, "settings": settings}


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, json_logs=settings.is_production)

    app = FastAPI(
        title="HanVoice API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
