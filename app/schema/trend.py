from pydantic import BaseModel, Field


class TrendAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Trend analysis question from frontend")


class TrendAnalyzeResponse(BaseModel):
    status: str
    source: str
    result_markdown: str


class TrendCategory(BaseModel):
    id: int
    name: str


class GoogleTrendHotQuery(BaseModel):
    query: str
    start_timestamp: int
    end_timestamp: int | None = None
    active: bool
    search_volume: int
    increase_percentage: int
    categories: list[TrendCategory]
    trend_breakdown: list[str] = Field(default_factory=list)
    serpapi_google_trends_link: str


class GoogleTrendTimePoint(BaseModel):
    date: str
    timestamp: int
    interest_score: int
    partial_data: bool = False


class GoogleTrendRelatedQuery(BaseModel):
    query: str
    value_label: str
    extracted_value: int
    link: str


class GoogleTrendSnapshot(BaseModel):
    keyword: str
    region: str
    date_range: str
    trending_searches: list[GoogleTrendHotQuery]
    interest_over_time: list[GoogleTrendTimePoint]
    related_queries_top: list[GoogleTrendRelatedQuery]
    related_queries_rising: list[GoogleTrendRelatedQuery]


class TikTokTrendingVideo(BaseModel):
    source_type: str
    source_value: str
    video_id: str
    author_id: str
    author_username: str
    caption: str
    hashtags: list[str]
    views: int
    likes: int
    comments: int
    shares: int
    created_at: str
    engagement_rate: float
    velocity: float
    virality: float
    trend_score: float
    video_url: str | None = None
    cover_url: str | None = None
    sound_title: str | None = None


class TikTokTrendSnapshot(BaseModel):
    region: str
    keyword: str
    hashtag: str
    fetched_at: str
    videos: list[TikTokTrendingVideo]


class TrendRecommendation(BaseModel):
    idea_id: str
    title: str
    hook: str
    platform: str
    format: str
    based_on: list[str]
    confidence_score: float
    why_it_matches: str


class CrossPlatformInsight(BaseModel):
    dominant_topic: str
    audience_intent: str
    recommended_posting_window: str
    momentum_score: float


class TrendOverviewResponse(BaseModel):
    status: str
    source: str
    generated_at: str
    google_trends: GoogleTrendSnapshot
    tiktok: TikTokTrendSnapshot
    cross_platform_insight: CrossPlatformInsight
    recommendations: list[TrendRecommendation]
