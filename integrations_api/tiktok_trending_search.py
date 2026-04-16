import requests
import time
from typing import List, Dict, Any
from datetime import datetime

class TiktokTrend:
    def __init__(self, token: str):
        self.token = token
    # ==============================
    # NORMALIZATION LAYER
    # ==============================

    def _normalize_keyword_response(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize keyword API (aweme_info format)"""
        results = []

        for item in raw.get("data", []):
            aweme = item.get("aweme_info", {})
            stats = aweme.get("statistics", {})
            author = aweme.get("author", {})
            music = aweme.get("music", {})

            results.append({
                "video_id": aweme.get("aweme_id"),
                "video_url": aweme.get("video", {}).get("download_addr", {}).get("url_list", []),
                "author_id": author.get("uid"),
                "author_username": author.get("unique_id"),

                "caption": aweme.get("desc"),
                "hashtags": [
                    h.get("hashtag_name")
                    for h in aweme.get("text_extra", [])
                    if h.get("type") == 1
                ],

                "views": stats.get("play_count", 0),
                "likes": stats.get("digg_count", 0),
                "comments": stats.get("comment_count", 0),
                "shares": stats.get("share_count", 0),

                "create_time": aweme.get("create_time"),  # timestamp

                "sound_id": music.get("id"),
                "sound_title": music.get("title"),
            })

        return results

    def _normalize_hashtag_response(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize hashtag API (itemInfos format)"""
        posts = raw.get("data", {}).get("posts", [])
        results = []

        for post in posts:
            item = post.get("itemInfos", {})
            url_list = item.get("video", {}).get("urls", [])
            video_urls = url_list[-1] if url_list else None
            author = post.get("authorInfos", {})

            caption = item.get("text", "")
            hashtags = list(set([w[1:] for w in caption.split() if w.startswith("#")]))

            ts = item.get("createTime")
            created_at = (
                datetime.fromtimestamp(int(ts)).isoformat()
                if ts else None
            )

            results.append({
                "video_id": item.get("id"),
                "video_url": video_urls,
                "author_id": author.get("userId"),
                "author_username": author.get("uniqueId"),

                "caption": caption,
                "hashtags": hashtags,

                "views": item.get("playCount", 0),
                "likes": item.get("diggCount", 0),
                "comments": item.get("commentCount", 0),
                "shares": item.get("shareCount", 0),

                "created_at": created_at,  # ISO string
            })

        return results

    # ==============================
    # TREND PIPELINE
    # ==============================

    def _add_trend_metrics(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        now = time.time()

        for v in videos:
            views = v.get("views", 0)
            likes = v.get("likes", 0)
            comments = v.get("comments", 0)
            shares = v.get("shares", 0)

            # Handle timestamp formats
            if v.get("create_time"):
                age_hours = max((now - v["create_time"]) / 3600, 1)
            elif v.get("created_at"):
                try:
                    ts = datetime.fromisoformat(v["created_at"]).timestamp()
                    age_hours = max((now - ts) / 3600, 1)
                except:
                    age_hours = 24
            else:
                age_hours = 24

            engagement = likes + comments + shares

            v["engagement_rate"] = engagement / max(views, 1)
            v["velocity"] = views / age_hours
            v["virality"] = shares / max(views, 1)

            # 🔥 Improved scoring
            v["trend_score"] = (
                0.5 * v["velocity"] +
                0.3 * (likes / max(views, 1)) +
                0.2 * (shares / max(views, 1))
            )

        return videos

    def _rank_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(videos, key=lambda x: x.get("trend_score", 0), reverse=True)

    def _process_pipeline(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        videos = self._add_trend_metrics(videos)
        return self._rank_videos(videos)

    # ==============================
    # API CALLS
    # ==============================

    def _fetch_by_keyword(
        self,
        keyword: str,
        period: str = "1",
        country: str = "VN",
        sorting: str = "0",
        match_exactly: bool = False,
    ) -> Dict[str, Any]:

        url = "https://ensembledata.com/apis/tt/keyword/full-search"

        params = {
            "name": keyword,
            "period": period,
            "sorting": sorting,
            "country": country,
            "match_exactly": match_exactly,
            "token": self.token,
        }

        res = requests.get(url, params=params, timeout=60)
        res.raise_for_status()
        return res.json()

    def _fetch_by_hashtag(
        self,
        hashtag: str,
        days: int = 7,
        max_cursor: int = 100,
        remap_output: bool = True,
    ) -> Dict[str, Any]:

        url = "https://ensembledata.com/apis/tt/hashtag/recent-posts"

        params = {
            "name": hashtag,
            "days": days,
            "max_cursor": max_cursor,
            "remap_output": str(remap_output).lower(),
            "token": self.token,
        }

        res = requests.get(url, params=params, timeout=60)
        res.raise_for_status()
        return res.json()

    # ==============================
    # PUBLIC METHODS (ENTRYPOINT)
    # ==============================

    def get_trending_by_keyword(
        self,
        keyword: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:

        raw = self._fetch_by_keyword(keyword)
        normalized = self._normalize_keyword_response(raw)

        ranked = self._process_pipeline(normalized)
        return ranked[:top_k]

    def get_trending_by_hashtag(
        self,
        hashtag: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:

        raw = self._fetch_by_hashtag(hashtag)
        normalized = self._normalize_hashtag_response(raw)

        ranked = self._process_pipeline(normalized)
        return ranked[:top_k]


# ==============================
# USAGE EXAMPLE
# ==============================

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()
    TOKEN = os.getenv("ENSEMBLE_TOKEN", "")
    tiktok_trend = TiktokTrend(TOKEN)

    print("\n=== HASHTAG TRENDING ===")
    hashtag_videos = tiktok_trend.get_trending_by_hashtag(
        hashtag="trending",
        top_k=5
    )

    for v in hashtag_videos:
        print({
            "video_id": v["video_id"],
            "video_url": v["video_url"],
            "views": v["views"],
            "trend_score": round(v["trend_score"], 2),
            "hashtags": v["hashtags"]
        })

    print("\n=== KEYWORD TRENDING ===")
    keyword_videos = tiktok_trend.get_trending_by_keyword(
        keyword="fashion",
        top_k=5
    )

    for v in keyword_videos:
        print({
            "video_id": v["video_id"],
            "video_url": v["video_url"],
            "views": v["views"],
            "trend_score": round(v["trend_score"], 2),
            "hashtags": v["hashtags"]
        })
