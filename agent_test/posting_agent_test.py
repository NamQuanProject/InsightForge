import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def run():
    print("=" * 50)
    print("Posting Agent - Simple Prompt Mode")
    print("=" * 50)
    print()
    print("Examples:")
    print("  • upload photos at /path/to/folder to instagram")
    print("  • post 'Hello world' to facebook")
    print("  • upload video /path/video.mp4 to tiktok")
    print()

    from agents.posting_agent.agent import PostingAgent

    agent = PostingAgent(api_key=os.getenv("GOOGLE_API_KEY"))
    await agent.initialize()

    print("\n📝 Enter your prompt:")
    prompt = input("> ").strip()

    if not prompt:
        print("Please enter a prompt!")
        return

    print("\n⏳ Processing...")

    result = await agent.process_prompt(prompt)

    if result.get("error"):
        print(f"\n❌ Error: {result.get('error')}")
        return

    print("\n" + "=" * 50)
    print("📋 POST PREVIEW")
    print("=" * 50)
    print(result.get("preview"))

    print("\n" + "=" * 50)
    user_input = input("\n✅ Execute this? (yes/no): ").strip().lower()
    print("=" * 50)

    if user_input in ["yes", "y", "ok", "go", "post", ""]:
        print("\n⏳ Executing...")

        result = await agent.execute_post(result.get("post_data"))

        if result.get("success"):
            print("\n✅ POSTED SUCCESSFULLY!")
            if result.get("response"):
                print(f"\n{result.get('response')}")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
    else:
        print("\n🚫 Cancelled.")


if __name__ == "__main__":
    asyncio.run(run())
