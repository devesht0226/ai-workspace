# Developer Guide

## Repository layout

```text
apps/api     FastAPI backend
apps/web     Next.js frontend
docs/        Product, architecture, guides
deploy/      Nginx and deploy assets
```

## Backend conventions

- Routers in `app/api/v1/` stay thin; business logic lives in `app/services/`.
- LLM / embeddings / STT go through `app/providers/` abstractions.
- Errors raise `AppError` subclasses → uniform `{ "error": { code, message, details } }`.
- V1 bootstrap uses `Base.metadata.create_all` on startup (swap to Alembic when schemas stabilize).

## Running tests

```bash
cd apps/api
pytest -q
```

Tests force `ENVIRONMENT=test`, `LLM_PROVIDER=fake`, SQLite, and disabled rate limits.

## Adding a feature

1. Update product docs / API outline if behavior is user-facing.
2. Add model/schema/service/router.
3. Wire router into `app/api/v1/router.py`.
4. Add API tests with the fake provider.
5. Add a web page + `api` client method + nav link.

## Security notes

- Rate limiting: `RateLimitMiddleware` (per IP + path).
- Headers: `SecurityHeadersMiddleware`.
- Audit: structured `aiworkspace.audit` logs with request IDs.
- Uploads: `app/core/validation.py` extension + size checks.
- SQL Assistant: SELECT-only allowlist.

## Local vs Compose

| Mode | Command |
|------|---------|
| Infra only | `docker compose up -d postgres redis qdrant ollama` |
| Apps profile | `docker compose --profile apps up -d --build` |
| Nginx entry | `docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile apps up -d --build` |

## Useful endpoints

- `GET /health`, `GET /ready`
- OpenAPI: `/docs`
- Versioned API: `/api/v1/...`
