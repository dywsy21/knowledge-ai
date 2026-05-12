from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from app.ai.harness import AIHarness
from app.platform.models import (
    EvolutionSummary,
    Feedback,
    FeedbackCreate,
    FullChainRequest,
    FullChainResponse,
    Interaction,
    InteractionCreate,
    KnowledgeSource,
    KnowledgeSourceCreate,
    SourceStatus,
)
from app.platform.object_storage import DisabledObjectStore, ObjectStore


class PlatformStore:
    def __init__(
        self,
        harness: AIHarness,
        object_store: ObjectStore | None = None,
        *,
        seed: bool = True,
    ) -> None:
        self.harness = harness
        self.object_store = object_store or DisabledObjectStore()
        self.sources: dict[str, KnowledgeSource] = {}
        self.interactions: dict[str, Interaction] = {}
        self.feedback: list[Feedback] = []
        if seed:
            self._seed()

    def create_source(self, payload: KnowledgeSourceCreate) -> KnowledgeSource:
        source = KnowledgeSource(**payload.model_dump())
        encoded = source.content.encode("utf-8")
        source.object_sha256 = sha256(encoded).hexdigest()
        source.object_bytes = len(encoded)
        stored = self.object_store.put_text(
            f"sources/{source.id}/source.txt",
            source.content,
        )
        if stored.bucket != "disabled":
            source.object_bucket = stored.bucket
            source.object_key = stored.key
        self.sources[source.id] = source
        return source

    def list_sources(self) -> list[KnowledgeSource]:
        return sorted(self.sources.values(), key=lambda item: item.created_at, reverse=True)

    def get_source(self, source_id: str) -> KnowledgeSource:
        return self.sources[source_id]

    def extract_source(self, source_id: str) -> KnowledgeSource:
        source = self.get_source(source_id)
        extraction = self.harness.extract_knowledge_units(
            source.content,
            source_title=source.title,
            domain=source.domain,
        )
        source.extraction = extraction
        source.status = SourceStatus.EXTRACTED
        source.updated_at = datetime.now(UTC)
        self.sources[source.id] = source
        return source

    def create_interaction(self, payload: InteractionCreate) -> Interaction:
        source = self.get_source(payload.source_id)
        if source.extraction is None:
            source = self.extract_source(source.id)

        units = source.extraction.units if source.extraction else []
        if payload.unit_titles:
            selected = [unit for unit in units if unit.title in payload.unit_titles]
            units = selected or units

        draft = self.harness.generate_interaction(
            units,
            domain=source.domain,
            template=payload.template,
        )
        interaction = Interaction(source_id=source.id, draft=draft)
        interaction.score = self._score_interaction(interaction)
        self.interactions[interaction.id] = interaction
        return interaction

    def list_interactions(self) -> list[Interaction]:
        return sorted(self.interactions.values(), key=lambda item: item.score, reverse=True)

    def get_interaction(self, interaction_id: str) -> Interaction:
        return self.interactions[interaction_id]

    def submit_feedback(self, payload: FeedbackCreate) -> Interaction:
        interaction = self.get_interaction(payload.interaction_id)
        event = Feedback(**payload.model_dump())
        self.feedback.append(event)

        interaction.plays += 1
        interaction.completions += 1 if event.completed else 0
        interaction.likes += 1 if event.liked else 0
        interaction.reports += 1 if event.reported else 0
        previous_count = max(interaction.plays - 1, 0)
        interaction.avg_quality = (
            ((interaction.avg_quality * previous_count) + event.quality) / interaction.plays
            if interaction.plays
            else event.quality
        )
        interaction.score = self._score_interaction(interaction)
        interaction.updated_at = datetime.now(UTC)
        self.interactions[interaction.id] = interaction
        return interaction

    def full_chain(self, payload: FullChainRequest) -> FullChainResponse:
        source = self.create_source(KnowledgeSourceCreate(**payload.model_dump(exclude={"template"})))
        source = self.extract_source(source.id)
        interaction = self.create_interaction(
            InteractionCreate(source_id=source.id, template=payload.template)
        )
        return FullChainResponse(
            source=source,
            units=source.extraction.units if source.extraction else [],
            interaction=interaction,
        )

    def summary(self) -> EvolutionSummary:
        total_units = sum(
            len(source.extraction.units)
            for source in self.sources.values()
            if source.extraction is not None
        )
        return EvolutionSummary(
            total_sources=len(self.sources),
            total_units=total_units,
            total_interactions=len(self.interactions),
            total_feedback=len(self.feedback),
            top_interactions=self.list_interactions()[:5],
            recent_sources=self.list_sources()[:5],
        )

    def _score_interaction(self, interaction: Interaction) -> float:
        completion_rate = interaction.completions / interaction.plays if interaction.plays else 0
        like_bonus = interaction.likes * 1.5
        report_penalty = interaction.reports * 3
        quality_bonus = interaction.avg_quality * 4
        engagement = interaction.plays * 0.8
        base = 25
        return round(base + quality_bonus + engagement + (completion_rate * 20) + like_bonus - report_penalty, 2)

    def _seed(self) -> None:
        sample = KnowledgeSourceCreate(
            title="Incident Review Playbook",
            domain="general operations",
            tags=["safety", "review"],
            content=(
                "A useful incident review identifies the triggering event, contributing factors, "
                "controls that failed, and follow-up actions. Teams should avoid blaming individuals "
                "before checking whether the process, tools, or training created the conditions for error."
            ),
        )
        source = self.create_source(sample)
        self.extract_source(source.id)
        self.create_interaction(InteractionCreate(source_id=source.id))
