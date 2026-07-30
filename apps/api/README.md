# AI Workspace API

FastAPI backend for authentication, streaming chat, and PDF RAG.

## Run

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

OpenAPI: http://localhost:8000/docs

## Tests

```bash
pytest -q
```

Uses `ENVIRONMENT=test`, SQLite, and fake LLM/embeddings.
