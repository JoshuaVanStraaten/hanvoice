import base64
import binascii

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, Db, VisionClient
from app.core.errors import BadRequestError
from app.core.ratelimit import rate_limit
from app.db.repositories import attempts, content
from app.db.repositories import usage as usage_repo
from app.schemas.handwriting import HandwritingAttemptRequest, HandwritingAttemptResponse
from app.services import progress as progress_service
from app.services.entitlements import resolve_plan
from app.services.quota import Metric, ensure_within_quota

router = APIRouter(tags=["handwriting"])

_MAX_IMAGE_BYTES = 2 * 1024 * 1024
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@router.post(
    "/handwriting/attempts",
    response_model=HandwritingAttemptResponse,
    dependencies=[Depends(rate_limit(max_requests=6, window_seconds=60))],
)
async def create_handwriting_attempt(
    body: HandwritingAttemptRequest,
    user: CurrentUser,
    db: Db,
    vision: VisionClient,
) -> HandwritingAttemptResponse:
    try:
        image = base64.b64decode(body.image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BadRequestError("image_base64 is not valid base64 data.") from exc
    if not image.startswith(_PNG_MAGIC):
        raise BadRequestError("The image must be a PNG.")
    if len(image) > _MAX_IMAGE_BYTES:
        raise BadRequestError("Image too large — export the canvas at a smaller size.")

    # Validate the block before any AI spend, mirroring the phrase lookup in
    # the pronunciation route.
    block = None
    if body.block_id is not None:
        block = await content.get_block(db, body.block_id)
        await content.get_published_lesson_by_id(db, int(block["lesson_id"]))
        if block["kind"] != "write":
            raise BadRequestError("block_id must reference a write block.")
        target = (block.get("payload") or {}).get("target")
        if target != body.target_text:
            raise BadRequestError("target_text does not match this block's target.")

    plan = await resolve_plan(db, user.id)
    usage = await usage_repo.get_today(db, user.id)
    ensure_within_quota(usage, plan, Metric.HANDWRITING)

    scores = await vision.assess_handwriting(body.image_base64, body.target_text)

    attempt = await attempts.insert_handwriting_attempt(
        db, user.id, body.target_text, scores, vision.model_version
    )
    await usage_repo.increment(db, user.id, handwriting=1)
    if block is not None:
        await progress_service.mark_block_result(
            db,
            user.id,
            block,
            score=scores.overall_score,
            passed=scores.overall_score >= progress_service.PASS_THRESHOLD,
        )

    return HandwritingAttemptResponse(
        attempt_id=int(attempt["id"]),
        target_text=body.target_text,
        scores=scores,
        model_version=vision.model_version,
    )
