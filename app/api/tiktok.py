from fastapi import APIRouter

from app.schema.common import UploadVideoRequest, UploadVideoResponse
from app.schema.tiktok import (
    TikTokChannelStatusResponse,
    TikTokRecommendationsResponse,
    TikTokTrendsResponse,
    TikTokVideoDetailResponse,
    TikTokVideosResponse,
)
from app.services.tiktok_service import TikTokService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1/tiktok", tags=["tiktok"])


@router.post("/upload", response_model=UploadVideoResponse)
async def upload_tiktok_video(payload: UploadVideoRequest):
    return UploadService().upload(platform="tiktok", payload=payload)


@router.get("/channel/status", response_model=TikTokChannelStatusResponse)
async def get_tiktok_channel_status():
    return TikTokService().get_channel_status()


@router.get("/trends", response_model=TikTokTrendsResponse)
async def get_tiktok_trends():
    return TikTokService().get_trends()


@router.get("/recommendations", response_model=TikTokRecommendationsResponse)
async def get_tiktok_recommendations():
    return TikTokService().get_recommendations()


@router.get("/videos/{video_id}", response_model=TikTokVideoDetailResponse)
async def get_tiktok_video(video_id: str):
    return TikTokService().get_video(video_id)


@router.get("/videos", response_model=TikTokVideosResponse)
async def get_tiktok_videos():
    return TikTokService().get_videos()
