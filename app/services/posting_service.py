import uuid
from typing import Any

from fastapi import UploadFile

from app.schema.upload_post import PublishJobResponse
from app.services.postgres_service import PostgresService
from app.services.upload_post_publish_service import UploadPostPublishService


class PostingService:
    def __init__(self) -> None:
        self.publish_provider = UploadPostPublishService()
        self.postgres = PostgresService()

    async def publish(
        self,
        profile_username: str,
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
        user_id: uuid.UUID | None = None,
        generated_content_id: uuid.UUID | None = None,
    ) -> tuple[PublishJobResponse, dict[str, Any]]:
        provider_payload = await self.publish_provider.publish(
            user=profile_username,
            platforms=platforms,
            title=title,
            description=description,
            tags=tags,
            schedule_post=schedule_post,
            first_comment=first_comment,
            link_url=link_url,
            subreddit=subreddit,
            asset_urls=asset_urls,
            files=files,
        )
        uploaded_files = [
            {
                "filename": upload.filename or "",
                "content_type": upload.content_type or "application/octet-stream",
            }
            for upload in (files or [])
            if upload.filename
        ]
        record = await self.postgres.save_publish_job(
            profile_username=profile_username,
            platforms=provider_payload.get("platforms", platforms),
            title=title,
            provider_response=provider_payload,
            user_id=user_id,
            generated_content_id=generated_content_id,
            description=description,
            tags=tags or [],
            first_comment=first_comment,
            schedule_post=schedule_post,
            link_url=link_url,
            subreddit=subreddit,
            asset_urls=asset_urls or [],
            uploaded_files=uploaded_files,
            post_kind=provider_payload.get("post_kind", "text"),
            status=self._resolve_status(provider_payload),
        )
        return self._to_response(record), provider_payload

    async def list_publish_jobs(
        self,
        user_id: uuid.UUID | None = None,
        generated_content_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[PublishJobResponse]:
        records = await self.postgres.list_publish_jobs(
            user_id=user_id,
            generated_content_id=generated_content_id,
            limit=limit,
        )
        return [self._to_response(record) for record in records]

    async def get_publish_job(self, publish_job_id: uuid.UUID) -> PublishJobResponse | None:
        record = await self.postgres.get_publish_job(publish_job_id)
        if record is None:
            return None
        return self._to_response(record)

    def _resolve_status(self, payload: dict[str, Any]) -> str:
        provider_inner = payload.get("payload", {}) if isinstance(payload, dict) else {}
        if provider_inner.get("success") is True:
            return "submitted"
        if payload.get("success") is True:
            return "submitted"
        return "failed"

    def _to_response(self, record) -> PublishJobResponse:
        return PublishJobResponse(
            id=record.id,
            user_id=record.user_id,
            generated_content_id=record.generated_content_id,
            profile_username=record.profile_username,
            platforms=record.platforms or [],
            title=record.title,
            description=record.description,
            tags=record.tags or [],
            first_comment=record.first_comment,
            schedule_post=record.schedule_post,
            link_url=record.link_url,
            subreddit=record.subreddit,
            asset_urls=record.asset_urls or [],
            uploaded_files=record.uploaded_files or [],
            post_kind=record.post_kind,
            provider_request_id=record.provider_request_id,
            provider_job_id=record.provider_job_id,
            provider_response=record.provider_response or {},
            status=record.status,
            created_at=record.created_at,
        )
