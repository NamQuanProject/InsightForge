import os
import uvicorn
from dotenv import load_dotenv
from agents.generating_agent.executor import ContentAgentExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message


def main():
    print("Starting Content Generating Agent Server...")
    load_dotenv()
    
    host = os.environ.get("AGENT_HOST", "localhost")
    port = int(os.environ.get("CONTENT_AGENT_PORT", 9998))

    skill = AgentSkill(
        id="generate_content",
        name="Generate Content",
        description="Find and analyze the latest trend using Google Trends and validation through Social Media Trends based on the user's query.",
        tags=["content", "generation", "video", "text"],
        examples=[
            "Generate a video script for covering today news.",
            "Generate post content for my Tiktok.",
        ],
    )

    agent_card = AgentCard(
        name="ContentGeneratingAgent",
        description="An agent that comprehends trend analysis and recommended actions to produce media content materials including video scripts, post and images",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )
    request_handler = DefaultRequestHandler(
        agent_executor=ContentAgentExecutor(),
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