from pydantic import BaseModel, Field
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
    top_hashtags: List[str]
    google: GoogleSummary
    tiktok: Optional[TikTokSummary] = None
    threads: Optional[dict] = None

class TrendReport(BaseModel):
    """The root object matching trend_analysis_sample.json structure."""
    query: str
    results: List[TrendResult]
    markdown_summary: str
    generated_at: int = Field(default_factory=lambda: int(time.time()))