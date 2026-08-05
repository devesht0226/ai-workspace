# Demo video script (2–3 minutes)

Record with OBS, Windows Game Bar (`Win+G`), or Loom. Target 1080p.

## Setup before recording

1. API + web running (`docs/INSTALL.md` or live deploy).
2. Signed-in demo user with one PDF uploaded and one chat open.
3. Browser at 1280×720 or wider; hide bookmarks bar.

## Script

| Time | Screen | Say |
|------|--------|-----|
| 0:00–0:20 | Home / Dashboard | “AI Workspace is a full-stack enterprise AI platform I built with Next.js and FastAPI — not just a chatbot.” |
| 0:20–0:50 | Chat | “Authenticated streaming chat with markdown history, export, and delete.” |
| 0:50–1:20 | Documents | “RAG over multi-format docs with citations so answers are grounded.” |
| 1:20–1:50 | SQL | “Natural language to SQL — safe SELECT-only — demo revenue is 2499.” |
| 1:50–2:20 | Agents | “Multi-agent orchestration: planner, specialists, report, and evaluation.” |
| 2:20–2:45 | Eval / Observability | “I also added retrieval metrics, traces, and model benchmarking.” |
| 2:45–3:00 | GitHub / architecture | “Open source on GitHub with Docker, CI, and architecture docs.” |

## Export

- Save as `docs/demo-video.mp4` (optional; large files — prefer YouTube/Drive link).
- Add link under **Live demo** in the root README.

## Do not

- Do not show `.env`, JWT secrets, or personal emails.
- Do not rely on slow `tinyllama` for the spoken SQL claim — run SQL before recording so the result is ready.
