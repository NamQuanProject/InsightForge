import os
import uuid
import re
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class PostStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class PostDraft:
    draft_id: str
    user: str
    content: str
    content_type: str
    platform: list[str]
    description: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    media_paths: list[str] = field(default_factory=list)
    scheduled_date: Optional[str] = None
    first_comment: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)


SYSTEM_PROMPT = """You are an expert Social Media Posting Assistant."""


class PostingAgent:
    def __init__(self, api_key: str = None) -> None:
        self.api_key = api_key
        self.agent = None
        self.mcp_client = None
        self._drafts: dict[str, PostDraft] = {}

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

        self.agent = create_agent(
            ChatLiteLLM(
                model="gemini/gemini-2.5-flash", max_tokens=2000, api_key=self.api_key
            ),
            tools,
            name="PostingAgent",
            system_prompt=SYSTEM_PROMPT,
        )

        print("PostingAgent initialized with tools:", [t.name for t in tools])
        return self

    def _parse_prompt(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()

        content_type = "text"
        if any(kw in prompt_lower for kw in ["photo", "image", "img"]):
            content_type = "photo"
        elif any(kw in prompt_lower for kw in ["video", "vid"]):
            content_type = "video"

        platforms = []
        platform_map = {
            "instagram": ["instagram", "ig"],
            "tiktok": ["tiktok"],
            "facebook": ["facebook", "fb"],
            "threads": ["threads"],
            "x": ["x twitter", "twitter", "tweet"],
            "youtube": ["youtube", "yt"],
            "linkedin": ["linkedin"],
            "reddit": ["reddit"],
            "bluesky": ["bluesky", "bsky"],
            "pinterest": ["pinterest", "pin"],
        }

        for platform, keywords in platform_map.items():
            for kw in keywords:
                if kw in prompt_lower:
                    if platform not in platforms:
                        platforms.append(platform)
                    break

        if not platforms:
            platforms = ["instagram"]

        media_paths = []
        path_patterns = [
            r"([/\w\-\.]+\.(?:jpg|jpeg|png|gif|mp4|mov|webp|png))",
        ]
        for pattern in path_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            media_paths.extend(matches)

        quotes = re.findall(r"'([^']+)'", prompt)
        if quotes:
            content = quotes[0]
        else:
            content = prompt
            for path in media_paths:
                content = content.replace(path, "")
            content = re.sub(
                r"(?:upload|post|share|publish|send)\s*(?:the|this|some)?\s*(?:photos?|videos?|content)?\s*(?:at|to|on|for)?",
                "",
                content,
                flags=re.IGNORECASE,
            )
            content = re.sub(r"\s+", " ", content).strip()

        hashtags = re.findall(r"#(\w+)", prompt)

        return {
            "content_type": content_type,
            "platform": platforms,
            "content": content,
            "media_paths": media_paths,
            "hashtags": hashtags,
            "user": "blhoang23",
        }

    async def process_prompt(self, prompt: str) -> dict:
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        parsed = self._parse_prompt(prompt)

        platform_str = ", ".join(parsed["platform"])

        preview_lines = [
            f"**Platform:** {platform_str}",
            f"**Content Type:** {parsed['content_type']}",
            f"**Content:** {parsed['content']}",
        ]

        if parsed["media_paths"]:
            preview_lines.append(f"**Media:** {', '.join(parsed['media_paths'])}")

        if parsed["hashtags"]:
            preview_lines.append(
                f"**Hashtags:** {', '.join(['#' + h for h in parsed['hashtags']])}"
            )

        draft_id = f"draft_{uuid.uuid4().hex[:8]}"
        draft = PostDraft(
            draft_id=draft_id,
            user=parsed["user"],
            content=parsed["content"],
            content_type=parsed["content_type"],
            platform=parsed["platform"],
            hashtags=parsed["hashtags"],
            media_paths=parsed["media_paths"],
            status=PostStatus.PENDING_APPROVAL,
        )
        self._drafts[draft_id] = draft

        return {
            "success": True,
            "preview": "\n".join(preview_lines),
            "post_data": parsed,
            "draft_id": draft_id,
        }

    async def execute_post(self, post_data: dict) -> dict:
        if self.agent is None:
            raise RuntimeError("Agent not initialized")

        content_type = post_data.get("content_type", "text")
        platform = post_data.get("platform", ["instagram"])
        content = post_data.get("content", "")
        media_paths = post_data.get("media_paths", [])
        hashtags = post_data.get("hashtags", [])
        user = post_data.get("user", "blhoang23")

        try:
            if content_type == "photo":
                tool_name = "upload_photos"
                params = {
                    "user": user,
                    "platform": platform,
                    "photos": media_paths
                    if media_paths
                    else ["https://example.com/placeholder.jpg"],
                    "title": content,
                }
            elif content_type == "video":
                tool_name = "upload_video"
                params = {
                    "user": user,
                    "platform": platform,
                    "video_path": media_paths[0]
                    if media_paths
                    else "https://example.com/video.mp4",
                    "title": content,
                }
            else:
                tool_name = "upload_text"
                params = {
                    "user": user,
                    "platform": platform,
                    "title": content,
                }

            if hashtags:
                params["first_comment"] = " ".join([f"#{h}" for h in hashtags])

            prompt = f"Use {tool_name} tool with these parameters: {params}"

            response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=prompt)]}
            )

            result_content = response["messages"][-1].content

            return {
                "success": True,
                "response": result_content,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_with_approval_flow(self, **kwargs) -> dict:
        return await self.process_prompt(kwargs.get("content", ""))

    async def handle_user_response(
        self, draft_id: str, response: str, auto_publish: bool = True
    ) -> dict:
        draft = self._drafts.get(draft_id)
        if not draft:
            return {"success": False, "error": "Draft not found"}

        response_lower = response.lower().strip()

        if response_lower in ["yes", "y", "ok", "go", "approve", "post", ""]:
            draft.status = PostStatus.APPROVED
            if auto_publish:
                result = await self.execute_post(
                    {
                        "content_type": draft.content_type,
                        "platform": draft.platform,
                        "content": draft.content,
                        "media_paths": draft.media_paths,
                        "hashtags": draft.hashtags,
                        "user": draft.user,
                    }
                )
                draft.status = PostStatus.PUBLISHED
                return {
                    "success": True,
                    "draft_id": draft_id,
                    "action": "published",
                    "response": result.get("response", ""),
                    "published": True,
                }
            return {"success": True, "draft_id": draft_id, "action": "approved"}

        else:
            draft.status = PostStatus.REJECTED
            return {"success": True, "draft_id": draft_id, "action": "rejected"}

    def list_drafts(self) -> list[dict]:
        return [
            {
                "draft_id": d.draft_id,
                "platform": d.platform,
                "content": d.content[:50] + "..." if len(d.content) > 50 else d.content,
                "status": d.status.value,
            }
            for d in sorted(
                self._drafts.values(), key=lambda x: x.created_at, reverse=True
            )
        ]
