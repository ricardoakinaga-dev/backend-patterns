#!/usr/bin/env python3
"""Validate the evidence report without pretending it proves runtime behavior."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "assurance-report.md"
EXECPLAN = ROOT / "docs" / "execplan.md"
PACKAGE_TOP_LEVEL = (ROOT / "SKILL.md", ROOT / "README.md", ROOT / "composition-contract.json")
PACKAGE_DIRS = (ROOT / "references", ROOT / "scripts", ROOT / "tests")
SKIP_PARTS = {"__pycache__", ".git", ".gauntlet"}
REQUIRED_HEADINGS = (
    "## Baseline",
    "## Final score",
    "## Delivered artifacts",
    "## Architecture and coverage",
    "## Verification evidence",
    "## Composition",
    "## Review history",
    "## Limitations and residual risks",
    "## Verdict",
)
CRITERIA = tuple(f"BP-{index:02d}" for index in range(1, 15))


def package_files() -> list[Path]:
    files = [path for path in PACKAGE_TOP_LEVEL if path.is_file()]
    for directory in PACKAGE_DIRS:
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and not any(part in SKIP_PARTS for part in path.parts):
                files.append(path)
    return sorted(set(files))


def package_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in package_files():
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def validate() -> dict:
    errors: list[str] = []
    if not REPORT.is_file() or REPORT.is_symlink():
        return {"scope": "ASSURANCE_REPORT", "errors": ["docs/assurance-report.md must be a regular file"]}
    text = REPORT.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing report section: {heading}")
    if not re.search(r"(?im)^Baseline score:\s*0/100\s*$", text):
        errors.append("report must record Baseline score: 0/100")
    if not re.search(r"(?im)^Final score:\s*(?:[1-9][0-9]?|100)/100\b", text):
        errors.append("report must record a numeric Final score out of 100")
    if not re.search(r"(?im)^Package fingerprint:\s*[0-9a-f]{64}\s*$", text):
        errors.append("report must record the package fingerprint for the non-docs consumer scope")
    expected_fingerprint = package_fingerprint()
    match = re.search(r"(?im)^Package fingerprint:\s*([0-9a-f]{64})\s*$", text)
    if match and match.group(1) != expected_fingerprint:
        errors.append("report package fingerprint is stale")
    for criterion in CRITERIA:
        if not re.search(rf"(?m)^\|\s*{re.escape(criterion)}\s*\|", text):
            errors.append(f"report is missing criterion row: {criterion}")
    for phrase in (
        "model_execution: NOT_RUN",
        "runtime validation: NOT_RUN",
        "limitations",
        "residual risks",
        "evidence",
        "Final verdict:",
        "Final gate decision: RECORDED_BY_GAUNTLET",
    ):
        if phrase.lower() not in text.lower():
            errors.append(f"report must state: {phrase}")
    if re.search(r"(?im)^Final verdict:\s*TRIPLE-A\s*$", text):
        errors.append("report may not claim TRIPLE-A without model and runtime evidence")
    if re.search(r"(?i)final(?: fresh)? critic[^\n]*(?:NOT_RUN|pending|still required)", text):
        errors.append("report must not leave final Critic status stale or pending")
    if not EXECPLAN.is_file():
        errors.append("docs/execplan.md must exist for assurance traceability")
    else:
        plan = EXECPLAN.read_text(encoding="utf-8")
        for stale in (
            "Current next action: run the final",
            "Current next action: close the Gauntlet",
            "last confirmed evidence is round 2",
        ):
            if stale.lower() in plan.lower():
                errors.append(f"ExecPlan contains stale live-state wording: {stale}")
        if "FINAL_GAUNTLET" not in plan and "final gate" not in plan.lower():
            errors.append("ExecPlan must identify the final Gauntlet state/checkpoint")
    return {
        "scope": "ASSURANCE_REPORT",
        "errors": errors,
        "report": str(REPORT.relative_to(ROOT)),
        "package_fingerprint": expected_fingerprint,
        "model_execution": "NOT_RUN" if "model_execution: NOT_RUN" in text else "UNDECLARED",
        "runtime_validation": "NOT_RUN" if "runtime validation: NOT_RUN" in text else "UNDECLARED",
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)
