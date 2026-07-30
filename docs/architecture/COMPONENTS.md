# Component Diagram

## Backend components (V1)

```mermaid
flowchart TB
  subgraph presentation [API_Layer]
    Routers[APIRouter_v1]
    Deps[Dependencies_Auth_DB]
  end
  subgraph domain [Services]
    AuthSvc[AuthService]
    ChatSvc[ChatService]
    DocSvc[DocumentService]
    RagSvc[RAGService]
  end
  subgraph providers [Providers]
    LLM[LLMProvider]
    Embed[EmbeddingProvider]
    OllamaAdapter[OllamaAdapter]
    CloudAdapter[CloudAdapter_optional]
  end
  subgraph infra [Infrastructure]
    DBSession[SQLAlchemy_Session]
    QdrantClient[QdrantClient]
    RedisClient[RedisClient]
    Storage[LocalFileStorage]
  end

  Routers --> Deps
  Routers --> AuthSvc
  Routers --> ChatSvc
  Routers --> DocSvc
  Routers --> RagSvc
  AuthSvc --> DBSession
  ChatSvc --> DBSession
  ChatSvc --> LLM
  DocSvc --> DBSession
  DocSvc --> Storage
  DocSvc --> Embed
  DocSvc --> QdrantClient
  RagSvc --> DBSession
  RagSvc --> Embed
  RagSvc --> QdrantClient
  RagSvc --> LLM
  LLM --> OllamaAdapter
  LLM --> CloudAdapter
  Embed --> OllamaAdapter
  Embed --> CloudAdapter
  Deps --> RedisClient
```

## Frontend components (V1)

```mermaid
flowchart LR
  subgraph pages [App_Router_Pages]
    Login[Login_Register]
    ChatPage[Chat]
    DocsPage[Documents]
  end
  subgraph ui [UI]
    ChatPanel[ChatPanel_Stream]
    Upload[UploadDropzone]
    CiteList[CitationList]
  end
  subgraph lib [Client_Lib]
    ApiClient[ApiClient]
    AuthStore[AuthTokenHelpers]
  end

  Login --> ApiClient
  ChatPage --> ChatPanel
  ChatPage --> ApiClient
  DocsPage --> Upload
  DocsPage --> CiteList
  DocsPage --> ApiClient
  ChatPanel --> ApiClient
  ApiClient --> AuthStore
```

## Trust boundaries

- Browser never talks to PostgreSQL, Qdrant, or Ollama directly.
- All AI and file processing goes through the API.
- Document and chat queries are scoped by authenticated `user_id`.
