import os
import asyncio
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from a2a.types import Message, TextPart, Part
from agents.posting_agent.agent import PostingAgent


class PostingAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = None
        self._pending_drafts: dict[str, dict] = {}

    async def _ensure_initialized(self) -> None:
        if self.agent is None:
            self.agent = await PostingAgent(
                api_key=os.getenv("GOOGLE_API_KEY")
            ).initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_initialized()

        user_input = context.get_user_input()
        session_id = context.session_id

        await event_queue.enqueue_event(
            new_agent_text_message("🤖 Processing your request...")
        )

        try:
            parsed_input = self._parse_input(user_input)

            if parsed_input.get("action") == "approve":
                result = await self._handle_approval(
                    draft_id=parsed_input.get("draft_id"),
                    event_queue=event_queue,
                )
            elif parsed_input.get("action") == "reject":
                result = await self._handle_rejection(
                    draft_id=parsed_input.get("draft_id"),
                    reason=parsed_input.get("reason"),
                    event_queue=event_queue,
                )
            elif parsed_input.get("action") == "check_status":
                result = await self._check_status(
                    draft_id=parsed_input.get("draft_id"),
                )
            else:
                result = await self._create_draft_and_wait(
                    user_input=user_input,
                    parsed_input=parsed_input,
                    session_id=session_id,
                    event_queue=event_queue,
                )

            await event_queue.enqueue_event(new_agent_text_message(result))

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_msg))

    def _parse_input(self, user_input: str) -> dict:
        input_lower = user_input.lower().strip()

        if input_lower.startswith("approve "):
            parts = user_input.split(maxsplit=1)
            return {
                "action": "approve",
                "draft_id": parts[1] if len(parts) > 1 else None,
            }

        if input_lower.startswith("reject "):
            parts = user_input.split(maxsplit=2)
            return {
                "action": "reject",
                "draft_id": parts[1] if len(parts) > 1 else None,
                "reason": parts[2] if len(parts) > 2 else None,
            }

        if input_lower.startswith("check "):
            parts = user_input.split(maxsplit=1)
            return {
                "action": "check_status",
                "draft_id": parts[1] if len(parts) > 1 else None,
            }

        return {"action": "create_post"}

    async def _create_draft_and_wait(
        self,
        user_input: str,
        parsed_input: dict,
        session_id: str,
        event_queue: EventQueue,
    ) -> str:
        user = parsed_input.get("user", "default")
        platform = parsed_input.get("platform", ["tiktok"])
        content_type = parsed_input.get("content_type", "text")
        scheduled_date = parsed_input.get("scheduled_date")

        draft_result = await self.agent.create_draft_and_wait(
            content=user_input,
            user=user,
            platform=platform,
            content_type=content_type,
            scheduled_date=scheduled_date,
        )

        draft_id = draft_result["draft_id"]
        self._pending_drafts[draft_id] = {
            "session_id": session_id,
            "content": user_input,
            "platform": platform,
            "created_at": asyncio.get_event_loop().time(),
        }

        approval_guide = f"""
{draft_result["preview"]}

---
**How to Approve/Reject:**

📱 **Via Frontend:** Visit {draft_result["approval_url"]}

🔗 **Via API:**
- Approve: POST /approval/drafts/{draft_id}/approve
- Reject: POST /approval/drafts/{draft_id}/reject

💬 **Or reply here with:**
- "approve {draft_id}" to publish
- "reject {draft_id}" to cancel
"""
        return approval_guide

    async def _handle_approval(
        self,
        draft_id: str,
        event_queue: EventQueue,
    ) -> str:
        from app.approval.service import approval_service

        if draft_id not in self._pending_drafts:
            return f"⚠️ Draft {draft_id} not found or already processed"

        draft_info = self._pending_drafts[draft_id]

        result = await approval_service.approve(
            draft_id=draft_id,
            approved_by="a2a_user",
        )

        if result["success"]:
            draft = approval_service.get_draft(draft_id)
            content = draft.content if draft else None

            if content:
                publish_result = await self.agent.answer_query(
                    prompt=f"Publish this post: {content.title}",
                    user=content.user,
                    platform=content.platform,
                    content_type=content.content_type,
                    scheduled_date=content.scheduled_date,
                )

                del self._pending_drafts[draft_id]
                return f"✅ Approved and Publishing!\n\n{publish_result}"

        return f"❌ Approval failed: {result.get('error', 'Unknown error')}"

    async def _handle_rejection(
        self,
        draft_id: str,
        reason: str,
        event_queue: EventQueue,
    ) -> str:
        from app.approval.service import approval_service

        if draft_id not in self._pending_drafts:
            return f"⚠️ Draft {draft_id} not found or already processed"

        result = await approval_service.reject(
            draft_id=draft_id,
            rejected_by="a2a_user",
            reason=reason,
        )

        del self._pending_drafts[draft_id]

        if result["success"]:
            return f"🚫 Draft {draft_id} rejected."

        return f"❌ Rejection failed: {result.get('error', 'Unknown error')}"

    async def _check_status(self, draft_id: str) -> str:
        from app.approval.service import approval_service

        draft = approval_service.get_draft(draft_id)

        if not draft:
            return f"⚠️ Draft {draft_id} not found"

        status_emoji = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "🚫",
            "expired": "⏰",
        }

        emoji = status_emoji.get(draft.status.value, "❓")

        return f"""
{emoji} **Draft Status: {draft.status.value.upper()}**

**Draft ID:** {draft.draft_id}
**Platform:** {", ".join(draft.content.platform)}
**Title:** {draft.content.title}
**Created:** {draft.created_at.isoformat()}
**Expires:** {draft.expires_at.isoformat()}
"""

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass
