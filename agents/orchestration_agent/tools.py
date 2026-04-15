"""
Sub-agent tools for the RoutingAgent.
Each tool wraps one downstream A2A agent via httpx message/send.
The BeeAI RequirementAgent LLM decides which tool(s) to call based on the user query.
"""

import os
import uuid
import json

import httpx
from beeai_framework.tools import StringToolOutput, tool



AGENT_HOST = os.environ.get("AGENT_HOST", "localhost")
TREND_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('TREND_AGENT_PORT', 9997)}"
CONTENT_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('CONTENT_AGENT_PORT', 9998)}"

A2A_TIMEOUT = 180  # seconds — generous for trend scraping + image gen


# ---------------------------------------------------------------------------
# Shared A2A transport
# ---------------------------------------------------------------------------

def extract_json(raw_content: str) -> dict:
    try:
            # Clean Markdown if present
            clean_json = raw_content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
    except Exception:
            return {"error": "Failed to parse agent response", "raw": raw_content}


def _build_message_send(text: str, task_id: str | None = None) -> dict:
    """Construct a spec-compliant A2A message/send JSON-RPC payload."""
    message_obj = {
        "messageId": str(uuid.uuid4()),
        "role": "user",
        "parts": [{"type": "text", "text": text}],
    }
    
    # Only add taskId if we are continuing an existing thread
    if task_id:
        message_obj["taskId"] = task_id

    return {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": message_obj,
        },
    }


def _extract_reply(response_json: dict) -> str:
    """
    Pull assistant text from an A2A message/send response.
    Tries result.status.message.parts → result.artifacts[0].parts → result.parts.
    """
    try:
        # The top-level key in your doc example is 'task'
        # Adjust based on whether your JSON-RPC wrapper puts this inside 'result'
        data = response_json.get("result", response_json).get("task", response_json.get("result", {}))

        # 1. Primary Target: The Artifacts (The actual 'output' of the workflow)
        artifacts = data.get("artifacts", [])
        for artifact in artifacts:
            # We look for the 'result' artifact specifically
            parts = artifact.get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            if text_parts:
                return "\n".join(text_parts)

        # 2. Secondary: Task Status Message
        status_msg = data.get("status", {}).get("message", {})
        status_parts = status_msg.get("parts", [])
        if status_parts:
            return "\n".join(p.get("text", "") for p in status_parts if "text" in p)

        # 3. Fallback: The latest message in 'history' with role 'ROLE_AGENT'
        history = data.get("history", [])
        for msg in reversed(history):
            if msg.get("role") == "ROLE_AGENT":
                parts = msg.get("parts", [])
                text = "\n".join(p.get("text", "") for p in parts if "text" in p)
                # Skip generic processing messages
                if text and "Processing" not in text:
                    return text

        return "[no text found]"

    except Exception as exc:
        return f"[parse error: {exc}]"


async def _call_a2a(base_url: str, message: str, agent_name: str) -> str:
    """POST message/send to an A2A agent and return the text reply."""
    payload = _build_message_send(message)
    async with httpx.AsyncClient(timeout=A2A_TIMEOUT) as client:
        resp = await client.post(f"{base_url}/", json=payload)
        resp.raise_for_status()
        data = resp.json()
    
    with open(f"{agent_name}_response.json",  "w", encoding = "utf-8") as f:
        json.dump(extract_json(data), f, indent = 4, ensure_ascii=False)

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
    result = await _call_a2a(
        base_url = TREND_AGENT_URL, 
        message = query, 
        agent_name="TrendAgent")
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
    result = await _call_a2a(
        CONTENT_AGENT_URL, prompt, "ContentGeneration")
    return StringToolOutput(result)