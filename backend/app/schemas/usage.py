from datetime import date

from pydantic import BaseModel

from app.schemas.plans import Plan


class UsageCounters(BaseModel):
    """Today's consumption for one user (zeros when no row exists yet)."""

    usage_date: date
    pronunciation_attempts: int = 0
    conversation_turns: int = 0
    llm_tokens_in: int = 0
    llm_tokens_out: int = 0
    tts_seconds: int = 0
    handwriting_checks: int = 0

    @property
    def llm_tokens_total(self) -> int:
        return self.llm_tokens_in + self.llm_tokens_out


class UsageTodayResponse(BaseModel):
    """Counters plus the resolved plan's limits, so the UI renders one meter."""

    usage: UsageCounters
    plan: Plan
