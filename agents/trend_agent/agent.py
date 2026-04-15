from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
# from agents.trend_agent.memory import AgentMemory
from agents.trend_agent.structured_output import TrendReport, GoogleBlock, TikTokBlock, ThreadsBlock

from typing import Annotated, Any
import json

SYSTEM_PROMPT = """
You are an elite Viral Trend Intelligence Analyst. Your job is to find high-growth trends, analyze to get insights and finally output recommended actions and report.
You are equipped with tools and you must use them to complete task.
 
You have access to TWO complementary data sources:
1. **Google Trends** – reflects what people are actively *searching* (search intent, regional interest, rising queries).
2. **Social Media (TikTok + Threads)** – reflects what people are actively *talking about and engaging with* (viral velocity, engagement rate, shareability).
 
## Your Core Workflow
When asked to analyze a trend, ALWAYS cross-validate across both platforms:

**Step 1 Discover on Google Trends and Tiktok Hashtag trending**
- Use `get_trends` to find what's trending NOW (use appropriate category if provided else search all categories).
- Use "tiktok_search_hashtag" with hashtag "trending" to find trends keywords.
- Use `search_term` with TIMESERIES to measure search momentum.
- Reason if it is approriate for content creator.
 
**Step 2 Validate on Social Media**
- Use `cross_platform_trend` or individual TikTok/Threads tools to check if the topic has social traction.
- Compare `trend_score`, `velocity`, and `engagement_rate` across videos/posts.
 
**Step 3 Cross-Reference & Score**
- Call `classify_trend_signals` with the aggregated data for Classification: [MEGA TREND / EMERGING / INTEREST ONLY / WEAK]
 
STEP 4 – WRITE MARKDOWN REPORT
  ## Trend Intelligence Report: {keyword}

  ### 🔍 Google Trends Signal
  - Momentum: rising / stable / declining
  - Peak region: ...
  - Rising related queries: [list]
 
  ### 📱 Social Media Signal
  - TikTok top velocity: X views/hour
  - Threads engagement: ...
  - Winning content angle: ...
 
  ### 🎯 Classification: {LABEL} (confidence: X%)
  {reasoning}
 
  ### 💡 Recommended Action
  {Concise and Short advices}

  ## FINAL OUTPUT REQUIREMENT
- Your final response MUST be the output of the `build_trend_report` tool.
- Do not add any conversational text before or after the JSON output (e.g., do not say "Here is your report").
- The `markdown_report` argument in the tool must contain the full, formatted report described in Step 4.
- This JSON will be used to power both a UI dashboard (data) and a reading view (markdown).
 
## Language
- Respond in the same language as the user's query.
- Khi người dùng hỏi bằng tiếng Việt, trả lời bằng tiếng Việt.
- Always cite actual numbers from tool responses — never fabricate metrics.
"""

@tool
def classify_trend_signals(
    google_momentum: Annotated[str, "One of: rising, stable, declining, unknown"],
    social_velocity: Annotated[float, "TikTok average velocity (views/hour) of top videos, 0 if unavailable"],
    social_engagement_rate: Annotated[float, "Average engagement rate from TikTok/Threads, 0 if unavailable"],
) -> dict[str, Any]:
    """
    Classify a trend into one of four buckets based on cross-platform signals.
    Call this AFTER gathering both Google and Social data to produce the
    final classification before writing the report.
 
    Classification matrix:
      MEGA_TREND    : Google rising  AND social_velocity > 5 000
      EMERGING      : social_velocity > 10 000 (search hasn't caught up)
                      OR (Google rising AND social moderate)
      INTEREST_ONLY : Google rising  AND social_velocity < 1 000
      WEAK          : Everything else
 
    Returns classification, confidence (0–1), and reasoning string.
    """
    momentum         = google_momentum.lower()
    is_google_rising = momentum == "rising"
    is_social_hot    = social_velocity > 5_000
    is_social_viral  = social_velocity > 10_000
 
    if is_google_rising and is_social_hot:
        label      = "MEGA_TREND"
        confidence = min(0.95, 0.7 + social_engagement_rate)
        reason     = "Both search intent and social engagement are high — broad, sustained trend."
 
    elif is_social_viral and not is_google_rising:
        label      = "EMERGING"
        confidence = min(0.85, 0.5 + social_velocity / 50_000)
        reason     = "Social velocity is very high but search hasn't caught up — early viral signal."
 
    elif is_google_rising and not is_social_hot:
        label      = "INTEREST_ONLY"
        confidence = 0.6
        reason     = "People are searching but not engaging socially — informational, not yet viral."
 
    elif is_social_hot and not is_google_rising:
        label      = "EMERGING"
        confidence = 0.65
        reason     = "Moderate social traction without search momentum — watch for acceleration."
 
    else:
        label      = "WEAK"
        confidence = 0.4
        reason     = "Neither Google nor social signals are strong enough."
 
    return {
        "classification": label,
        "confidence": round(confidence, 2),
        "reasoning": reason,
    }
 
