import os
import httpx
import logging
import uuid
from dotenv import load_dotenv
from typing import List
from mcp.server.fastmcp import FastMCP
from pathlib import Path

base_path = Path(__file__).parent.parent.parent
image_path = base_path / "images"
if not image_path.exists():
    image_path.mkdir(exist_ok=False)

# Load environment variables
load_dotenv()

# Cloudflare Configuration
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
# Using SDXL Base for high-quality generations
MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0" 

# Initialize FastMCP
mcp = FastMCP("ImageGenerating")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool: Generate Image via Cloudflare
# ---------------------------------------------------------------------------

# @mcp.tool()
# async def generate_image(
#     prompts: List[str],
#     output_path: List[str],
#     num_steps: int = 20,
#     guidance: float = 7.5
# ) -> dict:
#     """
#     Generate an image from a prompt using Cloudflare Workers AI (Stable Diffusion XL).

#     Args:
#         prompts: Details list of images description for each video script section.
#         output_path: List of local file path to save the resulting of each section image path.
#         num_steps: Number of inference steps (default 20).
#         guidance: How closely the model follows the prompt (default 7.5).

#     Returns:
#         dict: success status, saved_path, or error message.
#     """
#     if not ACCOUNT_ID or not API_TOKEN:
#         return {"success": False, "error": "Cloudflare credentials not set in environment."}

#     url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL}"
    
#     headers = {
#         "Authorization": f"Bearer {API_TOKEN}",
#         "Content-Type": "application/json",
#     }

#     payload_list = [{
#         "prompt": prompt,
#         "num_steps": num_steps,
#         "guidance": guidance
#     } for prompt in prompts]

#     try:
#         # Increase timeout for image generation
#         async with httpx.AsyncClient(timeout=120.0) as client:
#             logger.info(f"Requesting image generation from Cloudflare for prompts: {prompts}...")
            
#             for payload in payload_list:
#                 response = await client.post(url, headers=headers, json=payload)
                
#                 # Check for Cloudflare specific errors
#                 if response.status_code != 200:
#                     return {
#                         "success": False, 
#                         "error": f"Cloudflare API error {response.status_code}: {response.text}"
#                     }

#                 # Cloudflare returns raw binary data for images
#                 image_bytes = response.content

#                 # Save to disk
#                 with open(output_path, "wb") as f:
#                     f.write(image_bytes)

#                 logger.info(f"Image successfully saved to {output_path}")

#             return {
#                 "success": True,
#                 "saved_path": output_path,
#                 "model_used": MODEL,
#                 "error": None
#             }

#     except httpx.RequestError as e:
#         return {"success": False, "error": f"Network error: {str(e)}"}
#     except Exception as e:
#         return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool()
async def generate_images_batch(
    prompts: List[str],
    output_paths: List[str],
    num_steps: int = 20,
    guidance: float = 7.5
) -> dict:
    """
    Tạo hàng loạt hình ảnh từ danh sách prompts và lưu vào các đường dẫn tương ứng.

    Args:
        prompts: Danh sách các mô tả hình ảnh cho từng phần của video.
        output_paths: Danh sách các đường dẫn file cục bộ để lưu ảnh.
        num_steps: Số bước suy diễn (mặc định 20).
        guidance: Độ bám sát prompt (mặc định 7.5).

    Returns:
        dict: Trạng thái thành công, danh sách các đường dẫn đã lưu hoặc thông báo lỗi.
    """
    if not ACCOUNT_ID or not API_TOKEN:
        return {"success": False, "error": "Cloudflare credentials not set in environment."}

    if len(prompts) != len(output_paths):
        return {"success": False, "error": "Số lượng prompts và output_paths không khớp nhau."}

    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{MODEL}"
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    results = []
    success_count = 0

    try:
        # Sử dụng timeout lớn vì việc tạo nhiều ảnh sẽ mất thời gian
        async with httpx.AsyncClient(timeout=300.0) as client:
            for prompt, filename in zip(prompts, output_paths):
                payload = {
                    "prompt": prompt,
                    "num_steps": num_steps,
                    "guidance": guidance
                }
                
                logger.info(f"Đang tạo ảnh cho prompt: {prompt[:50]}...")
                response = await client.post(url, headers=headers, json=payload)
                image_path_section = image_path / filename
                
                if response.status_code == 200:
                    # Ghi dữ liệu binary vào file
                    with open(image_path_section, "wb") as f:
                        f.write(response.content)
                    
                    results.append({"path": str(image_path_section), "status": "success"})
                    success_count += 1
                else:
                    error_msg = f"Cloudflare API error {response.status_code}: {response.text}"
                    results.append({"path": filename, "status": "failed", "error": error_msg})

            return {
                "success": success_count > 0,
                "total_requested": len(prompts),
                "total_saved": success_count,
                "details": results,
                "base_directory": str(image_path)
            }

    except httpx.RequestError as e:
        return {"success": False, "error": f"Lỗi mạng: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Lỗi không xác định: {str(e)}"}


BASE_URL = os.getenv("INSIGHTFORGE_API_BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_USER_ID = os.getenv(
    "INSIGHTFORGE_DEFAULT_USER_ID",
    "cd129113-895c-4800-b4e4-48d63bf46d12",
)


def _is_valid_user_id(user_id: str) -> bool:
    try:
        uuid.UUID(str(user_id))
        return True
    except (TypeError, ValueError):
        return False


def _resolve_user_id(user_id: str) -> str | None:
    if _is_valid_user_id(user_id):
        return str(user_id)
    if _is_valid_user_id(DEFAULT_USER_ID):
        return DEFAULT_USER_ID
    return None


@mcp.tool()
async def get_latest_generated_content(user_id: str) -> dict:
    """
    Fetches the most recent generated content for a given user.
    Returns the latest content item if it exists, or an empty result if none found.
    Used to personalize content generation based on the user's history.

    Args:
        user_id: The UUID string of the user whose content history to fetch.
    """
    resolved_user_id = _resolve_user_id(user_id)
    if resolved_user_id is None:
        return {"has_history": False, "latest_content": None}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/contents",
            params={"user_id": resolved_user_id, "limit": 1},
        )
        response.raise_for_status()
        data = response.json()

    items = data.get("items", [])
    if not items:
        return {"has_history": False, "latest_content": None}

    return {"has_history": True, "latest_content": items[0]}


if __name__ == "__main__":
    mcp.run(transport = "stdio")
