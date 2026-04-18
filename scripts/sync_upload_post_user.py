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
        display_name=upload_post.get_configured_profile_username(),
        options={
            "linked_platforms": bundle["connected_platforms"],
        },
    )

    print(
        json.dumps(
            {
                "user_id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "linked_platforms": (user.options or {}).get("linked_platforms", []),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
