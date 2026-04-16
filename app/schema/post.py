from pydantic import BaseModel, Field
from typing import Literal


class PostRequest(BaseModel):
    prompt: str
    config_id: str
    decision: Literal["asking", "approve", "deny"] = Field(
        ..., 
    )


class PostResponse(BaseModel):
    status: str
    source: str
    result_markdown: str

