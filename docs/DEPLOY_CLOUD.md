# Cloud deploy (Vercel web + Render/Railway API)

Portfolio goal: public demo URL without changing product scope.

## Architecture

```text
Browser → Vercel (Next.js apps/web)
              │  NEXT_PUBLIC_API_URL
              ▼
         Render / Railway (FastAPI apps/api + Postgres)
              │
              ▼
         OpenAI or Mistral (cloud LLM — Ollama is local-only)
```

## 1) Deploy API (Render Blueprint — easiest)

1. Push `main` to GitHub.
2. [Render](https://render.com) → New → Blueprint → select this repo (`render.yaml`).
3. Set `OPENAI_API_KEY` when prompted (recommended for public demo).
4. Note the API URL, e.g. `https://ai-workspace-api.onrender.com`.
5. Open `/health` — should return OK.

The Blueprint uses a **native Python** free web service (not Docker) so free tier works.

**If deploy failed earlier with Docker:** sync the Blueprint again after pulling latest `render.yaml`, or delete the failed web service and re-apply.

**SQLite note:** free Render disks are ephemeral. Prefer the Blueprint Postgres (`DATABASE_URL`). Free Postgres expires after **30 days** unless upgraded.

### Alternative: Railway

1. New Project → Deploy from GitHub.
2. Root / Dockerfile: `apps/api/Dockerfile` (or use root `railway.toml`).
3. Add Postgres plugin; set `DATABASE_URL`.
4. Same env vars as above (`ENVIRONMENT=production`, CORS, OpenAI, JWT).

## 2) Deploy web (Vercel)

1. [Vercel](https://vercel.com) → Add New Project → import this GitHub repo.
2. **Root Directory:** `apps/web`
3. Framework: Next.js (auto).
4. Environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://YOUR-API.onrender.com` (no trailing slash)
5. Deploy. Copy the `*.vercel.app` URL.

## 3) Wire CORS (required)

On the API host, set:

```env
ENVIRONMENT=production
CORS_ORIGINS=https://YOUR-APP.vercel.app
APP_BASE_URL=https://YOUR-APP.vercel.app
CORS_ORIGIN_REGEX=https://([\w-]+\.)?vercel\.app
```

Redeploy API after changing env. Then hard-refresh the Vercel site and register a user.

## 4) Smoke checklist

- [ ] `GET /health` on API
- [ ] Open Vercel URL → Register / Login
- [ ] Chat returns a reply (needs OpenAI/Mistral key if no Ollama)
- [ ] SQL “total revenue” → **2499** on demo data
- [ ] Documents upload + ask shows citations (optional for first demo)

## 5) Resume / README

After deploy, put the Vercel URL in:

- Root `README.md` (Live demo)
- Your resume / LinkedIn
- GitHub repo About → Website

## Cost tips

| Piece | Free tier |
|-------|-----------|
| Vercel | Hobby |
| Render / Railway | Free web + free Postgres (sleeps when idle) |
| OpenAI | Pay-as-you-go; use `gpt-4o-mini` |

Cold starts on free API hosts are normal (first request 30–60s).

## Local still works

Nothing here replaces `docs/INSTALL.md` / SQLite + Ollama on your laptop.
