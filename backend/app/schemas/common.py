from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


class ReadyResponse(BaseModel):
    status: str = Field(..., examples=["ready"])
    database: str = Field(..., examples=["connected"])


class ErrorResponse(BaseModel):
    detail: str
