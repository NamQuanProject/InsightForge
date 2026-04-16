# import asyncio
# import json
# import os
# import uuid
# from typing import TYPE_CHECKING

# from app.schema.content import GeneratedContentResponse
# from app.services.postgres_service import PostgresService

# if TYPE_CHECKING:
#     from agents.generating_agent.agent import ContentGenerationAgent


# class ContentService:
#     _agent: "ContentGenerationAgent | None" = None
#     _lock = asyncio.Lock()

#     def __init__(self) -> None:
#         self.postgres = PostgresService()

#     async def generate(
#         self,
#         prompt: str | None = None,
#         user_id: uuid.UUID | None = None,
#         trend_analysis_id: uuid.UUID | None = None,
#         selected_keyword: str | None = None,
#     ) -> GeneratedContentResponse:
#         final_prompt = prompt or await self._build_prompt_from_trend(trend_analysis_id, selected_keyword)
#         agent = await self._get_agent()
#         result = await agent.answer_query(final_prompt)

#         video_script = result.get("video_script") or {}
#         post_content = result.get("post_content") or {}
#         thumbnail = result.get("image_result") or result.get("image_generation")
#         main_title = video_script.get("title") if isinstance(video_script, dict) else None
#         music_background = video_script.get("music_mood") if isinstance(video_script, dict) else None

#         record = await self.postgres.save_generated_content(
#             raw_output=result,
#             video_script=video_script,
#             platform_posts=post_content if isinstance(post_content, dict) else {"default": post_content},
#             thumbnail=thumbnail if isinstance(thumbnail, dict) else {"value": thumbnail} if thumbnail else None,
#             user_id=user_id,
#             trend_analysis_id=trend_analysis_id,
#             selected_keyword=selected_keyword,
#             main_title=main_title,
#             music_background=music_background,
#         )
#         return self._to_response(record)

#     async def list_contents(
#         self,
#         user_id: uuid.UUID | None = None,
#         limit: int = 20,
#     ) -> list[GeneratedContentResponse]:
#         records = await self.postgres.list_generated_contents(user_id=user_id, limit=limit)
#         return [self._to_response(record) for record in records]

#     async def get_content(self, content_id: uuid.UUID) -> GeneratedContentResponse | None:
#         record = await self.postgres.get_generated_content(content_id)
#         if record is None:
#             return None
#         return self._to_response(record)

#     async def _build_prompt_from_trend(
#         self,
#         trend_analysis_id: uuid.UUID | None,
#         selected_keyword: str | None,
#     ) -> str:
#         if trend_analysis_id is None:
#             raise ValueError("Provide prompt or trend_analysis_id to generate content.")

#         analysis = await self.postgres.get_trend_analysis(trend_analysis_id)
#         if analysis is None:
#             raise ValueError(f"Trend analysis not found: {trend_analysis_id}")

#         chosen_item = None
#         for item in analysis.results or []:
#             if selected_keyword and item.get("main_keyword") == selected_keyword:
#                 chosen_item = item
#                 break
#         if chosen_item is None and analysis.results:
#             chosen_item = analysis.results[0]

#         context_json = json.dumps(chosen_item or {}, ensure_ascii=False)
#         return (
#             "Generate content assets in Vietnamese based on this trend context. "
#             "Return a detailed video script, platform-ready post content, a thumbnail image direction, "
#             "and a suggested music background. "
#             f"Original trend query: {analysis.query}. "
#             f"Selected keyword: {selected_keyword or (chosen_item or {}).get('main_keyword', '')}. "
#             f"Trend context JSON: {context_json}"
#         )

#     async def _get_agent(self) -> "ContentGenerationAgent":
#         from agents.generating_agent.agent import ContentGenerationAgent

#         if self.__class__._agent is not None:
#             return self.__class__._agent

