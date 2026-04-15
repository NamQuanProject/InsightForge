import os
import asyncio
import warnings
from dotenv import load_dotenv
from typing import Any
from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.vertexai import VertexAIChatModel
from beeai_framework.backend import ChatModel
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

# # =========================
# # Main async function
# # =========================
# async def main():

#     # =========================
#     # Policy Agent (A2A)
#     # =========================
#     trending_analysis_agent = A2AAgent(
#         url="http://localhost:9997",
#         memory=UnconstrainedMemory()
#     )

#     content_generation_agent = A2AAgent(
#         url="http://localhost:"   
#     )

#     await trending_analysis_agent.check_agent_exists()
#     print("\tℹ️", f"{trending_analysis_agent.name} initialized")

#     think_tool = ThinkTool()
#     trending_agent = RequirementAgent(
#         name="Product Manager Agent",
#         description="Product Manager Agent",
#         llm=VertexAIChatModel(
#             model_id="gemini-2.5-flash",
#             api_key=os.getenv("GOOGLE_API_KEY"),
#             location="us-central1",
#             allow_parallel_tool_calls=True,
#             allow_prompt_caching=False,
#         ),
#         tools=[
#             think_tool,
#             HandoffTool(
#                 target=trending_analysis_agent,
#                 name=trending_analysis_agent.name,
#                 description=trending_analysis_agent.agent_card.description,
#             ),
#             HandoffTool(
#                 target=content_generation_agent,
#                 name=content_generation_agent.name,
#                 description=content_generation_agent.agent_card.description
#             )
#         ],
#         requirements=[
#             ConditionalRequirement(
#                 think_tool,
#                 force_at_step=1,
#                 consecutive_allowed=False
#             ),
#         ],
#         memory = BaseMemory,
#         role="Product Manager Agent",
#         instructions=f"""
#         You are a Product Manager Agent. Your task is to analyze the Product Manager and product analysis.
#         - Use {trending_analysis_agent.name} for trending-related questions to research the markets
#         """
#     )

#     print("\tℹ️", f"{trending_agent.meta.name} initialized")

#     # =========================
#     # Run agent
#     # =========================
#     # response = await healthcare_agent.run(
#     # """I'm based in Austin, TX. How do I get mental health therapy near me 
#     # and what does my insurance cover?"""
#     # ).middleware(ConciseGlobalTrajectoryMiddleware())


#     # print("\n=== Final Response ===")
#     # print(response.last_message.text)

    
#     return trending_agent

async def main():
    # 1. Define the Remote Sub-Agents
    # These are your specialized servers running elsewhere
    trending_analysis_agent = A2AAgent(
        url="http://localhost:9997",
        memory=UnconstrainedMemory()
    )

    content_generation_agent = A2AAgent(
        url="http://localhost:9998", # Added the missing port
        memory=UnconstrainedMemory()
    )
    await trending_analysis_agent.check_agent_exists()
    print("\tℹ️", f"{trending_analysis_agent.name} initialized")
    print("\tℹ️", f"{trending_analysis_agent.agent_card.description} description")

    await content_generation_agent.check_agent_exists()
    print("\tℹ️", f"{content_generation_agent.agent_card.description} description")

    # 2. Setup the Orchestrator's Brain
    llm = ChatModel.from_name(
        "gemini:gemini-2.5-flash"
    )

    think_tool = ThinkTool()

    # 3. Create the Orchestrator (RequirementAgent)
    # Using HandoffTool eliminates all your manual httpx/json code!
    orchestrator = RequirementAgent(
        name="ProductManager",
        description="I coordinate market research and content creation.",
        llm=llm,
        tools=[
            think_tool,
            HandoffTool(
                target=trending_analysis_agent,
                name=trending_analysis_agent.name,
                description=trending_analysis_agent.agent_card.description
            ),
             HandoffTool(
                target=content_generation_agent,
                name=content_generation_agent.name,
                description=content_generation_agent.agent_card.description
            )
        ],
        requirements=[
            ConditionalRequirement(
                think_tool,
                force_at_step=1,
                consecutive_allowed=False
            ),
        ],
        memory=UnconstrainedMemory(), # Fixed: Use instance, not class
        role="Product Manager",
        instructions= f"""
        You are the Lead Content Pipeline Router.
        
        You have two specialist agents available via handoff:
        - {trending_analysis_agent.name}: finds and analyzes trending topics
        - {content_generation_agent.name}: produces video scripts, post content, and images
        
        ## Workflow
        1. ALWAYS start with ThinkTool to reason about the user's intent.
        2. If the user wants trend data → hand off to {trending_analysis_agent.name}.
        3. If the user wants content generated → FIRST get trends, THEN hand off to {content_generation_agent.name}
        passing the FULL trend report as context.
        4. Summarize the final result clearly for the user, including both trend report and content generation.
        
        ## Rules
        - Never truncate the trend report when passing it to {content_generation_agent.name}.
        - Reply in the same language as the user's query.
        - Do NOT fabricate trend data or content.
        """
    )

    print(f"✅ Orchestrator '{orchestrator.meta.name}' is ready.")
    return orchestrator


# # =========================
# # Entry point
# # =========================
if __name__ == "__main__":
    my_agent = asyncio.run(main())

    A2AServer(
        config=A2AServerConfig(port="9996", protocol="jsonrpc", host="localhost"),
        memory_manager=LRUMemoryManager(maxsize=100),
    ).register(my_agent, send_trajectory=True).serve()

    