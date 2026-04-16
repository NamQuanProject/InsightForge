import json
import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agents.generating_agent.agent import ContentGenerationAgent

class ContentAgentExecutor(AgentExecutor):
    """Execution engine for handling user requests and routing to the ProviderAgent."""
    def __init__(self) -> None:
        self.agent = None

    async def _ensure_initialized(self) -> None:
        """Lazy initialization of the agent."""
        if self.agent is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
            self.agent = await ContentGenerationAgent(api_key=api_key).initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_initialized()
        prompt = context.get_user_input()
        response = await self.agent.answer_query(prompt)
        payload = json.dumps(response, ensure_ascii=False, indent=2) if isinstance(response, dict) else str(response)
        await event_queue.enqueue_event(new_agent_text_message(payload))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
