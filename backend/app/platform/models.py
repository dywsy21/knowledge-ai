from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.ai.schemas import InteractionDraft, KnowledgeExtraction, KnowledgeUnit


class SourceStatus(str, Enum):
    DRAFT = "draft"
    EXTRACTED = "extracted"


class InteractionStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"


class KnowledgeSourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1)
    domain: str = "general"
    tags: list[str] = Field(default_factory=list)


class KnowledgeSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    content: str
    domain: str = "general"
    tags: list[str] = Field(default_factory=list)
    object_bucket: str | None = None
    object_key: str | None = None
    object_sha256: str | None = None
    object_bytes: int = 0
    status: SourceStatus = SourceStatus.DRAFT
    extraction: KnowledgeExtraction | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InteractionCreate(BaseModel):
    source_id: str
    unit_titles: list[str] = Field(default_factory=list)
    template: str = "decision_scenario"


class Interaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    draft: InteractionDraft
    status: InteractionStatus = InteractionStatus.PUBLISHED
    score: float = 0
    plays: int = 0
    completions: int = 0
    likes: int = 0
    reports: int = 0
    avg_quality: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FeedbackCreate(BaseModel):
    interaction_id: str
    completed: bool = True
    liked: bool = False
    reported: bool = False
    quality: int = Field(default=4, ge=1, le=5)
    time_seconds: int = Field(default=120, ge=0)


class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    interaction_id: str
    completed: bool
    liked: bool
    reported: bool
    quality: int
    time_seconds: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvolutionSummary(BaseModel):
    total_sources: int
    total_units: int
    total_interactions: int
    total_feedback: int
    top_interactions: list[Interaction]
    recent_sources: list[KnowledgeSource]


class FullChainRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1)
    domain: str = "general"
    tags: list[str] = Field(default_factory=list)
    template: str = "decision_scenario"


class FullChainResponse(BaseModel):
    source: KnowledgeSource
    units: list[KnowledgeUnit]
    interaction: Interaction
