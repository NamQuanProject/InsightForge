import asyncio
from mcp_servers.posting_servers.mcp_server import upload_text, validate_api_key, get_user_profile

async def main():
    # Test API key first
    res = await validate_api_key()
    print("API KEY TEST:", res)


    res = await get_user_profile()
    print("CURRENT_USER_TEST", res)



    





if __name__ == "__main__":
    asyncio.run(main())