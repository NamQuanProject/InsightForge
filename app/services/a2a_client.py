import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx


class InsightForgeA2AClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        host = os.environ.get("AGENT_HOST", "localhost")
        port = os.environ.get("ROUTING_AGENT_PORT", "9996")
        self.base_url = (base_url or f"http://{host}:{port}").rstrip("/")
        self.timeout = timeout or float(os.environ.get("ORCHESTRATOR_TIMEOUT", "420"))

    async def ask(self, prompt: str) -> dict[str, Any]:
        payload = self._build_message_send(prompt)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/", json=payload)
            response.raise_for_status()
            raw_response = response.json()

        return {
            "raw_response": raw_response,
            "output": self._extract_final_json(raw_response),
        }

    def save_response_files(
        self,
        raw_response: dict[str, Any],
        output: dict[str, Any],
        output_dir: str | os.PathLike[str] = ".",
    ) -> tuple[str, str]:
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)

        raw_path = directory / "orchestrator_raw_response.json"
        output_path = directory / "orchestrator_output.json"
        raw_path.write_text(json.dumps(raw_response, indent=2, ensure_ascii=False), encoding="utf-8")
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(raw_path), str(output_path)

    def _build_message_send(self, text: str) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "user",
                    "parts": [{"type": "text", "text": text}],
                },
            },
        }

    def _extract_final_json(self, response_json: dict[str, Any]) -> dict[str, Any]:
        text = self._extract_final_text(response_json).strip()
        if not text:
            return {"error": "No final text found in orchestrator response"}

        parsed = self._parse_json_text(text)
        if isinstance(parsed, dict):
            return parsed
        return {"raw_text": text}

    def _parse_json_text(self, value: str, max_depth: int = 3) -> Any:
        cleaned = value.replace("```json", "").replace("```", "").strip()
        try:
            parsed: Any = json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                parsed = json.loads(cleaned.replace("\\'", "'"))
            except json.JSONDecodeError:
                return None

        for _ in range(max_depth):
            if not isinstance(parsed, str):
                break
            nested = parsed.replace("```json", "").replace("```", "").strip()
            if not nested.startswith(("{", "[")):
                break
            try:
                parsed = json.loads(nested)
            except json.JSONDecodeError:
                try:
                    parsed = json.loads(nested.replace("\\'", "'"))
                except json.JSONDecodeError:
                    break
        return parsed

    def normalize_orchestrator_output(self, output: dict[str, Any], prompt: str) -> dict[str, Any]:
        if "raw_text" in output and isinstance(output["raw_text"], str):
            parsed = self._parse_json_text(output["raw_text"])
            if isinstance(parsed, dict):
                output = parsed

        if "value" in output and isinstance(output["value"], str):
            parsed = self._parse_json_text(output["value"])
            if isinstance(parsed, dict):
                output = parsed

        trend = output.get("trend_analysis") if isinstance(output, dict) else None
        content = output.get("generated_content") if isinstance(output, dict) else None

        return {
            "trend_analysis": self._normalize_trend_analysis(trend, prompt),
            "generated_content": self._normalize_generated_content(content),
        }

    def _normalize_trend_analysis(self, trend: Any, prompt: str) -> dict[str, Any]:
        if isinstance(trend, str):
            parsed = self._parse_json_text(trend)
            trend = parsed if isinstance(parsed, dict) else {"raw_text": trend}
        if not isinstance(trend, dict):
            trend = {}

        if "raw" in trend and isinstance(trend["raw"], str):
            parsed = self._parse_json_text(trend["raw"])
            if isinstance(parsed, dict):
                trend = parsed

        results = trend.get("results", [])
        if not isinstance(results, list):
            results = []

        normalized_results = [
            self._normalize_trend_item(item)
            for item in results
            if isinstance(item, dict)
        ]

        raw_text = trend.get("raw_text") or trend.get("raw")
        error = trend.get("error")
        if raw_text and not normalized_results:
            error = error or {"type": "raw_text", "message": str(raw_text)}

        return {
            "query": str(trend.get("query") or prompt),
            "results": normalized_results,
            "markdown_summary": str(
                trend.get("markdown_summary")
                or trend.get("summary")
                or raw_text
                or ""
            ),
            "error": error,
        }

    def _normalize_trend_item(self, item: dict[str, Any]) -> dict[str, Any]:
        main_keyword = str(item.get("main_keyword") or item.get("keyword") or "")
        return {
            "main_keyword": main_keyword,
            "why_the_trend_happens": str(item.get("why_the_trend_happens") or item.get("reasoning") or ""),
            "trend_score": self._to_float(item.get("trend_score")),
            "interest_over_day": self._to_float_list(item.get("interest_over_day")),
            "avg_views_per_hour": self._to_float(item.get("avg_views_per_hour") or item.get("avg_velocity")),
            "recommended_action": str(item.get("recommended_action") or item.get("action") or ""),
            "top_hashtags": self._to_str_list(item.get("top_hashtags") or item.get("hashtags")),
            "google": item.get("google") if isinstance(item.get("google"), dict) else {
                "keyword": main_keyword,
                "momentum": "stable",
                "peak_region": None,
            },
            "tiktok": item.get("tiktok") if isinstance(item.get("tiktok"), dict) else None,
            "threads": item.get("threads") if isinstance(item.get("threads"), dict) else None,
        }

    def _normalize_generated_content(self, content: Any) -> dict[str, Any]:
        if isinstance(content, str):
            parsed = self._parse_json_text(content)
            content = parsed if isinstance(parsed, dict) else {"raw_text": content}
        if not isinstance(content, dict):
            content = {}

        if "raw" in content and isinstance(content["raw"], str):
            parsed = self._parse_json_text(content["raw"])
            if isinstance(parsed, dict):
                content = parsed

        video_script = content.get("video_script") if isinstance(content.get("video_script"), dict) else {}
        platform_posts = content.get("platform_posts") if isinstance(content.get("platform_posts"), dict) else {}
        thumbnail = content.get("thumbnail") if isinstance(content.get("thumbnail"), dict) else {}

        return {
            "selected_keyword": str(content.get("selected_keyword") or ""),
            "main_title": str(content.get("main_title") or video_script.get("title") or ""),
            "video_script": {
                "title": str(video_script.get("title") or ""),
                "duration_estimate": str(video_script.get("duration_estimate") or "60s"),
                "hook": str(video_script.get("hook") or ""),
                "sections": video_script.get("sections") if isinstance(video_script.get("sections"), list) else [],
                "call_to_action": str(video_script.get("call_to_action") or ""),
                "captions_style": str(video_script.get("captions_style") or ""),
                "music_mood": str(video_script.get("music_mood") or ""),
            },
            "platform_posts": {
                "tiktok": self._normalize_platform_post(platform_posts.get("tiktok")),
                "facebook": self._normalize_platform_post(platform_posts.get("facebook")),
                "instagram": self._normalize_platform_post(platform_posts.get("instagram")),
            },
            "thumbnail": {
                "prompt": str(thumbnail.get("prompt") or ""),
                "style": str(thumbnail.get("style") or "vivid"),
                "size": str(thumbnail.get("size") or "1792x1024"),
                "output_path": str(thumbnail.get("output_path") or "content_output.png"),
            },
            "music_background": str(
                content.get("music_background")
                or video_script.get("music_mood")
                or ""
            ),
            "error": content.get("error"),
        }

    def _normalize_platform_post(self, post: Any) -> dict[str, Any]:
        post = post if isinstance(post, dict) else {}
        return {
            "caption": str(post.get("caption") or ""),
            "hashtags": self._to_str_list(post.get("hashtags")),
            "cta": str(post.get("cta") or ""),
            "best_post_time": str(post.get("best_post_time") or ""),
            "thumbnail_description": str(post.get("thumbnail_description") or ""),
        }

    def _to_float(self, value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _to_float_list(self, value: Any) -> list[float]:
        if not isinstance(value, list):
            return []
        return [self._to_float(item) for item in value]

    def _to_str_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    def _extract_final_text(self, response_json: dict[str, Any]) -> str:
        result = response_json.get("result", {})
        task = result.get("task", result)

        if task.get("kind") == "message":
            for part in task.get("parts", []):
                if isinstance(part, dict) and "text" in part:
                    return part["text"]

        status_message = task.get("status", {}).get("message", {})
        for part in status_message.get("parts", []):
            if isinstance(part, dict) and "text" in part:
                return part["text"]

        for message in reversed(task.get("history", [])):
            if message.get("role") in {"agent", "ROLE_AGENT"}:
                for part in message.get("parts", []):
                    if isinstance(part, dict) and "text" in part:
                        return part["text"]

        return ""
