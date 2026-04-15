import uuid

from fastapi import APIRouter, HTTPException, Query

from app.schema.trend import (
    TrendAnalysesListResponse,
    TrendAnalysisRecordResponse,
    TrendAnalyzeRequest,
    TrendAnalyzeResponse,
    TrendOverviewResponse,
)
from app.services.trend_service import TrendService

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


@router.post("/analyze", response_model=TrendAnalyzeResponse)
async def analyze_trend(payload: TrendAnalyzeRequest):
    service = TrendService()
    return await service.analyze(query=payload.query, limit=payload.limit, user_id=payload.user_id)


@router.get("/history", response_model=TrendAnalysesListResponse)
async def list_trend_history(
    user_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    service = TrendService()
    return await service.list_history(user_id=user_id, limit=limit)


@router.get("/mock/overview", response_model=TrendOverviewResponse)
async def get_mock_trend_overview(
    keyword: str = Query(
        default="ai video editor",
        min_length=3,
        description="Seed keyword used to personalize the mock Google Trends and TikTok payload.",
    ),
    region: str = Query(
        default="VN",
        min_length=2,
        max_length=5,
        description="Region code reflected in the mock data.",
    ),
    hashtag: str = Query(
        default="aivideo",
        min_length=2,
        description="TikTok hashtag seed used in the mock payload.",
    ),
):
    service = TrendService()
    return service.get_mock_overview(keyword=keyword, region=region, hashtag=hashtag)


@router.get("/{analysis_id}", response_model=TrendAnalysisRecordResponse)
async def get_trend_detail(analysis_id: uuid.UUID):
    service = TrendService()
    record = await service.get_detail(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Trend analysis not found: {analysis_id}")
    return record
