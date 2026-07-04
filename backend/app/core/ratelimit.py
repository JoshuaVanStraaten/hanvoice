"""In-process sliding-window rate limiting.

Protects expensive AI routes from bursts and abuse *underneath* daily quotas
(quota says how much per day; this says how fast). In-process is deliberate:
we deploy single-instance per region at this scale, and the daily quota in
Postgres remains the authoritative cross-instance limit. Swap the store for
Redis if the API is ever scaled horizontally.
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Depends, Request

from app.core.errors import RateLimitedError
from app.core.security import AuthenticatedUser


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        """Record a hit for ``key``; return False if the window is full."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            return True


def rate_limit(max_requests: int, window_seconds: float) -> Callable[..., None]:
    """Per-user (fallback: per-IP) rate-limit dependency for a route."""
    limiter = SlidingWindowLimiter(max_requests, window_seconds)

    from app.api.deps import get_current_user  # local import avoids a cycle

    def dependency(
        request: Request,
        user: AuthenticatedUser = Depends(get_current_user),  # noqa: B008
    ) -> None:
        key = str(user.id) if user else (request.client.host if request.client else "unknown")
        if not limiter.check(key):
            raise RateLimitedError("Too many requests — give it a few seconds and try again.")

    return dependency


def rate_limit_anonymous(max_requests: int, window_seconds: float) -> Callable[..., None]:
    """Per-IP limiter for unauthenticated routes (e.g. waitlist)."""
    limiter = SlidingWindowLimiter(max_requests, window_seconds)

    def dependency(request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        if not limiter.check(key):
            raise RateLimitedError("Too many requests — give it a few seconds and try again.")

    return dependency
