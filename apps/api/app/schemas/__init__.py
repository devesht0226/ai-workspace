"""Pydantic request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    email_verified: bool = False
    avatar_url: str | None = None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


class ChatCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    metadata_json: dict | None = Field(default=None, validation_alias="metadata_json")
    created_at: datetime


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    model_name: str
    provider: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetail(ChatSessionOut):
    messages: list[MessageOut] = []


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20000)
    stream: bool = True


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    content_type: str
    status: str
    page_count: int | None
    error_message: str | None = None
    collection_id: UUID | None = None
    content_hash: str | None = None
    version: int = 1
    parent_document_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class DocumentCollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)


class DocumentCollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime


class CitationOut(BaseModel):
    document_id: UUID
    filename: str
    chunk_id: UUID
    page_number: int | None
    snippet: str
    score: float | None = None


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: UUID | None = None
    collection_id: UUID | None = None


class RAGQueryResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    eval_metrics: dict | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


# --- V2 SQL ---
class SQLQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SQLTextRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=10000)


class SQLExecuteRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=10000)
    max_rows: int = Field(default=100, ge=1, le=500)


# --- V3 Code ---
class CodeReviewOut(BaseModel):
    id: UUID
    title: str
    status: str
    result_json: dict | None = None
    error_message: str | None = None
    created_at: datetime


# --- V4 Resume ---
class ResumeOut(BaseModel):
    id: UUID
    filename: str
    status: str
    result_json: dict | None = None
    created_at: datetime


# --- V5 Meetings ---
class MeetingOut(BaseModel):
    id: UUID
    title: str
    filename: str | None
    status: str
    transcript: str | None = None
    summary: str | None = None
    action_items_json: list | None = None
    decisions_json: list | None = None
    follow_up_email: str | None = None
    error_message: str | None = None
    created_at: datetime


# --- V6 Agents ---
class AgentRunRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    model_family: str | None = Field(default=None, max_length=40)


class AgentRunOut(BaseModel):
    id: UUID
    task: str
    status: str
    plan_json: dict | None = None
    steps_json: list | None = None
    report: str | None = None
    evaluation_json: dict | None = None
    created_at: datetime
