from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from ._llm import complete_json


def _fallback(workbook_name: str, procedure_analysis: list[dict[str, Any]]) -> dict[str, Any]:
    rules = []
    for index, analysis in enumerate(procedure_analysis, start=1):
        name = str(analysis.get("procedure") or f"Procedure_{index}")
        logic = analysis.get("business_logic") or [f"Execute the {name} procedure as defined in the VBA source."]
        rules.append({
            "id": f"BR-{index:03d}",
            "name": f"{name} processing rule",
            "description": " ".join(str(item) for item in logic),
            "source_procedure": name,
            "source_module": analysis.get("module", ""),
            "implementation_notes": "Preserve source procedure order and dependencies.",
        })
    return {
        "workbook": workbook_name,
        "business_rule_extraction": {
            "rules": rules,
            "rule_count": len(rules),
        },
        "analysis_mode": "deterministic-fallback",
    }


def analyze_business_rules(workbook_name: str, procedure_analysis: list[dict[str, Any]]) -> dict[str, Any]:
    fallback = _fallback(workbook_name, procedure_analysis)
    result = complete_json(
        "Extract business rules from VBA procedure analyses. Return JSON with business_rule_extraction.rules.",
        f"Workbook: {workbook_name}\nAnalyses:\n{procedure_analysis}",
        step=4,
    )
    if not isinstance(result, dict):
        return fallback
    extraction = result.get("business_rule_extraction")
    if not isinstance(extraction, dict) or not isinstance(extraction.get("rules"), list) or not extraction["rules"]:
        return fallback
    result.setdefault("workbook", workbook_name)
    return result


def build_technical_business_rules(result: dict[str, Any]) -> dict[str, Any]:
    extraction = result.get("business_rule_extraction", {})
    rules = extraction.get("rules", []) if isinstance(extraction, dict) else []
    return {
        "workbook": result.get("workbook", ""),
        "rules": rules,
        "rule_count": len(rules),
    }


def write_business_rules_docx(result: dict[str, Any], output_path: Path) -> None:
    """Write the business-facing rule register as a minimal DOCX document."""
    extraction = result.get("business_rule_extraction", {})
    rules = extraction.get("rules", []) if isinstance(extraction, dict) else []
    paragraphs = [
        "Business Rules Document",
        f"Workbook: {result.get('workbook', '')}",
        f"Rule count: {len(rules)}",
    ]
    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            continue
        paragraphs.extend([
            f"{index}. {rule.get('name', f'Business Rule {index}')}",
            f"Description: {rule.get('description', '')}",
            f"Source procedure: {rule.get('source_procedure', '')}",
            f"Source module: {rule.get('source_module', '')}",
            f"Implementation notes: {rule.get('implementation_notes', '')}",
            "",
        ])

    body = "".join(
        f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(str(text))}</w:t></w:r></w:p>"
        for text in paragraphs
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
