"""Shared FastAPI dependencies.

``Db`` and ``CurrentUser`` are the two building blocks every protected route
uses. The database and settings live in lifespan state (one instance per
process); the user is decoded from the bearer token per request.
"""

from typing import Annotated

import httpx
import jwt
from fastapi import Depends, Request

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.core.security import AuthenticatedUser, decode_access_token
from app.db.client import Database
from app.services.ai.azure_pronunciation import AzurePronunciationClient
from app.services.ai.azure_stt import AzureSTTClient
from app.services.ai.llama_chat import LlamaChatClient
from app.services.ai.nemotron_vision import NemotronVisionClient
from app.services.ai.tts import TTSClient
from app.services.billing import BillingService
from app.services.conversation import ConversationService


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
    jwks: jwt.PyJWKClient = request.state.jwks
    return decode_access_token(token.strip(), settings.supabase_jwt_secret, jwks_client=jwks)


def get_azure_client(request: Request) -> AzurePronunciationClient:
    settings: Settings = request.state.settings
    return AzurePronunciationClient(
        request.state.http, key=settings.azure_speech_key, region=settings.azure_speech_region
    )


def get_vision_client(request: Request) -> NemotronVisionClient:
    settings: Settings = request.state.settings
    return NemotronVisionClient(
        request.state.http,
        api_key=settings.nvidia_api_key,
        url=settings.nvidia_vision_url,
        model=settings.nvidia_vision_model,
    )


def get_tts_client(request: Request) -> TTSClient:
    settings: Settings = request.state.settings
    return TTSClient(
        request.state.http,
        key=settings.azure_speech_key,
        region=settings.azure_speech_region,
        voice=settings.azure_tts_voice,
    )


def get_conversation_service(request: Request) -> ConversationService:
    settings: Settings = request.state.settings
    http = request.state.http
    return ConversationService(
        db=request.state.db,
        llama=LlamaChatClient(
            http,
            api_key=settings.nvidia_api_key,
            url=settings.nvidia_llm_url,
            model=settings.nvidia_llm_model,
        ),
        asr=AzureSTTClient(
            http, key=settings.azure_speech_key, region=settings.azure_speech_region
        ),
        tts=TTSClient(
            http,
            key=settings.azure_speech_key,
            region=settings.azure_speech_region,
            voice=settings.azure_tts_voice,
        ),
    )


def get_billing_service(request: Request) -> BillingService:
    return BillingService(request.state.settings)


Db = Annotated[Database, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Http = Annotated[httpx.AsyncClient, Depends(get_http)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
AzureClient = Annotated[AzurePronunciationClient, Depends(get_azure_client)]
Tts = Annotated[TTSClient, Depends(get_tts_client)]
VisionClient = Annotated[NemotronVisionClient, Depends(get_vision_client)]
Conversations = Annotated[ConversationService, Depends(get_conversation_service)]
Billing = Annotated[BillingService, Depends(get_billing_service)]
