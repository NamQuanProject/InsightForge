import os
import uuid
from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from pydantic import BaseModel, Field
from enum import Enum


class PostStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class PostPlatform(str, Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    X = "x"
    THREADS = "threads"
    LINKEDIN = "linkedin"
    BLUESKY = "bluesky"
    REDDIT = "reddit"
    PINTEREST = "pinterest"
    ALL = "all"


class PostingState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "conversation_history"]
    user_intent: str
    user: str
    content_type: str
    content: str
    description: Optional[str]
    platform: list[str]
    hashtags: list[str]
    media_paths: list[str]
    scheduled_date: Optional[str]
    first_comment: Optional[str]
    post_status: PostStatus
    draft_id: str
    request_id: Optional[str]
    job_id: Optional[str]
    human_feedback: Optional[str]
    requires_approval: bool
    result: Optional[dict]
    error: Optional[str]


SYSTEM_PROMPT = """
You are an expert Social Media Posting Agent with deep knowledge of content publishing across multiple platforms.

## Supported Platforms
You can post to: TikTok, Instagram, YouTube, Facebook, X (Twitter), Threads, LinkedIn, Bluesky, Reddit, Pinterest

## Your Capabilities
1. **Upload Videos** - Upload video content with titles, descriptions, hashtags
2. **Upload Photos** - Share photo posts across platforms
3. **Upload Text** - Create text-only posts, threads, announcements
4. **Schedule Posts** - Set future publication times using ISO-8601 format
5. **Cross-post** - Simultaneously post to multiple platforms

## Upload-Post API Integration
Use these tools with the user profile from upload-post.com:
- `upload_video` - For video content (requires: user, platform[], video, title)
- `upload_photos` - For photo content (requires: user, platform[], photos[], title)
- `upload_text` - For text posts (requires: user, platform[], title)
- `get_upload_status` - Check async upload status
- `get_upload_history` - View past uploads

## Human-in-the-Loop Workflow (IMPORTANT)
For ALL posting operations:
1. **Create Draft** - Present the post content for review
2. **Wait for Approval** - The executor will handle approval via:
   - Frontend: POST to /approval/drafts/{draft_id}/approve
   - Backend: Check via /approval/drafts/{draft_id}/wait
   - API: Call approval service directly
3. **Apply Feedback** - Modify if user requests changes
4. **Publish** - Only publish after explicit approval

## Workflow State Machine
```
create_draft -> await_approval -> [approved] -> publish -> END
                            -> [modify] -> create_draft
                            -> [rejected] -> END
                            -> [timeout] -> END
```

## Platform Configuration
- TikTok: max title 2200 chars, supports hashtags in caption
- Instagram: REELS for videos, supports descriptions
- YouTube: Requires title, supports description, tags
- Facebook: Requires page_id for page posts
- X/Twitter: Auto-threads for long text
- Threads: Auto-threads for text >500 chars
- LinkedIn: Supports link previews
- Reddit: Requires subreddit parameter
- Bluesky: Max 300 chars per post, auto-threads

## Error Handling
- Handle API errors gracefully and suggest corrections
- If platform-specific params missing, explain what's needed
- Report upload status with request_id for tracking

## Output Format
Always format responses clearly with:
- Platform(s) targeted
- Content preview
- Status/action required
- Next steps
"""


