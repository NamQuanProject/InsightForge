import os
import uvicorn
from dotenv import load_dotenv
from agents.planning_agent.executor import PlanningAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message


def main():
    print("Starting Healthcare Provider Agent Server...")
    load_dotenv()
    
    host = os.environ.get("AGENT_HOST", "localhost")
    port = int(os.environ.get("PLANNING_AGENT_PORT", 9998))

    skill = AgentSkill(
        id="planning",
        name="Planning",
        description="Plan and execute tasks effectively.",
        tags=["planning", "execution"],
        examples=[
            "Plan a marketing campaign for a new product launch.",
            "Create a project plan for developing a new feature in our app.",
        ],
    )

    agent_card = AgentCard(
        name="PlanningAgent",
        description="An agent that can plan and provides plan for others execute agents to work find interntion of user",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )
    request_handler = DefaultRequestHandler(
        agent_executor=PlanningAgentExecutor(),
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