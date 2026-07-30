"""Agent observability / execution tracing."""

from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models import AgentTrace, AgentTraceStep, User


def _token_estimate(text: str | None) -> int:
    if not text:
        return 0
    return max(1, len(text.split()))


class TraceRecorder:
    def __init__(self, db: Session, user: User, request_text: str, *, model_family: str | None = None):
        self.db = db
        self.user = user
        self.started = time.perf_counter()
        self.trace = AgentTrace(
            user_id=user.id,
            request_text=request_text,
            model_family=model_family,
            status="running",
        )
        db.add(self.trace)
        db.commit()
        db.refresh(self.trace)
        self._index = 0

    def add_step(
        self,
        *,
        agent_name: str,
        tool_name: str | None = None,
        prompt: str | None = None,
        output: str | None = None,
        model_name: str | None = None,
        latency_ms: int = 0,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> AgentTraceStep:
        step = AgentTraceStep(
            trace_id=self.trace.id,
            step_index=self._index,
            agent_name=agent_name,
            tool_name=tool_name,
            prompt=prompt,
            output=(output or "")[:8000],
            model_name=model_name,
            latency_ms=latency_ms,
            token_estimate=_token_estimate(prompt) + _token_estimate(output),
            error_message=error_message,
            metadata_json=metadata or {},
        )
        self._index += 1
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def timed_step(self, agent_name: str, fn, **kwargs):
        start = time.perf_counter()
        error = None
        output = None
        try:
            result = fn()
            output = result if isinstance(result, str) else str(result)[:4000]
            return result
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            raise
        finally:
            latency = int((time.perf_counter() - start) * 1000)
            self.add_step(
                agent_name=agent_name,
                tool_name=kwargs.get("tool_name"),
                prompt=kwargs.get("prompt"),
                output=output if error is None else None,
                model_name=kwargs.get("model_name"),
                latency_ms=latency,
                error_message=error,
                metadata=kwargs.get("metadata"),
            )

    def finish(
        self,
        *,
        final_response: str | None = None,
        run_id: UUID | None = None,
        error: str | None = None,
    ) -> AgentTrace:
        self.trace.total_latency_ms = int((time.perf_counter() - self.started) * 1000)
        steps = list(
            self.db.scalars(
                select(AgentTraceStep).where(AgentTraceStep.trace_id == self.trace.id)
            ).all()
        )
        self.trace.total_tokens = sum(s.token_estimate for s in steps)
        self.trace.final_response = final_response
        self.trace.run_id = run_id
        self.trace.status = "failed" if error else "completed"
        self.trace.error_message = error
        self.db.add(self.trace)
        self.db.commit()
        self.db.refresh(self.trace)
        return self.trace


def list_traces(db: Session, user: User, *, limit: int = 50) -> list[AgentTrace]:
    return list(
        db.scalars(
            select(AgentTrace)
            .where(AgentTrace.user_id == user.id)
            .order_by(AgentTrace.created_at.desc())
            .limit(limit)
        ).all()
    )


def get_trace(db: Session, user: User, trace_id: UUID) -> AgentTrace:
    trace = db.scalar(
        select(AgentTrace)
        .where(AgentTrace.id == trace_id, AgentTrace.user_id == user.id)
        .options(selectinload(AgentTrace.steps))
    )
    if not trace:
        raise NotFoundError("Trace not found")
    return trace


def trace_to_dict(trace: AgentTrace) -> dict:
    steps = sorted(trace.steps, key=lambda s: s.step_index) if trace.steps else []
    return {
        "id": str(trace.id),
        "run_id": str(trace.run_id) if trace.run_id else None,
        "request_text": trace.request_text,
        "status": trace.status,
        "model_family": trace.model_family,
        "total_latency_ms": trace.total_latency_ms,
        "total_tokens": trace.total_tokens,
        "error_message": trace.error_message,
        "final_response": trace.final_response,
        "created_at": trace.created_at.isoformat() if trace.created_at else None,
        "steps": [
            {
                "step_index": s.step_index,
                "agent_name": s.agent_name,
                "tool_name": s.tool_name,
                "prompt": s.prompt,
                "output": s.output,
                "model_name": s.model_name,
                "latency_ms": s.latency_ms,
                "token_estimate": s.token_estimate,
                "error_message": s.error_message,
                "metadata": s.metadata_json or {},
            }
            for s in steps
        ],
    }
