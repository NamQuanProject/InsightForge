"""
RoutingAgent — BeeAI RequirementAgent with sub-agent tools.
Exposed as an A2A server; the Backend sends free-text queries to it.
"""

import os
import sys

from beeai_framework.adapters.a2a import A2AServer, A2AServerConfig
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.serve.utils import LRUMemoryManager
from beeai_framework.tools.think import ThinkTool

from agents.orchestration_agent.tools import call_content_agent, call_trend_agent

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

ROUTER_INSTRUCTIONS = """
You are a smart routing orchestrator for a content marketing pipeline.

You have two specialist sub-agents available as tools:

1. call_trend_agent   — finds and analyzes trending topics; returns a rich trend report
2. call_content_agent — turns a trend report into a video script, post content, and image

## Decision rules

| User intent                                   | Tools to call (in order)              |
|-----------------------------------------------|---------------------------------------|
| "What's trending / find trends / analyze X"   | call_trend_agent only                 |
| "Generate content / make a video / post idea" | call_trend_agent → call_content_agent |
| "Full pipeline / end-to-end"                  | call_trend_agent → call_content_agent |
| Ambiguous but content-flavored                | call_trend_agent → call_content_agent |

## Rules
- ALWAYS use ThinkTool first to reason about what the user needs before picking tools.
- Pass the FULL output of call_trend_agent as input to call_content_agent — never truncate it.
- If the user supplies extra instructions (platform, tone, style), append them to the input
  of call_content_agent after the trend report.
- Reply in the same language as the user's query.
- Do NOT fabricate trend data or content. Everything must flow from the tool outputs.
- Return the final result clearly structured in JSON including both trend analysis and content generation, preserving the JSON from call_trend_agent when insights wer generated and
call_content_agent when content was generated.
"""

# ---------------------------------------------------------------------------
# Factory — builds the agent (called once per session by A2AServer)
# ---------------------------------------------------------------------------

def build_routing_agent() -> RequirementAgent:
    llm = ChatModel.from_name(
        "gemini:gemini-2.5-flash"
    )

    return RequirementAgent(
        llm=llm,
        tools=[
            ThinkTool(),           # Forces explicit reasoning before tool dispatch
            call_trend_agent,
            call_content_agent,
        ],
        # Force ThinkTool on the first step so the LLM reasons before acting
        requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
        role="Content Pipeline Router",
        instructions=ROUTER_INSTRUCTIONS,
        memory=UnconstrainedMemory(),
    )




