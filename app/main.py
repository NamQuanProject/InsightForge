from fastapi import FastAPI

from app.api.agents import router as agents_router
from app.api.content import router as content_router
from app.api.health import router as health_router
from app.api.trend import router as trend_router
from app.api.upload_post import router as upload_post_router
from app.api.users import router as users_router
from app.db import init_db

app = FastAPI(
    title="InsightForge API",
    version="0.1.0",
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
