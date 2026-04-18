import json
import os
from typing import Annotated, Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

from agents.trend_agent.structured_output import (
    GoogleSummary,
    TikTokSummary,
    TrendReport,
    TrendResult,
)


SYSTEM_PROMPT = """
You are an elite Viral Trend Intelligence Analyst.
Your job is to turn a user's topic into a compact shortlist of trend opportunities for content creators. 
You should filter only trends that are capable of being viral (For example, trends that are familiar with youngsters).

You have access to:
1. Google Trends for demand and momentum.
2. TikTok search for social velocity and hashtags.

## Required workflow
1. Discover or validate keywords from the user's request.
2. Use Google tools to inspect 24-hour trend movement.
3. Use TikTok only for the final shortlisted keywords and use tiktok_search keywords for posts and extract the URL for some tiktok videos in this, store in "top_videos" field in output JSON.
4. For each shortlisted keyword, call `classify_trend_signals`.
5. Assemble the final JSON with `build_trend_report`.

## Output shape
Return JSON matching this structure:
{
  "query": "...",
  "results": [
    {
      "main_keyword": "...",
      "why_the_trend_happens": "...",
      "trend_score": 0,
      "interest_over_day": [0, 0, 0],
      "avg_views_per_hour": 0,
      "recommended_action": "...",
      "top_hashtags": ["#example"],
      "top_videos": ["titkok_video_url1", "tiktok_video_url2"],
      "google": {
        "keyword": "...",
        "momentum": "rising",
        "peak_region": "..."
      },
      "tiktok": {
        "platform": "TikTok",
        "top_velocity": 0,
        "avg_engagement_rate": 0
      },
      "threads": null
    }
  ],
  "markdown_summary": "..."
}

## Rules
- ALWAYS write all user-facing explanations in Vietnamese.
- Keep actual hashtags and proper nouns unchanged.
- Do not fabricate numbers.
- Prefer at most two TikTok calls in one run.
- If TikTok data errors or is unavailable, continue with Google data and set social metrics conservatively.
- STRICTLY OUTPUT JSON ONLY.
"""

JSON_REPAIR_PROMPT = """
You are a strict JSON formatter.
Convert the provided trend analysis text into valid JSON matching this exact shape:
{
  "query": "...",
  "results": [
    {
      "main_keyword": "...",
      "why_the_trend_happens": "...",
      "trend_score": 0,
      "interest_over_day": [0, 0, 0],
      "avg_views_per_hour": 0,
      "recommended_action": "...",
      "top_hashtags": [],
      "google": {
        "keyword": "...",
        "momentum": "stable",
        "peak_region": null
      },
      "tiktok": null,
      "threads": null
    }
  ],
  "markdown_summary": "..."
}

Rules:
- Output JSON only.
- Write explanations in Vietnamese.
- If some metrics are missing, keep safe defaults such as 0, [], null, or "stable".
- Do not invent TikTok metrics if they are not present.
"""


@tool
def classify_trend_signals(
    google_momentum: Annotated[str, "One of: rising, stable, declining, unknown"],
    social_velocity: Annotated[float, "TikTok average velocity in views/hour, 0 if unavailable"],
    social_engagement_rate: Annotated[float, "Average engagement rate from TikTok, 0 if unavailable"],
) -> dict[str, Any]:
    """
    Produce a deterministic trend score and explanation for one candidate keyword.
    """
    momentum = google_momentum.lower()
    is_google_rising = momentum == "rising"

    velocity_points = min(50.0, max(social_velocity, 0.0) / 5000.0)
    momentum_bonus = 15.0 if is_google_rising else 0.0
    engagement_bonus = max(social_engagement_rate, 0.0) * 100.0
    trend_score = round(min(100.0, 20.0 + velocity_points + momentum_bonus + engagement_bonus), 1)

    if is_google_rising and social_velocity > 5000:
        reason = "Từ khóa đang có cả nhu cầu tìm kiếm lẫn độ lan truyền tốt trên TikTok."
    elif social_velocity > 10000:
        reason = "Tín hiệu TikTok đang tăng nhanh, cho thấy khả năng viral sớm."
    elif is_google_rising:
        reason = "Nhu cầu tìm kiếm đang tăng nhưng tín hiệu mạng xã hội còn ở mức vừa phải."
    else:
        reason = "Tín hiệu hiện tại ở mức theo dõi, chưa đủ mạnh để xem là bùng nổ."

    return {
        "trend_score": trend_score,
        "confidence": round(min(0.95, 0.4 + trend_score / 100.0), 2),
        "reasoning": reason,
    }


