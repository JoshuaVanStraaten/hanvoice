"""API router assembly. Feature routers register here."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.usage import router as usage_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(me_router)
api_router.include_router(usage_router)
