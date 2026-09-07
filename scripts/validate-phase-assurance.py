#!/usr/bin/env python3
"""Validate the phase-1.1 assurance report and its evidence identity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "triple-a-assurance-report.md"
PROMPT = ROOT / "docs" / "master-prompt-v1.1.md"
BAR = ROOT / "docs" / "phase-1.1-quality-bar.json"
PACKAGE_TOP_LEVEL = (ROOT / "SKILL.md", ROOT / "README.md", ROOT / "composition-contract.json")
PACKAGE_DIRS = (ROOT / "references", ROOT / "scripts", ROOT / "tests")
SKIP_PARTS = {".git", ".gauntlet", "__pycache__"}

REQUIRED_REPORTS = (
    "docs/phase-1.1-baseline.md",
    "docs/behavioral-eval-report.md",
    "docs/composition-evidence.md",
    "docs/context-efficiency-report.md",
    "docs/adversarial-findings.md",
    "docs/runtime-results.json",
    "docs/triple-a-assurance-report.md",
)
DIMENSIONS = (
    "Activation precision",
    "Activation recall",
    "Scope discipline",
    "Progressive disclosure",
    "Context efficiency",
    "Architecture judgment",
    "Pattern selection",
    "Pattern rejection",
    "Invariant reasoning",
    "Distributed-systems reasoning",
    "Transaction reasoning",
    "Concurrency reasoning",
    "Consistency reasoning",
    "API reasoning",
    "Messaging reasoning",
    "Resilience reasoning",
    "Security awareness",
    "Observability",
    "Operability",
    "Migration safety",
    "Anti-pattern resistance",
    "Cargo-cult resistance",
    "User-pressure resistance",
    "Ambiguity handling",
    "Verification quality",
    "Behavioral evidence",
    "Composition quality",
    "Framework independence",
    "Regression robustness",
    "Evidence honesty",
)


def package_files() -> list[Path]:
    files = [path for path in PACKAGE_TOP_LEVEL if path.is_file()]
    for directory in PACKAGE_DIRS:
        if directory.is_dir():
            files.extend(
                path for path in directory.rglob("*")
                if path.is_file() and not any(part in SKIP_PARTS for part in path.parts)
            )
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fresh_json(command: list[str]) -> tuple[dict | None, str | None]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return None, f"command returned non-JSON: {exc}"
    if not isinstance(parsed, dict):
        return None, "command JSON root is not an object"
    if completed.returncode != 0:
        return parsed, f"command exited {completed.returncode}"
    return parsed, None


def validate() -> dict:
    errors: list[str] = []
    if not REPORT.is_file() or REPORT.is_symlink():
        errors.append("docs/triple-a-assurance-report.md must be a regular file")
        return {"scope": "PHASE_1_1_ASSURANCE", "status": "FAIL", "errors": errors}
    text = REPORT.read_text(encoding="utf-8")
    for heading in (
        "# Triple-A Assurance Report",
        "## 1. Baseline",
        "## 2. Benchmark corpus",
        "## 3. Deterministic evidence",
        "## 4. Model execution",
        "## 5. Composition",
        "## 6. Runtime execution",
        "## 7. Context efficiency",
        "## 8. Adversarial findings",
        "## 9. Final gauntlet",
        "## 10. Required score dimensions",
        "## 11. Verdict",
    ):
        if heading not in text:
            errors.append(f"missing report section: {heading}")
    for relative in REQUIRED_REPORTS:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required report artifact: {relative}")
    if not PROMPT.is_file() or sha256(PROMPT) not in text:
        errors.append("report does not bind the revised prompt SHA-256")
    if not BAR.is_file() or sha256(BAR) not in text:
        errors.append("report does not bind the quality-bar SHA-256")
    current_package = package_fingerprint()
    match = re.search(r"(?im)^PACKAGE_FINGERPRINT:\s*([0-9a-f]{64})\s*$", text)
    if not match:
        errors.append("report must contain PACKAGE_FINGERPRINT")
    elif match.group(1) != current_package:
        errors.append("report package fingerprint is stale")
    deterministic_artifacts = (
        ("docs/benchmark-validation.json", [sys.executable, "-B", "scripts/validate-benchmark.py"]),
        ("docs/context-efficiency-results.json", [sys.executable, "-B", "scripts/run-context-efficiency.py"]),
        ("docs/response-mutation-results.json", [sys.executable, "-B", "scripts/run-response-mutations.py"]),
    )
    for relative, command in deterministic_artifacts:
        artifact_path = ROOT / relative
        if not artifact_path.is_file():
            errors.append(f"missing deterministic evidence artifact: {relative}")
            continue
        try:
            stored = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid deterministic evidence artifact {relative}: {exc}")
            continue
        fresh, command_error = fresh_json(command)
        if command_error:
            errors.append(f"freshness command failed for {relative}: {command_error}")
        elif stored != fresh:
            errors.append(f"deterministic evidence artifact is stale: {relative}")
    behavioral_path = ROOT / "docs" / "behavioral-eval-results.json"
    if behavioral_path.is_file():
        try:
            behavioral = json.loads(behavioral_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid behavioral evidence artifact: {exc}")
        else:
            if behavioral.get("package_fingerprint") != current_package:
                errors.append("behavioral evidence package fingerprint is stale")
            if behavioral.get("benchmark_fingerprint") != sha256(ROOT / "tests" / "benchmark" / "scenarios.json"):
                errors.append("behavioral evidence benchmark fingerprint is stale")
            if behavioral.get("rubric_fingerprint") not in {None, sha256(ROOT / "tests" / "benchmark" / "rubric.json")}:
                errors.append("behavioral evidence rubric fingerprint is stale")
    context_path = ROOT / "docs" / "context-efficiency-results.json"
    context_report_path = ROOT / "docs" / "context-efficiency-report.md"
    if context_path.is_file() and context_report_path.is_file():
        try:
            context = json.loads(context_path.read_text(encoding="utf-8"))
            context_report = context_report_path.read_text(encoding="utf-8")
            irrelevant = sum(len(item.get("irrelevant_references", [])) for item in context.get("scenarios", []))
            omitted = sum(len(item.get("omitted_relevant_references", [])) for item in context.get("scenarios", []))
            expected_lines = (
                f"| Reference precision | {context.get('reference_precision')} |",
                f"| Reference recall | {context.get('reference_recall')} |",
                f"| Average selected context | {context.get('average_context_bytes'):,.0f} bytes |",
                f"| Irrelevant references | {irrelevant} |",
                f"| Omitted relevant references | {omitted} |",
            )
            for line in expected_lines:
                if line not in context_report:
                    errors.append(f"context-efficiency Markdown is stale: missing '{line}'")
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"could not validate context-efficiency freshness: {exc}")
    if "model_execution: BLOCKED" not in text:
        errors.append("model execution must be explicitly BLOCKED or executed")
    if "composition: BLOCKED" not in text:
        errors.append("composition must be explicitly BLOCKED or observed")
    if "Final verdict: TRIPLE_A_CONDITIONAL" not in text:
        errors.append("unavailable model/composition evidence requires TRIPLE_A_CONDITIONAL")
    if "TRIPLE_A_PROVEN" in text and "Final verdict: TRIPLE_A_PROVEN" in text:
        errors.append("TRIPLE_A_PROVEN is not allowed while model/composition is blocked")
    for dimension in DIMENSIONS:
        if not re.search(rf"(?m)^\|\s*{re.escape(dimension)}\s*\|", text):
            errors.append(f"missing score dimension: {dimension}")
    if not re.search(r"(?im)^\|\s*Overall score\s*\|", text):
        errors.append("missing overall score row")
    if not re.search(r"(?im)^Status taxonomy:\s*PASS/FAIL/NOT_RUN/BLOCKED/STALE/NOT_APPLICABLE\s*$", text):
        errors.append("status taxonomy is not explicit")
    if "model_execution: NOT_RUN" not in text and "model_execution: BLOCKED" not in text:
        errors.append("model execution status is missing")
    return {
        "scope": "PHASE_1_1_ASSURANCE",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "package_fingerprint": current_package,
        "prompt_fingerprint": sha256(PROMPT) if PROMPT.is_file() else None,
        "quality_bar_fingerprint": sha256(BAR) if BAR.is_file() else None,
        "dimension_count": len(DIMENSIONS),
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
