from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schema.upload_post import (
    UploadPostAnalyticsEnvelope,
    UploadPostCommentsEnvelope,
    UploadPostCreateProfileRequest,
    UploadPostCurrentUserResponse,
    UploadPostDeleteProfileResponse,
    UploadPostGenerateJwtRequest,
    UploadPostGenerateJwtResponse,
    UploadPostHistoryEnvelope,
    UploadPostPostAnalyticsEnvelope,
    UploadPostProfileResponse,
    UploadPostProfilesResponse,
    UploadPostTotalImpressionsEnvelope,
    UploadPostValidateJwtRequest,
    UploadPostValidateJwtResponse,
)
from app.services.upload_post_service import UploadPostApiService
from app.services.upload_post_mock_service import UploadPostMockService

router = APIRouter(prefix="/api/v1/upload-post", tags=["upload-post"])
bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if not credentials:
        return None
    return credentials.credentials


@router.get("/account/me", response_model=UploadPostCurrentUserResponse)
async def get_upload_post_account():
    return UploadPostApiService().get_current_user()


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
    payload = UploadPostMockService().get_history(page=page, limit=limit)
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
):
    payload = UploadPostMockService().get_profile_analytics(
        profile_username=profile_username,
        platforms=_normalize_list_query(platforms),
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
):
    payload = UploadPostMockService().get_total_impressions(
        profile_username=profile_username,
        date_value=date,
        start_date=start_date,
        end_date=end_date,
        period=period,
        platforms=_normalize_list_query(platform) if platform else None,
        breakdown=breakdown,
        metrics=_normalize_list_query(metrics) if metrics else None,
    )
    return UploadPostTotalImpressionsEnvelope(profile_username=profile_username, payload=payload)


@router.get("/analytics/posts/{request_id}", response_model=UploadPostPostAnalyticsEnvelope)
async def get_upload_post_post_analytics(
    request_id: str,
    platform: str | None = None,
):
    payload = UploadPostMockService().get_post_analytics(
        request_id=request_id,
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
    payload = UploadPostMockService().get_comments(
        platform=platform,
        user=user,
        post_id=post_id,
        post_url=post_url,
    )
    return UploadPostCommentsEnvelope(payload=payload)


def _normalize_list_query(values: list[str] | None) -> list[str]:
    if not values:
        return []

    normalized: list[str] = []
    for value in values:
        normalized.extend(item.strip() for item in value.split(",") if item.strip())
    return normalized
