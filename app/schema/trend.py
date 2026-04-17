from datetime import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TrendAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Topic or keyword to analyze.")
    limit: int = Field(default=3, ge=1, le=5, description="How many ranked trend items to return.")
    user_id: uuid.UUID | None = None


class TrendResultItemResponse(BaseModel):
    main_keyword: str
    why_the_trend_happens: str
    trend_score: float
    interest_over_day: list[Any] = Field(default_factory=list)
    avg_views_per_hour: float
    recommended_action: str
    top_videos: list[str] 
    top_hashtags: list[str] = Field(default_factory=list)
    google: dict[str, Any] | None = None
    tiktok: dict[str, Any] | None = None
    threads: dict[str, Any] | None = None


class TrendAnalyzeResponse(BaseModel):
    analysis_id: uuid.UUID | None = None
    query: str
    results: list[TrendResultItemResponse] = Field(default_factory=list)
    markdown_summary: str = ""
    error: dict[str, Any] | None = None


class TrendAnalysisRecordResponse(TrendAnalyzeResponse):
    model_config = ConfigDict(from_attributes=True)

    status: str = "completed"
    user_id: uuid.UUID | None = None
    created_at: datetime


class TrendAnalysesListResponse(BaseModel):
    items: list[TrendAnalysisRecordResponse] = Field(default_factory=list)


class TrendOverviewResponse(BaseModel):
    keyword: str
    region: str
    hashtag: str
    overview: dict[str, Any]
