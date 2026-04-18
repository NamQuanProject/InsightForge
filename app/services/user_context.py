import os
import uuid


DEFAULT_USER_ID = os.getenv(
    "INSIGHTFORGE_DEFAULT_USER_ID",
    "cd129113-895c-4800-b4e4-48d63bf46d12",
)


def resolve_user_id(user_id: uuid.UUID | str | None = None) -> uuid.UUID | None:
    candidate = user_id or DEFAULT_USER_ID
    if not candidate:
        return None

    try:
        return uuid.UUID(str(candidate))
    except ValueError:
        return None
