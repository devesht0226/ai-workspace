# Wireframes (Low-Fidelity)

V1 UI is intentionally simple: one composition per screen, brand “AI Workspace” visible, chat and documents as primary jobs. Not pixel-perfect—layout contracts for implementation.

## Auth — Login / Register

```text
+--------------------------------------------------+
|  AI Workspace                                    |
|                                                  |
|     Sign in                                      |
|     [ email                         ]            |
|     [ password                      ]            |
|     [ Continue ]                                 |
|     Need an account? Register                    |
|                                                  |
+--------------------------------------------------+
```

## Chat

```text
+--------------------------------------------------+
| AI Workspace          [Docs] [Settings] [Logout] |
+------------------+-------------------------------+
| Sessions         |  Session title                |
| (+) New chat     |-------------------------------|
| - SLA questions  |  user: What is the uptime?    |
| - Onboarding     |  assistant: 99.9% ...         |
|                  |  (streaming caret)            |
|                  |-------------------------------|
|                  |  [ message input... ] [Send]  |
+------------------+-------------------------------+
```

## Documents / RAG

```text
+--------------------------------------------------+
| AI Workspace          [Chat] [Settings] [Logout] |
+------------------+-------------------------------+
| Your documents   |  Ask about: sla.pdf           |
| [Upload PDF]     |-------------------------------|
| - sla.pdf ready  |  Q: What is the uptime SLA?   |
| - handbook.pdf   |  A: ...                       |
|                  |  Sources:                     |
|                  |   - sla.pdf p.3 "Availability"|
|                  |-------------------------------|
|                  |  [ Ask a question... ] [Ask]  |
+------------------+-------------------------------+
```

## Notes for implementers

- Hero/marketing landing can wait; authenticated app shell is V1 priority.
- No dashboard cards, stat strips, or promo chips in V1.
- Citations render as a simple source list under the answer (highlighting later).
- Streaming: append tokens in the assistant bubble; disable double-submit while in flight.
