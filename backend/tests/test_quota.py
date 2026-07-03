from datetime import date

import pytest

from app.core.errors import QuotaExceededError
from app.schemas.plans import Plan
from app.schemas.usage import UsageCounters
from app.services.quota import Metric, ensure_within_quota
from tests.factories import plan_row

FREE = Plan.model_validate(plan_row("free"))


def usage(**kwargs) -> UsageCounters:
    return UsageCounters(usage_date=date(2026, 7, 3), **kwargs)


def test_under_limit_passes():
    ensure_within_quota(usage(pronunciation_attempts=19), FREE, Metric.PRONUNCIATION)


def test_at_pronunciation_limit_raises():
    with pytest.raises(QuotaExceededError):
        ensure_within_quota(usage(pronunciation_attempts=20), FREE, Metric.PRONUNCIATION)


def test_conversation_turn_limit_raises():
    with pytest.raises(QuotaExceededError):
        ensure_within_quota(usage(conversation_turns=10), FREE, Metric.CONVERSATION_TURN)


def test_token_budget_also_gates_turns():
    over_tokens = usage(conversation_turns=1, llm_tokens_in=15000, llm_tokens_out=5000)
    with pytest.raises(QuotaExceededError):
        ensure_within_quota(over_tokens, FREE, Metric.CONVERSATION_TURN)


def test_handwriting_limit_raises():
    with pytest.raises(QuotaExceededError):
        ensure_within_quota(usage(handwriting_checks=10), FREE, Metric.HANDWRITING)


def test_other_metrics_do_not_interfere():
    heavy_elsewhere = usage(pronunciation_attempts=20, conversation_turns=10)
    ensure_within_quota(heavy_elsewhere, FREE, Metric.HANDWRITING)
