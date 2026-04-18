# import uuid

# from fastapi import APIRouter, HTTPException, Query

# from app.schema.content import (
#     ContentGenerateRequest,
#     GeneratedContentResponse,
#     GeneratedContentsListResponse,
# )
# from app.services.content_service import ContentService

# router = APIRouter(prefix="/api/v1/contents", tags=["contents"])


# @router.post("/generate", response_model=GeneratedContentResponse)
# async def generate_content(payload: ContentGenerateRequest):
#     service = ContentService()
#     try:
#         return await service.generate(
#             prompt=payload.prompt,
#             user_id=payload.user_id,
#             trend_analysis_id=payload.trend_analysis_id,
#             selected_keyword=payload.selected_keyword,
#         )
#     except ValueError as exc:
#         raise HTTPException(status_code=400, detail=str(exc)) from exc


# @router.get("", response_model=GeneratedContentsListResponse)
# async def list_generated_contents(
#     user_id: uuid.UUID | None = Query(default=None),
#     limit: int = Query(default=20, ge=1, le=100),
# ):
#     service = ContentService()
#     items = await service.list_contents(user_id=user_id, limit=limit)
#     return GeneratedContentsListResponse(items=items)


# @router.get("/{content_id}", response_model=GeneratedContentResponse)
# async def get_generated_content(content_id: uuid.UUID):
#     service = ContentService()
#     item = await service.get_content(content_id)
#     if item is None:
#         raise HTTPException(status_code=404, detail=f"Generated content not found: {content_id}")
#     return item
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.schema.content import (
    ContentGenerateRequest,
    GeneratedContentResponse,
    GeneratedContentsListResponse,
)
from app.services.content_service import ContentService

router = APIRouter(prefix="/api/v1/contents", tags=["contents"])
legacy_router = APIRouter(tags=["contents"])


@router.post("/generate", response_model=GeneratedContentResponse)
async def generate_content(payload: ContentGenerateRequest):
    service = ContentService()
    try:
        return await service.generate(
            prompt=payload.prompt,
            user_id=payload.user_id,
            trend_analysis_id=payload.trend_analysis_id,
            selected_keyword=payload.selected_keyword,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=GeneratedContentsListResponse)
async def list_generated_contents(
    user_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    return await _list_generated_contents(user_id=user_id, limit=limit)


@legacy_router.get("/generated-contents", response_model=GeneratedContentsListResponse)
async def list_generated_contents_legacy(
    user_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    parsed_user_id = _parse_optional_uuid(user_id)
    if user_id and parsed_user_id is None:
        return GeneratedContentsListResponse(items=[])
    return await _list_generated_contents(user_id=parsed_user_id, limit=limit)


def _parse_optional_uuid(value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


async def _list_generated_contents(
    user_id: uuid.UUID | None,
    limit: int,
) -> GeneratedContentsListResponse:
    service = ContentService()
    items = await service.list_contents(user_id=user_id, limit=limit)
    return GeneratedContentsListResponse(items=items)


@router.get("/{content_id}", response_model=GeneratedContentResponse)
async def get_generated_content(content_id: uuid.UUID):
    service = ContentService()
    item = await service.get_content(content_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Generated content not found: {content_id}")
    return item
