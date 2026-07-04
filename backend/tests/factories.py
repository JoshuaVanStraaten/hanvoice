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


def lesson_row(lesson_id: int = 1, **overrides: Any) -> dict[str, Any]:
    return {
        "id": lesson_id,
        "slug": "cafe-essentials",
        "title": "Café essentials",
        "description": "The handful of phrases that get you through any Seoul café.",
        "section": "Speak",
        "sort_order": 1,
        **overrides,
    }


def block_row(block_id: int = 1, kind: str = "explain", **overrides: Any) -> dict[str, Any]:
    return {
        "id": block_id,
        "lesson_id": 1,
        "kind": kind,
        "phrase_id": None,
        "payload": {"segments": [{"type": "text", "body": "Hangul is an alphabet."}]},
        "sort_order": block_id,
        **overrides,
    }


def block_progress_row(block_id: int = 1, **overrides: Any) -> dict[str, Any]:
    return {
        "id": 1,
        "user_id": TEST_USER_ID,
        "block_id": block_id,
        "passed": True,
        "best_score": None,
        "passed_at": "2026-07-04T10:00:00+00:00",
        **overrides,
    }


def phrase_row(phrase_id: int = 1, **overrides: Any) -> dict[str, Any]:
    return {
        "id": phrase_id,
        "lesson_id": 1,
        "hangul": "아이스 아메리카노 주세요",
        "romanized": "aiseu amerikano juseyo",
        "english": "One iced americano, please",
        "audio_url": None,
        "sort_order": 1,
        **overrides,
    }


def scenario_row(**overrides: Any) -> dict[str, Any]:
    return {
        "id": 1,
        "slug": "cafe-iced-americano",
        "title": "Order an iced Americano",
        "description": "Greet the barista and order an iced Americano.",
        "difficulty": 1,
        "sort_order": 1,
        "completion_goals": [
            "greeted",
            "ordered_drink",
            "stated_size_or_temp",
            "paid",
            "said_thanks",
        ],
        **overrides,
    }


def prompt_row(**overrides: Any) -> dict[str, Any]:
    return {"id": 1, "version": 1, "system_prompt": "SYSTEM PROMPT", **overrides}


def session_row(**overrides: Any) -> dict[str, Any]:
    return {
        "id": 1,
        "user_id": TEST_USER_ID,
        "scenario_id": 1,
        "status": "active",
        "goals_completed": [],
        "started_at": "2026-07-03T10:00:00+00:00",
        "ended_at": None,
        **overrides,
    }


def message_row(message_id: int = 1, role: str = "assistant", **overrides: Any) -> dict[str, Any]:
    return {
        "id": message_id,
        "session_id": 1,
        "role": role,
        "hangul": "안녕하세요! 뭐 드릴까요?",
        "romanized": "annyeonghaseyo! mwo deurilkkayo?",
        "english": "Hello! What can I get you?",
        "contextual_correction": "",
        "created_at": "2026-07-03T10:00:01+00:00",
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
