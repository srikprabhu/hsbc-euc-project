"""
fastapi_app.py
==============
FastAPI backend for the EUC VBA -> Python Migration Platform.

The API owns:
    - workbook upload
    - run IDs
    - background pipeline execution
    - status
    - artifact download
    - business rules
    - token usage
    - logs

Run:
    uvicorn fastapi_app:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import json
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from main import run_pipeline


BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = BASE_DIR / "runtime"
RUN_DIR = RUNTIME_DIR / "runs"
RUN_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="EUC VBA to Python Migration API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS: dict[str, dict[str, Any]] = {}


def safe_filename(filename: str) -> str:
    filename = Path(
        filename or "workbook.xlsb"
    ).name

    return "".join(
        char
        if char.isalnum() or char in "._-"
        else "_"
        for char in filename
    )


def load_json(path: Path) -> Any:
    if not path.exists():
        return None

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return None


def collect_artifacts(
    output_dir: Path,
) -> dict[str, Any]:

    mapping = {
        "vba_modules":
            output_dir / "vba_modules.json",
        "procedure_analysis":
            output_dir / "procedure_analysis.json",
        "procedures":
            output_dir / "procedures.json",
        "business_rules":
            output_dir / "business_rules.json",
        "technical_business_rules":
            output_dir / "business_rules_technical.json",
        "business_rules_docx":
            output_dir / "business_rules.docx",
        "generated_python":
            output_dir / "generated_euc.py",
        "python_validation":
            output_dir / "generated_python_validation.json",
        "python_execution":
            output_dir / "generated_python_execution.json",
        "token_usage":
            output_dir / "token_usage.json",
        "pipeline_summary":
            output_dir / "pipeline_summary.json",
    }

    result: dict[str, Any] = {}

    for key, path in mapping.items():

        if path.exists():
            result[key] = str(
                path.resolve()
            )

    execution_dir = (
        output_dir / "test_execution"
    )

    if execution_dir.exists():

        result["generated_outputs"] = [
            str(
                path.resolve()
            )
            for path in sorted(
                execution_dir.glob("*.xlsx")
            )
        ]

    return result


def worker(
    run_id: str,
    input_path: Path,
    run_output_dir: Path,
) -> None:

    def progress_callback(
        step: int,
        message: str,
    ) -> None:

        RUNS[run_id].update(
            progress=min(
                99,
                max(
                    0,
                    int(
                        step * 100 / 7
                    ),
                ),
            ),
            current_step=message,
        )

    RUNS[run_id].update(
        status="RUNNING",
        progress=1,
        current_step="Starting pipeline",
    )

    try:

        summary = run_pipeline(
            input_path=input_path,
            output_dir=run_output_dir,
            progress_callback=progress_callback,
        )

        RUNS[run_id].update(
            status="COMPLETED",
            progress=100,
            current_step="Migration completed",
            summary=summary,
            artifacts=collect_artifacts(
                run_output_dir
            ),
            finished_at=time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    except Exception as exc:

        # Keep the last step reported by main.py so the UI can show exactly
        # where the pipeline stopped instead of incorrectly showing 100%.
        current = RUNS[run_id].get(
            "current_step",
            "Pipeline failed",
        )
        progress = RUNS[run_id].get(
            "progress",
            0,
        )

        RUNS[run_id].update(
            status="FAILED",
            progress=progress,
            current_step=current,
            error=f"{type(exc).__name__}: {exc}",
            artifacts=collect_artifacts(
                run_output_dir
            ),
            finished_at=time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "EUC Migration API",
    }


@app.post("/pipeline/run")
async def create_pipeline_run(
    file: UploadFile = File(...),
) -> dict[str, Any]:

    filename = safe_filename(
        file.filename or ""
    )

    if Path(filename).suffix.lower() not in {
        ".xlsb",
        ".xlsm",
    }:

        raise HTTPException(
            status_code=400,
            detail="Only XLSB and XLSM files are supported.",
        )

    run_id = (
        time.strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:8]
    )

    run_root = (
        RUN_DIR / run_id
    )

    input_dir = (
        run_root / "input"
    )

    output_dir = (
        run_root / "output"
    )

    input_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    input_path = (
        input_dir / filename
    )

    with input_path.open(
        "wb"
    ) as destination:

        shutil.copyfileobj(
            file.file,
            destination,
        )

    RUNS[run_id] = {
        "run_id": run_id,
        "status": "QUEUED",
        "progress": 0,
        "current_step": "Queued",
        "workbook": filename,
        "run_root": str(
            run_root.resolve()
        ),
        "output_dir": str(
            output_dir.resolve()
        ),
        "created_at": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    threading.Thread(
        target=worker,
        args=(
            run_id,
            input_path,
            output_dir,
        ),
        daemon=True,
    ).start()

    return {
        "run_id": run_id,
        "status": "QUEUED",
        "workbook": filename,
    }


@app.get("/pipeline/status/{run_id}")
def pipeline_status(
    run_id: str,
) -> dict[str, Any]:

    if run_id not in RUNS:
        raise HTTPException(
            status_code=404,
            detail="Run ID not found.",
        )

    return RUNS[run_id]


@app.get("/pipeline/results/{run_id}")
def pipeline_results(
    run_id: str,
) -> dict[str, Any]:

    if run_id not in RUNS:
        raise HTTPException(
            status_code=404,
            detail="Run ID not found.",
        )

    run = RUNS[run_id]

    return {
        "run_id": run_id,
        "status": run.get("status"),
        "summary": run.get(
            "summary",
            {},
        ),
        "artifacts": run.get(
            "artifacts",
            {},
        ),
    }


def find_artifact(
    run: dict[str, Any],
    artifact_name: str,
) -> Path | None:

    artifacts = run.get(
        "artifacts",
        {},
    )

    value = artifacts.get(
        artifact_name
    )

    if value:
        path = Path(value)

        if path.exists():
            return path

    # Excel report lookup by actual filename.
    for value in artifacts.get(
        "generated_outputs",
        [],
    ):

        path = Path(value)

        if path.name == artifact_name and path.exists():
            return path

    return None


@app.get("/files/{run_id}/{artifact_name:path}")
def download_file(
    run_id: str,
    artifact_name: str,
):
    """Download an artifact by logical key or physical relative filename.

    The Streamlit frontend uses logical keys for pipeline artifacts and
    physical filenames for generated Excel reports. Both are resolved
    dynamically within the run's output directory.
    """
    run = RUNS.get(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run ID not found.",
        )

    output_dir = Path(
        run["output_dir"]
    ).resolve()

    artifact_map = {
        "vba_modules": "vba_modules.json",
        "procedure_analysis": "procedure_analysis.json",
        "procedures": "procedures.json",
        "business_rules": "business_rules.json",
        "technical_business_rules": "business_rules_technical.json",
        "business_rules_docx": "business_rules.docx",
        "generated_python": "generated_euc.py",
        "python_validation": "generated_python_validation.json",
        "python_execution": "generated_python_execution.json",
        "token_usage": "token_usage.json",
        "pipeline_summary": "pipeline_summary.json",
    }

    logical_key = artifact_name.strip("/")
    relative_name = artifact_map.get(
        logical_key,
        logical_key,
    )

    candidate = (
        output_dir / relative_name
    ).resolve()

    # Prevent path traversal outside the run output directory.
    try:
        candidate.relative_to(output_dir)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid artifact path.",
        )

    if not candidate.exists() or not candidate.is_file():
        # Generated Excel reports live under test_execution/.
        execution_candidate = (
            output_dir / "test_execution" / Path(relative_name).name
        ).resolve()

        try:
            execution_candidate.relative_to(output_dir)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid artifact path.",
            )

        if execution_candidate.exists() and execution_candidate.is_file():
            candidate = execution_candidate
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact not found: {artifact_name}",
            )

    return FileResponse(
        path=str(candidate),
        filename=candidate.name,
    )


@app.get("/pipeline/rules/{run_id}")
def pipeline_rules(
    run_id: str,
) -> Any:

    if run_id not in RUNS:
        raise HTTPException(
            status_code=404,
            detail="Run ID not found.",
        )

    path = find_artifact(
        RUNS[run_id],
        "business_rules",
    )

    if path is None:
        return {
            "rules": [],
            "rule_count": 0,
        }

    return load_json(path) or {
        "rules": [],
        "rule_count": 0,
    }



@app.get("/pipeline/logs/{run_id}")
def pipeline_logs(
    run_id: str,
) -> dict[str, Any]:

    if run_id not in RUNS:
        raise HTTPException(
            status_code=404,
            detail="Run ID not found.",
        )

    output_dir = Path(
        RUNS[run_id]["output_dir"]
    )

    log_file = (
        output_dir
        / "logs"
        / "pipeline.log"
    )

    text = ""

    if log_file.exists():
        text = log_file.read_text(
            encoding="utf-8",
            errors="replace",
        )

    return {
        "run_id": run_id,
        "status": RUNS[run_id].get(
            "status",
            "UNKNOWN",
        ),
        "log_file": str(log_file),
        "content": text[-30000:],
    }


@app.get("/pipeline/tokens/{run_id}")
def pipeline_tokens(
    run_id: str,
) -> Any:

    if run_id not in RUNS:
        raise HTTPException(
            status_code=404,
            detail="Run ID not found.",
        )

    output_dir = Path(
        RUNS[run_id]["output_dir"]
    )

    candidates = [
        output_dir / "token_usage.json",
        output_dir / "token_usage_summary.json",
        output_dir / "logs" / "token_usage.json",
    ]

    for path in candidates:

        data = load_json(path)

        if data is not None:
            return data

    return {
        "steps": [],
        "message": "No token tracker output found.",
    }
