"""Multi-agent orchestration with RAG/SQL/Code/Research/Meeting specialists."""

from __future__ import annotations

import time
from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AgentRun, JobStatus, UsageEvent, User
from app.providers.llm import ChatMessage, get_llm_provider
from app.services import documents as document_service
from app.services import knowledge_graph as kg
from app.services import meetings as meeting_service
from app.services import memory as memory_service
from app.services import prompts as prompt_service
from app.services import research as research_service
from app.services import sql_assistant
from app.services.tracing import TraceRecorder


class AgentState(TypedDict, total=False):
    task: str
    plan: dict[str, Any]
    steps: list[dict[str, Any]]
    report: str
    evaluation: dict[str, Any]


def _planner(task: str) -> dict[str, Any]:
    lowered = task.lower()
    agents: list[str] = []
    if any(k in lowered for k in ("sql", "query", "database", "revenue", "customers")):
        agents.append("sql")
    if any(k in lowered for k in ("document", "pdf", "rag", "cite", "knowledge", "vector")):
        agents.append("retrieval")
    if any(k in lowered for k in ("research", "investigate", "brief", "compare", "graph")):
        agents.append("research")
    if any(k in lowered for k in ("code", "review", "refactor", "bug")):
        agents.append("code")
    if any(k in lowered for k in ("meeting", "notes", "action item", "transcript")):
        agents.append("meeting")
    if not agents:
        agents = ["research", "retrieval"]
    if "report" not in agents:
        agents.append("report")
    agents.append("evaluation")
    return {
        "goal": task,
        "agents": agents,
        "rationale": "Selected specialists from task keywords (AI orchestration layer).",
        "gateway": "fastapi+/nginx",
        "model_router": get_settings().default_model_family,
    }


def _run_sql_agent(db: Session, user: User, task: str) -> dict[str, Any]:
    generated = sql_assistant.generate_sql(db, user, task)
    executed = sql_assistant.execute_sql(db, user, generated["sql"])
    return {
        "agent": "sql",
        "sql": generated["sql"],
        "row_count": executed["row_count"],
        "preview": executed["rows"][:5],
    }


def _run_retrieval_agent(db: Session, user: User, task: str) -> dict[str, Any]:
    result = document_service.query_documents(db, user, question=task, top_k=3)
    return {
        "agent": "rag",
        "answer": result.answer,
        "citations": [c.model_dump(mode="json") for c in result.citations],
        "vector_db": "qdrant",
    }


def _run_code_agent(task: str) -> dict[str, Any]:
    llm = get_llm_provider()
    if get_settings().environment == "test" or get_settings().llm_provider == "fake":
        advice = "Focus on input validation, tests for edge cases, and clearer module boundaries."
    else:
        advice = llm.chat(
            [
                ChatMessage(
                    role="user",
                    content=f"As a code agent, give brief engineering advice for: {task}",
                )
            ]
        )
    return {"agent": "code", "advice": advice}


def _run_meeting_agent(db: Session, user: User, task: str) -> dict[str, Any]:
    # Use task text as a synthetic transcript when no upload is provided
    note = meeting_service.create_meeting_note(
        db,
        user,
        filename="agent-task.txt",
        data=None,
        title="Agent meeting extract",
        transcript_text=task,
    )
    return {
        "agent": "meeting",
        "summary": note.summary,
        "action_items": note.action_items_json,
    }


