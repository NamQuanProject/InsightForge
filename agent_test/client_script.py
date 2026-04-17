import asyncio
from beeai_framework.adapters.a2a.agents import A2AAgent, A2AAgentOutput
from beeai_framework.memory.base_memory import BaseMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.memory.summarize_memory import SummarizeMemory
from beeai_framework.backend import SystemMessage, UserMessage, AssistantMessage

async def call_healthcare_agent():
    client = A2AAgent(url="http://0.0.0.0:9995", memory=UnconstrainedMemory())

    await client.check_agent_exists()
    print("✅ Connected to Product Agent Server!\n")

    prompt_1 = "Upload for me the photo about bird with current username to instagram with description 'Test post from API'?"

    prompt_2 = "Okay can you post for me that picture"

    

    print(f"Sending prompt: '{prompt_2}'...\n")


    normal_message = UserMessage(content=prompt_2, meta={"decision": "asking", "config" : "019d925b-0d81-7d72-b673-72ae6652ed46"})

    approve_message = UserMessage(content=prompt_2, meta={"decision": "approve", "config" : "019d925b-0d81-7d72-b673-72ae6652ed46"})
    

    response = await client.run(approve_message)

    # 4. Print the result
    print("=== Final Response ===")
    print("=====================")    
    print("=====================")    
    print("=====================")    
    
    print(response)
    print("=====================")    
    print("=====================")    
    print("=====================")    
    print("=====================")    

    
if __name__ == "__main__":
    asyncio.run(call_healthcare_agent())