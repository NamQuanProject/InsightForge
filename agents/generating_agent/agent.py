"""
Content Generation Agent
Transforms trend analysis into JSON matching generated_content_sample.json.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_litellm import ChatLiteLLM

load_dotenv()

SYSTEM_PROMPT = """You are an Elite Content Strategist and Creative Director.
Your task is to transform a trend report into a production-ready content bundle.

You must return JSON only with this exact top-level shape:
{
  "selected_keyword": "",
  "main_title": "",
  "video_script": {
    "title": "",
    "duration_estimate": "60s",
    "hook": "",
    "sections": [
      {
        "timestamp": "0:00-0:10",
        "label": "",
        "narration": "",
        "visuals": "",
        "notes": ""
      }
    ],
    "call_to_action": "",
    "captions_style": "",
    "music_mood": ""
  },
  "platform_posts": {
    "tiktok": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "facebook": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "instagram": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" }
  },
  "thumbnail": {
    "prompt": "",
    "style": "vivid",
    "size": "1792x1024",
    "output_path": "content_output.png"
  },
  "music_background": ""
}

Rules:
- ALWAYS write all user-facing content in Vietnamese.
- Do not wrap JSON in markdown fences.
- Do not call external tools.
- The thumbnail object is descriptive data only; no actual image generation is required.
- Use the trend context provided by the user. Do not invent unrelated topics.
- If the input contains multiple trend results, choose the item with the highest `trend_score`.
- Keep the generated content tightly aligned with the provided keyword and trend report.
"""

JSON_REPAIR_PROMPT = """You are a strict JSON formatter.
Convert the provided content-planning text into valid JSON matching this exact shape:
{
  "selected_keyword": "",
  "main_title": "",
  "video_script": {
    "title": "",
    "duration_estimate": "60s",
    "hook": "",
    "sections": [
      {
        "timestamp": "0:00-0:10",
        "label": "",
        "narration": "",
        "visuals": "",
        "notes": ""
      }
    ],
    "call_to_action": "",
    "captions_style": "",
    "music_mood": ""
  },
  "platform_posts": {
    "tiktok": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "facebook": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "instagram": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" }
  },
  "thumbnail": {
    "prompt": "",
    "style": "vivid",
    "size": "1792x1024",
    "output_path": "content_output.png"
  },
  "music_background": ""
}

Rules:
- Output JSON only.
- Write in Vietnamese.
- If a field is missing, keep safe defaults such as empty strings or empty arrays.
"""


class ContentGenerationAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("CONTENT_AGENT_MODEL", "gemini/gemini-2.5-flash")
        self.model: ChatLiteLLM | None = None
        self.repair_model: ChatLiteLLM | None = None

    async def initialize(self) -> "ContentGenerationAgent":
        if self.api_key is None:
            raise RuntimeError("No API key provided. Set GOOGLE_API_KEY or GEMINI_API_KEY.")

        self.model = ChatLiteLLM(
            model=self.model_name,
            max_tokens=4000,
            api_key=self.api_key,
        )
        self.repair_model = self.model
        print(f"ContentGenerationAgent ready - model {self.model_name}")
        return self

    async def answer_query(self, prompt: str) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Call .initialize() first.")

        try:
            result = await self.model.ainvoke(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception as exc:
            return {
                "error": "Failed to invoke content model",
                "message": str(exc),
                "selected_keyword": "",
                "main_title": "",
                "video_script": {},
                "platform_posts": {},
                "thumbnail": {},
                "music_background": "",
            }

        raw_content = result.content
        if isinstance(raw_content, list):
            raw_content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            )

        clean_json = str(raw_content).replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_json)
        except Exception:
            repaired = await self._repair_to_json(prompt=prompt, raw_content=str(raw_content))
            if repaired is not None:
                return repaired
            return {
                "error": "Failed to parse content agent response",
                "raw": str(raw_content),
                "selected_keyword": "",
                "main_title": "",
                "video_script": {},
                "platform_posts": {},
                "thumbnail": {},
                "music_background": "",
            }

    async def _repair_to_json(self, prompt: str, raw_content: str) -> dict[str, Any] | None:
        if self.repair_model is None:
            return None

        try:
            repaired = await self.repair_model.ainvoke(
                [
                    {"role": "system", "content": JSON_REPAIR_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Original content request:\n{prompt}\n\n"
                            f"Content planning text to convert:\n{raw_content}"
                        ),
                    },
                ]
            )
            repaired_content = repaired.content
            if isinstance(repaired_content, list):
                repaired_content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in repaired_content
                )
            cleaned = str(repaired_content).replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception:
            return None
