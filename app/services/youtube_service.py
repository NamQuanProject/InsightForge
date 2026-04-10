from statistics import mean

from fastapi import HTTPException

from app.schema.youtube import (
    YouTubeChannelStatus,
    YouTubeChannelStatusResponse,
    YouTubeRecommendation,
    YouTubeRecommendationsResponse,
    YouTubeTrendOverviewSummary,
    YouTubeTrendTopic,
    YouTubeTrendsResponse,
    YouTubeVideo,
    YouTubeVideoAverages,
    YouTubeVideoDetailResponse,
    YouTubeVideoStats,
    YouTubeVideosResponse,
    YouTubeWatcherSegment,
)
from app.services.platform_mock_service import PlatformMockService


class YouTubeService(PlatformMockService):
    def __init__(self) -> None:
        super().__init__("youtube")

    def get_channel_status(self) -> YouTubeChannelStatusResponse:
        row = self._load_single("channel.csv")
        channel = YouTubeChannelStatus(
            channel_id=row["channel_id"],
            handle=row["handle"],
            display_name=row["display_name"],
            description=row["description"],
            avatar_url=row["avatar_url"],
            channel_url=row["channel_url"],
            subscribers=self._to_int(row["subscribers"]),
            total_views=self._to_int(row["total_views"]),
            total_watch_hours=self._to_int(row["total_watch_hours"]),
            total_videos=self._to_int(row["total_videos"]),
            average_views=self._to_int(row["average_views"]),
            average_likes=self._to_int(row["average_likes"]),
            average_comments=self._to_int(row["average_comments"]),
            engagement_rate=self._to_float(row["engagement_rate"]),
            average_view_duration_seconds=self._to_float(row["average_view_duration_seconds"]),
            click_through_rate=self._to_float(row["click_through_rate"]),
            upload_frequency_per_week=self._to_float(row["upload_frequency_per_week"]),
            top_regions=self._split(row["top_regions"]),
            traffic_sources=self._split(row["traffic_sources"]),
        )
        return YouTubeChannelStatusResponse(platform="youtube", channel=channel)

    def get_trends(self) -> YouTubeTrendsResponse:
        overview = self._load_single("trends_overview.csv")
        topics = self._get_trend_topics()
        videos = sorted(self._get_videos(), key=lambda item: item.stats.trend_score, reverse=True)[:5]
        segments = self._get_watcher_segments()
        return YouTubeTrendsResponse(
            platform="youtube",
            overview_summary=YouTubeTrendOverviewSummary(
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

    def get_recommendations(self) -> YouTubeRecommendationsResponse:
        rows = self._read_rows("recommendations.csv")
        recommendations = [
            YouTubeRecommendation(
                recommendation_id=row["recommendation_id"],
                content_idea=row["content_idea"],
                title_idea=row["title_idea"],
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
        return YouTubeRecommendationsResponse(platform="youtube", recommendations=recommendations)

    def get_video(self, video_id: str) -> YouTubeVideoDetailResponse:
        video = next((video for video in self._get_videos() if video.video_id == video_id), None)
        if video is None:
            raise HTTPException(status_code=404, detail=f"YouTube video not found: {video_id}")
        return YouTubeVideoDetailResponse(platform="youtube", video=video)

    def get_videos(self) -> YouTubeVideosResponse:
        videos = sorted(self._get_videos(), key=lambda item: item.published_at, reverse=True)
        averages = YouTubeVideoAverages(
            total_videos=len(videos),
            average_views=round(mean(video.stats.views for video in videos)),
            average_likes=round(mean(video.stats.likes for video in videos)),
            average_comments=round(mean(video.stats.comments for video in videos)),
            average_impressions=round(mean(video.stats.impressions for video in videos)),
            average_click_through_rate=round(mean(video.stats.click_through_rate for video in videos), 4),
            average_watch_hours=round(mean(video.stats.watch_hours for video in videos), 1),
            average_engagement_rate=round(mean(video.stats.engagement_rate for video in videos), 4),
        )
        return YouTubeVideosResponse(platform="youtube", averages=averages, videos=videos)

    def _get_videos(self) -> list[YouTubeVideo]:
        rows = self._read_rows("videos.csv")
        return [
            YouTubeVideo(
                video_id=row["video_id"],
                title=row["title"],
                description=row["description"],
                thumbnail_url=row["thumbnail_url"],
                video_url=row["video_url"],
                duration_seconds=self._to_int(row["duration_seconds"]),
                published_at=row["published_at"],
                stats=YouTubeVideoStats(
                    views=self._to_int(row["views"]),
                    likes=self._to_int(row["likes"]),
                    comments=self._to_int(row["comments"]),
                    impressions=self._to_int(row["impressions"]),
                    click_through_rate=self._to_float(row["click_through_rate"]),
                    average_view_duration_seconds=self._to_float(row["average_view_duration_seconds"]),
                    watch_hours=self._to_float(row["watch_hours"]),
                    engagement_rate=self._to_float(row["engagement_rate"]),
                    trend_score=self._to_float(row["trend_score"]),
                ),
            )
            for row in rows
        ]

    def _get_trend_topics(self) -> list[YouTubeTrendTopic]:
        rows = self._read_rows("trends.csv")
        return [
            YouTubeTrendTopic(
                topic_id=row["topic_id"],
                topic=row["topic"],
                keyword=row["keyword"],
                search_volume=self._to_int(row["search_volume"]),
                increase_percentage=self._to_int(row["increase_percentage"]),
                potential_views=self._to_int(row["potential_views"]),
                trend_score=self._to_float(row["trend_score"]),
                related_queries=self._split(row["related_queries"]),
                source=row["source"],
                sample_video_ids=self._split(row["sample_video_ids"]),
            )
            for row in rows
        ]

    def _get_watcher_segments(self) -> list[YouTubeWatcherSegment]:
        rows = self._read_rows("watcher_segments.csv")
        return [
            YouTubeWatcherSegment(
                segment=row["segment"],
                affinity_score=self._to_float(row["affinity_score"]),
                interests=self._split(row["interests"]),
                rationale=row["rationale"],
            )
            for row in rows
        ]
