import httpx


class InsightForgeA2AClient:
    def __init__(self, base_url: str = "http://localhost:5000/") -> None:
        self.base_url = base_url

    async def ask(self, prompt: str) -> str:
        try:
            from a2a.client import A2AClient
        except Exception as exc:
            raise RuntimeError(f"A2A client is unavailable in the current environment: {exc}") from exc

        async with httpx.AsyncClient(timeout=60.0) as httpx_client:
            client = A2AClient(url=self.base_url, httpx_client=httpx_client)
            response = await client.send_message(prompt)
            return str(response)
