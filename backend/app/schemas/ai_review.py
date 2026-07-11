from pydantic import BaseModel, Field


class OllamaHealthResponse(BaseModel):
    status: str = Field(..., examples=["available"])
    model: str
    models_available: list[str] = Field(default_factory=list)
    base_url: str


class AIReviewIssueOutput(BaseModel):
    file_path: str
    line_start: int = Field(ge=1)
    line_end: int | None = None
    category: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    title: str
    explanation: str
    suggestion: str


class AIReviewOutput(BaseModel):
    summary: str
    issues: list[AIReviewIssueOutput] = Field(default_factory=list)
