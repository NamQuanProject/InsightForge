import asyncio
import httpx
import uuid
import json

# Replace with your actual Orchestrator URL
ORCHESTRATOR_URL = "http://localhost:9996" 

async def test_orchestrator():
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"type": "text", "text": "Topic đang trend trong ngày hôm nay ở lĩnh vực tech và tôi nên tạo nội dung như nào ?"}],
            },
        },
    }

    async with httpx.AsyncClient() as client:
        print(f"🚀 Sending request to Orchestrator...")
        try:
            response = await client.post(ORCHESTRATOR_URL, json=payload, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()
            print("\n✅ Server Response:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())