"""Multi-agent orchestration routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas import AgentRunOut, AgentRunRequest
from app.services import agents as agent_service

router = APIRouter(prefix="/agents", tags=["agents"])


def _out(row) -> AgentRunOut:
    return AgentRunOut(
        id=row.id,
        task=row.task,
        status=row.status.value,
        plan_json=row.plan_json,
        steps_json=row.steps_json,
        report=row.report,
        evaluation_json=row.evaluation_json,
        created_at=row.created_at,
    )


@router.get("/runs", response_model=list[AgentRunOut])
def list_runs(db: DbSession, user: CurrentUser) -> list[AgentRunOut]:
    return [_out(r) for r in agent_service.list_runs(db, user)]


@router.post("/runs", response_model=AgentRunOut, status_code=201)
def run_agents(payload: AgentRunRequest, db: DbSession, user: CurrentUser) -> AgentRunOut:
    return _out(
        agent_service.run_agents(
            db, user, payload.task, model_family=payload.model_family
        )
    )


@router.get("/runs/{run_id}", response_model=AgentRunOut)
def get_run(run_id: UUID, db: DbSession, user: CurrentUser) -> AgentRunOut:
    return _out(agent_service.get_run(db, user, run_id))
