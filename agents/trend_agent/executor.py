import os
import uvicorn
from dotenv import load_dotenv

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from agents.trend_agent.agent import TrendAgent


class TrendAgentExecutor(AgentExecutor):
    """Execution engine for handling user requests and routing to the ProviderAgent."""
    def __init__(self) -> None:
        self.agent = None

    async def _ensure_initialized(self) -> None:
        """Lazy initialization of the agent."""
        if self.agent is None:
            self.agent = await TrendAgent().initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_initialized()
        prompt = context.get_user_input()
        response = await self.agent.answer_query(prompt)
        await event_queue.enqueue_event(new_agent_text_message(response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
