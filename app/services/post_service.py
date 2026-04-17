import csv
from pathlib import Path
from urllib.parse import quote_plus
import os
from app.schema.post import PostResponse, PostRequest
import base64
import asyncio
import httpx


async def photo_convert(photos: list[str]) -> list[str]:
    api_key = os.getenv("IMG_BB_API_KEY", "")
    if not api_key:
        raise Exception("IMG_BB_API_KEY not configured")

    url = "https://api.imgbb.com/1/upload"
    result_urls = []

    for photo in photos:
        if photo.startswith("http://") or photo.startswith("https://"):
            result_urls.append(photo)
            continue

        try:

            def read_file():
                with open(photo, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")

            image_data = await asyncio.to_thread(read_file)

            payload = {"key": api_key, "image": image_data}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, data=payload)
                result = response.json()

            if result.get("success"):
                result_urls.append(result["data"]["url"])
            else:
                raise Exception(f"Upload failed: {result}")

        except Exception as e:
            raise Exception(f"Error processing {photo}: {str(e)}")

    return result_urls


class PostService:
    def __init__(self) -> None:
        self.client = None
        self.mock_data_dir = Path(__file__).resolve().parents[1] / "mock_data"

    async def posting(self, query: PostRequest):
        if self.client is None:
            from app.services.a2a_client import InsightForgeA2AClient

            self.client = InsightForgeA2AClient()
        result = await self.client.posting(
            prompt=query.prompt, config_id=query.config_id, decisions=query.decision
        )

        return PostResponse(
            status="success",
            source="a2a-agent",
            result_markdown=str(result),
        )
