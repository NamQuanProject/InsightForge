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
        post_url: str | None = None,
    ) -> None:
        host = os.environ.get("AGENT_HOST", "localhost")
        port = os.environ.get("ROUTING_AGENT_PORT", "9996")
        post_host = os.environ.get("POSTING_AGENT_HOST", host)
        post_port = os.environ.get("POSTING_AGENT_PORT", "9995")
        self.base_url = (base_url or f"http://{host}:{port}").rstrip("/")
        self.timeout = timeout or float(os.environ.get("ORCHESTRATOR_TIMEOUT", "420"))
        self.post_url = (
            post_url
            or os.environ.get("POSTING_AGENT_URL")
            or f"http://{post_host}:{post_port}"
        ).rstrip("/")
        self.post_client: Any | None = None

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
        if not normalized_results and not error:
            error = {
                "type": "empty_results",
                "message": "Trend analysis returned no results.",
            }

        if not normalized_results and self._is_recoverable_trend_error(error):
            return self._fallback_trend_analysis(
                query=str(trend.get("query") or prompt),
                error=error,
            )

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

    def _is_recoverable_trend_error(self, error: Any) -> bool:
        if not isinstance(error, dict):
            return False
        message = str(error.get("message") or error)
        error_type = str(error.get("type") or "").lower()
        return error_type == "empty_results" or "list index out of range" in message.lower()

    def _fallback_trend_analysis(self, query: str, error: dict[str, Any]) -> dict[str, Any]:
        keyword = self._fallback_keyword(query)
        trend_score = 32.0
        avg_views_per_hour = 2500.0
        return {
            "query": query,
            "results": [
                {
                    "main_keyword": keyword,
                    "why_the_trend_happens": (
                        "Nguồn trend trả dữ liệu không đầy đủ nên hệ thống dùng fallback bảo thủ "
                        "dựa trên chủ đề người dùng để tiếp tục pipeline."
                    ),
                    "trend_score": trend_score,
                    "interest_over_day": self._normalize_interest_over_day(
                        [],
                        trend_score=trend_score,
                        momentum="stable",
                        avg_views_per_hour=avg_views_per_hour,
                    ),
                    "avg_views_per_hour": avg_views_per_hour,
                    "recommended_action": (
                        "Tạo bài post nhiều ảnh về một mẹo sức khỏe dễ áp dụng, có cảnh báo "
                        "không thay thế tư vấn y tế, và đưa ra hành động nhỏ người xem có thể thử ngay."
                    ),
                    "top_videos": [],
                    "top_hashtags": ["#meovatcuocsong", "#suckhoe", "#thoiquentot"],
                    "google": {
                        "keyword": keyword,
                        "momentum": "stable",
                        "peak_region": None,
                    },
                    "tiktok": None,
                    "threads": None,
                }
            ],
            "markdown_summary": (
                f"Trend agent gặp lỗi dữ liệu tạm thời ({error.get('message')}). "
                f"Hệ thống dùng fallback an toàn cho chủ đề '{keyword}' để tiếp tục tạo nội dung."
            ),
            "error": None,
            "fallback": True,
            "fallback_reason": error.get("message"),
        }

    def _fallback_keyword(self, query: str) -> str:
        lowered = query.lower()
        if "trà sữa" in lowered or "tra sua" in lowered:
            return "tác hại trà sữa"
        if "sức khỏe" in lowered or "suc khoe" in lowered:
            return "mẹo vặt sức khỏe tại nhà"
        if "mẹo vặt" in lowered or "lifehack" in lowered:
            return "mẹo vặt cuộc sống"
        return "thói quen tốt mỗi ngày"

    def _normalize_trend_item(self, item: dict[str, Any]) -> dict[str, Any]:
        main_keyword = str(item.get("main_keyword") or item.get("keyword") or "")
        trend_score = self._to_float(item.get("trend_score"))
        avg_views_per_hour = self._to_float(item.get("avg_views_per_hour") or item.get("avg_velocity"))
        google = item.get("google") if isinstance(item.get("google"), dict) else {
            "keyword": main_keyword,
            "momentum": "stable",
            "peak_region": None,
        }
        return {
            "main_keyword": main_keyword,
            "why_the_trend_happens": str(item.get("why_the_trend_happens") or item.get("reasoning") or ""),
            "trend_score": trend_score,
            "interest_over_day": self._normalize_interest_over_day(
                item.get("interest_over_day"),
                trend_score=trend_score,
                momentum=str(google.get("momentum") or "stable"),
                avg_views_per_hour=avg_views_per_hour,
            ),
            "avg_views_per_hour": avg_views_per_hour,
            "recommended_action": str(item.get("recommended_action") or item.get("action") or ""),
            "top_videos": self._to_str_list(item.get("top_videos") or item.get("videos")),
            "top_hashtags": self._to_str_list(item.get("top_hashtags") or item.get("hashtags")),
            "google": google,
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

        post_content = content.get("post_content") if isinstance(content.get("post_content"), dict) else {}
        image_set = content.get("image_set") if isinstance(content.get("image_set"), list) else []
        platform_posts = content.get("platform_posts") if isinstance(content.get("platform_posts"), dict) else {}
        publishing = content.get("publishing") if isinstance(content.get("publishing"), dict) else {}

        if not post_content and isinstance(content.get("video_script"), dict):
            video_script = content["video_script"]
            post_content = {
                "post_type": "multi_image_post",
                "title": video_script.get("title") or "",
                "hook": video_script.get("hook") or "",
                "caption": "",
                "description": video_script.get("call_to_action") or "",
                "body": "",
                "call_to_action": video_script.get("call_to_action") or "",
                "hashtags": [],
                "tone": video_script.get("captions_style") or "",
                "personalization_notes": [],
            }
            image_set = self._image_set_from_legacy_sections(video_script.get("sections"))

        return {
            "selected_keyword": str(content.get("selected_keyword") or ""),
            "main_title": str(content.get("main_title") or post_content.get("title") or ""),
            "post_content": self._normalize_post_content(post_content),
            "image_set": self._normalize_image_set(image_set),
            "platform_posts": {
                "tiktok": self._normalize_platform_post(platform_posts.get("tiktok")),
                "facebook": self._normalize_platform_post(platform_posts.get("facebook")),
                "instagram": self._normalize_platform_post(platform_posts.get("instagram")),
            },
            "publishing": self._normalize_publishing(publishing),
            "error": content.get("error"),
        }

    def _normalize_platform_post(self, post: Any) -> dict[str, Any]:
        post = post if isinstance(post, dict) else {}
        return {
            "caption": str(post.get("caption") or ""),
            "hashtags": self._to_str_list(post.get("hashtags")),
            "cta": str(post.get("cta") or ""),
            "best_post_time": str(post.get("best_post_time") or ""),
            "image_notes": str(post.get("image_notes") or post.get("thumbnail_description") or ""),
        }

    def _normalize_post_content(self, post: Any) -> dict[str, Any]:
        post = post if isinstance(post, dict) else {}
        return {
            "post_type": str(post.get("post_type") or "multi_image_post"),
            "title": str(post.get("title") or ""),
            "hook": str(post.get("hook") or ""),
            "caption": str(post.get("caption") or ""),
            "description": str(post.get("description") or ""),
            "body": str(post.get("body") or ""),
            "call_to_action": str(post.get("call_to_action") or ""),
            "hashtags": self._to_str_list(post.get("hashtags")),
            "tone": str(post.get("tone") or ""),
            "personalization_notes": self._to_str_list(post.get("personalization_notes")),
        }

    def _normalize_image_set(self, image_set: Any) -> list[dict[str, Any]]:
        if not isinstance(image_set, list):
            return []

        normalized = []
        for index, image in enumerate(image_set):
            if not isinstance(image, dict):
                continue
            prompt = str(image.get("prompt") or "")
            description = self._normalize_image_description(
                image.get("description"),
                prompt=prompt,
                title=str(image.get("title") or ""),
                index=index + 1,
            )
            normalized.append(
                {
                    "index": self._to_int(image.get("index") or index + 1),
                    "title": str(image.get("title") or ""),
                    "description": description,
                    "prompt": prompt,
                    "style": str(image.get("style") or "vivid"),
                    "size": str(image.get("size") or "1792x1024"),
                    "output_path": str(image.get("output_path") or f"post_image_{index + 1}.png"),
                }
            )
        return normalized

    def _normalize_publishing(self, publishing: Any) -> dict[str, Any]:
        publishing = publishing if isinstance(publishing, dict) else {}
        return {
            "default_visibility": str(publishing.get("default_visibility") or ""),
            "recommended_platforms": self._to_str_list(publishing.get("recommended_platforms")),
            "timezone": str(publishing.get("timezone") or ""),
            "weekly_content_frequency": self._to_int(publishing.get("weekly_content_frequency")),
        }

    def _image_set_from_legacy_sections(self, sections: Any) -> list[dict[str, Any]]:
        if not isinstance(sections, list):
            return []

        image_set = []
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            thumbnail = section.get("thumbnail") if isinstance(section.get("thumbnail"), dict) else {}
            prompt = str(thumbnail.get("prompt") or "")
            image_set.append(
                {
                    "index": index + 1,
                    "title": str(section.get("label") or f"Image {index + 1}"),
                    "description": self._normalize_image_description(
                        thumbnail.get("description") or section.get("notes"),
                        prompt=prompt,
                        title=str(section.get("label") or ""),
                        index=index + 1,
                    ),
                    "prompt": prompt,
                    "style": str(thumbnail.get("style") or "vivid"),
                    "size": str(thumbnail.get("size") or "1792x1024"),
                    "output_path": str(thumbnail.get("output_path") or f"post_image_{index + 1}.png"),
                }
            )
        return image_set

    def _normalize_image_description(
        self,
        value: Any,
        prompt: str,
        title: str = "",
        index: int = 1,
    ) -> str:
        description = str(value or "").strip()
        prompt_text = str(prompt or "").strip()

        if (
            not description
            or description.lower() == prompt_text.lower()
            or self._looks_like_image_prompt(description)
        ):
            label = title.strip() or f"ảnh {index}"
            return (
                f"Mô tả nội dung cho {label}: ảnh này cần truyền tải rõ ý chính "
                "của phần trong bài post, giúp người xem hiểu nhanh thông điệp "
                "và muốn tiếp tục xem các ảnh tiếp theo."
            )
        return description

    def _looks_like_image_prompt(self, value: str) -> bool:
        lowered = value.lower()
        prompt_markers = [
            "sdxl",
            "lighting",
            "camera",
            "composition",
            "vibrant colors",
            "minimalist",
            "background",
            "style:",
            "photorealistic",
        ]
        return any(marker in lowered for marker in prompt_markers)

    def _fallback_trend_analysis(self, query: str, error: dict[str, Any]) -> dict[str, Any]:
        keyword = self._fallback_keyword(query)
        trend_score = 32.0
        avg_views_per_hour = 2500.0
        return {
            "query": query,
            "results": [
                {
                    "main_keyword": keyword,
                    "why_the_trend_happens": (
                        "Nguồn trend trả dữ liệu không đầy đủ nên hệ thống dùng fallback bảo thủ "
                        "dựa trên chủ đề người dùng để tiếp tục pipeline."
                    ),
                    "trend_score": trend_score,
                    "interest_over_day": self._normalize_interest_over_day(
                        [],
                        trend_score=trend_score,
                        momentum="stable",
                        avg_views_per_hour=avg_views_per_hour,
                    ),
                    "avg_views_per_hour": avg_views_per_hour,
                    "recommended_action": (
                        "Tạo bài post nhiều ảnh về một mẹo sức khỏe dễ áp dụng, có cảnh báo "
                        "không thay thế tư vấn y tế, và đưa ra hành động nhỏ người xem có thể thử ngay."
                    ),
                    "top_videos": [],
                    "top_hashtags": ["#meovatcuocsong", "#suckhoe", "#thoiquentot"],
                    "google": {
                        "keyword": keyword,
                        "momentum": "stable",
                        "peak_region": None,
                    },
                    "tiktok": None,
                    "threads": None,
                }
            ],
            "markdown_summary": (
                f"Trend agent gặp lỗi dữ liệu tạm thời ({error.get('message')}). "
                f"Hệ thống dùng fallback an toàn cho chủ đề '{keyword}' để tiếp tục tạo nội dung."
            ),
            "error": None,
            "fallback": True,
            "fallback_reason": error.get("message"),
        }

    def _fallback_keyword(self, query: str) -> str:
        lowered = query.lower()
        if "trà sữa" in lowered or "tra sua" in lowered:
            return "tác hại trà sữa"
        if "sức khỏe" in lowered or "suc khoe" in lowered:
            return "mẹo vặt sức khỏe tại nhà"
        if "mẹo vặt" in lowered or "lifehack" in lowered:
            return "mẹo vặt cuộc sống"
        return "thói quen tốt mỗi ngày"

    def _normalize_image_description(
        self,
        value: Any,
        prompt: str,
        title: str = "",
        index: int = 1,
    ) -> str:
        description = str(value or "").strip()
        prompt_text = str(prompt or "").strip()

        if (
            not description
            or description.lower() == prompt_text.lower()
            or self._looks_like_image_prompt(description)
        ):
            label = title.strip() or f"ảnh {index}"
            return (
                f"Mô tả nội dung cho {label}: ảnh này cần truyền tải rõ ý chính "
                "của phần trong bài post, giúp người xem hiểu nhanh thông điệp "
                "và muốn tiếp tục xem các ảnh tiếp theo."
            )
        return description

    def _to_float(self, value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _to_float_list(self, value: Any) -> list[float]:
        if not isinstance(value, list):
            return []
        return [self._to_float(item) for item in value]

    def _normalize_interest_over_day(
        self,
        value: Any,
        trend_score: float,
        momentum: str = "stable",
        avg_views_per_hour: float = 0,
    ) -> list[float]:
        values = self._to_float_list(value)
        values = [max(0.0, item) for item in values]
        if len(values) >= 3 and any(item > 0 for item in values):
            return [round(item, 2) for item in values]

        score = self._clamp_float(trend_score, minimum=1.0, maximum=100.0)
        velocity_lift = min(18.0, max(avg_views_per_hour, 0.0) / 5000.0)
        base = self._clamp_float(score * 0.62 + velocity_lift, minimum=8.0, maximum=88.0)
        normalized_momentum = str(momentum or "stable").lower()

        if normalized_momentum == "rising":
            factors = [0.58, 0.68, 0.8, 0.93, 1.08, 1.22]
        elif normalized_momentum == "declining":
            factors = [1.18, 1.08, 0.96, 0.84, 0.73, 0.62]
        else:
            factors = [0.86, 0.94, 1.02, 0.97, 1.06, 1.0]

        return [
            round(self._clamp_float(base * factor, minimum=1.0, maximum=100.0), 2)
            for factor in factors
        ]

    def _clamp_float(self, value: Any, minimum: float, maximum: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = minimum
        return min(maximum, max(minimum, parsed))

    def _to_str_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    def _to_int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

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

    async def posting(self, prompt: str, config_id: str, decisions: str = "") -> Any:
        from beeai_framework.adapters.a2a.agents import A2AAgent
        from beeai_framework.backend import UserMessage
        from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory

        if self.post_client is None:
            self.post_client = A2AAgent(
                url=self.post_url,
                memory=UnconstrainedMemory(),
            )

        await self.post_client.check_agent_exists()
        print("Connected to Posting Agent Server!\n")

        print(f"Sending prompt: '{prompt}'...\n")
        message = UserMessage(
            content=prompt, meta={"decision": decisions, "config": config_id}
        )
        response = await self.post_client.run(message)
        response_text = response.event.parts[0].root.text

        return response_text
