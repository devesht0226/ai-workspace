# AI Workspace — Journey (Start → Now)

This file is the single place that records **what we built from the beginning until now**.

Related docs (details live elsewhere):

| File | What it contains |
|------|------------------|
| [README.md](../README.md) | Current status snapshot + quick start |
| [product/ROADMAP.md](./product/ROADMAP.md) | Original phases, milestones, status table |
| [product/VISION.md](./product/VISION.md) | Why the product exists |
| [product/FEATURES.md](./product/FEATURES.md) | Features by version V1–V6 |
| [INSTALL.md](./INSTALL.md) | How to run |
| [USER_GUIDE.md](./USER_GUIDE.md) | How to use each screen |
| [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) | How to extend the code |
| [PRODUCTION.md](./PRODUCTION.md) | Deploy/TLS/SMTP what’s left for you |
| [RESUME_BULLETS.md](./RESUME_BULLETS.md) | Interview/resume lines |

---

## Timeline of what we did

### 1. Planning (Phase 0)
- Product vision, personas, requirements, use cases, features, roadmap
- Saved under `docs/product/`

### 2. Design (Phase 1)
- System architecture, ER model, API outline, sequences, ADRs, wireframes
- Saved under `docs/architecture/`

### 3. Repo setup (Phase 2)
- Monorepo: README, LICENSE, `.gitignore`, Docker Compose, CI, pre-commit
- Skeletons: `apps/api` (FastAPI) + `apps/web` (Next.js)

### 4. V1 MVP (Phases 3–6)
- Backend foundation (config, logging, DB, health)
- Auth (register/login/JWT/refresh/profile)
- Streaming AI chat + history
- PDF RAG with citations
- Web UI: login, chat, documents

### 5. V2–V6 features
- **V2 SQL** — NL→SQL, explain, optimize, safe SELECT execute (`/sql`)
- **V3 Code review** — upload/analyze findings (`/code`)
- **V4 Resume** — ATS + JD match (`/resume`)
- **V5 Meetings** — transcript → summary/actions (`/meetings`)
- **V6 Agents + Dashboard** — multi-agent runs + usage dashboard

### 6. First polish
- Rate limits, secure headers, audit logs, upload validation
- Nginx + production Compose overlay
- Install / user / developer guides + resume bullets

### 8. Architecture completion pass
- Model router: Llama (Ollama) / GPT (OpenAI) / Mistral
- Knowledge graph (entities + relations from documents)
- Long-term / short-term memory
- Dedicated Research agent (RAG + graph + memory + router)
- Updated system architecture diagram to match as-built stack

### 9. Production-grade AI engineering layer
- **Agent observability** — step traces (planner → specialists → report → eval), prompts, latency, token estimates (`/observability`, `/api/v1/traces`)
- **Advanced RAG evaluation** — Precision@K, Recall@K, MRR, nDCG, faithfulness, answer relevance, hallucination, citation correctness (`/eval`, `/api/v1/eval/rag`)
- **Human feedback loop** — Good/Bad on chat & research answers → feedback store + summary
- **Prompt registry** — versioned prompts with active revision (`/prompts`)
- **Model benchmarking** — same question across Llama/GPT/Mistral with ranking (`/benchmark`)

### 10. Enterprise blueprint completion
- Organizations / teams + invite by email
- Notifications (document/agent/meeting ready)
- Multi-format RAG (PDF/DOCX/PPTX/TXT/MD/HTML), collections, versioning, lightweight rerank
- Chat rename + Markdown rendering + memory injection
- Research web search (DuckDuckGo), doc compare, Markdown/DOCX export
- SQL ER graph + CSV export; meetings decisions/follow-up/search; resume cover letter
- HuggingFace model family + auto router fallback
- GDPR account deletion, sessions, change password, Admin UI
- Dashboard storage/token/model metrics

### 11. Local Windows run + hardening (demo-ready)
- SQLite local mode when Docker/Postgres is unavailable
- Ollama models on `D:` (`tinyllama` + `nomic-embed-text`) after C: disk pressure
- Fixed root `.env` loading (`OLLAMA_CHAT_MODEL` etc. actually apply)
- CORS for `localhost` + LAN IP preflight (login OPTIONS 400 → 200)
- SQL Assistant: schema-safe templates (no invented `product_id`); demo DB at `apps/api/uploads/demo_analytics.sqlite`
- Agents: factual SQL reports instead of tinyllama hallucinations
- Research: resilient brief builder + clearer UI errors
- Faster page shell (less “Loading workspace…” flash on navigation)

### 12. Final checklist closure (v1.0 freeze)
- Chat **delete** + **export** UI wired to existing APIs
- Documents: multi-format upload, collections UI, delete
- Meetings: audio/transcript file upload UI
- GDPR **data export** (`GET /users/me/export`) + Settings button
- Docs: `FINAL_CHECKLIST.md`, `DEMO.md`, `screenshots/` guide
- Tests: chat export/delete + GDPR export
- UI polish: grouped nav (Core / Tools / Platform), humanized Research/Graph/Eval/Traces/Benchmark/Admin/Agents
- **Cross-check:** 39 pytest green, web typecheck clean, health endpoints OK
- **Stop major features** — polish demos only from here

---

## What the product does today

One authenticated AI workspace where a user can:

1. Sign up / sign in (sessions, password change, GDPR delete)  
2. Chat with streaming AI (+ markdown, rename, feedback)  
3. Ask questions over multi-format documents with citations (+ collections/eval)  
4. Run SQL assistant (schema/ER/CSV), code review, resume, meetings  
5. Run multi-agent tasks and inspect execution traces  
6. Score RAG quality, manage prompts, benchmark models  
7. Research with RAG + knowledge graph + memory + optional web leads  
8. Manage orgs/teams, notifications, and (admins) users  

---

## Local demo stack (current machine)

| Piece | Typical URL / note |
|-------|--------------------|
| Web | http://localhost:3000 |
| API | http://127.0.0.1:8000/docs |
| DB | SQLite `aiworkspace.db` (no Docker required) |
| LLM | Ollama `tinyllama` (free, local) |
| Embeddings | Ollama `nomic-embed-text` |
| Optional paid keys | OpenAI / Mistral / Hugging Face (only for multi-model demo) |

**Known local limits:** tinyllama is small — great for demos, weak at long free-form “code review / report” prose. Trust SQL results, heuristic findings, and structured agent SQL answers more than creative LLM text.

---

## What is still on *you* (not missing code)

- Keep API + web + Ollama running for demos  
- Optional: public hosting, real domain TLS, real SMTP, system Tesseract  
- Optional later: Celery workers, commercial web search, cross-encoder rerank  
- Optional: add `OPENAI_API_KEY` / `MISTRAL_API_KEY` for full model benchmarks  

See [PRODUCTION.md](./PRODUCTION.md) and [INSTALL.md](./INSTALL.md).

---

## One-line summary

> We went from empty folder → company-style docs → V1–V6 platform → AI-eng layer (eval/traces/feedback) → enterprise blueprint (orgs, multi-format RAG, admin, GDPR) → Windows/Ollama demo hardening — recorded in `docs/product/ROADMAP.md`, `README.md`, and this `docs/JOURNEY.md`.