def _run_report_agent(task: str, steps: list[dict[str, Any]]) -> str:
    """Build an executive report from specialist evidence (prefer facts over free LLM prose)."""
    lines: list[str] = ["## Agent report", f"**Task:** {task}", ""]

    sql_steps = [s for s in steps if s.get("agent") == "sql"]
    rag_steps = [s for s in steps if s.get("agent") in {"rag", "retrieval"}]
    research_steps = [s for s in steps if s.get("agent") == "research"]
    code_steps = [s for s in steps if s.get("agent") == "code"]
    meeting_steps = [s for s in steps if s.get("agent") == "meeting"]

    if sql_steps:
        lines.append("### SQL result")
        for step in sql_steps:
            lines.append(f"- Query: `{step.get('sql')}`")
            preview = step.get("preview") or []
            if preview:
                lines.append(f"- Answer: `{preview[0]}`")
            lines.append(f"- Rows returned: {step.get('row_count', 0)}")
        lines.append("")

    if rag_steps:
        lines.append("### Retrieval")
        for step in rag_steps:
            answer = str(step.get("answer") or "").strip()
            if answer:
                lines.append(answer[:800])
            cites = step.get("citations") or []
            if cites:
                lines.append(f"- Citations: {len(cites)}")
        lines.append("")

    if research_steps:
        lines.append("### Research")
        for step in research_steps:
            brief = step.get("brief") or step.get("summary") or step.get("answer")
            if brief:
                lines.append(str(brief)[:800])
        lines.append("")

    if code_steps:
        lines.append("### Code agent")
        for step in code_steps:
            lines.append(str(step.get("advice") or "")[:600])
        lines.append("")

    if meeting_steps:
        lines.append("### Meeting extract")
        for step in meeting_steps:
            lines.append(str(step.get("summary") or "")[:600])
        lines.append("")

    evidence_built = any([sql_steps, rag_steps, research_steps, code_steps, meeting_steps])
    if evidence_built:
        lines.append("### Conclusion")
        if sql_steps and sql_steps[0].get("preview"):
            lines.append(
                "The SQL specialist answered using the demo analytics database; "
                "see the query and result above."
            )
        else:
            lines.append(
                f"Completed {len(steps)} orchestration steps for this task."
            )
        return "\n".join(lines).strip()

    llm = get_llm_provider()
    if get_settings().environment == "test" or get_settings().llm_provider == "fake":
        return (
            f"Orchestration report for: {task}\n"
            f"Completed {len(steps)} specialist steps across the AI layer."
        )
    # Keep LLM input tiny so small local models stay on-task
    compact = [
        {k: v for k, v in s.items() if k != "snapshot"}
        for s in steps
        if s.get("agent") not in {"knowledge_graph", "prompt_registry"}
    ][:8]
    return llm.chat(
        [
            ChatMessage(
                role="user",
                content=(
                    "Write a short factual executive report (max 8 sentences) for this task. "
                    "Use ONLY the agent step evidence. Do not invent unrelated topics.\n"
                    f"TASK: {task}\nSTEPS: {compact}"
                ),
            )
        ]
    )


