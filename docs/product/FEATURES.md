# Feature List by Version

## Version 1 — MVP (Internship-ready core)

| Area | Features |
|------|----------|
| **Auth** | Registration, login, JWT access + refresh, profile, basic RBAC |
| **Chat** | Sessions, message history, streaming responses, config-based model/provider |
| **RAG** | PDF upload, text extraction, chunking, embeddings, vector search, citations, document CRUD |
| **Platform** | FastAPI skeleton, health checks, logging, `/api/v1`, Docker Compose, CI stub, product/architecture docs |

**Deferred from classic “full auth” checklist:** email verification and password reset → **V1.1** if they block demo velocity.

---

## Version 2 — SQL Assistant

- Natural language → SQL
- SQL explanation
- Query optimization hints
- Guarded query execution
- Result visualization hooks
- Schema understanding / introspection

---

## Version 3 — Code Review Assistant

- Repository or archive upload
- File-level analysis
- Bug / smell detection
- Refactoring suggestions
- Documentation generation
- Unit test generation assistance

---

## Version 4 — Resume Analyzer

- Resume parsing
- Skill extraction
- ATS-style checks
- Job description comparison
- Improvement suggestions

---

## Version 5 — Meeting Notes

- Audio upload
- Speech-to-text
- Summary
- Action items
- Optional speaker identification
- Export notes

---

## Version 6 — Agents + Dashboard

- Planner, Retrieval, SQL, Code, Report, Evaluation agents
- LangGraph orchestration
- Recent activity, documents, token usage, search history, analytics, settings

---

## Cross-cutting (Phased)

| Concern | When |
|---------|------|
| Security hardening (validation, rate limits, headers, audit logs) | Phase 13 / ongoing |
| Broad test suites | Phase 14 |
| Production deployment (Nginx, GH Actions deploy, env) | Phase 15 |
| User/dev manuals, demo video, resume bullets | Phase 16 |

## Feature Freeze Rule

No Version N+1 feature work starts until the current version’s **demo script** (README section) works on a clean machine.
