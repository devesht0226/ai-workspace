# Installation Guide

## Requirements

- Docker Desktop (or Docker Engine + Compose)
- Python 3.10+ (API on host)
- Node.js 22+ (web on host)
- 8GB+ RAM recommended if running Ollama locally

## 1. Clone and configure

```bash
git clone <your-repo-url> ai-workspace
cd ai-workspace
cp .env.example .env
```

Edit `.env` and set a long `JWT_SECRET` (32+ characters).

## 2. Start infrastructure

```bash
docker compose up -d postgres redis qdrant ollama
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull nomic-embed-text
```

## 3. Start API

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify: http://localhost:8000/health and http://localhost:8000/docs

## 4. Start web

```bash
cd apps/web
npm install
npm run dev
```

Open: http://localhost:3000

## Production-style Compose (Nginx on port 80)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile apps up -d --build
```

Then open http://localhost (Nginx proxies `/` → web and `/api` → API).

## Tests

```bash
cd apps/api
pytest -q
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| DB connection errors | Ensure Postgres is healthy: `docker compose ps` |
| Chat/RAG empty or errors | Pull Ollama models; or set `LLM_PROVIDER=fake` for offline demos |
| CORS errors | Add your web origin to `CORS_ORIGINS` |
| 429 responses | Raise `RATE_LIMIT_REQUESTS` or disable with `RATE_LIMIT_ENABLED=false` |
| Audio meetings fail | Upload `.txt` transcript or set `OLLAMA_WHISPER_MODEL` |
