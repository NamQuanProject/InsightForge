import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from dotenv import load_dotenv
import os

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Test MCP Clients
async def main():
    clients = MultiServerMCPClient(
        {
            "Google_Trend": 
            {
                "transport": "stdio",
                "command": "python",
                "args": ["-m", "mcp_server.trend_server.google_trend"]
            }
        }
    )
    tools = await clients.get_tools()
    print(f"Successfully loading {len(tools)} from MCP servers")
    llm =  ChatLiteLLM(
            model = "gemini/gemini-2.5-flash",
            max_tokens=1000,
            api_key=google_api_key
            )
    system_instruction = ("You are a Viral Trend Analyst. Your goal is to use the Google Trend tools "
        "to find high-growth topics and output your analysis in a clear Markdown table.")
    
    agent = create_agent(
            llm,
            tools,
            name="TrendingAnalysisAgent",
            system_prompt=system_instruction,
        )
    # 5. Run a Test Query
    query = "What is trending in Vietnam right now for the category 'Sports'?"
    print(f"Executing Query: {query}")
    
    result = await agent.ainvoke({"messages": [("user", query)]})
    
    # 6. Display the Final Response
    print("\n--- AGENT RESPONSE ---")
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main = main())