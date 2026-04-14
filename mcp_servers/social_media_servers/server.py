import os
from dotenv import load_dotenv
from typing import Optional

from mcp.server.fastmcp import FastMCP
from integrations_api.thread_trending import ThreadsTrendAnalyzer
from integrations_api.tiktok_trending_search import TiktokTrend
from mcp_servers.social_media_servers.helpers import _format_threads_results, _format_tiktok_results

load_dotenv()
ENSEMBLE_TOKEN = os.getenv("ENSEMBLEDATA_API_KEY", "")
threads_client = ThreadsTrendAnalyzer(token=ENSEMBLE_TOKEN)
tiktok_client = TiktokTrend(token=ENSEMBLE_TOKEN)

mcp = FastMCP("SocialMediaTrend")

# ─────────────────────────────────────────────
# THREADS TOOLS
# ─────────────────────────────────────────────
@mcp.tool()
def threads_search_keyword(
    keyword: str,
    top_posts: int = 2,
    top_comments: int = 1,
    sorting: str = "0",
) -> list[dict]:
    """
    Search Threads for posts matching a keyword and return the top trending posts
    together with their most-engaged comments.

    Parameters
    ----------
    keyword     : The search term (e.g. "AI", "chuyện lạ", "fashion").
    top_posts   : How many posts to return (default 5, max ~10).
    top_comments: How many top comments to include per post (default 3).
    sorting     : Post sort order.
                  "0" = Top / most relevant (default).
                  "1" = Most recent.
    """
    raw_results = threads_client.analyze_keyword(
        keyword=keyword,
        top_posts=max(1, min(top_posts, 2)),
        top_comments=max(0, min(top_comments, 1)),
    )
    return _format_threads_results(raw_results)

# ─────────────────────────────────────────────
# TIKTOK TOOLS
# ─────────────────────────────────────────────

@mcp.tool()
def tiktok_search_keyword(
    keyword: str,
    top_k: int = 3,
    period: str = "1",
    country: str = "VN",
    sorting: str = "0",
    match_exactly: bool = False,
) -> list[dict]:
    """
    Search TikTok for trending videos matching a keyword.
    Videos are ranked by a composite trend score (velocity + like-rate + virality).

    Parameters
    ----------
    keyword      : Search term (e.g. "fashion", "AI", "du lịch").
    top_k        : Number of top trending videos to return (default 10).
    period       : Time window for the search:
                   "1"  = Last 24 hours
                   "7"  = Last 7 days
                   "30" = Last 30 days
    country      : ISO 3166-1 alpha-2 country code to filter results (default "VN").
                   Pass "" for worldwide results.
    sorting      : "0" = Relevance (default) | "1" = Most liked.
    match_exactly: If True, only return posts containing the exact keyword phrase.
    """
    raw = tiktok_client._fetch_by_keyword(
        keyword=keyword,
        period=period,
        country=country,
        sorting=sorting,
        match_exactly=match_exactly,
    )
    if raw.get("error"):
        return [{"error": raw.get("error"), "message": raw.get("message", "")}]
    normalized = tiktok_client._normalize_keyword_response(raw)
    ranked = tiktok_client._process_pipeline(normalized)
    return _format_tiktok_results(ranked[: max(1, min(top_k, 3))])


@mcp.tool()
def tiktok_search_hashtag(
    hashtag: str,
    top_k: int = 3,
    days: int = 3,
) -> list[dict]:
    """
    Fetch recent TikTok posts for a hashtag and rank them by trend score.
    If there are no given keywords, use hashtag "trending" to find trending keywords for further search.

    Parameters
    ----------
    hashtag : Hashtag name WITHOUT the leading "#" (e.g. "trending").
    top_k   : Number of top trending videos to return (default 10).
    days    : Look-back window in days (default 7).
    """
    raw = tiktok_client._fetch_by_hashtag(hashtag=hashtag, days=max(1, min(days, 3)))
    if raw.get("error"):
        return [{"error": raw.get("error"), "message": raw.get("message", "")}]
    normalized = tiktok_client._normalize_hashtag_response(raw)
    ranked = tiktok_client._process_pipeline(normalized)
    return _format_tiktok_results(ranked[: max(1, min(top_k, 3))])


