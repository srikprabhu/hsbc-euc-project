from __future__ import annotations

import re
from typing import Any

from ._llm import complete_json


def _fallback(module_name: str, procedure_name: str, source_code: str, workbook_name: str) -> dict[str, Any]:
    calls = sorted(set(re.findall(r"\b(?:Call\s+)?([A-Za-z_]\w*)\s*(?:\(|$)", source_code, re.IGNORECASE)))
    return {
        "module": module_name,
        "procedure": procedure_name,
        "workbook": workbook_name,
        "purpose": f"Executes the VBA procedure {procedure_name}.",
        "inputs": [],
        "outputs": [],
        "business_logic": ["Preserve the procedure control flow and workbook interactions."],
        "dependencies": calls,
        "source_code": source_code,
        "analysis_mode": "deterministic-fallback",
    }


def analyze_procedure(module_name: str, procedure_name: str, source_code: str, workbook_name: str) -> dict[str, Any]:
    fallback = _fallback(module_name, procedure_name, source_code, workbook_name)
    result = complete_json(
        "Analyze one VBA procedure. Return JSON with purpose, inputs, outputs, business_logic, dependencies.",
        f"Workbook: {workbook_name}\nModule: {module_name}\nProcedure: {procedure_name}\nVBA:\n{source_code}",
        step=3,
    )
    if not isinstance(result, dict):
        return fallback
    fallback.update(result)
    fallback["source_code"] = source_code
    fallback["module"] = module_name
    fallback["procedure"] = procedure_name
    return fallback