#         async with self.__class__._lock:
#             if self.__class__._agent is None:
#                 api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
#                 self.__class__._agent = await ContentGenerationAgent(api_key=api_key).initialize()
#         return self.__class__._agent

#     def _to_response(self, record) -> GeneratedContentResponse:
#         return GeneratedContentResponse(
#             id=record.id,
#             user_id=record.user_id,
#             trend_analysis_id=record.trend_analysis_id,
#             selected_keyword=record.selected_keyword,
#             main_title=record.main_title,
#             video_script=record.video_script or {},
#             platform_posts=record.platform_posts or {},
#             thumbnail=record.thumbnail,
#             music_background=record.music_background,
#             raw_output=record.raw_output or {},
#             status=record.status,
#             created_at=record.created_at,
#         )
import asyncio
import json
import os
import uuid
from typing import TYPE_CHECKING

from app.schema.content import GeneratedContentResponse
from app.services.postgres_service import PostgresService

if TYPE_CHECKING:
    from agents.generating_agent.agent import ContentGenerationAgent


class ContentService:
    _agent: "ContentGenerationAgent | None" = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self.postgres = PostgresService()

    async def generate(
        self,
        prompt: str | None = None,
        user_id: uuid.UUID | None = None,
        trend_analysis_id: uuid.UUID | None = None,
        selected_keyword: str | None = None,
    ) -> GeneratedContentResponse:
        final_prompt = prompt or await self._build_prompt_from_trend(trend_analysis_id, selected_keyword)
        agent = await self._get_agent()
        result = await agent.answer_query(final_prompt)

        # Per Generating_agent.json schema:
        # - video_script is the full nested object (sections carry per-section thumbnails)
        # - platform_posts is the tiktok/facebook/instagram dict
        # - main_title and music_background are top-level keys, not nested inside video_script
        video_script = result.get("video_script") or {}
        platform_posts = result.get("platform_posts") or {}
        main_title = result.get("main_title")
        music_background = result.get("music_background")

        record = await self.postgres.save_generated_content(
            raw_output=result,
            video_script=video_script,
            platform_posts=platform_posts if isinstance(platform_posts, dict) else {"default": platform_posts},
            user_id=user_id,
            trend_analysis_id=trend_analysis_id,
            selected_keyword=selected_keyword,
            main_title=main_title,
            music_background=music_background,
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
            "Generate content assets in Vietnamese based on this trend context. "
            "Return a detailed video script, platform-ready post content (tiktok, facebook, instagram), "
            "and a suggested music background. "
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
        video_script = record.video_script if isinstance(record.video_script, dict) else {}
        platform_posts = self._normalize_platform_posts(record.platform_posts)
        main_title = record.main_title or video_script.get("title") or ""

        return GeneratedContentResponse(
            id=record.id,
            user_id=record.user_id,
            trend_analysis_id=record.trend_analysis_id,
            selected_keyword=record.selected_keyword or "",
            main_title=main_title,
            video_script=video_script,
            platform_posts=platform_posts,
            music_background=record.music_background or video_script.get("music_mood") or "",
            status=record.status,
            created_at=record.created_at,
        )

    def _normalize_platform_posts(self, value) -> dict:
        if not isinstance(value, dict):
            return {}

        normalized = {}
        for platform, post in value.items():
            if isinstance(post, dict):
                normalized[str(platform)] = {
                    "caption": str(post.get("caption") or ""),
                    "hashtags": [str(item) for item in post.get("hashtags", []) if item is not None]
                    if isinstance(post.get("hashtags"), list)
                    else [],
                    "cta": str(post.get("cta") or ""),
                    "best_post_time": str(post.get("best_post_time") or ""),
                    "thumbnail_description": str(post.get("thumbnail_description") or ""),
                }
            else:
                normalized[str(platform)] = {
                    "caption": str(post or ""),
                    "hashtags": [],
                    "cta": "",
                    "best_post_time": "",
                    "thumbnail_description": "",
                }
        return normalized
