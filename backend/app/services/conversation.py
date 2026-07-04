"""Conversation engine — orchestrates one scenario session end to end.

Pipeline per turn: (ASR if audio) → quota gate → Llama (strict JSON contract)
→ goal detection (backend, keyword-based) → persist both turns → TTS
(best-effort) → meter usage. TTS failures never fail a turn: the learner can
read the reply even when audio synthesis is down.
"""

import base64
from datetime import UTC, datetime
from uuid import UUID

import structlog

from app.core.errors import BadRequestError, ConflictError
from app.db.client import Database, JsonRow
from app.db.repositories import content, conversations
from app.db.repositories import usage as usage_repo
from app.schemas.conversation import (
    BaristaTurn,
    ChatMessage,
    ConversationMessage,
    ConversationSession,
    StartConversationResponse,
    TokenUsage,
    TurnResponse,
)
from app.schemas.plans import Plan
from app.services import goals as goals_service
from app.services import progress as progress_service
from app.services.ai.azure_stt import AzureSTTClient
from app.services.ai.base import AIServiceError
from app.services.ai.llama_chat import LlamaChatClient
from app.services.ai.tts import TTSClient
from app.services.quota import Metric, ensure_within_quota

logger = structlog.get_logger(__name__)

# Rough mp3 bytes→seconds for metering TTS spend (128 kbps ≈ 16 kB/s).
_MP3_BYTES_PER_SECOND = 16_000


