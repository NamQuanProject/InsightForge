import requests
import requests


def full_hashtag_search(
    name: str,
    days: int,
    remap_output: bool = True,
    max_cursor: int = 10000,
    token: str = "kagJdacF9n25MtKD",
):
    url = "https://api.tiktokapis.com/v2/research/hashtag/full_search/"
    params = {
        "name": name,
        "days": days,
        "remap_output": str(remap_output).lower(),
        "max_cursor": max_cursor,
        "token": token,
    }
    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        return {"error": "HTTP_ERROR", "message": str(e), "status": res.status_code}
    except Exception as e:
        return {"error": "UNKNOWN_ERROR", "message": str(e)}
    
def full_treding_search(
    days: int,
    remap_output: bool = True,
    max_cursor: int = 30,
    token: str = "kagJdacF9n25MtKD",
    name: str = "viral"
):
    url = "https://api.tiktokapis.com/v2/research/hashtag/full_search/"
    params = {
        "name": name,
        "days": days,
        "remap_output": str(remap_output).lower(),
        "max_cursor": max_cursor,
        "token": token,
    }
    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        return {"error": "HTTP_ERROR", "message": str(e), "status": res.status_code}
    except Exception as e:
        return {"error": "UNKNOWN_ERROR", "message": str(e)}

def extract_video_features(item):
    aweme = item.get("aweme_info", {})
    stats = aweme.get("statistics", {})
    author = aweme.get("author", {})
    music = aweme.get("music", {})

    return {
        # identifiers
        "video_id": aweme.get("aweme_id"),
        "author_id": author.get("uid"),
        "author_username": author.get("unique_id"),

        # time
        "create_time": aweme.get("create_time"),

        # engagement
        "views": stats.get("play_count", 0),
        "likes": stats.get("digg_count", 0),
        "comments": stats.get("comment_count", 0),
        "shares": stats.get("share_count", 0),
        "saves": stats.get("collect_count", 0),

        # hashtags
        "hashtags": [
            h.get("hashtag_name")
            for h in aweme.get("text_extra", [])
            if h.get("type") == 1
        ],

        # sound
        "sound_id": music.get("id"),
        "sound_title": music.get("title"),
        "sound_usage": music.get("user_count", 0),

        # content
        "caption": aweme.get("desc"),

        # region
        "region": aweme.get("region"),
    }


def extract_all_videos(data):
    videos = data.get("data", [])
    return [extract_video_features(v) for v in videos]

import time


def add_trend_metrics(videos):
    now = int(time.time())

    for v in videos:
        views = v["views"]
        likes = v["likes"]
        comments = v["comments"]
        shares = v["shares"]

        age_hours = max((now - v["create_time"]) / 3600, 1)

        # metrics
        v["engagement_rate"] = (likes + comments + shares) / max(views, 1)
        v["velocity"] = views / age_hours
        v["virality"] = shares / max(views, 1)

        # combined trend score
        v["trend_score"] = v["velocity"] * v["engagement_rate"]

    return videos


def get_trending_videos(res_json):
    videos = extract_all_videos(res_json)
    videos = add_trend_metrics(videos)

    # sort by trend score
    videos = sorted(videos, key=lambda x: x["trend_score"], reverse=True)

    return videos

import requests
import time


def fetch_tiktok_trending(
    keyword: str,
    token: str,
    period: str = "1",
    country: str = "vi",
    sorting: str = "0",
    match_exactly: bool = False,
):
    root = "https://ensembledata.com/apis"
    endpoint = "/tt/keyword/full-search"

    params = {
        "name": keyword,
        "period": period,
        "sorting": sorting,
        "country": country,
        "match_exactly": match_exactly,
        "token": token,
    }

    res = requests.get(root + endpoint, params=params, timeout=30)
    res.raise_for_status()
    return res.json()

def process_tiktok_data(data):
    now = int(time.time())
    results = []

    for item in data.get("data", []):
        aweme = item.get("aweme_info", {})
        stats = aweme.get("statistics", {})
        author = aweme.get("author", {})
        music = aweme.get("music", {})

        views = stats.get("play_count", 0)
        likes = stats.get("digg_count", 0)
        comments = stats.get("comment_count", 0)
        shares = stats.get("share_count", 0)

        create_time = aweme.get("create_time", now)
        age_hours = max((now - create_time) / 3600, 1)

        # compute metrics
        engagement_rate = (likes + comments + shares) / max(views, 1)
        velocity = views / age_hours
        trend_score = velocity * engagement_rate

        video = {
            "video_id": aweme.get("aweme_id"),
            "author": author.get("unique_id"),
            "create_time": create_time,

            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,

            "engagement_rate": engagement_rate,
            "velocity": velocity,
            "trend_score": trend_score,

            "hashtags": [
                h.get("hashtag_name")
                for h in aweme.get("text_extra", [])
                if h.get("type") == 1
            ],

            "sound_id": music.get("id"),
            "sound_usage": music.get("user_count", 0),

            "caption": aweme.get("desc"),
            "region": aweme.get("region"),
        }

        results.append(video)

    # sort by trend score
    results.sort(key=lambda x: x["trend_score"], reverse=True)

    return results

def get_tiktok_trending(
    keyword: str,
    token: str,
    top_k: int = 10,
    country: str = "vi"
):
    raw_data = fetch_tiktok_trending(
        keyword=keyword,
        token=token,
        country=country
    )

    processed = process_tiktok_data(raw_data)

    return processed[:top_k]


if __name__ == "__main__":
    TOKEN = "kagJdacF9n25MtKD"

    top_videos = get_tiktok_trending(
        keyword="music",
        token=TOKEN,
        top_k=10
    )

    for v in top_videos:
        print({
            "video_id": v["video_id"],
            "views": v["views"],
            "engagement_rate": round(v["engagement_rate"], 4),
            "trend_score": round(v["trend_score"], 2),
            "hashtags": v["hashtags"]
        })