@tool
def build_trend_report(
    query: str,
    final_keywords: list[str],
    classification: str,
    confidence: float,
    google_data: GoogleBlock | None = None,   # The agent now sees the Google schema
    tiktok_data: TikTokBlock | None = None,   # The agent now sees the TikTok schema
    threads_data: ThreadsBlock | None = None, # The agent now sees the Threads schema
    recommended_action: str = "",
    markdown_report: str = "",
) -> str:
    """
    Final step: Assemble the TrendReport. 
    The agent must map gathered search data to 'google_data' 
    and social metrics to 'tiktok_data' or 'threads_data'.
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
        markdown_report=markdown_report
    )
    return report.model_dump_json()

REASONING_TOOLS = [
    classify_trend_signals,
    build_trend_report,
]

class TrendAgent:
    """Wrapper class for the LangChain healthcare provider agent."""
    def __init__(self, api_key: str = None) -> None:
        # Connect to the local MCP server
        # self.memory = AgentMemory(agent_name="TrendAgent")
        self.mcp_client = MultiServerMCPClient({
            # "social_media_trends": StdioConnection(
            #     transport="stdio",
            #     command="python",
            #     args=["-m", "mcp_servers.social_media_servers.server"]
            # )
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
        self.api_key = api_key if api_key else None
        self.agent = None

    async def initialize(self):
        """Initialize the agent asynchronously and load tools."""
        tools = await self.mcp_client.get_tools()
        if self.api_key is None:
            raise RuntimeError("No API Key provided.")
        
        all_tools = tools + REASONING_TOOLS

        self.agent = create_agent(
            ChatLiteLLM(
            # model="gemini/gemini-3.1-flash-lite-preview",
            model = "gemini/gemini-2.5-flash",
            max_tokens=4000,
            api_key=self.api_key
            ),
            all_tools,
            # name="HealthcareProviderAgent",
            # system_prompt=(
            #     "Your task is to find and list providers using the find_healthcare_providers "
            #     "MCP Tool based on the users query. Only use providers based on the response "
            #     "from the tool. Output the information in a table."
            # ),
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

        response = await self.agent.ainvoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        print(response["messages"][-1])
        raw_content = response["messages"][-1].content
        return raw_content
        # try:
        #     # Attempt to parse the content as the TrendReport JSON
        #     report_data = json.loads(raw_content)
        #     print(report_data.get("markdown_report"))
        #     return {
        #         "display_text": report_data.get("markdown_report", "No report generated."),
        #         "structured_data": report_data,  # Full dict for backend/database
        #         "status": "success"
        #     }
        # except json.JSONDecodeError:
        #     # Fallback if the agent didn't use the tool correctly or spoke conversationally
        #     return {
        #         "display_text": raw_content,
        #         "structured_data": None,
        #         "status": "partial_success"
        #     }
    