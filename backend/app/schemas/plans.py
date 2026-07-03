from typing import Literal

from pydantic import BaseModel


class Plan(BaseModel):
    """A row of public.plans — quota limits are data, not code."""

    id: str
    name: str
    price_usd_cents: int
    billing_period: Literal["none", "monthly", "lifetime"]
    daily_pronunciation_limit: int
    daily_conversation_turn_limit: int
    daily_llm_token_limit: int
    daily_handwriting_limit: int
