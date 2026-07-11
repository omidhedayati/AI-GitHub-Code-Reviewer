import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.repository import RepositoryStatus


class RepositoryCreate(BaseModel):
    url: str = Field(min_length=3, max_length=512)
    branch: str | None = Field(default=None, max_length=255)


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    owner: str
    name: str
    default_branch: str | None
    local_path: str | None
    status: RepositoryStatus
    error_message: str | None
    cloned_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RepositoryListResponse(BaseModel):
    items: list[RepositoryResponse]
    total: int
