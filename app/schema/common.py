from pydantic import BaseModel, Field


class UploadVideoRequest(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = ""
    file_path: str
    user: str | None = None
    visibility: str = "public"
    tags: list[str] = Field(default_factory=list)
    schedule_at: str | None = None
    async_upload: bool = True
    thumbnail_url: str | None = None
    category_id: str | None = None
    disable_comment: bool | None = None
    disable_duet: bool | None = None
    disable_stitch: bool | None = None
    is_aigc: bool | None = None
    cover_timestamp: int | None = None


class UploadVideoResponse(BaseModel):
    status: str
    platform: str
    upload_mode: str
    message: str
    external_post_id: str
    preview_url: str | None = None


class AnalyzeTrendsRequest(BaseModel):
    query: str = Field(..., min_length=3)
    region: str = "VN"
    limit: int = Field(default=5, ge=1, le=20)


class AgentProcessStatus(BaseModel):
    name: str
    url: str
    reachable: bool
    detail: str


class AgentsStatusResponse(BaseModel):
    status: str
    processes: list[AgentProcessStatus]
