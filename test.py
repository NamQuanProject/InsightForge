# import requests
# import json
# import uuid

# def call_agent():
#     url = "http://localhost:9997/"
    
#     # We generate a random UUID for the messageId to ensure it's always unique
#     msg_id = str(uuid.uuid4())
    
#     payload = {
#         "jsonrpc": "2.0",
#         "method": "message/send",
#         "params": {
#             "message": {
#                 "messageId": msg_id,
#                 "role": "user",
#                 "parts": [
#                     {"text": "I am based in Austin, TX. Are there any Psychiatrists near me?"}
#                 ]
#             }
#         },
#         "id": "1"
#     }

#     print("Sending request to your running agent...\n")
    
#     try:
#         response = requests.post(url, json=payload)
#         response.raise_for_status() 
        
#         print("=== Agent Response ===")
#         print(json.dumps(response.json(), indent=2))
        
#     except requests.exceptions.RequestException as e:
#         print(f"Connection error: {e}")

# if __name__ == "__main__":
#     call_agent()

import os
import warnings
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.vertexai import VertexAIChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import EventMeta, GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool
from dotenv import load_dotenv
import asyncio


policy_agent = A2AAgent(
    url=f"http://localhost:9997", 
    memory=UnconstrainedMemory()
)
# Run `check_agent_exists()` to fetch and populate AgentCard
asyncio.run(policy_agent.check_agent_exists())
print("\tℹ️", f"{policy_agent.name} initialized")