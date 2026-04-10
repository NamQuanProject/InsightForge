from pydantic import BaseModel


class YouTubeChannelStatus(BaseModel):
    channel_id: str
    handle: str
    display_name: str
    description: str
    avatar_url: str
    channel_url: str
    subscribers: int
    total_views: int
    total_watch_hours: int
    total_videos: int
    average_views: int
    average_likes: int
    average_comments: int
    engagement_rate: float
    average_view_duration_seconds: float
    click_through_rate: float
    upload_frequency_per_week: float
    top_regions: list[str]
    traffic_sources: list[str]


class YouTubeVideoStats(BaseModel):
    views: int
    likes: int
    comments: int
    impressions: int
    click_through_rate: float
    average_view_duration_seconds: float
    watch_hours: float
    engagement_rate: float
    trend_score: float


class YouTubeVideo(BaseModel):
    video_id: str
    title: str
    description: str
    thumbnail_url: str
    video_url: str
    duration_seconds: int
    published_at: str
    stats: YouTubeVideoStats


class YouTubeTrendTopic(BaseModel):
    topic_id: str
    topic: str
    keyword: str
    search_volume: int
    increase_percentage: int
    potential_views: int
    trend_score: float
    related_queries: list[str]
    source: str
    sample_video_ids: list[str]


class YouTubeWatcherSegment(BaseModel):
    segment: str
    affinity_score: float
    interests: list[str]
    rationale: str


class YouTubeTrendOverviewSummary(BaseModel):
    trend_window: str
    hottest_topic: str
    average_potential_views: int
    rising_topic_count: int
    strategist_note: str


class YouTubeRecommendation(BaseModel):
    recommendation_id: str
    content_idea: str
    title_idea: str
    thumbnail_idea: str
    voice_style: str
    background_music: str
    format: str
    confidence_score: float
    reasoning: str
    source_topics: list[str]


class YouTubeVideoAverages(BaseModel):
    total_videos: int
    average_views: int
    average_likes: int
    average_comments: int
    average_impressions: int
    average_click_through_rate: float
    average_watch_hours: float
    average_engagement_rate: float


class YouTubeChannelStatusResponse(BaseModel):
    platform: str
    channel: YouTubeChannelStatus


class YouTubeTrendsResponse(BaseModel):
    platform: str
    overview_summary: YouTubeTrendOverviewSummary
    trend_topics: list[YouTubeTrendTopic]
    trending_videos: list[YouTubeVideo]
    watcher_segments: list[YouTubeWatcherSegment]


class YouTubeRecommendationsResponse(BaseModel):
    platform: str
    recommendations: list[YouTubeRecommendation]


class YouTubeVideoDetailResponse(BaseModel):
    platform: str
    video: YouTubeVideo


class YouTubeVideosResponse(BaseModel):
    platform: str
    averages: YouTubeVideoAverages
    videos: list[YouTubeVideo]
