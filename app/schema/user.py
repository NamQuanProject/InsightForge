from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserContentPreferences(BaseModel):
    content_groups: list[str] = Field(default_factory=list)
    priority_formats: list[str] = Field(default_factory=list)
    keyword_hashtags: list[str] = Field(default_factory=list)
    audience_persona: str = ""
    focus_content_goal: str = ""


class UserOptions(BaseModel):
    timezone: str = "Asia/Saigon"
    linked_platforms: list[str] = Field(default_factory=list)
    default_visibility: str = "public"
    default_post_times: dict[str, str] = Field(default_factory=dict)
    weekly_content_frequency: int = 0


class UserCreateRequest(BaseModel):
    email: str = Field(..., min_length=3)
    display_name: str | None = None
    phone_number: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    about_me: str | None = None
    content_preferences: UserContentPreferences = Field(default_factory=UserContentPreferences)
    options: UserOptions = Field(default_factory=UserOptions)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None = None
    phone_number: str | None = None
    location: str | None = None
    avatar_url: str | None = None
    about_me: str | None = None
    content_preferences: UserContentPreferences = Field(default_factory=UserContentPreferences)
    options: UserOptions = Field(default_factory=UserOptions)
    created_at: datetime


class UserSummaryResponse(UserResponse):
    trend_analysis_count: int = 0
    generated_content_count: int = 0
    publish_job_count: int = 0


class UsersListResponse(BaseModel):
    users: list[UserSummaryResponse] = Field(default_factory=list)
