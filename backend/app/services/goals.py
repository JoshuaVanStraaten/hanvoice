"""Scenario completion-goal detection.

Deliberately backend code, not model output (per the approved prompt's
integration notes): keyword heuristics over the learner's own words. A goal
counts when the learner *says* the thing — the AI saying it doesn't count.
Patterns are per-goal, not per-scenario; a new scenario reusing goal names
gets detection for free, and new goal names only need a pattern entry here.
"""

from collections.abc import Iterable

# Substring patterns (lowercased comparison). Korean needs no stemming for
# these beginner phrases; romanized/English forms count only where saying it
# in English still demonstrates the scene step (payment method, thanks).
_GOAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "greeted": ("안녕", "여보세요"),
    "ordered_drink": ("아메리카노", "라떼", "라테", "커피", "주세요", "카페모카", "에스프레소"),
    "stated_size_or_temp": (
        "아이스", "뜨거운", "뜨겁게", "핫", "차가운", "톨", "그란데", "벤티", "큰", "작은",
    ),
    "paid": ("카드", "현금", "결제", "계산"),
    "said_thanks": ("감사", "고마워", "고맙습니다"),
}


def detect_goals(user_text: str, candidate_goals: Iterable[str]) -> set[str]:
    """Which of ``candidate_goals`` does this user utterance satisfy?"""
    text = user_text.lower()
    hit: set[str] = set()
    for goal in candidate_goals:
        patterns = _GOAL_PATTERNS.get(goal, ())
        if any(pattern in text for pattern in patterns):
            hit.add(goal)
    return hit


def merge_goals(already_completed: list[str], newly_hit: set[str]) -> list[str]:
    """Stable-ordered union (existing order first, new goals appended)."""
    merged = list(already_completed)
    merged += [goal for goal in sorted(newly_hit) if goal not in already_completed]
    return merged
