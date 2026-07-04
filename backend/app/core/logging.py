"""Structured logging with a per-request correlation id.

Logs are JSON in production (machine-ingestable) and pretty-printed in
development. ``RequestContextMiddleware`` binds a request id into the
structlog context so every log line emitted while handling a request can be
correlated, and echoes it back in the ``X-Request-ID`` response header.
"""

import logging
import uuid

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def configure_logging(log_level: str, *, json_logs: bool) -> None:
    renderer: structlog.typing.Processor
    renderer = structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


class RequestContextMiddleware:
    """Pure-ASGI middleware: bind a request id, log request completion."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:16]
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        status_holder = {"status": 0}

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                headers = message.setdefault("headers", [])
                headers.append((b"x-request-id", request_id.encode()))
            await send(message)

        await self.app(scope, receive, send_with_request_id)

        structlog.get_logger("hanvoice.request").info(
            "request",
            method=scope["method"],
            path=scope["path"],
            status=status_holder["status"],
        )
