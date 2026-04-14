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
from beeai_framework.memory.base_memory import BaseMemory
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
    trending_analysis_agent = A2AAgent(
        url="http://localhost:9997",
        memory=UnconstrainedMemory()
    )

    posting_agent = A2AAgent(
        url="http://localhost:9999",
        memory = UnconstrainedMemory()
    )



    await trending_analysis_agent.check_agent_exists()
    print("\tℹ️", f"{trending_analysis_agent.name} initialized")

    await posting_agent.check_agent_exists()
    print("\tℹ️", f"{posting_agent.name} initialized")

    think_tool = ThinkTool()
    my_super_strong_agent = RequirementAgent(
        name="InsightForge Agent",
        description="Product Manager Agent",
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
                target=trending_analysis_agent,
                name=trending_analysis_agent.name,
                description=trending_analysis_agent.agent_card.description,
            ),
            HandoffTool(
                target=posting_agent,
                name=posting_agent.name,
                description=posting_agent.agent_card.description,
            ),

        ],
        requirements=[
            ConditionalRequirement(
                think_tool,
                force_at_step=1,
                consecutive_allowed=False
            ),
        ],
        role="Product Manager Agent",
        instructions=f"""
        You are a Product Manager Agent. Your task is to analyze the Product Manager and product analysis.
        - Use {posting_agent.name} for creating, scheduling, and publishing social media posts with human-in-the-loop approval. 
        Integrates with Upload-Post API for multi-platform posting. All the tools for posting are in {posting_agent.agent_card.description}.
        - Use {trending_analysis_agent.name} for trending-related questions to research the markets
        """
    )

    print("\tℹ️", f"{my_super_strong_agent.meta.name} initialized")

    # =========================
    # Run agent
    # =========================
    # response = await healthcare_agent.run(
    # """I'm based in Austin, TX. How do I get mental health therapy near me 
    # and what does my insurance cover?"""
    # ).middleware(ConciseGlobalTrajectoryMiddleware())


    # print("\n=== Final Response ===")
    # print(response.last_message.text)

    
    return my_super_strong_agent


# # =========================
# # Entry point
# # =========================
if __name__ == "__main__":
    my_agent = asyncio.run(main())

    A2AServer(
        config=A2AServerConfig(port="5000", protocol="jsonrpc", host="localhost"),
        memory_manager=LRUMemoryManager(maxsize=100),
    ).register(my_agent, send_trajectory=True).serve()

    