class PostingAgent:
    def __init__(self, api_key: str = None) -> None:
        self.mcp_client = MultiServerMCPClient(
            {
                "posting_tools": StdioConnection(
                    transport="stdio",
                    command="python",
                    args=["-m", "mcp_servers.posting_servers.mcp_server"],
                )
            }
        )
        self.api_key = api_key
        self.agent = None
        self.graph = None

    async def initialize(self):
        tools = await self.mcp_client.get_tools()
        if self.api_key is None:
            raise RuntimeError("No API Key provided")

        self.agent = create_agent(
            ChatLiteLLM(
                model="gemini/gemini-2.5-flash", max_tokens=4000, api_key=self.api_key
            ),
            tools,
            name="PostingAgent",
            system_prompt=SYSTEM_PROMPT,
        )
        self.graph = self._build_human_feedback_graph()
        print("PostingAgent initialized with tools:", [t.name for t in tools])
        return self

    def _build_human_feedback_graph(self) -> StateGraph:
        workflow = StateGraph(PostingState)

        workflow.add_node("parse_request", self._parse_request_node)
        workflow.add_node("create_draft", self._create_draft_node)
        workflow.add_node("await_human_feedback", self._await_feedback_node)
        workflow.add_node("apply_feedback", self._apply_feedback_node)
        workflow.add_node("publish", self._publish_node)
        workflow.add_node("handle_failure", self._failure_node)

        workflow.set_entry_point("parse_request")

        workflow.add_edge("parse_request", "create_draft")
        workflow.add_edge("create_draft", "await_human_feedback")
        workflow.add_conditional_edges(
            "await_human_feedback",
            self._route_feedback,
            {
                "approved": "publish",
                "modify": "apply_feedback",
                "rejected": END,
                "timeout": END,
            },
        )
        workflow.add_edge("apply_feedback", "create_draft")
        workflow.add_edge("publish", END)
        workflow.add_edge("handle_failure", END)

        return workflow.compile()

    async def _parse_request_node(self, state: PostingState) -> PostingState:
        prompt = state.get("messages", [HumanMessage(content="")])[-1].content

        parsed = {
            "user_intent": prompt,
            "user": "default",
            "content_type": "text",
            "platform": ["tiktok"],
            "content": prompt,
            "post_status": PostStatus.DRAFT,
            "draft_id": f"draft_{uuid.uuid4().hex[:8]}",
        }

        return {**state, **parsed}

    async def _create_draft_node(self, state: PostingState) -> PostingState:
        draft_preview = self._format_draft_preview(state)

        return {
            **state,
            "post_status": PostStatus.PENDING_APPROVAL,
            "requires_approval": True,
            "messages": [*state["messages"], AIMessage(content=draft_preview)],
        }

    def _format_draft_preview(self, state: PostingState) -> str:
        platform_str = ", ".join(state.get("platform", []))
        content = state.get("content", "")
        description = state.get("description", "")
        hashtags = state.get("hashtags", [])
        scheduled = state.get("scheduled_date", "Immediately")

        preview = f"""
📝 **Post Draft Preview**

**Platform(s):** {platform_str}
**Content Type:** {state.get("content_type", "text")}

**Title/Content:**
{content}

**Description:** {description or "None"}

**Hashtags:** {", ".join(["#" + h if not h.startswith("#") else h for h in hashtags]) or "None"}

**Schedule:** {scheduled}

---
⏳ **Awaiting Your Approval**

Please respond with:
- **"Approve"** or **"Yes"** - Publish immediately
- **"Modify [your changes]"** - Adjust content before publishing  
- **"Reject"** or **"Cancel"** - Discard this draft
"""
        return preview.strip()

    def _route_feedback(self, state: PostingState) -> str:
        feedback = state.get("human_feedback", "").lower().strip()

        if not feedback:
            return "timeout"

        if any(
            word in feedback
            for word in ["approve", "yes", "publish", "ok", "go", "post"]
        ):
            return "approved"
        elif any(
            word in feedback
            for word in ["modify", "change", "update", "edit", "adjust"]
        ):
            return "modify"
        else:
            return "rejected"

    async def _await_feedback_node(self, state: PostingState) -> PostingState:
        return {
            **state,
            "messages": [
                *state["messages"],
                AIMessage(content="Waiting for human approval..."),
            ],
        }

    async def _apply_feedback_node(self, state: PostingState) -> PostingState:
        feedback = state.get("human_feedback", "")

        update_msg = f"""
User requested modifications:
{feedback}

Please update the post content accordingly.
"""

        return {
            **state,
            "messages": [*state["messages"], AIMessage(content=update_msg)],
            "post_status": PostStatus.DRAFT,
        }

    async def _publish_node(self, state: PostingState) -> PostingState:
        from langchain_core.messages import HumanMessage

        user = state.get("user", "default")
        platform = state.get("platform", ["tiktok"])
        content_type = state.get("content_type", "text")
        content = state.get("content", "")
        description = state.get("description")
        hashtags = state.get("hashtags", [])
        scheduled = state.get("scheduled_date")

        if content_type == "video":
            tool_name = "upload_video"
            params = {
                "user": user,
                "platform": platform,
                "video_path": state.get("media_paths", [""])[0]
                or "https://example.com/video.mp4",
                "title": content,
            }
            if description:
                params["description"] = description
        elif content_type == "photo":
            tool_name = "upload_photos"
            params = {
                "user": user,
                "platform": platform,
                "photos": state.get("media_paths", []),
                "title": content,
            }
        else:
            tool_name = "upload_text"
            params = {
                "user": user,
                "platform": platform,
                "title": content,
            }
            if description:
                params["description"] = description

        if scheduled:
            params["scheduled_date"] = scheduled

        if hashtags:
            params["first_comment"] = " ".join(
                [f"#{h}" if not h.startswith("#") else h for h in hashtags]
            )

        response = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=f"Use {tool_name} tool with: {params}")]}
        )

        result_content = response["messages"][-1].content

        success_msg = f"""
✅ **Post Published Successfully!**

**Platform(s):** {", ".join(platform)}
**Status:** {state.get("post_status", "published").value}

{result_content}

---
Draft ID: {state.get("draft_id")}
"""

        return {
            **state,
            "post_status": PostStatus.PUBLISHED,
            "result": {"success": True, "response": result_content},
            "messages": [*state["messages"], AIMessage(content=success_msg)],
        }

    async def _failure_node(self, state: PostingState) -> PostingState:
        error_msg = f"""
❌ **Posting Failed**

Error: {state.get("error", "Unknown error")}

Draft ID: {state.get("draft_id")}
Please try again or contact support.
"""
        return {
            **state,
            "post_status": PostStatus.FAILED,
            "messages": [*state["messages"], AIMessage(content=error_msg)],
        }

    async def answer_query(
        self,
        prompt: str,
        human_feedback: str = None,
        user: str = "default",
        platform: list[str] = None,
        content_type: str = "text",
        scheduled_date: str = None,
    ) -> str:
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        initial_state = PostingState(
            messages=[HumanMessage(content=prompt)],
            user_intent=prompt,
            user=user,
            content_type=content_type,
            content=prompt,
            description=None,
            platform=platform or ["tiktok"],
            hashtags=[],
            media_paths=[],
            scheduled_date=scheduled_date,
            first_comment=None,
            post_status=PostStatus.DRAFT,
            draft_id=f"draft_{uuid.uuid4().hex[:8]}",
            request_id=None,
            job_id=None,
            human_feedback=human_feedback,
            requires_approval=True,
            result=None,
            error=None,
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["messages"][-1].content

    async def create_draft_and_wait(
        self,
        content: str,
        user: str,
        platform: list[str],
        content_type: str = "text",
        description: str = None,
        hashtags: list[str] = None,
        media_paths: list[str] = None,
        scheduled_date: str = None,
        first_comment: str = None,
        timeout_seconds: int = 3600,
    ) -> dict:
        from app.approval.service import approval_service, DraftContent

        draft_id = f"draft_{uuid.uuid4().hex[:8]}"

        draft_content = DraftContent(
            content_type=content_type,
            user=user,
            platform=platform,
            title=content,
            description=description,
            hashtags=hashtags or [],
            media_urls=media_paths or [],
            scheduled_date=scheduled_date,
            first_comment=first_comment,
        )

        callback_url = os.getenv("APPROVAL_CALLBACK_URL", "")
        if callback_url:
            callback_url = f"{callback_url}/approval/drafts/{draft_id}/approve"

        approval_service.create_draft(
            draft_id=draft_id,
            content=draft_content,
            callback_url=callback_url,
        )

        draft_preview = f"""
📝 **Draft Created - Awaiting Approval**

**Draft ID:** {draft_id}
**Platform(s):** {", ".join(platform)}
**Content:** {content}

**Approval URL:** /approval/drafts/{draft_id}
**Approval API:** POST /approval/drafts/{draft_id}/approve
"""

        return {
            "draft_id": draft_id,
            "preview": draft_preview.strip(),
            "approval_url": f"/approval/drafts/{draft_id}",
            "status": "pending_approval",
        }

    async def check_and_publish(
        self,
        draft_id: str,
        auto_modifications: str = None,
    ) -> dict:
        from app.approval.service import approval_service, ApprovalStatus

        status = await approval_service.wait_for_approval(draft_id, timeout_seconds=10)

        if status == ApprovalStatus.APPROVED:
            draft = approval_service.get_draft(draft_id)
            return {
                "status": "approved",
                "draft": draft,
                "can_publish": True,
                "modifications": draft.modifications if draft else None,
            }
        elif status == ApprovalStatus.REJECTED:
            return {"status": "rejected", "can_publish": False}
        else:
            return {"status": status.value, "can_publish": False}
