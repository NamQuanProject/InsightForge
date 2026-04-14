import os
import httpx
from typing import List, Optional
from dotenv import load_dotenv
import base64
import requests
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("PostingAgent")
UPLOAD_POST_API_KEY = os.getenv("UPLOAD_POST_API_KEY", "")
# print(UPLOAD_POST_API_KEY)
UPLOAD_POST_BASE_URL = "https://api.upload-post.com/api"


def _get_headers() -> dict:
    return {"Authorization": f"Apikey {UPLOAD_POST_API_KEY}"}


def photo_convert(photos: list[str]) -> list[str]:
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
            with open(photo, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            payload = {"key": api_key, "image": image_data}
            response = requests.post(url, data=payload)
            result = response.json()

            if result.get("success"):
                result_urls.append(result["data"]["url"])
            else:
                raise Exception(f"Upload failed: {result}")

        except Exception as e:
            raise Exception(f"Error processing {photo}: {str(e)}")

    return result_urls


async def _upload_post_request(endpoint: str, data: dict, files: dict = None) -> dict:
    headers = _get_headers()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            formatted_data = {}

            for key, value in data.items():
                if isinstance(value, list):
                    formatted_data[key] = [str(item) for item in value]
                else:
                    formatted_data[key] = str(value)

            response = await client.post(
                f"{UPLOAD_POST_BASE_URL}/{endpoint}",
                headers=headers,
                data=formatted_data,
                files=files,
            )

            return response.json()

        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def _get_request(endpoint: str, params: dict = None) -> dict:
    headers = _get_headers()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(
                f"{UPLOAD_POST_BASE_URL}/{endpoint}",
                headers=headers,
                params=params,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}


@mcp.tool()
async def upload_text(
    user: str,
    platform: List[str],
    title: str,
    description: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    first_comment: Optional[str] = None,
    link_url: Optional[str] = None,
    subreddit: Optional[str] = None,
) -> dict:
    """Upload text posts to platforms."""
    if not UPLOAD_POST_API_KEY:
        return {"success": False, "error": "Upload-Post API key not configured"}

    data = {
        "user": user,
        "platform[]": platform,
        "title": title,
    }

    if description:
        data["description"] = description
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
    if first_comment:
        data["first_comment"] = first_comment
    if link_url:
        data["link_url"] = link_url
    if subreddit:
        data["subreddit"] = subreddit

    result = await _upload_post_request("upload_text", data)
    return result


@mcp.tool()
async def upload_photos(
    user: str,
    platform: List[str],
    photos: List[str],
    title: Optional[str] = None,
    description: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    facebook_page_id: Optional[str] = None,
) -> dict:
    """Upload photos to platforms."""
    if not UPLOAD_POST_API_KEY:
        return {"success": False, "error": "Upload-Post API key not configured"}

    converted_photos = photo_convert(photos)

    data = {
        "user": user,
        "platform[]": platform,
        "photos[]": converted_photos,
    }

    if title:
        data["title"] = title
    if facebook_page_id:
        data["facebook_page_id"] = facebook_page_id
    if description:
        data["description"] = description
    if scheduled_date:
        data["scheduled_date"] = scheduled_date

    result = await _upload_post_request("upload_photos", data)
    return result


@mcp.tool()
async def upload_video(
    user: str,
    platform: List[str],
    video_path: str,
    title: str,
    description: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    first_comment: Optional[str] = None,
) -> dict:
    """Upload video to platforms."""
    if not UPLOAD_POST_API_KEY:
        return {"success": False, "error": "Upload-Post API key not configured"}

    data = {
        "user": user,
        "platform[]": platform,
        "title": title,
    }

    if description:
        data["description"] = description
    if scheduled_date:
        data["scheduled_date"] = scheduled_date
    if first_comment:
        data["first_comment"] = first_comment

    if video_path.startswith("http"):
        data["video"] = video_path

    result = await _upload_post_request("upload", data)
    return result


@mcp.tool()
async def get_upload_status(
    request_id: Optional[str] = None, job_id: Optional[str] = None
) -> dict:
    """Check upload status."""
    if not request_id and not job_id:
        return {"success": False, "error": "Either request_id or job_id is required"}

    params = {}
    if request_id:
        params["request_id"] = request_id
    if job_id:
        params["job_id"] = job_id

    result = await _get_request("uploadposts/status", params)
    return result


@mcp.tool()
async def get_upload_history(
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Get upload history."""
    result = await _get_request("uploadposts/history", {"page": page, "limit": limit})
    return result


@mcp.tool()
async def get_media_list(
    user: str,
    platform: Optional[str] = None,
) -> dict:
    """Get media list."""
    params = {"user": user}
    if platform:
        params["platform"] = platform

    result = await _get_request("uploadposts/media", params)
    return result


@mcp.tool()
async def get_analytics(
    profile_username: str,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Get analytics."""
    params = {}
    if platform:
        params["platforms"] = platform
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    result = await _get_request(f"analytics/{profile_username}", params)
    return result


@mcp.tool()
async def validate_api_key() -> dict:
    """Validate API key."""
    result = await _get_request("uploadposts/me")
    return result


@mcp.tool()
async def get_user_profile() -> dict:
    """Get user profile."""
    result = await _get_request("uploadposts/users")
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
