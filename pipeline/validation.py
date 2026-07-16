from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


# ---------- Support Bot ----------

class SupportQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    customer_email: Optional[EmailStr] = None
    session_id: Optional[str] = None  # For conversation context


class SupportAnswerResponse(BaseModel):
    answer: str
    escalated: bool
    source: Literal["cache", "agent"]
    session_id: Optional[str] = None  # Return session ID for context


class KnowledgeDocRequest(BaseModel):
    text: str = Field(..., min_length=10)
    metadata: dict = Field(default_factory=dict)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    n_results: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list


class BulkImportResponse(BaseModel):
    status: str
    imported_count: int
    failed_count: int
    errors: list


# ---------- Content Generator ----------

class ContentBriefRequest(BaseModel):
    content_type: Literal["social_post", "email", "blog_intro", "ad_copy"]
    platform: str = Field(..., min_length=2)
    topic: str = Field(..., min_length=3)
    tone: str = "professional"
    audience: str = "general"
    max_length: int = Field(default=280, ge=20, le=5000)


class ContentResponse(BaseModel):
    content: str


# ---------- Data Analyst ----------

class AnalysisTaskResponse(BaseModel):
    task_id: str
    status: str


class AnalysisStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None


# ---------- Analytics ----------

class DailyMetricsResponse(BaseModel):
    date: str
    total_requests: int
    agent_metrics: dict
    cache: dict


class LatencyStatsResponse(BaseModel):
    count: int
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


class TrendsResponse(BaseModel):
    trends: list
