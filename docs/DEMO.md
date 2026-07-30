# AI Workspace — Demo Guide (10 minutes)

Use this script for interviews or portfolio walkthroughs.  
Stack: **Web** http://localhost:3000 · **API** http://127.0.0.1:8000 · **Ollama** (`tinyllama` + `nomic-embed-text`) · **SQLite**

## Before you start

1. API running: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` in `apps/api`
2. Web running: `npm run dev` in `apps/web`
3. Ollama running with `tinyllama` and `nomic-embed-text`
4. `.env` has `DATABASE_URL=sqlite:///./aiworkspace.db` and `OLLAMA_CHAT_MODEL=tinyllama`

---

## Script

### 1. Auth (30s)
- Open http://localhost:3000 → Login / Register
- Show Settings: profile, sessions, **Export my data**, GDPR delete (don’t delete during demo)

### 2. Chat (1 min)
- New chat → ask: `Explain RAG in two sentences`
- Show streaming + markdown
- **Rename**, **Export** (.md), mention **Delete**

### 3. Documents / RAG (2 min)
- Upload a PDF (or DOCX/TXT)
- Ask a grounded question → show **citations**
- Mention collections in the sidebar

### 4. SQL Assistant (1 min)
- Ask: `What is total revenue from orders?`
- Expect SQL `SELECT SUM(amount)…` and result **2499**
- Mention read-only safety (no DELETE)

### 5. Code Review (1 min)
- Upload a small `.py` with `eval()` / bare `except` / hard-coded key
- Show **heuristic findings** (trust these more than tinyllama prose)

### 6. Meetings (45s)
- Paste a short transcript with an action item → Process
- Show summary + action items

### 7. Agents (1 min)
- Task: `What is total order revenue in SQL?`
- Show planner → SQL step → factual report → score

### 8. Research (1 min)
- Ask about an **uploaded** document theme (not random SLA unless you uploaded one)
- Show brief + citations

### 9. Eval / Traces / Benchmark (1 min)
- **Eval**: RAG metrics (Precision@K, nDCG, faithfulness…)
- **Traces**: agent step timeline
- **Benchmark**: Llama works locally; GPT/Mistral need API keys

### 10. Close (30s)
- Dashboard metrics + notifications
- Architecture one-liner: Next.js → FastAPI → SQLite/Qdrant/Ollama + multi-agent + eval

---

## Honest demo tips

| Trust | Be careful |
|-------|------------|
| SQL results, heuristic code findings, agent SQL steps | Free-form tinyllama summaries |
| Citations pointing at real files | Invented medical/legal claims |
| Local Ollama = free | OpenAI/Mistral = optional paid |

## Screenshots

Capture pages into `docs/screenshots/` (see README there) and link them from the portfolio README when ready.
