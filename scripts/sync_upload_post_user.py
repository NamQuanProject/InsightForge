import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import init_db
from app.services.postgres_service import PostgresService
from app.services.upload_post_service import UploadPostApiService


async def main() -> None:
    await init_db()

    upload_post = UploadPostApiService()
    bundle = upload_post.get_account_bundle()
    account = bundle["account"]
    email = account.get("email")
    if not email:
        raise RuntimeError("Upload-Post account response did not include an email.")

    user = await PostgresService().upsert_user(
        email=str(email),
        name=upload_post.get_configured_profile_username(),
        plan=account.get("plan"),
        upload_post_account=account,
        profiles=bundle["profiles"],
        social_accounts=bundle["social_accounts"],
        connected_platforms=bundle["connected_platforms"],
    )

    print(
        json.dumps(
            {
                "user_id": str(user.id),
                "email": user.email,
                "plan": user.plan,
                "profile_count": len(user.profiles or []),
                "profile_usernames": [profile.get("username") for profile in (user.profiles or [])],
                "connected_platforms": user.connected_platforms or [],
                "social_account_platforms": sorted((user.social_accounts or {}).keys()),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
