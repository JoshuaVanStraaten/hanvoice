from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.api.deps import Conversations, CurrentUser, Db
from app.core.ratelimit import rate_limit
from app.schemas.conversation import (
    ConversationMessage,
    ConversationSession,
    StartConversationRequest,
    StartConversationResponse,
    TurnResponse,
)
from app.services.entitlements import resolve_plan

router = APIRouter(tags=["conversations"])


class ConversationDetailResponse(BaseModel):
    session: ConversationSession
    messages: list[ConversationMessage]


@router.post(
    "/conversations",
    response_model=StartConversationResponse,
    dependencies=[Depends(rate_limit(max_requests=6, window_seconds=60))],
)
async def start_conversation(
    body: StartConversationRequest,
    user: CurrentUser,
    db: Db,
    service: Conversations,
) -> StartConversationResponse:
    plan = await resolve_plan(db, user.id)
    return await service.start(user.id, body.scenario_slug, plan)


@router.post(
    "/conversations/{session_id}/turns",
    response_model=TurnResponse,
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
async def take_turn(
    session_id: int,
    user: CurrentUser,
    db: Db,
    service: Conversations,
    audio: Annotated[UploadFile | None, File()] = None,
    text: Annotated[str | None, Form(max_length=500)] = None,
) -> TurnResponse:
    plan = await resolve_plan(db, user.id)
    audio_bytes = await audio.read() if audio is not None else None
    content_type = (audio.content_type or "audio/webm").split(";")[0] if audio else "audio/webm"
    return await service.take_turn(
        user.id,
        session_id,
        plan,
        text=text,
        audio=audio_bytes,
        audio_content_type=content_type,
    )


@router.post("/conversations/{session_id}/complete", response_model=ConversationSession)
async def complete_conversation(
    session_id: int, user: CurrentUser, service: Conversations
) -> ConversationSession:
    return await service.end(user.id, session_id)


@router.get("/conversations/{session_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    session_id: int, user: CurrentUser, service: Conversations
) -> ConversationDetailResponse:
    session, messages = await service.get_with_messages(user.id, session_id)
    return ConversationDetailResponse(session=session, messages=messages)
