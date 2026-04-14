from fastapi import FastAPI
from app.api.health import router as health_router
# from app.api.tiktok import router as tiktok_router
from app.api.trend import router as trend_router
from app.api.upload_post import router as upload_post_router
# from app.api.youtube import router as youtube_router

app = FastAPI(
    title="InsightForge API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(trend_router)
app.include_router(upload_post_router)
