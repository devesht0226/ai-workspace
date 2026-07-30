"""Document and RAG routes."""

from uuid import UUID

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import ValidationAppError
from app.schemas import (
    DocumentCollectionCreate,
    DocumentCollectionOut,
    DocumentOut,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services import documents as document_service

router = APIRouter(tags=["documents"])


def _document_out(document: object) -> DocumentOut:
    return DocumentOut.model_validate(document)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    db: DbSession,
    user: CurrentUser,
    collection_id: UUID | None = Query(default=None),
) -> list[DocumentOut]:
    return [_document_out(d) for d in document_service.list_documents(db, user, collection_id=collection_id)]


@router.post("/document-collections", response_model=DocumentCollectionOut, status_code=201)
def create_collection(
    payload: DocumentCollectionCreate, db: DbSession, user: CurrentUser
) -> DocumentCollectionOut:
    return document_service.create_collection(
        db, user, name=payload.name, description=payload.description
    )


@router.get("/document-collections", response_model=list[DocumentCollectionOut])
def list_collections(db: DbSession, user: CurrentUser) -> list[DocumentCollectionOut]:
    return document_service.list_collections(db, user)


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    collection_id: UUID | None = Form(default=None),
) -> DocumentOut:
    if not file.filename:
        raise ValidationAppError("Filename is required")
    data = await file.read()
    doc = document_service.ingest_document(
        db,
        user,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        data=data,
        collection_id=collection_id,
    )
    return _document_out(doc)


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: UUID, db: DbSession, user: CurrentUser) -> DocumentOut:
    return _document_out(document_service.get_document(db, user, document_id))


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: DbSession, user: CurrentUser) -> None:
    document_service.delete_document(db, user, document_id)


@router.post("/documents/{document_id}/query", response_model=RAGQueryResponse)
def query_document(
    document_id: UUID,
    payload: RAGQueryRequest,
    db: DbSession,
    user: CurrentUser,
) -> RAGQueryResponse:
    return document_service.query_documents(
        db,
        user,
        question=payload.question,
        top_k=payload.top_k,
        document_id=document_id,
    )


@router.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(
    payload: RAGQueryRequest,
    db: DbSession,
    user: CurrentUser,
    collection_id: UUID | None = Query(default=None),
) -> RAGQueryResponse:
    return document_service.query_documents(
        db,
        user,
        question=payload.question,
        top_k=payload.top_k,
        document_id=payload.document_id,
        collection_id=collection_id or payload.collection_id,
    )
