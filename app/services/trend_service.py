import asyncio
import os
import uuid
from typing import TYPE_CHECKING

from app.schema.trend import (
    TrendAnalysesListResponse,
    TrendAnalysisRecordResponse,
    TrendAnalyzeResponse,
    TrendOverviewResponse,
)
from app.services.postgres_service import PostgresService
from app.services.user_context import resolve_user_id

if TYPE_CHECKING:
    from agents.trend_agent.agent import TrendAgent


class TrendService:
    _agent: "TrendAgent | None" = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self.postgres = PostgresService()

    async def analyze(
        self,
        query: str,
        limit: int = 3,
        user_id: uuid.UUID | None = None,
    ) -> TrendAnalyzeResponse:
        resolved_user_id = resolve_user_id(user_id)
        agent = await self._get_agent()
        prompt = self._build_prompt(query=query, limit=limit)
        result = await agent.answer_query(prompt)

        structured = result.get("structured_data") or {}
        response = TrendAnalyzeResponse(
            query=structured.get("query", query),
            results=structured.get("results", []),
            markdown_summary=structured.get("markdown_summary") or result.get("display_text", ""),
            error=structured.get("error"),
        )

        if response.error is not None or result.get("status") not in {"success", "repaired"}:
            if response.error is None:
                response.error = {
                    "type": "agent_status",
                    "message": f"Trend agent returned status: {result.get('status')}",
                }
            return response

        record = await self.postgres.save_trend_analysis(
            query=response.query,
            results=[item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in response.results],
            summary=response.markdown_summary,
            user_id=resolved_user_id,
            status="completed",
            error=None,
        )
        response.analysis_id = record.id
        return response

    async def list_history(
        self,
        user_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> TrendAnalysesListResponse:
        records = await self.postgres.list_trend_analyses(user_id=user_id, limit=limit)
        return TrendAnalysesListResponse(items=[self._to_record_response(record) for record in records])

    async def search_history(
        self,
        text: str,
        user_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> TrendAnalysesListResponse:
        records = await self.postgres.search_trend_analyses(text=text, user_id=user_id, limit=limit)
        return TrendAnalysesListResponse(items=[self._to_record_response(record) for record in records])

    async def get_detail(self, analysis_id: uuid.UUID) -> TrendAnalysisRecordResponse | None:
        record = await self.postgres.get_trend_analysis(analysis_id)
        if record is None:
            return None
        return self._to_record_response(record)

    def get_mock_overview(self, keyword: str, region: str, hashtag: str) -> TrendOverviewResponse:
        return TrendOverviewResponse(
            keyword=keyword,
            region=region,
            hashtag=hashtag,
            overview={
                "message": "Mock overview endpoint is available for UI wiring.",
                "suggested_query": keyword,
                "suggested_hashtag": hashtag,
                "region": region,
            },
        )

    async def _get_agent(self) -> "TrendAgent":
        from agents.trend_agent.agent import TrendAgent

        if self.__class__._agent is not None:
            return self.__class__._agent

        async with self.__class__._lock:
            if self.__class__._agent is None:
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
                self.__class__._agent = await TrendAgent(api_key=api_key).initialize()
        return self.__class__._agent

    def _build_prompt(self, query: str, limit: int) -> str:
        return (
            f"Analyze trends for this topic or keyword set: {query}. "
            f"Return {limit} ranked trend opportunities. "
            "For each item, include: main_keyword, why_the_trend_happens, trend_score, "
            "interest_over_day for the last 24 hours, avg_views_per_hour, recommended_action, "
            "and top_hashtags. Use Google Trends and TikTok signals, stay close to the user's keywords, "
            "return structured JSON only, and write all explanations in Vietnamese."
        )

    def _to_record_response(self, record) -> TrendAnalysisRecordResponse:
        return TrendAnalysisRecordResponse(
            analysis_id=record.id,
            query=record.query,
            results=record.results or [],
            markdown_summary=record.summary or "",
            error=record.error,
            status=record.status,
            user_id=record.user_id,
            created_at=record.created_at,
        )
