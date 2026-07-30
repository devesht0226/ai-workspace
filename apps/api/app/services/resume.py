"""Resume Analyzer: parse, skills, ATS checks, JD match."""

from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.validation import ALLOWED_RESUME, validate_upload
from app.models import JobStatus, ResumeAnalysis, UsageEvent, User
from app.providers.llm import ChatMessage, get_llm_provider

SKILL_LEXICON = {
    "python",
    "fastapi",
    "django",
    "flask",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node",
    "sql",
    "postgresql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "langchain",
    "rag",
    "machine learning",
    "git",
    "ci/cd",
    "pytest",
    "graphql",
}


def _extract_text(filename: str, data: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(BytesIO(data))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts).strip()
        if not text:
            raise ValidationAppError("No extractable text in resume PDF")
        return text
    if lower.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace")
    # Treat unknown as utf-8 text
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationAppError("Unsupported resume format; use PDF or TXT") from exc


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    found = [skill for skill in sorted(SKILL_LEXICON) if skill in lowered]
    return found


def _ats_checks(text: str) -> dict:
    checks = {
        "has_email": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)),
        "has_phone": bool(re.search(r"\+?\d[\d\s()-]{7,}\d", text)),
        "has_sections": any(
            h in text.lower() for h in ("experience", "education", "skills", "projects")
        ),
        "length_ok": 200 <= len(text) <= 20000,
        "has_action_verbs": any(
            v in text.lower() for v in ("built", "led", "designed", "implemented", "improved")
        ),
    }
    score = int(100 * (sum(1 for v in checks.values() if v) / len(checks)))
    return {"checks": checks, "score": score}


def grammar_suggestions(resume_text: str) -> list[str]:
    """Return practical grammar edits, with a deterministic fallback."""
    fallback = [
        "Use consistent verb tense within each role.",
        "Start experience bullets with a strong action verb.",
        "Replace first-person phrasing with concise achievement statements.",
    ]
    settings = get_settings()
    if settings.environment == "test" or settings.llm_provider == "fake":
        return fallback
    try:
        response = get_llm_provider().chat(
            [
                ChatMessage(
                    role="user",
                    content=(
                        "Review this resume for grammar and clarity. Return up to five concise "
                        "bullet suggestions, without rewriting facts.\n\n"
                        f"{resume_text[:6000]}"
                    ),
                )
            ]
        )
        suggestions = [line.strip("-• ").strip() for line in response.splitlines() if line.strip()]
        return suggestions[:5] or fallback
    except Exception:
        return fallback


def cover_letter_draft(job_description: str, resume_text: str) -> str:
    """Draft a factual, editable cover letter from the resume and job description."""
    settings = get_settings()
    if settings.environment == "test" or settings.llm_provider == "fake":
        return (
            "Dear Hiring Manager,\n\n"
            "I am excited to apply for this opportunity. My experience and skills align with "
            "the role's requirements, and I would welcome the chance to discuss my background.\n\n"
            "Sincerely,\nCandidate"
        )
    try:
        return get_llm_provider().chat(
            [
                ChatMessage(
                    role="user",
                    content=(
                        "Write a concise, professional cover-letter draft using only the provided "
                        "resume facts. Do not invent achievements.\n\n"
                        f"JOB DESCRIPTION:\n{job_description[:4000]}\n\n"
                        f"RESUME:\n{resume_text[:6000]}"
                    ),
                )
            ]
        )
    except Exception:
        return (
            "Dear Hiring Manager,\n\n"
            "I am interested in this role and believe my documented experience is relevant to "
            "your needs. I would value the opportunity to discuss my qualifications.\n\n"
            "Sincerely,\nCandidate"
        )


def analyze_resume(
    db: Session,
    user: User,
    *,
    filename: str,
    data: bytes,
    job_description: str | None = None,
) -> ResumeAnalysis:
    validate_upload(filename=filename, data=data, allowed_extensions=ALLOWED_RESUME)
    text = _extract_text(filename, data)
    skills = _extract_skills(text)
    ats = _ats_checks(text)
    grammar = grammar_suggestions(text)
    jd = (job_description or "").strip()
    matched: list[str] = []
    missing: list[str] = []
    if jd:
        jd_skills = _extract_skills(jd)
        matched = [s for s in jd_skills if s in skills]
        missing = [s for s in jd_skills if s not in skills]

    llm = get_llm_provider()
    if get_settings().environment == "test" or get_settings().llm_provider == "fake":
        suggestions = [
            "Quantify impact with metrics where possible",
            "Mirror keywords from the job description",
            "Keep formatting ATS-simple (no tables/columns)",
        ]
        summary = "Resume analyzed with rule-based ATS checks and skill extraction."
    else:
        prompt = (
            "Provide concise resume improvement suggestions as a bullet list.\n"
            f"RESUME:\n{text[:4000]}\n\nJOB DESCRIPTION:\n{jd[:2000] or 'N/A'}"
        )
        summary = llm.chat([ChatMessage(role="user", content=prompt)])
        suggestions = [line.strip("-• ") for line in summary.splitlines() if line.strip()][:8]

    match_score = None
    if jd:
        denom = max(len(matched) + len(missing), 1)
        match_score = int(100 * len(matched) / denom)

    row = ResumeAnalysis(
        user_id=user.id,
        filename=filename,
        resume_text=text,
        job_description=jd or None,
        status=JobStatus.ready,
        result_json={
            "skills": skills,
            "ats": ats,
            "job_match": {
                "matched_skills": matched,
                "missing_skills": missing,
                "score": match_score,
            },
            "suggestions": suggestions,
            "grammar_suggestions": grammar,
            "summary": summary,
        },
    )
    db.add(row)
    db.add(
        UsageEvent(
            user_id=user.id,
            event_type="resume_analyze",
            model_name=get_settings().ollama_chat_model,
            metadata_json={"filename": filename},
        )
    )
    db.commit()
    db.refresh(row)
    return row


def list_analyses(db: Session, user: User) -> list[ResumeAnalysis]:
    return list(
        db.scalars(
            select(ResumeAnalysis)
            .where(ResumeAnalysis.user_id == user.id)
            .order_by(ResumeAnalysis.created_at.desc())
        ).all()
    )


def get_analysis(db: Session, user: User, analysis_id) -> ResumeAnalysis:
    row = db.scalar(
        select(ResumeAnalysis).where(
            ResumeAnalysis.id == analysis_id, ResumeAnalysis.user_id == user.id
        )
    )
    if not row:
        raise NotFoundError("Resume analysis not found")
    return row
