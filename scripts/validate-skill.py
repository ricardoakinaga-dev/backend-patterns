#!/usr/bin/env python3
"""Validate the self-contained backend-patterns package structure."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DIRS = (ROOT / "references", ROOT / "scripts", ROOT / "tests")
SKIP_DIRS = {".git", ".gauntlet", "__pycache__", "docs"}
REQUIRED_HEADINGS = (
    "Activate and decline",
    "Non-negotiable reasoning rules",
    "Required execution loop",
    "Discover the actual system",
    "Classify and load selectively",
    "Model constraints, forces and invariants",
    "Generate and eliminate candidates",
    "Select and define the boundary contract",
    "High-risk decision gates",
    "Decision record",
    "Negative guidance and anti-rationalization",
    "Verification contract",
    "Composition and exit",
)


def markdown_targets(path: Path):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\]\(([^)\n]+)\)", text):
        yield match.group(1).strip().strip("<>")


def local_link_errors(path: Path) -> list[str]:
    errors: list[str] = []
    for target in markdown_targets(path):
        parsed = urlsplit(target)
        if parsed.scheme == "file":
            errors.append(f"{path.relative_to(ROOT)}: file URL is not portable: {target}")
            continue
        if parsed.scheme or parsed.netloc or target.startswith("#"):
            continue
        candidate = (path.parent / unquote(parsed.path)).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{path.relative_to(ROOT)}: local link escapes package: {target}")
            continue
        if not candidate.exists():
            errors.append(f"{path.relative_to(ROOT)}: missing local link: {target}")
    return errors


def package_files() -> list[Path]:
    files = [ROOT / "SKILL.md", ROOT / "README.md"]
    for directory in PRODUCT_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                files.append(path)
    return sorted(set(files))


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    skill = ROOT / "SKILL.md"
    if not skill.is_file() or skill.is_symlink():
        errors.append("SKILL.md must be a regular file")
        return {"scope": "STATIC_SKILL_STRUCTURE", "errors": errors, "warnings": warnings}

    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append("SKILL.md: frontmatter boundaries are missing")
    else:
        front = text.split("---", 2)[1]
        if not re.search(r"^name:\s*backend-patterns\s*$", front, re.M):
            errors.append("SKILL.md: metadata name must be backend-patterns")
        description = re.search(r"^description:\s*(.+)$", front, re.M)
        if not description:
            errors.append("SKILL.md: metadata description is missing")
        else:
            value = description.group(1).lower()
            if len(value) < 80:
                errors.append("SKILL.md: activation description is too short")
            for phrase in ("use when", "do not use"):
                if phrase not in value:
                    warnings.append(f"SKILL.md: metadata description does not contain '{phrase}'")
    if len(text.splitlines()) >= 500:
        errors.append(f"SKILL.md: orchestration layer has {len(text.splitlines())} lines; keep it below 500")
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"SKILL.md: required section missing: {heading}")
    if "CURRENT" not in text or "PROPOSED" not in text or "UNKNOWN" not in text:
        errors.append("SKILL.md: must distinguish CURRENT, PROPOSED, and UNKNOWN")
    if "minimum sufficient" not in text.lower():
        errors.append("SKILL.md: minimum-sufficient architecture principle missing")
    if "exactly-once" not in text.lower() or "duplicate" not in text.lower():
        errors.append("SKILL.md: duplicate/exactly-once guidance missing")

    for path in package_files():
        if path.is_symlink():
            errors.append(f"{path.relative_to(ROOT)}: symlinks are not self-contained package resources")
            continue
        if path.suffix.lower() in {".md", ".json", ".py"}:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"{path.relative_to(ROOT)}: expected UTF-8 text")
                continue
            template_open = "{" * 2
            template_close = "}" * 2
            if path.suffix.lower() in {".md", ".json"} and (template_open in content or template_close in content):
                errors.append(f"{path.relative_to(ROOT)}: unresolved template marker")
            if path.suffix.lower() == ".md":
                errors.extend(local_link_errors(path))

    required = {
        "references/pattern-index.md",
        "references/composition-contracts.md",
        "scripts/validate-links.py",
        "scripts/validate-pattern-index.py",
        "scripts/validate-composition.py",
        "scripts/validate-framework-independence.py",
        "scripts/validate-assurance-report.py",
        "composition-contract.json",
        "tests/run_evals.py",
        "tests/run_known_bad.py",
    }
    for relative in sorted(required):
        if not (ROOT / relative).is_file():
            errors.append(f"required package artifact missing: {relative}")
    return {"scope": "STATIC_SKILL_STRUCTURE", "errors": errors, "warnings": warnings}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)
