"""Model router: Llama (Ollama), GPT (OpenAI), Mistral, Hugging Face."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import ProcessingError, ValidationAppError
from app.providers.llm import (
    ChatMessage,
    FakeLLM,
    LLMProvider,
    OllamaLLM,
)


class OpenAICompatibleLLM:
    """OpenAI Chat Completions API (also used by many Mistral gateways)."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        default_model: str,
        label: str = "openai",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.label = label

    def chat(self, messages: list[ChatMessage], *, model: str | None = None) -> str:
        if not self.api_key:
            raise ProcessingError(f"{self.label} API key is not configured")
        model_name = model or self.default_model
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": model_name,
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise ProcessingError(f"{self.label} chat failed: {exc}") from exc

    def stream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> Iterator[str]:
        # Non-streaming fallback for simplicity across providers
        text = self.chat(messages, model=model)
        for word in text.split(" "):
            yield word + " "

    async def astream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> AsyncIterator[str]:
        for token in self.stream_chat(messages, model=model):
            yield token


class HuggingFaceInferenceLLM:
    """Hugging Face Inference API chat-compatible adapter."""

    def __init__(self, *, api_key: str, default_model: str) -> None:
        self.api_key = api_key
        self.default_model = default_model

    def chat(self, messages: list[ChatMessage], *, model: str | None = None) -> str:
        if not self.api_key:
            raise ProcessingError("Hugging Face API key is not configured")
        model_name = model or self.default_model
        prompt = "\n".join(f"{message.role}: {message.content}" for message in messages)
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"https://api-inference.huggingface.co/models/{model_name}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"inputs": prompt, "parameters": {"return_full_text": False}},
                )
                response.raise_for_status()
                data = response.json()
            if isinstance(data, list) and data:
                text = data[0].get("generated_text", "")
            elif isinstance(data, dict):
                text = data.get("generated_text", "")
            else:
                text = ""
            if not text:
                raise KeyError("generated_text")
            return str(text)
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ProcessingError(f"Hugging Face chat failed: {exc}") from exc

    def stream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> Iterator[str]:
        yield from (word + " " for word in self.chat(messages, model=model).split(" "))

    async def astream_chat(
        self, messages: list[ChatMessage], *, model: str | None = None
    ) -> AsyncIterator[str]:
        for token in self.stream_chat(messages, model=model):
            yield token


class ModelRouter:
    """Routes requests to llama / gpt / mistral / huggingface backends."""

    FAMILY_ALIASES = {
        "llama": "llama",
        "ollama": "llama",
        "gpt": "gpt",
        "openai": "gpt",
        "mistral": "mistral",
        "huggingface": "huggingface",
        "hf": "huggingface",
        "auto": "auto",
    }

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._backends: dict[str, LLMProvider] = {}
        if self.settings.environment == "test" or self.settings.llm_provider == "fake":
            fake = FakeLLM()
            self._backends = {
                "llama": fake,
                "gpt": fake,
                "mistral": fake,
                "huggingface": fake,
            }
            return

        self._backends["llama"] = OllamaLLM(self.settings)
        if self.settings.openai_api_key:
            self._backends["gpt"] = OpenAICompatibleLLM(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
                default_model=self.settings.openai_chat_model,
                label="gpt",
            )
        if self.settings.mistral_api_key:
            self._backends["mistral"] = OpenAICompatibleLLM(
                api_key=self.settings.mistral_api_key,
                base_url=self.settings.mistral_base_url,
                default_model=self.settings.mistral_chat_model,
                label="mistral",
            )
        if self.settings.huggingface_api_key:
            self._backends["huggingface"] = HuggingFaceInferenceLLM(
                api_key=self.settings.huggingface_api_key,
                default_model=self.settings.huggingface_model,
            )

    def available(self) -> list[dict]:
        catalog = [
            {
                "family": "llama",
                "provider": "ollama",
                "model": self.settings.ollama_chat_model,
                "available": "llama" in self._backends,
            },
            {
                "family": "gpt",
                "provider": "openai",
                "model": self.settings.openai_chat_model,
                "available": "gpt" in self._backends,
            },
            {
                "family": "mistral",
                "provider": "mistral",
                "model": self.settings.mistral_chat_model,
                "available": "mistral" in self._backends,
            },
            {
                "family": "huggingface",
                "provider": "huggingface",
                "model": self.settings.huggingface_model,
                "available": "huggingface" in self._backends,
            },
        ]
        return catalog

    def resolve_family(self, family: str | None = None) -> str:
        raw = (family if family is not None else "auto").lower()
        return self.FAMILY_ALIASES.get(raw, raw)

    def get(self, family: str | None = None) -> tuple[str, LLMProvider]:
        key = self.resolve_family(family)
        if key == "auto":
            # Prefer the configured default provider; never pick local Ollama first in cloud.
            provider = (self.settings.llm_provider or "").lower()
            if provider in {"openai", "gpt"}:
                order = ("gpt", "mistral", "huggingface", "llama")
            elif provider in {"mistral"}:
                order = ("mistral", "gpt", "huggingface", "llama")
            elif provider in {"huggingface", "hf"}:
                order = ("huggingface", "gpt", "mistral", "llama")
            else:
                # Local / ollama-first demos
                order = ("llama", "gpt", "mistral", "huggingface")
            for candidate in order:
                if candidate in self._backends:
                    return candidate, self._backends[candidate]
        backend = self._backends.get(key)
        if backend is None:
            # Fall back to any configured cloud provider before local Ollama
            for candidate in ("gpt", "mistral", "huggingface", "llama"):
                if candidate in self._backends:
                    return candidate, self._backends[candidate]
            raise ValidationAppError(
                f"Model family '{key}' is not configured. Set API keys or use llama/ollama."
            )
        return key, backend

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        family: str | None = None,
        model: str | None = None,
    ) -> dict:
        if self.resolve_family(family) == "auto":
            errors: list[str] = []
            provider = (self.settings.llm_provider or "").lower()
            if provider in {"openai", "gpt"}:
                order = ("gpt", "mistral", "huggingface", "llama")
            elif provider in {"mistral"}:
                order = ("mistral", "gpt", "huggingface", "llama")
            elif provider in {"huggingface", "hf"}:
                order = ("huggingface", "gpt", "mistral", "llama")
            else:
                order = ("llama", "gpt", "mistral", "huggingface")
            for candidate in order:
                backend = self._backends.get(candidate)
                if backend is None:
                    continue
                try:
                    return {"family": candidate, "content": backend.chat(messages, model=model)}
                except ProcessingError as exc:
                    errors.append(str(exc))
            raise ProcessingError("No auto-routed model succeeded: " + "; ".join(errors))
        resolved, backend = self.get(family)
        return {"family": resolved, "content": backend.chat(messages, model=model)}


_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def reset_model_router() -> None:
    global _router
    _router = None