@tool
def build_trend_report(
    query: str,
    results_data: list[dict[str, Any]],
    markdown_summary: str,
) -> str:
    """
    Final step: normalize the shortlisted trend items into the exact JSON shape.
    """
    processed_results: list[TrendResult] = []

    for item in results_data:
        result = TrendResult(
            main_keyword=item["main_keyword"],
            why_the_trend_happens=item["why_the_trend_happens"],
            trend_score=float(item["trend_score"]),
            interest_over_day=[float(value) for value in item.get("interest_over_day", [])],
            avg_views_per_hour=float(item.get("avg_views_per_hour", 0)),
            recommended_action=item.get("recommended_action", ""),
            top_videos=item.get("top_videos", []),
            top_hashtags=item.get("top_hashtags", []),
            google=GoogleSummary(
                keyword=item.get("google", {}).get("keyword", item["main_keyword"]),
                momentum=item.get("google", {}).get("momentum", "stable"),
                peak_region=item.get("google", {}).get("peak_region"),
            ),
            tiktok=(
                TikTokSummary(
                    top_velocity=float(item.get("tiktok", {}).get("top_velocity", 0)),
                    avg_engagement_rate=float(item.get("tiktok", {}).get("avg_engagement_rate", 0)),
                )
                if item.get("tiktok") is not None
                else None
            ),
            threads=item.get("threads"),
        )
        processed_results.append(result)

    report = TrendReport(
        query=query,
        results=processed_results,
        markdown_summary=markdown_summary,
    )
    return report.model_dump_json(indent=2, ensure_ascii=False)


REASONING_TOOLS = [
    classify_trend_signals,
    build_trend_report,
]


class TrendAgent:
    """LangChain wrapper for the Trend Analysis agent."""

    def __init__(self, api_key: str | None = None) -> None:
        self.mcp_client = MultiServerMCPClient(
            {
                "google_trends": StdioConnection(
                    transport="stdio",
                    command="python",
                    args=["-m", "mcp_servers.trends_servers.server"],
                ),
                "social_media_trends": StdioConnection(
                    transport="stdio",
                    command="python",
                    args=["-m", "mcp_servers.social_media_servers.server"],
                ),
            }
        )
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("TREND_AGENT_MODEL", "gemini/gemini-2.5-flash")
        self.agent = None
        self.repair_model = None

    async def initialize(self) -> "TrendAgent":
        tools = await self.mcp_client.get_tools()
        if self.api_key is None:
            raise RuntimeError("No LLM API key provided. Set GOOGLE_API_KEY or GEMINI_API_KEY.")

        allowed_tool_names = {"get_trends", "search_term", "tiktok_search_keyword"}
        filtered_tools = [tool_obj for tool_obj in tools if tool_obj.name in allowed_tool_names]
        all_tools = filtered_tools + REASONING_TOOLS

        llm = ChatLiteLLM(
            model=self.model_name,
            max_tokens=4000,
            api_key=self.api_key,
        )
        self.repair_model = llm

        self.agent = create_agent(
            llm,
            all_tools,
            name="TrendIntelligenceAgent",
            system_prompt=SYSTEM_PROMPT,
        )
        print("Agent initialized with tools: \n", all_tools)
        print("Model:", self.model_name)
        print("\nNumber of tools: ", len(all_tools))
        return self

    async def answer_query(self, prompt: str) -> dict[str, Any]:
        if self.agent is None:
            raise RuntimeError("Agent not initialized.")

        try:
            response = await self.agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        except Exception as exc:
            message = (
                "Trend agent khong the tao bao cao co cau truc. "
                f"Model: {self.model_name}. Error: {exc}"
            )
            return {
                "display_text": message,
                "structured_data": {
                    "query": prompt,
                    "results": [],
                    "markdown_summary": message,
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                },
                "status": "error",
            }

        raw_content = response["messages"][-1].content
        if isinstance(raw_content, list):
            raw_content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            )
        clean_json = str(raw_content).replace("```json", "").replace("```", "").strip()

        try:
            report_data = json.loads(clean_json)
            display_text = report_data.get("markdown_summary") or self._fallback_summary(report_data)
            return {
                "display_text": display_text,
                "structured_data": report_data,
                "status": "success",
            }
        except json.JSONDecodeError:
            repaired = await self._repair_to_json(prompt=prompt, raw_content=str(raw_content))
            if repaired is not None:
                display_text = repaired.get("markdown_summary") or self._fallback_summary(repaired)
                return {
                    "display_text": display_text,
                    "structured_data": repaired,
                    "status": "repaired",
                }
            return {
                "display_text": str(raw_content),
                "structured_data": None,
                "status": "partial_success",
            }

    def _fallback_summary(self, report_data: dict[str, Any]) -> str:
        results = report_data.get("results") or []
        if not results:
            return "Khong co ket qua xu huong phu hop."

        lines = ["## Tom tat xu huong"]
        for index, item in enumerate(results, start=1):
            lines.append(
                f"{index}. {item.get('main_keyword', 'Unknown keyword')} - "
                f"trend_score {item.get('trend_score', 0)}, "
                f"avg_views_per_hour {item.get('avg_views_per_hour', 0)}"
            )
        return "\n".join(lines)

    async def _repair_to_json(self, prompt: str, raw_content: str) -> dict[str, Any] | None:
        if self.repair_model is None:
            return None

        try:
            repaired = await self.repair_model.ainvoke(
                [
                    {"role": "system", "content": JSON_REPAIR_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Original user query:\n{prompt}\n\n"
                            f"Trend analysis text to convert:\n{raw_content}"
                        ),
                    },
                ]
            )
            repaired_content = repaired.content
            if isinstance(repaired_content, list):
                repaired_content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in repaired_content
                )
            cleaned = str(repaired_content).replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception:
            return None
