import asyncio
import os
from dotenv import load_dotenv
from a2a.client import A2AClient

load_dotenv()


async def test_direct_agent():
    """Test the agent directly (unit test)."""
    print("\n" + "=" * 60)
    print("TEST 1: Direct Agent Test")
    print("=" * 60)

    from agents.posting_agent.agent import PostingAgent

    agent = PostingAgent(api_key=os.getenv("GOOGLE_API_KEY"))
    await agent.initialize()

    test_cases = [
        "Show me my upload history",
        "What's my user profile?",
        "Validate my API key",
    ]

    for i, user_input in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {user_input} ---")
        config, result = await agent.chat(user_input)

        if hasattr(result, "interrupts") and result.interrupts:
            print(f"⏸️  Interrupt triggered (expected for upload actions)")
            print(f"    Interrupt value: {result.interrupts[0].value}")
        else:
            messages = result.get("messages", []) if isinstance(result, dict) else []
            if messages:
                print(f"Response: {messages[-1].content[:200]}...")
            else:
                print(f"Result: {result}")

    await agent.cleanup()
    print("\n✅ Direct agent test completed!")


async def test_with_approval_workflow():
    """Test the HumanInTheLoop approval workflow."""
    print("\n" + "=" * 60)
    print("TEST 2: HumanInTheLoop Approval Workflow")
    print("=" * 60)

    from agents.posting_agent.agent import PostingAgent

    agent = PostingAgent(api_key=os.getenv("GOOGLE_API_KEY"))
    await agent.initialize()

    print("\n--- Testing upload_photos trigger ---")
    user_input = "upload photos at sample_data/image.png with username blhoang23 to instagram with description 'Test post from API'"

    config, result = await agent.chat(user_input)

    if hasattr(result, "interrupts") and result.interrupts:
        print("✅ Interrupt triggered as expected!")
        interrupt = result.interrupts[0]
        interrupt_value = interrupt.value

        print(f"\nAction requests: {interrupt_value.get('action_requests', [])}")
        print(f"Review configs: {interrupt_value.get('review_configs', [])}")

        print("\n--- Resuming with approval ---")
        decisions = [{"type": "approve"}]
        resume_result = await agent.resume(config=config, decisions=decisions)

        messages = (
            resume_result.get("messages", []) if isinstance(resume_result, dict) else []
        )
        if messages:
            print(f"Final response: {messages[-1].content[:300]}...")
    else:
        print("⚠️  No interrupt triggered (tool may not have been called)")
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if messages:
            print(f"Response: {messages[-1].content[:300]}...")

    await agent.cleanup()
    print("\n✅ Approval workflow test completed!")


async def test_a2a_server():
    """Test the A2A server endpoints."""
    print("\n" + "=" * 60)
    print("TEST 3: A2A Server Integration Test")
    print("=" * 60)

    import httpx

    base_url = "http://localhost:5000/"
    card_url = base_url + ".well-known/agent.json"
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        
        client = A2AClient(url=base_url, httpx_client=httpx_client)
        print(client)
        msg = "Show me my upload history"



        response = await client.send_message(msg)
        # print(f"<<< {response}")

        # print("\n✅ A2A server test completed!")



async def test_executor_parse():
    """Test the executor input parsing."""
    print("\n" + "=" * 60)
    print("TEST 5: Executor Parse Test")
    print("=" * 60)

    from agents.posting_agent.executor import PostingAgentExecutor

    executor = PostingAgentExecutor()

    test_cases = [
        ("Show my history", {"action": "chat"}),
        ("approve", {"action": "approve"}),
        ("reject draft_123", {"action": "reject", "reason": None}),
        (
            "reject draft_456 because typo",
            {"action": "reject", "reason": "because typo"},
        ),
        ("resume", {"action": "resume"}),
        ("list drafts", {"action": "list"}),
    ]

    for user_input, expected in test_cases:
        result = executor._parse_input(user_input)
        status = "✅" if result["action"] == expected["action"] else "❌"
        print(f"{status} '{user_input}' -> action={result['action']}")

    print("\n✅ Executor parse test completed!")


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("POSTING AGENT TEST SUITE")
    print("=" * 60)

    # try:
    #     await test_approval_service()
    # except Exception as e:
    #     print(f"❌ Approval service test failed: {e}")

    # try:
    #     await test_executor_parse()
    # except Exception as e:
    #     print(f"❌ Executor parse test failed: {e}")

    # try:
    #     await test_direct_agent()
    # except Exception as e:
    #     print(f"❌ Direct agent test failed: {e}")

    # try:
    #     await test_with_approval_workflow()
    # except Exception as e:
    #     print(f"❌ Approval workflow test failed: {e}")

    try:
        await test_a2a_server()
    except Exception as e:
        print(f"❌ A2A server test failed (is server running?): {e}")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
