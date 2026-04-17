import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.content import router as content_router
from app.api.health import router as health_router
from app.api.trend import router as trend_router
from app.api.upload_post import router as upload_post_router
from app.api.users import router as users_router
from app.db import init_db
from app.api.post import router as post_router

app = FastAPI(
    title="InsightForge API",
    version="0.1.0",
)

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def get_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or list(DEFAULT_CORS_ORIGINS)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


app.include_router(health_router)
app.include_router(users_router)
app.include_router(trend_router)
app.include_router(content_router)
app.include_router(upload_post_router)
app.include_router(agents_router)
app.include_router(post_router)
