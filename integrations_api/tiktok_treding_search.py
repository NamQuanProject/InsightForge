# import requests
# import time
# from typing import List, Dict, Any


# # ==============================
# # SHARED PROCESSING LOGIC
# # ==============================
# def extract_video_features(item: Dict[str, Any]) -> Dict[str, Any]:
#     aweme = item.get("aweme_info", {})
#     stats = aweme.get("statistics", {})
#     author = aweme.get("author", {})
#     music = aweme.get("music", {})

#     return {
#         "video_id": aweme.get("aweme_id"),
#         "author_id": author.get("uid"),
#         "author_username": author.get("unique_id"),
#         "create_time": aweme.get("create_time"),

#         "views": stats.get("play_count", 0),
#         "likes": stats.get("digg_count", 0),
#         "comments": stats.get("comment_count", 0),
#         "shares": stats.get("share_count", 0),
#         "saves": stats.get("collect_count", 0),

#         "hashtags": [
#             h.get("hashtag_name")
#             for h in aweme.get("text_extra", [])
#             if h.get("type") == 1
#         ],

#         "sound_id": music.get("id"),
#         "sound_title": music.get("title"),
#         "sound_usage": music.get("user_count", 0),

#         "caption": aweme.get("desc"),
#         "region": aweme.get("region"),
#     }


# def extract_all_videos(data: Dict[str, Any]) -> List[Dict[str, Any]]:
#     return [extract_video_features(v) for v in data.get("data", [])]


# def add_trend_metrics(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     now = int(time.time())

#     for v in videos:
#         views = v["views"]
#         likes = v["likes"]
#         comments = v["comments"]
#         shares = v["shares"]

#         age_hours = max((now - v["create_time"]) / 3600, 1)

#         v["engagement_rate"] = (likes + comments + shares) / max(views, 1)
#         v["velocity"] = views / age_hours
#         v["virality"] = shares / max(views, 1)

#         v["trend_score"] = v["velocity"] * v["engagement_rate"]

#     return videos


# def rank_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     return sorted(videos, key=lambda x: x["trend_score"], reverse=True)


# def process_pipeline(data: Dict[str, Any]) -> List[Dict[str, Any]]:
#     videos = extract_all_videos(data)
#     videos = add_trend_metrics(videos)
#     return rank_videos(videos)


# # ==============================
# # 1. KEYWORD SEARCH
# # ==============================
# def fetch_by_keyword(
#     keyword: str,
#     token: str,
#     period: str = "1",
#     country: str = "vi",
#     sorting: str = "0",
#     match_exactly: bool = False,
# ) -> Dict[str, Any]:

#     url = "https://ensembledata.com/apis/tt/keyword/full-search"

#     params = {
#         "name": keyword,
#         "period": period,
#         "sorting": sorting,
#         "country": country,
#         "match_exactly": match_exactly,
#         "token": token,
#     }

#     res = requests.get(url, params=params, timeout=30)
#     res.raise_for_status()
#     return res.json()


# def get_trending_by_keyword(
#     keyword: str,
#     token: str,
#     top_k: int = 10,
# ) -> List[Dict[str, Any]]:

#     raw = fetch_by_keyword(keyword, token)
#     ranked = process_pipeline(raw)
#     return ranked[:top_k]


# # ==============================
# # 2. HASHTAG SEARCH
# # ==============================
# from typing import List, Dict, Any
# from datetime import datetime


# def normalize_hashtag_response(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
#     posts = raw.get("data", {}).get("posts", [])
#     results = []

#     for post in posts:
#         item = post.get("itemInfos", {})
#         author = post.get("authorInfos", {})
        
#         # Extract hashtags from caption
#         caption = item.get("text", "")
#         hashtags = [word[1:] for word in caption.split() if word.startswith("#")]

#         # Convert timestamp
#         ts = item.get("createTime")
#         created_at = (
#             datetime.fromtimestamp(int(ts)).isoformat()
#             if ts else None
#         )

#         results.append({
#             "video_id": item.get("id"),
#             "author_id": author.get("userId"),
#             "author_username": author.get("uniqueId"),
#             "author_nickname": author.get("nickName"),

#             "caption": caption,
#             "hashtags": hashtags,

#             "views": item.get("playCount"),
#             "likes": item.get("diggCount"),
#             "comments": item.get("commentCount"),
#             "shares": item.get("shareCount"),

#             "duration": item.get("video", {}).get("videoMeta", {}).get("duration"),
#             "width": item.get("video", {}).get("videoMeta", {}).get("width"),
#             "height": item.get("video", {}).get("videoMeta", {}).get("height"),

#             "video_url": (item.get("video", {}).get("urls") or [None])[0],
#             "cover_url": (item.get("covers") or [None])[0],

#             "created_at": created_at,

#             # optional extras
#             "music_name": post.get("musicInfos", {}).get("musicName"),
#             "verified": author.get("verified"),
#         })

