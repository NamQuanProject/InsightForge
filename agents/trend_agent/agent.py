import os
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_openai import ChatOpenAI
import asyncio


class TrendAgent:
    """Wrapper class for the LangChain healthcare provider agent."""
    def __init__(self) -> None:
        # Connect to the local MCP server
        self.mcp_client = MultiServerMCPClient({
            "find_healthcare_providers": StdioConnection(
                transport="stdio",
                command="uv",
                args=["run", "mcp_servers/trends_servers/mcpserver.py"], 
            )
        })
        self.agent = None

    async def initialize(self):
        """Initialize the agent asynchronously and load tools."""
        tools = await self.mcp_client.get_tools()
        self.agent = create_agent(
            ChatLiteLLM(
            # model="gemini/gemini-3.1-flash-lite-preview",
            model = "gemini/gemini-2.5-flash",
            max_tokens=1000,
            ),
            tools,
            name="HealthcareProviderAgent",
            system_prompt=(
                "Your task is to find and list providers using the find_healthcare_providers "
                "MCP Tool based on the users query. Only use providers based on the response "
                "from the tool. Output the information in a table."
            ),
        )
        print("Agent initialized with tools:", tools)
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
    