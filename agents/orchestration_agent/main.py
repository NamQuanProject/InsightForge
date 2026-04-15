import os
import uvicorn
from dotenv import load_dotenv
import sys

from beeai_framework.adapters.a2a import A2AServer, A2AServerConfig
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.serve.utils import LRUMemoryManager
from beeai_framework.tools.think import ThinkTool

from agents.orchestration_agent.agent import build_routing_agent

# ---------------------------------------------------------------------------
# A2A Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import uvicorn
    from dotenv import load_dotenv
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
                # Agent card metadata — visible at /.well-known/agent-card.json
                name="RoutingAgent",
                description=(
                    "Orchestrates the content marketing pipeline: "
                    "routes queries to TrendingAnalysisAgent and/or ContentGeneratingAgent."
                ),
                version="1.0.0",
            ),
            memory_manager=LRUMemoryManager(maxsize=50),
        ).register(build_routing_agent(), send_trajectory=True).serve()
    except FrameworkError as e:
        print(e.explain())
        sys.exit(1)

if __name__ == "__main__":
    main()