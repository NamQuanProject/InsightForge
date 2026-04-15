"""
Content Generation Agent
Receives trend analysis + recommended actions → outputs:
  1. Detailed video script
  2. Post content (caption, hashtags, CTA)
  3. Generated image (via MCP tool)
"""

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate
from langchain_litellm import ChatLiteLLM
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

load_dotenv()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an Elite Content Strategist and Creative Director.
Your task is to transform trend analysis into a production-ready content bundle.

## INPUT
You will receive:
1. Selected Keyword (The primary trend)
2. Trend Analysis (Signals, velocity, reasoning)
3. Recommended Actions (Angles, duration, CTA)

## OUTPUT FORMAT (Strict JSON)
{
  "selected_keyword": "<the trend keyword analyzed>",
  "main_title": "<a catchy, high-CTR title for the campaign>",
  "video_script": {
    "title": "<video title>",
    "duration_estimate": "60s",
    "hook": "<opening 5-second line>",
    "sections": [
      {
        "timestamp": "0:00-0:10",
        "label": "Hook",
        "narration": "<exact words to be spoken>",
        "visuals": "<B-roll or screen directions>",
        "notes": "<tone/pacing instructions>"
      }
    ],
    "call_to_action": "<exact closing words>",
    "captions_style": "<visual description of subs>",
    "music_mood": "<music description>"
  },
  "platform_posts": {
    "tiktok": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "facebook": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "instagram": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" }
  },
  "thumbnail": {
    "prompt": "<detailed StableDiffusion-XL Prompt based on trend analysis>",
    "style": "vivid",
    "size": "1792x1024",
    "output_path": "content_output.png"
  },
  "music_background": "<matching the music_mood>"
}

## RULES
- NARRATION: Write out every single word. Do not summarize sections.
- THUMBNAIL PROMPT: Must include lighting, mood, color palette, and specific subjects.
- PLATFORMS: Adapt the tone (TikTok = high energy/short, Facebook = informative, Instagram = aesthetic).
- LANGUAGE: If the input is in Vietnamese, all content (narration, captions) MUST be in Vietnamese.
- Output ONLY the JSON object. No preamble.
"""

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ContentGenerationAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.mcp_client: MultiServerMCPClient | None = None
        self.agent = None

    # ------------------------------------------------------------------
    # Initialisation (call once, before any queries)
    # ------------------------------------------------------------------

    async def initialize(self) -> "ContentGenerationAgent":
        if self.api_key is None:
            raise RuntimeError("No API key provided. Set GEMINI_API_KEY or pass api_key=.")

        # ── MCP client pointing at our local server ──────────────────────
        self.mcp_client = MultiServerMCPClient(
             {
                    "image_generation": StdioConnection(
                        command="python",
                        args=["-m",  "mcp_servers.generating_servers.mcp_server"],
                        transport="stdio"
                    )
             }
        )

        all_tools = await self.mcp_client.get_tools()

        # ── LLM ──────────────────────────────────────────────────────────
        llm = ChatLiteLLM(
            model="gemini/gemini-2.5-flash",
            max_tokens=4000,
            api_key=self.api_key,
        )

        # ── ReAct prompt ─────────────────────────────────────────────────
        # react_prompt = PromptTemplate.from_template(
        #     SYSTEM_PROMPT
        #     + """

        #     You have access to the following tools:
        #     {tools}

        #     Tool names: {tool_names}

        #     Use this format:
        #     Thought: <your reasoning>
        #     Action: <tool name>
        #     Action Input: <tool input as JSON>
        #     Observation: <tool result>
        #     ... (repeat Thought/Action/Observation as needed)
        #     Thought: I now have all outputs ready.
        #     Final Answer: <the strict JSON object described above>

        #     Begin!

        #     User query:
        #     {input}

        #     {agent_scratchpad}"""
        #     )
        system_message = (
            f"{SYSTEM_PROMPT}\n\n"
            "STEP 1: Use the 'generate_image' tool with the 'thumbnail.prompt' you design.\n"
            "STEP 2: Use the tool output (image path) to populate the 'thumbnail.output_path'.\n"
            "STEP 3: Compile all sections into the final JSON structure."
        )

        self.agent = create_agent(
            model = llm,
            tools = all_tools,
            name = "ContentGenerationAgent",
            system_prompt = system_message
        )

        print(f"✅ ContentGenerationAgent ready — {len(all_tools)} tool(s): {[t.name for t in all_tools]}")
        return self

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    async def answer_query(self, prompt: str) -> dict[str, Any]:
        if not self.agent:
            raise RuntimeError("Call .initialize() first.")

        query = prompt

        # The agent will now automatically:
        # 1. Thought: 'I need an image. I'll call generate_image.'
        # 2. Action: Call tool.
        # 3. Observation: 'Image saved at path/to/img.png'
        # 4. Final Answer: JSON with all parts.
        result = await self.agent.ainvoke({"messages": [("user", query)]})
        
        # The final message in the state is the agent's answer
        final_message = result["messages"][-1].content
        return final_message
        # try:
        #     # Clean Markdown if present
        #     clean_json = final_message.replace("```json", "").replace("```", "").strip()
        #     return json.loads(clean_json)
        # except Exception:
        #     return {"error": "Failed to parse agent response", "raw": final_message}

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    # async def close(self):
    #     if self.mcp_client:
    #         await self.mcp_client.__aexit__(None, None, None)


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

async def _demo():
    agent = ContentGenerationAgent()
    await agent.initialize()

    trend_analysis = """
    TikTok trend: 'AI tools that save time' is surging (+340% WoW).
    Target audience: freelancers & small business owners aged 25-40.
    Top performing hook style: problem-agitation-solution in under 10 seconds.
    Competitor gap: nobody is showing real workflow demos (only feature lists).
    """

    recommended_actions = """
    1. Post a 60-second TikTok showing a REAL before/after workflow using AI.
    2. Use authentic, lo-fi screen-recording aesthetic (no polished studio).
    3. Lean into the 'time saved' metric — show a clock or timer on screen.
    4. CTA: 'Follow for daily AI tips that save you 2 hours a day.'
    """
    query = (
            f"Based on the following trend analysis, generate a detailed video script, "
            f"post content, and a hero image.\n\n"
            f"## Trend Analysis: {trend_analysis}"
            f"## Recommended action: {recommended_actions}"
        )

    result = await agent.answer_query(query)

    print("\n" + "=" * 60)
    print("\n📹 VIDEO SCRIPT TITLE:", result["video_script"] if result["video_script"] else "N/A")
    print("📝 CAPTION PREVIEW:", str(result["post_content"]) if result["post_content"] else "N/A")
    print("🖼  IMAGE SAVED:", result["image_result"] if result["image_result"] else "N/A")
    print("=" * 60)

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent = 4, ensure_ascii=False)
    return result

if __name__ == "__main__":
    asyncio.run(_demo())