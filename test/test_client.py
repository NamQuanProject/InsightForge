import asyncio
from a2a.client import A2AClient
import httpx

async def test_agent():
    # Setup HTTP client and connect to your local agent server
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        print("Discovering Agent Card...")
        client = A2AClient(url="http://localhost:9997/", httpx_client=httpx_client)
        
        prompt = "I am based in Austin, TX. Are there any Psychiatrists near me?"
        print(f"Sending prompt: '{prompt}'\n")
        
        # sendMessage automatically creates the JSON-RPC payload
        response = await client.send_message(prompt)
        
        print("Agent Response:")
        print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())