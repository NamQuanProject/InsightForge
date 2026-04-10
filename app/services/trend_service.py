import csv
from pathlib import Path
from urllib.parse import quote_plus

from app.schema.trend import (
    CrossPlatformInsight,
    GoogleTrendHotQuery,
    GoogleTrendRelatedQuery,
    GoogleTrendSnapshot,
    GoogleTrendTimePoint,
    TikTokTrendingVideo,
    TikTokTrendSnapshot,
    TrendAnalyzeResponse,
    TrendCategory,
    TrendOverviewResponse,
    TrendRecommendation,
)


class TrendService:
    def __init__(self) -> None:
        self.client = None
        self.mock_data_dir = Path(__file__).resolve().parents[1] / "mock_data"

    async def analyze(self, query: str) -> TrendAnalyzeResponse:
        if self.client is None:
            from app.services.a2a_client import InsightForgeA2AClient

            self.client = InsightForgeA2AClient()
        result = await self.client.ask(query)
        return TrendAnalyzeResponse(
            status="success",
            source="a2a-agent",
            result_markdown=result,
        )

    def get_mock_overview(
        self,
        keyword: str = "ai video editor",
        region: str = "VN",
        hashtag: str = "aivideo",
    ) -> TrendOverviewResponse:
        context = self._build_template_context(keyword=keyword, region=region, hashtag=hashtag)
        metadata = self._load_single_row("overview_metadata.csv", context)
        google_trends = self._build_mock_google_trends(keyword=keyword, region=region, context=context)
        tiktok = self._build_mock_tiktok(keyword=keyword, hashtag=hashtag, region=region, context=context)
        cross_platform_insight = self._build_cross_platform_insight(context=context)
        recommendations = self._build_recommendations(context=context)

        return TrendOverviewResponse(
            status=metadata["status"],
            source=metadata["source"],
            generated_at=metadata["generated_at"],
            google_trends=google_trends,
            tiktok=tiktok,
            cross_platform_insight=cross_platform_insight,
            recommendations=recommendations,
        )

    def _build_mock_google_trends(
        self,
        keyword: str,
        region: str,
        context: dict[str, str],
    ) -> GoogleTrendSnapshot:
        metadata = self._load_single_row("overview_metadata.csv", context)
        trending_rows = self._read_csv_rows("google_trending_searches.csv", context)
        time_rows = self._read_csv_rows("google_interest_over_time.csv", context)
        related_rows = self._read_csv_rows("google_related_queries.csv", context)

        trending_searches = [
            GoogleTrendHotQuery(
                query=row["query"],
                start_timestamp=int(row["start_timestamp"]),
                end_timestamp=int(row["end_timestamp"]) if row["end_timestamp"] else None,
                active=self._to_bool(row["active"]),
                search_volume=int(row["search_volume"]),
                increase_percentage=int(row["increase_percentage"]),
                categories=self._build_categories(
                    ids=row["category_ids"],
                    names=row["category_names"],
                ),
                trend_breakdown=self._split_pipe(row["trend_breakdown"]),
                serpapi_google_trends_link=row["serpapi_google_trends_link"],
            )
            for row in trending_rows
        ]

        interest_over_time = [
            GoogleTrendTimePoint(
                date=row["date"],
                timestamp=int(row["timestamp"]),
                interest_score=int(row["interest_score"]),
                partial_data=self._to_bool(row["partial_data"]),
            )
            for row in time_rows
        ]

        top_queries = []
        rising_queries = []
        for row in related_rows:
            query = GoogleTrendRelatedQuery(
                query=row["query"],
                value_label=row["value_label"],
                extracted_value=int(row["extracted_value"]),
                link=row["link"],
            )
            if row["kind"] == "top":
                top_queries.append(query)
            elif row["kind"] == "rising":
                rising_queries.append(query)

        return GoogleTrendSnapshot(
            keyword=keyword,
            region=region,
            date_range=metadata["google_date_range"],
            trending_searches=trending_searches,
            interest_over_time=interest_over_time,
            related_queries_top=top_queries,
            related_queries_rising=rising_queries,
        )

    def _build_mock_tiktok(
        self,
        keyword: str,
        hashtag: str,
        region: str,
        context: dict[str, str],
    ) -> TikTokTrendSnapshot:
        metadata = self._load_single_row("overview_metadata.csv", context)
        video_rows = self._read_csv_rows("tiktok_trending_videos.csv", context)

        videos = [
            TikTokTrendingVideo(
                source_type=row["source_type"],
                source_value=row["source_value"],
                video_id=row["video_id"],
                author_id=row["author_id"],
                author_username=row["author_username"],
                caption=row["caption"],
                hashtags=self._split_pipe(row["hashtags"]),
                views=int(row["views"]),
                likes=int(row["likes"]),
                comments=int(row["comments"]),
                shares=int(row["shares"]),
                created_at=row["created_at"],
                engagement_rate=float(row["engagement_rate"]),
                velocity=float(row["velocity"]),
                virality=float(row["virality"]),
                trend_score=float(row["trend_score"]),
                video_url=row["video_url"] or None,
                cover_url=row["cover_url"] or None,
                sound_title=row["sound_title"] or None,
            )
            for row in video_rows
        ]

        return TikTokTrendSnapshot(
            region=region,
            keyword=keyword,
            hashtag=hashtag,
            fetched_at=metadata["tiktok_fetched_at"],
            videos=videos,
        )

    def _build_cross_platform_insight(self, context: dict[str, str]) -> CrossPlatformInsight:
        row = self._load_single_row("cross_platform_insight.csv", context)
        return CrossPlatformInsight(
            dominant_topic=row["dominant_topic"],
            audience_intent=row["audience_intent"],
            recommended_posting_window=row["recommended_posting_window"],
            momentum_score=float(row["momentum_score"]),
        )

    def _build_recommendations(self, context: dict[str, str]) -> list[TrendRecommendation]:
        rows = self._read_csv_rows("recommendations.csv", context)
        return [
            TrendRecommendation(
                idea_id=row["idea_id"],
                title=row["title"],
                hook=row["hook"],
                platform=row["platform"],
                format=row["format"],
                based_on=self._split_pipe(row["based_on"]),
                confidence_score=float(row["confidence_score"]),
                why_it_matches=row["why_it_matches"],
            )
            for row in rows
        ]

    def _build_template_context(
        self,
        keyword: str,
        region: str,
        hashtag: str,
    ) -> dict[str, str]:
        return {
            "{{keyword}}": keyword,
            "{{keyword_plus}}": quote_plus(keyword),
            "{{region}}": region,
            "{{hashtag}}": hashtag,
            "{{hashtag_plus}}": quote_plus(hashtag),
        }

    def _read_csv_rows(
        self,
        filename: str,
        context: dict[str, str],
    ) -> list[dict[str, str]]:
        path = self.mock_data_dir / filename
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            return [
                {key: self._render_template(value or "", context) for key, value in row.items()}
                for row in reader
            ]

    def _load_single_row(
        self,
        filename: str,
        context: dict[str, str],
    ) -> dict[str, str]:
        rows = self._read_csv_rows(filename, context)
        if not rows:
            raise ValueError(f"Mock data file is empty: {filename}")
        return rows[0]

    def _render_template(self, value: str, context: dict[str, str]) -> str:
        rendered = value
        for placeholder, replacement in context.items():
            rendered = rendered.replace(placeholder, replacement)
        return rendered

    def _build_categories(self, ids: str, names: str) -> list[TrendCategory]:
        category_ids = self._split_pipe(ids)
        category_names = self._split_pipe(names)
        return [
            TrendCategory(id=int(category_id), name=category_name)
            for category_id, category_name in zip(category_ids, category_names, strict=False)
        ]

    def _split_pipe(self, value: str) -> list[str]:
        return [item.strip() for item in value.split("|") if item.strip()]

    def _to_bool(self, value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes"}
