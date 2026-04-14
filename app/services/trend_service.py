import asyncio
import os
from typing import Any

from agents.trend_agent.agent import TrendAgent
from app.schema.trend import TrendAnalyzeResponse, TrendOverviewResponse


class TrendService:
    _agent: TrendAgent | None = None
    _lock = asyncio.Lock()

    async def analyze(self, query: str, limit: int = 3) -> TrendAnalyzeResponse:
        agent = await self._get_agent()
        prompt = self._build_prompt(query=query, limit=limit)
        result = await agent.answer_query(prompt)

        structured = result.get("structured_data") or {}
        return TrendAnalyzeResponse(
            query=structured.get("query", query),
            results=structured.get("results", []),
            markdown_summary=structured.get("markdown_summary")
            or result.get("display_text", ""),
            error=structured.get("error"),
        )

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

    async def _get_agent(self) -> TrendAgent:
        if self.__class__._agent is not None:
            return self.__class__._agent

        async with self.__class__._lock:
            if self.__class__._agent is None:
                api_key = os.getenv("OPENAI_API_KEY")
                self.__class__._agent = await TrendAgent(api_key=api_key).initialize()
        return self.__class__._agent

    def _build_prompt(self, query: str, limit: int) -> str:
        return (
            f"Hãy phân tích xu hướng cho chủ đề hoặc bộ từ khóa sau: {query}. "
            f"Trả về {limit} cơ hội xu hướng đã được xếp hạng. "
            "Với mỗi mục, hãy gồm: main_keyword, why_the_trend_happens, trend_score, "
            "interest_over_day trong 24 giờ gần nhất, avg_views_per_hour, "
            "recommended_action, và top_hashtags. "
            "Sử dụng tín hiệu từ Google Trends và TikTok, bám sát bộ từ khóa người dùng cung cấp, "
            "và chỉ trả về structured JSON. "
            "Toàn bộ phần nội dung giải thích, tóm tắt, khuyến nghị phải viết bằng tiếng Việt."
        )
