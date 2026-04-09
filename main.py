import os
import asyncio
import warnings
from dotenv import load_dotenv
from typing import Any
from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.vertexai import VertexAIChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import EventMeta, GlobalTrajectoryMiddleware
from beeai_framework.serve.utils import LRUMemoryManager
from beeai_framework.tools import Tool, tool
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






    
    think_tool = ThinkTool()
    trending_agent = RequirementAgent(
        name="Trending Analysis Agent",
        description="Trending Analysis Agent",
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
        role="A profession treding analysis",
        instructions=f"""
        You are a profession treding analysis. Your task is to analyze the latest google trend and provide insights based on the trend.
        - Use {policy_agent.name} for trending-related questions
        """
    )

    print("\tℹ️", f"{trending_agent.meta.name} initialized")

    # =========================
    # Run agent
    # =========================
    # response = await healthcare_agent.run(
    # """I'm based in Austin, TX. How do I get mental health therapy near me 
    # and what does my insurance cover?"""
    # ).middleware(ConciseGlobalTrajectoryMiddleware())


    # print("\n=== Final Response ===")
    # print(response.last_message.text)

    
    return trending_agent


# # =========================
# # Entry point
# # =========================
if __name__ == "__main__":
    my_agent = asyncio.run(main())

    A2AServer(
        config=A2AServerConfig(port="5000", protocol="jsonrpc", host="localhost"),
        memory_manager=LRUMemoryManager(maxsize=100),
    ).register(my_agent, send_trajectory=True).serve()

    