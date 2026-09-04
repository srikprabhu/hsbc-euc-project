"""
main.py
=======

Single orchestration entry point for:

Excel VBA EUC
      ↓
1. VBA extraction
      ↓
2. Procedure parsing
      ↓
3. LLM procedure analysis
      ↓
4. LLM business-rule extraction
      ↓
5. LLM Python generation
      ↓
6. Static Python validation
      ↓
7. Generated Python execution

      ↓
Excel reports

Compatible with:
    fastapi_app.py
    streamlit_app.py

Dynamic:
    - Input workbook name
    - Procedure names
    - Output directory
    - Generated Python
    - Execution reports

CLI:
    python main.py --input input\\EUC_Macro_1.xlsb

"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


# =====================================================================
# EXISTING PROJECT COMPONENTS
# =====================================================================

from app.agent.business_rule_agent import (
    analyze_business_rules,
    build_technical_business_rules,
)
from app.agent.procedure_agent import analyze_procedure
from app.agent.python_code_agent import generate_python_code

from app.services.vba_extractor import extract_vba_modules
from app.services.vba_procedure_parser import split_procedures


# =====================================================================
# CONFIGURATION
# =====================================================================

BASE_DIR = Path(__file__).resolve().parent

ProgressCallback = Callable[[int, str], None]


# =====================================================================
# LOGGING
# =====================================================================

def configure_logging(output_dir: Path) -> logging.Logger:

    log_dir = output_dir / "logs"
    log_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("euc_pipeline")

    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        log_dir / "pipeline.log",
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(
        sys.stdout
    )

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# =====================================================================
# UTILITIES
# =====================================================================

def emit(
    callback: ProgressCallback | None,
    step: int,
    message: str,
) -> None:

    if callback:
        callback(
            step,
            message,
        )


def write_json(
    path: Path,
    data: Any,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def normalize_procedures(
    modules: dict[str, str],
) -> list[dict[str, Any]]:

    procedures = []

    for module_name, source in modules.items():

        parsed = split_procedures(source)

        for procedure in parsed:

            item = dict(procedure)

            item.setdefault(
                "module",
                module_name,
            )

            item.setdefault(
                "procedure",
                item.get(
                    "procedure_name",
                    item.get(
                        "name",
                        "",
                    ),
                ),
            )

            procedures.append(item)

    return procedures


# =====================================================================
# STEP 1
# =====================================================================

def step_1_extract_vba(
    input_path: Path,
    output_dir: Path,
    logger: logging.Logger,
) -> dict[str, str]:

    logger.info(
        "STEP 1 | VBA raw extraction | input=%s",
        input_path.name,
    )

    modules = extract_vba_modules(
        str(input_path)
    )

    if not isinstance(
        modules,
        dict,
    ):
        raise TypeError(
            "extract_vba_modules() must return a dictionary."
        )

    write_json(
        output_dir / "vba_modules.json",
        modules,
    )

    logger.info(
        "STEP 1 | completed | modules=%d",
        len(modules),
    )

    return modules


# =====================================================================
# STEP 2
# =====================================================================

def step_2_parse_procedures(
    modules: dict[str, str],
    output_dir: Path,
    logger: logging.Logger,
) -> list[dict[str, Any]]:

    logger.info(
        "STEP 2 | procedure parsing"
    )

    procedures = normalize_procedures(
        modules
    )

    write_json(
        output_dir / "procedures.json",
        procedures,
    )

    logger.info(
        "STEP 2 | completed | procedures=%d",
        len(procedures),
    )

    return procedures


# =====================================================================
# STEP 3
# =====================================================================

def step_3_procedure_agent(
    workbook_name: str,
    procedures: list[dict[str, Any]],
    output_dir: Path,
    logger: logging.Logger,
) -> list[dict[str, Any]]:

    logger.info(
        "STEP 3 | procedure analysis | procedures=%d",
        len(procedures),
    )

    results = []

    for index, procedure in enumerate(
        procedures,
        start=1,
    ):

        procedure_name = procedure.get(
            "procedure",
            procedure.get(
                "procedure_name",
                procedure.get(
                    "name",
                    "",
                ),
            ),
        )

        source_code = procedure.get(
            "code",
            procedure.get(
                "source",
                "",
            ),
        )

        module_name = procedure.get(
            "module",
            "",
        )

        logger.info(
            "STEP 3 | %d/%d | %s",
            index,
            len(procedures),
            procedure_name,
        )

        # IMPORTANT:
        # Current procedure_agent.py contract:
        #
        # analyze_procedure(
        #     module_name,
        #     procedure_name,
        #     source_code,
        #     workbook_name
        # )

        analysis = analyze_procedure(
            module_name=module_name,
            procedure_name=procedure_name,
            source_code=source_code,
            workbook_name=workbook_name,
        )

        if isinstance(
            analysis,
            dict,
        ):

            analysis.setdefault(
                "module",
                module_name,
            )

            analysis.setdefault(
                "procedure",
                procedure_name,
            )

            results.append(
                analysis
            )

    write_json(
        output_dir / "procedure_analysis.json",
        results,
    )

    logger.info(
        "STEP 3 | completed | analyses=%d",
        len(results),
    )

    return results


# =====================================================================
# STEP 4
# =====================================================================

def step_4_business_rules(
    workbook_name: str,
    procedure_analysis: list[dict[str, Any]],
    output_dir: Path,
    logger: logging.Logger,
) -> dict[str, Any]:

    logger.info(
        "STEP 4 | business-rule extraction"
    )

    result = analyze_business_rules(
        workbook_name=workbook_name,
        procedure_analysis=procedure_analysis,
    )

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            "Business rule agent must return a dictionary."
        )

    write_json(
        output_dir / "business_rules.json",
        result,
    )

    # MASTER JSON keeps the business-facing structure.
    # Rules are nested under business_rule_extraction.rules.
    business_rule_extraction = result.get(
        "business_rule_extraction",
        {},
    )
    rules = business_rule_extraction.get(
        "rules",
        [],
    )

    # Build the compact technical contract used by Step 5/6.
    technical = build_technical_business_rules(result)

    write_json(
        output_dir / "business_rules_technical.json",
        technical,
    )

    logger.info(
        "STEP 4 | completed | rules=%d",
        len(rules),
    )

    if not rules:
        raise RuntimeError(
            "Step 4 produced zero business rules. "
            "Expected rules under 'business_rule_extraction.rules'."
        )

    return result


# =====================================================================
# STEP 5
# =====================================================================

def step_5_generate_python(
    workbook_name: str,
    procedure_analysis: list[dict[str, Any]],
    business_rules: dict[str, Any],
    vba_modules: dict[str, str],
    output_dir: Path,
    logger: logging.Logger,
) -> Path:

    logger.info(
        "STEP 5 | Python code generation"
    )

    code = generate_python_code(
        workbook_name=workbook_name,
        procedure_analysis=procedure_analysis,
        business_rules=business_rules,
        vba_modules=vba_modules,
    )

    if not isinstance(
        code,
        str,
    ) or not code.strip():

        raise RuntimeError(
            "Python code agent returned empty code."
        )

    generated_file = (
        output_dir / "generated_euc.py"
    )

    generated_file.write_text(
        code,
        encoding="utf-8",
    )

    logger.info(
        "STEP 5 | completed | generated=%s",
        generated_file,
    )

    return generated_file


# =====================================================================
# STEPS 6 / 7
# =====================================================================

def run_existing_script(
    script_name: str,
    arguments: list[str],
    output_dir: Path,
    logger: logging.Logger,
) -> None:

    script_path = BASE_DIR / script_name

    if not script_path.exists():

        raise FileNotFoundError(
            f"Required script not found: {script_path}"
        )

    command = [
        sys.executable,
        str(script_path),
        *arguments,
    ]

    logger.info(
        "RUN | %s",
        " ".join(command),
    )

    environment = os.environ.copy()

    # Dynamic input/output context
    environment["EUC_OUTPUT_DIR"] = str(
        output_dir
    )

    process = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        env=environment,
    )

    if process.stdout:

        logger.info(
            "%s",
            process.stdout.strip(),
        )

    if process.returncode != 0:

        if process.stderr:

            logger.error(
                "%s",
                process.stderr.strip(),
            )

        raise RuntimeError(
            f"{script_name} failed with exit code "
            f"{process.returncode}."
        )


# =====================================================================
# MAIN PIPELINE
# =====================================================================

def run_pipeline(
    input_path: Path,
    output_dir: Path | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:

    # ---------------------------------------------------------------
    # Dynamic input
    # ---------------------------------------------------------------

    input_path = Path(
        input_path
    ).resolve()

    if not input_path.exists():

        raise FileNotFoundError(
            f"Workbook not found: {input_path}"
        )

    if input_path.suffix.lower() not in {
        ".xlsb",
        ".xlsm",
    }:

        raise ValueError(
            "Only XLSB and XLSM workbooks are supported."
        )

    # ---------------------------------------------------------------
    # Dynamic output
    # ---------------------------------------------------------------

    if output_dir is None:

        output_dir = (
            BASE_DIR / "output"
        )

    output_dir = Path(
        output_dir
    ).resolve()

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # IMPORTANT:
    # Always use the actual uploaded workbook name.
    # ---------------------------------------------------------------

    workbook_name = input_path.name

    logger = configure_logging(
        output_dir
    )

    started = time.perf_counter()

    logger.info(
        "=" * 72
    )

    logger.info(
        "EUC MIGRATION STARTED | workbook=%s",
        workbook_name,
    )

    steps = []

    # ===============================================================
    # STEP EXECUTOR
    # ===============================================================

    def execute_step(
        number: int,
        name: str,
        function,
    ):

        step_started = time.perf_counter()

        emit(
            progress_callback,
            number,
            f"Step {number} - {name}",
        )

        logger.info(
            "STEP %d | START | %s",
            number,
            name,
        )

        try:

            value = function()

            duration = round(
                time.perf_counter()
                - step_started,
                3,
            )

            steps.append(
                {
                    "step": number,
                    "name": name,
                    "status": "SUCCESS",
                    "duration_seconds": duration,
                }
            )

            logger.info(
                "STEP %d | SUCCESS | %.3fs",
                number,
                duration,
            )

            return value

        except Exception as exc:

            duration = round(
                time.perf_counter()
                - step_started,
                3,
            )

            steps.append(
                {
                    "step": number,
                    "name": name,
                    "status": "FAILED",
                    "duration_seconds": duration,
                    "error":
                        f"{type(exc).__name__}: {exc}",
                }
            )

            logger.exception(
                "STEP %d | FAILED | %s",
                number,
                name,
            )

            raise

    # ===============================================================
    # STEP 1
    # ===============================================================

    modules = execute_step(
        1,
        "VBA raw extraction",
        lambda: step_1_extract_vba(
            input_path,
            output_dir,
            logger,
        ),
    )

    # ===============================================================
    # STEP 2
    # ===============================================================

    procedures = execute_step(
        2,
        "Procedure parsing",
        lambda: step_2_parse_procedures(
            modules,
            output_dir,
            logger,
        ),
    )

    # ===============================================================
    # STEP 3
    # ===============================================================

    procedure_analysis = execute_step(
        3,
        "Procedure analysis",
        lambda: step_3_procedure_agent(
            workbook_name,
            procedures,
            output_dir,
            logger,
        ),
    )

    # ===============================================================
    # STEP 4
    # ===============================================================

    business_rules = execute_step(
        4,
        "Business-rule extraction",
        lambda: step_4_business_rules(
            workbook_name,
            procedure_analysis,
            output_dir,
            logger,
        ),
    )

    # Step 4 now produces a business-facing MASTER JSON plus a
    # compact technical JSON contract for downstream code generation.
    # Keep the MASTER JSON for UI/BRD, but pass the technical contract
    # to Step 5 because the Python Code Agent expects {workbook, rules, rule_count}.
    technical_business_rules = build_technical_business_rules(
        business_rules
    )

    technical_rule_count = len(
        technical_business_rules.get("rules", [])
    )

    logger.info(
        "STEP 4 | technical contract ready | rules=%d",
        technical_rule_count,
    )

    if technical_rule_count == 0:
        raise RuntimeError(
            "Business Rule Agent produced no technical rules. "
            "Expected business_rules_technical.json with a non-empty 'rules' list."
        )

    # ===============================================================
    # STEP 5
    # ===============================================================

    generated_file = execute_step(
        5,
        "Python code generation",
        lambda: step_5_generate_python(
            workbook_name,
            procedure_analysis,
            technical_business_rules,
            modules,
            output_dir,
            logger,
        ),
    )

    # ===============================================================
    # STEP 6
    #
    # Keep existing validator.
    # It receives dynamic paths.
    # ===============================================================

    # ===============================================================
    # STEP 6
    #
    # Keep existing validator unchanged.
    # IMPORTANT:
    # test_generated_python.py does NOT accept --output-dir.
    # It expects the explicit input/report JSON file arguments.
    # ===============================================================

    validation_report = (
        output_dir / "generated_python_validation.json"
    )

    execute_step(
        6,
        "Static Python validation",
        lambda: run_existing_script(
            "test_generated_python.py",
            [
                "--input",
                str(input_path),

                "--generated-file",
                str(generated_file),

                "--procedure-file",
                str(output_dir / "procedure_analysis.json"),

                "--business-rule-file",
                str(output_dir / "business_rules_technical.json"),

                "--vba-module-file",
                str(output_dir / "vba_modules.json"),

                "--report-file",
                str(validation_report),
            ],
            output_dir,
            logger,
        ),
    )

    # ===============================================================
    # STEP 7
    #
    # IMPORTANT:
    # Do NOT hard-code Mat_Var,
    # ASF_RSF_Var,
    # Prod_Type_Var.
    #
    # Step 7 discovers procedures dynamically.
    # ===============================================================

    execution_dir = (
        output_dir / "test_execution"
    )

    execution_report = (
        output_dir
        / "generated_python_execution.json"
    )

    execute_step(
        7,
        "Generated Python execution",
        lambda: run_existing_script(
            "test_generated_execution.py",
            [
                "--input",
                str(input_path),

                "--generated-file",
                str(generated_file),

                "--output-dir",
                str(execution_dir),

                "--report-file",
                str(execution_report),
            ],
            output_dir,
            logger,
        ),
    )

    # ===============================================================
    # SUMMARY
    # ===============================================================

    elapsed = round(
        time.perf_counter()
        - started,
        3,
    )

    validation_data = None

    validation_file = (
        output_dir
        / "generated_python_validation.json"
    )

    if validation_file.exists():

        try:

            validation_data = json.loads(
                validation_file.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            validation_data = None

    execution_data = None

    if execution_report.exists():

        try:

            execution_data = json.loads(
                execution_report.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            execution_data = None

    rules = technical_business_rules.get(
        "rules",
        [],
    )

    # ===============================================================
    # GENERATED OUTPUTS
    # ===============================================================

    generated_outputs = []

    if execution_dir.exists():

        generated_outputs = [
            str(path.resolve())
            for path in sorted(
                execution_dir.glob("*.xlsx")
            )
        ]

    # ===============================================================
    # PIPELINE SUMMARY
    # ===============================================================

    summary = {
        "status": "COMPLETED",

        "workbook": workbook_name,

        "input_file":
            str(input_path),

        "procedure_count":
            len(procedures),

        "business_rule_count":
            len(rules),

        "generated_python":
            str(generated_file),

        "validation":
            validation_data,

        "execution":
            execution_data,

        "generated_outputs":
            generated_outputs,

        "steps":
            steps,

        "duration_seconds":
            elapsed,

        "output_dir":
            str(output_dir),
    }

    write_json(
        output_dir / "pipeline_summary.json",
        summary,
    )

    logger.info(
        "EUC MIGRATION COMPLETED | %.3fs",
        elapsed,
    )

    return summary


# =====================================================================
# CLI
# =====================================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Run complete EUC VBA -> Python migration."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to XLSB/XLSM workbook.",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory.",
    )

    args = parser.parse_args()

    input_path = Path(
        args.input
    )

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else BASE_DIR / "output"
    )

    try:

        result = run_pipeline(
            input_path=input_path,
            output_dir=output_dir,
        )

        print()
        print("=" * 80)
        print("PIPELINE COMPLETED")
        print("=" * 80)

        print(
            "Workbook:",
            result["workbook"],
        )

        print(
            "Procedures:",
            result["procedure_count"],
        )

        print(
            "Business Rules:",
            result["business_rule_count"],
        )

        print(
            "Generated Python:",
            result["generated_python"],
        )

        print(
            "Generated Outputs:",
            len(
                result["generated_outputs"]
            ),
        )

        print(
            "Output Directory:",
            result["output_dir"],
        )

        return 0

    except Exception as exc:

        print()
        print("=" * 80)
        print("PIPELINE FAILED")
        print("=" * 80)

        print(
            f"{type(exc).__name__}: {exc}"
        )

        return 1


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )