"""Code review routes."""

from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.schemas import CodeReviewOut
from app.services import code_review as code_service

router = APIRouter(prefix="/code", tags=["code"])


def _out(row) -> CodeReviewOut:
    return CodeReviewOut(
        id=row.id,
        title=row.title,
        status=row.status.value,
        result_json=row.result_json,
        error_message=row.error_message,
        created_at=row.created_at,
    )


@router.get("/reviews", response_model=list[CodeReviewOut])
def list_reviews(db: DbSession, user: CurrentUser) -> list[CodeReviewOut]:
    return [_out(r) for r in code_service.list_reviews(db, user)]


@router.post("/reviews", response_model=CodeReviewOut, status_code=201)
async def create_review(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
) -> CodeReviewOut:
    data = await file.read()
    row = code_service.create_review(
        db, user, filename=file.filename or "upload.zip", data=data, title=title
    )
    return _out(row)


@router.get("/reviews/{review_id}", response_model=CodeReviewOut)
def get_review(review_id: UUID, db: DbSession, user: CurrentUser) -> CodeReviewOut:
    return _out(code_service.get_review(db, user, review_id))
