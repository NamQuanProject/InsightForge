import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dotenv import load_dotenv
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
