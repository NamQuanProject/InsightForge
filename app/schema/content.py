from datetime import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContentGenerateRequest(BaseModel):
    user_id: uuid.UUID | None = None
    trend_analysis_id: uuid.UUID | None = None
    selected_keyword: str | None = None
    prompt: str | None = Field(default=None, min_length=5)


class GeneratedContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    trend_analysis_id: uuid.UUID | None = None
    selected_keyword: str | None = None
    main_title: str | None = None
    video_script: dict[str, Any] | list[Any] = Field(default_factory=dict)
    platform_posts: dict[str, Any] = Field(default_factory=dict)
    thumbnail: dict[str, Any] | None = None
    music_background: str | None = None
    raw_output: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime


class GeneratedContentsListResponse(BaseModel):
    items: list[GeneratedContentResponse] = Field(default_factory=list)
