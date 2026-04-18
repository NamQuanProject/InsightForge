"""
RoutingAgent - BeeAI RequirementAgent with sub-agent tools.
Exposed as an A2A server; the Backend sends free-text queries to it.
"""

import os

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.think import ThinkTool

from agents.orchestration_agent.tools import call_content_agent, call_trend_agent


ROUTER_INSTRUCTIONS = """
You are a smart routing orchestrator for a content marketing pipeline.

You have two specialist sub-agents available as tools:

1. call_trend_agent - finds and analyzes trending topics; returns a rich trend report.
2. call_content_agent - turns a trend report into a personalized multi-image post bundle.

Decision rules:
- "What's trending / find trends / analyze X": call_trend_agent only.
- "Generate content / make a post / post idea": call_trend_agent then call_content_agent.
- "Full pipeline / end-to-end": call_trend_agent then call_content_agent.
- Ambiguous but content-flavored: call_trend_agent then call_content_agent.

Rules:
- ALWAYS use ThinkTool first to reason about what the user needs before picking tools.
- Pass the FULL output of call_trend_agent as input to call_content_agent; never truncate it.
- If the user supplies extra instructions (platform, tone, style), append them to the input
  of call_content_agent after the trend report.
- If the backend prompt includes a user_id, preserve that exact user_id when calling
  call_content_agent so the content agent can fetch user profile and content history.
- Reply in the same language as the user's query.
- Do NOT fabricate trend data or content. Everything must flow from the tool outputs.
- Your final answer MUST be valid JSON only. No prose outside JSON.
- When the user asks for both trend insights and content ideas, return:
  {
    "trend_analysis": <JSON object returned by call_trend_agent>,
    "generated_content": <JSON object returned by call_content_agent>
  }
- When the user only asks for trends, return:
  {
    "trend_analysis": <JSON object returned by call_trend_agent>,
    "generated_content": null
  }
- Preserve the original JSON from call_trend_agent and call_content_agent as much as possible.
- If one tool returns invalid JSON, wrap its raw text in:
  { "raw": "<tool output>" }
"""


def build_routing_agent() -> RequirementAgent:
    model_name = os.getenv("ROUTING_AGENT_MODEL", "gemini:gemini-2.5-flash")
    llm = ChatModel.from_name(model_name)
    think_tool = ThinkTool()

    return RequirementAgent(
        llm=llm,
        tools=[
            think_tool,
            call_trend_agent,
            call_content_agent,
        ],
        requirements=[ConditionalRequirement(think_tool, force_at_step=1, consecutive_allowed=False)],
        role="Content Pipeline Router",
        instructions=ROUTER_INSTRUCTIONS,
        memory=UnconstrainedMemory(),
    )
