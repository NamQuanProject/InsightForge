from fastapi import APIRouter

from app.schema.common import AgentsStatusResponse
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/status", response_model=AgentsStatusResponse)
async def get_agents_status():
    return AgentService().get_status()
