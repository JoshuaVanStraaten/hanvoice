"""Daily quota enforcement.

Pure functions over (today's usage, resolved plan) so the rules are trivially
testable. Called by every metered route *before* the AI provider is invoked —
quota errors must cost us nothing.
"""

from enum import StrEnum

from app.core.errors import QuotaExceededError
from app.schemas.plans import Plan
from app.schemas.usage import UsageCounters


class Metric(StrEnum):
    PRONUNCIATION = "pronunciation"
    CONVERSATION_TURN = "conversation_turn"
    HANDWRITING = "handwriting"


_MESSAGES = {
    Metric.PRONUNCIATION: "You've used all of today's pronunciation checks.",
    Metric.CONVERSATION_TURN: "You've used all of today's conversation turns.",
    Metric.HANDWRITING: "You've used all of today's handwriting checks.",
}
_UPGRADE_HINT = " Upgrade for a higher daily limit, or come back tomorrow."


def ensure_within_quota(usage: UsageCounters, plan: Plan, metric: Metric) -> None:
    """Raise QuotaExceededError (HTTP 429) if the next unit of work is not allowed."""
    if metric is Metric.PRONUNCIATION:
        exceeded = usage.pronunciation_attempts >= plan.daily_pronunciation_limit
    elif metric is Metric.CONVERSATION_TURN:
        exceeded = (
            usage.conversation_turns >= plan.daily_conversation_turn_limit
            or usage.llm_tokens_total >= plan.daily_llm_token_limit
        )
    else:
        exceeded = usage.handwriting_checks >= plan.daily_handwriting_limit

    if exceeded:
        raise QuotaExceededError(_MESSAGES[metric] + _UPGRADE_HINT)
