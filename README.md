# AI Workspace

[![CI](https://github.com/devesht0226/ai-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/devesht0226/ai-workspace/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An enterprise-style AI knowledge platform you can run on a laptop.**

One signed-in product that combines chat, document Q&A (RAG), SQL, code review, resume analysis, meeting notes, multi-agent orchestration, research, evaluation, and admin — built as a portfolio-grade full-stack system (Next.js + FastAPI).

| | |
|---|---|
| **Local web** | http://localhost:3000 |
| **API docs** | http://127.0.0.1:8000/docs |
| **Live demo** | _Deploy with [docs/DEPLOY_CLOUD.md](docs/DEPLOY_CLOUD.md) — then paste your Vercel URL here_ |
| **Status** | **v1.0.0** complete — demo-ready on Windows with SQLite + Ollama |
| **License** | MIT |
| **Changelog** | [CHANGELOG.md](CHANGELOG.md) |

---

## What is this project?

AI Workspace answers: *“What would a real internal AI platform look like if I built the full stack myself?”*

It is **not** a single chatbot demo. It is one authenticated workspace with:

1. **People & security** — register/login, JWT + refresh, sessions, RBAC, GDPR export/delete  
2. **Knowledge** — upload documents, ask questions with **citations** (RAG)  
3. **Specialist tools** — SQL assistant, code review, resume ATS, meeting notes  
4. **Orchestration** — multi-agent planner → specialists → report + score  
5. **Quality** — RAG metrics (nDCG, faithfulness…), feedback, traces, model benchmarks  

**Stack:** Next.js (web) → FastAPI (API) → SQLite or PostgreSQL → Ollama (local LLM) → optional Qdrant / Redis / OpenAI / Mistral.

---

## Feature map (what to click)

| Module | Path | What a visitor should see |
|--------|------|---------------------------|
| Dashboard | `/dashboard` | Usage, recent chats/docs, start-here guide |
| Chat | `/chat` | Streaming answers, markdown, rename/export/delete |
| Documents | `/documents` | Upload PDF/DOCX/… → ask → citations |
| SQL | `/sql` | “Total revenue?” → safe SQL → **2499** on demo data |
| Code | `/code` | Upload `.py`/ZIP → heuristic security/bug findings |
| Resume | `/resume` | ATS score + JD match |
| Meetings | `/meetings` | Transcript/audio → summary + action items |
| Agents | `/agents` | Multi-step run with SQL/RAG specialists |
| Research | `/research` | RAG + graph + memory brief |
| Eval / Traces / Benchmark | `/eval`, `/observability`, `/benchmark` | Quality & observability |
| Settings / Admin | `/settings`, `/admin` | Profile, GDPR, user admin |

**10-minute walkthrough:** [docs/DEMO.md](docs/DEMO.md) · **Video script:** [docs/DEMO_VIDEO.md](docs/DEMO_VIDEO.md)

---

## Screenshots

Capture UI images into [`docs/screenshots/`](docs/screenshots/README.md), then uncomment:

<!--
![Home](docs/screenshots/01-home.png)
![Dashboard](docs/screenshots/02-dashboard.png)
![Chat](docs/screenshots/03-chat.png)
![RAG](docs/screenshots/04-rag.png)
![SQL](docs/screenshots/05-sql.png)
![Agents](docs/screenshots/06-agents.png)
-->

---

## Quick start (local)

```bash
# 1) Config
cp .env.example .env
# For laptop demo without Docker, set in .env:
#   DATABASE_URL=sqlite:///./aiworkspace.db
#   OLLAMA_CHAT_MODEL=tinyllama
#   OLLAMA_EMBED_MODEL=nomic-embed-text

# 2) Ollama (required for local AI)
#    ollama pull tinyllama
#    ollama pull nomic-embed-text

# 3) API
cd apps/api
python -m venv .venv
# Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 4) Web (new terminal)
cd apps/web
npm install
npm run dev
```

Open **http://localhost:3000** → Register → follow [DEMO.md](docs/DEMO.md).

Optional infra (Postgres/Redis/Qdrant/Ollama via Docker): `docker compose up -d`

Full install notes: [docs/INSTALL.md](docs/INSTALL.md)

---

## Deploy (public demo)

| Layer | Host | Guide |
|-------|------|--------|
| Web | **Vercel** (`apps/web`) | [docs/DEPLOY_CLOUD.md](docs/DEPLOY_CLOUD.md) |
| API + DB | **Render** Blueprint or **Railway** | `render.yaml` / `railway.toml` |

Cloud demos should use **OpenAI or Mistral** (Ollama does not run on Vercel/Render free tiers).

---

## Architecture (simple view)

```text
Browser (Next.js)
    │
    ▼
FastAPI  ──► Auth / Orgs / Notifications / Admin
    │
    ├── Chat + Memory
    ├── Documents → Chunk → Embed → Vector search → LLM → Citations
    ├── SQL / Code / Resume / Meetings
    ├── Agents (planner → specialists → report → eval)
    ├── Research + Knowledge Graph
    └── Eval · Traces · Prompts · Benchmarks
         │
         ▼
   SQLite or Postgres · Ollama · (optional Qdrant/Redis)
```

Deeper design: [docs/architecture/SYSTEM.md](docs/architecture/SYSTEM.md) · ADRs: [docs/architecture/TECH_DECISIONS.md](docs/architecture/TECH_DECISIONS.md)

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [DEMO.md](docs/DEMO.md) | Interview / portfolio walkthrough |
| [DEMO_VIDEO.md](docs/DEMO_VIDEO.md) | 2–3 min recording script |
| [DEPLOY_CLOUD.md](docs/DEPLOY_CLOUD.md) | Vercel + Render/Railway |
| [JOURNEY.md](docs/JOURNEY.md) | How the project was built start → now |
| [FINAL_CHECKLIST.md](docs/FINAL_CHECKLIST.md) | v1.0 completion status |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | How to use each screen |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | How to extend the code |
| [RESUME_BULLETS.md](docs/RESUME_BULLETS.md) | Resume + interview talking points |
| [screenshots/](docs/screenshots/README.md) | Where to put UI captures |

---

## Design choices (honest)

- **Ollama-first** so demos work offline/free; cloud keys (OpenAI/Mistral) are optional.  
- **SQLite** supported so Windows demos don’t require Docker.  
- Small local models (e.g. `tinyllama`) are fine for wiring demos; trust SQL results and heuristic code findings more than long free-form LLM prose.  
- Scope is frozen at **v1.0** — polish and demonstrate, don’t keep adding features.

---

## License

MIT — see [LICENSE](LICENSE).
