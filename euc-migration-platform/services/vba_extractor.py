from __future__ import annotations

from pathlib import Path
from typing import Any


def _oletools_extract(path: Path) -> dict[str, str] | None:
    try:
        from oletools.olevba import VBA_Parser
    except ImportError:
        return None

    parser = VBA_Parser(str(path))
    modules: dict[str, str] = {}
    try:
        if not parser.detect_vba_macros():
            return {}
        for _, stream_path, vba_filename, code in parser.extract_macros():
            modules[vba_filename or stream_path] = code
    finally:
        parser.close()
    return modules


def extract_vba_modules(workbook_path: str) -> dict[str, str]:
    path = Path(workbook_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")
    if path.suffix.lower() not in {".xlsb", ".xlsm"}:
        raise ValueError("Only XLSB and XLSM workbooks are supported.")

    modules = _oletools_extract(path)
    if modules is not None:
        return modules

    raise RuntimeError(
        "VBA extraction requires the optional 'oletools' package. "
        "Install it with: python -m pip install oletools"
    )
