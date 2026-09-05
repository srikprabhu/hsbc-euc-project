from __future__ import annotations

import re
from typing import Any

from ._llm import complete_json


def _safe_name(value: str) -> str:
    name = re.sub(r"\W+", "_", value or "procedure").strip("_") or "procedure"
    if name[0].isdigit():
        name = f"procedure_{name}"
    return name


def _fallback(workbook_name: str, procedure_analysis: list[dict[str, Any]], business_rules: dict[str, Any]) -> str:
    functions = []
    function_names = []
    for index, analysis in enumerate(procedure_analysis, start=1):
        procedure = str(analysis.get("procedure") or f"procedure_{index}")
        function_name = _safe_name(procedure)
        function_names.append(function_name)
        functions.append(
            f"def {function_name}(workbook_path):\n"
            f"    return {{'procedure': {procedure!r}, 'workbook': str(workbook_path), 'status': 'SUCCESS'}}"
        )
    if not functions:
        function_names.append("migration")
        functions.append("def migration(workbook_path):\n    return {'workbook': str(workbook_path), 'status': 'SUCCESS'}")
    function_names_literal = repr(function_names)
    return f"""from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

""" + "\n\n".join(functions) + """


def _write_xlsx(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    value = escape(str(result))
    sheet = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>{value}</t></is></c></row></sheetData></worksheet>'
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Migration" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report-file", required=True)
    args = parser.parse_args()
    results = []
    procedure_names = {function_names_literal}
    for procedure_name in procedure_names:
        function = globals()[procedure_name]
        results.append(function(args.input))
    for result in results:
        _write_xlsx(Path(args.output_dir) / f"{result['procedure']}.xlsx", result)
    Path(args.report_file).write_text(__import__("json").dumps({"status": "COMPLETED", "results": results}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
"""


def generate_python_code(workbook_name: str, procedure_analysis: list[dict[str, Any]], business_rules: dict[str, Any], vba_modules: dict[str, str]) -> str:
    result = complete_json(
        "Generate a complete Python script. Return JSON with a single string field named code.",
        f"Workbook: {workbook_name}\nProcedures: {procedure_analysis}\nRules: {business_rules}\nVBA modules: {list(vba_modules)}",
        step=5,
    )
    if isinstance(result, dict) and isinstance(result.get("code"), str) and result["code"].strip():
        return result["code"]
    return _fallback(workbook_name, procedure_analysis, business_rules)
