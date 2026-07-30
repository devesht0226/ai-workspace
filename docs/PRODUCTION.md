# Production readiness notes

## What “perfect” means in this repo

This project now includes the features and operational pieces expected of a serious portfolio platform:

- Email verification + password reset (file mailer or SMTP)
- Hybrid RAG search (BM25 + vector RRF)
- OCR fallback path for sparse PDFs
- Admin APIs (list/activate/deactivate/promote, stats)
- Metrics endpoint (`/metrics`)
- TLS Nginx config + cert generator
- Postgres backup script
- Settings / verify / reset UI pages
- API E2E smoke script

## Still outside any single local repo

| Item | Why |
|------|-----|
| Public internet demo URL | Needs your cloud account / DNS |
| Real Let’s Encrypt certs | Needs a public domain |
| Managed SMTP (SendGrid etc.) | Needs API keys |
| System Tesseract install | Optional OS package for full OCR |

Configure those when you deploy; the hooks are already in code.
