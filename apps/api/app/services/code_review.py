"""Code Review Assistant: static heuristics + LLM analysis."""

from __future__ import annotations

import ast
import io
import re
import zipfile
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.validation import ALLOWED_CODE, validate_upload
from app.models import CodeReview, JobStatus, UsageEvent, User
from app.providers.llm import ChatMessage, get_llm_provider

TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".md", ".txt"}
_DECISION_KEYWORDS = re.compile(r"\b(if|for|while|case|catch)\b|&&|\|\|", re.IGNORECASE)


def _read_upload_files(filename: str, data: bytes) -> dict[str, str]:
    files: dict[str, str] = {}
    lower = filename.lower()
    if lower.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    path = PurePosixPath(info.filename)
                    if path.suffix.lower() not in TEXT_EXTENSIONS:
                        continue
                    if info.file_size > 200_000:
                        continue
                    raw = zf.read(info)
                    try:
                        files[str(path)] = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        continue
        except zipfile.BadZipFile as exc:
            raise ValidationAppError("Invalid ZIP archive") from exc
    else:
        suffix = PurePosixPath(filename).suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            raise ValidationAppError("Upload a .zip or a text/source file")
        files[filename] = data.decode("utf-8", errors="replace")
    if not files:
        raise ValidationAppError("No readable source files found")
    if len(files) > 40:
        # Keep analysis bounded
        files = dict(list(files.items())[:40])
    return files


def _python_findings(path: str, source: str) -> list[dict]:
    findings: list[dict] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        findings.append(
            {
                "file": path,
                "severity": "high",
                "category": "bug",
                "message": f"Syntax error: {exc.msg}",
                "line": exc.lineno,
            }
        )
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(
                {
                    "file": path,
                    "severity": "medium",
                    "category": "bug",
                    "message": "Bare except clause swallows all errors",
                    "line": getattr(node, "lineno", None),
                }
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "eval"
        ):
            findings.append(
                {
                    "file": path,
                    "severity": "high",
                    "category": "security",
                    "message": "Use of eval() is dangerous",
                    "line": getattr(node, "lineno", None),
                }
            )
    if "TODO" in source or "FIXME" in source:
        findings.append(
            {
                "file": path,
                "severity": "low",
                "category": "maintainability",
                "message": "Contains TODO/FIXME markers",
                "line": None,
            }
        )
    return findings


def _heuristic_findings(files: dict[str, str]) -> list[dict]:
    findings: list[dict] = []
    for path, source in files.items():
        if path.endswith(".py"):
            findings.extend(_python_findings(path, source))
        if "password =" in source.lower() or "api_key =" in source.lower():
            findings.append(
                {
                    "file": path,
                    "severity": "high",
                    "category": "security",
                    "message": "Possible hard-coded secret",
                    "line": None,
                }
            )
    return findings


def _complexity_analysis(files: dict[str, str]) -> dict[str, dict[str, int]]:
    """Estimate per-file cyclomatic complexity from branching tokens."""
    return {
        path: {
            "decision_points": len(_DECISION_KEYWORDS.findall(source)),
            "cyclomatic_estimate": 1 + len(_DECISION_KEYWORDS.findall(source)),
        }
        for path, source in files.items()
    }


def create_review(
    db: Session, user: User, *, filename: str, data: bytes, title: str | None = None
) -> CodeReview:
    validate_upload(filename=filename, data=data, allowed_extensions=ALLOWED_CODE)
    files = _read_upload_files(filename, data)
    review = CodeReview(
        user_id=user.id,
        title=title or f"Review: {filename}",
        status=JobStatus.processing,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    findings = _heuristic_findings(files)
    complexity = _complexity_analysis(files)
    llm = get_llm_provider()
    sample = "\n\n".join(f"FILE: {p}\n{content[:1500]}" for p, content in list(files.items())[:5])
    if get_settings().environment == "test" or get_settings().llm_provider == "fake":
        refactor = ["Extract duplicated logic into helpers", "Add type hints and docstrings"]
        docs = "Module overview: uploaded sources for automated review."
        tests = "def test_smoke():\n    assert True\n"
        summary = f"Analyzed {len(files)} files with {len(findings)} heuristic findings."
    else:
        analysis = llm.chat(
            [
                ChatMessage(
                    role="user",
                    content=(
                        "Perform a concise code review. Return sections: SUMMARY, REFACTOR, DOCS, TESTS.\n\n"
                        f"{sample}"
                    ),
                )
            ]
        )
        summary = analysis
        refactor = ["See LLM summary for refactor opportunities"]
        docs = analysis
        tests = "Generated tests should cover critical paths identified in the review."

    review.result_json = {
        "files_analyzed": list(files.keys()),
        "findings": findings,
        "summary": summary,
        "refactoring_suggestions": refactor,
        "documentation": docs,
        "unit_test_suggestions": tests,
        "complexity": complexity,
    }
    review.status = JobStatus.ready
    db.add(review)
    db.add(
        UsageEvent(
            user_id=user.id,
            event_type="code_review",
            model_name=get_settings().ollama_chat_model,
            metadata_json={"review_id": str(review.id), "files": len(files)},
        )
    )
    db.commit()
    db.refresh(review)
    return review


def list_reviews(db: Session, user: User) -> list[CodeReview]:
    return list(
        db.scalars(
            select(CodeReview)
            .where(CodeReview.user_id == user.id)
            .order_by(CodeReview.created_at.desc())
        ).all()
    )


def get_review(db: Session, user: User, review_id) -> CodeReview:
    review = db.scalar(
        select(CodeReview).where(CodeReview.id == review_id, CodeReview.user_id == user.id)
    )
    if not review:
        raise NotFoundError("Code review not found")
    return review
