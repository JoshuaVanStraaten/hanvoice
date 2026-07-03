"""Shared plumbing for AI provider clients.

Every provider call goes through :func:`post_with_retry`: one bounded retry
on transient failures (timeouts, 5xx), then a typed error the route layer
maps to 502/503. Provider error bodies are logged, never leaked to clients.
"""

from typing import Any

import httpx
import structlog

from app.core.errors import AppError

logger = structlog.get_logger(__name__)


class AIServiceError(AppError):
    """The provider responded, but unusably (bad status, malformed payload)."""

    status_code = 502
    code = "ai_service_error"

    def __init__(self, message: str = "The AI service returned an unexpected response."):
        super().__init__(message)


class AIServiceUnavailableError(AIServiceError):
    """The provider could not be reached (or is not configured)."""

    status_code = 503
    code = "ai_service_unavailable"

    def __init__(self, message: str = "The AI service is temporarily unavailable."):
        super().__init__(message)


_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


async def post_with_retry(
    http: httpx.AsyncClient,
    url: str,
    *,
    provider: str,
    headers: dict[str, str] | None = None,
    json: Any | None = None,
    content: bytes | None = None,
    files: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    timeout: float = 60.0,
) -> httpx.Response:
    last_error: str = ""
    for attempt in (1, 2):
        try:
            response = await http.post(
                url,
                headers=headers,
                json=json,
                content=content,
                files=files,
                data=data,
                params=params,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            last_error = repr(exc)
            logger.warning(
                "ai_request_failed", provider=provider, attempt=attempt, error=last_error
            )
            continue

        if response.status_code in _RETRYABLE_STATUSES:
            last_error = f"HTTP {response.status_code}"
            logger.warning("ai_request_retrying", provider=provider, status=response.status_code)
            continue
        if response.status_code >= 400:
            logger.error(
                "ai_request_error",
                provider=provider,
                status=response.status_code,
                body=response.text[:500],
            )
            raise AIServiceError(f"{provider} request failed.")
        return response

    logger.error("ai_request_exhausted", provider=provider, error=last_error)
    raise AIServiceUnavailableError(f"{provider} is temporarily unavailable.")
