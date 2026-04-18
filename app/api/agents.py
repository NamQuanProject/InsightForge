from fastapi import APIRouter, Query

from app.schema.common import AgentsStatusResponse, OrchestratorRequest, OrchestratorResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/status", response_model=AgentsStatusResponse)
async def get_agents_status():
    return AgentService().get_status()


@router.post(
    "/orchestrate",
    response_model=OrchestratorResponse,
    response_model_exclude_none=True,
)
async def orchestrate(
    payload: OrchestratorRequest,
    include_raw_response: bool = Query(default=False),
    save_files: bool = Query(default=False),
):
    return await AgentService().orchestrate(
        prompt=payload.prompt,
        user_id=payload.user_id,
        include_raw_response=include_raw_response,
        save_files=save_files,
    )
