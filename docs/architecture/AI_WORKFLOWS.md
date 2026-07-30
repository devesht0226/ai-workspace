# AI Workflows

## Chat completion (V1)

```mermaid
flowchart LR
  UserMsg[User_Message] --> History[Load_History]
  History --> Prompt[Build_Messages]
  Prompt --> Provider[LLM_Provider]
  Provider --> Stream[Token_Stream]
  Stream --> Persist[Persist_Assistant]
  Persist --> Client[SSE_to_Client]
```

- System prompt: concise assistant for workspace chat.
- History window: last N messages (config) to control context size.
- Usage event optional after completion.

## PDF RAG ingest (V1)

```mermaid
flowchart TD
  Upload[PDF_Upload] --> Validate[Validate_MIME_Size]
  Validate --> Store[Store_File]
  Store --> Extract[Extract_Text]
  Extract --> Chunk[Chunk_Text]
  Chunk --> Embed[Embed_Chunks]
  Embed --> Upsert[Upsert_Qdrant]
  Upsert --> Meta[Save_Chunk_Metadata]
  Meta --> Ready[Status_Ready]
```

**Chunking defaults (tunable):** ~500–800 tokens, ~10–15% overlap; retain `page_number` when extractors provide it.

## PDF RAG query (V1)

```mermaid
flowchart TD
  Question[User_Question] --> QEmbed[Embed_Question]
  QEmbed --> Search[Qdrant_TopK]
  Search --> Filter[Filter_by_User_and_Doc]
  Filter --> Context[Assemble_Context]
  Context --> Gen[LLM_Generate]
  Gen --> Cite[Attach_Citations]
  Cite --> Respond[Return_Answer]
```

**Grounding rule:** Prompt instructs the model to answer only from provided snippets; if insufficient, say so.

## Out of scope until later

| Workflow | Version |
|----------|---------|
| Hybrid BM25 + vector + rerank | V1.x+ |
| OCR pipeline | later |
| SQL agent tool loop | V2 |
| Multi-agent LangGraph planner | V6 |

## Evaluation (lightweight V1)

- Manual fixture PDF with known facts
- Assert citation document IDs present
- Spot-check refusal when question is off-document
