import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schema.upload_post import (
    PublishJobResponse,
    PublishJobsListResponse,
    UploadPostAnalyticsEnvelope,
    UploadPostCommentsEnvelope,
    UploadPostCreateProfileRequest,
    UploadPostCurrentUserResponse,
    UploadPostDeleteProfileResponse,
    UploadPostGenerateJwtRequest,
    UploadPostGenerateJwtResponse,
    UploadPostHistoryEnvelope,
    UploadPostPostAnalyticsEnvelope,
    UploadPostPublishResponse,
    UploadPostProfileResponse,
    UploadPostProfilesResponse,
    UploadPostTotalImpressionsEnvelope,
    UploadPostValidateJwtRequest,
    UploadPostValidateJwtResponse,
)
from app.services.posting_service import PostingService
from app.services.postgres_service import PostgresService
from app.services.upload_post_service import UploadPostApiService

router = APIRouter(prefix="/api/v1/upload-post", tags=["upload-post"])
bearer_scheme = HTTPBearer(auto_error=False)




def _extract_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if not credentials:
        return None
    return credentials.credentials


@router.get("/account/me", response_model=UploadPostCurrentUserResponse)
async def get_upload_post_account():
    upload_post_service = UploadPostApiService()
    bundle = upload_post_service.get_account_bundle()
    account = bundle["account"]
    email = account.get("email")
    if not email:
        raise HTTPException(status_code=502, detail="Upload-Post account response did not include an email.")

    app_user = await PostgresService().upsert_user(
        email=str(email),
        name=upload_post_service.get_configured_profile_username(),
        plan=account.get("plan"),
        upload_post_account=account,
        profiles=bundle["profiles"],
        social_accounts=bundle["social_accounts"],
        connected_platforms=bundle["connected_platforms"],
    )
    return {
        **account,
        "profiles": bundle["profiles"],
        "social_accounts": bundle["social_accounts"],
        "connected_platforms": bundle["connected_platforms"],
        "app_user": app_user,
    }


@router.post("/users", response_model=UploadPostProfileResponse)
async def create_upload_post_profile(payload: UploadPostCreateProfileRequest):
    return UploadPostApiService().create_profile(payload)


@router.get("/users", response_model=UploadPostProfilesResponse)
async def get_upload_post_profiles():
    return UploadPostApiService().get_profiles()


@router.get("/history", response_model=UploadPostHistoryEnvelope)
async def get_upload_post_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    payload = UploadPostApiService().get_history(page=page, limit=limit)
    return UploadPostHistoryEnvelope(payload=payload)


@router.get("/users/{username}", response_model=UploadPostProfileResponse)
async def get_upload_post_profile(username: str):
    return UploadPostApiService().get_profile(username)


@router.delete("/users/{username}", response_model=UploadPostDeleteProfileResponse)
async def delete_upload_post_profile(username: str):
    return UploadPostApiService().delete_profile(username)


@router.post("/jwt/generate", response_model=UploadPostGenerateJwtResponse)
async def generate_upload_post_jwt(payload: UploadPostGenerateJwtRequest):
    return UploadPostApiService().generate_jwt(payload)


@router.post("/publish", response_model=UploadPostPublishResponse)
async def publish_upload_post_content(
    user: str | None = Form(default=None),
    platforms: str = Form(..., description="Comma-separated platform list, e.g. youtube,tiktok"),
    title: str = Form(..., min_length=1),
    description: str | None = Form(default=None),
    tags: str | None = Form(default=None, description="Comma-separated tags, e.g. demo,test"),
    first_comment: str | None = Form(default=None),
    schedule_post: str | None = Form(default=None),
    link_url: str | None = Form(default=None),
    subreddit: str | None = Form(default=None),
    asset_urls: str | None = Form(default=None, description="Comma-separated public asset URLs."),
    files: list[UploadFile] = File(default_factory=list),
    user_id: uuid.UUID | None = Form(default=None),
    generated_content_id: uuid.UUID | None = Form(default=None),
):
    normalized_platforms = _normalize_csv_field(platforms)
    publish_job, provider_payload = await PostingService().publish(
        profile_username=user,
        platforms=normalized_platforms,
        title=title,
        description=description,
        tags=_normalize_csv_field(tags) if tags else [],
        schedule_post=schedule_post,
        first_comment=first_comment,
        link_url=link_url,
        subreddit=subreddit,
        asset_urls=_normalize_csv_field(asset_urls) if asset_urls else [],
        files=files,
        user_id=user_id,
        generated_content_id=generated_content_id,
    )
    return UploadPostPublishResponse(publish_job=publish_job, provider_payload=provider_payload)


