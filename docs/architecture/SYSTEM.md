# System Architecture (as-built)

## Target diagram — now implemented

```text
                    User
                      |
                 Web Application (Next.js)
                      |
              API Gateway (/api/v1 + Nginx)
                      |
         Auth · Orgs/Teams · Notifications · Admin
                      |
              AI Orchestration Layer
                      |
     -------------------------------------------------
     |        |        |         |         |         |
   RAG     SQL     Code     Research   Meeting   Report
  Agent   Agent   Agent      Agent      Agent    /Eval
     |
 ----------------------------
 |            |              |
Vector DB   Knowledge      Memory
(Qdrant)     Graph       (short/long)

                      |
                 Model Router
                      |
        ---------------------------------
        |          |          |         |
      Llama      GPT      Mistral   HuggingFace
     (Ollama)  (OpenAI)            (optional)

              Evaluation Framework  (RAG metrics + nDCG + agent scores)
              Observability Layer   (agent traces, latency, tokens)
              Feedback Learning Loop (👍/👎 → feedback store)
              Prompt Registry       (versioned system prompts)
              Model Benchmarks      (cross-model ranking)
              Monitoring System     (/metrics, audit logs)
              Security Layer        (JWT, sessions, GDPR delete, RBAC)
```

## Responsibility map

| Layer | Implementation |
|-------|----------------|
| Web | `apps/web` (Home, Chat, Docs, Orgs, Admin, Alerts, Eval, …) |
| API Gateway | FastAPI routers + optional Nginx |
| Orgs / Teams | `app/services/orgs.py` |
| Notifications | `app/services/notifications.py` |
| Orchestration | `app/services/agents.py` |
| RAG | multi-format `documents` + hybrid + rerank + collections |
| Research | DuckDuckGo + compare + export |
| Vector DB | Qdrant (+ memory fallback) |
| Knowledge Graph | `knowledge_nodes` / `knowledge_edges` |
| Memory | `memory_entries` |
| Model Router | `app/providers/router.py` |
| Evaluation | `app/services/rag_eval.py` |
| Observability | `app/services/tracing.py` |
| Security | JWT, rate limit, headers, GDPR delete, admin RBAC |

## Related

- [DATA_MODEL.md](./DATA_MODEL.md)
- [API.md](./API.md)
- [AI_WORKFLOWS.md](./AI_WORKFLOWS.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)
