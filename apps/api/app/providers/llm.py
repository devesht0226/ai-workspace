"""LLM / embedding provider abstractions."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import ProcessingError


@dataclass
class ChatMessage:
    role: str
    content: str


class LLMProvider(Protocol):
    def chat(self, messages: list[ChatMessage], *, model: str | None = None) -> str: ...

    def stream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> Iterator[str]: ...

    async def astream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> AsyncIterator[str]: ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]: ...

    @property
    def dimensions(self) -> int: ...


class OllamaLLM:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")

    def chat(self, messages: list[ChatMessage], *, model: str | None = None) -> str:
        model_name = model or self.settings.ollama_chat_model
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "stream": False,
                    },
                )
                if response.status_code == 404:
                    detail = ""
                    try:
                        detail = response.json().get("error", "")
                    except Exception:  # noqa: BLE001
                        detail = response.text
                    raise ProcessingError(
                        f"Ollama model '{model_name}' not found ({detail or '404'}). "
                        f"Pull it with `ollama pull {model_name}` or set OLLAMA_CHAT_MODEL."
                    )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except httpx.HTTPError as exc:
            raise ProcessingError(f"Ollama chat failed: {exc}") from exc

    def stream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> Iterator[str]:
        model_name = model or self.settings.ollama_chat_model
        try:
            with httpx.Client(timeout=None) as client:
                with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        import json

                        payload = json.loads(line)
                        if payload.get("done"):
                            break
                        token = payload.get("message", {}).get("content")
                        if token:
                            yield token
        except httpx.HTTPError as exc:
            raise ProcessingError(f"Ollama stream failed: {exc}") from exc

    async def astream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> AsyncIterator[str]:
        model_name = model or self.settings.ollama_chat_model
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model_name,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        import json

                        payload = json.loads(line)
                        if payload.get("done"):
                            break
                        token = payload.get("message", {}).get("content")
                        if token:
                            yield token
        except httpx.HTTPError as exc:
            raise ProcessingError(f"Ollama stream failed: {exc}") from exc


class OllamaEmbeddings:
    def __init__(self, settings: Settings | None = None, dimensions: int = 768) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        model_name = model or self.settings.ollama_embed_model
        vectors: list[list[float]] = []
        try:
            with httpx.Client(timeout=120.0) as client:
                for text in texts:
                    response = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": model_name, "prompt": text},
                    )
                    response.raise_for_status()
                    embedding = response.json().get("embedding")
                    if not embedding:
                        raise ProcessingError("Empty embedding from Ollama")
                    vectors.append(embedding)
                    self._dimensions = len(embedding)
        except httpx.HTTPError as exc:
            raise ProcessingError(f"Ollama embeddings failed: {exc}") from exc
        return vectors


class FakeLLM:
    """Deterministic provider for tests."""

    def chat(self, messages: list[ChatMessage], *, model: str | None = None) -> str:
        last = messages[-1].content if messages else ""
        return f"Echo: {last}"

    def stream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> Iterator[str]:
        text = self.chat(messages, model=model)
        for word in text.split(" "):
            yield word + " "

    async def astream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> AsyncIterator[str]:
        for token in self.stream_chat(messages, model=model):
            yield token


class FakeEmbeddings:
    def __init__(self, dimensions: int = 8) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = sum(ord(c) for c in text) % 97
            vectors.append([((seed + i) % 13) / 13.0 for i in range(self._dimensions)])
        return vectors


def get_llm_provider(family: str | None = None) -> LLMProvider:
    settings = get_settings()
    if settings.environment == "test" or settings.llm_provider == "fake":
        return FakeLLM()
    from app.providers.router import get_model_router

    _, backend = get_model_router().get(family)
    return backend


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.environment == "test" or settings.llm_provider == "fake":
        return FakeEmbeddings()
    if settings.llm_provider == "ollama":
        return OllamaEmbeddings(settings)
    raise ProcessingError(f"Unsupported embedding provider: {settings.llm_provider}")
