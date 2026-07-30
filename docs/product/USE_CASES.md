# Use Cases & User Stories

## Primary Use Cases (V1)

### UC-01 — Register and authenticate

**Actor:** User  
**Goal:** Create an account and obtain a session.  
**Main flow:**

1. User submits email and password.
2. System validates input and stores a hashed password.
3. User logs in; system returns access and refresh JWTs.
4. User accesses protected resources with the access token.

**Alternate:** Invalid credentials → 401 with safe error message.

---

### UC-02 — Multi-turn AI chat

**Actor:** Authenticated user  
**Goal:** Converse with an AI model and retain history.  
**Main flow:**

1. User creates a chat session.
2. User sends a message.
3. System streams tokens from the configured provider (default Ollama).
4. System persists user and assistant messages.
5. User reopens the session and continues the conversation.

---

### UC-03 — Ask a question over an uploaded PDF

**Actor:** Authenticated user  
**Goal:** Get an answer grounded in a personal document, with citations.  
**Main flow:**

1. User uploads a PDF.
2. System extracts text, chunks, embeds, and indexes vectors in Qdrant.
3. User asks a question (chat or dedicated Q&A endpoint).
4. System retrieves top-k chunks, builds a grounded prompt, generates an answer.
5. Response includes citations pointing to source chunks/document metadata.

**Alternate:** Empty/unreadable PDF → clear processing error; no silent success.

---

### UC-04 — Manage workspace artifacts

**Actor:** Authenticated user  
**Goal:** List and remove chats and documents they own.  
**Main flow:** User lists resources → deletes unwanted items → system removes DB rows and vector points for that document.

---

## User Stories by Milestone

### Milestone 1 — Project Setup

- As a developer, I want a documented monorepo with Compose so I can run dependencies locally.
- As a reviewer, I want CI and a clear README so I can trust the project structure.

### Milestone 2 — Authentication

- As a user, I want to register and log in so my data is private to my account.
- As a user, I want refresh tokens so I stay signed in without re-entering my password constantly.
- As an admin (later), I want roles so privileged operations can be restricted.

### Milestone 3 — AI Chat

- As a user, I want streaming replies so the UI feels responsive.
- As a user, I want conversation history so I can resume prior work.
- As a developer, I want a provider abstraction so I can demo with Ollama or a cloud API.

### Milestone 4 — RAG

- As a user, I want to upload PDFs and ask questions so answers use my content.
- As a user, I want citations so I can verify claims.
- As a user, I want to delete documents so I control what the system can retrieve.

### Milestones 5–13 (V2+)

Mapped in [ROADMAP.md](./ROADMAP.md): SQL → Code Review → Resume → Meetings → Agents → Dashboard → Security → Deploy → Docs.

## Story Template (for issues)

```text
Title: [Area] Short outcome
As a <persona>,
I want <capability>,
so that <benefit>.

Acceptance:
- [ ] ...
Milestone: N
Version: V1|V2|...
```
