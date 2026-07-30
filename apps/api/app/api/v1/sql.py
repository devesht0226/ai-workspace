"""SQL Assistant routes."""

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas import SQLExecuteRequest, SQLQuestionRequest, SQLTextRequest
from app.services import sql_assistant

router = APIRouter(prefix="/sql", tags=["sql"])


class CSVExportRequest(BaseModel):
    columns: list[str] = Field(min_length=1, max_length=100)
    rows: list[dict] = Field(default_factory=list, max_length=1000)


@router.get("/schema")
def schema(_: CurrentUser) -> dict:
    return sql_assistant.get_schema()


@router.get("/er")
def er_graph(_: CurrentUser) -> dict:
    return sql_assistant.schema_er_graph()


@router.post("/generate")
def generate(payload: SQLQuestionRequest, db: DbSession, user: CurrentUser) -> dict:
    return sql_assistant.generate_sql(db, user, payload.question)


@router.post("/explain")
def explain(payload: SQLTextRequest, db: DbSession, user: CurrentUser) -> dict:
    return sql_assistant.explain_sql(db, user, payload.sql)


@router.post("/optimize")
def optimize(payload: SQLTextRequest, db: DbSession, user: CurrentUser) -> dict:
    return sql_assistant.optimize_sql(db, user, payload.sql)


@router.post("/execute")
def execute(payload: SQLExecuteRequest, db: DbSession, user: CurrentUser) -> dict:
    return sql_assistant.execute_sql(db, user, payload.sql, max_rows=payload.max_rows)


@router.post("/export-csv")
def export_csv(payload: CSVExportRequest, _: CurrentUser) -> Response:
    return Response(
        sql_assistant.export_results_csv(payload.columns, payload.rows),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sql-results.csv"'},
    )
