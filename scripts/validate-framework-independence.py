#!/usr/bin/env python3
"""Reject accidental framework dominance in the skill's decision core."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
CORE_FILES = (
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "references" / "pattern-index.md",
    ROOT / "references" / "decision-matrix.md",
)
REQUIRED_TERMS = ("framework-independent", "language", "constraints")
FRAMEWORK_NAMES = re.compile(
    r"(?i)(?<![\w])(?:node(?:\.js)?|express(?:\.js)?|django|rails|spring\s+boot|laravel|nestjs|fastapi|asp\.net|dotnet)(?![\w])"
)


def validate() -> dict:
    errors: list[str] = []
    corpus: list[str] = []
    for path in CORE_FILES:
        if not path.is_file():
            errors.append(f"missing core file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        corpus.append(text.lower())
        for match in FRAMEWORK_NAMES.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(
                f"{path.relative_to(ROOT)}:{line}: framework-specific name in decision core: {match.group(0)}"
            )
    joined = "\n".join(corpus)
    for term in REQUIRED_TERMS:
        if term.lower() not in joined:
            errors.append(f"decision core is missing framework-independence term: {term}")
    return {
        "scope": "FRAMEWORK_INDEPENDENCE",
        "files_checked": [str(path.relative_to(ROOT)) for path in CORE_FILES if path.is_file()],
        "errors": errors,
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)
