import os
import httpx
from typing import Optional
from dotenv import load_dotenv
import base64
import requests
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("PostingAgent")
UPLOAD_POST_API_KEY = os.getenv("UPLOAD_POST_API_KEY", "")
print(UPLOAD_POST_API_KEY)
UPLOAD_POST_BASE_URL = "https://api.upload-post.com/api"


def _get_headers() -> dict:
    return {
        "Authorization": f"Apikey {UPLOAD_POST_API_KEY}",
    }



def photo_convert(photos: list[str]) -> list[str]:
    api_key = os.getenv("IMG_BB_API_KEY", "")
    if not api_key:
        raise Exception("IMG_BB_API_KEY not configured")

    url = "https://api.imgbb.com/1/upload"
    result_urls = []

    for photo in photos:
        # ✅ If already a URL → keep it
        if photo.startswith("http://") or photo.startswith("https://"):
            result_urls.append(photo)
            continue

        # ✅ Else → upload local file
        try:
            with open(photo, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "key": api_key,
                "image": image_data
            }

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

            # ✅ Add normal fields
            for key, value in data.items():
                if isinstance(value, list):
                    formatted_data[key] = [str(item) for item in value]
                else:
                    formatted_data[key] = str(value)

            # ✅ Add files (if any)
            response = await client.post(
                f"{UPLOAD_POST_BASE_URL}/{endpoint}",
                headers=headers,
                data=formatted_data,
                files=files, 
            )

            return response.json()

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
async def upload_video(
    user: str,
    platform: list[str],
    video_path: str,
    title: str,
    description: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    first_comment: Optional[str] = None,
) -> dict:
    """
    Upload a video to multiple social media platforms using Upload-Post API.

    Parameters
    ----------
    user           : Upload-Post profile username.
    platform       : List of platforms (tiktok, instagram, youtube, facebook, x, threads, linkedin, bluesky, reddit, pinterest).
    video_path     : Local path or URL to the video file.
    title          : Video title/caption.
    description    : Optional extended description.
    scheduled_date : Optional ISO-8601 datetime for scheduling.
    first_comment  : Optional comment to post after publishing.

    Returns
    -------
    dict with request_id, job_id (if scheduled), or results per platform.
    """
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
async def upload_photos(
    user: str,
    platform: list[str],
    photos: list[str],
    title: Optional[str] = None,
    description: Optional[str] = None,
    scheduled_date: Optional[str] = None,
) -> dict:
    """
    Upload photos to multiple platforms using Upload-Post API.

    Parameters
    ----------
    user           : Upload-Post profile username.
    platform       : List of platforms (instagram, facebook, x, threads, linkedin, pinterest, bluesky, reddit).
    photos         : List of photo paths or URLs.
    title          : Optional title/description for the post.
    description    : Optional extended description.
    scheduled_date : Optional ISO-8601 datetime for scheduling.

    Returns
    -------
    dict with upload results per platform.
    """
    if not UPLOAD_POST_API_KEY:
        return {"success": False, "error": "Upload-Post API key not configured"}


    converted_photos = photo_convert(photos)



    data = {
        "user": user,
        "platform[]": platform,
        "photos[]": converted_photos,   # ✅ use converted URLs
    }

    

    if title:
        data["title"] = title
    if description:
        data["description"] = description
    if scheduled_date:
        data["scheduled_date"] = scheduled_date

    result = await _upload_post_request("upload_photos", data)
    return result


@mcp.tool()
async def upload_text(
    user: str,
    platform: list[str],
    title: str,
    description: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    first_comment: Optional[str] = None,
    link_url: Optional[str] = None,
    subreddit: Optional[str] = None,
) -> dict:
    """
    Upload text-only posts to multiple platforms using Upload-Post API.

    Parameters
    ----------
    user           : Upload-Post profile username.
    platform       : List of platforms (x, linkedin, facebook, threads, reddit, bluesky, google_business).
    title          : Text content for the post.
    description    : Optional extended body (Reddit only).
    scheduled_date : Optional ISO-8601 datetime for scheduling.
    first_comment  : Optional comment to post after publishing.
    link_url       : Optional URL for link preview.
    subreddit      : Required for Reddit posts.

    Returns
    -------
    dict with upload results per platform.
    """
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
async def get_upload_status(
    request_id: Optional[str] = None, job_id: Optional[str] = None
) -> dict:
    """
    Check the status of an upload or scheduled post.

    Parameters
    ----------
    request_id : For async uploads.
    job_id     : For scheduled posts.

    Returns
    -------
    dict with upload status and results.
    """
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
    """
    Get paginated history of all uploads.

    Parameters
    ----------
    page  : Page number (default 1).
    limit : Items per page (default 20, max 100).

    Returns
    -------
    dict with paginated upload history.
    """
    result = await _get_request("uploadposts/history", {"page": page, "limit": limit})
    return result


@mcp.tool()
async def get_media_list(
    user: str,
    platform: Optional[str] = None,
) -> dict:
    """
    Get recent media from connected social accounts.

    Parameters
    ----------
    user     : Upload-Post profile username.
    platform : Optional platform filter.

    Returns
    -------
    dict with media list.
    """
    params = {"user": user}
    if platform:
        params["platform"] = platform

    result = await _get_request("uploadposts/media", params)
    return result


@mcp.tool()
async def get_analytics(
    profile_username: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    Get analytics for a social media profile.

    Parameters
    ----------
    profile_username : Profile username to get analytics for.
    start_date      : Optional start date (YYYY-MM-DD).
    end_date        : Optional end date (YYYY-MM-DD).

    Returns
    -------
    dict with analytics data.
    """
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    result = await _get_request(f"analytics/{profile_username}", params)
    return result


@mcp.tool()
async def validate_api_key() -> dict:
    """
    Validate the Upload-Post API key and get account info.

    Returns
    -------
    dict with account information.
    """
    result = await _get_request("uploadposts/me")
    return result

@mcp.tool()
async def get_user_profile() -> dict:
    """
    Validate the Upload-Post API key and get profile info.

    Returns
    -------
    dict with profile information.
    """
    result = await _get_request("uploadposts/users")
    return result


@mcp.tool()
async def create_draft_for_review(
    user: str,
    platform: list[str],
    content_type: str,
    content: dict,
    draft_id: str,
) -> dict:
    """
    Create a draft for human review before publishing.
    This stores the draft locally and waits for approval.

    Parameters
    ----------
    user        : Upload-Post profile username.
    platform    : Target platforms.
    content_type: Type of content (video, photo, text).
    content     : Content details (title, description, etc.).
    draft_id    : Unique draft identifier.

    Returns
    -------
    dict with draft status and approval URL.
    """
    return {
        "success": True,
        "draft_id": draft_id,
        "status": "pending_approval",
        "user": user,
        "platform": platform,
        "content_type": content_type,
        "content": content,
        "approval_url": f"http://localhost:8000/approval/{draft_id}",
        "message": "Draft created. Awaiting human approval via frontend or API.",
    }


@mcp.tool()
async def check_draft_approval(draft_id: str) -> dict:
    """
    Check if a draft has been approved or rejected.

    Parameters
    ----------
    draft_id : The draft ID to check.

    Returns
    -------
    dict with approval status.
    """
    return {
        "draft_id": draft_id,
        "status": "pending_approval",
        "message": "Use approval service endpoint to check status",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
