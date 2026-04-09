import os
import asyncio
import warnings
from typing import Any
from dotenv import load_dotenv

from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.vertexai import VertexAIChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import EventMeta, GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool

# ✅ Load env
load_dotenv()

warnings.filterwarnings("ignore")

# =========================
# Middleware
# =========================
class ConciseGlobalTrajectoryMiddleware(GlobalTrajectoryMiddleware):
    def _format_prefix(self, meta: EventMeta) -> str:
        return super()._format_prefix(meta).rstrip(": ")

    def _format_payload(self, value: Any) -> str:
        return ""

# =========================
# Main async function
# =========================
async def main():

    # =========================
    # Policy Agent (A2A)
    # =========================
    policy_agent = A2AAgent(
        url="http://localhost:9997",
        memory=UnconstrainedMemory()
    )

    await policy_agent.check_agent_exists()
    print("\tℹ️", f"{policy_agent.name} initialized")

    # =========================
    # Healthcare Agent
    # =========================
    think_tool = ThinkTool()
    healthcare_agent = RequirementAgent(
        name="Healthcare Agent",
        description="Healthcare concierge agent",
        llm=VertexAIChatModel(
            model_id="gemini-2.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            location="us-central1",
            allow_parallel_tool_calls=True,
            allow_prompt_caching=False,
        ),
        tools=[
            think_tool,
            HandoffTool(
                target=policy_agent,
                name=policy_agent.name,
                description=policy_agent.agent_card.description,
            ),
        ],
        requirements=[
            ConditionalRequirement(
                think_tool,
                force_at_step=1,
                consecutive_allowed=False
            ),
        ],
        role="Healthcare Concierge",
        instructions=f"""
        You are a healthcare concierge.

        - Use {policy_agent.name} for insurance-related questions.
        - Always handoff when needed.
        - Combine answers into a final response.
        - Clearly state which agent provided each piece of info.

        Do NOT hallucinate provider or insurance data.
        """
    )

    print("\tℹ️", f"{healthcare_agent.meta.name} initialized")

    # =========================
    # Run agent
    # =========================
    response = await healthcare_agent.run(
    """I'm based in Austin, TX. How do I get mental health therapy near me 
    and what does my insurance cover?"""
    ).middleware(ConciseGlobalTrajectoryMiddleware())


    print("\n=== Final Response ===")
    print(response.last_message.text)


# =========================
# Entry point
# =========================
if __name__ == "__main__":
    asyncio.run(main())