def _run_evaluation_agent(task: str, report: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    score = 65
    if any(s.get("agent") == "sql" and s.get("row_count", 0) > 0 for s in steps):
        score += 8
    if any(s.get("agent") in {"rag", "retrieval"} and s.get("citations") for s in steps):
        score += 8
    if any(s.get("agent") == "research" for s in steps):
        score += 8
    if any(s.get("agent") == "meeting" for s in steps):
        score += 4
    if report:
        score += 5
    return {
        "agent": "evaluation",
        "score": min(score, 100),
        "notes": "Evaluation system scored evidence coverage across specialists.",
        "task": task,
        "monitoring": {"metrics_path": "/metrics"},
        "security": {"auth": "jwt", "rate_limit": True},
    }


def _build_graph():
    try:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(AgentState)

        def plan_node(state: AgentState) -> AgentState:
            state["plan"] = _planner(state["task"])
            state["steps"] = []
            return state

        def specialists_node(state: AgentState) -> AgentState:
            return state

        def report_node(state: AgentState) -> AgentState:
            state["report"] = _run_report_agent(state["task"], state.get("steps") or [])
            return state

        def eval_node(state: AgentState) -> AgentState:
            state["evaluation"] = _run_evaluation_agent(
                state["task"], state.get("report") or "", state.get("steps") or []
            )
            return state

        graph.add_node("planner", plan_node)
        graph.add_node("specialists", specialists_node)
        graph.add_node("report", report_node)
        graph.add_node("evaluation", eval_node)
        graph.set_entry_point("planner")
        graph.add_edge("planner", "specialists")
        graph.add_edge("specialists", "report")
        graph.add_edge("report", "evaluation")
        graph.add_edge("evaluation", END)
        return graph.compile()
    except Exception:
        return None


def run_agents(
    db: Session, user: User, task: str, *, model_family: str | None = None
) -> AgentRun:
    run = AgentRun(user_id=user.id, task=task, status=JobStatus.processing)
    db.add(run)
    db.commit()
    db.refresh(run)

    tracer = TraceRecorder(db, user, task, model_family=model_family)
    try:
        plan = _planner(task)
        if model_family:
            plan["model_router"] = model_family
        steps: list[dict[str, Any]] = [{"agent": "planner", "plan": plan}]
        tracer.add_step(
            agent_name="planner",
            tool_name="orchestrator",
            prompt=task,
            output=str(plan),
            model_name=model_family or get_settings().default_model_family,
            metadata={"agents": plan.get("agents")},
        )

        mem = memory_service.memory_context(db, user, task)
        if mem:
            steps.append({"agent": "memory", "context": mem})
            tracer.add_step(agent_name="memory", tool_name="recall", output=mem)

        for agent_name in plan["agents"]:
            started = time.perf_counter()
            if agent_name == "sql":
                result = _run_sql_agent(db, user, task)
                steps.append(result)
            elif agent_name == "retrieval":
                result = _run_retrieval_agent(db, user, task)
                steps.append(result)
            elif agent_name == "research":
                result = research_service.run_research(
                    db, user, task, model_family=model_family
                )
                steps.append(result)
            elif agent_name == "code":
                result = _run_code_agent(task)
                steps.append(result)
            elif agent_name == "meeting":
                result = _run_meeting_agent(db, user, task)
                steps.append(result)
            elif agent_name in {"report", "evaluation"}:
                continue
            else:
                continue
            latency = int((time.perf_counter() - started) * 1000)
            tracer.add_step(
                agent_name=result.get("agent", agent_name),
                tool_name=agent_name,
                prompt=task,
                output=str(result)[:4000],
                model_name=model_family or get_settings().default_model_family,
                latency_ms=latency,
                metadata={"keys": list(result.keys())},
            )

        graph_snap = kg.get_graph(db, user, limit=20)
        steps.append({"agent": "knowledge_graph", "snapshot": graph_snap})
        tracer.add_step(
            agent_name="knowledge_graph",
            tool_name="graph_snapshot",
            output=str(graph_snap)[:2000],
        )

        try:
            rag_prompt = prompt_service.get_active_prompt(db, "rag_grounded")
            steps.append(
                {
                    "agent": "prompt_registry",
                    "prompt": rag_prompt.name,
                    "version": rag_prompt.version,
                }
            )
        except Exception:
            pass

        report = _run_report_agent(task, steps)
        steps.append({"agent": "report", "report": report})
        tracer.add_step(agent_name="report", tool_name="synthesize", prompt=task, output=report)

        evaluation = _run_evaluation_agent(task, report, steps)
        steps.append(evaluation)
        tracer.add_step(
            agent_name="evaluation",
            tool_name="score",
            output=str(evaluation),
            metadata=evaluation,
        )

        _build_graph()

        memory_service.remember(
            db,
            user,
            content=f"Agent run completed for '{task}' with score {evaluation.get('score')}",
            memory_type="short_term",
            source="orchestration",
            importance=1,
        )

        run.plan_json = plan
        run.steps_json = steps
        run.report = report
        run.evaluation_json = evaluation
        run.status = JobStatus.ready
        db.add(run)
        db.add(
            UsageEvent(
                user_id=user.id,
                event_type="agent_run",
                model_name=model_family or get_settings().default_model_family,
                metadata_json={
                    "run_id": str(run.id),
                    "agents": plan["agents"],
                    "trace_id": str(tracer.trace.id),
                },
            )
        )
        db.commit()
        db.refresh(run)
        tracer.finish(final_response=report, run_id=run.id)
        try:
            from app.services import notifications

            notifications.notify(
                db,
                user,
                title="Agent run complete",
                body=f"Your agent run for '{task[:80]}' is ready.",
                category="agent",
                link=f"/agents/runs/{run.id}",
            )
        except Exception:
            # A notification failure should not make a completed run fail.
            pass
        return run
    except Exception as exc:  # noqa: BLE001
        run.status = JobStatus.failed
        db.add(run)
        db.commit()
        tracer.finish(error=str(exc), run_id=run.id)
        raise


def get_run(db: Session, user: User, run_id) -> AgentRun:
    from sqlalchemy import select

    from app.core.exceptions import NotFoundError

    run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user.id))
    if not run:
        raise NotFoundError("Agent run not found")
    return run


def list_runs(db: Session, user: User) -> list[AgentRun]:
    from sqlalchemy import select

    return list(
        db.scalars(
            select(AgentRun).where(AgentRun.user_id == user.id).order_by(AgentRun.created_at.desc())
        ).all()
    )
