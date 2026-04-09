import os
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_openai import ChatOpenAI
import asyncio


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
        self.mcp_client = MultiServerMCPClient({
            "fetch_trends": StdioConnection(
                transport="stdio",
                command="python",
                args=["-m", "mcp_servers.trends_servers.server"], 
            )
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
            max_tokens=1000,
            api_key=self.api_key
            ),
            tools,
            # name="HealthcareProviderAgent",
            # system_prompt=(
            #     "Your task is to find and list providers using the find_healthcare_providers "
            #     "MCP Tool based on the users query. Only use providers based on the response "
            #     "from the tool. Output the information in a table."
            # ),
            name="TrendAnalysisAgent",
            system_prompt = (
                "You are a Viral Trend Analyst. Your goal is to use the Google Trend tools "
                "to find high-growth topics and output your analysis in a clear Markdown table."
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
    