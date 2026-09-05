from __future__ import annotations

import argparse
import importlib.util
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


def safe_name(value: str) -> str:
    name = re.sub(r"\W+", "_", value or "procedure").strip("_") or "procedure"
    return f"procedure_{name}" if name[0].isdigit() else name


def write_xlsx(path: Path, result: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = escape(json.dumps(result, ensure_ascii=False, default=str))
    sheet = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>{text}</t></is></c></row></sheetData></worksheet>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'''
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Migration" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    relationships = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    workbook_relationships = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute generated EUC Python procedures.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--generated-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report-file", required=True)
    args = parser.parse_args()
    report_path = Path(args.report_file)
    results = []
    try:
        module_spec = importlib.util.spec_from_file_location("generated_euc", args.generated_file)
        if module_spec is None or module_spec.loader is None:
            raise RuntimeError("Unable to load generated Python module.")
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        procedure_file = Path(args.generated_file).with_name("procedure_analysis.json")
        procedure_names = []
        if procedure_file.exists():
            data = json.loads(procedure_file.read_text(encoding="utf-8"))
            procedure_names = [item.get("procedure") for item in data if isinstance(item, dict)]
        functions = []
        for procedure_name in procedure_names:
            function = getattr(module, safe_name(str(procedure_name)), None)
            if callable(function):
                functions.append((str(procedure_name), function))
        if not functions:
            functions = [(name, value) for name, value in vars(module).items() if callable(value) and not name.startswith("_")]
        output_dir = Path(args.output_dir)
        for procedure_name, function in functions:
            try:
                result = function(args.input)
                output_path = output_dir / f"{safe_name(procedure_name)}.xlsx"
                write_xlsx(output_path, result)
                results.append({"procedure": procedure_name, "status": "SUCCESS", "output": str(output_path.resolve())})
            except Exception as exc:
                results.append({"procedure": procedure_name, "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})
        status = "COMPLETED" if results and all(item["status"] == "SUCCESS" for item in results) else "FAILED"
        report = {"status": status, "results": results}
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0 if status == "COMPLETED" else 1
    except Exception as exc:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "FAILED", "results": results, "error": f"{type(exc).__name__}: {exc}"}, indent=2), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
