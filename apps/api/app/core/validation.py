"""Shared upload validation helpers."""

from __future__ import annotations

from pathlib import PurePosixPath

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError

ALLOWED_PDF = {".pdf"}
ALLOWED_DOCS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html", ".htm"}
ALLOWED_CODE = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".md", ".txt", ".zip"}
ALLOWED_RESUME = {".pdf", ".txt", ".md"}
ALLOWED_MEETING = {
    ".txt",
    ".md",
    ".vtt",
    ".srt",
    ".wav",
    ".mp3",
    ".m4a",
    ".webm",
    ".ogg",
}


def validate_upload(
    *,
    filename: str,
    data: bytes,
    allowed_extensions: set[str],
    max_mb: int | None = None,
) -> None:
    settings = get_settings()
    limit_mb = max_mb if max_mb is not None else settings.max_upload_mb
    if not filename or filename.strip() in {".", ".."}:
        raise ValidationAppError("Filename is required")
    name = PurePosixPath(filename).name
    suffix = PurePosixPath(name).suffix.lower()
    if suffix not in allowed_extensions:
        raise ValidationAppError(
            f"Unsupported file type '{suffix or '(none)'}'. Allowed: {', '.join(sorted(allowed_extensions))}"
        )
    if ".." in PurePosixPath(filename).parts:
        raise ValidationAppError("Invalid filename path")
    max_bytes = limit_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise ValidationAppError(f"File exceeds {limit_mb}MB limit")
    if len(data) == 0:
        raise ValidationAppError("Uploaded file is empty")
