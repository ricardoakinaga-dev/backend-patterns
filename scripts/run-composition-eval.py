#!/usr/bin/env python3
"""Evaluate observed cross-skill composition traces without conflating schemas with execution."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "composition-contract.json"
REQUIRED_STAGES = (
    "backend-engineering-vNext",
    "backend-patterns",
    "security-engineering-vNext",
    "verification-loop-vNext",
)


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocked(reason: str, scenario_count: int = 0) -> dict:
    return {
        "scope": "REAL_COMPOSITION",
        "status": "BLOCKED",
        "composition": "BLOCKED",
        "reason": reason,
        "required_host_capability": "An executable composition adapter or observed trace from the neighboring skills.",
        "evidence_unavailable": "actual backend → patterns → security → verification handoffs and repair-loop observations",
        "impact_on_verdict": "Composition proof is unavailable; Triple-A proven is ineligible.",
        "scenario_count": scenario_count,
        "contract_fingerprint": fingerprint(CONTRACT) if CONTRACT.is_file() else None,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "errors": [],
    }


def validate_trace(trace: object) -> dict:
    if not isinstance(trace, dict):
        return {"status": "FAIL", "errors": ["trace must be an object"]}
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        return {"status": "FAIL", "errors": ["trace.events must be a non-empty array"]}
    names = [event.get("stage") for event in events if isinstance(event, dict)]
    missing = [stage for stage in REQUIRED_STAGES if stage not in names]
    repair = any(event.get("stage") == "repair" for event in events if isinstance(event, dict))
    reverification = any(event.get("stage") in {"re-verification", "verification-rerun"} for event in events if isinstance(event, dict))
    errors = []
    if missing:
        errors.append("missing observed stages: " + ", ".join(missing))
    if not repair:
        errors.append("missing observed repair stage")
    if not reverification:
        errors.append("missing observed re-verification stage")
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not event.get("observed"):
            errors.append(f"event {index} is not marked observed")
        if isinstance(event, dict) and not event.get("output"):
            errors.append(f"event {index} has no output/evidence payload")
    return {
        "status": "PASS" if not errors else "FAIL",
        "events": len(events),
        "stages": names,
        "repair_loop_observed": repair and reverification,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-file")
    parser.add_argument("--adapter-command")
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    trace_path = Path(args.trace_file).resolve() if args.trace_file else None
    if trace_path is None and args.adapter_command:
        try:
            result = subprocess.run(shlex.split(args.adapter_command), cwd=ROOT, text=True, capture_output=True, check=False)
        except OSError as exc:
            report = blocked(f"composition adapter could not start: {exc}")
        else:
            if result.returncode != 0:
                report = {"scope": "REAL_COMPOSITION", "status": "FAIL", "composition": "FAIL", "errors": [result.stderr[-1000:] or result.stdout[-1000:]]}
            else:
                try:
                    report = validate_trace(json.loads(result.stdout))
                except json.JSONDecodeError as exc:
                    report = {"scope": "REAL_COMPOSITION", "status": "FAIL", "composition": "FAIL", "errors": [f"adapter returned invalid JSON: {exc}"]}
    elif trace_path is not None:
        try:
            report = validate_trace(json.loads(trace_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            report = {"scope": "REAL_COMPOSITION", "status": "FAIL", "composition": "FAIL", "errors": [str(exc)]}
    else:
        report = blocked("No composition adapter or observed trace was supplied.")
    report.setdefault("scope", "REAL_COMPOSITION")
    report.setdefault("captured_at", datetime.now(timezone.utc).isoformat())
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report.get("status") in {"PASS", "BLOCKED", "NOT_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
