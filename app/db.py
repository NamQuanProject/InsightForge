import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/insightforge",
)


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(_normalize_database_url(DATABASE_URL), future=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_db_session():
    async with get_session_factory()() as session:
        yield session


async def init_db() -> None:
    import app.models  # noqa: F401

    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS upload_post_account JSONB NOT NULL DEFAULT '{}'::jsonb,
                ADD COLUMN IF NOT EXISTS profiles JSONB NOT NULL DEFAULT '[]'::jsonb,
                ADD COLUMN IF NOT EXISTS social_accounts JSONB NOT NULL DEFAULT '{}'::jsonb,
                ADD COLUMN IF NOT EXISTS connected_platforms JSONB NOT NULL DEFAULT '[]'::jsonb
                """
            )
        )
        await connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS image_store (
                    id TEXT PRIMARY KEY,
                    image_url TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    local_path TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        await connection.execute(
            text(
                """
                ALTER TABLE image_store
                ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS local_path TEXT
                """
            )
        )
        await connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_image_store_created_at ON image_store (created_at DESC)"
            )
        )
        await connection.execute(text("NOTIFY pgrst, 'reload schema'"))


def _normalize_database_url(url: str) -> str:
    """
    Ensure Supabase/Postgres URLs include SSL mode when not already present.
    Supabase pooler/direct Postgres expects TLS by default.
    """
    if not url.startswith("postgresql"):
        return url

    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("ssl", "require")
    normalized_query = urlencode(query)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, normalized_query, parsed.fragment))
