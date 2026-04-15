import asyncio
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg
from dotenv import load_dotenv

load_dotenv()


def normalize_postgres_url(url: str) -> str:
    parsed = urlsplit(url.replace("postgresql+asyncpg://", "postgresql://"))
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("ssl", "require")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def build_candidate_urls() -> list[str]:
    candidates: list[str] = []
    base_url = os.getenv("DATABASE_URL", "").strip()
    if base_url:
        candidates.append(normalize_postgres_url(base_url))

    project_ref = os.getenv("SUPABASE_PROJECT_REF", "mxzmkxnbripcltuopawa").strip()
    db_password = os.getenv("SUPABASE_DB_PASSWORD", "Domixi%4012342005").strip()

    fallback_pooler_hosts = [
        "aws-0-ap-northeast-2.pooler.supabase.com",
        "aws-0-us-east-1.pooler.supabase.com",
        "aws-0-ap-southeast-1.pooler.supabase.com",
    ]

    for host in fallback_pooler_hosts:
        candidates.append(
            normalize_postgres_url(
                f"postgresql://postgres.{project_ref}:{db_password}@{host}:5432/postgres"
            )
        )
        candidates.append(
            normalize_postgres_url(
                f"postgresql://postgres.{project_ref}:{db_password}@{host}:6543/postgres"
            )
        )

    candidates.append(
        normalize_postgres_url(
            f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
        )
    )

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    return unique_candidates


async def try_connect(url: str) -> bool:
    redacted = url.replace(os.getenv("SUPABASE_DB_PASSWORD", ""), "***")
    print(f"Trying: {redacted}")
    try:
        conn = await asyncpg.connect(url, timeout=10)
        value = await conn.fetchval("select current_database()")
        server_version = await conn.fetchval("show server_version")
        await conn.close()
        print(f"Connected to database: {value}")
        print(f"Server version: {server_version}")
        return True
    except Exception as exc:
        print(f"Failed: {type(exc).__name__}: {exc}")
        return False


async def main():
    candidates = build_candidate_urls()
    print(f"Testing {len(candidates)} candidate DATABASE_URL values...")
    for url in candidates:
        ok = await try_connect(url)
        if ok:
            print("\nUse this DATABASE_URL in .env:")
            print(url.replace("postgresql://", "postgresql+asyncpg://", 1))
            return

    raise RuntimeError(
        "Could not connect with the current Supabase candidates. "
        "Copy the exact Session pooler connection string from Supabase Dashboard -> Connect."
    )

asyncio.run(main())
