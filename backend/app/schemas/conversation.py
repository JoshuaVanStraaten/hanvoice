from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BaristaTurn(BaseModel):
    """The exact 4-key JSON contract from the approved scenario prompt."""

    model_config = ConfigDict(extra="forbid")

    ai_response_hangul: str
    ai_response_romanized: str
    ai_response_english: str
    contextual_correction: str = ""


class TokenUsage(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    hangul: str
    romanized: str | None = None
    english: str | None = None
    contextual_correction: str | None = None
    created_at: datetime


class ConversationSession(BaseModel):
    id: int
    scenario_id: int
    status: Literal["active", "completed", "abandoned"]
    goals_completed: list[str]
    started_at: datetime
    ended_at: datetime | None = None


class StartConversationRequest(BaseModel):
    scenario_slug: str


class StartConversationResponse(BaseModel):
    session: ConversationSession
    opening_message: ConversationMessage
    audio_base64: str | None = None


class TurnRequest(BaseModel):
    """A turn is either typed text or transcribed audio (audio sent as multipart)."""

    text: str | None = None


class TurnResponse(BaseModel):
    user_message: ConversationMessage
    assistant_message: ConversationMessage
    goals_completed: list[str]
    scenario_completed: bool
    audio_base64: str | None = None
