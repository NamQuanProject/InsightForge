from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PostRecord(BaseModel):
    post_id: str
    draft_id: str
    content: str
    platform: str
    hashtags: list[str]
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    metrics: Optional[dict] = None


class AgentMemory:
    def __init__(self, agent_name: str = "PostingAgent") -> None:
        self.agent_name = agent_name
        self.conversation_history: list[dict] = []
        self.post_records: dict[str, PostRecord] = {}
        self.pending_drafts: dict[str, dict] = {}

    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_post_record(self, record: PostRecord) -> None:
        self.post_records[record.post_id] = record

    def get_post_record(self, post_id: str) -> Optional[PostRecord]:
        return self.post_records.get(post_id)

    def add_pending_draft(self, draft_id: str, draft_data: dict) -> None:
        self.pending_drafts[draft_id] = draft_data

    def get_pending_draft(self, draft_id: str) -> Optional[dict]:
        return self.pending_drafts.get(draft_id)

    def approve_draft(self, draft_id: str) -> dict:
        draft = self.pending_drafts.pop(draft_id, None)
        if draft:
            return {"status": "approved", "draft": draft}
        return {"status": "not_found"}

    def reject_draft(self, draft_id: str) -> dict:
        draft = self.pending_drafts.pop(draft_id, None)
        if draft:
            return {"status": "rejected", "draft": draft}
        return {"status": "not_found"}

    def get_recent_posts(self, limit: int = 10) -> list[PostRecord]:
        posts = sorted(
            self.post_records.values(), key=lambda x: x.created_at, reverse=True
        )
        return posts[:limit]

    def clear_history(self) -> None:
        self.conversation_history.clear()
