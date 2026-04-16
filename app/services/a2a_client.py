import httpx
from a2a.client import A2AClient
import asyncio
from beeai_framework.adapters.a2a.agents import A2AAgent, A2AAgentOutput
from beeai_framework.memory.base_memory import BaseMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.memory.summarize_memory import SummarizeMemory
from beeai_framework.backend import SystemMessage, UserMessage, AssistantMessage


class InsightForgeA2AClient:
    def __init__(
        self,
        base_url: str = "http://localhost:5000/",
        post_url: str = "http://localhost:9995/",
    ) -> None:
        self.base_url = base_url
        self.post_url = post_url
        self.post_client = A2AAgent(url="http://0.0.0.0:9995", memory=UnconstrainedMemory())


    async def ask(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as httpx_client:
            client = A2AClient(url=self.base_url, httpx_client=httpx_client)
            response = await client.send_message(prompt)
            return str(response)

    async def posting(self, prompt: str, config_id: str, decisions: str = ""):
        
        await self.post_client.check_agent_exists()
        print("Connected to Posting Agent Server!\n")
        print(f"Sending prompt: '{prompt}'...\n")
        message = UserMessage(
            content=prompt, meta={"decision": decisions, "config": config_id}
        )
        response: A2AAgentOutput = await self.post_client.run(message)
        return response
