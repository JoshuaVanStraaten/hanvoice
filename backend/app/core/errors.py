"""Application error hierarchy and the single JSON error envelope.

Every non-2xx response the API produces has the shape::

    {"error": {"code": "<machine_readable>", "message": "<human readable>"}}

Routes and services raise :class:`AppError` subclasses; the handlers
registered by :func:`register_error_handlers` translate them (and unexpected
exceptions) into that envelope so clients only ever parse one format.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Base class for expected, client-presentable failures."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "Something went wrong."):
        self.message = message
        super().__init__(message)


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class QuotaExceededError(AppError):
    status_code = 429
    code = "quota_exceeded"


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "service_unavailable"


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


def _envelope(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return _envelope(exc.code, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in first.get("loc", []))
        detail = first.get("msg", "Invalid request.")
        return _envelope("validation_error", f"{location}: {detail}", 422)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _envelope("http_error", str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=request.url.path)
        return _envelope("internal_error", "Something went wrong on our side.", 500)
