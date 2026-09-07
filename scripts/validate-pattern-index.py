#!/usr/bin/env python3
"""Validate the routing index and minimum coverage of each reference."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "references" / "pattern-index.md"
EXPECTED = {
    "architecture-boundaries.md": ("problem", "forces", "when not", "dependency"),
    "domain-modeling.md": ("invariant", "aggregate", "when not", "verification"),
    "api-patterns.md": ("contract", "compatibility", "error", "pagination"),
    "data-access-patterns.md": ("query", "transaction", "orm", "when not"),
    "transaction-patterns.md": ("atomic", "outbox", "saga", "failure"),
    "consistency-patterns.md": ("strong", "eventual", "conflict", "stale"),
    "concurrency-patterns.md": ("race", "lock", "compare-and-swap", "verification"),
    "messaging-patterns.md": ("duplicate", "dead-letter", "ordering", "exactly-once"),
    "resilience-patterns.md": ("timeout", "retry", "backpressure", "circuit"),
    "distributed-systems.md": ("partial failure", "reorder", "clock", "partition"),
    "caching-patterns.md": ("source of truth", "invalidation", "stale", "stampede"),
    "idempotency.md": ("canonical", "digest", "duplicate", "concurrent"),
    "security-boundaries.md": ("trust", "authorization", "tenant", "ssrf"),
    "observability-patterns.md": ("structured", "metric", "trace", "recovery"),
    "performance-patterns.md": ("measure", "query plan", "tail", "load"),
    "migration-patterns.md": ("expand", "contract", "mixed", "backfill"),
    "testing-patterns.md": ("known-bad", "invariant", "failure injection", "evidence"),
    "anti-patterns.md": ("symptom", "danger", "detection", "migration"),
    "decision-matrix.md": ("problem solved", "when not", "cost", "evidence"),
    "composition-contracts.md": ("backend-engineering-vnext", "security-engineering-vnext", "verification-loop-vnext", "handoff"),
}


def validate() -> dict:
    errors: list[str] = []
    if not INDEX.is_file():
        return {"scope": "PATTERN_INDEX", "errors": ["references/pattern-index.md is missing"]}
    index = INDEX.read_text(encoding="utf-8").lower()
    for filename, terms in EXPECTED.items():
        if filename.lower() not in index:
            errors.append(f"index does not route to {filename}")
        path = ROOT / "references" / filename
        if not path.is_file():
            errors.append(f"reference is missing: references/{filename}")
            continue
        content = path.read_text(encoding="utf-8").lower()
        for term in terms:
            if term.lower() not in content:
                errors.append(f"references/{filename}: required coverage term missing: {term}")
    links = re.findall(r"\]\(([^)\n]+\.md(?:#[^)]*)?)\)", index)
    if len(set(link.split("#", 1)[0] for link in links)) < len(EXPECTED):
        errors.append("index has fewer unique Markdown routes than the required reference set")
    return {
        "scope": "PATTERN_INDEX",
        "expected_reference_count": len(EXPECTED),
        "errors": errors,
        "references": sorted(EXPECTED),
    }


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(1 if result["errors"] else 0)

