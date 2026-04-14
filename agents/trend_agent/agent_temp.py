import json
import math
import os
from typing import Annotated, Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

from agents.trend_agent.structured_output import (
    GoogleBlock,
    ThreadsBlock,
    TikTokBlock,
    TrendDiscoveryReport,
    TrendReport,
    TrendResultItem,
)


SYSTEM_PROMPT = """
You are an elite Viral Trend Intelligence Analyst.
Your job is to turn a user's keyword or topic into a shortlist of concrete trend opportunities.
You must use tools and return structured JSON only.

You have access to two complementary signal sources:
1. Google Trends for search demand and interest-over-time.
2. Social platforms (TikTok + Threads) for viral velocity, engagement, and hashtag angles.

## Output Goal
Return a list of 3 results by default, or up to 5 when the user explicitly asks for more or there are enough strong candidates.
Each result item must include:
- `main_keyword`
- `why_the_trend_happens`
- `trend_score`
- `interest_over_day`
- `avg_views_per_hour`
- `recommended_action`
- `top_hashtags`

## Required Workflow
1. Understand the user's topic or keyword(s).
2. Discover candidate keywords:
- If the user asks broadly, use `get_trends` first. Use social validation only after narrowing to the final candidate keywords.
- If the user gives specific keyword(s), stay close to those keywords and their related or rising variants.
3. For each selected candidate keyword, gather structured evidence:
- `search_term` with `TIMESERIES` and `date="now 1-d"` for 24-hour Google interest.
- `search_term` with `RELATED_QUERIES` to explain why the topic is happening now.
- `search_term` with `GEO_MAP_0` when regional context helps.
- `tiktok_search_keyword` to measure social traction and hashtags.
4. Call `score_trend_item` for each result item to produce a deterministic numeric trend score.
5. Build the final JSON using `build_trend_results_report`.

## Output Rules
- `interest_over_day` must come from the Google TIMESERIES `timeline`.
- `avg_views_per_hour` must come from TikTok average velocity.
- `top_hashtags` must be based on TikTok hashtags from tool output, not invented.
- `why_the_trend_happens` must cite the real signal mix: rising related queries, search spikes, trend breakdown terms, or social content angle.
- Prefer concrete keywords over vague themes.
- Keep recommendations concise and actionable for a content creator.
- Minimize expensive social tool calls. Do not fan out across many social keywords.
- Prefer at most one social validation call per final result item, and no more than two social calls total in one run.
- If TikTok returns an error, quota message, or empty data, do not retry with more social tools. Continue with Google signals and set social values conservatively.

## Final Output Requirement
- Your final response MUST be the output of the `build_trend_results_report` tool.
- Do not add conversational text before or after the JSON.

## Language
- ALWAYS write the entire user-facing output in Vietnamese.
- This includes: `main_keyword`, `why_the_trend_happens`, `recommended_action`, `top_hashtags` labels if described in prose, and `markdown_summary`.
- Even if the user enters English keywords, keep the explanation and recommendations in Vietnamese.
- Keep proper nouns, brand names, hashtags, and exact search keywords unchanged when needed.
- Always cite actual numbers from tool responses and do not fabricate metrics.
"""


@tool
def score_trend_item(
    google_latest_value: Annotated[float, "Most recent Google interest value (0-100) for the keyword."],
    google_peak_value: Annotated[float, "Peak Google interest value (0-100) within the selected window."],
    social_avg_velocity: Annotated[float, "Average TikTok views per hour for the sampled videos."],
    social_avg_trend_score: Annotated[float, "Average TikTok trend score for the sampled videos."],
) -> dict[str, Any]:
    """
    Produce a deterministic 0-100 trend score by blending Google demand and TikTok velocity.
    This score is designed for ranking multiple candidate keywords in the final shortlist.
    """
    google_component = min(
        35.0,
        max(0.0, google_latest_value) * 0.20 + max(0.0, google_peak_value) * 0.15,
    )
    velocity_component = min(
        40.0,
        math.log10(max(social_avg_velocity, 1.0) + 1.0) * 10.0,
    )
    social_component = min(
        25.0,
        math.log10(max(social_avg_trend_score, 1.0) + 1.0) * 6.0,
    )
    score = round(min(100.0, google_component + velocity_component + social_component), 2)

    if score >= 80:
        signal = "breakout"
    elif score >= 60:
        signal = "strong"
    elif score >= 40:
        signal = "watchlist"
    else:
        signal = "early"

    return {
        "trend_score": score,
        "signal_label": signal,
        "components": {
            "google_component": round(google_component, 2),
            "velocity_component": round(velocity_component, 2),
            "social_component": round(social_component, 2),
        },
    }


