# Folder Structure

Monorepo layout for AI Workspace (V1 scaffold + growth path).

```text
ai-workspace/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── .gitignore
├── LICENSE
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── product/
│   │   ├── VISION.md
│   │   ├── PERSONAS.md
│   │   ├── REQUIREMENTS.md
│   │   ├── USE_CASES.md
│   │   ├── FEATURES.md
│   │   └── ROADMAP.md
│   └── architecture/
│       ├── SYSTEM.md
│       ├── DATA_MODEL.md
│       ├── API.md
│       ├── SEQUENCES.md
│       ├── FOLDER_STRUCTURE.md
│       ├── COMPONENTS.md
│       ├── TECH_DECISIONS.md
│       ├── AI_WORKFLOWS.md
│       ├── WIREFRAMES.md
│       └── DEPLOYMENT.md
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── pyproject.toml            # or requirements.txt initially
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── core/                 # config, logging, security
│   │   │   ├── api/
│   │   │   │   └── v1/               # routers
│   │   │   ├── models/               # SQLAlchemy models
│   │   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── services/             # business logic
│   │   │   ├── providers/            # LLM / embedding abstractions
│   │   │   ├── db/                   # session, base
│   │   │   └── workers/              # optional background jobs later
│   │   └── tests/
│   └── web/                          # Next.js frontend
│       ├── package.json
│       ├── Dockerfile
│       ├── README.md
│       ├── src/
│       │   ├── app/                  # App Router
│       │   ├── components/
│       │   ├── lib/                  # API client, auth helpers
│       │   └── styles/
│       └── public/
└── scripts/                          # optional: seed, smoke demos
```

## Conventions

- **Feature logic lives in `services/`**, not in routers.
- **Providers** isolate Ollama vs cloud SDKs behind interfaces.
- **No shared `packages/` until** a clear cross-app type contract is needed (OpenAPI-generated client preferred first).
- **Docs-as-code:** product and architecture stay in `docs/` and update when behavior changes.
