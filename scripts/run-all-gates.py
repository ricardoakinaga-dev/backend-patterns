#!/usr/bin/env python3
"""Run the complete local backend-patterns validation surface.

The aggregator preserves every check's status. BLOCKED and NOT_RUN are never
silently treated as PASS; the process exits non-zero unless every required
check is PASS. Model and composition adapters can be supplied to the child
runners through their documented options/environment.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent

CHECKS = [
    ("static_skill", "python3 -B scripts/validate-skill.py"),
    ("links", "python3 -B scripts/validate-links.py"),
    ("pattern_index", "python3 -B scripts/validate-pattern-index.py"),
    ("composition_contract", "python3 -B scripts/validate-composition.py"),
    ("framework_independence", "python3 -B scripts/validate-framework-independence.py"),
    ("benchmark", "python3 -B scripts/validate-benchmark.py"),
    ("context_efficiency", "python3 -B scripts/run-context-efficiency.py"),
    ("legacy_fixture_eval", "python3 -B tests/run_evals.py"),
    ("legacy_known_bad", "python3 -B tests/run_known_bad.py"),
    ("response_mutations", "python3 -B scripts/run-response-mutations.py"),
    ("generalization", "python3 -B scripts/run-generalization-gates.py"),
    ("backend_runtime", "python3 -B scripts/run-runtime-gates.py"),
    ("unit_tests", "python3 -B -m unittest discover -s tests -p 'test_*.py'"),
    ("behavioral_model_eval", "python3 -B scripts/run-behavioral-eval.py"),
    ("real_composition", "python3 -B scripts/run-composition-eval.py"),
    ("assurance_report", "python3 -B scripts/validate-phase-assurance.py"),
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def summarize(name: str, command: str, completed: subprocess.CompletedProcess[str]) -> dict:
    raw = (completed.stdout or "") + (completed.stderr or "")
    parsed = None
    try:
        parsed = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        pass
    explicit = parsed.get("status") if isinstance(parsed, dict) else None
    if completed.returncode != 0:
        status = explicit if explicit in {"FAIL", "BLOCKED", "NOT_RUN", "STALE"} else "FAIL"
    elif explicit in {"BLOCKED", "NOT_RUN", "STALE", "FAIL", "PASS", "NOT_APPLICABLE"}:
        status = explicit
    else:
        status = "PASS"
    return {
        "name": name,
        "command": command,
        "status": status,
        "exit_status": completed.returncode,
        "raw_output_sha256": sha256_bytes(raw.encode("utf-8")),
        "summary": (raw.strip()[-800:] if raw.strip() else ""),
        "structured": parsed if isinstance(parsed, dict) and name not in {"context_efficiency"} else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="optional path for the complete JSON result")
    args = parser.parse_args()
    checks = []
    for name, command in CHECKS:
        completed = subprocess.run(shlex.split(command), cwd=ROOT, text=True, capture_output=True, check=False)
        checks.append(summarize(name, command, completed))
    statuses = [item["status"] for item in checks]
    if any(status == "FAIL" for status in statuses):
        overall = "FAIL"
    elif any(status in {"BLOCKED", "NOT_RUN", "STALE"} for status in statuses):
        overall = "BLOCKED"
    else:
        overall = "PASS"
    report = {
        "scope": "COMPLETE_LOCAL_VALIDATION",
        "status": overall,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "required_check_count": len(CHECKS),
        "status_counts": {status: statuses.count(status) for status in ("PASS", "FAIL", "NOT_RUN", "BLOCKED", "STALE", "NOT_APPLICABLE")},
        "checks": checks,
        "limitations": ["BLOCKED/NOT_RUN checks are not success; provide the required host adapters for full closure."],
    }
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    print(encoded)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
