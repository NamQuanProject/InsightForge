import re
from typing import Optional


def parse_hashtags(text: str) -> list[str]:
    """Extract hashtags from text."""
    return [tag.lower().strip("#") for tag in re.findall(r"#\w+", text)]


def parse_scheduled_time(time_str: str) -> Optional[str]:
    """Parse and validate scheduled time string."""
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, AttributeError):
        return None


def truncate_content(content: str, max_length: int = 500) -> str:
    """Truncate content to max length with ellipsis."""
    if len(content) <= max_length:
        return content
    return content[: max_length - 3] + "..."


def format_post_preview(
    content: str,
    platform: str,
    hashtags: list[str],
    media_count: int = 0,
) -> str:
    """Format a post preview for human review."""
    platform_emoji = {
        "tiktok": "TikTok",
        "threads": "Threads",
        "all": "All Platforms",
    }.get(platform.lower(), platform)

    preview = f"""
📝 **Post Preview**

**Platform:** {platform_emoji}
**Content:**
{content}

**Hashtags:** {", ".join(["#" + h if not h.startswith("#") else h for h in hashtags]) or "None"}
**Media:** {media_count} file(s) attached

---
⏳ Awaiting your approval...
"""
    return preview.strip()


def validate_platform(platform: str) -> bool:
    """Validate if platform is supported."""
    valid_platforms = ["tiktok", "threads", "all"]
    return platform.lower() in valid_platforms


def validate_visibility(visibility: str) -> bool:
    """Validate post visibility setting."""
    valid_settings = ["public", "private", "friends"]
    return visibility.lower() in valid_settings
