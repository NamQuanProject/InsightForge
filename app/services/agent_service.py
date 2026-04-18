import copy
import json
import socket
import os
import uuid
from pathlib import Path

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
        self.demo_scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
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
        include_raw_response: bool = False,
    ) -> OrchestratorResponse:
        if self._demo_fast_path_enabled():
            demo_response = self._demo_orchestrator_response(prompt)
            if demo_response is not None:
                return demo_response

        resolved_user_id = resolve_user_id(user_id)
        client = InsightForgeA2AClient()
        routed_prompt = (
            f"user_id: {resolved_user_id}\n"
            "Use this user_id when generating content so the content agent can fetch profile and history.\n"
            f"{prompt}"
        )
        result = await client.ask(routed_prompt)
        output = client.normalize_orchestrator_output(result["output"], prompt=prompt)

        trend_analysis = output["trend_analysis"]
        generated_content = output["generated_content"]
        if self._is_empty_generated_content(generated_content):
            output = self._mark_failure(
                output,
                ["output.generated_content: empty generated content"],
            )
            raw_file, output_file = self._save_debug_files_if_requested(
                client=client,
                raw_response=result["raw_response"],
                output=output,
                save_files=save_files,
            )
            return OrchestratorResponse(
                status="failed",
                output=output,
                raw_response=result["raw_response"] if include_raw_response else None,
                raw_response_file=raw_file,
                output_file=output_file,
            )

        failures = self._collect_failures(output)
        if failures:
            output = self._mark_failure(output, failures)
            raw_file, output_file = self._save_debug_files_if_requested(
                client=client,
                raw_response=result["raw_response"],
                output=output,
                save_files=save_files,
            )
            return OrchestratorResponse(
                status="failed",
                output=output,
                raw_response=result["raw_response"] if include_raw_response else None,
                raw_response_file=raw_file,
                output_file=output_file,
            )

        image_set = await self.image_store.attach_post_images(generated_content.get("image_set"))
        generated_content_to_save = copy.deepcopy(generated_content)
        generated_content_to_save["image_set"] = image_set
        output["generated_content"] = generated_content_to_save

        failures = self._collect_failures(output)
        if failures:
            output = self._mark_failure(output, failures)
            raw_file, output_file = self._save_debug_files_if_requested(
                client=client,
                raw_response=result["raw_response"],
                output=output,
                save_files=save_files,
            )
            return OrchestratorResponse(
                status="failed",
                output=output,
                raw_response=result["raw_response"] if include_raw_response else None,
                raw_response_file=raw_file,
                output_file=output_file,
            )

        trend_record = await self.postgres.save_trend_analysis(
            query=trend_analysis["query"],
            results=trend_analysis["results"],
            summary=trend_analysis["markdown_summary"],
            user_id=resolved_user_id,
            status="completed",
            error=None,
        )

        generated_record = await self.postgres.save_generated_content(
            raw_output=generated_content_to_save,
            post_content=generated_content_to_save.get("post_content") or {},
            image_set=image_set,
            platform_posts=generated_content_to_save.get("platform_posts") or {},
            publishing=generated_content_to_save.get("publishing") or {},
            video_script={},
            user_id=resolved_user_id,
            trend_analysis_id=trend_record.id,
            selected_keyword=generated_content_to_save.get("selected_keyword") or self._best_keyword(trend_analysis),
            main_title=generated_content_to_save.get("main_title"),
            status="generated",
        )

        raw_file, output_file = self._save_debug_files_if_requested(
            client=client,
            raw_response=result["raw_response"],
            output=output,
            save_files=save_files,
        )

        return OrchestratorResponse(
            status="success",
            output=output,
            trend_analysis_id=trend_record.id,
            generated_content_id=generated_record.id,
            raw_response=result["raw_response"] if include_raw_response else None,
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

    def _demo_orchestrator_response(self, prompt: str) -> OrchestratorResponse | None:
        script_path = self.demo_scripts_dir / "script_orchestrator.json"
        output_path = self.demo_scripts_dir / "output_orchestrator.json"
        try:
            script = json.loads(script_path.read_text(encoding="utf-8"))
            expected_prompt = script.get("prompt")
            if not isinstance(expected_prompt, str):
                return None
            if self._normalize_prompt(prompt) != self._normalize_prompt(expected_prompt):
                return None

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return None
            return OrchestratorResponse(**payload)
        except Exception:
            return None

    def _normalize_prompt(self, value: str) -> str:
        return " ".join(str(value or "").split()).casefold()

    def _demo_fast_path_enabled(self) -> bool:
        value = os.environ.get("DEMO_FAST_PATH_ENABLED", "true")
        return value.strip().lower() not in {"0", "false", "no", "off"}

    def _is_empty_generated_content(self, generated_content) -> bool:
        if not isinstance(generated_content, dict):
            return True
        post_content = generated_content.get("post_content")
        image_set = generated_content.get("image_set")
        main_title = str(generated_content.get("main_title") or "").strip()
        post_title = ""
        caption = ""
        if isinstance(post_content, dict):
            post_title = str(post_content.get("title") or "").strip()
            caption = str(post_content.get("caption") or "").strip()
        return not (main_title or post_title or caption or image_set)

    def _save_debug_files_if_requested(
        self,
        client: InsightForgeA2AClient,
        raw_response: dict,
        output: dict,
        save_files: bool,
    ) -> tuple[str | None, str | None]:
        if not save_files:
            return None, None
        return client.save_response_files(
            raw_response=raw_response,
            output=output,
            output_dir=os.environ.get("ORCHESTRATOR_OUTPUT_DIR", "."),
        )

    def _has_failure(self, value) -> bool:
        return bool(self._collect_failures(value))

    def _collect_failures(self, value, path: str = "output") -> list[str]:
        failures: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).lower()
                if normalized_key in {"error", "image_store_error"} and self._is_failure_value(item):
                    failures.append(f"{path}.{key}: {item}")
                if normalized_key in {"status", "state"} and isinstance(item, str):
                    if item.lower() in {"failed", "fail", "error", "partial_success"}:
                        failures.append(f"{path}.{key}: {item}")
                failures.extend(self._collect_failures(item, f"{path}.{key}"))
            return failures

        if isinstance(value, list):
            for index, item in enumerate(value):
                failures.extend(self._collect_failures(item, f"{path}[{index}]"))
            return failures

        return failures

    def _is_failure_value(self, value) -> bool:
        if value is None or value is False:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    def _mark_failure(self, output: dict, failures: list[str]) -> dict:
        marked = copy.deepcopy(output)
        message = "Output contains failure markers; skipped database persistence."
        details = failures[:10]
        generated_content = marked.get("generated_content")
        if isinstance(generated_content, dict) and not generated_content.get("error"):
            generated_content["error"] = {
                "type": "persistence_skipped",
                "message": message,
                "details": details,
            }
        elif not isinstance(generated_content, dict):
            marked["generated_content"] = {
                "error": {
                    "type": "persistence_skipped",
                    "message": message,
                    "details": details,
                }
            }
        marked["persistence_skipped"] = {
            "reason": message,
            "details": details,
        }
        return marked

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
