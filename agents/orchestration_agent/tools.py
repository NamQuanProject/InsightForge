"""
Sub-agent tools for the RoutingAgent.
Each tool wraps one downstream A2A agent via JSON-RPC over HTTP.
"""

import json
import os
import uuid

import httpx
from beeai_framework.tools import StringToolOutput, tool


AGENT_HOST = os.environ.get("AGENT_HOST", "localhost")
TREND_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('TREND_AGENT_PORT', 9997)}"
CONTENT_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('CONTENT_AGENT_PORT', 9998)}"

A2A_TIMEOUT = 420


def extract_json(raw_content: str | dict) -> dict:
    try:
        if isinstance(raw_content, dict):
            return raw_content
        clean_json = raw_content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception:
        return {"error": "Failed to parse agent response", "raw": raw_content}


def _build_message_send(text: str, task_id: str | None = None) -> dict:
    message_obj = {
        "messageId": str(uuid.uuid4()),
        "role": "user",
        "parts": [{"type": "text", "text": text}],
    }
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
    try:
        result = response_json.get("result", response_json)
        data = result.get("task", result)

        if data.get("kind") == "message":
            parts = data.get("parts", [])
            text = "\n".join(
                part.get("text", "")
                for part in parts
                if isinstance(part, dict) and "text" in part
            )
            if text:
                return text

        artifacts = data.get("artifacts", [])
        for artifact in artifacts:
            parts = artifact.get("parts", [])
            text_parts = [part.get("text", "") for part in parts if isinstance(part, dict) and "text" in part]
            if text_parts:
                return "\n".join(text_parts)

        status_msg = data.get("status", {}).get("message", {})
        status_parts = status_msg.get("parts", [])
        if status_parts:
            text = "\n".join(
                part.get("text", "")
                for part in status_parts
                if isinstance(part, dict) and "text" in part
            )
            if text:
                return text

        history = data.get("history", [])
        for msg in reversed(history):
            if msg.get("role") in {"ROLE_AGENT", "agent"}:
                parts = msg.get("parts", [])
                text = "\n".join(
                    part.get("text", "")
                    for part in parts
                    if isinstance(part, dict) and "text" in part
                )
                if text and "Processing" not in text:
                    return text

        return "[no text found]"
    except Exception as exc:
        return f"[parse error: {exc}]"


async def _call_a2a(base_url: str, message: str, agent_name: str) -> str:
    payload = _build_message_send(message)
    async with httpx.AsyncClient(timeout=A2A_TIMEOUT) as client:
        resp = await client.post(f"{base_url}/", json=payload)
        resp.raise_for_status()
        data = resp.json()

    with open(f"{agent_name}_response.json", "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)

    if "error" in data:
        raise RuntimeError(f"A2A error from {base_url}: {data['error']}")

    return _extract_reply(data)


@tool
async def call_trend_agent(query: str) -> StringToolOutput:
    """
    Calls the TrendingAnalysisAgent to find and analyze the latest trending topics.
    """
    result = await _call_a2a(
        base_url=TREND_AGENT_URL,
        message=query,
        agent_name="TrendAgent",
    )
    return StringToolOutput(result)


@tool
async def call_content_agent(trend_analysis_and_actions: str) -> StringToolOutput:
    """
    Calls the ContentGeneratingAgent to produce media content from trend insights.
    """
    prompt = (
        "Dua tren bao cao xu huong sau, hay tao goi noi dung dung dinh dang JSON.\n"
        "Neu co nhieu ket qua trend, uu tien ket qua co trend_score cao nhat.\n"
        "Phai giu sat chu de trong bao cao, khong duoc chuyen sang chu de khac.\n"
        "Chi tra ve JSON dung format content generation.\n\n"
        f"## Trend Analysis\n{trend_analysis_and_actions}"
    )
    result = await _call_a2a(
        CONTENT_AGENT_URL,
        prompt,
        "ContentGeneration",
    )
    return StringToolOutput(result)
