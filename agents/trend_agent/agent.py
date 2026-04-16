import os
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
# from agents.trend_agent.memory import AgentMemory
from agents.trend_agent.structured_output import TrendReport, GoogleSummary, TrendResult, TikTokSummary

from typing import Annotated, Any
import json

SYSTEM_PROMPT = """
You are an elite Viral Trend Intelligence Analyst. Your job is to identify high-growth trends, perform cross-platform validation, and output a structured intelligence report for content creators.

You have access to TWO complementary data sources:
1. **Google Trends** – reflects search intent, regional interest, and rising queries.
2. **Social Media (TikTok)** – reflects viral velocity, engagement rates, and shareability.

## Your Core Workflow
When asked to analyze a trend or query, you MUST cross-validate across both platforms for every potential keyword discovered:

**Step 1: Discover (Google Trends & TikTok Hashtags)**
- Use `get_trends` to find what is trending NOW.
- Use `tiktok_search_hashtag` with "trending" to find high-velocity keywords.
- Use `search_term` with TIMESERIES to measure search momentum over time.

**Step 2: Validate (TikTok Engagement)**
- Use `tiktok_search_keywords` for specific keywords found in Step 1.
- Identify the `top_velocity`, `avg_engagement_rate`, and winning content angles.

**Step 3: Cross-Reference & Score**
- For EACH relevant keyword found, you MUST call `classify_trend_signals`.
- This tool provides the `trend_score`, `classification` (MEGA_TREND, EMERGING, etc.), and the `reasoning` (why it's trending).

**Step 4: Final Assembly**
- Synthesize all findings into a list of "results" objects.
- Create a global `markdown_summary` that captures the overall market sentiment for the user's query.

## Final Output Requirement
- Your final response MUST be the output of the `build_trend_report` tool.
- Do not add any conversational text before or after the JSON output.
- The `results_data` argument must be a list of dictionaries, where each dict represents one keyword analysis (including momentum, trend_score, and recommended actions).
- This JSON powers a UI dashboard; ensure all numerical metrics (interest_over_day, velocity) are extracted accurately from tool responses.

## Language & Accuracy
- Respond in the same language as the user's query.
- Khi người dùng hỏi bằng tiếng Việt, trả lời bằng tiếng Việt.
- Never fabricate metrics. Use actual numbers from tool responses.
"""

@tool
def classify_trend_signals(
    google_momentum: Annotated[str, "One of: rising, stable, declining, unknown"],
    social_velocity: Annotated[float, "TikTok average velocity (views/hour) of top videos, 0 if unavailable"],
    social_engagement_rate: Annotated[float, "Average engagement rate from TikTok, 0 if unavailable"],
) -> dict[str, Any]:
    """
    Classify a trend and calculate a numerical trend_score for the sample format.
    """
    momentum = google_momentum.lower()
    is_google_rising = momentum == "rising"
    
    # Calculate Trend Score (0-100) based on sample heuristics
    # Logic: Base (20) + Velocity Component + Momentum Bonus
    velocity_points = min(50, social_velocity / 5000) 
    momentum_bonus = 15 if is_google_rising else 0
    engagement_bonus = social_engagement_rate * 100
    trend_score = round(20 + velocity_points + momentum_bonus + engagement_bonus, 1)

    # Standard Classification
    if is_google_rising and social_velocity > 5000:
        label, reason = "MEGA_TREND", "Both search intent and social engagement are high — broad, sustained trend."
    elif social_velocity > 10000:
        label, reason = "EMERGING", "Social velocity is very high but search hasn't caught up — early viral signal."
    elif is_google_rising:
        label, reason = "INTEREST_ONLY", "People are searching but not engaging socially — informational, not yet viral."
    else:
        label, reason = "WEAK", "Neither Google nor social signals are strong enough."

    return {
        "classification": label,
        "trend_score": trend_score,
        "confidence": round(min(0.95, 0.4 + (trend_score/100)), 2),
        "reasoning": reason,
    }

@tool
def build_trend_report(
    query: str,
    results_data: list[dict], # List of processed keyword data
    markdown_summary: str,
) -> str:
    """
    Final step: Assembles the TrendReport into the exact JSON format 
    required by the UI (trend_analysis_sample.json).
    """
    processed_results = []
    
    for item in results_data:
        # Extract interest_over_day from timeseries if available, else use placeholder
        interest_points = item.get("interest_over_day", [10, 20, 30, 40, 50, 60, 70, 80])
        
        res = TrendResult(
            main_keyword=item["keyword"],
            why_the_trend_happens=item["reasoning"],
            trend_score=item["trend_score"],
            interest_over_day=interest_points,
            avg_views_per_hour=item.get("avg_velocity", 0),
            recommended_action=item.get("action", ""),
            top_hashtags=item.get("hashtags", []),
            google=GoogleSummary(
                keyword=item["keyword"],
                momentum=item.get("momentum", "stable"),
                peak_region=item.get("peak_region", "N/A")
            ),
            tiktok=TikTokSummary(
                top_velocity=item.get("top_velocity", 0),
                avg_engagement_rate=item.get("engagement_rate", 0)
            ) if item.get("has_tiktok") else None,
            threads=None
        )
        processed_results.append(res)

    report = TrendReport(
        query=query,
        results=processed_results,
        markdown_summary=markdown_summary
    )
    
    return report.model_dump_json(indent=2)

REASONING_TOOLS = [
    classify_trend_signals,
    build_trend_report,
]

class TrendAgent:
    """Wrapper class for the LangChain Trend Analysis agent."""
    def __init__(self, api_key: str = None) -> None:
        # Connect to the local MCP server
        self.mcp_client = MultiServerMCPClient({
             # ── Server 1: Google Trends ──────────────────────────────────
            "google_trends": StdioConnection(
                transport="stdio",
                command="python",
                args=["-m", "mcp_servers.trends_servers.server"],
            ),
            # ── Server 2: Social Media (TikTok + Threads) ────────────────
            "social_media_trends": StdioConnection(
                transport="stdio",
                command="python",
                args=["-m", "mcp_servers.social_media_servers.server"],
            ),
        })
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.agent = None

    async def initialize(self):
        """Initialize the agent asynchronously and load tools."""
        tools = await self.mcp_client.get_tools()
        if self.api_key is None:
            raise RuntimeError("No API Key provided. Set GOOGLE_API_KEY or GEMINI_API_KEY, or pass api_key=.")
        
        all_tools = tools + REASONING_TOOLS

        self.agent = create_agent(
            ChatLiteLLM(
            # model="gemini/gemini-3.1-flash-lite-preview",
            model = "gemini/gemini-2.5-flash",
            max_tokens=4000,
            api_key=self.api_key
            ),
            all_tools,
            name="TrendIntelligenceAgent",
            system_prompt = SYSTEM_PROMPT
        )
        print("Agent initialized with tools: \n", all_tools)
        print("\nNumber of tools: ", len(all_tools))
        return self

    async def answer_query(self, prompt: str) -> str:
        """Send a prompt and return a dict containing both UI and Backend data."""
        if self.agent is None:
            raise RuntimeError("Agent not initialized.")

        # response = await self.agent.ainvoke({
        #     "messages": [{"role": "user", "content": prompt}]
        # })
        response = await self.agent.ainvoke({"messages": [("user", prompt)]})

        print(response["messages"][-1])
        raw_content = response["messages"][-1].content
        return raw_content # ```json tag`
    