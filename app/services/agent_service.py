import copy
import socket
import os
import uuid

from app.schema.common import AgentProcessStatus, AgentsStatusResponse, OrchestratorResponse
from app.services.a2a_client import InsightForgeA2AClient
from app.services.image_store_service import ImageStoreService
from app.services.postgres_service import PostgresService
from app.services.user_context import resolve_user_id


class AgentService:
    def __init__(self) -> None:
        host = os.environ.get("AGENT_HOST", "localhost")
        self.postgres = PostgresService()
        self.image_store = ImageStoreService()
        self.processes = [
            ("routing_orchestrator", host, int(os.environ.get("ROUTING_AGENT_PORT", 9996))),
            ("trend_agent", host, int(os.environ.get("TREND_AGENT_PORT", 9997))),
            ("content_agent", host, int(os.environ.get("CONTENT_AGENT_PORT", 9998))),
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

    async def orchestrate(
        self,
        prompt: str,
        save_files: bool = True,
        user_id: uuid.UUID | None = None,
    ) -> OrchestratorResponse:
        resolved_user_id = resolve_user_id(user_id)
        client = InsightForgeA2AClient()
        result = await client.ask(prompt)
        output = client.normalize_orchestrator_output(result["output"], prompt=prompt)

        trend_analysis = output["trend_analysis"]
        trend_record = await self.postgres.save_trend_analysis(
            query=trend_analysis["query"],
            results=trend_analysis["results"],
            summary=trend_analysis["markdown_summary"],
            user_id=resolved_user_id,
            status="failed" if trend_analysis.get("error") else "completed",
            error=trend_analysis.get("error"),
        )

        # generated_content = output["generated_content"]
        # generated_record = await self.postgres.save_generated_content(
        #     raw_output=generated_content,
        #     video_script=generated_content["video_script"],
        #     platform_posts=generated_content["platform_posts"],
        #     thumbnail=generated_content["thumbnail"],
        #     user_id=user_id,
        #     trend_analysis_id=trend_record.id,
        #     selected_keyword=generated_content.get("selected_keyword") or self._best_keyword(trend_analysis),
        #     main_title=generated_content.get("main_title"),
        #     music_background=generated_content.get("music_background"),
        #     status="failed" if generated_content.get("error") else "generated",
        # )
        generated_content = output["generated_content"]
        video_script = await self.image_store.attach_section_images(generated_content["video_script"])
        generated_content_to_save = copy.deepcopy(generated_content)
        generated_content_to_save["video_script"] = video_script
        output["generated_content"] = generated_content_to_save

        # video_script is stored whole: it contains title, duration_estimate, hook,
        # sections (each with its own thumbnail dict), call_to_action, captions_style,
        # and music_mood.  There is no separate top-level thumbnail field.
        generated_record = await self.postgres.save_generated_content(
            raw_output=generated_content_to_save,
            video_script=video_script,
            platform_posts=generated_content_to_save["platform_posts"],
            user_id=resolved_user_id,
            trend_analysis_id=trend_record.id,
            selected_keyword=generated_content_to_save.get("selected_keyword") or self._best_keyword(trend_analysis),
            main_title=generated_content_to_save.get("main_title"),
            music_background=generated_content_to_save.get("music_background"),
            status="failed" if generated_content_to_save.get("error") else "generated",
        )

        raw_file = None
        output_file = None
        if save_files:
            raw_file, output_file = client.save_response_files(
                raw_response=result["raw_response"],
                output=output,
                output_dir=os.environ.get("ORCHESTRATOR_OUTPUT_DIR", "."),
            )

        return OrchestratorResponse(
            status="success",
            output=output,
            trend_analysis_id=trend_record.id,
            generated_content_id=generated_record.id,
            raw_response=result["raw_response"],
            raw_response_file=raw_file,
            output_file=output_file,
        )

    def _best_keyword(self, trend_analysis: dict) -> str | None:
        results = trend_analysis.get("results")
        if not isinstance(results, list) or not results:
            return None
        best = max(results, key=lambda item: item.get("trend_score", 0) if isinstance(item, dict) else 0)
        if not isinstance(best, dict):
            return None
        return best.get("main_keyword")

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
