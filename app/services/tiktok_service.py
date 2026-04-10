from statistics import mean

from fastapi import HTTPException

from app.schema.tiktok import (
    TikTokChannelStatus,
    TikTokChannelStatusResponse,
    TikTokRecommendation,
    TikTokRecommendationsResponse,
    TikTokTrendOverviewSummary,
    TikTokTrendTopic,
    TikTokTrendsResponse,
    TikTokVideo,
    TikTokVideoAverages,
    TikTokVideoDetailResponse,
    TikTokVideoStats,
    TikTokVideosResponse,
    TikTokWatcherSegment,
)
from app.services.platform_mock_service import PlatformMockService


class TikTokService(PlatformMockService):
    def __init__(self) -> None:
        super().__init__("tiktok")

    def get_channel_status(self) -> TikTokChannelStatusResponse:
        row = self._load_single("channel.csv")
        channel = TikTokChannelStatus(
            channel_id=row["channel_id"],
            handle=row["handle"],
            display_name=row["display_name"],
            bio=row["bio"],
            avatar_url=row["avatar_url"],
            profile_url=row["profile_url"],
            followers=self._to_int(row["followers"]),
            following=self._to_int(row["following"]),
            total_likes=self._to_int(row["total_likes"]),
            total_views=self._to_int(row["total_views"]),
            total_videos=self._to_int(row["total_videos"]),
            average_views=self._to_int(row["average_views"]),
            average_likes=self._to_int(row["average_likes"]),
            average_comments=self._to_int(row["average_comments"]),
            average_shares=self._to_int(row["average_shares"]),
            average_saves=self._to_int(row["average_saves"]),
            engagement_rate=self._to_float(row["engagement_rate"]),
            posting_frequency_per_week=self._to_float(row["posting_frequency_per_week"]),
            average_watch_time_seconds=self._to_float(row["average_watch_time_seconds"]),
            primary_regions=self._split(row["primary_regions"]),
            primary_categories=self._split(row["primary_categories"]),
        )
        return TikTokChannelStatusResponse(platform="tiktok", channel=channel)

    def get_trends(self) -> TikTokTrendsResponse:
        overview = self._load_single("trends_overview.csv")
        topics = self._get_trend_topics()
        videos = sorted(self._get_videos(), key=lambda item: item.stats.trend_score, reverse=True)[:5]
        segments = self._get_watcher_segments()
        return TikTokTrendsResponse(
            platform="tiktok",
            overview_summary=TikTokTrendOverviewSummary(
                trend_window=overview["trend_window"],
                hottest_topic=overview["hottest_topic"],
                average_potential_views=self._to_int(overview["average_potential_views"]),
                rising_topic_count=self._to_int(overview["rising_topic_count"]),
                strategist_note=overview["strategist_note"],
            ),
            trend_topics=topics,
            trending_videos=videos,
            watcher_segments=segments,
        )

    def get_recommendations(self) -> TikTokRecommendationsResponse:
        rows = self._read_rows("recommendations.csv")
        recommendations = [
            TikTokRecommendation(
                recommendation_id=row["recommendation_id"],
                content_idea=row["content_idea"],
                hook=row["hook"],
                thumbnail_idea=row["thumbnail_idea"],
                voice_style=row["voice_style"],
                background_music=row["background_music"],
                format=row["format"],
                confidence_score=self._to_float(row["confidence_score"]),
                reasoning=row["reasoning"],
                source_topics=self._split(row["source_topics"]),
            )
            for row in rows
        ]
        return TikTokRecommendationsResponse(platform="tiktok", recommendations=recommendations)

    def get_video(self, video_id: str) -> TikTokVideoDetailResponse:
        video = next((video for video in self._get_videos() if video.video_id == video_id), None)
        if video is None:
            raise HTTPException(status_code=404, detail=f"TikTok video not found: {video_id}")
        return TikTokVideoDetailResponse(platform="tiktok", video=video)

    def get_videos(self) -> TikTokVideosResponse:
        videos = sorted(self._get_videos(), key=lambda item: item.posted_at, reverse=True)
        averages = TikTokVideoAverages(
            total_videos=len(videos),
            average_views=round(mean(video.stats.views for video in videos)),
            average_likes=round(mean(video.stats.likes for video in videos)),
            average_comments=round(mean(video.stats.comments for video in videos)),
            average_shares=round(mean(video.stats.shares for video in videos)),
            average_saves=round(mean(video.stats.saves for video in videos)),
            average_engagement_rate=round(mean(video.stats.engagement_rate for video in videos), 4),
        )
        return TikTokVideosResponse(platform="tiktok", averages=averages, videos=videos)

    def _get_videos(self) -> list[TikTokVideo]:
        rows = self._read_rows("videos.csv")
        return [
            TikTokVideo(
                video_id=row["video_id"],
                caption=row["caption"],
                description=row["description"],
                hashtags=self._split(row["hashtags"]),
                music_title=row["music_title"],
                duration_seconds=self._to_int(row["duration_seconds"]),
                posted_at=row["posted_at"],
                thumbnail_url=row["thumbnail_url"],
                video_url=row["video_url"],
                stats=TikTokVideoStats(
                    views=self._to_int(row["views"]),
                    likes=self._to_int(row["likes"]),
                    comments=self._to_int(row["comments"]),
                    shares=self._to_int(row["shares"]),
                    saves=self._to_int(row["saves"]),
                    engagement_rate=self._to_float(row["engagement_rate"]),
                    trend_score=self._to_float(row["trend_score"]),
                ),
            )
            for row in rows
        ]

    def _get_trend_topics(self) -> list[TikTokTrendTopic]:
        rows = self._read_rows("trends.csv")
        return [
            TikTokTrendTopic(
                topic_id=row["topic_id"],
                topic=row["topic"],
                keyword=row["keyword"],
                search_volume=self._to_int(row["search_volume"]),
                increase_percentage=self._to_int(row["increase_percentage"]),
                potential_views=self._to_int(row["potential_views"]),
                trend_score=self._to_float(row["trend_score"]),
                related_hashtags=self._split(row["related_hashtags"]),
                source=row["source"],
                sample_video_ids=self._split(row["sample_video_ids"]),
            )
            for row in rows
        ]

    def _get_watcher_segments(self) -> list[TikTokWatcherSegment]:
        rows = self._read_rows("watcher_segments.csv")
        return [
            TikTokWatcherSegment(
                segment=row["segment"],
                affinity_score=self._to_float(row["affinity_score"]),
                interests=self._split(row["interests"]),
                rationale=row["rationale"],
            )
            for row in rows
        ]
