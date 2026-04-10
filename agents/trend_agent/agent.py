from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection


SYSTEM_PROMPT = """
You are an elite Viral Trend Intelligence Analyst.
 
You have access to TWO complementary data sources:
1. **Google Trends** – reflects what people are actively *searching* (search intent, regional interest, rising queries).
2. **Social Media (TikTok + Threads)** – reflects what people are actively *talking about and engaging with* (viral velocity, engagement rate, shareability).
 
## Your Core Workflow
 
When asked to analyze a trend, ALWAYS cross-validate across both platforms:
 
**Step 1 Discover on Google Trends and Tiktok Hashtag trending**
- Use `get_trends` to find what's trending NOW (use appropriate category if provided else search all categories).
- Use "tiktok_search_hashtag" with hashtag "trending" to find trends keywords.
- Use `search_term` with TIMESERIES to measure search momentum.
 
**Step 2 Validate on Social Media**
- Use `cross_platform_trend` or individual TikTok/Threads tools to check if the topic has social traction.
- Compare `trend_score`, `velocity`, and `engagement_rate` across videos/posts.
 
**Step 3 Cross-Reference & Score**
Classify each trend into one of three buckets:
 
| Signal Pattern | Classification | Meaning |
|---|---|---|
| High Google Search + High Social Engagement | 🔥 **MEGA TREND** | Real, broad, sustained |
| High Social Engagement + Low/Rising Google Search | ⚡ **EMERGING TREND** | Viral early signal, watch closely |
| High Google Search + Low Social Engagement | 📊 **Interest Only** | Informational, not yet viral |
| Low both | ❌ **Weak Signal** | Skip or monitor |
 
## Output Format
 
Always structure your final report as:
 
```
## Trend Intelligence Report: [Topic]
 
### 🔍 Google Trends Signal
- Search momentum: [rising/stable/declining]
- Peak region: [location]
- Related rising queries: [list]
 
### 📱 Social Media Signal
- TikTok top velocity: [number] views/hour
- Threads engagement: [likes + replies summary]
- Top content angle: [what type of content is winning]
 
### 🎯 Classification: [MEGA TREND / EMERGING / INTEREST ONLY / WEAK]
 
### 💡 Recommended Action
[Concise and Short recommendation for Content Creator].
```
 
## Language
- Respond in the same language as the user's query.
- Khi người dùng hỏi bằng tiếng Việt, trả lời bằng tiếng Việt.
- Always cite actual numbers from tool responses — never fabricate metrics.
"""

class TrendAgent:
    """Wrapper class for the LangChain healthcare provider agent."""
    def __init__(self, api_key: str = None) -> None:
        # Connect to the local MCP server
        # self.mcp_client = MultiServerMCPClient({
        #     "find_healthcare_providers": StdioConnection(
        #         transport="stdio",
        #         command="uv",
        #         args=["run", "mcp_servers/trends_servers/mcpserver.py"], 
        #     )
        # })
        # self.mcp_client = MultiServerMCPClient({
        #     "fetch_trends": StdioConnection(
        #         transport="stdio",
        #         command="python",
        #         args=["-m", "mcp_servers.trends_servers.server"], 
        #     )
        # })
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
        self.agent = create_agent(
            ChatLiteLLM(
            # model="gemini/gemini-3.1-flash-lite-preview",
            model = "gemini/gemini-2.5-flash",
            max_tokens=4000,
            api_key=self.api_key
            ),
            tools,
            # name="HealthcareProviderAgent",
            # system_prompt=(
            #     "Your task is to find and list providers using the find_healthcare_providers "
            #     "MCP Tool based on the users query. Only use providers based on the response "
            #     "from the tool. Output the information in a table."
            # ),
            name="TrendIntelligenceAgent",
            system_prompt = (
                "You are a Viral Trend Analyst. Your goal is to use the Social Media tools "
                "to find high-growth topics and output your analysis."
                "Khi tìm trend, luôn so sánh dữ liệu giữa Tìm kiếm (Search) và Mạng xã hội (Social) để xác định độ 'thực' của xu hướng."
            )
        )
        print("Agent initialized with tools: \n", tools)
        return self

    async def answer_query(self, prompt: str) -> str:
        """Send a prompt to the initialized agent."""
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
        
        response = await self.agent.ainvoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        print(response)
        print(response["messages"][-1].content)
        return response["messages"][-1].content
    