#     return results


# def fetch_by_hashtag(
#     hashtag: str,
#     token: str,
#     days: int = 1,
#     max_cursor: int = 100,
#     remap_output: bool = True,
# ) -> Dict[str, Any]:

#     root = "https://ensembledata.com/apis"
#     endpoint = "/tt/hashtag/recent-posts"
#     url = root + endpoint
#     params = {
#         "name": hashtag,
#         "days": days,
#         "max_cursor": max_cursor,
#         "remap_output": str(remap_output).lower(),
#         "token": token,
#     }

#     res = requests.get(url, params=params)
#     res.raise_for_status()
#     return res.json()


# def get_trending_by_hashtag(
#     hashtag: str,
#     token: str,
#     top_k: int = 10,
# ) -> List[Dict[str, Any]]:

#     raw = fetch_by_hashtag(hashtag, token)
#     normalized = normalize_hashtag_response(raw)

#     ranked = process_pipeline(normalized)  # now clean input
#     return ranked[:top_k]


# # ==============================
# # USAGE EXAMPLE
# # ==============================

# if __name__ == "__main__":
#     TOKEN = "Zpwn5wkjp7AZcwu2"

#     # print("\n=== KEYWORD TRENDING ===")
#     # keyword_videos = get_trending_by_keyword(
#     #     keyword="fashion",
#     #     token=TOKEN,
#     #     top_k=5
#     # )

#     # for v in keyword_videos:
#     #     print({
#     #         "video_id": v["video_id"],
#     #         "views": v["views"],
#     #         "trend_score": round(v["trend_score"], 2),
#     #         "hashtags": v["hashtags"]
#     #     })

#     print("\n=== HASHTAG TRENDING ===")
#     hashtag_videos = get_trending_by_hashtag(
#         hashtag="treding",
#         token=TOKEN,
#         top_k=5
#     )

#     for v in hashtag_videos:
#         print({
#             "video_id": v["video_id"],
#             "views": v["views"],
#             "trend_score": round(v["trend_score"], 2),
#             "hashtags": v["hashtags"]
#         })
import requests
import time
from typing import List, Dict, Any
from datetime import datetime


# ==============================
# NORMALIZATION LAYER
# ==============================

def normalize_keyword_response(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize keyword API (aweme_info format)"""
    results = []

    for item in raw.get("data", []):
        aweme = item.get("aweme_info", {})
        stats = aweme.get("statistics", {})
        author = aweme.get("author", {})
        music = aweme.get("music", {})

        results.append({
            "video_id": aweme.get("aweme_id"),
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


def normalize_hashtag_response(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize hashtag API (itemInfos format)"""
    posts = raw.get("data", {}).get("posts", [])
    results = []

    for post in posts:
        item = post.get("itemInfos", {})
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

def add_trend_metrics(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def rank_videos(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(videos, key=lambda x: x.get("trend_score", 0), reverse=True)


def process_pipeline(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    videos = add_trend_metrics(videos)
    return rank_videos(videos)


# ==============================
# API CALLS
# ==============================

def fetch_by_keyword(
    keyword: str,
    token: str,
    period: str = "1",
    country: str = "vi",
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
        "token": token,
    }

    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    return res.json()


def fetch_by_hashtag(
    hashtag: str,
    token: str,
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
        "token": token,
    }

    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    return res.json()


# ==============================
# PUBLIC FUNCTIONS (ENTRYPOINT)
# ==============================

def get_trending_by_keyword(
    keyword: str,
    token: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:

    raw = fetch_by_keyword(keyword, token)
    normalized = normalize_keyword_response(raw)

    ranked = process_pipeline(normalized)
    return ranked[:top_k]


def get_trending_by_hashtag(
    hashtag: str,
    token: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:

    raw = fetch_by_hashtag(hashtag, token)
    normalized = normalize_hashtag_response(raw)

    ranked = process_pipeline(normalized)
    return ranked[:top_k]


# ==============================
# USAGE EXAMPLE
# ==============================

if __name__ == "__main__":
    TOKEN = "Zpwn5wkjp7AZcwu2"

    print("\n=== HASHTAG TRENDING ===")
    hashtag_videos = get_trending_by_hashtag(
        hashtag="trending",
        token=TOKEN,
        top_k=5
    )

    for v in hashtag_videos:
        print({
            "video_id": v["video_id"],
            "views": v["views"],
            "trend_score": round(v["trend_score"], 2),
            "hashtags": v["hashtags"]
        })

    # print("\n=== KEYWORD TRENDING ===")
    # keyword_videos = get_trending_by_keyword(
    #     keyword="fashion",
    #     token=TOKEN,
    #     top_k=5
    # )

    # for v in keyword_videos:
    #     print({
    #         "video_id": v["video_id"],
    #         "views": v["views"],
    #         "trend_score": round(v["trend_score"], 2),
    #         "hashtags": v["hashtags"]
    #     })