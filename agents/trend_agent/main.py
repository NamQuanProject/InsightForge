import os
import uvicorn
from dotenv import load_dotenv
from .executor import ProviderAgentExecutor
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message

from test.provider_agent import ProviderAgent



def main():
    print("Starting Healthcare Provider Agent Server...")
    load_dotenv()
    
    host = os.environ.get("AGENT_HOST", "localhost")
    port = int(os.environ.get("TREND_AGENT_PORT", 9997))

    skill = AgentSkill(
        id="find_healthcare_providers",
        name="Find Healthcare Providers",
        description="Finds and lists healthcare providers based on user's location and specialty.",
        tags=["healthcare", "providers", "doctor", "psychiatrist"],
        examples=[
            "Are there any Psychiatrists near me in Boston, MA?",
            "Find a pediatrician in Springfield, IL.",
        ],
    )

    agent_card = AgentCard(
        name="HealthcareProviderAgent",
        description="An agent that can find and list healthcare providers based on a user's location and desired specialty.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )
    request_handler = DefaultRequestHandler(
        agent_executor=ProviderAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("\n=== REGISTERED ROUTES ===")
    for route in server.build().routes:
        print(route.path, route.methods)

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main()