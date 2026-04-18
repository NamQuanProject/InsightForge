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


def _clamp_history_limit(limit: int | None) -> int:
    try:
        parsed = int(limit or 10)
    except (TypeError, ValueError):
        parsed = 10
    return max(1, min(parsed, 10))


def _compact_generated_content(item: dict, position: int) -> dict:
    post_content = item.get("post_content") if isinstance(item.get("post_content"), dict) else {}
    platform_posts = item.get("platform_posts") if isinstance(item.get("platform_posts"), dict) else {}
    image_set = item.get("image_set") if isinstance(item.get("image_set"), list) else []

    return {
        "position": position,
        "id": item.get("id"),
        "created_at": item.get("created_at"),
        "selected_keyword": item.get("selected_keyword") or "",
        "main_title": item.get("main_title") or post_content.get("title") or "",
        "post_title": post_content.get("title") or "",
        "hook": post_content.get("hook") or "",
        "description": post_content.get("description") or "",
        "call_to_action": post_content.get("call_to_action") or "",
        "hashtags": post_content.get("hashtags") if isinstance(post_content.get("hashtags"), list) else [],
        "platform_captions": {
            platform: post.get("caption") or ""
            for platform, post in platform_posts.items()
            if isinstance(post, dict)
        },
        "image_titles": [
            image.get("title") or ""
            for image in image_set
            if isinstance(image, dict)
        ],
    }


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


@mcp.tool()
async def get_recent_generated_contents(user_id: str, limit: int = 10) -> dict:
    """
    Fetches recent generated content for a user so the content agent can avoid
    repeating old ideas, keywords, hooks, and image sequences.

    The first 1-3 items are the recent-series window: the agent may continue a
    topic if it uses a fresh angle. Items 5-10 are the cooldown window: avoid
    repeating their keywords, titles, hooks, and core content angles.

    Args:
        user_id: The UUID string of the user whose content history to fetch.
        limit: Number of recent items to fetch. Clamped to 1-10.
    """
    resolved_user_id = _resolve_user_id(user_id)
    safe_limit = _clamp_history_limit(limit)
    if resolved_user_id is None:
        return {
            "has_history": False,
            "user_id": None,
            "limit": safe_limit,
            "recent_contents": [],
            "series_window": [],
            "avoid_window": [],
        }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/contents",
            params={"user_id": resolved_user_id, "limit": safe_limit},
        )
        response.raise_for_status()
        data = response.json()

    items = data.get("items", [])
    if not isinstance(items, list):
        items = []

    compact_items = [
        _compact_generated_content(item, index + 1)
        for index, item in enumerate(items)
        if isinstance(item, dict)
    ]

    return {
        "has_history": bool(compact_items),
        "user_id": resolved_user_id,
        "limit": safe_limit,
        "recent_contents": compact_items,
        "series_window": compact_items[:3],
        "avoid_window": compact_items[4:10],
        "guidance": (
            "May reuse a broad topic in positions 1-3 only as a short series "
            "with a fresh angle. Avoid repeating keywords, titles, hooks, CTAs, "
            "and core ideas from positions 5-10."
        ),
    }


@mcp.tool()
async def get_user_profile(user_id: str) -> dict:
    """
    Fetches the user profile used to personalize generated content.

    Args:
        user_id: The UUID string of the user. Invalid placeholders fall back to
            INSIGHTFORGE_DEFAULT_USER_ID when configured.
    """
    resolved_user_id = _resolve_user_id(user_id)
    if resolved_user_id is None:
        return {
            "has_profile": False,
            "user_id": None,
            "user_profile": None,
            "error": "No valid user id or INSIGHTFORGE_DEFAULT_USER_ID configured.",
        }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/users/{resolved_user_id}")

    if response.status_code == 404:
        return {
            "has_profile": False,
            "user_id": resolved_user_id,
            "user_profile": None,
            "error": "User profile not found.",
        }

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {
            "has_profile": False,
            "user_id": resolved_user_id,
            "user_profile": None,
            "error": str(exc),
        }

    return {
        "has_profile": True,
        "user_id": resolved_user_id,
        "user_profile": response.json(),
    }


if __name__ == "__main__":
    mcp.run(transport = "stdio")
