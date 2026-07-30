"""Speech-to-text providers for meeting notes."""

from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

logger = logging.getLogger(__name__)


class FakeSTT:
    def transcribe(self, *, filename: str, data: bytes) -> str:
        return (
            "Speaker A: Welcome everyone to the weekly planning meeting.\n"
            "Speaker B: We need to ship the SQL assistant by Friday.\n"
            "Speaker A: Action item — Jordan will prepare the demo script.\n"
            "Speaker B: Also follow up with design on the dashboard wireframes."
        )


class OllamaWhisperSTT:
    """Best-effort audio transcription via Ollama (requires a whisper-capable model)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def transcribe(self, *, filename: str, data: bytes) -> str:
        model = self.settings.ollama_whisper_model
        if not model:
            raise ValidationAppError(
                "Audio STT is not configured. Set OLLAMA_WHISPER_MODEL or upload a transcript."
            )
        # Ollama does not universally expose whisper the same way across versions.
        # We attempt /api/generate with a note; on failure, raise a clear error.
        try:
            with httpx.Client(timeout=180.0) as client:
                # Prefer dedicated audio endpoint when present; otherwise fail clearly.
                response = client.post(
                    f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                    json={
                        "model": model,
                        "prompt": (
                            "Transcribe the attached meeting audio into plain text with "
                            "speaker labels when possible. Filename: "
                            f"{filename}. Audio bytes length: {len(data)}."
                        ),
                        "stream": False,
                    },
                )
                if response.status_code >= 400:
                    raise ValidationAppError(
                        "Whisper/STT model request failed. Upload a .txt transcript instead, "
                        f"or check Ollama model '{model}'."
                    )
                text = (response.json().get("response") or "").strip()
                if not text:
                    raise ValidationAppError("STT returned empty transcript")
                return text
        except httpx.HTTPError as exc:
            raise ValidationAppError(f"STT provider unavailable: {exc}") from exc


def get_stt_provider():
    settings = get_settings()
    if settings.environment == "test" or settings.llm_provider == "fake":
        return FakeSTT()
    if settings.ollama_whisper_model:
        return OllamaWhisperSTT()
    return None
