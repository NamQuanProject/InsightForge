import asyncio
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile

# no files + no asset_urls -> text post
# one video file or one video URL -> video post
# one or more image files or image URLs -> photo post
# mixed image + video in one request -> rejected


class UploadPostPublishService:
    SUPPORTED_PLATFORMS = {
        "tiktok",
        "instagram",
        "youtube",
        "facebook",
        "x",
        "threads",
        "linkedin",
        "bluesky",
        "reddit",
        "pinterest",
        "google_business",
    }

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    def __init__(self) -> None:
        load_dotenv()
        self.base_url = os.getenv("UPLOAD_POST_BASE_URL", "https://api.upload-post.com/api").rstrip("/")
        self.timeout = float(os.getenv("UPLOAD_POST_TIMEOUT_SECONDS", "120"))

    async def publish(
        self,
        user: str,
        platforms: list[str],
        title: str,
        description: str | None = None,
        tags: list[str] | None = None,
        schedule_post: str | None = None,
        first_comment: str | None = None,
        link_url: str | None = None,
        subreddit: str | None = None,
        asset_urls: list[str] | None = None,
        files: list[UploadFile] | None = None,
    ) -> dict[str, Any]:
        api_key = os.getenv("UPLOAD_POST_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing UPLOAD_POST_API_KEY in the backend environment.")

        normalized_platforms = self._normalize_platforms(platforms)
        normalized_asset_urls = [url.strip() for url in (asset_urls or []) if url and url.strip()]
        uploaded_files = [file for file in (files or []) if file.filename]

        post_kind = self._infer_post_kind(uploaded_files, normalized_asset_urls)
        data: dict[str, Any] = {
            "user": user,
            "platform[]": normalized_platforms,
            "title": title,
        }
        if description:
            data["description"] = description
        if tags:
            data["tags[]"] = [tag for tag in tags if tag]
        if schedule_post:
            data["scheduled_date"] = schedule_post
        if first_comment and post_kind in {"video", "text"}:
            data["first_comment"] = first_comment
        if link_url and post_kind == "text":
            data["link_url"] = link_url
        if subreddit and post_kind == "text":
            data["subreddit"] = subreddit

        endpoint = self._endpoint_for_kind(post_kind)
        request_files: list[tuple[str, bytes, str]] = []

        if post_kind == "video":
            if normalized_asset_urls:
                data["video"] = normalized_asset_urls[0]
            elif uploaded_files:
                upload = uploaded_files[0]
                request_files.append(
                    (
                        upload.filename or "video.bin",
                        await upload.read(),
                        upload.content_type or "application/octet-stream",
                    )
                )
        elif post_kind == "photos":
            for url in normalized_asset_urls:
                data.setdefault("photos[]", []).append(url)
            for upload in uploaded_files:
                request_files.append(
                    (
                        upload.filename or "photo.bin",
                        await upload.read(),
                        upload.content_type or "application/octet-stream",
                    )
                )

        payload = await self._upload_post_request(api_key=api_key, endpoint=endpoint, data=data, files=request_files)
        return {
            "success": True,
            "post_kind": post_kind,
            "platforms": normalized_platforms,
            "payload": payload,
        }

    def _normalize_platforms(self, platforms: list[str]) -> list[str]:
        normalized: list[str] = []
        for raw in platforms:
            for item in raw.split(","):
                platform = item.strip().lower()
                if not platform:
                    continue
                if platform not in self.SUPPORTED_PLATFORMS:
                    raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
                normalized.append(platform)

        if not normalized:
            raise HTTPException(status_code=400, detail="At least one platform is required.")
        return normalized

    def _infer_post_kind(self, files: list[UploadFile], asset_urls: list[str]) -> str:
        if not files and not asset_urls:
            return "text"

        asset_types = []
        for upload in files:
            asset_types.append(self._detect_asset_type(upload.filename or "", upload.content_type))
        for url in asset_urls:
            asset_types.append(self._detect_asset_type(url, None))

        if any(asset_type == "unknown" for asset_type in asset_types):
            raise HTTPException(status_code=400, detail="Unsupported file type. Use a video, image, or text-only post.")

        if all(asset_type == "video" for asset_type in asset_types):
            if len(asset_types) > 1:
                raise HTTPException(status_code=400, detail="Upload-Post video publishing supports only one video per request.")
            return "video"

        if all(asset_type == "image" for asset_type in asset_types):
            return "photos"

        raise HTTPException(
            status_code=400,
            detail="Do not mix video and image assets in one publish request.",
        )

    def _detect_asset_type(self, name_or_url: str, content_type: str | None) -> str:
        normalized_content_type = (content_type or "").lower()
        if normalized_content_type.startswith("video/"):
            return "video"
        if normalized_content_type.startswith("image/"):
            return "image"

        suffix = Path(name_or_url.split("?")[0]).suffix.lower()
        if suffix in self.VIDEO_EXTENSIONS:
            return "video"
        if suffix in self.IMAGE_EXTENSIONS:
            return "image"
        return "unknown"

    def _endpoint_for_kind(self, post_kind: str) -> str:
        mapping = {
            "video": "upload",
            "photos": "upload_photos",
            "text": "upload_text",
        }
        return mapping[post_kind]

    async def _upload_post_request(
        self,
        api_key: str,
        endpoint: str,
        data: dict[str, Any],
        files: list[tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(self._upload_post_request_sync, api_key, endpoint, data, files)

    def _upload_post_request_sync(
        self,
        api_key: str,
        endpoint: str,
        data: dict[str, Any],
        files: list[tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Apikey {api_key}"}
        formatted_data: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, list):
                formatted_data[key] = [str(item) for item in value]
            else:
                formatted_data[key] = str(value)

        request_files = None
        if files:
            if endpoint == "upload":
                filename, content, content_type = files[0]
                request_files = {
                    "video": (filename, content, content_type),
                }
            elif endpoint == "upload_photos":
                request_files = [
                    ("photos[]", (filename, content, content_type))
                    for filename, content, content_type in files
                ]

        try:
            with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                response = client.post(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    data=formatted_data,
                    files=request_files,
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Upload-Post request timed out.") from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Upload-Post request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            raise HTTPException(status_code=502, detail=f"Upload-Post returned a non-JSON response: {response.text}")

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=payload)
        return payload
