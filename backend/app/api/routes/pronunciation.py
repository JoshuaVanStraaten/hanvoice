"""Pronunciation attempts: audio in, Azure scores out, rollups updated.

Order of operations is cost-driven: rate limit → quota gate → Azure call →
persist → meter. A learner over quota never costs us an Azure call.
"""

import base64
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import AzureClient, CurrentUser, Db, Tts
from app.core.errors import BadRequestError
from app.core.ratelimit import rate_limit
from app.db.repositories import attempts, content
from app.db.repositories import usage as usage_repo
from app.schemas.pronunciation import PronunciationAttemptResponse
from app.services import progress as progress_service
from app.services.entitlements import resolve_plan
from app.services.quota import Metric, ensure_within_quota

router = APIRouter(tags=["pronunciation"])

_MAX_AUDIO_BYTES = 10 * 1024 * 1024  # ~10 MB covers any 30s recording
_ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/webm", "audio/ogg", "audio/mpeg", "audio/mp4"}


@router.post(
    "/pronunciation/attempts",
    response_model=PronunciationAttemptResponse,
    dependencies=[Depends(rate_limit(max_requests=10, window_seconds=60))],
)
async def create_pronunciation_attempt(
    user: CurrentUser,
    db: Db,
    azure: AzureClient,
    audio: Annotated[UploadFile, File(description="The learner's recording")],
    phrase_id: Annotated[int | None, Form()] = None,
    target_text: Annotated[str | None, Form(max_length=200)] = None,
) -> PronunciationAttemptResponse:
    content_type = (audio.content_type or "").split(";")[0].strip()
    if content_type not in _ALLOWED_AUDIO_TYPES:
        raise BadRequestError(f"Unsupported audio type '{content_type}'.")
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise BadRequestError("The recording is empty — try again.")
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise BadRequestError("Recording too large — keep it under 30 seconds.")

    phrase = None
    if phrase_id is not None:
        phrase = await content.get_phrase(db, phrase_id)
        reference_text = str(phrase["hangul"])
    elif target_text and target_text.strip():
        reference_text = target_text.strip()
    else:
        raise BadRequestError("Provide a phrase_id or target_text to practice.")

    plan = await resolve_plan(db, user.id)
    usage = await usage_repo.get_today(db, user.id)
    ensure_within_quota(usage, plan, Metric.PRONUNCIATION)

    scores = await azure.assess(audio_bytes, reference_text, content_type=content_type)

    attempt = await attempts.insert_pronunciation_attempt(
        db, user.id, reference_text, scores, phrase_id
    )
    await usage_repo.increment(db, user.id, pronunciation=1)
    if phrase is not None:
        await progress_service.update_after_pronunciation(
            db, user.id, phrase, scores.overall
        )

    return PronunciationAttemptResponse(
        attempt_id=int(attempt["id"]), target_text=reference_text, scores=scores
    )


@router.get(
    "/pronunciation/phrases/{phrase_id}/audio",
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
async def get_phrase_audio(
    phrase_id: int, user: CurrentUser, db: Db, tts: Tts
) -> dict[str, str]:
    """Reference pronunciation for a phrase, synthesized on demand.

    Locked to known phrase ids — never arbitrary text — so the TTS spend is
    bounded by our own content. Not quota-metered: listening is learning.
    """
    phrase = await content.get_phrase(db, phrase_id)
    audio = await tts.synthesize(str(phrase["hangul"]))
    return {"audio_base64": base64.b64encode(audio).decode()}
