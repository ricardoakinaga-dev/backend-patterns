#!/usr/bin/env python3
"""State backend-runtime execution separately from static and model evidence.

The package is a reasoning skill, not a running backend service.  This runner
therefore emits an explicit BLOCKED result until a host supplies a service,
database/broker, and workload/repair harness.  It never turns the absence of
those systems into a synthetic PASS.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def run(args: argparse.Namespace) -> dict:
    if args.evidence_file:
        path = Path(args.evidence_file).resolve()
        try:
            evidence = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "scope": "BACKEND_RUNTIME",
                "status": "FAIL",
                "runtime_status": "FAIL",
                "reason": f"runtime evidence could not be read: {exc}",
                "errors": [str(exc)],
            }
        if not isinstance(evidence, dict) or evidence.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
            return {
                "scope": "BACKEND_RUNTIME",
                "status": "FAIL",
                "runtime_status": "FAIL",
                "reason": "runtime evidence must be an object with status PASS, FAIL, or BLOCKED",
                "errors": ["invalid runtime evidence schema"],
            }
        evidence.setdefault("scope", "BACKEND_RUNTIME")
        evidence.setdefault("runtime_status", evidence["status"])
        evidence.setdefault("captured_at", datetime.now(timezone.utc).isoformat())
        return evidence

    return {
        "scope": "BACKEND_RUNTIME",
        "status": "BLOCKED",
        "runtime_status": "BLOCKED",
        "execution_status": "BLOCKED",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "reason": "No executable backend service or runtime harness was supplied.",
        "required_host_capability": [
            "backend service with representative routes and persistence",
            "database and broker or equivalent external dependencies",
            "load/concurrency, migration, security, failure-injection, and operator-repair harnesses",
        ],
        "evidence_unavailable": [
            "latency, throughput, and saturation behavior",
            "transaction, duplicate, timeout, and recovery behavior under runtime failure",
            "migration interruption, authorization isolation, and repair-loop observations",
        ],
        "impact_on_verdict": "Runtime proof is unavailable; it cannot be counted as PASS and Triple-A proven remains ineligible.",
        "errors": [],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-file", help="consume a host-produced runtime evidence JSON object")
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    result = run(args)
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if result.get("status") in {"PASS", "BLOCKED"} else 1)