@tool
def build_trend_report(
    query: str,
    final_keywords: list[str],
    classification: str,
    confidence: float,
    google_data: GoogleBlock | None = None,
    tiktok_data: TikTokBlock | None = None,
    threads_data: ThreadsBlock | None = None,
    recommended_action: str = "",
    markdown_report: str = "",
) -> str:
    """
    Legacy single-report builder retained for backwards compatibility.
    """
    report = TrendReport(
        query=query,
        final_keywords=final_keywords,
        google=google_data,
        tiktok=tiktok_data,
        threads=threads_data,
        classification=classification,
        confidence=confidence,
        recommended_action=recommended_action,
        markdown_report=markdown_report,
    )
    return report.model_dump_json()


@tool
def build_trend_results_report(
    query: str,
    results: list[dict[str, Any]],
    markdown_summary: str = "",
) -> str:
    """
    Final step for the updated shortlist flow.
    Assemble multiple ranked trend result items into one JSON response.
    """
    normalized_results = [
        item if isinstance(item, TrendResultItem) else TrendResultItem.model_validate(item)
        for item in results
    ]
    report = TrendDiscoveryReport(
        query=query,
        results=normalized_results,
        markdown_summary=markdown_summary,
    )
    return report.model_dump_json()


REASONING_TOOLS = [
    score_trend_item,
    build_trend_results_report,
]


class TrendAgent:
    """Wrapper class for the multi-result trend intelligence agent."""

    def __init__(self, api_key: str = None) -> None:
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
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        # Old Gemini default kept here for reference:
        # self.model_name = os.getenv("TREND_AGENT_MODEL", "gemini/gemini-2.5-flash")
        self.model_name = os.getenv("TREND_AGENT_MODEL", "openai/gpt-4o-mini")
        self.agent = None

    async def initialize(self):
        """Initialize the agent asynchronously and load tools."""
        tools = await self.mcp_client.get_tools()
        if self.api_key is None:
            raise RuntimeError("No OPENAI_API_KEY provided.")

        low_cost_tool_names = {"get_trends", "search_term", "tiktok_search_keyword"}
        filtered_tools = [tool for tool in tools if tool.name in low_cost_tool_names]
        all_tools = filtered_tools + REASONING_TOOLS

        self.agent = create_agent(
            ChatLiteLLM(
                # Old Gemini model:
                # model="gemini/gemini-2.5-flash",
                model=self.model_name,
                max_tokens=4000,
                api_key=self.api_key,
            ),
            all_tools,
            name="TrendIntelligenceAgent",
            system_prompt=SYSTEM_PROMPT,
        )
        print("Agent initialized with tools: \n", all_tools)
        print("Model:", self.model_name)
        print("\nNumber of tools: ", len(all_tools))
        return self

    async def answer_query(self, prompt: str) -> dict[str, Any]:
        """Send a prompt and return both summary text and structured shortlist data."""
        if self.agent is None:
            raise RuntimeError("Agent not initialized.")

        try:
            response = await self.agent.ainvoke(
                {
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
        except Exception as exc:
            message = (
                "Trend agent model invocation failed before any structured output was produced. "
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
                        "model": self.model_name,
                    },
                },
                "status": "error",
            }

        print(response["messages"][-1])
        raw_content = response["messages"][-1].content

        try:
            report_data = json.loads(raw_content)
            display_text = (
                report_data.get("markdown_summary")
                or report_data.get("markdown_report")
                or self._fallback_summary(report_data)
            )
            print(display_text)
            return {
                "display_text": display_text,
                "structured_data": report_data,
                "status": "success",
            }
        except json.JSONDecodeError:
            return {
                "display_text": raw_content,
                "structured_data": None,
                "status": "partial_success",
            }

    def _fallback_summary(self, report_data: dict[str, Any]) -> str:
        results = report_data.get("results") or []
        if not results:
            return "No trend results generated."

        lines = ["## Trend Results"]
        for index, item in enumerate(results, start=1):
            lines.append(
                f"{index}. **{item.get('main_keyword', 'Unknown keyword')}**"
                f" - trend score {item.get('trend_score', 0)},"
                f" avg views/hour {item.get('avg_views_per_hour', 0)}"
            )
            action = item.get("recommended_action")
            if action:
                lines.append(f"   Action: {action}")
        return "\n".join(lines)
