from datetime import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    email: str = Field(..., min_length=3)
    name: str | None = None
    plan: str | None = None
    upload_post_account: dict[str, Any] = Field(default_factory=dict)
    profiles: list[dict[str, Any]] = Field(default_factory=list)
    social_accounts: dict[str, Any] = Field(default_factory=dict)
    connected_platforms: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str | None = None
    plan: str | None = None
    upload_post_account: dict[str, Any] = Field(default_factory=dict)
    profiles: list[dict[str, Any]] = Field(default_factory=list)
    social_accounts: dict[str, Any] = Field(default_factory=dict)
    connected_platforms: list[str] = Field(default_factory=list)
    created_at: datetime


class UserSummaryResponse(UserResponse):
    trend_analysis_count: int = 0
    generated_content_count: int = 0
    publish_job_count: int = 0


class UsersListResponse(BaseModel):
    users: list[UserSummaryResponse] = Field(default_factory=list)
