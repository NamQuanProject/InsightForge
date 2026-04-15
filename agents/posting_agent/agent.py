import os
from typing import Optional, Tuple, Any
from langchain_core.messages import HumanMessage
from langchain_core.utils.uuid import uuid7
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


SYSTEM_PROMPT = """You are a Social Media Posting Assistant.

## Available Tools

### Upload (Require Permission)
- upload_text(user, platform[], title, first_comment?)
- upload_photos(user, platform[], photos[], title?)
- upload_video(user, platform[], video_path, title, first_comment?)

### Read (No Permission)
- get_upload_history, get_upload_status, get_media_list
- get_analytics, get_user_profile, validate_api_key

User: post "Hello world" to facebook
Assistant: Shows preview, asks for approval, then calls upload_text if approved.

User: show my history
Assistant: Calls get_upload_history directly.
"""


class PostingAgent:
    def __init__(self, api_key: str = None) -> None:
        self.api_key = api_key
        self.agent = None
        self.mcp_client = None

    async def initialize(self):
        self.mcp_client = MultiServerMCPClient(
            {
                "posting_tools": StdioConnection(
                    transport="stdio",
                    command="python",
                    args=["-m", "mcp_servers.posting_servers.mcp_server"],
                )
            }
        )
        print("YES")

        if self.api_key is None:
            raise RuntimeError("No API Key provided")

        tools = await self.mcp_client.get_tools()

        self.agent = create_agent(
            ChatLiteLLM(
                model="gemini/gemini-2.5-flash", max_tokens=4000, api_key=self.api_key
            ),
            tools,
            middleware=[
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "upload_photos": {"allowed_decisions": ["approve", "reject"]},
                    },
                    description_prefix="Tool execution pending approval",
                ),
            ],
            name="PostingAgent",
            system_prompt=SYSTEM_PROMPT,
            checkpointer=InMemorySaver(),
        )

        print("PostingAgent initialized with tools:", [t.name for t in tools])
        return self

    async def chat(self, user_input: str) -> Tuple[Any, Any]:
        """Main chat method - returns (config, result) tuple.

        Returns:
            Tuple of (config, result) where result may contain interrupts
            if HumanInTheLoopMiddleware is triggered.
        """
        if self.agent is None:
            raise RuntimeError("Agent not initialized")

        config = {"configurable": {"thread_id": str(uuid7())}}
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            version="v2",
        )


        print(result)
        answer = result["messages"][-1].content

        if result.interrupts:
            answer = f"⏸️  Interrupt triggered with value: {result.interrupts[0].value}"
            print(f"⏸️  Interrupt triggered with value: {result.interrupts[0].value}")
        else:
            print(f"Response: {answer[:200]}...")

        return config, answer

    async def chat_with_thread(
        self, user_input: str, thread_id: str
    ) -> Tuple[Any, Any]:
        """Chat with a specific thread ID for conversation continuity."""
        if self.agent is None:
            raise RuntimeError("Agent not initialized")

        config = {"configurable": {"thread_id": thread_id}}
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            version="v2",
        )
        return config, result

    async def resume(self, config: Any, decisions: list) -> Any:
        """Resume agent execution after an interrupt with user decisions."""
        result = await self.agent.ainvoke(
            Command(resume={"decisions": decisions}),
            config=config,
            version="v2",
        )
        return result

    async def cleanup(self):
        """Cleanup resources."""
        if self.mcp_client:
            await self.mcp_client.cleanup()
