import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContentGenerateRequest(BaseModel):
    user_id: Optional[uuid.UUID] = None
    trend_analysis_id: Optional[uuid.UUID] = None
    selected_keyword: Optional[str] = None
    prompt: Optional[str] = Field(default=None, min_length=5)


class PostContentSchema(BaseModel):
    post_type: str = "multi_image_post"
    title: str = ""
    hook: str = ""
    caption: str = ""
    description: str = ""
    body: str = ""
    call_to_action: str = ""
    hashtags: List[str] = Field(default_factory=list)
    tone: str = ""
    personalization_notes: List[str] = Field(default_factory=list)


class PostImageSchema(BaseModel):
    index: int = 0
    title: str = ""
    description: str = ""
    prompt: str = ""
    style: str = "vivid"
    size: str = "1792x1024"
    output_path: str = ""
    id: str = ""
    image_url: str = ""
    local_path: str = ""
    created_at: str = ""
    image_store_error: str = ""

    @model_validator(mode="before")
    @classmethod
    def default_description_from_prompt(cls, value):
        if isinstance(value, dict) and not value.get("description"):
            value = {**value, "description": value.get("prompt") or ""}
        return value


class PlatformPostDetailSchema(BaseModel):
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    cta: str = ""
    best_post_time: str = ""
    image_notes: str = ""


class PublishingSchema(BaseModel):
    default_visibility: str = ""
    recommended_platforms: List[str] = Field(default_factory=list)
    timezone: str = ""
    weekly_content_frequency: int = 0


class GeneratedContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = None
    trend_analysis_id: Optional[uuid.UUID] = None
    selected_keyword: str = ""
    main_title: str = ""
    post_content: PostContentSchema = Field(default_factory=PostContentSchema)
    image_set: List[PostImageSchema] = Field(default_factory=list)
    platform_posts: Dict[str, PlatformPostDetailSchema] = Field(default_factory=dict)
    publishing: PublishingSchema = Field(default_factory=PublishingSchema)
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedContentsListResponse(BaseModel):
    items: List[GeneratedContentResponse] = Field(default_factory=list)
