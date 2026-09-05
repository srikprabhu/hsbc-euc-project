from __future__ import annotations

import re
from typing import Any


_PROCEDURE_START = re.compile(
    r"^\s*(?P<kind>Public\s+|Private\s+|Friend\s+)?"
    r"(?P<type>Sub|Function|Property\s+(?:Get|Let|Set))\s+"
    r"(?P<name>[A-Za-z_]\w*)",
    re.IGNORECASE | re.MULTILINE,
)
_PROCEDURE_END = re.compile(r"^\s*End\s+(?:Sub|Function|Property)\b", re.IGNORECASE)


def split_procedures(source: str) -> list[dict[str, Any]]:
    matches = list(_PROCEDURE_START.finditer(source or ""))
    procedures: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end_match = _PROCEDURE_END.search(source, match.end())
        end = end_match.end() if end_match else (matches[index + 1].start() if index + 1 < len(matches) else len(source))
        code = source[match.start():end].strip()
        procedures.append({
            "procedure": match.group("name"),
            "procedure_name": match.group("name"),
            "kind": match.group("type"),
            "code": code,
            "source": code,
            "start_line": source.count("\n", 0, match.start()) + 1,
            "end_line": source.count("\n", 0, end) + 1,
        })
    return procedures
