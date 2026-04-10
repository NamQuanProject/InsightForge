from agents.trend_agent.agent import TrendAgent
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "")

async def run_test():
    agent = TrendAgent(
        api_key=api_key
    )
    await agent.initialize()

    query = (
            "Khám phá và phân tích xu hướng hiện tại có tốc độ lan truyền và tranh luận nhanh ở Việt Nam trong 1 ngày trở lại. Đề xuất nội dung cho sáng tạo nội dung phù hợp xu hướng và thị hiếu."
            )
            
    print(f"--- Starting Test ---\nQuery: {query}\n")
    print("\n--- FINAL AGENT OUTPUT ---")
    result = await agent.answer_query(query)
    # print(result)

if __name__ == "__main__":
    asyncio.run(run_test())

