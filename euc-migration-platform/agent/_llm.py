from __future__ import annotations

import json
import re
from typing import Any


def _parse_json(content: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = min((position for position in (cleaned.find("{"), cleaned.find("[")) if position >= 0), default=-1)
        if start < 0:
            raise
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        return json.loads(cleaned[start:end + 1])


def complete_json(system_prompt: str, user_prompt: str, step: int) -> Any | None:
    """Invoke the project's Gemini wrapper and decode a JSON response.

    Missing credentials or optional Gemini dependencies intentionally return
    ``None`` so each agent can use its deterministic contract-preserving fallback.
    """
    try:
        try:
            from llm import get_llm
        except ImportError:
            from app.llm import get_llm

        response = get_llm(step=step).invoke(
            f"{system_prompt}\n\nReturn JSON only.\n\n{user_prompt}"
        )
        return _parse_json(response.content)
    except Exception as exc:
        print(f"[LLM] Step {step} unavailable: {type(exc).__name__}: {exc}")
        return None
