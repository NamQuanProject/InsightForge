import asyncio
import copy
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from app.services.post_service import photo_convert


class ImageStoreService:
    def __init__(self, base_dir: str | Path = "sample_data") -> None:
        self.base_dir = Path(base_dir)
        self.image_dir = self.base_dir / "img_db"
        self.embedding_dir = self.base_dir / "embeddings"
        self.metadata_path = self.base_dir / "metadata.json"
        self.project_root = Path(__file__).resolve().parents[2]
        self.generated_image_dir = self.project_root / "images"
        self.cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.cloudflare_model = os.getenv(
            "CLOUDFLARE_IMAGE_MODEL",
            "@cf/stabilityai/stable-diffusion-xl-base-1.0",
        )

    async def save_local_image(
        self,
        source_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        source = self.resolve_source_path(source_path)
        if source is None:
            raise FileNotFoundError(f"Image file not found: {source_path}")

        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_dir.mkdir(parents=True, exist_ok=True)

        image_id = str(uuid.uuid4())
        suffix = source.suffix or ".png"
        stored_path = self.image_dir / f"{image_id}{suffix}"
        await asyncio.to_thread(shutil.copyfile, source, stored_path)

        embedding = await self._embed_image(stored_path)
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)

        embedding_path = self.embedding_dir / f"{image_id}.npy"
        await asyncio.to_thread(np.save, embedding_path, embedding)

        uploaded_urls = await photo_convert([str(stored_path)])
        image_url = uploaded_urls[0]

        created_at = datetime.now(timezone.utc).isoformat()
        description = self._metadata_description(metadata)
        metadata_entry = {
            "id": image_id,
            "image_url": image_url,
            "description": description,
            "local_path": str(stored_path),
            "created_at": created_at,
        }
        supabase_row = {
            "id": image_id,
            "image_url": image_url,
            "description": description,
            "local_path": str(stored_path),
            "created_at": created_at,
        }
        self._insert_supabase_image(supabase_row)

        await asyncio.to_thread(self._write_metadata, image_id, metadata_entry)

        return {
            "id": image_id,
            "image_url": image_url,
            "description": description,
            "local_path": str(stored_path),
            "created_at": created_at,
        }

    async def attach_section_images(self, video_script: Any) -> dict:
        if not isinstance(video_script, dict):
            return {}

        enriched = copy.deepcopy(video_script)
        sections = enriched.get("sections")
        if not isinstance(sections, list):
            return enriched

        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            thumbnail = section.get("thumbnail")
            if not isinstance(thumbnail, dict):
                thumbnail = {}
                section["thumbnail"] = thumbnail

            description = str(thumbnail.get("description") or thumbnail.get("prompt") or "").strip()
            thumbnail["description"] = description

            output_path = str(thumbnail.get("output_path") or "").strip()
            if not output_path or thumbnail.get("id"):
                continue

            try:
                stored = await self.save_local_image(
                    output_path,
                    metadata={
                        "source": "generated_content_section",
                        "section_index": index,
                        "section_label": section.get("label"),
                        "thumbnail_prompt": thumbnail.get("prompt"),
                        "description": description,
                    },
                )
            except Exception as exc:
                thumbnail["image_store_error"] = str(exc)
                continue

            section["thumbnail"] = stored

        return enriched

    async def attach_post_images(self, image_set: Any) -> list[dict[str, Any]]:
        if not isinstance(image_set, list):
            return []

        enriched = copy.deepcopy(image_set)
        for index, image in enumerate(enriched):
            if not isinstance(image, dict):
                continue

            prompt = str(image.get("prompt") or "").strip()
            description = self._normalize_post_image_description(
                image.get("description"),
                prompt=prompt,
                title=str(image.get("title") or ""),
                index=index + 1,
            )
            image["description"] = description

            output_path = str(image.get("output_path") or "").strip()
            if not output_path or image.get("id"):
                continue

            try:
                await self.ensure_post_image_file(
                    output_path=output_path,
                    prompt=prompt,
                )
                stored = await self.save_local_image(
                    output_path,
                    metadata={
                        "source": "generated_content_post_image",
                        "image_index": image.get("index") or index + 1,
                        "image_title": image.get("title"),
                        "prompt": image.get("prompt"),
                        "description": description,
                    },
                )
            except Exception as exc:
                image["image_store_error"] = str(exc)
                continue

            image.update(stored)

        return enriched

    async def ensure_post_image_file(self, output_path: str, prompt: str) -> Path:
        existing = self.resolve_source_path(output_path)
        if existing is not None:
            return existing

        if not prompt:
            raise FileNotFoundError(f"Image file not found and prompt is empty: {output_path}")

        target_path = self._generated_output_path(output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.cloudflare_account_id or not self.cloudflare_api_token:
            raise RuntimeError(
                "Image file not found and Cloudflare credentials are not configured. "
                "Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN."
            )

        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self.cloudflare_account_id}/ai/run/{self.cloudflare_model}"
        )
        headers = {
            "Authorization": f"Bearer {self.cloudflare_api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "num_steps": int(os.getenv("CLOUDFLARE_IMAGE_NUM_STEPS", "20")),
            "guidance": float(os.getenv("CLOUDFLARE_IMAGE_GUIDANCE", "7.5")),
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Cloudflare image generation failed {response.status_code}: {response.text}")

        await asyncio.to_thread(target_path.write_bytes, response.content)
        return target_path.resolve()

    def _generated_output_path(self, output_path: str) -> Path:
        path = Path(output_path)
        if path.is_absolute():
            return path
        return self.generated_image_dir / path.name

    def _normalize_post_image_description(
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
            or self._looks_like_generation_prompt(description)
        ):
            label = title.strip() or f"ảnh {index}"
            return (
                f"Mô tả nội dung cho {label}: ảnh này cần truyền tải rõ ý chính "
                "của phần trong bài post, giúp người xem hiểu nhanh thông điệp "
                "và muốn tiếp tục xem các ảnh tiếp theo."
            )
        return description

    def _looks_like_generation_prompt(self, value: str) -> bool:
        lowered = value.lower()
        markers = [
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
        return any(marker in lowered for marker in markers)

    def _normalize_post_image_description(
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
            or self._looks_like_generation_prompt(description)
        ):
            label = title.strip() or f"ảnh {index}"
            return (
                f"Mô tả nội dung cho {label}: ảnh này cần truyền tải rõ ý chính "
                "của phần trong bài post, giúp người xem hiểu nhanh thông điệp "
                "và muốn tiếp tục xem các ảnh tiếp theo."
            )
        return description

    def resolve_source_path(self, source_path: str | Path) -> Path | None:
        path = Path(source_path)
        candidates = [
            path,
            Path.cwd() / path,
            Path.cwd() / "images" / path,
            Path.cwd() / self.image_dir / path,
            self.project_root / path,
            self.project_root / "images" / path,
            self.project_root / self.image_dir / path,
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()
        return None

    def _insert_supabase_image(self, row: dict[str, Any]) -> Any:
        try:
            from database.client import db
        except Exception as exc:
            raise RuntimeError(f"Supabase client import failed: {exc}") from exc

        if not db.is_configured:
            raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY.")

        try:
            return db.insert("image_store", row)
        except Exception as exc:
            raise RuntimeError(f"Supabase image_store insert failed: {exc}") from exc

    def _metadata_description(self, metadata: dict[str, Any] | None) -> str:
        if not isinstance(metadata, dict):
            return ""
        value = metadata.get("description") or metadata.get("thumbnail_prompt") or metadata.get("prompt")
        return str(value or "")

    async def _embed_image(self, image_path: Path) -> np.ndarray:
        try:
            from integrations_api.embedding import embedder
        except Exception as exc:
            raise RuntimeError(f"Image embedder import failed: {exc}") from exc

        return await embedder.embed_image(str(image_path))

    def _write_metadata(self, image_id: str, metadata: dict[str, Any]) -> None:
        existing: dict[str, Any] = {}
        if self.metadata_path.exists():
            try:
                existing = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}

        existing[image_id] = metadata
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
