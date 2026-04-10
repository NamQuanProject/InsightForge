from fastapi import APIRouter

from app.schema.common import UploadVideoRequest, UploadVideoResponse
from app.schema.youtube import (
    YouTubeChannelStatusResponse,
    YouTubeRecommendationsResponse,
    YouTubeTrendsResponse,
    YouTubeVideoDetailResponse,
    YouTubeVideosResponse,
)
from app.services.youtube_service import YouTubeService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1/youtube", tags=["youtube"])


@router.post("/upload", response_model=UploadVideoResponse)
async def upload_youtube_video(payload: UploadVideoRequest):
    return UploadService().upload(platform="youtube", payload=payload)


@router.get("/channel/status", response_model=YouTubeChannelStatusResponse)
async def get_youtube_channel_status():
    return YouTubeService().get_channel_status()


@router.get("/trends", response_model=YouTubeTrendsResponse)
async def get_youtube_trends():
    return YouTubeService().get_trends()


@router.get("/recommendations", response_model=YouTubeRecommendationsResponse)
async def get_youtube_recommendations():
    return YouTubeService().get_recommendations()


@router.get("/videos/{video_id}", response_model=YouTubeVideoDetailResponse)
async def get_youtube_video(video_id: str):
    return YouTubeService().get_video(video_id)


@router.get("/videos", response_model=YouTubeVideosResponse)
async def get_youtube_videos():
    return YouTubeService().get_videos()
