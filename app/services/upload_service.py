import importlib
import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import HTTPException

from app.schema.common import UploadVideoRequest, UploadVideoResponse


class UploadService:
    def __init__(self) -> None:
        load_dotenv()

    def upload(self, platform: str, payload: UploadVideoRequest) -> UploadVideoResponse:
        self._validate_platform(platform)
        self._validate_file_path(payload.file_path)

        module = self._resolve_module()
        if module is None:
            raise HTTPException(
                status_code=500,
                detail="The upload_post package is not available in the active Python environment.",
            )

        api_key = os.getenv("UPLOAD_POST_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Missing UPLOAD_POST_API_KEY in the backend environment.",
            )

        user = payload.user or os.getenv(f"UPLOAD_POST_{platform.upper()}_USER") or os.getenv("UPLOAD_POST_DEFAULT_USER")
        if not user:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Missing upload-post profile for {platform}. "
                    f"Provide 'user' in the request body or set UPLOAD_POST_{platform.upper()}_USER."
                ),
            )

        client = module.UploadPostClient(api_key)
        upload_kwargs = self._build_upload_kwargs(platform=platform, payload=payload)

        try:
            response = client.upload_video(
                video_path=payload.file_path,
                title=payload.title,
                user=user,
                platforms=[platform],
                **upload_kwargs,
            )
        except module.UploadPostError as exc:
            raise HTTPException(status_code=502, detail=f"upload_post failed: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Unexpected upload failure: {exc}") from exc

        file_name = Path(urlparse(payload.file_path).path).name or Path(payload.file_path).name
        reference = (
            response.get("request_id")
            or response.get("job_id")
            or response.get("upload_id")
            or response.get("id")
            or f"{platform[:2]}_{uuid.uuid4().hex[:10]}"
        )
        message = (
            response.get("message")
            or response.get("detail")
            or f"Upload request submitted to {platform} via upload_post."
        )
        preview_url = response.get("preview_url") or response.get("url") or f"https://mock.{platform}.local/upload/{file_name}"
        status = response.get("status") or ("scheduled" if response.get("job_id") else "submitted")

        return UploadVideoResponse(
            status=status,
            platform=platform,
            upload_mode=f"package:{module.__name__}",
            message=message,
            external_post_id=str(reference),
            preview_url=preview_url,
        )

    def _resolve_module(self):
        try:
            return importlib.import_module("upload_post")
        except Exception:
            return None

    def _validate_platform(self, platform: str) -> None:
        if platform not in {"tiktok", "youtube"}:
            raise HTTPException(status_code=400, detail=f"Unsupported upload platform: {platform}")

    def _validate_file_path(self, file_path: str) -> None:
        parsed = urlparse(file_path)
        if parsed.scheme in {"http", "https"}:
            return

        if not Path(file_path).exists():
            raise HTTPException(status_code=400, detail=f"Video file not found: {file_path}")

    def _build_upload_kwargs(self, platform: str, payload: UploadVideoRequest) -> dict:
        kwargs: dict = {
            "description": payload.description or None,
            "scheduled_date": payload.schedule_at,
            "async_upload": payload.async_upload,
        }

        if platform == "tiktok":
            kwargs.update(
                {
                    "privacy_level": self._map_tiktok_visibility(payload.visibility),
                    "disable_comment": payload.disable_comment,
                    "disable_duet": payload.disable_duet,
                    "disable_stitch": payload.disable_stitch,
                    "is_aigc": payload.is_aigc,
                    "cover_timestamp": payload.cover_timestamp,
                }
            )
        elif platform == "youtube":
            kwargs.update(
                {
                    "tags": payload.tags,
                    "categoryId": payload.category_id or "22",
                    "privacyStatus": self._map_youtube_visibility(payload.visibility),
                    "thumbnail_url": payload.thumbnail_url,
                }
            )

        return {key: value for key, value in kwargs.items() if value is not None}

    def _map_tiktok_visibility(self, visibility: str) -> str:
        normalized = visibility.strip().lower()
        mapping = {
            "public": "PUBLIC_TO_EVERYONE",
            "friends": "MUTUAL_FOLLOW_FRIENDS",
            "followers": "FOLLOWER_OF_CREATOR",
            "private": "SELF_ONLY",
            "self_only": "SELF_ONLY",
        }
        if normalized not in mapping:
            raise HTTPException(
                status_code=400,
                detail="Invalid TikTok visibility. Use one of: public, friends, followers, private.",
            )
        return mapping[normalized]

    def _map_youtube_visibility(self, visibility: str) -> str:
        normalized = visibility.strip().lower()
        mapping = {
            "public": "public",
            "private": "private",
            "unlisted": "unlisted",
        }
        if normalized not in mapping:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube visibility. Use one of: public, unlisted, private.",
            )
        return mapping[normalized]
