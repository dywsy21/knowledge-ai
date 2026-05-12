from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.ai import build_ai_harness
from app.ai.schemas import KnowledgeExtraction
from app.core.config import get_settings
from app.platform.models import (
    EvolutionSummary,
    FeedbackCreate,
    FullChainRequest,
    FullChainResponse,
    Interaction,
    InteractionCreate,
    KnowledgeSource,
    KnowledgeSourceCreate,
)
from app.platform.object_storage import build_object_store
from app.platform.store import PlatformStore

app = FastAPI(title="Knowledge Evolution Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def get_store() -> PlatformStore:
    settings = get_settings()
    object_store = build_object_store(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
    )
    return PlatformStore(
        build_ai_harness(
            settings.ai_provider,
            settings.ai_model,
            api_base=settings.ai_api_base,
            api_key=settings.ai_api_key,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout_seconds=settings.ai_timeout_seconds,
        ),
        object_store=object_store,
        seed=False,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/summary", response_model=EvolutionSummary)
def summary() -> EvolutionSummary:
    return get_store().summary()


@app.post("/sources", response_model=KnowledgeSource)
def create_source(payload: KnowledgeSourceCreate) -> KnowledgeSource:
    return get_store().create_source(payload)


@app.get("/sources", response_model=list[KnowledgeSource])
def list_sources() -> list[KnowledgeSource]:
    return get_store().list_sources()


@app.get("/sources/{source_id}", response_model=KnowledgeSource)
def get_source(source_id: str) -> KnowledgeSource:
    try:
        return get_store().get_source(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc


@app.post("/sources/{source_id}/extract", response_model=KnowledgeSource)
def extract_source(source_id: str) -> KnowledgeSource:
    try:
        return get_store().extract_source(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc


@app.post("/interactions", response_model=Interaction)
def create_interaction(payload: InteractionCreate) -> Interaction:
    try:
        return get_store().create_interaction(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source not found") from exc


@app.get("/interactions", response_model=list[Interaction])
def list_interactions() -> list[Interaction]:
    return get_store().list_interactions()


@app.get("/interactions/{interaction_id}", response_model=Interaction)
def get_interaction(interaction_id: str) -> Interaction:
    try:
        return get_store().get_interaction(interaction_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Interaction not found") from exc


@app.post("/feedback", response_model=Interaction)
def submit_feedback(payload: FeedbackCreate) -> Interaction:
    try:
        return get_store().submit_feedback(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Interaction not found") from exc


@app.post("/full-chain", response_model=FullChainResponse)
def full_chain(payload: FullChainRequest) -> FullChainResponse:
    return get_store().full_chain(payload)


@app.post("/ai/extract", response_model=KnowledgeExtraction)
def extract(payload: dict[str, str]) -> KnowledgeExtraction:
    settings = get_settings()
    harness = build_ai_harness(
        settings.ai_provider,
        settings.ai_model,
        api_base=settings.ai_api_base,
        api_key=settings.ai_api_key,
        temperature=settings.ai_temperature,
        max_tokens=settings.ai_max_tokens,
        timeout_seconds=settings.ai_timeout_seconds,
    )
    return harness.extract_knowledge_units(
        payload.get("text", ""),
        source_title=payload.get("title", "Untitled source"),
        domain=payload.get("domain", "general"),
    )
