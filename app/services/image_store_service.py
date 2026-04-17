import asyncio
import copy
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from app.services.post_service import photo_convert


class ImageStoreService:
    def __init__(self, base_dir: str | Path = "sample_data") -> None:
        self.base_dir = Path(base_dir)
        self.image_dir = self.base_dir / "img_db"
        self.embedding_dir = self.base_dir / "embeddings"
        self.metadata_path = self.base_dir / "metadata.json"

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

    def resolve_source_path(self, source_path: str | Path) -> Path | None:
        path = Path(source_path)
        candidates = [
            path,
            Path.cwd() / path,
            Path.cwd() / "images" / path,
            Path.cwd() / self.image_dir / path,
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
