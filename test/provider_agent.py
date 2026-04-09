import os
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_openai import ChatOpenAI
from agents.trend_agent.helpers import authenticate
import asyncio


class ProviderAgent:
    """Wrapper class for the LangChain healthcare provider agent."""
    def __init__(self) -> None:
        credentials, project_id = authenticate()
        location = "us-central1"
        self.base_url = f"{os.getenv('GOOGLE_VERTEX_BASE_URL')}/v1/projects/{project_id}/locations/{location}/endpoints/openapi"
        self.credentials = credentials
        
        # Connect to the local MCP server
        self.mcp_client = MultiServerMCPClient({
            "find_healthcare_providers": StdioConnection(
                transport="stdio",
                command="uv",
                args=["run", "mcpserver.py"], 
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
    

# def main():
#     """Test the ProviderAgent independently."""
#     import asyncio

#     agent = ProviderAgent()
#     asyncio.run(agent.initialize())
    
#     test_prompt = "Are there any Psychiatrists near me in Boston, MA?"
#     print(f"\nSending prompt: '{test_prompt}'")
    
#     # Use 'await' here as well
#     response = asyncio.run(agent.answer_query(test_prompt))

#     print("Agent Response:\n", response)

# if __name__ == "__main__":
#     main()