class ConversationService:
    def __init__(
        self,
        db: Database,
        llama: LlamaChatClient,
        asr: AzureSTTClient,
        tts: TTSClient,
    ):
        self._db = db
        self._llama = llama
        self._asr = asr
        self._tts = tts

    async def start(
        self, user_id: UUID, scenario_slug: str, plan: Plan
    ) -> StartConversationResponse:
        scenario = await content.get_published_scenario(self._db, scenario_slug)
        prompt = await content.get_active_prompt(self._db, int(scenario["id"]))
        await self._ensure_turn_quota(user_id, plan)

        turn, tokens = await self._llama.next_turn(str(prompt["system_prompt"]), [])
        session = await conversations.create_session(self._db, user_id, int(scenario["id"]))
        message = await self._store_assistant_turn(int(session["id"]), turn)

        audio_base64, tts_seconds = await self._synthesize(turn.ai_response_hangul)
        await self._meter(user_id, tokens, tts_seconds)

        return StartConversationResponse(
            session=_session_model(session),
            opening_message=_message_model(message),
            audio_base64=audio_base64,
        )

    async def take_turn(
        self,
        user_id: UUID,
        session_id: int,
        plan: Plan,
        *,
        text: str | None,
        audio: bytes | None,
        audio_content_type: str = "audio/webm",
    ) -> TurnResponse:
        session = await conversations.get_own_session(self._db, user_id, session_id)
        if session["status"] != "active":
            raise ConflictError("This conversation has already ended.")

        scenario = await content.get_scenario_by_id(self._db, int(session["scenario_id"]))
        prompt = await content.get_active_prompt(self._db, int(scenario["id"]))
        await self._ensure_turn_quota(user_id, plan)

        if audio is not None:
            user_text = await self._asr.transcribe(audio, audio_content_type)
        else:
            user_text = (text or "").strip()
        if not user_text:
            raise BadRequestError("Say (or type) something first — even just 안녕하세요!")

        history = await self._build_history(session_id)
        history.append(ChatMessage(role="user", content=user_text))
        turn, tokens = await self._llama.next_turn(str(prompt["system_prompt"]), history)

        scenario_goals = [str(g) for g in scenario["completion_goals"]]
        already = [str(g) for g in session["goals_completed"]]
        merged = goals_service.merge_goals(
            already, goals_service.detect_goals(user_text, scenario_goals)
        )
        completed = bool(scenario_goals) and set(scenario_goals) <= set(merged)

        user_message = await conversations.insert_message(
            self._db, session_id, {"role": "user", "hangul": user_text}
        )
        assistant_message = await self._store_assistant_turn(session_id, turn)

        if completed:
            await conversations.update_session(
                self._db,
                session_id,
                {
                    "goals_completed": merged,
                    "status": "completed",
                    "ended_at": datetime.now(UTC).isoformat(),
                },
            )
            await progress_service.update_after_scenario_completion(
                self._db, user_id, int(scenario["id"]), session_id
            )
        else:
            await conversations.update_session(
                self._db, session_id, {"goals_completed": merged}
            )

        audio_base64, tts_seconds = await self._synthesize(turn.ai_response_hangul)
        await self._meter(user_id, tokens, tts_seconds)

        return TurnResponse(
            user_message=_message_model(user_message),
            assistant_message=_message_model(assistant_message),
            goals_completed=merged,
            scenario_completed=completed,
            audio_base64=audio_base64,
        )

    async def end(self, user_id: UUID, session_id: int) -> ConversationSession:
        session = await conversations.get_own_session(self._db, user_id, session_id)
        if session["status"] == "active":
            scenario = await content.get_scenario_by_id(self._db, int(session["scenario_id"]))
            scenario_goals = {str(g) for g in scenario["completion_goals"]}
            done = scenario_goals and scenario_goals <= {str(g) for g in session["goals_completed"]}
            session = await conversations.end_session(
                self._db, session_id, "completed" if done else "abandoned"
            )
        return _session_model(session)

    async def get_with_messages(
        self, user_id: UUID, session_id: int
    ) -> tuple[ConversationSession, list[ConversationMessage]]:
        session = await conversations.get_own_session(self._db, user_id, session_id)
        messages = await conversations.list_messages(self._db, session_id)
        return _session_model(session), [_message_model(m) for m in messages]

    async def _ensure_turn_quota(self, user_id: UUID, plan: Plan) -> None:
        usage = await usage_repo.get_today(self._db, user_id)
        ensure_within_quota(usage, plan, Metric.CONVERSATION_TURN)

    async def _build_history(self, session_id: int) -> list[ChatMessage]:
        """Replay stored turns; assistant turns as their raw JSON (keeps the
        model anchored to the output format, per the prompt's contract)."""
        history: list[ChatMessage] = []
        for row in await conversations.list_messages(self._db, session_id):
            if row["role"] == "assistant":
                turn = BaristaTurn(
                    ai_response_hangul=row["hangul"],
                    ai_response_romanized=row["romanized"] or "",
                    ai_response_english=row["english"] or "",
                    contextual_correction=row["contextual_correction"] or "",
                )
                history.append(ChatMessage(role="assistant", content=turn.model_dump_json()))
            else:
                history.append(ChatMessage(role="user", content=str(row["hangul"])))
        return history

    async def _store_assistant_turn(self, session_id: int, turn: BaristaTurn) -> JsonRow:
        return await conversations.insert_message(
            self._db,
            session_id,
            {
                "role": "assistant",
                "hangul": turn.ai_response_hangul,
                "romanized": turn.ai_response_romanized,
                "english": turn.ai_response_english,
                "contextual_correction": turn.contextual_correction,
            },
        )

    async def _synthesize(self, text: str) -> tuple[str | None, int]:
        if not self._tts.is_configured:
            return None, 0
        try:
            audio = await self._tts.synthesize(text)
        except AIServiceError:
            logger.warning("tts_failed_turn_continues")
            return None, 0
        seconds = max(1, len(audio) // _MP3_BYTES_PER_SECOND)
        return base64.b64encode(audio).decode(), seconds

    async def _meter(self, user_id: UUID, tokens: TokenUsage, tts_seconds: int) -> None:
        await usage_repo.increment(
            self._db,
            user_id,
            turns=1,
            tokens_in=tokens.tokens_in,
            tokens_out=tokens.tokens_out,
            tts_seconds=tts_seconds,
        )


def _session_model(row: JsonRow) -> ConversationSession:
    return ConversationSession(
        id=int(row["id"]),
        scenario_id=int(row["scenario_id"]),
        status=row["status"],
        goals_completed=[str(g) for g in row["goals_completed"]],
        started_at=row["started_at"],
        ended_at=row.get("ended_at"),
    )


def _message_model(row: JsonRow) -> ConversationMessage:
    return ConversationMessage(
        id=int(row["id"]),
        role=row["role"],
        hangul=str(row["hangul"]),
        romanized=row.get("romanized"),
        english=row.get("english"),
        contextual_correction=row.get("contextual_correction"),
        created_at=row["created_at"],
    )
