def _format_threads_results(results: list) -> list[dict]:
    """
    Flatten the nested analyze_keyword output into a clean, serialisable list.
    Each entry contains post metadata + its top comments.
    """
    formatted = []
    for item in results:
        post = item.get("post", {})
        top_comments = item.get("top_comments", [])
        total_comments = item.get("total_comments", 0)

        formatted.append({
            "post_url": post.get("post_url"),
            "username": post.get("username"),
            "is_verified": post.get("is_verified"),
            "text": post.get("text"),
            "likes": post.get("likes"),
            "total_comments": total_comments,
            "top_comments": [
                {
                    "username": c.get("username"),
                    "text": c.get("text"),
                    "likes": c.get("likes"),
                    "reply_count": c.get("reply_count"),
                }
                for c in top_comments
            ],
        })

    return formatted

def _format_tiktok_results(videos: list) -> list[dict]:
    """
    Reduce the full TikTok video dict to the fields most useful for trend analysis.
    """
    formatted = []
    for v in videos:
        formatted.append({
            "video_id": v.get("video_id"),
            "video_url": v.get("video_url"),
            "author_username": v.get("author_username"),
            "caption": v.get("caption"),
            "hashtags": v.get("hashtags", []),
            "views": v.get("views", 0),
            "likes": v.get("likes", 0),
            "comments": v.get("comments", 0),
            "shares": v.get("shares", 0),
            "trend_score": round(v.get("trend_score", 0), 4),
            "velocity": round(v.get("velocity", 0), 4),
            "engagement_rate": round(v.get("engagement_rate", 0), 4),
            "virality": round(v.get("virality", 0), 4),
        })
    return formatted