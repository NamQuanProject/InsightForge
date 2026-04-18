import csv
import json
from pathlib import Path
from urllib.parse import quote_plus
import os
from app.schema.post import PostResponse, PostRequest
import base64
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()


async def photo_convert(photos: list[str]) -> list[str]:
    load_dotenv(override=True)
    api_key = _clean_env_secret(os.getenv("IMG_BB_API_KEY", ""))
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

            payload = {"image": image_data}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, params={"key": api_key}, data=payload)
                result = response.json()

            if result.get("success"):
                result_urls.append(result["data"]["url"])
            else:
                raise Exception(f"Upload failed: {result}")

        except Exception as e:
            raise Exception(f"Error processing {photo}: {str(e)}")

    return result_urls


def _clean_env_secret(value: str) -> str:
    return value.strip().strip("\"'")


class PostService:
    def __init__(self) -> None:
        self.client = None
        self.mock_data_dir = Path(__file__).resolve().parents[1] / "mock_data"
        self.demo_scripts_dir = Path(__file__).resolve().parents[2] / "scripts"

    async def posting(self, query: PostRequest):
        if self._demo_fast_path_enabled():
            demo_response = self._demo_posting_response(query)
            if demo_response is not None:
                return demo_response

        if self.client is None:
            from app.services.a2a_client import InsightForgeA2AClient
            self.client = InsightForgeA2AClient()
        

        result = await self.client.posting(query.prompt, query.config_id, query.decision)

        return PostResponse(
            status="success",
            source="a2a-agent",
            result_markdown=str(result),
        )

    def _demo_posting_response(self, query: PostRequest) -> PostResponse | None:
        script_path = self.demo_scripts_dir / "script_upload.json"
        output_path = self.demo_scripts_dir / "output_upload.json"
        try:
            scripts = json.loads(script_path.read_text(encoding="utf-8"))
            outputs = json.loads(output_path.read_text(encoding="utf-8"))
            if not isinstance(scripts, list) or not isinstance(outputs, list):
                return None

            for index, item in enumerate(scripts):
                if not isinstance(item, dict) or index >= len(outputs):
                    continue
                prompt_matches = self._normalize_prompt(query.prompt) == self._normalize_prompt(item.get("prompt", ""))
                config_matches = str(query.config_id) == str(item.get("config_id", ""))
                decision_matches = query.decision == item.get("decision")
                if prompt_matches and config_matches and decision_matches:
                    return PostResponse(**outputs[index])
        except Exception:
            return None
        return None

    def _normalize_prompt(self, value: str) -> str:
        return " ".join(str(value or "").split()).casefold()

    def _demo_fast_path_enabled(self) -> bool:
        value = os.environ.get("DEMO_FAST_PATH_ENABLED", "true")
        return value.strip().lower() not in {"0", "false", "no", "off"}
