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
            "Hãy quét các kênh truyền thông xã hội để tìm ra 3 chủ đề đang có tốc độ lan truyền cao nhất tại Việt Nam trong vòng 12 giờ qua. Với mỗi chủ đề, hãy liệt kê các chỉ số về lượt xem/lượt tương tác và tóm tắt xem cộng đồng đang phản ứng như thế nào."
            )
            
    print(f"--- Starting Test ---\nQuery: {query}\n")
    print("\n--- FINAL AGENT OUTPUT ---")
    result = await agent.answer_query(query)
    # print(result)

if __name__ == "__main__":
    asyncio.run(run_test())

