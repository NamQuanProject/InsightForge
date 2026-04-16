import os
import sys

from dotenv import load_dotenv

from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.errors import FrameworkError
from beeai_framework.serve.utils import LRUMemoryManager

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


if __name__ == "__main__":
    main()
