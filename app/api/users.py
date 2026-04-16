import uuid

from fastapi import APIRouter, HTTPException

from app.schema.user import UserCreateRequest, UserResponse, UsersListResponse
from app.services.postgres_service import PostgresService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("", response_model=UserResponse)
async def create_user(payload: UserCreateRequest):
    service = PostgresService()
    return await service.create_user(
        email=payload.email,
        name=payload.name,
        plan=payload.plan,
        upload_post_account=payload.upload_post_account,
        profiles=payload.profiles,
        social_accounts=payload.social_accounts,
        connected_platforms=payload.connected_platforms,
    )


@router.get("", response_model=UsersListResponse)
async def list_users():
    service = PostgresService()
    users = await service.list_user_summaries()
    return UsersListResponse(users=users)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID):
    service = PostgresService()
    user = await service.get_user_response(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
    return user
