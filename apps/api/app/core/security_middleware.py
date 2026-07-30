"""Security middleware: headers, request IDs, rate limiting, audit trail."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

audit_logger = logging.getLogger("aiworkspace.audit")
_rate_lock = Lock()
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _allow_request(key: str, *, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    with _rate_lock:
        bucket = _rate_buckets[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store"
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Request-ID"] = request_id

        user_hint = request.headers.get("authorization", "")[:16]
        audit_logger.info(
            "method=%s path=%s status=%s duration_ms=%s request_id=%s auth=%s ip=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
            "yes" if user_hint else "no",
            _client_key(request),
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if settings.environment == "test" or not settings.rate_limit_enabled:
            return await call_next(request)

        # Health checks and CORS preflight bypass rate limiting
        if request.url.path in {"/health", "/ready"} or request.method == "OPTIONS":
            return await call_next(request)

        key = f"{_client_key(request)}:{request.url.path}"
        limit = settings.rate_limit_requests
        window = settings.rate_limit_window_seconds

        # Stricter bucket for auth endpoints
        if request.url.path.startswith(f"{settings.api_prefix}/auth/"):
            limit = min(limit, settings.rate_limit_auth_requests)

        if not _allow_request(key, limit=limit, window_seconds=window):
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests. Please retry later.",
                        "details": {"window_seconds": window},
                    }
                },
                headers={"Retry-After": str(window)},
            )
        return await call_next(request)
