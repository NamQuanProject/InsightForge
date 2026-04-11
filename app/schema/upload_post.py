from typing import Any

from pydantic import BaseModel, Field


class UploadPostProfile(BaseModel):
    username: str
    created_at: str | None = None
    social_accounts: dict[str, Any] = Field(default_factory=dict)


class UploadPostCurrentUserResponse(BaseModel):
    success: bool
    message: str | None = None
    email: str | None = None
    plan: str | None = None


class UploadPostCreateProfileRequest(BaseModel):
    username: str = Field(..., min_length=1)


class UploadPostProfileResponse(BaseModel):
    success: bool
    profile: UploadPostProfile


class UploadPostProfilesResponse(BaseModel):
    success: bool
    plan: str | None = None
    limit: int | None = None
    profiles: list[UploadPostProfile] = Field(default_factory=list)


class UploadPostDeleteProfileResponse(BaseModel):
    success: bool
    message: str | None = None


class UploadPostGenerateJwtRequest(BaseModel):
    username: str = Field(..., min_length=1)
    redirect_url: str | None = None
    logo_image: str | None = None
    redirect_button_text: str | None = None
    connect_title: str | None = None
    connect_description: str | None = None
    platforms: list[str] = Field(default_factory=list)
    show_calendar: bool | None = None
    readonly_calendar: bool | None = None


class UploadPostGenerateJwtResponse(BaseModel):
    success: bool
    access_url: str
    duration: str | None = None


class UploadPostValidateJwtRequest(BaseModel):
    jwt_token: str | None = Field(default=None, min_length=1)


class UploadPostValidateJwtResponse(BaseModel):
    success: bool | None = None
    isValid: bool | None = None
    reason: str | None = None
    profile: UploadPostProfile | None = None


class UploadPostAnalyticsEnvelope(BaseModel):
    source: str = "upload_post"
    profile_username: str
    payload: dict[str, Any]


class UploadPostTotalImpressionsEnvelope(BaseModel):
    source: str = "upload_post"
    profile_username: str
    payload: dict[str, Any]


class UploadPostPostAnalyticsEnvelope(BaseModel):
    source: str = "upload_post"
    request_id: str
    payload: dict[str, Any]


class UploadPostHistoryEnvelope(BaseModel):
    source: str = "upload_post"
    payload: dict[str, Any]


class UploadPostCommentsEnvelope(BaseModel):
    source: str = "upload_post"
    payload: dict[str, Any]
