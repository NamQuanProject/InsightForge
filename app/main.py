from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.trend import router as trends_router
from app.api.post import router as post_router

app = FastAPI(
    title="InsightForge API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(trends_router)
app.include_router(post_router)