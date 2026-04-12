import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException


class UploadPostMockService:
    def __init__(self) -> None:
        self.data_path = Path(__file__).resolve().parents[1] / "mock_data" / "upload_post" / "mock_bundle.json"
        self.data = self._load_data()

    def get_profile_analytics(self, profile_username: str, platforms: list[str]) -> dict[str, Any]:
        profile = self._get_profile(profile_username)
        selected_platforms = self._resolve_platforms(platforms)

        platform_payload: dict[str, Any] = {}
        summary = {
            "followers": 0,
            "reach": 0,
            "views": 0,
            "impressions": 0,
            "profileViews": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "saves": 0,
        }

        for platform in selected_platforms:
            analytics = self._platform_analytics(platform)
            platform_payload[platform] = {
                "followers": analytics["followers"],
                "reach": analytics["reach"],
                "views": analytics["views"],
                "impressions": analytics["impressions"],
                "profileViews": analytics["profileViews"],
                "likes": analytics["likes"],
                "comments": analytics["comments"],
                "shares": analytics["shares"],
                "saves": analytics["saves"],
                "reach_timeseries": self._timeseries(analytics["daily_metrics"], "reach"),
                "impressions_timeseries": self._timeseries(analytics["daily_metrics"], "impressions"),
                "views_timeseries": self._timeseries(analytics["daily_metrics"], "views"),
                "likes_timeseries": self._timeseries(analytics["daily_metrics"], "likes"),
                "comments_timeseries": self._timeseries(analytics["daily_metrics"], "comments"),
                "shares_timeseries": self._timeseries(analytics["daily_metrics"], "shares"),
                "metric_type": "reach",
            }

            for metric in summary:
                summary[metric] += analytics.get(metric, 0)

        return {
            "success": True,
            "profile_username": profile["profile_username"],
            "start_date": profile["start_date"],
            "end_date": profile["end_date"],
            "platforms": platform_payload,
            "summary": summary,
        }

    def get_total_impressions(
        self,
        profile_username: str,
        date_value: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str | None = None,
        platforms: list[str] | None = None,
        breakdown: bool = False,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        profile = self._get_profile(profile_username)
        selected_platforms = self._resolve_platforms(platforms or [])
        metric_names = metrics or ["impressions", "likes", "comments", "shares"]
        window_start, window_end = self._resolve_date_window(profile, date_value, start_date, end_date, period)

        per_platform: dict[str, dict[str, int]] = {metric: {} for metric in metric_names}
        per_day: dict[str, dict[str, int]] = {metric: {} for metric in metric_names}

        for platform in selected_platforms:
            analytics = self._platform_analytics(platform)
            daily_rows = self._filter_daily_metrics(analytics["daily_metrics"], window_start, window_end)

            for metric in metric_names:
                platform_total = sum(int(row.get(metric, 0)) for row in daily_rows)
                per_platform[metric][platform] = platform_total
                for row in daily_rows:
                    metric_date = row["date"]
                    per_day[metric][metric_date] = per_day[metric].get(metric_date, 0) + int(row.get(metric, 0))

        totals = {metric: sum(platform_map.values()) for metric, platform_map in per_platform.items()}
        response: dict[str, Any] = {
            "success": True,
            "profile_username": profile["profile_username"],
            "start_date": window_start.isoformat(),
            "end_date": window_end.isoformat(),
            "metrics": totals,
            "per_platform": per_platform,
            "per_day": per_day,
        }
        if breakdown:
            response["breakdown"] = {
                platform: {
                    "impressions": per_platform.get("impressions", {}).get(platform, 0),
                    "likes": per_platform.get("likes", {}).get(platform, 0),
                    "comments": per_platform.get("comments", {}).get(platform, 0),
                    "shares": per_platform.get("shares", {}).get(platform, 0),
                }
                for platform in selected_platforms
            }
        return response

    def get_post_analytics(self, request_id: str, platform: str | None = None) -> dict[str, Any]:
        post = self._find_post(request_id)
        platforms = post["platforms"]
        if platform:
            if platform not in platforms:
                raise HTTPException(status_code=404, detail=f"Platform '{platform}' not found for request_id '{request_id}'.")
            platforms = {platform: platforms[platform]}

        return {
            "success": True,
            "post": {
                "request_id": post["request_id"],
                "profile_username": post["profile_username"],
                "post_title": post["post_title"],
                "post_caption": post["post_caption"],
                "media_type": post["media_type"],
                "upload_timestamp": post["upload_timestamp"],
            },
            "platforms": platforms,
        }

    def get_history(self, profile_username: str | None = None, page: int = 1, limit: int = 20) -> dict[str, Any]:
        profile = self._get_profile(profile_username or self.data["profile"]["profile_username"])
        history = self._build_history(profile)
        start_index = (page - 1) * limit
        end_index = start_index + limit
        return {
            "history": history[start_index:end_index],
            "total": len(history),
            "page": page,
            "limit": limit,
        }

    def get_comments(
        self,
        platform: str,
        user: str,
        post_id: str | None = None,
        post_url: str | None = None,
    ) -> dict[str, Any]:
        self._get_profile(user)
        if not post_id and not post_url:
            raise HTTPException(status_code=400, detail="Provide either post_id or post_url.")

        normalized_platform = platform.strip().lower()
        for post in self.data["posts"]:
            platform_entry = post["platforms"].get(normalized_platform)
            if not platform_entry:
                continue
            if post_id and platform_entry["platform_post_id"] == post_id:
                return {"success": True, "comments": platform_entry.get("comments", [])}
            if post_url and platform_entry["post_url"] == post_url:
                return {"success": True, "comments": platform_entry.get("comments", [])}

        raise HTTPException(
            status_code=404,
            detail=f"No mock comments found for platform='{normalized_platform}', user='{user}', post_id/post_url provided.",
        )

    def _load_data(self) -> dict[str, Any]:
        with self.data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _get_profile(self, profile_username: str) -> dict[str, Any]:
        profile = self.data["profile"]
        if profile["profile_username"] != profile_username:
            raise HTTPException(status_code=404, detail=f"Mock upload-post profile not found: {profile_username}")
        return profile

    def _platform_analytics(self, platform: str) -> dict[str, Any]:
        analytics = self.data["profile_analytics"].get(platform)
        if analytics is None:
            raise HTTPException(status_code=404, detail=f"Mock analytics not found for platform: {platform}")
        return analytics

    def _resolve_platforms(self, platforms: list[str]) -> list[str]:
        requested = [platform.strip().lower() for platform in platforms if platform and platform.strip()]
        available = set(self.data["profile"]["connected_platforms"])
        if not requested:
            return list(available)

        invalid = [platform for platform in requested if platform not in available]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unsupported mock platform(s): {', '.join(invalid)}")
        return requested

    def _timeseries(self, daily_rows: list[dict[str, Any]], metric: str) -> list[dict[str, Any]]:
        return [{"date": row["date"], "value": int(row.get(metric, 0))} for row in daily_rows]

    def _resolve_date_window(
        self,
        profile: dict[str, Any],
        date_value: str | None,
        start_date: str | None,
        end_date: str | None,
        period: str | None,
    ) -> tuple[date, date]:
        if date_value:
            target = date.fromisoformat(date_value)
            return target, target

        if start_date or end_date:
            start = date.fromisoformat(start_date or profile["start_date"])
            end = date.fromisoformat(end_date or profile["end_date"])
            return start, end

        profile_end = date.fromisoformat(profile["end_date"])
        if period == "last_3_days":
            return profile_end - timedelta(days=2), profile_end
        if period == "last_week":
            return date.fromisoformat(profile["start_date"]), profile_end

        return date.fromisoformat(profile["start_date"]), profile_end

    def _filter_daily_metrics(
        self,
        daily_rows: list[dict[str, Any]],
        window_start: date,
        window_end: date,
    ) -> list[dict[str, Any]]:
        return [
            row
            for row in daily_rows
            if window_start <= date.fromisoformat(row["date"]) <= window_end
        ]

    def _find_post(self, request_id: str) -> dict[str, Any]:
        for post in self.data["posts"]:
            if post["request_id"] == request_id:
                return post
        raise HTTPException(status_code=404, detail=f"Mock post analytics not found for request_id: {request_id}")

    def _build_history(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        history: list[dict[str, Any]] = []
        for post in self.data["posts"]:
            for platform, platform_entry in post["platforms"].items():
                history.append(
                    {
                        "user_email": profile["user_email"],
                        "profile_username": post["profile_username"],
                        "platform": platform,
                        "media_type": post["media_type"],
                        "upload_timestamp": post["upload_timestamp"],
                        "success": platform_entry["success"],
                        "platform_post_id": platform_entry["platform_post_id"],
                        "post_url": platform_entry["post_url"],
                        "media_size_bytes": post["media_size_bytes"],
                        "post_title": post["post_title"],
                        "post_caption": post["post_caption"],
                        "is_async": post["is_async"],
                        "job_id": platform_entry["job_id"],
                        "dashboard": post["dashboard"],
                        "request_id": post["request_id"],
                        "request_total_platforms": len(post["platforms"]),
                    }
                )

        history.sort(key=lambda item: self._parse_datetime(item["upload_timestamp"]), reverse=True)
        return history

    def _parse_datetime(self, value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
