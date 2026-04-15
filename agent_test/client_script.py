import asyncio
from beeai_framework.adapters.a2a.agents import A2AAgent, A2AAgentOutput
from beeai_framework.memory.base_memory import BaseMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.memory.summarize_memory import SummarizeMemory


async def call_healthcare_agent():
    client = A2AAgent(url="http://0.0.0.0:9995", memory=UnconstrainedMemory())

    await client.check_agent_exists()
    print("✅ Connected to Product Agent Server!\n")

    prompt = "Can you upload for me a photo at sample_data/image.png with username blhoang23 to instagram with description 'Test post from API'?"
    print(f"Sending prompt: '{prompt}'...\n")
    

    response : A2AAgentOutput = await client.run(prompt)

    print(response.json)
    # 4. Print the result
    print("=== Final Response ===")
    print(response)
    print("=====================")
    


    print(response)
    
    
if __name__ == "__main__":
    asyncio.run(call_healthcare_agent())