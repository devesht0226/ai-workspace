"""Application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security_middleware import (
    RateLimitMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from app.db import session as db_session
from app.db.session import init_db

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Workspace API",
    version="0.2.0",
    description="AI Workspace API — Auth, Chat, RAG, SQL, Code, Resume, Meetings, Agents.",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    lifespan=lifespan,
)

register_exception_handlers(app)

# Last added = outermost. CORS must be outermost so OPTIONS preflight succeeds.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)

_cors_origins = settings.cors_origins_list
# In development, also allow any private LAN origin (e.g. http://192.168.x.x:3000)
_cors_kwargs: dict = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
_cors_regex = None
if settings.environment == "development":
    # Allow localhost + private LAN origins used when opening the UI by IP
    _cors_regex = (
        r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?"
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_regex,
    **_cors_kwargs,
)

app.include_router(api_router, prefix=settings.api_prefix)

# Lightweight Prometheus-compatible metrics (no extra dependency)
_request_count = {"value": 0}


@app.middleware("http")
async def count_requests(request, call_next):
    response = await call_next(request)
    _request_count["value"] += 1
    return response


@app.get("/metrics", tags=["observability"])
def metrics() -> PlainTextResponse:
    body = (
        "# HELP aiworkspace_http_requests_total Total HTTP requests processed.\n"
        "# TYPE aiworkspace_http_requests_total counter\n"
        f"aiworkspace_http_requests_total {_request_count['value']}\n"
        "# HELP aiworkspace_up 1 if process is up.\n"
        "# TYPE aiworkspace_up gauge\n"
        "aiworkspace_up 1\n"
    )
    return PlainTextResponse(body, media_type="text/plain; version=0.0.4")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
def ready() -> dict[str, object]:
    """Readiness probe with database check."""
    checks: dict[str, str] = {}
    try:
        if db_session.SessionLocal is None:
            raise RuntimeError("database not configured")
        with db_session.SessionLocal() as session:
            session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"
        return {"status": "not_ready", "checks": checks}
    return {"status": "ready", "checks": checks}
