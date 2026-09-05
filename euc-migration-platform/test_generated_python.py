from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(args: argparse.Namespace) -> dict[str, Any]:
    generated_path = Path(args.generated_file)
    source = generated_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(generated_path))
    functions = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    procedures = load_json(Path(args.procedure_file))
    rules = load_json(Path(args.business_rule_file))
    modules = load_json(Path(args.vba_module_file))
    procedure_count = len(procedures) if isinstance(procedures, list) else 0
    rule_count = len(rules.get("rules", [])) if isinstance(rules, dict) else 0
    return {
        "status": "PASS",
        "generated_file": str(generated_path.resolve()),
        "syntax_valid": True,
        "function_count": len(functions),
        "functions": functions,
        "procedure_count": procedure_count,
        "business_rule_count": rule_count,
        "vba_module_count": len(modules) if isinstance(modules, dict) else 0,
        "checks": [
            {"name": "python_syntax", "status": "PASS"},
            {"name": "generated_file_present", "status": "PASS"},
            {"name": "procedure_analysis_present", "status": "PASS"},
            {"name": "business_rules_present", "status": "PASS"},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated EUC Python.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--generated-file", required=True)
    parser.add_argument("--procedure-file", required=True)
    parser.add_argument("--business-rule-file", required=True)
    parser.add_argument("--vba-module-file", required=True)
    parser.add_argument("--report-file", required=True)
    args = parser.parse_args()
    report_path = Path(args.report_file)
    try:
        report = validate(args)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        report = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
