import csv
from pathlib import Path
from urllib.parse import quote_plus

from app.schema.post import PostResponse

class PostService:
    def __init__(self) -> None:
        self.client = None
        self.mock_data_dir = Path(__file__).resolve().parents[1] / "mock_data"

    async def posting(self, query: str):
        if self.client is None:
            from app.services.a2a_client import InsightForgeA2AClient

            self.client = InsightForgeA2AClient()
        result = await self.client.posting(query)

        return PostResponse(
            status="success",
            source="a2a-agent",
            result_markdown=result,
        )


