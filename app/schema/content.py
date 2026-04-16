from datetime import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# class ContentGenerateRequest(BaseModel):
#     user_id: uuid.UUID | None = None
#     trend_analysis_id: uuid.UUID | None = None
#     selected_keyword: str | None = None
#     prompt: str | None = Field(default=None, min_length=5)


# class GeneratedContentResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: uuid.UUID
#     user_id: uuid.UUID | None = None
#     trend_analysis_id: uuid.UUID | None = None
#     selected_keyword: str | None = None
#     main_title: str | None = None
#     video_script: dict[str, Any] | list[Any] = Field(default_factory=dict)
#     platform_posts: dict[str, Any] = Field(default_factory=dict)
#     thumbnail: dict[str, Any] | None = None
#     music_background: str | None = None
#     raw_output: dict[str, Any] = Field(default_factory=dict)
#     status: str
#     created_at: datetime


# class GeneratedContentsListResponse(BaseModel):
#     items: list[GeneratedContentResponse] = Field(default_factory=list)
import uuid
from datetime import datetime
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------
 
class ContentGenerateRequest(BaseModel):
    user_id: Optional[uuid.UUID] = None
    trend_analysis_id: Optional[uuid.UUID] = None
    selected_keyword: Optional[str] = None
    prompt: Optional[str] = Field(default=None, min_length=5)

# --- Phân cấp nhỏ nhất: Thumbnail ---
class ThumbnailSchema(BaseModel):
    prompt: str
    style: str = "vivid"
    size: str = "1792x1024"
    output_path: str

# --- Phân đoạn Video ---
class VideoSectionSchema(BaseModel):
    timestamp: str
    label: str
    narration: str
    notes: str
    thumbnail: ThumbnailSchema  # Mỗi section có 1 thumbnail riêng

# --- Kịch bản Video tổng thể ---
class VideoScriptSchema(BaseModel):
    title: str
    duration_estimate: str = "60s"
    hook: str
    sections: List[VideoSectionSchema]
    call_to_action: str
    captions_style: str
    music_mood: str

# --- Chi tiết bài đăng mạng xã hội ---
class PlatformPostDetailSchema(BaseModel):
    caption: str
    hashtags: List[str]
    cta: str
    best_post_time: str
    thumbnail_description: str

# --- Schema chính cho kết quả trả về ---
class GeneratedContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = None
    trend_analysis_id: Optional[uuid.UUID] = None
    selected_keyword: str
    main_title: str
    video_script: VideoScriptSchema # Cấu trúc đã được định nghĩa ở trên
    platform_posts: Dict[str, PlatformPostDetailSchema]
    music_background: str
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedContentsListResponse(BaseModel):
    items: List[GeneratedContentResponse] = Field(default_factory=list)
