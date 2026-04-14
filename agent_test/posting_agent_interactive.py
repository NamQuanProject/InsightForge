import os
import asyncio
from dotenv import load_dotenv
from langgraph.types import Command

load_dotenv()


async def run_interactive():


    from agents.posting_agent.agent import PostingAgent

    agent = PostingAgent(api_key=os.getenv("GOOGLE_API_KEY"))
    await agent.initialize()
    user_input_1 = "upload photos at sample_data/image.png with username blhoang23 to instagram with description 'Test post from API'"
    print("\nUser Input:")
    print(user_input_1)
    config, response = await agent.chat(user_input_1)

    print ("\n--- Agent Response ---")
    print(response)


    if response.interrupts:
        print("\n--- Interrupts ---")
        print(response.interrupts)

        interrupt_value = response.interrupts[0].value  
        action_requests = interrupt_value["action_requests"]
        review_configs = interrupt_value["review_configs"]
        

        config_map = {cfg["action_name"]: cfg for cfg in review_configs}
        for action in action_requests:
            review_config = config_map[action["name"]]
            print(f"Tool: {action['name']}")
            print(f"Arguments: {action['args']}")
            print(f"Allowed decisions: {review_config['allowed_decisions']}")
        


        decisions = [
            {"type": "approve"}  # User approved the deletion
        ]
        
        # Resume execution with decisions
        result = await agent.agent.ainvoke(
            Command(resume={"decisions": decisions}),
            config=config,  # Must use the same config!
            version="v2",
        )


        print(result.value["messages"][-1].content)




    # # Wait 5 seconds
    # await asyncio.sleep(5)
    # response = await agent.agent.ainvoke(
    #         Command(
    #             resume={"decisions": [{"type": "approve"}]}  # or "reject"
    #         ),
    #         config= {"configurable": {"thread_id": "1"}}, # Same thread ID to resume the paused conversation
    #         version="v2",
    #     )  
    








    # print("\nResponse:")
    # print(response["messages"][-1].content)



if __name__ == "__main__":
    asyncio.run(run_interactive())
