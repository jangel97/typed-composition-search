from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .graph import Path
from .registry import Registry

if TYPE_CHECKING:
    pass

_SYSTEM_PROMPT = """You are a type predictor for a tool composition system.

Given a user query, predict:
- source_type: The entity type the user already has or starts from
- target_type: The entity type the user wants to obtain

Available entity types:
{entity_types}

Respond ONLY with a JSON object:
{{"source_type": "...", "target_type": "..."}}"""


@dataclass(frozen=True)
class Prediction:
    source_type: str
    target_type: str


def _parse_prediction(text: str) -> Prediction:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in response: {text!r}")
    obj = json.loads(text[start:end])
    source = obj.get("source_type")
    target = obj.get("target_type")
    if not source or not target:
        raise ValueError(f"Missing source_type or target_type in response: {obj!r}")
    return Prediction(source_type=source, target_type=target)


def _build_system_prompt(entity_types: dict[str, str]) -> str:
    lines = [f"- {name}: {desc}" for name, desc in sorted(entity_types.items())]
    return _SYSTEM_PROMPT.format(entity_types="\n".join(lines))


class TypePredictor:
    def __init__(
        self,
        model: str,
        entity_types: dict[str, str],
        **litellm_kwargs: Any,
    ) -> None:
        try:
            import litellm as _litellm
        except ImportError:
            raise ImportError(
                "litellm is required for TypePredictor. "
                "Install it with: pip install toolgraph[llm]"
            )
        self._litellm = _litellm
        self._model = model
        self._entity_types = dict(entity_types)
        self._litellm_kwargs = litellm_kwargs
        self._system_prompt = _build_system_prompt(entity_types)

    def predict(self, query: str) -> Prediction:
        response = self._litellm.completion(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0,
            **self._litellm_kwargs,
        )
        text = response.choices[0].message.content or ""
        return _parse_prediction(text.strip())

    def resolve(self, query: str, registry: Registry) -> Path | None:
        prediction = self.predict(query)
        return registry.resolve(prediction.source_type, prediction.target_type)
