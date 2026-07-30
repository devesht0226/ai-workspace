# Resume Bullet Points (Portfolio)

Copy/adapt these for internships and junior roles:

- Built **AI Workspace**, a full-stack enterprise-style AI platform (Next.js + FastAPI) with JWT/session auth, orgs/teams, GDPR account deletion, streaming chat, and multi-format RAG (PDF/DOCX/PPTX/TXT/MD/HTML) with citations, hybrid search, and collections.
- Implemented an **AI evaluation framework** (Precision@K, Recall@K, MRR, nDCG, faithfulness, hallucination, citation correctness), human feedback loop, prompt registry, and cross-model benchmarking (Llama/GPT/Mistral/HuggingFace).
- Designed **multi-agent orchestration** with execution tracing (planner → specialists → report → eval), knowledge graph, short/long-term memory, and in-app notifications.
- Delivered specialized assistants: SQL (NL→SQL, ER graph, CSV export), code review with complexity estimates, resume ATS + cover letter, meeting intelligence (decisions + follow-up email).
- Applied production habits: Docker Compose, Nginx, CI, audit logging, rate limiting, secure headers, Admin RBAC UI, and automated API tests across the full blueprint surface.
- Documented the system with product requirements, architecture ADRs, install/user/developer guides, and an explicit MVP → enterprise completion journey.

## Interview talking points

1. Why Ollama-first + multi-provider model router (incl. auto fallback)?
2. How RAG citations and eval metrics prove answer quality?
3. How SQL injection / mutation risk is mitigated (allowlist + SELECT-only)?
4. How orgs/teams + GDPR deletion demonstrate production/security thinking?
5. What was intentionally pragmatic (DDG search, lightweight rerank) vs what you'd harden next?
