import os
import sys

from dotenv import load_dotenv

from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.errors import FrameworkError
from beeai_framework.serve.utils import LRUMemoryManager
# from beeai_framework.tools import Tool, tool
# from beeai_framework.tools.handoff import HandoffTool
# from beeai_framework.tools.think import ThinkTool
# from beeai_framework.tools import Tool
# from beeai_framework.memory.base_memory import BaseMemory
# # ✅ Load env
load_dotenv()

from agents.orchestration_agent.agent import build_routing_agent


def main() -> None:
    load_dotenv()

    host = os.environ.get("AGENT_HOST", "localhost")
    port = int(os.environ.get("ROUTING_AGENT_PORT", 9996))

    print(f"Starting RoutingAgent A2A server on {host}:{port} ...")

    try:
        A2AServer(
            config=A2AServerConfig(
                host=host,
                port=port,
                protocol="jsonrpc",
                name="RoutingAgent",
                description=(
                    "Orchestrates the content marketing pipeline by routing queries "
                    "to TrendingAnalysisAgent and ContentGeneratingAgent."
                ),
                version="1.0.0",
            ),
            memory_manager=LRUMemoryManager(maxsize=50),
        ).register(build_routing_agent(), send_trajectory=True).serve()
    except FrameworkError as exc:
        print(exc.explain())
        sys.exit(1)


# async def main():
#     # 1. Define the Remote Sub-Agents
#     # These are your specialized servers running elsewhere
#     trending_analysis_agent = A2AAgent(
#         url="http://localhost:9997",
#         memory=UnconstrainedMemory()
#     )

#     content_generation_agent = A2AAgent(
#         url="http://localhost:9998", # Added the missing port
#         memory=UnconstrainedMemory()
#     )
#     await trending_analysis_agent.check_agent_exists()
#     print("\tℹ️", f"{trending_analysis_agent.name} initialized")
#     print("\tℹ️", f"{trending_analysis_agent.agent_card.description} description")

#     await content_generation_agent.check_agent_exists()
#     print("\tℹ️", f"{content_generation_agent.agent_card.description} description")

#     # 2. Setup the Orchestrator's Brain
#     llm = ChatModel.from_name(
#         "gemini:gemini-2.5-flash"
#     )

#     think_tool = ThinkTool()

#     # 3. Create the Orchestrator (RequirementAgent)
#     # Using HandoffTool eliminates all your manual httpx/json code!
#     orchestrator = RequirementAgent(
#         name="ProductManager",
#         description="I coordinate market research and content creation.",
#         llm=llm,
#         tools=[
#             think_tool,
#             # HandoffTool(
#             #     target=trending_analysis_agent,
#             #     name=trending_analysis_agent.name,
#             #     description=trending_analysis_agent.agent_card.description,
#             # ),
#             HandoffTool(
#                 target=trending_analysis_agent,
#                 name=trending_analysis_agent.name,
#                 description=trending_analysis_agent.agent_card.description
#             ),
#              HandoffTool(
#                 target=content_generation_agent,
#                 name=content_generation_agent.name,
#                 description=content_generation_agent.agent_card.description
#             )
#         ],
#         requirements=[
#             ConditionalRequirement(
#                 think_tool,
#                 force_at_step=1,
#                 force_after=Tool,
#                 consecutive_allowed=False
#             ),
            
#         ],
#         memory=UnconstrainedMemory(), # Fixed: Use instance, not class
#         role="Product Manager",
#         instructions= f"""
#         You are the Lead Content Pipeline Router.
        
#         You have two specialist agents available via handoff:
#         - {trending_analysis_agent.name}: finds and analyzes trending topics
#         - {content_generation_agent.name}: produces video scripts, post content, and images
        
#         ## Workflow
#         1. ALWAYS start with ThinkTool to reason about the user's intent.
#         2. If the user wants trend data → hand off to {trending_analysis_agent.name}.
#         3. If the user wants content generated → FIRST get trends, THEN hand off to {content_generation_agent.name}
#         passing the FULL trend report as context.
#         4. Summarize the final result clearly for the user, including both trend report and content generation.
        
#         ## Rules
#         - Never truncate the trend report when passing it to {content_generation_agent.name}.
#         - Reply in the same language as the user's query.
#         - Do NOT fabricate trend data or content.
#         """
#     )

#     print(f"✅ Orchestrator '{orchestrator.meta.name}' is ready.")
#     return orchestrator


# # =========================
# # Entry point
# # =========================
if __name__ == "__main__":
    main()
