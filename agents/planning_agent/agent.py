import os
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_openai import ChatOpenAI
import asyncio


class PlanningAgent:
    """Wrapper class for the LangChain planning provider agent."""
    def __init__(self, api_key: str = None) -> None:
        self.mcp_client = MultiServerMCPClient({
            "controlling_planning": StdioConnection(
                transport="stdio",
                command="python",
                args=["-m", "mcp_servers.planning_servers.mcp_server"], 
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
            name="PlanningAgent",
            system_prompt = (
                "You are a Planning Agent. Your goal is to use the available tools "
                "to plan and ready for comfirmations from the users to execute tasks effectively."
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

        print(response["messages"][-1].content)
        return response["messages"][-1].content
    