@router.get("/publish-jobs", response_model=PublishJobsListResponse)
async def list_publish_jobs(
    user_id: uuid.UUID | None = Query(default=None),
    generated_content_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    items = await PostingService().list_publish_jobs(
        user_id=user_id,
        generated_content_id=generated_content_id,
        limit=limit,
    )
    return PublishJobsListResponse(items=items)


@router.get("/publish-jobs/{publish_job_id}", response_model=PublishJobResponse)
async def get_publish_job(publish_job_id: uuid.UUID):
    item = await PostingService().get_publish_job(publish_job_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Publish job not found: {publish_job_id}")
    return item


@router.post("/jwt/validate", response_model=UploadPostValidateJwtResponse)
async def validate_upload_post_jwt(
    payload: UploadPostValidateJwtRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    token = payload.jwt_token or _extract_token(credentials)
    return UploadPostApiService().validate_jwt(token or "")


@router.get("/analytics/profiles/{profile_username}", response_model=UploadPostAnalyticsEnvelope)
async def get_upload_post_profile_analytics(
    profile_username: str,
    platforms: list[str] = Query(
        ...,
        description="Repeat the query key or pass a comma-separated value, e.g. platforms=instagram&platforms=youtube.",
    ),
    page_id: str | None = None,
    page_urn: str | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    payload = UploadPostApiService().get_profile_analytics(
        profile_username=profile_username,
        platforms=_normalize_list_query(platforms),
        jwt_token=_extract_token(credentials),
        page_id=page_id,
        page_urn=page_urn,
    )
    return UploadPostAnalyticsEnvelope(profile_username=profile_username, payload=payload)


@router.get(
    "/analytics/profiles/{profile_username}/total-impressions",
    response_model=UploadPostTotalImpressionsEnvelope,
)
async def get_upload_post_total_impressions(
    profile_username: str,
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    period: str | None = None,
    platform: list[str] | None = Query(default=None),
    breakdown: bool = False,
    metrics: list[str] | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    payload = UploadPostApiService().get_total_impressions(
        profile_username=profile_username,
        jwt_token=_extract_token(credentials),
        date=date,
        start_date=start_date,
        end_date=end_date,
        period=period,
        platform=_normalize_list_query(platform) if platform else None,
        breakdown=breakdown,
        metrics=_normalize_list_query(metrics) if metrics else None,
    )
    return UploadPostTotalImpressionsEnvelope(profile_username=profile_username, payload=payload)


@router.get("/analytics/posts/{request_id}", response_model=UploadPostPostAnalyticsEnvelope)
async def get_upload_post_post_analytics(
    request_id: str,
    platform: str | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    payload = UploadPostApiService().get_post_analytics(
        request_id=request_id,
        jwt_token=_extract_token(credentials),
        platform=platform,
    )
    return UploadPostPostAnalyticsEnvelope(request_id=request_id, payload=payload)


@router.get("/interactions/comments", response_model=UploadPostCommentsEnvelope)
async def get_upload_post_comments(
    platform: str = Query(..., min_length=1),
    user: str = Query(..., min_length=1),
    post_id: str | None = None,
    post_url: str | None = None,
):
    payload = UploadPostApiService().get_comments(
        platform=platform,
        user=user,
        post_id=post_id,
        post_url=post_url,
    )
    return UploadPostCommentsEnvelope(payload=payload)


@router.get("/interactions/comments/all", response_model=UploadPostCommentsEnvelope)
async def get_all_upload_post_comments(
    platform: str = Query(default="instagram", min_length=1),
    user: str = Query(..., min_length=1),
    max_media: int = Query(default=20, ge=1, le=100),
    continue_on_error: bool = Query(default=True),
):
    payload = UploadPostApiService().get_all_comments(
        platform=platform,
        user=user,
        max_media=max_media,
        continue_on_error=continue_on_error,
    )
    return UploadPostCommentsEnvelope(payload=payload)


@router.delete("/interactions/comments/bad-words", response_model=UploadPostCommentsEnvelope)
async def delete_upload_post_bad_word_comments(
    platform: str = Query(default="instagram", min_length=1),
    user: str = Query(..., min_length=1),
    post_id: str | None = Query(default=None),
    post_url: str | None = Query(default=None),
    max_media: int = Query(default=20, ge=1, le=100),
    dry_run: bool = Query(default=False),
):
    payload = UploadPostApiService().delete_bad_word_comments(
        platform=platform,
        user=user,
        post_id=post_id,
        post_url=post_url,
        max_media=max_media,
        dry_run=dry_run,
    )
    return UploadPostCommentsEnvelope(payload=payload)


def _normalize_list_query(values: list[str] | None) -> list[str]:
    if not values:
        return []

    normalized: list[str] = []
    for value in values:
        normalized.extend(item.strip() for item in value.split(",") if item.strip())
    return normalized


def _normalize_csv_field(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
