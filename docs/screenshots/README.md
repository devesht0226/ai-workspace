# Screenshots (for a professional README)

Add image files here, then link them from the root `README.md`.

## Recommended set (capture at http://localhost:3000)

| File name | What to show | Caption idea |
|-----------|--------------|--------------|
| `01-home.png` | Landing page with brand **AI Workspace** | Product identity |
| `02-dashboard.png` | Dashboard + Start here | Account hub |
| `03-chat.png` | Streaming chat with markdown | Conversational AI |
| `04-rag.png` | Document Q&A with citations visible | Grounded RAG |
| `05-sql.png` | SQL result `total_revenue = 2499` | Safe NL→SQL |
| `06-agents.png` | Agent steps including SQL preview | Multi-agent orchestration |

## How to capture (Windows)

1. Start API + web (`docs/INSTALL.md`).
2. Sign in; seed demo data (one PDF, one chat, one SQL run).
3. Use a wide window (1280px+).
4. `Win+Shift+S` → capture region → paste into Paint → save as PNG with the names above.
5. Or browser DevTools → Ctrl+Shift+P → “Capture full size screenshot”.

## After adding files

Uncomment the Screenshots section in the root `README.md`:

```markdown
## Screenshots

![Dashboard](docs/screenshots/02-dashboard.png)
![RAG with citations](docs/screenshots/04-rag.png)
![SQL assistant](docs/screenshots/05-sql.png)
```

## Related

- Walkthrough: [docs/DEMO.md](../DEMO.md)
- Video script: [docs/DEMO_VIDEO.md](../DEMO_VIDEO.md)