# @mcp.tool()
# def tiktok_compare_keywords(
#     keywords: list[str],
#     top_k: int = 5,
#     country: str = "VN",
#     period: str = "1",
# ) -> dict[str, list[dict]]:
#     """
#     Compare multiple TikTok keywords side-by-side.
#     Returns a mapping of keyword → top trending videos so an agent can
#     identify which keyword is generating the most traction right now.

#     Parameters
#     ----------
#     keywords : List of search terms to compare (e.g. ["AI", "ChatGPT", "Gemini"]).
#     top_k    : Videos to return per keyword (default 5).
#     country  : Country filter (default "VN"). Pass "" for worldwide.
#     period   : Time window — "1" (24 h) | "7" (7 days) | "30" (30 days).
#     """
#     comparison: dict[str, list[dict]] = {}

#     for kw in keywords:
#         try:
#             raw = tiktok_client._fetch_by_keyword(
#                 keyword=kw,
#                 period=period,
#                 country=country,
#             )
#             normalized = tiktok_client._normalize_keyword_response(raw)
#             ranked = tiktok_client._process_pipeline(normalized)
#             comparison[kw] = _format_tiktok_results(ranked[:top_k])
#         except Exception as e:
#             comparison[kw] = [{"error": str(e)}]

#     return comparison


# @mcp.tool()
# def tiktok_compare_hashtags(
#     hashtags: list[str],
#     top_k: int = 5,
#     days: int = 7,
# ) -> dict[str, list[dict]]:
#     """
#     Compare multiple TikTok hashtags side-by-side.
#     Returns a mapping of hashtag → top trending videos.

#     Parameters
#     ----------
#     hashtags : List of hashtags WITHOUT "#" (e.g. ["trending", "xuhuong", "viral"]).
#     top_k    : Videos to return per hashtag (default 5).
#     days     : Look-back window in days (default 7).
#     """
#     comparison: dict[str, list[dict]] = {}

#     for tag in hashtags:
#         try:
#             raw = tiktok_client._fetch_by_hashtag(hashtag=tag, days=days)
#             normalized = tiktok_client._normalize_hashtag_response(raw)
#             ranked = tiktok_client._process_pipeline(normalized)
#             comparison[tag] = _format_tiktok_results(ranked[:top_k])
#         except Exception as e:
#             comparison[tag] = [{"error": str(e)}]

#     return comparison


# ─────────────────────────────────────────────
# CROSS-PLATFORM TOOL
# ─────────────────────────────────────────────
@mcp.tool()
def cross_platform_trend(
    keyword: str,
    tiktok_top_k: int = 2,
    threads_top_posts: int = 1,
    threads_top_comments: int = 1,
    tiktok_country: str = "VN",
    tiktok_period: str = "1",
) -> dict:
    """
    Pull trend signals for a keyword from BOTH TikTok and Threads in one call.
    Useful for understanding whether a topic is gaining traction across platforms.

    Parameters
    ----------
    keyword              : Topic to research (e.g. "AI", "thời trang", "du lịch").
    tiktok_top_k         : TikTok videos to return (default 5).
    threads_top_posts    : Threads posts to return (default 5).
    threads_top_comments : Top comments per Threads post (default 3).
    tiktok_country       : ISO country code for TikTok filter (default "VN").
    tiktok_period        : TikTok look-back — "1" (24 h) | "7" (7 d) | "30" (30 d).

    Returns
    -------
    A dict with keys:
      "tiktok"  → list of ranked TikTok videos
      "threads" → list of Threads posts with top comments
    """
    # TikTok
    try:
        raw_tt = tiktok_client._fetch_by_keyword(
            keyword=keyword,
            period=tiktok_period,
            country=tiktok_country,
        )
        if raw_tt.get("error"):
            raise RuntimeError(raw_tt.get("message", raw_tt["error"]))
        tiktok_results = _format_tiktok_results(
            tiktok_client._process_pipeline(
                tiktok_client._normalize_keyword_response(raw_tt)
            )[: max(1, min(tiktok_top_k, 2))]
        )
    except Exception as e:
        tiktok_results = [{"error": str(e)}]

    # Threads
    try:
        raw_th = threads_client.analyze_keyword(
            keyword=keyword,
            top_posts=max(1, min(threads_top_posts, 1)),
            top_comments=max(0, min(threads_top_comments, 1)),
        )
        threads_results = _format_threads_results(raw_th)
    except Exception as e:
        threads_results = [{"error": str(e)}]

    return {
        "tiktok": tiktok_results,
        "threads": threads_results,
    }
# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
