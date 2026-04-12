import asyncio
from mcp_servers.posting_servers.mcp_server import upload_text, validate_api_key, get_user_profile, upload_photos

async def main():
    # Test API key first
    res = await validate_api_key()
    print("API KEY TEST:", res)


    res = await get_user_profile()
    print("CURRENT_USER_TEST", res)


#     @mcp.tool()
# async def upload_text(
#     user: str,
#     platform: list[str],
#     title: str,
#     description: Optional[str] = None,
#     scheduled_date: Optional[str] = None,
#     first_comment: Optional[str] = None,
#     link_url: Optional[str] = None,
#     subreddit: Optional[str] = None,
# ) -> dict:

    
    res = await upload_photos(
        user="blhoang23",
        platform=["instagram"],
        photos = ["sample_data/image.png"],
        title="Test Post from API",
        description="This is a test post created via the Upload-Post API.",
    )


    print("UPLOAD_TEXT_TEST", res)





if __name__ == "__main__":
    asyncio.run(main())