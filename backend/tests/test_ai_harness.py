from app.ai import build_ai_harness
from app.platform.models import FeedbackCreate, FullChainRequest
from app.platform.store import PlatformStore


def test_mock_extracts_knowledge_units() -> None:
    harness = build_ai_harness("mock")

    extraction = harness.extract_knowledge_units(
        "A good incident review identifies the triggering event, contributing factors, and controls.",
        source_title="Incident review basics",
    )

    assert extraction.source_title
    assert extraction.units
    assert extraction.units[0].unit_type == "concept"


def test_mock_generates_interaction_from_extraction() -> None:
    harness = build_ai_harness("mock")
    extraction = harness.extract_knowledge_units("Teams should validate a policy before applying it.")

    interaction = harness.generate_interaction(extraction.units)

    assert interaction.steps
    assert interaction.steps[0].choices
    assert any(choice.is_correct for choice in interaction.steps[0].choices)


def test_platform_store_runs_full_chain_and_feedback() -> None:
    store = PlatformStore(build_ai_harness("mock"))

    result = store.full_chain(
        FullChainRequest(
            title="Policy validation",
            content="Teams should validate a policy before applying it to a high-risk case.",
        )
    )
    previous_score = result.interaction.score
    updated = store.submit_feedback(
        FeedbackCreate(
            interaction_id=result.interaction.id,
            completed=True,
            liked=True,
            quality=5,
            time_seconds=180,
        )
    )

    assert result.units
    assert updated.plays == 1
    assert updated.score > previous_score
