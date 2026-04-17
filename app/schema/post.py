from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class PostRequest(BaseModel):
    prompt: str
    config_id: str
    decision: Literal["asking", "approve", "deny"] = Field(...)


class PostResponse(BaseModel):
    status: str
    source: str
    result_markdown: str


class ImageInfo(BaseModel):
    id: str
    image_url: str
    description: str = ""
    local_path: str = ""
    created_at: datetime
