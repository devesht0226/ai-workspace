# API Specification (V1 Outline)

Base path: `/api/v1`  
Auth: `Authorization: Bearer <access_token>` unless noted.  
OpenAPI: served by FastAPI at `/docs` and `/openapi.json` when the API runs.

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Liveness |
| GET | `/ready` | No | Readiness (DB/Qdrant checks as available) |

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create user |
| POST | `/auth/login` | No | Access + refresh tokens |
| POST | `/auth/refresh` | No | Rotate/refresh access token |
| POST | `/auth/logout` | Yes | Revoke refresh token |
| GET | `/users/me` | Yes | Current profile |
| PATCH | `/users/me` | Yes | Update profile |

### Example payloads

**POST `/auth/register`**

```json
{ "email": "alex@example.com", "password": "••••••••", "full_name": "Alex Chen" }
```

**POST `/auth/login` →**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

## Chat

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/chats` | Yes | List sessions |
| POST | `/chats` | Yes | Create session |
| GET | `/chats/{id}` | Yes | Session + messages |
| DELETE | `/chats/{id}` | Yes | Delete session |
| POST | `/chats/{id}/messages` | Yes | Send message; `text/event-stream` or JSON |
| GET | `/chats/{id}/export` | Yes | Export Markdown/JSON (Could) |

**Streaming:** Prefer SSE (`text/event-stream`) with events `token`, `citation`, `done`, `error`.

## Documents & RAG

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/documents` | Yes | List documents |
| POST | `/documents` | Yes | Upload PDF (`multipart/form-data`) |
| GET | `/documents/{id}` | Yes | Metadata + status |
| DELETE | `/documents/{id}` | Yes | Delete doc + vectors |
| POST | `/documents/{id}/query` | Yes | Question → grounded answer + citations |
| POST | `/rag/query` | Yes | Query across user docs (optional filter) |

### Example RAG response

```json
{
  "answer": "The SLA commits to 99.9% monthly uptime.",
  "citations": [
    {
      "document_id": "...",
      "filename": "sla.pdf",
      "chunk_id": "...",
      "page_number": 3,
      "snippet": "Availability shall be maintained at 99.9%..."
    }
  ]
}
```

## Errors

Consistent shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Human-readable summary",
    "details": {}
  }
}
```

Common codes: `unauthorized`, `forbidden`, `not_found`, `validation_error`, `conflict`, `rate_limited`, `processing_failed`.

## Versioning Policy

Breaking changes go to `/api/v2`. Additive fields are allowed in v1 with care.
