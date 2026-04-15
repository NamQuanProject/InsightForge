import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def run_interactive():
    from agents.posting_agent.agent import PostingAgent

    agent = PostingAgent(api_key=os.getenv("GOOGLE_API_KEY"))
    await agent.initialize()

    user_input = "Can you provide me with some kind of user informations '"
    print("\nUser Input:")
    print(user_input)

    config, response = await agent.chat(user_input)
    print(config, response)

    

    


if __name__ == "__main__":
    asyncio.run(run_interactive())
