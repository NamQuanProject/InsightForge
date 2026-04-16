from fastapi import APIRouter

from app.schema.common import AgentsStatusResponse, OrchestratorRequest, OrchestratorResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/status", response_model=AgentsStatusResponse)
async def get_agents_status():
    return AgentService().get_status()


@router.post("/orchestrate", response_model=OrchestratorResponse)
async def orchestrate(payload: OrchestratorRequest):
    return await AgentService().orchestrate(
        prompt=payload.prompt,
        save_files=payload.save_files,
        user_id=payload.user_id,
    )
