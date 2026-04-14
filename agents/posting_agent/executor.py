import asyncio
import uuid
from typing import Optional, Any
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message
from agents.posting_agent.agent import PostingAgent


class PostingAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self._agent: Optional[PostingAgent] = None
        self._session_threads: dict[str, str] = {}
        self._pending_interrupts: dict[str, dict] = {}

    async def _get_agent(self) -> PostingAgent:
        if self._agent is None:
            import os

            self._agent = PostingAgent(api_key=os.getenv("GOOGLE_API_KEY"))
            await self._agent.initialize()
        return self._agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_input = context.get_user_input()
        session_id = context.session_id
        print("YES YES YES")
        if not user_input or not user_input.strip():
            await event_queue.enqueue_event(
                new_agent_text_message("Please provide a message.")
            )
            return

        await event_queue.enqueue_event(
            new_agent_text_message("🤖 Processing your request...")
        )

        try:
            parsed = self._parse_input(user_input)

            if parsed["action"] == "approve":
                result = await self._handle_approve(
                    draft_id=parsed["draft_id"],
                    event_queue=event_queue,
                )
            elif parsed["action"] == "reject":
                result = await self._handle_reject(
                    draft_id=parsed["draft_id"],
                    reason=parsed.get("reason"),
                    event_queue=event_queue,
                )
            elif parsed["action"] == "resume":
                result = await self._handle_resume(
                    session_id=session_id,
                    decisions=parsed.get("decisions", [{"type": "approve"}]),
                    event_queue=event_queue,
                )
            else:
                result = await self._handle_chat(
                    user_input=user_input,
                    session_id=session_id,
                    event_queue=event_queue,
                )

            await event_queue.enqueue_event(new_agent_text_message(result))

        except Exception as e:
            import traceback

            error_detail = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            await event_queue.enqueue_event(new_agent_text_message(error_detail))

    async def _handle_chat(
        self,
        user_input: str,
        session_id: str,
        event_queue: EventQueue,
    ) -> str:
        agent = await self._get_agent()

        thread_id = self._session_threads.get(session_id)
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            self._session_threads[session_id] = thread_id

        config, result = await agent.chat_with_thread(
            user_input=user_input,
            thread_id=thread_id,
        )

        if hasattr(result, "interrupts") and result.interrupts:
            interrupt = result.interrupts[0]
            self._pending_interrupts[session_id] = {
                "config": config,
                "interrupt": interrupt,
                "thread_id": thread_id,
            }

            interrupt_value = interrupt.value
            action_requests = interrupt_value.get("action_requests", [])
            review_configs = interrupt_value.get("review_configs", [])

            config_map = {cfg["action_name"]: cfg for cfg in review_configs}

            lines = ["⏸️ **Action Paused - Approval Required**\n"]
            for action in action_requests:
                review_config = config_map.get(action["name"], {})
                allowed = review_config.get("allowed_decisions", ["approve", "reject"])
                lines.append(
                    f"**Tool:** {action['name']}\n"
                    f"**Arguments:** {action.get('args', {})}\n"
                    f"**Allowed decisions:** {', '.join(allowed)}\n"
                )

            lines.append(f"\n💡 Reply with `approve` or `reject` to continue.")
            return "\n".join(lines)

        messages = result.get("messages", []) if isinstance(result, dict) else []
        if messages:
            last_message = messages[-1]
            return (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

        return "I processed your request but have no response."

    def _parse_input(self, user_input: str) -> dict:
        input_lower = user_input.lower().strip()
        parts = user_input.split(maxsplit=2)

        if input_lower.startswith("approve") or input_lower == "approve":
            return {"action": "approve", "draft_id": None}

        if input_lower.startswith("reject") or input_lower == "reject":
            return {
                "action": "reject",
                "draft_id": None,
                "reason": parts[1] if len(parts) > 1 else None,
            }

        if input_lower in ["resume", "continue", "yes", "y"]:
            return {"action": "resume", "decisions": [{"type": "approve"}]}

        return {"action": "chat", "content": user_input}

    async def _handle_approve(
        self,
        draft_id: Optional[str],
        event_queue: EventQueue,
    ) -> str:
        return "✅ Approved. Use `resume` or `continue` to proceed with the action."

    async def _handle_reject(
        self,
        draft_id: Optional[str],
        reason: Optional[str],
        event_queue: EventQueue,
    ) -> str:
        return "🚫 Rejected. Use `resume` or provide more details."

    async def _handle_resume(
        self,
        session_id: str,
        decisions: list,
        event_queue: EventQueue,
    ) -> str:
        if session_id not in self._pending_interrupts:
            return "⚠️ No pending action to resume."

        interrupt_info = self._pending_interrupts[session_id]
        agent = await self._get_agent()
        config = interrupt_info["config"]

        try:
            resume_result = await agent.resume(config=config, decisions=decisions)

            del self._pending_interrupts[session_id]

            messages = (
                resume_result.get("messages", [])
                if isinstance(resume_result, dict)
                else []
            )
            if messages:
                last_message = messages[-1]
                return (
                    last_message.content
                    if hasattr(last_message, "content")
                    else str(resume_result)
                )

            return "✅ Action completed successfully."

        except Exception as e:
            return f"❌ Error resuming action: {str(e)}"

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        session_id = context.session_id
        if session_id in self._session_threads:
            del self._session_threads[session_id]
        if session_id in self._pending_interrupts:
            del self._pending_interrupts[session_id]
