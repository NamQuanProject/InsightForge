import asyncio
import copy
import json
import os
import uuid
from typing import Any, TYPE_CHECKING

from app.schema.content import GeneratedContentResponse
from app.services.image_store_service import ImageStoreService
from app.services.postgres_service import PostgresService
from app.services.user_context import resolve_user_id

if TYPE_CHECKING:
    from agents.generating_agent.agent import ContentGenerationAgent


class ContentService:
    _agent: "ContentGenerationAgent | None" = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self.postgres = PostgresService()
        self.image_store = ImageStoreService()

    async def generate(
        self,
        prompt: str | None = None,
        user_id: uuid.UUID | None = None,
        trend_analysis_id: uuid.UUID | None = None,
        selected_keyword: str | None = None,
    ) -> GeneratedContentResponse:
        resolved_user_id = resolve_user_id(user_id)
        final_prompt = prompt or await self._build_prompt_from_trend(trend_analysis_id, selected_keyword)
        final_prompt = self._with_user_context_instruction(final_prompt, resolved_user_id)

        agent = await self._get_agent()
        result = await agent.answer_query(final_prompt)

        post_content = self._normalize_post_content(result.get("post_content"))
        image_set = await self.image_store.attach_post_images(result.get("image_set"))
        platform_posts = self._normalize_platform_posts(result.get("platform_posts"))
        publishing = self._normalize_publishing(result.get("publishing"))
        main_title = str(result.get("main_title") or post_content.get("title") or "")

        raw_output = copy.deepcopy(result) if isinstance(result, dict) else {}
        raw_output["post_content"] = post_content
        raw_output["image_set"] = image_set
        raw_output["platform_posts"] = platform_posts
        raw_output["publishing"] = publishing

        record = await self.postgres.save_generated_content(
            raw_output=raw_output,
            post_content=post_content,
            image_set=image_set,
            platform_posts=platform_posts,
            publishing=publishing,
            video_script={},
            user_id=resolved_user_id,
            trend_analysis_id=trend_analysis_id,
            selected_keyword=result.get("selected_keyword") or selected_keyword,
            main_title=main_title,
            status="failed" if result.get("error") else "generated",
        )
        return self._to_response(record)

    async def list_contents(
        self,
        user_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[GeneratedContentResponse]:
        records = await self.postgres.list_generated_contents(user_id=user_id, limit=limit)
        return [self._to_response(record) for record in records]

    async def get_content(self, content_id: uuid.UUID) -> GeneratedContentResponse | None:
        record = await self.postgres.get_generated_content(content_id)
        if record is None:
            return None
        return self._to_response(record)

    async def _build_prompt_from_trend(
        self,
        trend_analysis_id: uuid.UUID | None,
        selected_keyword: str | None,
    ) -> str:
        if trend_analysis_id is None:
            raise ValueError("Provide prompt or trend_analysis_id to generate content.")

        analysis = await self.postgres.get_trend_analysis(trend_analysis_id)
        if analysis is None:
            raise ValueError(f"Trend analysis not found: {trend_analysis_id}")

        chosen_item = None
        for item in analysis.results or []:
            if selected_keyword and item.get("main_keyword") == selected_keyword:
                chosen_item = item
                break
        if chosen_item is None and analysis.results:
            chosen_item = analysis.results[0]

        context_json = json.dumps(chosen_item or {}, ensure_ascii=False)
        return (
            "Generate a personalized Vietnamese multi-image social post based on this trend context. "
            "Do not create a video script. Return post_content, image_set, platform_posts, and publishing. "
            f"Original trend query: {analysis.query}. "
            f"Selected keyword: {selected_keyword or (chosen_item or {}).get('main_keyword', '')}. "
            f"Trend context JSON: {context_json}"
        )

    async def _get_agent(self) -> "ContentGenerationAgent":
        from agents.generating_agent.agent import ContentGenerationAgent

        if self.__class__._agent is not None:
            return self.__class__._agent

        async with self.__class__._lock:
            if self.__class__._agent is None:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
                self.__class__._agent = await ContentGenerationAgent(api_key=api_key).initialize()
        return self.__class__._agent

    def _to_response(self, record) -> GeneratedContentResponse:
        post_content = self._normalize_post_content(getattr(record, "post_content", None))
        image_set = getattr(record, "image_set", None)
        platform_posts = self._normalize_platform_posts(record.platform_posts)
        publishing = self._normalize_publishing(getattr(record, "publishing", None))

        return GeneratedContentResponse(
            id=record.id,
            user_id=record.user_id,
            trend_analysis_id=record.trend_analysis_id,
            selected_keyword=record.selected_keyword or "",
            main_title=record.main_title or post_content.get("title") or "",
            post_content=post_content,
            image_set=image_set if isinstance(image_set, list) else [],
            platform_posts=platform_posts,
            publishing=publishing,
            status=record.status,
            created_at=record.created_at,
        )

    def _with_user_context_instruction(self, prompt: str, user_id: uuid.UUID | None) -> str:
        if user_id is None:
            return prompt
        return (
            f"user_id: {user_id}\n"
            "Before generating, call get_user_profile(user_id) and get_latest_generated_content(user_id). "
            "Use about_me, content preferences, keywords, audience persona, and content goal heavily.\n"
            f"{prompt}"
        )

    def _normalize_post_content(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            value = {}
        return {
            "post_type": str(value.get("post_type") or "multi_image_post"),
            "title": str(value.get("title") or ""),
            "hook": str(value.get("hook") or ""),
            "caption": str(value.get("caption") or ""),
            "description": str(value.get("description") or ""),
            "body": str(value.get("body") or ""),
            "call_to_action": str(value.get("call_to_action") or ""),
            "hashtags": self._to_str_list(value.get("hashtags")),
            "tone": str(value.get("tone") or ""),
            "personalization_notes": self._to_str_list(value.get("personalization_notes")),
        }

    def _normalize_platform_posts(self, value: Any) -> dict[str, dict[str, Any]]:
        source = value if isinstance(value, dict) else {}
        return {
            "tiktok": self._normalize_platform_post(source.get("tiktok")),
            "facebook": self._normalize_platform_post(source.get("facebook")),
            "instagram": self._normalize_platform_post(source.get("instagram")),
        }

    def _normalize_platform_post(self, post: Any) -> dict[str, Any]:
        post = post if isinstance(post, dict) else {}
        return {
            "caption": str(post.get("caption") or ""),
            "hashtags": self._to_str_list(post.get("hashtags")),
            "cta": str(post.get("cta") or ""),
            "best_post_time": str(post.get("best_post_time") or ""),
            "image_notes": str(post.get("image_notes") or post.get("thumbnail_description") or ""),
        }

    def _normalize_publishing(self, value: Any) -> dict[str, Any]:
        value = value if isinstance(value, dict) else {}
        return {
            "default_visibility": str(value.get("default_visibility") or ""),
            "recommended_platforms": self._to_str_list(value.get("recommended_platforms")),
            "timezone": str(value.get("timezone") or ""),
            "weekly_content_frequency": self._to_int(value.get("weekly_content_frequency")),
        }

    def _to_str_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item is not None]

    def _to_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
