from datetime import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TrendAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Topic or keyword to analyze.")
    limit: int = Field(default=3, ge=1, le=5, description="How many ranked trend items to return.")
    user_id: uuid.UUID | None = None


class TrendHistorySearchRequest(BaseModel):
    text: str | None = Field(default=None, description="Substring to search in saved trend history.")
    keyword: str | None = Field(default=None, description="Alias for text.")
    user_id: uuid.UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def normalize_search_text(self) -> "TrendHistorySearchRequest":
        value = str(self.text or self.keyword or "").strip()
        if not value:
            raise ValueError("text or keyword is required")
        self.text = value
        return self


class TrendResultItemResponse(BaseModel):
    main_keyword: str
    why_the_trend_happens: str
    trend_score: float
    interest_over_day: list[Any] = Field(default_factory=list)
    avg_views_per_hour: float
    recommended_action: str
    top_videos: list[str] = Field(default_factory=list)
    top_hashtags: list[str] = Field(default_factory=list)
    google: dict[str, Any] | None = None
    tiktok: dict[str, Any] | None = None
    threads: dict[str, Any] | None = None

    @model_validator(mode="after")
    def ensure_nonzero_interest_over_day(self) -> "TrendResultItemResponse":
        values = []
        for value in self.interest_over_day or []:
            try:
                values.append(max(0.0, float(value)))
            except (TypeError, ValueError):
                continue

        if len(values) >= 3 and any(value > 0 for value in values):
            self.interest_over_day = [round(value, 2) for value in values]
            return self

        momentum = "stable"
        if isinstance(self.google, dict):
            momentum = str(self.google.get("momentum") or "stable")

        score = min(100.0, max(1.0, float(self.trend_score or 1.0)))
        velocity_lift = min(18.0, max(float(self.avg_views_per_hour or 0.0), 0.0) / 5000.0)
        base = min(88.0, max(8.0, score * 0.62 + velocity_lift))

        if momentum.lower() == "rising":
            factors = [0.58, 0.68, 0.8, 0.93, 1.08, 1.22]
        elif momentum.lower() == "declining":
            factors = [1.18, 1.08, 0.96, 0.84, 0.73, 0.62]
        else:
            factors = [0.86, 0.94, 1.02, 0.97, 1.06, 1.0]

        self.interest_over_day = [
            round(min(100.0, max(1.0, base * factor)), 2)
            for factor in factors
        ]
        return self


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
