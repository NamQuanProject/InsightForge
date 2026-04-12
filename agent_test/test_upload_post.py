import asyncio
from mcp_servers.posting_servers.mcp_server import upload_text, validate_api_key, get_user_profile, upload_photos, get_upload_history, get_media_list, get_analytics

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

    
    # res = await upload_photos(
    #     user="blhoang23",
    #     platform=["instagram"],
    #     photos = ["sample_data/image.png"],
    #     title="Test Post from API",
    #     description="This is a test post created via the Upload-Post API.",
    # )

    # get_upload_history 

    # print("UPLOAD_TEXT_TEST", res)

    # res = await get_upload_history()
    # print("UPLOAD_HISTORY_TEST", res)


    # res = await get_media_list(user="blhoang23", platform="instagram")
    # print("MEDIA_LIST_TEST", res)


    res = await get_analytics(profile_username="blhoang23", platform="instagram")
    print("ANALYTICS_TEST", res)


    
    





if __name__ == "__main__":
    asyncio.run(main())