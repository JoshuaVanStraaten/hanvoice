"""API router assembly. Feature routers register here."""

from fastapi import APIRouter

from app.api.routes.billing import router as billing_router
from app.api.routes.content import router as content_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.handwriting import router as handwriting_router
from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.progress import router as progress_router
from app.api.routes.pronunciation import router as pronunciation_router
from app.api.routes.usage import router as usage_router
from app.api.routes.waitlist import router as waitlist_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(me_router)
api_router.include_router(usage_router)
api_router.include_router(content_router)
api_router.include_router(pronunciation_router)
api_router.include_router(conversations_router)
api_router.include_router(handwriting_router)
api_router.include_router(progress_router)
api_router.include_router(waitlist_router)
api_router.include_router(billing_router)
