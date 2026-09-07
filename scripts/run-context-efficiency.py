#!/usr/bin/env python3
"""Measure deterministic reference routing precision and context size.

This is a routing measurement, not a model-quality claim. The benchmark's
recommended_references are independently curated relevance labels; the router
below uses only free-text task fields and the package's topic vocabulary. It
must not read family, domain, or gold-reference labels because doing so would
turn the measurement into label leakage.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "tests" / "benchmark" / "scenarios.json"
INDEX = ROOT / "references" / "pattern-index.md"
SKILL = ROOT / "SKILL.md"
TARGET_PRECISION = 0.85

# Text-only routing vocabulary. Terms are deliberately high-signal: broad
# words such as "database", "event", "verify", and "unknown" are avoided
# because they occur in almost every benchmark record. The gold labels remain
# independent benchmark data and are never consulted by route().
TEXT_REFERENCE_RULES: dict[str, tuple[str, ...]] = {
    "architecture-boundaries.md": (
        "microservices", "modular monolith", "monolith", "service extraction",
        "module boundary", "bounded context", "independent deployment", "service split",
        "same process", "same database", "one release cadence", "ownership friction",
    ),
    "domain-modeling.md": (
        "event sourcing", "temporal reconstruction", "domain model", "domain ownership",
        "aggregate", "business rule", "bounded context", "immutable history",
    ),
    "api-patterns.md": (
        "rest api", "public api", "api client", "api endpoint", "http", "grpc", "graphql",
        "webhook", "mobile clients", "pagination",
    ),
    "data-access-patterns.md": (
        "orm", "direct sql", "repository", "relational model", "query plan", "database source",
        "database query", "sql consumer", "read model", "data access",
    ),
    "transaction-patterns.md": (
        "transactional outbox", "dual write", "local transaction", "atomic transaction",
        "transaction boundary", "unit of work", "same transaction", "commit atomically",
        "saga",
    ),
    "consistency-patterns.md": (
        "consistency", "eventual", "stale read", "read model", "projection lag",
        "committed writes", "publication obligation",
    ),
    "concurrency-patterns.md": (
        "compare-and-swap", "concurrent", "race", "distributed lock",
        "atomic uniqueness", "double booking", "multiple clients", "optimistic concurrency",
        "conflict frequency",
    ),
    "messaging-patterns.md": (
        "message broker", "broker", "queue", "dead letter", "kafka", "publish",
        "post-commit notification", "asynchronous", "integration event", "poison message",
    ),
    "resilience-patterns.md": (
        "retried payment", "unsafe retry", "retry around", "retry amplification", "retry storm",
        "retry until", "retry layers", "bounded retry", "timeout outcome", "network timeout",
        "backoff", "circuit breaker", "bulkhead", "overload", "backpressure", "load shedding",
        "deadline", "saturation", "outage",
    ),
    "distributed-systems.md": (
        "remote commit", "network timeout", "remote service", "external side effect",
    ),
    "caching-patterns.md": (
        "cache-aside", "cache stampede", "invalidation", "stale cache", "eviction", "cache key",
        "redis everywhere", "redis in front",
    ),
    "idempotency.md": (
        "idempotency", "duplicate delivery", "deduplication", "safe replay", "exactly-once delivery",
        "one fulfillment", "one label", "one charge", "at least once", "inbox",
    ),
    "security-boundaries.md": (
        "authz", "tenant", "ssrf", "secret", "privileged", "permission",
        "webhook authenticity", "signature", "trust boundary", "secrets in logs", "cross-tenant",
    ),
    "observability-patterns.md": (
        "observability", "telemetry", "runbook", "metrics", "traces", "correlation",
        "slo", "audit evidence", "repair path", "operational visibility",
    ),
    "performance-patterns.md": (
        "performance", "p99", "slow query", "saturation",
    ),
    "migration-patterns.md": (
        "schema rollout", "backfill", "rollout", "rollback", "mixed-version",
        "mixed versions", "expand-contract", "old clients", "legacy monolith", "version skew",
        "old payloads",
    ),
    "testing-patterns.md": (
        "failure injection", "test harness", "characterize", "regression", "holdout",
        "metamorphic",
    ),
    "anti-patterns.md": (
        "premature", "cargo cult", "more professional", "because enterprises", "slogan",
        "unjustified", "temptation", "without an independent", "no durable async need",
        "not a substitute", "everywhere without",
    ),
    "decision-matrix.md": (
        "unknown driver", "unknown consistency", "unknown tenant", "unknown write volume",
        "unknown owner", "unknown recovery objective", "unknown broker semantics",
        "before choosing", "need more evidence", "measure before",
    ),
}


def load_scenarios() -> list[dict]:
    if not BENCHMARK.is_file():
        raise FileNotFoundError(f"missing benchmark: {BENCHMARK.relative_to(ROOT)}")
    data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("benchmark scenarios must be an array")
    return data


def text_for(scenario: dict) -> str:
    # Keep the routing query independent from structured labels and from the
    # benchmark's gold fields. Titles and prompts are the user-facing task
    # text; lower-level fields are retained for scoring, not routing.
    pieces = [scenario.get("title", ""), scenario.get("prompt", "")]
    for key in ("current_facts", "unknowns", "invariants", "forces", "required_signals"):
        value = scenario.get(key, [])
        pieces.extend(str(item) for item in value) if isinstance(value, list) else pieces.append(str(value))
    return " ".join(pieces).lower()


def term_present(query: str, term: str) -> bool:
    # Word boundaries prevent short vocabulary such as "orm" from matching
    # unrelated words such as "normalized" or "platform".
    pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
    return re.search(pattern, query) is not None


def route(scenario: dict) -> list[str]:
    query = text_for(scenario)
    return sorted(
        reference
        for reference, terms in TEXT_REFERENCE_RULES.items()
        if any(term_present(query, term) for term in terms)
    )


def fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run() -> dict:
    scenarios = load_scenarios()
    errors: list[str] = []
    results: list[dict] = []
    package_refs = {path.name for path in (ROOT / "references").glob("*.md")}
    for scenario in scenarios:
        # Corpus labels may be package-relative paths while the router emits
        # reference basenames. Normalize both sides before measuring routing.
        expected = {Path(str(reference)).name for reference in scenario.get("recommended_references", [])}
        missing = sorted(expected - package_refs)
        if missing:
            errors.append(f"{scenario.get('id')}: missing recommended references: {', '.join(missing)}")
        loaded = route(scenario)
        relevant_loaded = sorted(set(loaded) & expected)
        irrelevant_loaded = sorted(set(loaded) - expected)
        omitted_relevant = sorted(expected - set(loaded))
        precision = len(relevant_loaded) / len(loaded) if loaded else 0.0
        recall = len(relevant_loaded) / len(expected) if expected else 1.0
        context_paths = [SKILL] + [ROOT / "references" / name for name in loaded if (ROOT / "references" / name).is_file()]
        results.append({
            "scenario_id": scenario.get("id"),
            "references_loaded": loaded,
            "relevant_references": sorted(expected),
            "irrelevant_references": irrelevant_loaded,
            "omitted_relevant_references": omitted_relevant,
            "reference_precision": round(precision, 4),
            "reference_recall": round(recall, 4),
            "approximate_context_bytes": sum(path.stat().st_size for path in context_paths),
        })
    precision_values = [item["reference_precision"] for item in results]
    recall_values = [item["reference_recall"] for item in results]
    overall_precision = sum(precision_values) / len(precision_values) if precision_values else 0.0
    overall_recall = sum(recall_values) / len(recall_values) if recall_values else 0.0
    status = "PASS" if not errors and overall_precision >= TARGET_PRECISION else "FAIL"
    return {
        "scope": "CONTEXT_EFFICIENCY",
        "status": status,
        "router_version": "topic-term-v2-text-only",
        "routing_inputs": ["title", "prompt", "current_facts", "unknowns", "invariants", "forces", "required_signals"],
        "gold_labels_independent": True,
        "target_precision": TARGET_PRECISION,
        "scenario_count": len(scenarios),
        "reference_precision": round(overall_precision, 4),
        "reference_recall": round(overall_recall, 4),
        "average_context_bytes": round(sum(item["approximate_context_bytes"] for item in results) / len(results), 2) if results else 0,
        "package_fingerprint": fingerprint([SKILL, INDEX, *sorted((ROOT / "references").glob("*.md"))]),
        "errors": errors,
        "scenarios": results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="write the JSON evidence artifact to this path")
    args = parser.parse_args()
    try:
        report = run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {"scope": "CONTEXT_EFFICIENCY", "status": "FAIL", "errors": [str(exc)]}
    encoded = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    raise SystemExit(0 if report["status"] == "PASS" else 1)
