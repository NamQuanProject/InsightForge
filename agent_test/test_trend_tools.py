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
               "Tại thị trường Việt Nam, hãy tìm chủ đề đang bùng nổ nhất trong lĩnh vực Công nghệ (Technology) trong vòng 24 giờ qua. Sau khi xác định được tên chủ đề hoặc từ khóa cụ thể đó, hãy thực hiện phân tích sâu để cho tôi biết: xu hướng tìm kiếm của nó đang biến động thế nào trong thời gian gần đây và những khái niệm/chủ đề nào khác đang được người dùng nhắc kèm nhiều nhất với nó."
            )
            
    print(f"--- Starting Test ---\nQuery: {query}\n")
    print("\n--- FINAL AGENT OUTPUT ---")
    result = await agent.answer_query(query)
    # print(result)

if __name__ == "__main__":
    asyncio.run(run_test())

