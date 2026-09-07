#!/usr/bin/env python3
"""Validate the Phase 1.2 evidence package without fabricating runtime proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent.parent
QUALITY_BAR = ROOT / "docs" / "phase-1.2-quality-bar.json"
EXPECTED_PROMPT_SHA256 = "68faec7e4d2e17b82003fb872fe8bcb3a9f09a2ceed36e269f57c8665990f110"
REQUIRED_ARTIFACTS = (
    "docs/phase-1.2-baseline.md",
    "docs/routing-error-analysis.md",
    "docs/routing-results.json",
    "docs/behavioral-eval-report-v1.2.md",
    "docs/behavioral-eval-results-v1.2.json",
    "docs/generalization-report.md",
    "docs/generalization-results-v1.2.json",
    "docs/composition-evidence-v1.2.md",
    "docs/composition-results-v1.2.json",
    "docs/adversarial-findings-v1.2.md",
    "docs/triple-a-assurance-report-v1.2.md",
)
ALLOWED_STATUSES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "STALE", "NOT_APPLICABLE", "INVALID"}


def read_json(relative: str) -> dict:
    path = ROOT / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return value


def package_files() -> list[Path]:
    paths = [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "composition-contract.json"]
    for directory_name in ("references", "scripts", "tests"):
        directory = ROOT / directory_name
        if directory.is_dir():
            paths.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(
        path
        for path in set(paths)
        if ".pyc" not in path.name and "__pycache__" not in path.parts and ".gauntlet" not in path.parts
    )


def fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def current_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    for relative in REQUIRED_ARTIFACTS:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            errors.append(f"missing, symlinked or empty required artifact: {relative}")

    try:
        bar = read_json("docs/phase-1.2-quality-bar.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"scope": "PHASE_1_2_ASSURANCE", "status": "FAIL", "errors": [str(exc)], "warnings": []}
    if bar.get("prompt_sha256") != EXPECTED_PROMPT_SHA256:
        errors.append("quality bar prompt fingerprint does not match the Phase 1.2 prompt")
    criteria = bar.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 16:
        errors.append("quality bar must contain at least 16 Phase 1.2 criteria")
    else:
        ids = [item.get("id") for item in criteria if isinstance(item, dict)]
        expected_ids = [f"P12-{index:02d}" for index in range(1, 17)]
        if ids != expected_ids:
            errors.append("quality bar criteria IDs/order must be P12-01 through P12-16")
        for item in criteria:
            if not isinstance(item, dict) or not all(item.get(key) for key in ("id", "target", "evidence_method", "required", "priority")):
                errors.append("quality bar contains an incomplete criterion")

    routing: dict = {}
    try:
        routing = read_json("docs/routing-results.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"routing result cannot be read: {exc}")
    if routing:
        for key in ("reference_precision", "primary_recall", "primary_secondary_recall"):
            if not isinstance(routing.get(key), (int, float)):
                errors.append(f"routing result missing numeric {key}")
        if routing.get("reference_precision", 0) < 0.90:
            errors.append("routing precision is below 0.90")
        if routing.get("primary_recall", 0) < 0.85:
            errors.append("PRIMARY routing recall is below 0.85")
        if routing.get("primary_secondary_recall", 0) < 0.75:
            errors.append("PRIMARY+SECONDARY routing recall is below 0.75")
        if routing.get("context_growth_within_bound") is not True:
            errors.append("routing context growth is outside the frozen bound")
        for key in ("average_context_bytes", "p95_context_bytes", "max_average_context_bytes", "max_p95_context_bytes"):
            if not isinstance(routing.get(key), (int, float)):
                errors.append(f"routing result missing numeric {key}")
        if all(isinstance(routing.get(key), (int, float)) for key in ("average_context_bytes", "max_average_context_bytes")) and routing["average_context_bytes"] > routing["max_average_context_bytes"]:
            errors.append("routing average context exceeds its bound")
        if all(isinstance(routing.get(key), (int, float)) for key in ("p95_context_bytes", "max_p95_context_bytes")) and routing["p95_context_bytes"] > routing["max_p95_context_bytes"]:
            errors.append("routing P95 context exceeds its bound")
        if routing.get("gold_labels_independent") is not True:
            errors.append("routing result does not assert gold-label independence")

    result_files = (
        "docs/behavioral-eval-results-v1.2.json",
        "docs/generalization-results-v1.2.json",
        "docs/composition-results-v1.2.json",
    )
    result_statuses: dict[str, str] = {}
    for relative in result_files:
        try:
            result = read_json(relative)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{relative} cannot be read: {exc}")
            continue
        status = result.get("status")
        result_statuses[relative] = str(status)
        if status not in ALLOWED_STATUSES:
            errors.append(f"{relative} has unsupported status {status!r}")
        if status == "BLOCKED" and not result.get("reason"):
            errors.append(f"{relative} BLOCKED result lacks a reason")

    report_path = ROOT / "docs" / "triple-a-assurance-report-v1.2.md"
    if report_path.is_file():
        report = report_path.read_text(encoding="utf-8")
        for heading in (
            "# BACKEND-PATTERNS PHASE 1.2 — TRIPLE-A ASSURANCE REPORT",
            "## BASELINE",
            "## ROUTING",
            "## BEHAVIORAL",
            "## GENERALIZATION",
            "## COMPOSITION",
            "## RUNTIME",
            "## ASSURANCE",
        ):
            if heading not in report:
                errors.append(f"Phase 1.2 report missing section: {heading}")
        for marker in ("PACKAGE_SCORE:", "BEHAVIORAL_SCORE:", "ASSURANCE_SCORE:", "FINAL VERDICT:", "BLOCKED:"):
            if marker not in report:
                errors.append(f"Phase 1.2 report missing marker: {marker}")
        package_match = re.search(r"(?im)^PACKAGE FINGERPRINT:\s*([0-9a-f]{64})\s*$", report)
        expected_package = fingerprint(package_files())
        if not package_match:
            errors.append("Phase 1.2 report is missing PACKAGE FINGERPRINT")
        elif package_match.group(1) != expected_package:
            errors.append("Phase 1.2 report package fingerprint is stale")
        if any(status in {"BLOCKED", "NOT_RUN", "STALE", "INVALID"} for status in result_statuses.values()):
            if re.search(r"(?im)^FINAL VERDICT:\s*TRIPLE_A_PROVEN\s*$", report):
                errors.append("Phase 1.2 report cannot claim TRIPLE_A_PROVEN with unavailable/invalid execution")
    else:
        errors.append("missing Phase 1.2 assurance report")

    routing_audit = ROOT / "docs" / "routing-error-analysis.md"
    if routing_audit.is_file() and "omitted" not in routing_audit.read_text(encoding="utf-8").lower():
        warnings.append("routing audit does not use the word omitted; inspect manually")
    result = {
        "scope": "PHASE_1_2_ASSURANCE",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "prompt_fingerprint": EXPECTED_PROMPT_SHA256,
        "package_fingerprint": fingerprint(package_files()),
        "commit": current_commit(),
        "criteria_count": len(criteria) if isinstance(criteria, list) else 0,
        "routing_status": routing.get("status") if routing else None,
        "result_statuses": result_statuses,
    }
    return result


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
