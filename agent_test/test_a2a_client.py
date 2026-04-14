"""
A2A Workflow Client
Chains: User Query → TrendingAnalysisAgent (9997) → ContentGeneratingAgent (9998)
"""

import asyncio
import json
import os
import uuid
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AGENT_HOST = os.environ.get("AGENT_HOST", "localhost")
TREND_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('TREND_AGENT_PORT', 9997)}"
CONTENT_AGENT_URL = f"http://{AGENT_HOST}:{os.environ.get('CONTENT_AGENT_PORT', 9998)}"

TIMEOUT = 120  # seconds — trend + image gen can be slow


# ---------------------------------------------------------------------------
# Low-level A2A helpers
# ---------------------------------------------------------------------------

def _build_task_payload(user_message: str, task_id: str | None = None) -> dict:
    """Build a minimal A2A message/send JSON-RPC payload (A2A spec >= 0.2)."""
    # return {
    #     "jsonrpc": "2.0",
    #     "id": str(uuid.uuid4()),
    #     "method": "message/send",
    #     "params": {
    #         "message": {
    #             "messageId": str(uuid.uuid4()),
    #             "taskId": task_id or str(uuid.uuid4()),
    #             "role": "user",
    #             "parts": [{"type": "text", "text": user_message}],
    #         },
    #     },
    # }
    message_obj = {
        "messageId": str(uuid.uuid4()),
        "role": "user",
        "parts": [{"type": "text", "text": user_message}],
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


def _extract_text(response_json: dict) -> str:
    """
    Pull assistant text from an A2A JSON-RPC response.
    Tries every known response shape in priority order:
      1. result.status.message.parts     (message/send -> Task, most common)
      2. result.artifacts[0].parts       (Task with artifacts)
      3. result.parts                    (bare Message response)
    """
    # try:
    #     result = response_json["result"]
 
    #     # 1. Task.status.message.parts
    #     status_msg = (result.get("status") or {}).get("message") or {}
    #     status_parts = status_msg.get("parts", [])
    #     if status_parts:
    #         return "\n".join(
    #             p.get("text", "") for p in status_parts if p.get("type") == "text"
    #         )
 
    #     # 2. Task.artifacts[0].parts
    #     artifacts = result.get("artifacts") or []
    #     if artifacts:
    #         parts = artifacts[0].get("parts", [])
    #         text = "\n".join(p.get("text", "") for p in parts if p.get("type") == "text")
    #         if text:
    #             return text
 
    #     # 3. Bare Message.parts
    #     if "parts" in result:
    #         return "\n".join(
    #             p.get("text", "") for p in result["parts"] if p.get("type") == "text"
    #         )
 
    #     return f"[no text found] raw={json.dumps(result)[:400]}"
 
    # except Exception as exc:
    #     return f"[parse error: {exc}] raw={json.dumps(response_json)[:400]}"
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

async def call_agent(base_url: str, message: str, label: str, client: httpx.AsyncClient) -> str:
    """Send one task to an A2A agent and return the assistant text."""
    payload = _build_task_payload(message)

    print(f"\n{'─'*60}")
    print(f"▶  Calling {label}")
    print(f"   URL  : {base_url}")
    print(f"   Input: {message[:120]}{'…' if len(message) > 120 else ''}")
    print(f"{'─'*60}")

    response = await client.post(base_url, json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    data = response.json()
    with open(f"{label}_response.json", "w", encoding = 'utf-8') as f:
        json.dump(data, f, indent = 4)

    if "error" in data:
        raise RuntimeError(f"{label} returned error: {data['error']}")

    text = _extract_text(data)
    with open(f"{label}_text.json", "w", encoding = "utf-8") as f:
        json.dump(text, f, indent = 4)
    print(f"✅ {label} responded ({len(text)} chars)")
    return text


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def check_agent_card(base_url: str, name: str, client: httpx.AsyncClient) -> bool:
    """Verify agent is reachable via /.well-known/agent.json"""
    try:
        r = await client.get(f"{base_url}/.well-known/agent-card.json", timeout=10)
        card = r.json()
        print(f"  ✓ {name}: {card.get('name')} v{card.get('version')} — {card.get('description', '')[:60]}")
        return True
    except Exception as exc:
        print(f"  ✗ {name} unreachable: {exc}")
        return False


# ---------------------------------------------------------------------------
# Workflow orchestration
# ---------------------------------------------------------------------------

async def run_workflow(user_query: str) -> dict[str, Any]:
    """
    Full pipeline:
      1. Trend agent  → trend analysis + recommended actions
      2. Content agent → video script + post content + image

    Returns a dict with both agents' outputs.
    """
    async with httpx.AsyncClient() as client:

        # ── 0. Health checks ─────────────────────────────────────────────
        print("\n🔍 Checking agents…")
        ok_trend = await check_agent_card(TREND_AGENT_URL, "TrendingAnalysisAgent", client)
        ok_content = await check_agent_card(CONTENT_AGENT_URL, "ContentGeneratingAgent", client)

        if not ok_trend:
            raise RuntimeError(f"TrendingAnalysisAgent not reachable at {TREND_AGENT_URL}")
        if not ok_content:
            raise RuntimeError(f"ContentGeneratingAgent not reachable at {CONTENT_AGENT_URL}")

        # ── 1. Trend Analysis ─────────────────────────────────────────────
        trend_output = await call_agent(
            base_url=f"{TREND_AGENT_URL}/",
            message=user_query,
            label="TrendingAnalysisAgent",
            client=client,
        )

        print(trend_output)

        # ── 2. Content Generation ─────────────────────────────────────────
        # Pass the full trend output as context to the content agent
        content_prompt = (
            f"Based on the following trend analysis, generate a detailed video script, "
            f"post content, and a hero image.\n\n"
            f"## Trend Analysis & Recommended Actions\n{trend_output}"
        )

        content_output = await call_agent(
            base_url=f"{CONTENT_AGENT_URL}/",
            message=content_prompt,
            label="ContentGeneratingAgent",
            client=client,
        )
        print(content_output)

    return {
        "query": user_query,
        "trend_analysis": trend_output,
        "content_output": content_output,
    }


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def print_results(results: dict[str, Any]) -> None:
    divider = "═" * 60

    print(f"\n{divider}")
    print("  WORKFLOW RESULTS")
    print(divider)

    print("\n📊  TREND ANALYSIS")
    print("─" * 60)
    print(results["trend_analysis"])

    print(f"\n{divider}")
    print("🎬  CONTENT OUTPUT")
    print("─" * 60)

    raw = results["content_output"]
    try:
        # Try to pretty-print if the agent returned JSON
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        structured = json.loads(clean)

        vs = structured.get("video_script", {})
        print(f"\n🎥 Video Script: {vs.get('title', 'N/A')}")
        print(f"   Duration    : {vs.get('duration_estimate', 'N/A')}")
        print(f"   Hook        : {vs.get('hook', 'N/A')}")
        for sec in vs.get("sections", []):
            print(f"\n   [{sec.get('timestamp')}] {sec.get('label')}")
            print(f"   Narration : {sec.get('narration', '')[:120]}")
            print(f"   Visuals   : {sec.get('visuals', '')[:80]}")

        pc = structured.get("post_content", {})
        print(f"\n📝 Post Content ({pc.get('platform', 'N/A')})")
        print(f"   Caption : {str(pc.get('caption', ''))[:200]}")
        print(f"   Hashtags: {' '.join(pc.get('hashtags', []))}")
        print(f"   CTA     : {pc.get('cta', 'N/A')}")

        ig = structured.get("image_generation", {})
        print(f"\n🖼  Image")
        print(f"   Prompt  : {str(ig.get('prompt', ''))[:120]}")
        print(f"   Saved   : {ig.get('output_path', 'N/A')}")

    except (json.JSONDecodeError, AttributeError):
        # Plain text fallback
        print(raw)

    print(f"\n{divider}\n")


# ---------------------------------------------------------------------------
# Interactive test menu
# ---------------------------------------------------------------------------

SAMPLE_QUERIES = [
    "Topics đang trendings nhất ở Việt Nam hiện tại là gì và tôi muốn tạo dựng nội dung trên nó như thế nào ?"
]

async def interactive_mode() -> None:
    print("\n" + "═" * 60)
    print("  A2A WORKFLOW CLIENT — Trend → Content Pipeline")
    print("═" * 60)
    print(f"  Trend Agent  : {TREND_AGENT_URL}")
    print(f"  Content Agent: {CONTENT_AGENT_URL}")
    print("═" * 60)

    print("\nSample queries:")
    for i, q in enumerate(SAMPLE_QUERIES, 1):
        print(f"  [{i}] {q}")
    print("  [0] Enter custom query")
    print("  [q] Quit")

    while True:
        choice = input("\nSelect option: ").strip()

        if choice.lower() == "q":
            print("Bye!")
            break

        if choice == "0":
            query = input("Enter your query: ").strip()
        elif choice.isdigit() and 1 <= int(choice) <= len(SAMPLE_QUERIES):
            query = SAMPLE_QUERIES[int(choice) - 1]
        else:
            print("Invalid choice.")
            continue

        if not query:
            continue

        try:
            print(f"\n🚀 Running workflow for: {query}")
            results = await run_workflow(query)
            print_results(results)

            # Optionally save raw results
            out_file = f"workflow_result_{uuid.uuid4().hex[:8]}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Full results saved to: {out_file}")

        except Exception as exc:
            print(f"\n❌ Workflow failed: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(interactive_mode())