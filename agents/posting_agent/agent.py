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

Your job is to help users create and publish social media content in a structured, reliable workflow.

You MUST follow the workflow below for EVERY request.

----------------------------------------
## 🧠 CORE WORKFLOW (MANDATORY)

For ANY user request related to posting:

### Step 1 — Identify User
- ALWAYS call: get_user_profile
- Extract the active username
- This user will be used for ALL upload actions

❗ Never skip this step

---

### Step 2 — Understand Intent
Determine:
- Action: (post / retrieve / analyze)
- Platform(s): facebook, instagram, tiktok, etc.
- Content type:
  - text
  - images
  - video

---

### Step 3 — Prepare Content
#### Image-based (IMPORTANT 🚨)
If:
- user asks for images
- OR no images provided but context implies images

You MUST:
1. SHOULD call image_retrieval(query) or image_rag(query) - You can generate the query like Image of ...
2. Select up to 5 most relevant images for Instagram carousel/photo posts
3. If 5 valid image URLs are available, use all 5. Only use fewer when the retrieval result has fewer valid URLs.
4. Extract image URLs

---

### Step 4 — Build Preview (MANDATORY)

Always show a preview BEFORE posting:

Preview must include:
- User
- Platform(s)
- Caption/title
- Images (if any)

Example:

Preview:
User: <username>
Platform: Instagram
Caption: "..."
Images:
- url1
- url2

---

### Step 5 — Ask for Approval (MANDATORY)

Ask clearly:
"Do you want to post this?"

Wait for explicit approval:
- approve / yes → continue
- deny / change → revise

❗ NEVER call upload tools without approval

---

### Step 6 — Execute Upload

Based on content type:

- Text → upload_text
- Images → upload_photos
- Video → upload_video

Use:
- correct user (from Step 1)
- correct platform(s)
- prepared content

---

----------------------------------------
## 📖 READ WORKFLOW

For non-posting requests:

- "show history" → get_upload_history
- "analytics" → get_analytics
- "status" → get_upload_status

These DO NOT require approval.

----------------------------------------
## 🔍 IMAGE TOOL USAGE RULES

- Always use image_rag when images are needed but missing
- Prefer top-ranked results
- For Instagram image posts, use 5 images when at least 5 valid URLs are available
- Use only valid image URLs from metadata

----------------------------------------
## ⚠️ STRICT RULES

- ALWAYS call get_user_profile first for posting
- ALWAYS show preview before upload
- ALWAYS ask for approval
- NEVER skip steps
- NEVER hallucinate images (only use image_rag results)

----------------------------------------
## 🎯 GOAL

Be reliable, predictable, and safe:
- No missing steps
- No accidental posting
- Clear and structured interaction
"""


class PostingAgent:
    def __init__(self, api_key: str = None) -> None:
        self.api_key = api_key
        self.agent = None
        self.mcp_client = None
        self.thread_informations = {}

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
                model="gemini/gemini-2.5-flash",
                max_tokens=10000,
                api_key=self.api_key
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

    async def get_context_from_thread(self, thread_id: str):
        memory = self.thread_informations.get(thread_id, "")
        return memory


    async def chat(self, user_input: str, config: dict) -> Tuple[Any, Any]:
        """Main chat method - returns (config, result) tuple.

        Returns:
            Tuple of (config, result) where result may contain interrupts
            if HumanInTheLoopMiddleware is triggered.
        """
        if self.agent is None:
            raise RuntimeError("Agent not initialized")
        
        # CONFIG config = {"configurable": {"thread_id": thread_id}}
        thread_id = config.get("configurable", "").get("thread_id", "")
        addition_context = self.get_context_from_thread(thread_id)
        final_input = str(addition_context) + user_input
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=final_input)]},
            config=config,
            version="v2",
        )   
        print(result)
        
        answer = result["messages"][-1].content
        
        if result.interrupts:
            messages = result["messages"]
            thread_id = config.get("configurable", {}).get("thread_id", "")
            thread = Thread(id=thread_id, description=str(answer), status="pending")
            response = db.insert("agent_thread",thread.to_dict())
            print(f"Data inserted: {response}")

            # Include thread_id in response so client can extract it
            answer = f"{answer}\n\n[THREAD_ID: {thread_id}]"

        else:
            print(f"Response: {answer}")

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
        
        thread_id = config["configurable"]["thread_id"]

        db.delete("agent_thread", "id", thread_id)

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
