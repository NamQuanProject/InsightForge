"""
Content Generation Agent
Transforms trend analysis and user context into a multi-image social post bundle.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

load_dotenv()

SYSTEM_PROMPT = """
You are InsightForge's Content Generation Agent: a senior Vietnamese content
strategist and creative director.

Your job is to turn a trend report into a personalized, production-ready
multi-image social post. The output is NOT a video script anymore.

MANDATORY TOOL ORDER
1. Before writing content, call `get_user_profile(user_id)`.
2. Then call `get_latest_generated_content(user_id)`.
3. Use `generate_images_batch(prompts, output_paths)` to generate the images
   for the post image set when image prompts are ready.

PERSONALIZATION PRIORITY
Use the user profile as the primary creative context, not as an afterthought.
Strongly adapt the content using:
- about_me: point of view, credibility, lived context, and brand voice.
- content_preferences.content_groups: topic lanes to stay within.
- content_preferences.priority_formats: preferred content format cues.
- content_preferences.keyword_hashtags: keywords and hashtag language to reuse.
- content_preferences.audience_persona: who the post is speaking to.
- content_preferences.focus_content_goal: what the content must achieve.
- options.timezone and options.default_post_times: best posting time.
- options.linked_platforms: platforms to prepare.
- options.default_visibility and options.weekly_content_frequency: publishing plan.

If the user has previous generated content, use it as a style reference for
voice, hook style, caption length, and recurring keywords. Do not repeat the
same post idea; build continuity.

CONTENT RULES
- User-facing text must be natural Vietnamese.
- Image prompts must be English for the image model.
- Create a carousel or multi-image post with 3 to 6 images.
- Every image needs a user-facing `description` explaining what the image
  communicates, plus an English `prompt` for generation.
- Every image item must include a unique `output_path`, for example
  `post_image_1.png`, `post_image_2.png`.
- The content should connect the trend to the user's own expertise, keywords,
  target audience, and content direction.
- Avoid generic advice. Make the angle feel like it belongs to this specific user.
- Return pure JSON only. Do not wrap the JSON in markdown fences.

REQUIRED JSON SHAPE
{
  "selected_keyword": "chosen trend keyword",
  "main_title": "main post title",
  "post_content": {
    "post_type": "multi_image_post",
    "title": "post title",
    "hook": "opening line",
    "caption": "full caption for the main post",
    "description": "short summary of the post angle",
    "body": "core post copy or carousel narrative",
    "call_to_action": "CTA",
    "hashtags": ["#tag"],
    "tone": "tone description",
    "personalization_notes": [
      "how user profile, keywords, audience, or goals shaped the content"
    ]
  },
  "image_set": [
    {
      "index": 1,
      "title": "image title",
      "description": "Vietnamese description of what this image should show",
      "prompt": "English image-generation prompt with composition, lighting, style",
      "style": "vivid",
      "size": "1792x1024",
      "output_path": "post_image_1.png"
    }
  ],
  "platform_posts": {
    "tiktok": {
      "caption": "",
      "hashtags": [],
      "cta": "",
      "best_post_time": "",
      "image_notes": ""
    },
    "facebook": {
      "caption": "",
      "hashtags": [],
      "cta": "",
      "best_post_time": "",
      "image_notes": ""
    },
    "instagram": {
      "caption": "",
      "hashtags": [],
      "cta": "",
      "best_post_time": "",
      "image_notes": ""
    }
  },
  "publishing": {
    "default_visibility": "",
    "recommended_platforms": [],
    "timezone": "",
    "weekly_content_frequency": 0
  },
  "error": null
}

If image generation fails, still return the full `image_set` with prompts and
descriptions, and include a concise error object in `error`.
"""

JSON_REPAIR_PROMPT = """
You repair malformed content-planning text into valid JSON.

Return pure JSON only, matching this exact shape:
{
  "selected_keyword": "",
  "main_title": "",
  "post_content": {
    "post_type": "multi_image_post",
    "title": "",
    "hook": "",
    "caption": "",
    "description": "",
    "body": "",
    "call_to_action": "",
    "hashtags": [],
    "tone": "",
    "personalization_notes": []
  },
  "image_set": [
    {
      "index": 1,
      "title": "",
      "description": "",
      "prompt": "",
      "style": "vivid",
      "size": "1792x1024",
      "output_path": "post_image_1.png"
    }
  ],
  "platform_posts": {
    "tiktok": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "image_notes": "" },
    "facebook": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "image_notes": "" },
    "instagram": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "image_notes": "" }
  },
  "publishing": {
    "default_visibility": "",
    "recommended_platforms": [],
    "timezone": "",
    "weekly_content_frequency": 0
  },
  "error": null
}

Vietnamese for user-facing content. English for image prompts.
"""


class ContentGenerationAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("CONTENT_AGENT_MODEL", "gemini/gemini-2.5-flash")
        self.mcp_client = MultiServerMCPClient(
            {
                "image_generation": StdioConnection(
                    transport="stdio",
                    command="python",
                    args=["-m", "mcp_servers.generating_servers.mcp_server"],
                )
            }
        )
        self.agent = None
        self.model: ChatLiteLLM | None = None
        self.repair_model: ChatLiteLLM | None = None

    async def initialize(self) -> "ContentGenerationAgent":
        tools = await self.mcp_client.get_tools()
        if self.api_key is None:
            raise RuntimeError("No API key provided. Set GOOGLE_API_KEY or GEMINI_API_KEY.")

        self.model = ChatLiteLLM(
            model=self.model_name,
            max_tokens=4000,
            api_key=self.api_key,
        )
        self.repair_model = self.model
        self.agent = create_agent(
            model=self.model,
            tools=tools,
            name="ContentGenerationAgent",
            system_prompt=SYSTEM_PROMPT,
        )
        print("Agent initialized with tools: \n", tools)
        print("Model:", self.model_name)
        print("\nNumber of tools: ", len(tools))
        return self

    async def answer_query(self, prompt: str) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Call .initialize() first.")

        try:
            response = await self.agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        except Exception as exc:
            return self._empty_response(
                error="Failed to invoke content model",
                message=str(exc),
            )

        print(response)
        raw_content = response["messages"][-1].content
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
            return self._empty_response(
                error="Failed to parse content agent response",
                raw=str(raw_content),
            )

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

    def _empty_response(self, **error_fields: Any) -> dict[str, Any]:
        return {
            "selected_keyword": "",
            "main_title": "",
            "post_content": {},
            "image_set": [],
            "platform_posts": {},
            "publishing": {},
            "error": error_fields or None,
        }


if __name__ == "__main__":
    import asyncio

    async def test_agent():
        agent = ContentGenerationAgent()
        await agent.initialize()
        result = await agent.answer_query(
            "Trend Report: wellness habits for busy founders. "
            "Trend Score: 91. Keywords: daily wellness, healthy routines."
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test_agent())
