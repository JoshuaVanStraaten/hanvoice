"""Row factories mirroring the Supabase schema, for respx-mocked responses."""

import time
import uuid
from typing import Any

import jwt

TEST_JWT_SECRET = "test-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_USER_ID = "1b671a64-40d5-491e-99b0-da01ff1f3341"


def auth_headers(user_id: str = TEST_USER_ID) -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": user_id,
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
            "email": "user@example.com",
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def plan_row(plan_id: str = "free", **overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "free": {
            "name": "Free",
            "price_usd_cents": 0,
            "billing_period": "none",
            "daily_pronunciation_limit": 20,
            "daily_conversation_turn_limit": 10,
            "daily_llm_token_limit": 20000,
            "daily_handwriting_limit": 10,
        },
        "founder": {
            "name": "Lifetime Founder Pass",
            "price_usd_cents": 6900,
            "billing_period": "lifetime",
            "daily_pronunciation_limit": 200,
            "daily_conversation_turn_limit": 150,
            "daily_llm_token_limit": 300000,
            "daily_handwriting_limit": 100,
        },
        "premium": {
            "name": "Premium",
            "price_usd_cents": 1499,
            "billing_period": "monthly",
            "daily_pronunciation_limit": 200,
            "daily_conversation_turn_limit": 150,
            "daily_llm_token_limit": 300000,
            "daily_handwriting_limit": 100,
        },
    }[plan_id]
    return {"id": plan_id, "is_active": True, **defaults, **overrides}


def profile_row(user_id: str = TEST_USER_ID, **overrides: Any) -> dict[str, Any]:
    return {
        "id": user_id,
        "display_name": "Josh",
        "native_language": "en",
        "onboarding_completed": True,
        "created_at": "2026-07-01T00:00:00+00:00",
        "updated_at": "2026-07-01T00:00:00+00:00",
        **overrides,
    }


def usage_row(user_id: str = TEST_USER_ID, **overrides: Any) -> dict[str, Any]:
    return {
        "id": 1,
        "user_id": user_id,
        "usage_date": "2026-07-03",
        "pronunciation_attempts": 0,
        "conversation_turns": 0,
        "llm_tokens_in": 0,
        "llm_tokens_out": 0,
        "tts_seconds": 0,
        "handwriting_checks": 0,
        **overrides,
    }


def subscription_row(user_id: str = TEST_USER_ID, **overrides: Any) -> dict[str, Any]:
    return {
        "id": 1,
        "user_id": user_id,
        "plan_id": "premium",
        "status": "active",
        "provider": "stripe",
        "provider_subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
        "cancel_at_period_end": False,
        **overrides,
    }


def founder_pass_row(user_id: str = TEST_USER_ID) -> dict[str, Any]:
    return {
        "id": 1,
        "user_id": user_id,
        "provider": "stripe",
        "provider_payment_id": "pi_test",
        "amount_usd_cents": 6900,
    }
