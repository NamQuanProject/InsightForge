from agents.trend_agent.agent import TrendAgent
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "")

async def run_test():
    agent = TrendAgent(
        api_key=api_key
    )
    await agent.initialize()

    query = (
                "1. Find the top trending search in Vietnam for Music.\n"
                "2. For that specific topic, fetch the related topics and interests over time data "
                "to show how its interest has changed recently."
            )
            
    print(f"--- Starting Test ---\nQuery: {query}\n")
    print("\n--- FINAL AGENT OUTPUT ---")
    result = await agent.answer_query(query)
    # print(result)

if __name__ == "__main__":
    asyncio.run(run_test())

