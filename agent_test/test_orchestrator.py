import asyncio
import json
import os
import uuid
from pathlib import Path

import httpx

from app.services.a2a_client import InsightForgeA2AClient


ORCHESTRATOR_URL = f"http://{os.environ.get('AGENT_HOST', 'localhost')}:{os.environ.get('ROUTING_AGENT_PORT', 9996)}"
OUTPUT_DIR = Path(os.environ.get("ORCHESTRATOR_OUTPUT_DIR", "."))
RAW_RESPONSE_FILE = OUTPUT_DIR / "orchestrator_raw_response.json"
FINAL_OUTPUT_FILE = OUTPUT_DIR / "orchestrator_output.json"


def _extract_final_text(response_json: dict) -> str:
    result = response_json.get("result", {})
    task = result.get("task", result)

    status_message = task.get("status", {}).get("message", {})
    parts = status_message.get("parts", [])
    for part in parts:
        if isinstance(part, dict) and "text" in part:
            return part["text"]

    history = task.get("history", [])
    for message in reversed(history):
        if message.get("role") in {"agent", "ROLE_AGENT"}:
            for part in message.get("parts", []):
                if isinstance(part, dict) and "text" in part:
                    return part["text"]

    return ""


def _extract_final_json(response_json: dict) -> dict:
    text = _extract_final_text(response_json).strip()
    if not text:
        return {"error": "No final text found in orchestrator response", "raw": response_json}

    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw_text": text}


async def test_orchestrator() -> None:
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Chu de dang trend trong ngay hom nay ve the thao la gi va toi nen tao noi dung nhu the nao?",
                    }
                ],
            },
        },
    }

    async with httpx.AsyncClient() as client:
        print("Sending request to Orchestrator...")
        try:
            response = await client.post(f"{ORCHESTRATOR_URL}/", json=payload, timeout=420.0)
            response.raise_for_status()

            result = response.json()
            extracted_output = _extract_final_json(result)
            final_output = InsightForgeA2AClient().normalize_orchestrator_output(
                extracted_output,
                prompt=payload["params"]["message"]["parts"][0]["text"],
            )

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            RAW_RESPONSE_FILE.write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            FINAL_OUTPUT_FILE.write_text(
                json.dumps(final_output, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            print("\nServer Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"\nSaved raw response to: {RAW_RESPONSE_FILE}")
            print(f"Saved extracted output to: {FINAL_OUTPUT_FILE}")
        except Exception as exc:
            print(f"Error: {exc!r}")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
