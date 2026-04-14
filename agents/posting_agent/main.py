import logging
import os
import uvicorn
from dotenv import load_dotenv
from agents.posting_agent.executor import PostingAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.responses import JSONResponse
from a2a.client import ClientFactory


from a2a.types import AgentCapabilities, AgentCard, AgentSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def main():
    print("Starting Posting Agent Server...")
    load_dotenv()

    host = os.getenv("AGENT_HOST", "localhost")
    port = int(os.getenv("POSTING_AGENT_PORT", 9999))

    skill = AgentSkill(
        id="create_post",
        name="Create Post",
        description="Create and publish social media posts with human approval workflow. Supports TikTok, Instagram, YouTube, Facebook, X, Threads, LinkedIn, Bluesky, Reddit, Pinterest.",
        tags=["posting", "social-media", "publishing", "human-in-the-loop"],
        examples=[
            "Post a video about AI trends on TikTok",
            "Schedule a text post for tomorrow on all platforms",
            "Create a photo post for Instagram and Facebook",
            "approve draft_abc123",
            "reject draft_xyz789 because of typo",
        ],
    )

    agent_card = AgentCard(
        name="PostingAgent",
        description="An agent that creates, schedules, and publishes social media posts with human-in-the-loop approval. Integrates with Upload-Post API for multi-platform posting." \
        "Can get current username and others informations about accounts in upload-post and controlled your account activities as well as informations about your social plat-forms",
        url=f"https://{host}:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )
    
    
    request_handler = DefaultRequestHandler(
        agent_executor=PostingAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    uvicorn.run(server.build(), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
