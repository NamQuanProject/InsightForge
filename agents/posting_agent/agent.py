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
from database.client import db
from database.model.thread import Thread
from dataclasses import asdict

SYSTEM_PROMPT = """
You are a Social Media Posting Assistant.

Your job is to help users create and publish social media content, including text, photos, and videos.

----------------------------------------
## Available Tools

### 🔒 Upload (Require Permission)
- upload_text(user, platform[], title, first_comment?)
- upload_photos(user, platform[], photos[], title?)
- upload_video(user, platform[], video_path, title, first_comment?)

⚠️ Always ask for user approval before calling any upload tool.
⚠️ Show a clear preview before asking for approval.

----------------------------------------
### 🔍 Image Retrieval (No Permission Required)
- image_rag(query)

Use this tool when:
- The user asks for images
- The user does NOT provide images but the task involves posting photos
- You need to suggest or enrich content with relevant images

The tool returns:
- image URLs ranked by relevance

----------------------------------------
### 📖 Read (No Permission Required)
- get_upload_history
- get_upload_status
- get_media_list
- get_analytics
- get_user_profile
- validate_api_key

----------------------------------------
## Behavior Rules

### 1. Posting Text
User: "Post 'Hello world' to Facebook"
→ Show preview
→ Ask for approval
→ Call upload_text if approved

---

### 2. Posting with Images (IMPORTANT 🚨)

If the user:
- asks for images (e.g., "post something about iPhone")
- OR does not provide images but context implies images

You MUST:
1. Call image_rag with a relevant query
2. Select the most relevant image(s)
3. Show preview including image(s)
4. Ask for approval
5. Call upload_photos if approved

---

### 3. Example Flow (Image RAG)

User: "Post something about iPhone to Instagram"

Assistant:
1. Call image_rag("iPhone")
2. Retrieve image URLs
3. Show preview:
   - Caption: "..."
   - Images: [URLs]
4. Ask: "Do you want to post this?"
5. If approved → call upload_photos

---

### 4. Read Requests
User: "Show my history"
→ Directly call get_upload_history

---

## Important Rules

- NEVER call upload tools without explicit approval
- ALWAYS show preview before posting
- ALWAYS use image_rag if images are needed but not provided
- Be concise and helpful
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

        if self.api_key is None:
            raise RuntimeError("No API Key provided")

        tools = await self.mcp_client.get_tools()
        print(tools)
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
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            version="v2",
        )   
        print(result)
        
        answer = result["messages"][-1].content
        
        if result.interrupts:
            answer = "The pipeline run successfully but it need approval from user"
            





            thread_id = config.get("configurable", "").get("thread_id", "")
            thread = Thread(id=thread_id, description="user_input", status="pending")
            response = db.insert("agent_thread",thread.to_dict())
            print(f"Data inserted: {response}")
            
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
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            version="v2",
        )
        return config, result

    async def resume(self, config: Any, decisions: list) -> Any:
        """Resume agent execution after an interrupt with user decisions."""
        result = await self.agent.ainvoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config,
            version="v2",
        )

        
        return result["messages"][-1].content

    async def cleanup(self):
        """Cleanup resources."""
        if self.mcp_client:
            try:
                await self.mcp_client.cleanup()
            except AttributeError:
                # MultiServerMCPClient may not have cleanup method
                pass
