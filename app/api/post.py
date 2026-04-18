from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
import os
import uuid
import json
import numpy as np
from datetime import datetime

from app.schema.post import PostRequest, PostResponse, ImageInfo
from app.services.post_service import PostService, photo_convert
from database.client import db
from integrations_api.embedding import embedder

router = APIRouter(prefix="/api/v1/post", tags=["post"])


@router.post("/post", response_model=PostResponse)
async def post(payload: PostRequest):
    service = PostService()
    return await service.posting(payload)


@router.post("/upload_image")
async def upload_image_to_store(
    file: UploadFile = File(...),
    description: str = Form(default=""),
):
    base_dir = "sample_data"
    image_dir = os.path.join(base_dir, "img_db")
    embedding_dir = os.path.join(base_dir, "embeddings")
    metadata_path = os.path.join(base_dir, "metadata.json")

    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(embedding_dir, exist_ok=True)

    if not file.content_type.startswith("image/"):
        return {"error": "Only image files are allowed"}

    image_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    image_path = os.path.join(image_dir, f"{image_id}.{ext}")

    content = await file.read()
    with open(image_path, "wb") as f:
        f.write(content)

    embedding = await embedder.embed_image(image_path)
    if not isinstance(embedding, np.ndarray):
        embedding = np.array(embedding)

    embedding_path = os.path.join(embedding_dir, f"{image_id}.npy")
    np.save(embedding_path, embedding)

    uploaded_urls = await photo_convert([image_path])
    image_url = uploaded_urls[0]

    image_info = ImageInfo(
        id=image_id,
        image_url=image_url,
        description=description,
        local_path=image_path,
        created_at=datetime.now(),
    )
    db_data = image_info.model_dump()
    db_data["created_at"] = db_data["created_at"].isoformat()
    db.insert("image_store", db_data)

    metadata = {
        image_id: {
            "id": image_id,
            "image_url": image_url,
            "description": description,
            "local_path": image_path,
            "created_at": db_data["created_at"],
        }
    }

    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_data.update(metadata)
        metadata = existing_data

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return {
        "id": image_id,
        "image_url": image_url,
        "description": description,
        "local_path": image_path,
        "created_at": db_data["created_at"],
    }
