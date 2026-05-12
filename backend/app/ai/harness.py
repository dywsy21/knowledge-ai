from __future__ import annotations

import json

from pydantic import BaseModel

from app.ai.prompts import (
    INTERACTION_GENERATION_SYSTEM,
    KNOWLEDGE_EXTRACTION_SYSTEM,
    VALUE_ASSESSMENT_SYSTEM,
)
from app.ai.providers import BaseAIProvider, LiteLLMProvider, MockAIProvider
from app.ai.schemas import (
    AIMessage,
    AIResult,
    AISettings,
    AITask,
    InteractionDraft,
    KnowledgeExtraction,
    KnowledgeUnit,
    KnowledgeValueAssessment,
)


class AIHarness:
    def __init__(
        self,
        provider: BaseAIProvider,
        settings: AISettings | None = None,
        fallback_provider: BaseAIProvider | None = None,
    ) -> None:
        self.provider = provider
        self.settings = settings or AISettings()
        self.fallback_provider = fallback_provider

    def extract_knowledge_units(
        self,
        source_text: str,
        *,
        source_title: str = "Untitled source",
        domain: str = "general",
    ) -> KnowledgeExtraction:
        result = self._run(
            AITask.EXTRACT_KNOWLEDGE,
            [
                AIMessage(role="system", content=KNOWLEDGE_EXTRACTION_SYSTEM),
                AIMessage(
                    role="user",
                    content=(
                        f"Source title: {source_title}\n"
                        f"Domain: {domain}\n"
                        f"Source text:\n{source_text}"
                    ),
                ),
            ],
            KnowledgeExtraction,
        )
        return KnowledgeExtraction.model_validate(result.content)

    def assess_knowledge_value(
        self,
        source_text: str,
        *,
        domain: str = "general",
    ) -> KnowledgeValueAssessment:
        result = self._run(
            AITask.ASSESS_VALUE,
            [
                AIMessage(role="system", content=VALUE_ASSESSMENT_SYSTEM),
                AIMessage(role="user", content=f"Domain: {domain}\nSource text:\n{source_text}"),
            ],
            KnowledgeValueAssessment,
        )
        return KnowledgeValueAssessment.model_validate(result.content)

    def generate_interaction(
        self,
        units: list[KnowledgeUnit],
        *,
        domain: str = "general",
        template: str = "decision_scenario",
    ) -> InteractionDraft:
        unit_payload = [unit.model_dump() for unit in units]
        result = self._run(
            AITask.GENERATE_INTERACTION,
            [
                AIMessage(role="system", content=INTERACTION_GENERATION_SYSTEM),
                AIMessage(
                    role="user",
                    content=(
                        f"Domain: {domain}\n"
                        f"Preferred template: {template}\n"
                        f"Knowledge units:\n{json.dumps(unit_payload, ensure_ascii=False)}"
                    ),
                ),
            ],
            InteractionDraft,
        )
        return InteractionDraft.model_validate(result.content)

    def _run(
        self,
        task: AITask,
        messages: list[AIMessage],
        response_model: type[BaseModel],
    ) -> AIResult:
        try:
            return self.provider.generate_json(task, messages, response_model, self.settings)
        except Exception:
            if not self.fallback_provider:
                raise
            return self.fallback_provider.generate_json(task, messages, response_model, self.settings)


def build_ai_harness(
    provider_name: str = "mock",
    model: str | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    timeout_seconds: float = 30,
) -> AIHarness:
    settings = AISettings(
        model=model or ("mock/local" if provider_name == "mock" else "openai/gpt-4o-mini"),
        api_base=api_base,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
    )
    if provider_name == "litellm":
        return AIHarness(LiteLLMProvider(), settings=settings, fallback_provider=MockAIProvider())
    return AIHarness(MockAIProvider(), settings=settings)
