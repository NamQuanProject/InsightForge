"""
Content Generation Agent
Transforms trend analysis into JSON matching generated_content_sample.json.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_litellm import ChatLiteLLM
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from pathlib import Path

load_dotenv()

SYSTEM_PROMPT = """Bạn là một Chuyên gia Chiến lược Nội dung và Giám đốc Sáng tạo xuất sắc.
Nhiệm vụ của bạn là biến một báo cáo xu hướng (trend report) thành một bộ nội dung sản xuất hoàn chỉnh.

QUY TRÌNH TỪNG BƯỚC:
1. Phân tích xu hướng: Chọn từ khóa có `trend_score` cao nhất.
2. Video Script: Tạo kịch bản chi tiết với nhiều phân đoạn. Mỗi phân đoạn gồm: timestamp, label, narration, notes.
3. Hình ảnh (Thumbnails): Với MỖI phân đoạn video, tạo một mô tả hình ảnh (prompt) riêng biệt để đưa vào công cụ generate_image_batches và phải generate ra ảnh.
4. Platform Posts: Viết nội dung quảng bá cho TikTok, Facebook, Instagram.

CẤU TRÚC JSON BẮT BUỘC:
{
  "selected_keyword": "Từ khóa được chọn",
  "main_title": "Tiêu đề chính hấp dẫn",
  "video_script": {
    "title": "Tiêu đề kịch bản",
    "duration_estimate": "30s",
    "hook": "Câu mở đầu thu hút",
    "sections": [
      {
        "timestamp": "0:00-0:10",
        "label": "Tên phân đoạn",
        "narration": "Lời bình tiếng Việt",
        "notes": "Ghi chú hình ảnh/hiệu ứng",
        "thumbnail": {
            "prompt": "Mô tả hình ảnh bằng tiếng Anh (chi tiết về ánh sáng, bố cục, SDXL style)",
            "description": "Same value as prompt, saved to image_store.description",
            "style": "vivid",
            "size": "1792x1024",
            "output_path": "section_1.png" 
        }
      }
    ],
    "call_to_action": "Lời kêu gọi hành động",
    "captions_style": "Phong cách phụ đề",
    "music_mood": "Tâm trạng âm nhạc"
  },
  "platform_posts": {
    "tiktok": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "facebook": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" },
    "instagram": { "caption": "", "hashtags": [], "cta": "", "best_post_time": "", "thumbnail_description": "" }
  },
  "music_background": "Mô tả nhạc nền"
}

QUY TẮC CỐ ĐỊNH:
- Ngôn ngữ: Toàn bộ nội dung cho người dùng phải bằng tiếng Việt tự nhiên, không dùng từ ngữ máy móc.
- Image Prompts: Phải viết bằng tiếng Anh để mô hình Stable Diffusion hiểu tốt nhất.
- Thumbnail Description: Mỗi thumbnail.description phải giống thumbnail.prompt để backend lưu vào image_store.description.
- Output Path: Mỗi section PHẢI có tên file output_path riêng biệt (vd: section_1.png, section_2.png...).
- Phải dùng tools generate_image_patches để tạo ảnh cho từng video section
- Không bao quanh JSON bằng markdown fences (```json).
- Chỉ trả về duy nhất dữ liệu JSON.
"""

JSON_REPAIR_PROMPT = """Bạn là một chuyên gia sửa lỗi định dạng JSON.
Hãy chuyển đổi văn bản kế hoạch nội dung sau đây thành định dạng JSON hợp lệ, khớp chính xác với cấu trúc này:

{
  "selected_keyword": "",
  "main_title": "",
  "video_script": {
    "title": "",
    "duration_estimate": "30s",
    "hook": "",
    "sections": [
      {
        "timestamp": "",
        "label": "",
        "narration": "",
        "notes": "",
        "thumbnail": {
          "prompt": "",
          "description": "",
          "style": "vivid",
          "size": "1792x1024",
          "output_path": ""
        }
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
  "music_background": ""
}

QUY TẮC:
- Trả về JSON thuần túy, không có văn bản giải thích hay dấu ngoặc markdown.
- Đảm bảo mỗi section trong video_script đều có object thumbnail riêng.
- Nội dung hiển thị bằng tiếng Việt, Prompt hình ảnh bằng tiếng Anh.
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
                    args=["-m", "mcp_servers.generating_servers.mcp_server"]
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
            api_key=self.api_key
        )
        self.repair_model = self.model
        self.agent = create_agent(
            model = self.model,
            tools = tools,
            name = "ContentGenerationAgent",
            system_prompt=SYSTEM_PROMPT
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


if __name__ == "__main__":
    import asyncio
    import json

    async def test_agent():
        # 1. Khởi tạo Agent
        # Đảm bảo bạn đã có GOOGLE_API_KEY hoặc GEMINI_API_KEY trong file .env
        agent = ContentGenerationAgent()
        
        try:
            print("--- Đang khởi tạo ContentGenerationAgent ---")
            await agent.initialize()
            
            # 2. Tạo một báo cáo xu hướng mẫu (Trend Report) để test
            sample_trend_report = """
            Trend Report: Sự trỗi dậy của AI Agents trong năm 2026.
            Trend Score: 98
            Keywords: AI Automation, Agentic Workflows, Productivity, Future of Work.
            Bối cảnh: Người dùng đang chuyển dịch từ việc 'chat' với AI sang việc sử dụng AI để thực hiện các tác vụ tự động (Task Execution).
            """
            
            print(f"--- Đang phân tích xu hướng và tạo nội dung cho: {agent.model_name} ---")
            
            # 3. Thực thi query
            result = await agent.answer_query(sample_trend_report)
            
            # 4. In kết quả ra console dưới dạng JSON đẹp mắt
            print("\n" + "="*50)
            print("KẾT QUẢ GENERATED CONTENT BUNDLE:")
            print("="*50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            with open(f"Generating_agent.json", "w", encoding = 'utf-8') as f:
                json.dumps(result, indent=4, ensure_ascii=False)
            
            # Kiểm tra nhanh các trường dữ liệu quan trọng
            if "error" not in result:
                print("\n[✓] Thành công: Cấu trúc JSON hợp lệ.")
                print(f"[i] Số lượng video sections: {len(result.get('video_script', {}).get('sections', []))}")
            else:
                print(f"\n[!] Có lỗi xảy ra: {result.get('message')}")
                
        except Exception as e:
            print(f"\n[X] Lỗi hệ thống khi chạy test: {e}")

    # Chạy hàm test
    asyncio.run(test_agent())
