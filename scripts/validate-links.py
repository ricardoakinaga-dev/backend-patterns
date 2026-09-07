#!/usr/bin/env python3
"""Validate local Markdown navigation without requiring third-party packages."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", ".gauntlet", "__pycache__", "docs"}


def markdown_files() -> list[Path]:
    result = []
    for path in [ROOT / "SKILL.md", ROOT / "README.md", *(ROOT / "references").glob("*.md")]:
        if path.is_file():
            result.append(path)
    for path in (ROOT / "tests").rglob("*.md") if (ROOT / "tests").exists() else []:
        if not any(part in SKIP for part in path.parts):
            result.append(path)
    return sorted(set(result))


def check(path: Path) -> list[str]:
    errors = []
    content = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\]\(([^)\n]+)\)", content):
        raw = match.group(1).strip().strip("<>")
        parsed = urlsplit(raw)
        if parsed.scheme == "file":
            errors.append(f"{path.relative_to(ROOT)}: file URL: {raw}")
            continue
        if parsed.scheme or parsed.netloc or raw.startswith("#"):
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{path.relative_to(ROOT)}: link escapes package: {raw}")
            continue
        if not target.exists():
            errors.append(f"{path.relative_to(ROOT)}: missing link: {raw}")
    return errors


def validate() -> dict:
    files = markdown_files()
    errors = [error for path in files for error in check(path)]
    return {"scope": "MARKDOWN_LOCAL_LINKS", "files_checked": len(files), "errors": errors}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)

