from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class AITask(str, Enum):
    EXTRACT_KNOWLEDGE = "extract_knowledge"
    ASSESS_VALUE = "assess_value"
    GENERATE_INTERACTION = "generate_interaction"
    REVIEW_INTERACTION = "review_interaction"
    RECOMMEND_NEXT = "recommend_next"
    SUMMARIZE_SIGNALS = "summarize_signals"


class AIMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class AISettings(BaseModel):
    model: str = "mock/local"
    api_base: str | None = None
    api_key: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2000
    timeout_seconds: float = 30


class AIResult(BaseModel):
    task: AITask
    provider: str
    model: str
    content: dict[str, Any]
    raw_text: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class KnowledgeUnit(BaseModel):
    title: str
    summary: str
    unit_type: Literal[
        "concept",
        "rule",
        "risk",
        "procedure",
        "decision",
        "case",
        "metric",
        "question",
    ]
    domain: str = "general"
    tags: list[str] = Field(default_factory=list)
    difficulty: Literal["intro", "basic", "intermediate", "advanced"] = "basic"
    evidence: list[str] = Field(default_factory=list)


class KnowledgeExtraction(BaseModel):
    source_title: str
    source_summary: str
    domain: str = "general"
    units: list[KnowledgeUnit]
    warnings: list[str] = Field(default_factory=list)


class InteractionChoice(BaseModel):
    id: str
    label: str
    is_correct: bool = False
    feedback: str


class InteractionStep(BaseModel):
    id: str
    prompt: str
    choices: list[InteractionChoice]
    explanation: str


class InteractionDraft(BaseModel):
    title: str
    objective: str
    template: Literal[
        "decision_scenario",
        "anomaly_spotting",
        "incident_reconstruction",
        "process_ordering",
        "risk_triage",
        "role_dialogue",
        "flash_review",
    ]
    domain: str = "general"
    estimated_minutes: int = Field(default=5, ge=1, le=60)
    difficulty: Literal["intro", "basic", "intermediate", "advanced"] = "basic"
    steps: list[InteractionStep]
    source_unit_titles: list[str] = Field(default_factory=list)


class KnowledgeValueAssessment(BaseModel):
    education_value: int = Field(ge=1, le=5)
    interaction_fit: int = Field(ge=1, le=5)
    freshness: int = Field(ge=1, le=5)
    risk_if_wrong: int = Field(ge=1, le=5)
    recommended_templates: list[str] = Field(default_factory=list)
    rationale: str
