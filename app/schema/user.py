from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    email: str = Field(..., min_length=3)
    name: str | None = None
    plan: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str | None = None
    plan: str | None = None
    created_at: datetime


class UsersListResponse(BaseModel):
    users: list[UserResponse] = Field(default_factory=list)
