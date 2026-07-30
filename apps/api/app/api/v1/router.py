"""API v1 router aggregate — API Gateway surface."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    agents,
    auth,
    benchmarks,
    chats,
    code,
    dashboard,
    documents,
    eval_api,
    feedback_api,
    health,
    knowledge,
    meetings,
    memory_api,
    models,
    notifications_api,
    orgs_api,
    prompts_api,
    research_api,
    resumes,
    sql,
    traces,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(orgs_api.router)
api_router.include_router(notifications_api.router)
api_router.include_router(chats.router)
api_router.include_router(documents.router)
api_router.include_router(sql.router)
api_router.include_router(code.router)
api_router.include_router(resumes.router)
api_router.include_router(meetings.router)
api_router.include_router(agents.router)
api_router.include_router(research_api.router)
api_router.include_router(knowledge.router)
api_router.include_router(memory_api.router)
api_router.include_router(models.router)
api_router.include_router(traces.router)
api_router.include_router(eval_api.router)
api_router.include_router(feedback_api.router)
api_router.include_router(prompts_api.router)
api_router.include_router(benchmarks.router)
api_router.include_router(dashboard.router)
api_router.include_router(admin.router)
