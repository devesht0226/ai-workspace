# User Manual

## Sign in

1. Open the app and choose **Open workspace**.
2. Register with email + password (min 8 characters).
3. You land on the **Dashboard**.

## Dashboard

Shows counts (documents, chats, reviews, resumes, meetings, agent runs), usage by event type, and recent activity.

## Chat

1. Open **Chat** → **New chat**.
2. Send a message; tokens stream into the assistant bubble.
3. History is saved per session.

## Documents (RAG)

1. Open **Documents**.
2. Upload a text-based PDF.
3. Ask a question; read the answer and **Sources** citations.

## SQL Assistant

1. Open **SQL**.
2. Ask a natural-language question (e.g. total order revenue).
3. Review generated SQL, explanation, optimization tips, and result table.
4. Only read-only `SELECT` queries are allowed.

## Code Review

1. Open **Code**.
2. Upload a `.py` / `.ts` file or `.zip`.
3. Inspect findings, summary, and suggested tests.

## Resume Analyzer

1. Open **Resume**.
2. Paste a job description and upload a PDF/TXT resume.
3. Review ATS score, skills, match gaps, and suggestions.

## Meeting Notes

1. Open **Meetings**.
2. Paste a transcript (recommended) or upload `.txt` / `.vtt` / audio.
3. Review summary and action items; export via API `/meetings/{id}/export`.

## Agents

1. Open **Agents**.
2. Enter a task (e.g. “What is total order revenue in SQL?”).
3. Inspect planner steps, specialist outputs, report, and evaluation score.

## Privacy tips

- Change `JWT_SECRET` before sharing a deployment.
- Do not upload secrets into code review archives.
- Demo SQL data is local SQLite sample data only.
