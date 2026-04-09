import asyncio
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.memory import UnconstrainedMemory

async def call_healthcare_agent():
    client = A2AAgent(url="http://localhost:5000", memory=UnconstrainedMemory())

    await client.check_agent_exists()
    print("✅ Connected to Healthcare Agent Server!\n")

    prompt = "I'm based in Austin, TX. How do I get mental health therapy near me and what does my insurance cover?"
    print(f"Sending prompt: '{prompt}'...\n")
    
    response = await client.run(prompt)
    
    # 4. Print the result
    print("=== Final Response ===")
    print(response.last_message.text)

if __name__ == "__main__":
    asyncio.run(call_healthcare_agent())