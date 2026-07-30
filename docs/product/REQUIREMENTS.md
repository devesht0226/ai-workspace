# Requirements

Requirements are prioritized with **MoSCoW** relative to **Version 1 (MVP)** unless noted.

## Functional Requirements

### Authentication & Users

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AUTH-01 | User can register with email and password | Must (V1) |
| FR-AUTH-02 | User can log in and receive access + refresh tokens (JWT) | Must (V1) |
| FR-AUTH-03 | User can refresh an access token using a valid refresh token | Must (V1) |
| FR-AUTH-04 | User can view and update basic profile fields | Must (V1) |
| FR-AUTH-05 | Role-based access (e.g. `user`, `admin`) enforced on protected routes | Should (V1) |
| FR-AUTH-06 | Email verification flow | Could (V1.1) |
| FR-AUTH-07 | Password reset via email | Could (V1.1) |

### AI Chat

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CHAT-01 | User can create and list chat sessions | Must (V1) |
| FR-CHAT-02 | User can send messages and receive streaming assistant replies | Must (V1) |
| FR-CHAT-03 | Conversation history persists and loads per session | Must (V1) |
| FR-CHAT-04 | Model / provider selectable via configuration (Ollama default) | Must (V1) |
| FR-CHAT-05 | Prompt templates for common tasks | Should (V1) |
| FR-CHAT-06 | Export chat session (Markdown/JSON) | Could (V1) |
| FR-CHAT-07 | Runtime UI model switching across multiple cloud providers | Won’t (V1) / Should (later) |

### Document Intelligence (RAG)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RAG-01 | User can upload PDF documents | Must (V1) |
| FR-RAG-02 | System extracts text, chunks content, and stores embeddings | Must (V1) |
| FR-RAG-03 | User can ask questions answered from retrieved chunks | Must (V1) |
| FR-RAG-04 | Answers include citations (document + chunk/page reference when available) | Must (V1) |
| FR-RAG-05 | User can list and delete their documents | Must (V1) |
| FR-RAG-06 | Hybrid search + reranking | Won’t (V1) / Should (V1.x+) |
| FR-RAG-07 | OCR for scanned PDFs | Won’t (V1) |
| FR-RAG-08 | Source highlighting in UI | Could (V2 UI polish) |

### Platform (Later Versions)

| ID | Area | Earliest version |
|----|------|------------------|
| FR-SQL-* | Natural language → SQL, explain, execute (safe) | V2 |
| FR-CODE-* | Repo/file analysis, suggestions, docs/tests | V3 |
| FR-RESUME-* | Parse, skills, ATS checks, JD match | V4 |
| FR-MEET-* | Audio → transcript → summary / actions | V5 |
| FR-AGENT-* | LangGraph multi-agent orchestration | V6 |
| FR-DASH-* | Activity, usage, settings analytics | V6 |

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | API is versioned under `/api/v1` | Must |
| NFR-02 | Stack runs locally via Docker Compose | Must |
| NFR-03 | Structured application logging | Must |
| NFR-04 | Centralized exception handling with consistent error payloads | Must |
| NFR-05 | Secrets and config via environment variables | Must |
| NFR-06 | Stateless API instances (session state in DB/Redis as appropriate) | Must |
| NFR-07 | Meaningful automated tests for auth and RAG critical paths | Should (expand in Phase 14) |
| NFR-08 | Rate limiting, secure headers, audit logging | Should (Phase 13) |
| NFR-09 | CI pipeline runs lint/tests on pull requests | Should (from Phase 2 stub) |
| NFR-10 | Horizontal scale readiness (no local disk as sole source of truth for uploads long-term) | Could |

## Constraints

- **Primary LLM runtime for V1:** Ollama (local)
- **Provider abstraction:** Interfaces allow OpenAI/Anthropic via env without feature rewrites
- **Primary relational DB:** PostgreSQL
- **Vector store:** Qdrant
- **Cache / ephemeral:** Redis
- **Frontend:** Next.js + TypeScript + Tailwind
- **Backend:** FastAPI + SQLAlchemy

## Acceptance Criteria (V1 Done)

1. Fresh clone + Compose brings up dependencies and apps with documented env sample.
2. Register → login → create chat → streaming reply works.
3. Upload PDF → query → cited answer works for a sample document.
4. Product and architecture docs exist and match the implemented V1 scope.
