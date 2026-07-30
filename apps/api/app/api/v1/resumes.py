"""Resume analyzer routes."""

from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas import ResumeOut
from app.services import resume as resume_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


class CoverLetterRequest(BaseModel):
    job_description: str = Field(min_length=1, max_length=10000)


def _out(row) -> ResumeOut:
    return ResumeOut(
        id=row.id,
        filename=row.filename,
        status=row.status.value,
        result_json=row.result_json,
        created_at=row.created_at,
    )


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: DbSession, user: CurrentUser) -> list[ResumeOut]:
    return [_out(r) for r in resume_service.list_analyses(db, user)]


@router.post("/analyze", response_model=ResumeOut, status_code=201)
async def analyze(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    job_description: str | None = Form(default=None),
) -> ResumeOut:
    data = await file.read()
    row = resume_service.analyze_resume(
        db,
        user,
        filename=file.filename or "resume.txt",
        data=data,
        job_description=job_description,
    )
    return _out(row)


@router.get("/{analysis_id}", response_model=ResumeOut)
def get_resume(analysis_id: UUID, db: DbSession, user: CurrentUser) -> ResumeOut:
    return _out(resume_service.get_analysis(db, user, analysis_id))


@router.post("/{analysis_id}/cover-letter")
def draft_cover_letter(
    analysis_id: UUID, payload: CoverLetterRequest, db: DbSession, user: CurrentUser
) -> dict:
    analysis = resume_service.get_analysis(db, user, analysis_id)
    return {
        "analysis_id": str(analysis.id),
        "cover_letter": resume_service.cover_letter_draft(
            payload.job_description, analysis.resume_text
        ),
    }
