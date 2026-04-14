from pydantic import BaseModel, Field
import time
 
# 1.  SCHEMA
# ═══════════════════════════════════════════════════════════════
 
# ── 1a. Shared primitives ────────────────────────────────────
 
class TimePoint(BaseModel):
    """One point on a time-series chart."""
    date: str                       # "Mar 25, 2026"
    timestamp: int                  # unix epoch — use for x-axis sorting
    value: float                    # normalised 0-100 (Google) or trend_score (social)
 
 
class GoogleInsights(BaseModel):
    """Derived analytics the UI can display directly."""
    momentum: str                   # "rising" | "stable" | "declining" | "spike_then_drop"
    peak_value: float               # highest extracted_value in the window
    peak_date: str                  # date of that peak
    trough_value: float             # lowest value
    latest_value: float             # most recent data point
    is_partial_today: bool          # True if last point has partial_data=true
    # week-over-week change (last 7 days vs previous 7 days), None if < 14 pts
    wow_change_pct: float | None    = None
    # simple linear slope (positive = rising)
    slope: float | None             = None
    acceleration: float | None      = None   # slope of the slope — curvature signal
    related_rising_queries: list[str] = Field(default_factory=list)
    peak_region: str | None         = None
 
 
class SocialTimePoint(BaseModel):
    """One point on the social time-series — bucketed by day."""
    date: str
    timestamp: int
    avg_trend_score: float
    avg_velocity: float             # views/hour average for that day's videos
    avg_engagement_rate: float
    total_videos: int               # how many videos fall in this bucket
 
 
class SocialInsights(BaseModel):
    platform: str                   # "tiktok" | "threads"
    top_velocity: float             # highest velocity across all fetched videos
    avg_velocity: float
    avg_engagement_rate: float
    avg_trend_score: float
    top_content_angle: str | None   = None
    top_hashtags: list[str]         = Field(default_factory=list)
    sample_url: str | None          = None
    total_items_analyzed: int       = 0
 
 
# ── 1b. Per-platform blocks ──────────────────────────────────
 
class GoogleBlock(BaseModel):
    keyword: str
    timeseries: list[TimePoint]     = Field(default_factory=list)
    insights: GoogleInsights | None = None
 
 
class TikTokBlock(BaseModel):
    keyword: str
    timeseries: list[SocialTimePoint] = Field(default_factory=list)
    insights: SocialInsights | None   = None
    top_videos: list[dict]            = Field(default_factory=list)  # raw top-5
 
 
class ThreadsBlock(BaseModel):
    keyword: str
    timeseries: list[SocialTimePoint] = Field(default_factory=list)
    insights: SocialInsights | None   = None
    top_posts: list[dict]             = Field(default_factory=list)
 
 
# ── 1c. Root report ──────────────────────────────────────────
 
class TrendReport(BaseModel):
    """
    Everything the backend needs.
 
    UI usage guide
    ──────────────
    Line chart (search interest over time) → google.timeseries
    Bar / area chart (social velocity)     → tiktok.timeseries
    KPI cards                              → google.insights + tiktok.insights
    Classification badge                   → classification + confidence
    Markdown panel                         → markdown_report
    """
    query: str
    final_keywords: list[str]
 
    google:  GoogleBlock  | None = None
    tiktok:  TikTokBlock  | None = None
    threads: ThreadsBlock | None = None
 
    classification: str      # MEGA_TREND | EMERGING | INTEREST_ONLY | WEAK
    confidence: float        # 0–1
    recommended_action: str
    markdown_report: str
    generated_at: int = Field(default_factory=lambda: int(time.time()))


class TrendResultItem(BaseModel):
    """One ranked trend idea tailored for the client response."""

    main_keyword: str
    why_the_trend_happens: str
    trend_score: float
    interest_over_day: list[TimePoint] = Field(default_factory=list)
    avg_views_per_hour: float
    recommended_action: str
    top_hashtags: list[str] = Field(default_factory=list)
    google: GoogleBlock | None = None
    tiktok: TikTokBlock | None = None
    threads: ThreadsBlock | None = None


class TrendDiscoveryReport(BaseModel):
    """
    Multi-result trend report used by the updated trend discovery flow.

    UI usage guide
    - Render `results` as the main list view.
    - Render each item's `interest_over_day` as its sparkline or trend chart.
    - Use `markdown_summary` as an optional narrative summary panel.
    """

    query: str
    results: list[TrendResultItem] = Field(default_factory=list)
    markdown_summary: str = ""
    generated_at: int = Field(default_factory=lambda: int(time.time()))
