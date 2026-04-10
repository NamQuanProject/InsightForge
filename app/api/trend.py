from fastapi import APIRouter, Query
from app.schema.trend import (
    TrendAnalyzeRequest,
    TrendAnalyzeResponse,
    TrendOverviewResponse,
)
from app.services.trend_service import TrendService

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


@router.post("/analyze", response_model=TrendAnalyzeResponse)
async def analyze_trend(payload: TrendAnalyzeRequest):
    service = TrendService()
    return await service.analyze(payload.query)


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
