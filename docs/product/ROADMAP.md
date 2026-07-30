# Product Roadmap

## Timeline Overview

**Duration:** ~5–6 months part-time (~2–3 hours/day)  
**Strategy:** MVP first (V1), then expand by version. Each GitHub milestone ends in a demonstrable feature.

```text
Phase 0  Product Planning          ████  2–3 days
Phase 1  Software Design           ████████  5–7 days
Phase 2  Dev Environment           ████  2–3 days
Phase 3  Backend Foundation        ████████  ~1 week
Phase 4  Authentication            ████████  ~1 week
Phase 5  AI Chat                   ████████  ~1 week
Phase 6  Document Intelligence     ████████████████  ~2 weeks
         ——— V1 DEMO CHECKPOINT ———
Phase 7  SQL Assistant             ████████  ~1 week     (V2)
Phase 8  Code Review               ████████████████  ~2 weeks (V3)
Phase 9  Resume Analyzer           ████████  ~1 week     (V4)
Phase 10 Meeting Notes             ████████  ~1 week     (V5)
Phase 11 Agent Orchestration       ████████████████  ~2 weeks (V6)
Phase 12 Dashboard                 ████████  ~1 week     (V6)
Phase 13 Security                  ██████  4–5 days
Phase 14 Testing                   ████████  ~1 week
Phase 15 Deployment                ████████  ~1 week
Phase 16 Documentation             ██████  3–4 days
```

## GitHub Milestones

| # | Milestone | Maps to | Demo checkpoint |
|---|-----------|---------|-----------------|
| 1 | Project Setup | Phases 0–2 | Repo clones; Compose starts infra; docs present |
| 2 | Authentication | Phase 4 | Register/login/refresh/profile via API (and UI when ready) |
| 3 | AI Chat | Phase 5 | Streaming chat with persisted history |
| 4 | RAG | Phase 6 | PDF upload + cited Q&A |
| 5 | SQL Assistant | Phase 7 | NL→SQL explain/run on sample schema |
| 6 | Code Review | Phase 8 | Analyze sample repo; return findings |
| 7 | Resume Analyzer | Phase 9 | Score/compare resume vs JD |
| 8 | Meeting Notes | Phase 10 | Audio → summary + action items |
| 9 | Multi-Agent Workflow | Phase 11 | LangGraph multi-step task |
| 10 | Dashboard | Phase 12 | Activity + usage views |
| 11 | Security | Phase 13 | Rate limits, headers, audit trail |
| 12 | Deployment | Phase 15 | Public or VPS demo URL |
| 13 | Documentation | Phase 16 | Full docs + demo video + resume bullets |

## Version Mapping

| Product version | Milestones | Outcome |
|-----------------|------------|---------|
| **V1** | 1–4 | Auth + Chat + PDF RAG — apply/internship showcase |
| **V2** | 5 | SQL Assistant |
| **V3** | 6 | Code Review |
| **V4** | 7 | Resume Analyzer |
| **V5** | 8 | Meeting Notes |
| **V6** | 9–10 | Agents + Dashboard |
| **Hardening** | 11–13 | Security, deploy, docs (can overlap late V1+) |

## Demo Checkpoints

1. **After Milestone 1:** “Here’s the company-style repo and how to run it.”
2. **After Milestone 4 (V1):** Full happy path: sign up → chat → upload PDF → cited answer.
3. **After each later milestone:** One vertical demo script added to README.
4. **After Milestone 12–13:** Live demo + polished documentation pack.

## Current Status

| Phase / Version | Status |
|-----------------|--------|
| Phases 0–6 / **V1** | Done |
| **V2** SQL Assistant | Done |
| **V3** Code Review | Done |
| **V4** Resume Analyzer | Done |
| **V5** Meeting Notes | Done |
| **V6** Agents + Dashboard | Done |
| Phase 13 Security hardening | Done (rate limits, headers, audit logs, upload validation) |
| Phase 14 Testing | Done (API suites for V1–V6 + security) |
| Phase 15 Deployment | Done (Compose + Nginx prod overlay) |
| Phase 16 Documentation | Done (install/user/dev guides + resume bullets) |

## Related Docs

- [VISION.md](./VISION.md)
- [PERSONAS.md](./PERSONAS.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
- [USE_CASES.md](./USE_CASES.md)
- [FEATURES.md](./FEATURES.md)
- Architecture: [`../architecture/`](../architecture/)
