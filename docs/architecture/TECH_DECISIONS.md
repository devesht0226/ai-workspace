# Technology Decisions (ADRs)

## ADR-001: Monorepo

**Decision:** Single repository with `apps/api`, `apps/web`, and `docs/`.  
**Why:** One flagship GitHub project; aligned versions; simpler portfolio narrative.  
**Tradeoff:** CI must path-filter later; avoid premature shared packages.

## ADR-002: FastAPI + SQLAlchemy + PostgreSQL

**Decision:** Python FastAPI for HTTP API; SQLAlchemy for ORM; PostgreSQL as system of record.  
**Why:** Strong async story, automatic OpenAPI, industry-standard relational model for users/chats/docs.  
**Tradeoff:** Python packaging discipline required; migrations via Alembic when models stabilize.

## ADR-003: Next.js + TypeScript + Tailwind

**Decision:** App Router frontend with TS and Tailwind.  
**Why:** Modern full-stack portfolio signal; good DX for streaming UI.  
**Tradeoff:** Frontend can lag backend during foundation weeks—API-first is acceptable.

## ADR-004: Ollama-first with provider abstraction

**Decision:** Default completions/embeddings via Ollama; `LLMProvider` / `EmbeddingProvider` interfaces; optional OpenAI/Anthropic via env.  
**Why:** Zero-cost local demos, reproducible for reviewers, no secrets required to run V1.  
**Tradeoff:** Local model quality varies; document recommended pull tags in README.

## ADR-005: Qdrant for vectors

**Decision:** Qdrant as vector database for chunk embeddings.  
**Why:** Purpose-built similarity search; clean Docker story; payload filtering by `user_id` / `document_id`.  
**Tradeoff:** Operational dependency vs pgvector; chosen for clearer RAG interview story.

## ADR-006: Redis in Compose from day one

**Decision:** Include Redis in Compose even if V1 uses it lightly.  
**Why:** Ready for refresh denylist, caching, and rate limiting without redesign.  
**Tradeoff:** Extra container; keep V1 usage optional/minimal.

## ADR-007: JWT access + refresh tokens

**Decision:** Short-lived access JWT + longer-lived refresh tokens stored hashed server-side.  
**Why:** Stateless API requests with revocation path for refresh.  
**Tradeoff:** Email verification / password reset deferred to V1.1 to protect MVP schedule.

## ADR-008: PDF-only RAG in V1

**Decision:** Support PDF upload/extract only for MVP RAG.  
**Why:** Narrow scope; high demo value; OCR and other formats later.  
**Tradeoff:** Scanned PDFs without text layer will fail until OCR phase.

## ADR-009: LangChain/LangGraph timing

**Decision:** Use thin provider clients for V1 chat/RAG; introduce LangGraph in Version 6 (multi-agent).  
**Why:** Avoid framework lock-in before core pipelines work; still learn RAG fundamentals.  
**Tradeoff:** Some re-integration work later—acceptable and interview-honest.

## ADR-010: Docker Compose as primary local runtime

**Decision:** All services documented and runnable via Compose.  
**Why:** Matches production-minded onboarding; reviewers get one path.  
**Tradeoff:** Requires Docker resources for Ollama; document host-Ollama alternative if needed.
