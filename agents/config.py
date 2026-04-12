TOOLS = [
    {
        "name": "google_trends_search",
        "description": "Search latest trending topics",
        "input_schema": {"query": "string", "geo": "string"},
    },
    {
        "name": "trend_analysis",
        "description": "Analyze trends and extract insights",
        "input_schema": {"data": "string"},
    },
    {
        "name": "upload_tiktok_post",
        "description": "Upload a video post to TikTok",
        "input_schema": {
            "video_path": "string",
            "title": "string",
            "description": "string",
            "tags": "array",
            "visibility": "string",
        },
    },
    {
        "name": "upload_thread_post",
        "description": "Create a text post on Threads (Meta)",
        "input_schema": {"text": "string", "image_urls": "array"},
    },
    {
        "name": "schedule_post",
        "description": "Schedule a post for later publishing",
        "input_schema": {
            "platform": "string",
            "content": "string",
            "scheduled_time": "string",
            "media_paths": "array",
            "hashtags": "array",
        },
    },
    {
        "name": "create_post_draft",
        "description": "Create a post draft for human review before publishing",
        "input_schema": {
            "content": "string",
            "platform": "string",
            "suggested_hashtags": "array",
        },
    },
    {
        "name": "publish_draft",
        "description": "Publish a draft that has been approved by human",
        "input_schema": {
            "draft_id": "string",
            "approved": "boolean",
            "modifications": "string",
        },
    },
    {
        "name": "get_post_status",
        "description": "Check the status of a published or scheduled post",
        "input_schema": {"post_id": "string", "platform": "string"},
    },
    {
        "name": "cross_post",
        "description": "Publish the same content to multiple platforms simultaneously",
        "input_schema": {
            "content": "string",
            "platforms": "array",
            "media_paths": "array",
            "hashtags": "array",
            "auto_tag": "boolean",
        },
    },
]
