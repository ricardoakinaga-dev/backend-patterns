#!/usr/bin/env python3
"""Validate the machine-readable ownership and handoff contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_CAPABILITIES = {
    "backend-engineering-vNext",
    "security-engineering-vNext",
    "verification-loop-vNext",
}


def validate() -> dict:
    path = ROOT / "composition-contract.json"
    errors: list[str] = []
    if not path.is_file():
        errors.append("composition-contract.json is missing")
        return {"scope": "COMPOSITION_CONTRACT", "errors": errors}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON: {exc}")
        return {"scope": "COMPOSITION_CONTRACT", "errors": errors}
    for field in ("schema_version", "package", "owner", "record_required_fields", "handoffs", "execution_claim"):
        if field not in data:
            errors.append(f"missing top-level field: {field}")
    if data.get("package") != "backend-patterns":
        errors.append("package must be backend-patterns")
    fields = data.get("record_required_fields", [])
    for field in ("problem", "forces", "invariants", "selected_patterns", "rejected_patterns", "verification_requirements"):
        if field not in fields:
            errors.append(f"record_required_fields missing {field}")
    handoffs = data.get("handoffs", [])
    seen = set()
    for index, handoff in enumerate(handoffs):
        if not isinstance(handoff, dict):
            errors.append(f"handoffs[{index}] must be an object")
            continue
        capability = handoff.get("capability")
        if capability in seen:
            errors.append(f"duplicate handoff: {capability}")
        seen.add(capability)
        for field in ("capability", "trigger", "input", "expected_output", "optional", "circular"):
            if field not in handoff:
                errors.append(f"handoffs[{index}] missing {field}")
        if handoff.get("circular") is not False:
            errors.append(f"handoffs[{index}] must declare circular=false")
    missing = sorted(REQUIRED_CAPABILITIES - seen)
    errors.extend(f"missing required capability handoff: {name}" for name in missing)
    return {"scope": "COMPOSITION_CONTRACT", "errors": errors, "capabilities": sorted(seen)}


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)

