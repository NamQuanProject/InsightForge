from fastapi import APIRouter, Query
from app.schema.post import PostResponse
from app.services.post_service import PostService
from app.services.post_service import PostResponse

router = APIRouter(prefix="/api/v1/post", tags=["post"])


@router.post("/post", response_model=PostResponse)
async def post(payload):
    service = PostService()
    return await service.posting(payload)