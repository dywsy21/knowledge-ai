from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ai.schemas import (
    AIMessage,
    AIResult,
    AISettings,
    AITask,
    InteractionChoice,
    InteractionDraft,
    InteractionStep,
    KnowledgeExtraction,
    KnowledgeUnit,
    KnowledgeValueAssessment,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AIProviderError(RuntimeError):
    pass


class BaseAIProvider(ABC):
    name: str

    @abstractmethod
    def generate_json(
        self,
        task: AITask,
        messages: list[AIMessage],
        response_model: type[SchemaT],
        settings: AISettings,
    ) -> AIResult:
        raise NotImplementedError


class MockAIProvider(BaseAIProvider):
    name = "mock"

    def generate_json(
        self,
        task: AITask,
        messages: list[AIMessage],
        response_model: type[SchemaT],
        settings: AISettings,
    ) -> AIResult:
        user_text = " ".join(message.content for message in messages if message.role == "user")
        payload = self._payload_for(task, user_text)
        parsed = response_model.model_validate(payload)
        return AIResult(
            task=task,
            provider=self.name,
            model=settings.model,
            content=parsed.model_dump(),
            raw_text=json.dumps(payload, ensure_ascii=False),
        )

    def _payload_for(self, task: AITask, text: str) -> dict[str, Any]:
        if task == AITask.EXTRACT_KNOWLEDGE:
            title = self._field_from(text, "Source title") or self._title_from(text)
            body = self._field_from(text, "Source text") or text
            unit = KnowledgeUnit(
                title=f"Core idea: {title}",
                summary=self._summary_from(body),
                unit_type="concept",
                domain=self._field_from(text, "Domain") or "general",
                tags=["generated", "mock"],
                difficulty="basic",
                evidence=[body[:220]] if body else [],
            )
            return KnowledgeExtraction(
                source_title=title,
                source_summary=self._summary_from(body),
                domain=self._field_from(text, "Domain") or "general",
                units=[unit],
            ).model_dump()

        if task == AITask.ASSESS_VALUE:
            return KnowledgeValueAssessment(
                education_value=4,
                interaction_fit=4,
                freshness=3,
                risk_if_wrong=3,
                recommended_templates=["decision_scenario", "flash_review"],
                rationale="The source contains enough structure for a basic interactive learning item.",
            ).model_dump()

        if task == AITask.GENERATE_INTERACTION:
            unit_title = self._first_unit_title(text)
            choice_a = InteractionChoice(
                id="a",
                label="Apply the stated rule or principle.",
                is_correct=True,
                feedback="Correct. This choice follows the extracted knowledge unit.",
            )
            choice_b = InteractionChoice(
                id="b",
                label="Ignore the source context and choose by habit.",
                is_correct=False,
                feedback="This misses the source-specific constraint.",
            )
            step = InteractionStep(
                id="step-1",
                prompt="Which action best applies the provided knowledge?",
                choices=[choice_a, choice_b],
                explanation="The best answer uses the supplied source knowledge instead of an unrelated assumption.",
            )
            return InteractionDraft(
                title=f"Decision practice: {unit_title}",
                objective="Practice applying one extracted knowledge unit.",
                template="decision_scenario",
                domain=self._field_from(text, "Domain") or "general",
                estimated_minutes=3,
                difficulty="basic",
                steps=[step],
                source_unit_titles=[unit_title],
            ).model_dump()

        return {"summary": self._summary_from(text)}

    def _title_from(self, text: str) -> str:
        clean = " ".join(text.split())
        return clean[:64] or "Untitled source"

    def _summary_from(self, text: str) -> str:
        clean = " ".join(text.split())
        return clean[:240] or "No source content was provided."

    def _field_from(self, text: str, field_name: str) -> str | None:
        match = re.search(rf"^{re.escape(field_name)}:\s*(.+)$", text, flags=re.MULTILINE)
        return match.group(1).strip() if match else None

    def _first_unit_title(self, text: str) -> str:
        marker = "Knowledge units:"
        if marker in text:
            raw = text.split(marker, 1)[1].strip()
            try:
                units = json.loads(raw)
                if units and units[0].get("title"):
                    return str(units[0]["title"])
            except json.JSONDecodeError:
                pass
        return self._title_from(text)


class LiteLLMProvider(BaseAIProvider):
    name = "litellm"

    def generate_json(
        self,
        task: AITask,
        messages: list[AIMessage],
        response_model: type[SchemaT],
        settings: AISettings,
    ) -> AIResult:
        try:
            from litellm import completion
        except ImportError as exc:
            raise AIProviderError("LiteLLM is not installed. Install backend requirements.") from exc

        litellm_messages = [message.model_dump() for message in messages]
        litellm_messages.append(
            {
                "role": "user",
                "content": (
                    "Return valid JSON only. The JSON must match this schema: "
                    f"{json.dumps(response_model.model_json_schema(), ensure_ascii=False)}"
                ),
            }
        )

        response = None
        raw_text = ""
        try:
            json_schema = response_model.model_json_schema()
            response = self._complete(
                completion,
                litellm_messages,
                settings,
                {
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "schema": json_schema,
                        "strict": True,
                    },
                },
            )
            raw_text = response.choices[0].message.content or ""
            payload = self._parse_json(raw_text)
            parsed = response_model.model_validate(payload)
        except Exception as exc:
            try:
                response = self._complete(
                    completion,
                    litellm_messages,
                    settings,
                    {"type": "text"},
                )
                raw_text = response.choices[0].message.content or ""
                payload = self._parse_json(raw_text)
                parsed = response_model.model_validate(payload)
            except Exception as fallback_exc:
                raise AIProviderError(
                    f"Model returned invalid JSON for {task.value}: {raw_text}"
                ) from fallback_exc

        usage = getattr(response, "usage", None)
        return AIResult(
            task=task,
            provider=self.name,
            model=settings.model,
            content=parsed.model_dump(),
            raw_text=raw_text,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        )

    def _complete(
        self,
        completion: Any,
        messages: list[dict[str, str]],
        settings: AISettings,
        response_format: dict[str, Any],
    ) -> Any:
        return completion(
            model=settings.model,
            messages=messages,
            api_base=settings.api_base,
            api_key=settings.api_key,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout_seconds,
            response_format=response_format,
        )

    def _parse_json(self, text: str) -> dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            raise ValueError("empty model response")
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
            stripped = re.sub(r"\s*```$", "", stripped)
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start >= 0 and end > start:
                return json.loads(stripped[start : end + 1])
            raise
