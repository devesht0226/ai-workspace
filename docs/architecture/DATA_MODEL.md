# Data Model (ER)

## Entity Relationship (V1)

```mermaid
erDiagram
  users ||--o{ chat_sessions : owns
  users ||--o{ documents : owns
  users ||--o{ refresh_tokens : has
  chat_sessions ||--o{ messages : contains
  documents ||--o{ document_chunks : has
  users ||--o{ usage_events : generates

  users {
    uuid id PK
    string email UK
    string password_hash
    string full_name
    string role
    boolean is_active
    timestamptz created_at
    timestamptz updated_at
  }

  refresh_tokens {
    uuid id PK
    uuid user_id FK
    string token_hash
    timestamptz expires_at
    boolean revoked
    timestamptz created_at
  }

  chat_sessions {
    uuid id PK
    uuid user_id FK
    string title
    string model_name
    string provider
    timestamptz created_at
    timestamptz updated_at
  }

  messages {
    uuid id PK
    uuid session_id FK
    string role
    text content
    jsonb metadata
    timestamptz created_at
  }

  documents {
    uuid id PK
    uuid user_id FK
    string filename
    string content_type
    string storage_path
    string status
    int page_count
    timestamptz created_at
    timestamptz updated_at
  }

  document_chunks {
    uuid id PK
    uuid document_id FK
    int chunk_index
    text content
    int page_number
    string qdrant_point_id
    timestamptz created_at
  }

  usage_events {
    uuid id PK
    uuid user_id FK
    string event_type
    string model_name
    int input_tokens
    int output_tokens
    jsonb metadata
    timestamptz created_at
  }
```

## Notes

- **Passwords:** Store only hashes (bcrypt/argon2); never plaintext.
- **Refresh tokens:** Store hash of token; support revoke on logout.
- **Document status:** `pending | processing | ready | failed`.
- **Qdrant payload:** `user_id`, `document_id`, `chunk_id`, `page_number`, optional `filename` for filtered search.
- **Messages.metadata:** Citations, model info, token counts, RAG flags.
- **usage_events:** Lightweight metering for dashboard (V6); optional writes in V1 chat/RAG paths.

## Indexes (planned)

- `users.email` unique
- `chat_sessions(user_id, updated_at DESC)`
- `messages(session_id, created_at)`
- `documents(user_id, created_at DESC)`
- `document_chunks(document_id, chunk_index)`
- `refresh_tokens(user_id)`, `refresh_tokens(token_hash)` unique
