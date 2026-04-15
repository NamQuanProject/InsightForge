"""
Sub-agent tools for the RoutingAgent.
Each tool wraps one downstream A2A agent via httpx message/send.
The BeeAI RequirementAgent LLM decides which tool(s) to call based on the user query.
"""

import os
import uuid

import httpx
from beeai_framework.tools import StringToolOutput, tool



AGENT_HOST = os.environ.get("AGENT_HOST", "localhost")
TREND_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('TREND_AGENT_PORT', 9997)}"
CONTENT_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('CONTENT_AGENT_PORT', 9998)}"

A2A_TIMEOUT = 180  # seconds — generous for trend scraping + image gen


# ---------------------------------------------------------------------------
# Shared A2A transport
# ---------------------------------------------------------------------------

def _build_message_send(text: str) -> dict:
    """Construct a spec-compliant A2A message/send JSON-RPC payload."""
    return {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "taskId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"type": "text", "text": text}],
            }
        },
    }


def _extract_reply(data: dict) -> str:
    """
    Pull assistant text from an A2A message/send response.
    Tries result.status.message.parts → result.artifacts[0].parts → result.parts.
    """
    result = data.get("result", {})

    # 1. Task.status.message.parts  (most common path)
    status_parts = (result.get("status") or {}).get("message", {}).get("parts", [])
    if status_parts:
        return "\n".join(p.get("text", "") for p in status_parts if p.get("type") == "text")

    # 2. Task.artifacts[0].parts
    artifacts = result.get("artifacts") or []
    if artifacts:
        parts = artifacts[0].get("parts", [])
        text = "\n".join(p.get("text", "") for p in parts if p.get("type") == "text")
        if text:
            return text

    # 3. Bare Message.parts
    if "parts" in result:
        return "\n".join(p.get("text", "") for p in result["parts"] if p.get("type") == "text")

    return f"[no text extracted] raw={str(result)[:300]}"


async def _call_a2a(base_url: str, message: str) -> str:
    """POST message/send to an A2A agent and return the text reply."""
    payload = _build_message_send(message)
    async with httpx.AsyncClient(timeout=A2A_TIMEOUT) as client:
        resp = await client.post(f"{base_url}/", json=payload)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise RuntimeError(f"A2A error from {base_url}: {data['error']}")

    return _extract_reply(data)


# ---------------------------------------------------------------------------
# Tool 1 — Trend Analysis
# ---------------------------------------------------------------------------

@tool
async def call_trend_agent(query: str) -> StringToolOutput:
    """
    Calls the TrendingAnalysisAgent to find and analyze the latest trending topics.

    Use this tool when the user wants to:
    - Discover what is currently trending (Google Trends, social media, news)
    - Understand trend data for a specific topic, keyword, or region
    - Get market/content insights driven by trend signals
    - Receive recommended actions based on trend analysis

    The agent returns a structured trend report with analysis and content recommendations.

    Args:
        query: The user's natural language request about trends
               (e.g. "What is trending in Vietnam right now?",
                     "Analyze trends for AI productivity tools")

    Returns:
        A detailed trend analysis report with recommended content actions.
    """
    result = await _call_a2a(TREND_AGENT_URL, query)
    return StringToolOutput(result)


# ---------------------------------------------------------------------------
# Tool 2 — Content Generation
# ---------------------------------------------------------------------------

@tool
async def call_content_agent(trend_analysis_and_actions: str) -> StringToolOutput:
    """
    Calls the ContentGeneratingAgent to produce media content from trend insights.

    Use this tool when you already have trend analysis output and need to generate:
    - A detailed video script (hook, narration per section, visuals direction, CTA)
    - Post content (caption, hashtags, best posting time)
    - A hero image prompt (sent to DALL-E 3)

    IMPORTANT: This tool expects the FULL output of call_trend_agent as its input,
    optionally enriched with extra creative direction from the user.
    Do NOT call this tool without first calling call_trend_agent.

    Args:
        trend_analysis_and_actions: The complete trend report + recommended actions,
                                    plus any extra user instructions about tone,
                                    platform, or style.

    Returns:
        JSON object containing video_script, post_content, and image_generation fields.
    """
    prompt = (
        "Based on the following trend analysis, generate a detailed video script, "
        "post content, and a hero image.\n\n"
        f"## Trend Analysis & Recommended Actions\n{trend_analysis_and_actions}"
    )
    result = await _call_a2a(CONTENT_AGENT_URL, prompt)
    return StringToolOutput(result)