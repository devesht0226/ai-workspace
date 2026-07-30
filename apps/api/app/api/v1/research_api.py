"""Research agent API."""

from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.services import research as research_service

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    model_family: str | None = Field(default=None, max_length=40)


class CompareDocumentsRequest(BaseModel):
    doc_a_id: UUID
    doc_b_id: UUID


@router.post("")
def research(payload: ResearchRequest, db: DbSession, user: CurrentUser) -> dict:
    return research_service.run_research(
        db, user, payload.question, model_family=payload.model_family
    )


@router.post("/compare")
def compare_documents(payload: CompareDocumentsRequest, db: DbSession, user: CurrentUser) -> dict:
    return research_service.compare_documents(db, user, payload.doc_a_id, payload.doc_b_id)


@router.get("/export")
def export_brief(
    brief: str = Query(min_length=1, max_length=50000),
    format: str = Query(default="md", pattern="^(md|docx)$"),
):
    if format == "docx":
        return Response(
            research_service.export_brief_docx(brief),
            media_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            headers={"Content-Disposition": 'attachment; filename="research-brief.docx"'},
        )
    return PlainTextResponse(
        research_service.export_brief_markdown(brief),
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="research-brief.md"'},
    )
