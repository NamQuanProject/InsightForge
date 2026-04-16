#!/usr/bin/env python3
"""Test script to verify MCP server async fixes"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


async def test_mcp_server_direct():
    """Test MCP server tools directly"""
    print("\n" + "=" * 60)
    print("TEST: MCP Server Direct Tool Test")
    print("=" * 60)

    from mcp_servers.posting_servers.mcp_server import (
        get_user_profile,
        get_upload_history,
        image_rag,
    )

    try:
        print("\n--- Testing get_user_profile ---")
        result = await get_user_profile()
        print(f"✅ get_user_profile: {str(result)[:100]}...")

        print("\n--- Testing get_upload_history ---")
        result = await get_upload_history()
        print(f"✅ get_upload_history: {str(result)[:100]}...")

        print("\n--- Testing image_rag ---")
        result = await image_rag("test query")
        print(f"✅ image_rag: {str(result)[:100]}...")

        print("\n✅ All direct tool tests passed!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_posting_agent():
    """Test the PostingAgent with fixed async tools"""
    print("\n" + "=" * 60)
    print("TEST: PostingAgent Integration Test")
    print("=" * 60)

    try:
        from agents.posting_agent.agent import PostingAgent

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return False

        agent = PostingAgent(api_key=api_key)
        await agent.initialize()

        print("\n--- Testing agent chat (read-only) ---")
        config, result = await agent.chat("Show me my upload history")

        print(f"✅ Agent chat completed successfully")
        print(f"   Result type: {type(result)}")

        if isinstance(result, dict) and "messages" in result:
            print(f"   Last message: {str(result['messages'][-1])[:100]}...")
        elif hasattr(result, "interrupts"):
            print(f"   Interrupts: {result.interrupts}")

        await agent.cleanup()
        print("\n✅ PostingAgent test passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MCP SERVER ASYNC FIX TEST SUITE")
    print("=" * 60)

    results = []

    print("\n📋 Running MCP Server Direct Tests...")
    results.append(await test_mcp_server_direct())

    print("\n📋 Running PostingAgent Tests...")
    results.append(await test_posting_agent())

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")

    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
