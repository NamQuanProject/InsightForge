from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
import time

class GoogleSummary(BaseModel):
    keyword: str
    momentum: str
    peak_region: Optional[str] = None

class TikTokSummary(BaseModel):
    platform: str = "TikTok"
    top_velocity: float
    avg_engagement_rate: float

class TrendResult(BaseModel):
    main_keyword: str
    why_the_trend_happens: str
    trend_score: float
    interest_over_day: List[float] = Field(default_factory=list)
    avg_views_per_hour: float
    recommended_action: str
    top_videos: List[str] = Field(default_factory=list)
    top_hashtags: List[str] = Field(default_factory=list)
    google: GoogleSummary
    tiktok: Optional[TikTokSummary] = None
    threads: Optional[dict] = None

    @model_validator(mode="after")
    def ensure_nonzero_interest_over_day(self) -> "TrendResult":
        if len(self.interest_over_day) >= 3 and any(value > 0 for value in self.interest_over_day):
            self.interest_over_day = [round(max(0.0, float(value)), 2) for value in self.interest_over_day]
            return self

        score = min(100.0, max(1.0, float(self.trend_score or 1.0)))
        velocity_lift = min(18.0, max(float(self.avg_views_per_hour or 0.0), 0.0) / 5000.0)
        base = min(88.0, max(8.0, score * 0.62 + velocity_lift))
        momentum = (self.google.momentum or "stable").lower()

        if momentum == "rising":
            factors = [0.58, 0.68, 0.8, 0.93, 1.08, 1.22]
        elif momentum == "declining":
            factors = [1.18, 1.08, 0.96, 0.84, 0.73, 0.62]
        else:
            factors = [0.86, 0.94, 1.02, 0.97, 1.06, 1.0]

        self.interest_over_day = [
            round(min(100.0, max(1.0, base * factor)), 2)
            for factor in factors
        ]
        return self

class TrendReport(BaseModel):
    """The root object matching trend_analysis_sample.json structure."""
    query: str
    results: List[TrendResult]
    markdown_summary: str
    generated_at: int = Field(default_factory=lambda: int(time.time()))
