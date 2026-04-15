from pydantic import BaseModel


class TikTokChannelStatus(BaseModel):
    channel_id: str
    handle: str
    display_name: str
    bio: str
    avatar_url: str
    profile_url: str
    followers: int
    following: int
    total_likes: int
    total_views: int
    total_videos: int
    average_views: int
    average_likes: int
    average_comments: int
    average_shares: int
    average_saves: int
    engagement_rate: float
    posting_frequency_per_week: float
    average_watch_time_seconds: float
    primary_regions: list[str]
    primary_categories: list[str]


class TikTokVideoStats(BaseModel):
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    engagement_rate: float
    trend_score: float


class TikTokVideo(BaseModel):
    video_id: str
    caption: str
    description: str
    hashtags: list[str]
    music_title: str
    duration_seconds: int
    posted_at: str
    thumbnail_url: str
    video_url: str
    stats: TikTokVideoStats


class TikTokTrendTopic(BaseModel):
    topic_id: str
    topic: str
    keyword: str
    search_volume: int
    increase_percentage: int
    potential_views: int
    trend_score: float
    related_hashtags: list[str]
    source: str
    sample_video_ids: list[str]


class TikTokWatcherSegment(BaseModel):
    segment: str
    affinity_score: float
    interests: list[str]
    rationale: str


class TikTokTrendOverviewSummary(BaseModel):
    trend_window: str
    hottest_topic: str
    average_potential_views: int
    rising_topic_count: int
    strategist_note: str


class TikTokRecommendation(BaseModel):
    recommendation_id: str
    content_idea: str
    hook: str
    thumbnail_idea: str
    voice_style: str
    background_music: str
    format: str
    confidence_score: float
    reasoning: str
    source_topics: list[str]


class TikTokVideoAverages(BaseModel):
    total_videos: int
    average_views: int
    average_likes: int
    average_comments: int
    average_shares: int
    average_saves: int
    average_engagement_rate: float


class TikTokChannelStatusResponse(BaseModel):
    platform: str
    channel: TikTokChannelStatus


class TikTokTrendsResponse(BaseModel):
    platform: str
    overview_summary: TikTokTrendOverviewSummary
    trend_topics: list[TikTokTrendTopic]
    trending_videos: list[TikTokVideo]
    watcher_segments: list[TikTokWatcherSegment]


class TikTokRecommendationsResponse(BaseModel):
    platform: str
    recommendations: list[TikTokRecommendation]


class TikTokVideoDetailResponse(BaseModel):
    platform: str
    video: TikTokVideo


class TikTokVideosResponse(BaseModel):
    platform: str
    averages: TikTokVideoAverages
    videos: list[TikTokVideo]
