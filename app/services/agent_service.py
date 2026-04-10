import socket

from app.schema.common import AgentProcessStatus, AgentsStatusResponse
from app.services.a2a_client import InsightForgeA2AClient


class AgentService:
    def __init__(self) -> None:
        self.processes = [
            ("main_orchestrator", "localhost", 5000),
            ("trend_agent", "localhost", 9997),
            ("planning_agent", "localhost", 9998),
        ]

    async def analyze(self, platform: str, query: str) -> tuple[str, str]:
        prompt = (
            f"Platform: {platform}. Analyze current external trends for this request: {query}. "
            "Focus on trend topics, expected audience interest, and actionable content directions."
        )
        client = InsightForgeA2AClient()
        try:
            result = await client.ask(prompt)
            return "a2a-agent", result
        except Exception as exc:
            fallback = (
                f"Agent fallback summary for {platform}: current mock data shows strong momentum around {query}. "
                f"Use this as a temporary analysis while the agent runtime is unavailable. Details: {exc}"
            )
            return "mock-fallback", fallback

    def get_status(self) -> AgentsStatusResponse:
        statuses = []
        for name, host, port in self.processes:
            reachable = self._is_port_open(host, port)
            statuses.append(
                AgentProcessStatus(
                    name=name,
                    url=f"http://{host}:{port}",
                    reachable=reachable,
                    detail="reachable" if reachable else "not reachable",
                )
            )
        overall = "ok" if all(proc.reachable for proc in statuses) else "degraded"
        return AgentsStatusResponse(status=overall, processes=statuses)

    def _is_port_open(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.8):
                return True
        except OSError:
            return False
