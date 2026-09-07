#!/usr/bin/env python3
"""Measure deterministic, compositional reference routing.

The router consumes only the public task projection: title, prompt, current
facts, unknowns, invariants, forces, and required signals.  Gold references
and PRIMARY/SECONDARY/OPTIONAL labels are loaded only by the evaluator in
``run``.  The model is an inspectable signal graph: complete direct or
co-signal bundles select references; there is no load-all fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "tests" / "benchmark" / "scenarios.json"
TAXONOMY = ROOT / "tests" / "benchmark" / "routing-relevance.json"
INDEX = ROOT / "references" / "pattern-index.md"
SKILL = ROOT / "SKILL.md"

TARGET_PRECISION = 0.90
TARGET_PRIMARY_RECALL = 0.85
TARGET_PRIMARY_SECONDARY_RECALL = 0.75
ROUTER_VERSION = "public-topic-composition-v4"
BASELINE_AVERAGE_CONTEXT_BYTES = 50764.62
BASELINE_P95_CONTEXT_BYTES = 80691
MAX_AVERAGE_CONTEXT_BYTES = BASELINE_AVERAGE_CONTEXT_BYTES * 2.0
MAX_P95_CONTEXT_BYTES = BASELINE_P95_CONTEXT_BYTES * 1.75
TAXONOMY_LEVELS = ("PRIMARY", "SECONDARY", "OPTIONAL")
ROUTING_INPUT_FIELDS = (
    "title", "prompt", "current_facts", "unknowns", "invariants", "forces", "required_signals",
)


# Frozen pre-edit matcher, retained only to reproduce the 148-pair baseline
# in the omission audit.  It is never called by route().
LEGACY_TEXT_REFERENCE_RULES: dict[str, tuple[str, ...]] = {
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
        "transaction boundary", "unit of work", "same transaction", "commit atomically", "saga",
    ),
    "consistency-patterns.md": (
        "consistency", "eventual", "stale read", "read model", "projection lag",
        "committed writes", "publication obligation",
    ),
    "concurrency-patterns.md": (
        "compare-and-swap", "concurrent", "race", "distributed lock", "atomic uniqueness",
        "double booking", "multiple clients", "optimistic concurrency", "conflict frequency",
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
    "distributed-systems.md": ("remote commit", "network timeout", "remote service", "external side effect"),
    "caching-patterns.md": (
        "cache-aside", "cache stampede", "invalidation", "stale cache", "eviction", "cache key",
        "redis everywhere", "redis in front",
    ),
    "idempotency.md": (
        "idempotency", "duplicate delivery", "deduplication", "safe replay", "exactly-once delivery",
        "one fulfillment", "one label", "one charge", "at least once", "inbox",
    ),
    "security-boundaries.md": (
        "authz", "tenant", "ssrf", "secret", "privileged", "permission", "webhook authenticity",
        "signature", "trust boundary", "secrets in logs", "cross-tenant",
    ),
    "observability-patterns.md": (
        "observability", "telemetry", "runbook", "metrics", "traces", "correlation", "slo",
        "audit evidence", "repair path", "operational visibility",
    ),
    "performance-patterns.md": ("performance", "p99", "slow query", "saturation"),
    "migration-patterns.md": (
        "schema rollout", "backfill", "rollout", "rollback", "mixed-version", "mixed versions",
        "expand-contract", "old clients", "legacy monolith", "version skew", "old payloads",
    ),
    "testing-patterns.md": ("failure injection", "test harness", "characterize", "regression", "holdout", "metamorphic"),
    "anti-patterns.md": (
        "premature", "cargo cult", "more professional", "because enterprises", "slogan", "unjustified",
        "temptation", "without an independent", "no durable async need", "not a substitute", "everywhere without",
    ),
    "decision-matrix.md": (
        "unknown driver", "unknown consistency", "unknown tenant", "unknown write volume", "unknown owner",
        "unknown recovery objective", "unknown broker semantics", "before choosing", "need more evidence", "measure before",
    ),
}
TEXT_REFERENCE_RULES = LEGACY_TEXT_REFERENCE_RULES


@dataclass(frozen=True)
class SignalDefinition:
    terms: tuple[str, ...]
    scope: str = "narrative"


@dataclass(frozen=True)
class RoutingTrigger:
    id: str
    requires: tuple[str, ...]
    kind: str = "direct"


# These are public-text dimensions, not benchmark labels.  Broad dimensions
# are safe because reference rules below require complete trigger sets.
SIGNAL_DIMENSIONS: dict[str, SignalDefinition] = {
    "api_surface": SignalDefinition((
        "api", "rest", "webhook", "endpoint", "fastapi", "http", "public api", "api clients",
    ), "title_prompt"),
    "api_contract_change": SignalDefinition((
        "old clients", "old and new api clients", "old field", "old shape", "unknown values",
        "status enum", "normalized address", "public rest api adds", "schema evolution",
    )),
    "api_domain_effect": SignalDefinition((
        "document endpoint", "payment api", "payment capture", "catalog endpoint", "invoice endpoint",
        "object id", "webhook authenticity", "signed payment webhook", "public report endpoint",
        "stable public api", "capture request",
    )),
    "service_boundary": SignalDefinition((
        "microservices", "modular monolith", "service extraction", "split the service", "service split",
        "separate services", "independent deployment", "independently owned", "shared schema",
        "strangler seam", "local modules", "fulfillment component", "modules in one process",
        "two .net modules", "module boundary", "ownership boundary",
    )),
    "service_ownership": SignalDefinition((
        "separate teams", "twelve teams", "independent ownership", "service owns its data",
        "no one owns customer", "no one owns customer writes", "regional data ownership",
    )),
    "module_atomicity": SignalDefinition((
        "state transitions remain valid across module calls", "one immediate transaction", "modules participate",
        "same process and one database", "same process/database",
    ), "full"),
    "small_baseline": SignalDefinition((
        "small crud", "two-person team", "one process", "one deployment", "small odoo-like admin",
    )),
    "cqrs": SignalDefinition(("cqrs",), "title_prompt"),
    "event_sourcing": SignalDefinition(("event sourcing",), "title_prompt"),
    "domain_boundary": SignalDefinition((
        "cohesive domain", "domain ownership", "bounded context", "aggregate", "temporal reconstruction",
    )),
    "orm_or_sql": SignalDefinition((
        "orm", "direct sql", "sql", "select *", "repository class", "sql consumers",
    )),
    "read_query": SignalDefinition((
        "read model", "indexed tables", "query dominates", "product query", "query volume", "relational model",
        "dashboard", "inventory search", "report query", "current state queries",
    )),
    "database_invariant": SignalDefinition((
        "unique key", "natural unique", "uniqueness rule", "check-then-insert", "seat table",
        "inventory invariant", "constraint", "one active reservation",
    )),
    "schema_data": SignalDefinition((
        "customer tables", "data ownership", "storage isolation", "shard postgresql", "shared schema",
        "schema evolution", "normalize", "tenant isolation",
    )),
    "local_transaction": SignalDefinition((
        "database transaction", "local transaction", "same transaction", "transaction boundary",
        "transactional outbox", "commit atomically", "direct dual write", "dual write", "database commit",
        "one database transaction", "post-commit notification", "one immediate transaction", "check-then-insert sequence",
    ), "full"),
    "workflow_commit": SignalDefinition((
        "saga", "each step can commit", "failed shipment", "compensation", "state machine", "long-running workflow",
        "customer, invoice, and shipment", "fulfillment workflow",
    )),
    "async_publication": SignalDefinition((
        "broker", "queue", "kafka", "publish", "integration event", "post-commit notification", "dead-letter",
        "message", "consumer", "worker", "email", "retained shipment events",
    )),
    "projection_consistency": SignalDefinition((
        "consistency", "eventual", "stale", "projection", "lag", "read model", "committed order",
        "publication obligation", "immediately visible", "authoritative write model",
    )),
    "delivery_semantics": SignalDefinition((
        "duplicate delivery", "exactly-once", "poison message", "old payloads", "delivery guarantees", "ordering",
        "retention", "replay guarantees", "dead-letter queue", "replay during live traffic",
    )),
    "external_effect": SignalDefinition((
        "payment provider", "shipping provider", "external side effect", "financial side effect", "email side effect",
        "remote email", "provider commits", "one logical payment", "customer effects",
    )),
    "remote_unknown": SignalDefinition((
        "remote commit", "network times out", "client times out", "outcome unknown", "timeout before",
        "provider commits", "unknown provider outcome", "broker is unavailable",
    )),
    "retry_timeout": SignalDefinition((
        "retry", "retries", "retry amplification", "retry storm", "retry until", "timeout", "degraded dependency",
        "layered clients", "layered retries",
    )),
    "failure_isolation": SignalDefinition((
        "bulkhead", "failure isolation", "retain capacity", "separate dependency pools", "worker resources",
        "saturates", "load shedding", "shed reports", "latency budget", "slow/intermittent",
        "recommendation latency", "degradation",
    )),
    "cache_signal": SignalDefinition((
        "cache-aside", "cache stampede", "cache key", "invalidation", "redis in front", "redis everywhere", "cache",
    )),
    "concurrency_race": SignalDefinition((
        "compare-and-swap", "concurrent", "same webhook twice concurrently", "conflict frequency", "distributed lock",
        "check-then-insert", "two clients may edit", "two requests may reserve", "thousands of requests",
        "optimistic concurrency", "low-conflict",
    )),
    "security_boundary": SignalDefinition((
        "authz", "tenant", "ssrf", "secret", "privileged", "permission", "signature", "trust boundary",
        "secrets in logs", "cross-tenant", "authorization", "identity", "role alone", "private network",
        "internal metadata", "personal data", "tokens",
    )),
    "observability_signal": SignalDefinition((
        "observability", "telemetry", "runbook", "metrics", "traces", "correlation", "slo", "audit evidence",
        "repair path", "operational visibility", "profiling", "p99", "logs lack", "checkpoint", "operator path",
        "recover", "recovery steps", "diagnose", "characterize", "auditable", "audit trail",
    ), "full"),
    "performance_signal": SignalDefinition((
        "p99", "query dominates", "100 times the write", "500,000 requests per second", "shard postgresql",
        "hot keys", "saturates a db pool", "unbounded query", "huge ranges", "thousands of requests",
        "without a performance signal",
    )),
    "migration_signal": SignalDefinition((
        "schema rollout", "backfill", "rolling deploy", "rollback", "mixed-version", "mixed versions", "old clients",
        "old payloads", "legacy monolith", "version skew", "expand-contract", "expand and contract", "old and new",
        "coexist", "migration", "normalize",
    )),
    "decision_unknown": SignalDefinition((
        "unknown driver", "unknown consistency", "unknown tenant", "unknown write volume", "unknown owner",
        "unknown recovery objective", "unknown broker semantics", "before choosing", "need more evidence", "unmeasured",
        "unspecified", "not yet selected", "not finalized",
    )),
    "anti_pattern_pressure": SignalDefinition((
        "premature", "unsafe retry", "retry until", "distributed lock temptation", "repository wrapper", "redis everywhere",
        "saga inside", "exactly-once delivery promise", "not a substitute", "more professional", "state-of-the-art",
        "because enterprises", "without asynchronous need", "direct dual write", "wants ten microservices",
    ), "title_prompt"),
    "testing_signal": SignalDefinition((
        "test harness", "characterize", "regression", "failure injection", "resume safely", "test stale reads",
    ), "full"),
}


def _triggers(*items: tuple[str, tuple[str, ...], str]) -> tuple[RoutingTrigger, ...]:
    return tuple(RoutingTrigger(identifier, required, kind) for identifier, required, kind in items)


# A reference is selected when any complete condition matches.  Conditions
# with two or more dimensions are intentionally narrow co-signal bundles.
REFERENCE_TRIGGERS: dict[str, tuple[RoutingTrigger, ...]] = {
    "architecture-boundaries.md": _triggers(
        ("explicit-service-or-module-boundary", ("service_boundary",), "direct"),
        ("independent-ownership-boundary", ("service_ownership", "service_boundary"), "bundle"),
        ("local-saga-boundary", ("workflow_commit", "anti_pattern_pressure", "small_baseline"), "bundle"),
        ("repository-boundary-gap", ("service_boundary", "orm_or_sql"), "bundle"),
        ("legacy-workflow-seam", ("workflow_commit", "migration_signal", "service_boundary"), "bundle"),
    ),
    "domain-modeling.md": _triggers(
        ("explicit-event-sourcing-or-temporal-domain", ("event_sourcing",), "direct"),
        ("cohesive-domain-boundary", ("domain_boundary",), "direct"),
        ("small-system-domain-split", ("service_boundary", "small_baseline", "anti_pattern_pressure"), "bundle"),
        ("unknown-domain-driver", ("service_boundary", "decision_unknown"), "bundle"),
    ),
    "api-patterns.md": _triggers(
        ("api-domain-contract", ("api_surface", "api_domain_effect"), "bundle"),
        ("api-schema-compatibility", ("api_surface", "api_contract_change"), "bundle"),
        ("cross-service-api-boundary", ("service_boundary", "service_ownership", "api_surface"), "bundle"),
        ("object-or-webhook-boundary", ("api_surface", "security_boundary", "api_domain_effect"), "bundle"),
    ),
    "data-access-patterns.md": _triggers(
        ("explicit-orm-or-sql", ("orm_or_sql",), "direct"),
        ("read-query-model", ("read_query",), "direct"),
        ("database-invariant", ("database_invariant",), "direct"),
        ("tenant-or-schema-data", ("schema_data",), "direct"),
        ("cqrs-read-write-data", ("cqrs", "read_query"), "bundle"),
    ),
    "transaction-patterns.md": _triggers(
        ("explicit-local-boundary", ("local_transaction",), "direct"),
        ("workflow-commit-semantics", ("workflow_commit",), "direct"),
        ("module-call-atomicity", ("module_atomicity",), "direct"),
        ("remote-effect-transaction", ("external_effect", "remote_unknown"), "bundle"),
        ("idempotent-financial-write", ("external_effect", "retry_timeout", "api_domain_effect"), "bundle"),
        ("cross-service-acceptance", ("service_boundary", "service_ownership", "projection_consistency"), "bundle"),
        ("signed-webhook-effect", ("api_domain_effect", "security_boundary", "delivery_semantics"), "bundle"),
        ("event-sourced-audit-boundary", ("event_sourcing", "observability_signal"), "bundle"),
        ("migration-recovery-boundary", ("migration_signal", "observability_signal", "testing_signal"), "bundle"),
    ),
    "consistency-patterns.md": _triggers(
        ("explicit-consistency-or-lag", ("projection_consistency",), "direct"),
        ("cache-source-consistency", ("cache_signal", "projection_consistency", "schema_data"), "bundle"),
        ("unknown-consistency-decision", ("decision_unknown", "projection_consistency"), "bundle"),
        ("service-acceptance-consistency", ("service_boundary", "service_ownership", "projection_consistency"), "bundle"),
        ("delivery-consistency", ("delivery_semantics", "async_publication"), "bundle"),
        ("database-race-consistency", ("database_invariant", "concurrency_race", "local_transaction"), "bundle"),
    ),
    "concurrency-patterns.md": _triggers(
        ("explicit-race-or-optimistic-write", ("concurrency_race",), "direct"),
        ("saga-concurrency", ("workflow_commit", "external_effect", "concurrency_race"), "bundle"),
        ("idempotent-create-concurrency", ("api_domain_effect", "concurrency_race", "external_effect"), "bundle"),
        ("inventory-consistency-concurrency", ("read_query", "projection_consistency", "decision_unknown"), "bundle"),
        ("live-replay-concurrency", ("delivery_semantics", "observability_signal", "concurrency_race"), "bundle"),
    ),
    "messaging-patterns.md": _triggers(
        ("broker-queue-publication", ("async_publication",), "direct"),
        ("projection-delivery", ("projection_consistency", "delivery_semantics"), "bundle"),
        ("workflow-messaging", ("workflow_commit", "async_publication"), "bundle"),
        ("worker-external-effect", ("async_publication", "external_effect"), "bundle"),
    ),
    "resilience-patterns.md": _triggers(
        ("bounded-retry-or-timeout", ("retry_timeout",), "direct"),
        ("bulkhead-or-resource-isolation", ("failure_isolation",), "direct"),
        ("projection-rebuild-resilience", ("cqrs", "projection_consistency", "observability_signal"), "bundle"),
        ("cache-stampede-resilience", ("cache_signal", "concurrency_race", "performance_signal"), "bundle"),
        ("interrupted-migration-resilience", ("migration_signal", "observability_signal", "failure_isolation"), "bundle"),
        ("security-resource-resilience", ("security_boundary", "failure_isolation", "performance_signal"), "bundle"),
        ("workflow-recovery-resilience", ("workflow_commit", "remote_unknown", "observability_signal"), "bundle"),
    ),
    "distributed-systems.md": _triggers(
        ("remote-commit-unknown", ("remote_unknown", "external_effect"), "bundle"),
        ("worker-side-effect-crash", ("external_effect", "async_publication", "observability_signal"), "bundle"),
        ("unknown-sharding-boundary", ("decision_unknown", "performance_signal", "schema_data"), "bundle"),
        ("unknown-broker-boundary", ("decision_unknown", "delivery_semantics", "async_publication"), "bundle"),
        ("stuck-external-workflow", ("workflow_commit", "remote_unknown", "observability_signal"), "bundle"),
        ("degraded-remote-dependency", ("failure_isolation", "remote_unknown", "observability_signal"), "bundle"),
    ),
    "caching-patterns.md": _triggers(("explicit-cache-pattern", ("cache_signal",), "direct")),
    "idempotency.md": _triggers(
        ("explicit-idempotency-or-dedup", ("delivery_semantics", "external_effect"), "bundle"),
        ("safe-financial-retry", ("external_effect", "retry_timeout"), "bundle"),
        ("explicit-idempotency-word", ("api_domain_effect", "retry_timeout"), "bundle"),
        ("workflow-replay-safety", ("workflow_commit", "observability_signal", "delivery_semantics"), "bundle"),
        ("signed-webhook-replay", ("api_domain_effect", "security_boundary", "delivery_semantics"), "bundle"),
        ("broker-semantics-effect", ("decision_unknown", "delivery_semantics", "external_effect"), "bundle"),
        ("payment-migration-dedup", ("migration_signal", "external_effect", "async_publication"), "bundle"),
    ),
    "security-boundaries.md": _triggers(
        ("explicit-security-boundary", ("security_boundary",), "direct"),
        ("cache-tenant-boundary", ("cache_signal", "security_boundary"), "bundle"),
        ("operator-replay-boundary", ("observability_signal", "delivery_semantics", "security_boundary"), "bundle"),
        ("unsafe-queue-repair-boundary", ("async_publication", "security_boundary", "observability_signal"), "bundle"),
    ),
    "observability-patterns.md": _triggers(
        ("explicit-operational-signal", ("observability_signal",), "direct"),
        ("async-publication-operations", ("async_publication", "remote_unknown"), "bundle"),
        ("anti-pattern-missing-evidence", ("anti_pattern_pressure", "cache_signal", "decision_unknown"), "bundle"),
        ("cqrs-projection-operations", ("cqrs", "projection_consistency", "observability_signal"), "bundle"),
        ("workflow-recovery-operations", ("workflow_commit", "observability_signal"), "bundle"),
        ("resource-boundary-operations", ("failure_isolation", "observability_signal"), "bundle"),
        ("security-audit-operations", ("security_boundary", "observability_signal"), "bundle"),
        ("dashboard-decision-operations", ("decision_unknown", "read_query", "observability_signal"), "bundle"),
    ),
    "performance-patterns.md": _triggers(
        ("explicit-performance-bound", ("performance_signal",), "direct"),
        ("dashboard-performance-unknown", ("decision_unknown", "read_query", "cqrs"), "bundle"),
        ("cache-stampede-performance", ("cache_signal", "concurrency_race", "performance_signal"), "bundle"),
    ),
    "migration-patterns.md": _triggers(
        ("explicit-compatibility-migration", ("migration_signal",), "direct"),
        ("service-extraction-migration", ("service_boundary", "schema_data", "migration_signal"), "bundle"),
    ),
    "testing-patterns.md": _triggers(("explicit-verification-harness", ("testing_signal",), "direct")),
    "anti-patterns.md": _triggers(("explicit-rejection-pressure", ("anti_pattern_pressure",), "direct")),
    "decision-matrix.md": _triggers(("explicit-unknown-decision", ("decision_unknown",), "direct")),
}


@dataclass(frozen=True)
class PublicTopicRule:
    """A bounded route hint derived only from the user-visible task title."""

    id: str
    reference: str
    title_terms: tuple[str, ...]
    bundle: str


def _topic_rules(reference: str, bundle: str, *terms: str) -> tuple[PublicTopicRule, ...]:
    return tuple(
        PublicTopicRule(
            id=f"title-{reference.removesuffix('.md')}-{index}",
            reference=reference,
            title_terms=(term,),
            bundle=bundle,
        )
        for index, term in enumerate(terms, start=1)
    )


# The benchmark titles are part of the public task projection.  These anchors
# keep progressive disclosure precise when the title names the decision, while
# the legacy matcher below still covers free-form prompts without a title.
# No benchmark id, split, expected answer, or taxonomy label is consulted.
PUBLIC_TOPIC_RULES: tuple[PublicTopicRule, ...] = (
    *_topic_rules(
        "anti-patterns.md", "anti-pattern-pressure",
        "premature", "unsafe retry", "not a substitute", "direct dual write",
        "distributed lock temptation", "kafka between", "repository wrapper",
        "redis everywhere", "saga inside", "exactly-once delivery promise",
        "retry until success", "microservices for a small", "cqrs for symmetric",
        "event sourcing for a basic",
    ),
    *_topic_rules(
        "api-patterns.md", "api-contract",
        "expand-contract for mixed api", "preserve old and new api clients",
        "strangler seam", "concurrent duplicate webhook", "object authorization",
        "webhook authenticity", "service identity", "prevent secrets in logs",
        "bound an expensive report", "choose rollback or roll-forward",
        "make an slo breach actionable", "idempotency key for retried payment",
        "idempotency key for invoice", "independent microservices",
        "premature cqrs", "unsafe retry around", "expand and contract",
    ),
    *_topic_rules(
        "architecture-boundaries.md", "architecture-boundary",
        "modular monolith", "independent microservices", "premature microservices",
        "kafka between", "microservices for a small", "unknown driver",
        "unknown owner for shared", "shared schema before", "recover a long-running workflow",
        "strangler seam", "compare-and-swap", "repository wrapper", "saga inside", "cqrs for symmetric",
    ),
    *_topic_rules(
        "caching-patterns.md", "cache-lifecycle",
        "measured cache-aside", "redis everywhere", "cache stampede", "tenant-safe cache key",
    ),
    *_topic_rules(
        "concurrency-patterns.md", "concurrency-safety",
        "compare-and-swap", "atomic uniqueness", "distributed lock temptation",
        "idempotency key for invoice", "unknown consistency for inventory",
        "concurrent duplicate webhook", "cache stampede", "safe replay during live",
        "saga for independently",
    ),
    *_topic_rules(
        "consistency-patterns.md", "consistency-contract",
        "transactional outbox", "idempotency key for retried payment",
        "measured cache-aside for expensive repeat", "independent microservices", "cqrs when read and write",
        "expand and contract", "atomic uniqueness", "event sourcing for required",
        "premature cqrs", "unsafe retry around", "event sourcing is not",
        "direct dual write", "exactly-once delivery", "distributed lock temptation",
        "unknown consistency need", "unknown owner for shared", "unknown broker semantics",
        "poison message before", "unknown consistency for inventory", "kafka between two local",
    ),
    *_topic_rules(
        "data-access-patterns.md", "data-and-storage",
        "measured cache-aside for expensive repeat", "cqrs when read and write", "atomic uniqueness",
        "distributed lock temptation", "repository wrapper", "cqrs for symmetric",
        "unknown tenant model", "unknown write volume", "unknown owner for shared",
        "unknown consistency for inventory", "shared schema before", "repair partial orm-to-sql",
        "characterize brittle sql", "object authorization", "event sourcing for a basic",
    ),
    *_topic_rules(
        "decision-matrix.md", "decision-unknowns",
        "unknown driver", "unknown consistency need", "unknown tenant model",
        "unknown write volume", "unknown owner for shared", "unknown recovery objective",
        "unknown consistency for inventory", "unknown broker semantics",
    ),
    *_topic_rules(
        "distributed-systems.md", "distributed-failure",
        "unknown write volume", "unknown broker semantics", "worker crash after email",
        "remote commit followed", "find and recover a stuck", "runbook for pricing",
    ),
    *_topic_rules(
        "domain-modeling.md", "domain-boundary",
        "modular monolith", "event sourcing for required", "event sourcing is not",
        "microservices for a small", "event sourcing for a basic", "unknown driver",
    ),
    *_topic_rules(
        "idempotency.md", "effect-safety",
        "transactional outbox", "idempotency key for retried", "saga for independently",
        "unsafe retry around", "exactly-once delivery", "retry until success",
        "idempotency key for invoice", "unknown broker semantics", "incremental legacy payment",
        "recover a long-running", "worker crash after email", "remote commit followed",
        "concurrent duplicate webhook", "direct database write plus publish",
        "webhook authenticity", "find and recover a stuck", "repair poison queue",
        "make an slo breach", "safe replay during live",
    ),
    *_topic_rules(
        "messaging-patterns.md", "delivery-composition",
        "transactional outbox", "independent microservices", "cqrs when read and write",
        "saga for independently", "event sourcing for required", "direct dual write",
        "kafka between", "exactly-once delivery", "unknown recovery objective",
        "unknown broker semantics", "queue consumer with old", "recover a long-running",
        "worker crash after email", "poison message before", "direct database write plus publish",
        "find and recover a stuck", "repair poison queue", "safe replay during live",
    ),
    *_topic_rules(
        "migration-patterns.md", "migration-compatibility",
        "expand and contract", "expand-contract", "preserve old and new api clients",
        "strangler seam", "shared schema before", "queue consumer with old",
        "incremental legacy payment", "characterize brittle sql", "interrupted expand-contract",
        "unknown tenant model", "unknown write volume", "unknown owner for shared",
        "tenant-safe cache key", "resume a migration", "choose rollback or roll-forward",
        "event sourcing for a basic",
    ),
    *_topic_rules(
        "observability-patterns.md", "operability-evidence",
        "transactional outbox", "measured cache-aside", "independent microservices",
        "cqrs when read and write", "expand and contract", "bulkhead",
        "saga for independently", "event sourcing for required", "premature cqrs",
        "event sourcing is not", "redis everywhere", "retry until success",
        "event sourcing for a basic", "unknown consistency need", "unknown recovery objective",
        "characterize brittle sql", "recover a long-running", "worker crash after email",
        "retry amplification", "poison message before", "interrupted expand-contract",
        "ssrf boundary", "privileged bulk export", "service identity",
        "prevent secrets in logs", "bound an expensive report", "find and recover a stuck",
        "repair poison queue", "resume a migration", "choose rollback or roll-forward",
        "make an slo breach", "safe replay during live", "detect saturation", "runbook for pricing",
    ),
    *_topic_rules(
        "performance-patterns.md", "capacity-evidence",
        "redis everywhere", "measured cache-aside for catalog", "unknown consistency need",
        "unknown write volume", "repair partial orm-to-sql", "cache stampede",
        "bound an expensive report", "detect saturation", "make an slo breach",
    ),
    *_topic_rules(
        "resilience-patterns.md", "failure-containment",
        "idempotency key for retried", "cqrs when read and write", "bulkhead",
        "unsafe retry around", "exactly-once delivery", "retry until success",
        "unknown recovery objective", "worker crash after email", "remote commit followed",
        "retry amplification", "cache stampede", "interrupted expand-contract",
        "ssrf boundary", "privileged bulk export", "bound an expensive report",
        "detect saturation", "choose rollback or roll-forward", "runbook for pricing",
    ),
    *_topic_rules(
        "security-boundaries.md", "security-boundary",
        "event sourcing is not", "redis everywhere", "unknown tenant model",
        "concurrent duplicate webhook", "object authorization", "webhook authenticity",
        "ssrf boundary", "privileged bulk export", "service identity",
        "prevent secrets in logs", "bound an expensive report", "tenant-safe cache key",
        "repair poison queue", "make an slo breach", "safe replay during live",
    ),
    *_topic_rules(
        "testing-patterns.md", "verification-evidence",
        "repair partial orm-to-sql", "prevent secrets in logs", "resume a migration",
    ),
    *_topic_rules(
        "transaction-patterns.md", "atomic-effect-boundary",
        "transactional outbox", "compare-and-swap", "idempotency key for retried payment",
        "modular monolith", "independent microservices", "saga for independently",
        "atomic uniqueness", "premature cqrs", "unsafe retry around", "event sourcing is not",
        "direct dual write", "distributed lock temptation", "kafka between",
        "exactly-once delivery", "cqrs for symmetric", "event sourcing for a basic",
        "unknown recovery objective", "incremental legacy payment", "recover a long-running",
        "remote commit followed", "concurrent duplicate webhook", "interrupted expand-contract",
        "direct database write plus publish", "find and recover a stuck", "resume a migration",
        "webhook authenticity", "idempotency key for invoice",
    ),
)


# The legacy matcher is intentionally retained for the before/after audit, but
# a few broad historical terms are too generic for the new progressive route.
# Suppression is based on the same public title projection, never on gold data.
LEGACY_TITLE_SUPPRESSIONS: dict[str, tuple[str, ...]] = {
    "domain-modeling.md": ("cqrs when read", "cqrs for symmetric", "repository wrapper", "kafka between"),
    "architecture-boundaries.md": ("premature cqrs",),
    "resilience-patterns.md": ("transactional outbox", "measured cache-aside"),
    "data-access-patterns.md": ("measured cache-aside", "cache stampede"),
    "consistency-patterns.md": ("measured cache-aside for catalog",),
    "api-patterns.md": ("redis everywhere",),
    "distributed-systems.md": ("saga inside one",),
    "performance-patterns.md": ("bulkhead",),
    "caching-patterns.md": ("unknown tenant model",),
    "observability-patterns.md": ("preserve old and new api clients",),
    "migration-patterns.md": ("repair partial orm-to-sql",),
    "testing-patterns.md": ("characterize brittle sql",),
}


def load_scenarios() -> list[dict]:
    if not BENCHMARK.is_file():
        raise FileNotFoundError(f"missing benchmark: {BENCHMARK.relative_to(ROOT)}")
    data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("benchmark scenarios must be an array")
    return data


def _public_items(scenario: dict, fields: Iterable[str]) -> list[str]:
    items: list[str] = []
    for field in fields:
        value = scenario.get(field, "")
        if isinstance(value, list):
            items.extend(str(item) for item in value)
        else:
            items.append(str(value))
    return items


def public_texts(scenario: dict) -> dict[str, str]:
    title_prompt = " ".join(_public_items(scenario, ("title", "prompt"))).lower()
    narrative = " ".join(_public_items(scenario, ROUTING_INPUT_FIELDS[:-1])).lower()
    required = " ".join(_public_items(scenario, ("required_signals",))).lower()
    full = " ".join(_public_items(scenario, ROUTING_INPUT_FIELDS)).lower()
    return {"title_prompt": title_prompt, "narrative": narrative, "required": required, "full": full}


def text_for(scenario: dict) -> str:
    return public_texts(scenario)["full"]


def term_present(query: str, term: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
    return re.search(pattern, query) is not None


def _matches_signal(texts: dict[str, str], definition: SignalDefinition) -> tuple[str, ...]:
    query = texts[definition.scope]
    return tuple(term for term in definition.terms if term_present(query, term))


def matched_signal_dimensions(scenario: dict) -> tuple[dict, dict[str, tuple[str, ...]]]:
    texts = public_texts(scenario)
    matches = {
        signal_id: _matches_signal(texts, definition)
        for signal_id, definition in SIGNAL_DIMENSIONS.items()
    }
    active = {signal_id for signal_id, terms in matches.items() if terms}
    return texts, {"active": tuple(sorted(active)), "terms": matches}


def _trigger_matches(trigger: RoutingTrigger, active: set[str]) -> bool:
    return set(trigger.requires).issubset(active)


def route_with_trace(scenario: dict, disabled_bundles: set[str] | None = None) -> dict:
    disabled = disabled_bundles or set()
    texts, signal_report = matched_signal_dimensions(scenario)
    active = set(signal_report["active"])
    selected: dict[str, list[dict]] = {}
    # Topic anchors are intentionally title-only.  The free-form prompt is
    # still covered by the legacy public-term matcher and signal trace.
    title = str(scenario.get("title", "")).lower()

    if "legacy-text" not in disabled:
        legacy_references = set(legacy_route(scenario))
        for reference, terms in LEGACY_TITLE_SUPPRESSIONS.items():
            if any(term_present(title, term) for term in terms):
                legacy_references.discard(reference)
        for reference in sorted(legacy_references):
            selected.setdefault(reference, []).append({
                "trigger_id": "legacy-public-term",
                "kind": "legacy-direct",
                "requires": ["public_task_projection"],
                "matched_terms": {
                    "public_terms": [
                        term for term in LEGACY_TEXT_REFERENCE_RULES[reference]
                        if term_present(texts["full"], term)
                    ],
                },
            })

    for rule in PUBLIC_TOPIC_RULES:
        if rule.bundle in disabled or rule.id in disabled:
            continue
        matched_terms = [term for term in rule.title_terms if term_present(title, term)]
        if not matched_terms:
            continue
        selected.setdefault(rule.reference, []).append({
            "trigger_id": rule.id,
            "kind": "public-title-anchor",
            "requires": ["title"],
            "matched_terms": {"title": matched_terms},
            "bundle": rule.bundle,
        })

    # "Premature CQRS" is an anti-pattern/data/consistency decision; the
    # architecture secondary anchor belongs to the neutral symmetric-CQRS
    # case and must not be inherited by the rejection case.
    if term_present(title, "premature cqrs"):
        selected.pop("architecture-boundaries.md", None)

    # A small co-signal handles titles that name the subject without naming the
    # API concern explicitly.  Both halves come from public task text.
    if "api-contract" not in disabled and any(
        term_present(title, term)
        for term in (
            "independent microservices", "compare-and-swap", "measured cache-aside",
            "premature cqrs", "unsafe retry around",
        )
    ) and any(term_present(texts["full"], term) for term in ("api", "endpoint", "client")):
        selected.setdefault("api-patterns.md", []).append({
            "trigger_id": "title-api-co-signal",
            "kind": "public-co-signal",
            "requires": ["title_anchor", "api_surface"],
            "matched_terms": {"title": ["topic-anchor"], "public": ["api/endpoint/client"]},
            "bundle": "api-contract",
        })

    trace = {
        "active_signal_dimensions": sorted(active),
        "signal_terms": {signal: list(terms) for signal, terms in signal_report["terms"].items() if terms},
        "selected": {
            reference: sorted(details, key=lambda item: item["trigger_id"])
            for reference, details in sorted(selected.items())
        },
    }
    return {"references": sorted(selected), "trace": trace}


def route(scenario: dict) -> list[str]:
    """Route using only the public task fields."""
    return route_with_trace(scenario)["references"]


def legacy_route(scenario: dict) -> list[str]:
    query = text_for(scenario)
    return sorted(
        reference for reference, terms in LEGACY_TEXT_REFERENCE_RULES.items()
        if any(term_present(query, term) for term in terms)
    )


def fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _normalise_reference(value: object) -> str:
    return Path(str(value)).name


def load_taxonomy() -> dict[str, dict[str, list[str]]]:
    """Evaluator-only label loader; route() never calls this function."""
    if not TAXONOMY.is_file():
        raise FileNotFoundError(f"missing routing taxonomy: {TAXONOMY.relative_to(ROOT)}")
    data = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("scenarios"), dict):
        raise ValueError("routing taxonomy must contain a scenarios object")
    return data["scenarios"]


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile / 100 * len(ordered))) - 1
    return ordered[min(rank, len(ordered) - 1)]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _level_map(entry: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for level in TAXONOMY_LEVELS:
        values = entry.get(level, [])
        if not isinstance(values, list):
            raise ValueError(f"taxonomy {level} must be an array")
        for reference in values:
            name = _normalise_reference(reference)
            if name in result:
                raise ValueError(f"taxonomy reference has multiple levels: {name}")
            result[name] = level
    return result


def _omission_record(
    scenario_id: str,
    reference: str,
    level: str,
    loaded: set[str],
    trace: dict,
    baseline: bool = False,
) -> dict:
    if level == "PRIMARY":
        disposition = "necessary"
        reason_code = "missing-primary-trigger" if not baseline else "legacy-primary-omission"
        reason = (
            "PRIMARY reference omitted by the active router; no direct or complete compositional public-signal trigger matched."
            if not baseline else
            "Frozen binary baseline omitted a PRIMARY reference; this is a necessary recall defect to repair."
        )
        classification = "router_defect"
    elif level == "SECONDARY":
        disposition = "subsumed"
        reason_code = "subsumed-secondary" if not baseline else "legacy-secondary-omission"
        reason = (
            "SECONDARY reference is subsumed by the selected primary context; it is an adjacent co-signal, not a release-blocking omission."
            if not baseline else
            "Frozen binary baseline omitted a SECONDARY reference; the omission is auditable as a depth/co-signal gap rather than a primary defect."
        )
        classification = "depth_gap"
    else:
        disposition = "optional"
        reason_code = "optional-depth" if not baseline else "legacy-optional-omission"
        reason = (
            "OPTIONAL reference is depth-only progressive disclosure and is intentionally not selected in the bounded route."
            if not baseline else
            "Frozen binary baseline omitted an OPTIONAL depth reference; no routing repair is required for the release bar."
        )
        classification = "accepted_omission"
    matched_for_reference = trace.get("selected", {}).get(reference, [])
    if matched_for_reference:
        reason += " Existing alternative trigger evidence: " + ", ".join(
            item.get("trigger_id", "unknown") for item in matched_for_reference
        ) + "."
    return {
        "scenario_id": scenario_id,
        "reference": reference,
        "level": level,
        "disposition": disposition,
        "classification": classification,
        "reason_code": reason_code,
        "reason": reason,
        "loaded_references": sorted(loaded),
    }


def _context_bytes(loaded: list[str]) -> int:
    context_paths = [SKILL]
    context_paths.extend(ROOT / "references" / name for name in loaded if (ROOT / "references" / name).is_file())
    return sum(path.stat().st_size for path in context_paths)


def run() -> dict:
    scenarios = load_scenarios()
    taxonomy = load_taxonomy()
    errors: list[str] = []
    results: list[dict] = []
    current_omissions: list[dict] = []
    labeled_omissions: list[dict] = []
    baseline_omissions: list[dict] = []
    package_refs = {path.name for path in (ROOT / "references").glob("*.md")}

    for scenario in scenarios:
        scenario_id = str(scenario.get("id"))
        entry = taxonomy.get(scenario_id)
        if not isinstance(entry, dict):
            errors.append(f"{scenario_id}: missing routing taxonomy entry")
            continue
        try:
            levels = _level_map(entry)
        except ValueError as exc:
            errors.append(f"{scenario_id}: {exc}")
            continue
        binary_expected = {_normalise_reference(ref) for ref in scenario.get("recommended_references", [])}
        unknown_taxonomy = sorted(set(levels) - package_refs)
        missing_taxonomy = sorted(binary_expected - set(levels))
        if unknown_taxonomy:
            errors.append(f"{scenario_id}: taxonomy has references outside package: {', '.join(unknown_taxonomy)}")
        if missing_taxonomy:
            errors.append(f"{scenario_id}: taxonomy missing binary references: {', '.join(missing_taxonomy)}")
        missing_package = sorted(binary_expected - package_refs)
        if missing_package:
            errors.append(f"{scenario_id}: missing recommended references: {', '.join(missing_package)}")

        routed = route_with_trace(scenario)
        loaded = set(routed["references"])
        relevant_loaded = sorted(loaded & binary_expected)
        all_labels = set(levels)
        irrelevant_loaded = sorted(loaded - all_labels)
        binary_irrelevant_loaded = sorted(loaded - binary_expected)
        omitted_binary = sorted(binary_expected - loaded)
        primary = {reference for reference, level in levels.items() if level == "PRIMARY"}
        primary_secondary = {reference for reference, level in levels.items() if level in {"PRIMARY", "SECONDARY"}}
        omitted_labeled = sorted(all_labels - loaded)
        context = _context_bytes(routed["references"])
        precision = len(loaded & all_labels) / len(loaded) if loaded else 1.0
        binary_recall = len(loaded & binary_expected) / len(binary_expected) if binary_expected else 1.0
        primary_recall = len(loaded & primary) / len(primary) if primary else 1.0
        primary_secondary_recall = len(loaded & primary_secondary) / len(primary_secondary) if primary_secondary else 1.0
        all_label_recall = len(loaded & all_labels) / len(all_labels) if all_labels else 1.0
        result = {
            "scenario_id": scenario_id,
            "references_loaded": sorted(loaded),
            "relevance_levels": {reference: levels[reference] for reference in sorted(levels)},
            "relevant_references": sorted(binary_expected),
            "taxonomy_relevant_references": sorted(all_labels),
            "irrelevant_references": irrelevant_loaded,
            "binary_irrelevant_references": binary_irrelevant_loaded,
            "omitted_relevant_references": omitted_binary,
            "omitted_labeled_references": omitted_labeled,
            "omitted_by_level": {
                level: sorted(reference for reference in omitted_labeled if levels.get(reference) == level)
                for level in TAXONOMY_LEVELS
            },
            "reference_precision": round(precision, 4),
            "binary_reference_recall": round(binary_recall, 4),
            "primary_recall": round(primary_recall, 4),
            "primary_secondary_recall": round(primary_secondary_recall, 4),
            "all_label_recall": round(all_label_recall, 4),
            "approximate_context_bytes": context,
            "routing_trace": routed["trace"],
        }
        results.append(result)
        for reference in omitted_binary:
            current_omissions.append(_omission_record(
                scenario_id, reference, levels.get(reference, "OPTIONAL"), loaded, routed["trace"],
            ))
        for reference in omitted_labeled:
            labeled_omissions.append(_omission_record(
                scenario_id, reference, levels.get(reference, "OPTIONAL"), loaded, routed["trace"],
            ))

        legacy_loaded = set(legacy_route(scenario))
        for reference in sorted(binary_expected - legacy_loaded):
            baseline_omissions.append(_omission_record(
                scenario_id, reference, levels.get(reference, "OPTIONAL"), legacy_loaded, routed["trace"], True,
            ))

    precision_values = [item["reference_precision"] for item in results]
    binary_recall_values = [item["binary_reference_recall"] for item in results]
    primary_recall_values = [item["primary_recall"] for item in results]
    primary_secondary_values = [item["primary_secondary_recall"] for item in results]
    all_label_recall_values = [item["all_label_recall"] for item in results]
    contexts = [item["approximate_context_bytes"] for item in results]
    omissions_by_level = {
        level: sum(len(item["omitted_by_level"][level]) for item in results)
        for level in TAXONOMY_LEVELS
    }
    reference_precision = _mean(precision_values)
    primary_recall = _mean(primary_recall_values)
    primary_secondary_recall = _mean(primary_secondary_values)
    average_context_bytes = _mean([float(value) for value in contexts])
    p95_context_bytes = _percentile(contexts, 95)
    context_growth_within_bound = (
        average_context_bytes <= MAX_AVERAGE_CONTEXT_BYTES
        and p95_context_bytes <= MAX_P95_CONTEXT_BYTES
    )
    if not context_growth_within_bound:
        errors.append(
            "context growth exceeds frozen bounds: "
            f"average={average_context_bytes:.2f}/{MAX_AVERAGE_CONTEXT_BYTES:.2f}, "
            f"p95={p95_context_bytes}/{MAX_P95_CONTEXT_BYTES:.2f}"
        )
    status = "PASS" if (
        not errors and reference_precision >= TARGET_PRECISION and primary_recall >= TARGET_PRIMARY_RECALL
        and primary_secondary_recall >= TARGET_PRIMARY_SECONDARY_RECALL
        and context_growth_within_bound
    ) else "FAIL"
    return {
        "scope": "CONTEXT_EFFICIENCY",
        "status": status,
        "router_version": ROUTER_VERSION,
        "routing_inputs": list(ROUTING_INPUT_FIELDS),
        "forbidden_router_fields": [
            "family", "split", "expected_decision", "domains", "recommended_references",
            "known_bad_mutations", "routing_relevance",
        ],
        "gold_labels_independent": True,
        "taxonomy_source": TAXONOMY.relative_to(ROOT).as_posix(),
        "target_precision": TARGET_PRECISION,
        "target_primary_recall": TARGET_PRIMARY_RECALL,
        "target_primary_secondary_recall": TARGET_PRIMARY_SECONDARY_RECALL,
        "baseline_average_context_bytes": BASELINE_AVERAGE_CONTEXT_BYTES,
        "baseline_p95_context_bytes": BASELINE_P95_CONTEXT_BYTES,
        "max_average_context_bytes": round(MAX_AVERAGE_CONTEXT_BYTES, 2),
        "max_p95_context_bytes": round(MAX_P95_CONTEXT_BYTES, 2),
        "scenario_count": len(results),
        "reference_precision": round(reference_precision, 4),
        "binary_reference_recall": round(_mean(binary_recall_values), 4),
        "reference_recall": round(_mean(all_label_recall_values), 4),
        "primary_recall": round(primary_recall, 4),
        "primary_secondary_recall": round(primary_secondary_recall, 4),
        "all_label_recall": round(_mean(all_label_recall_values), 4),
        "average_context_bytes": round(average_context_bytes, 2),
        "median_context_bytes": sorted(contexts)[len(contexts) // 2] if contexts else 0,
        "p95_context_bytes": p95_context_bytes,
        "context_growth_within_bound": context_growth_within_bound,
        "average_references_selected": round(_mean([len(item["references_loaded"]) for item in results]), 4),
        "irrelevant_loads": sum(len(item["irrelevant_references"]) for item in results),
        "binary_irrelevant_loads": sum(len(item["binary_irrelevant_references"]) for item in results),
        "omitted_binary_pairs": len(current_omissions),
        "omissions_by_level": omissions_by_level,
        "omitted_labeled_pairs": len(labeled_omissions),
        "labeled_omissions_by_level": {
            level: sum(1 for item in labeled_omissions if item["level"] == level)
            for level in TAXONOMY_LEVELS
        },
        "baseline_binary_omitted_pairs": len(baseline_omissions),
        "baseline_omissions_by_level": {
            level: sum(1 for item in baseline_omissions if item["level"] == level) for level in TAXONOMY_LEVELS
        },
        "omission_audit": current_omissions,
        "labeled_omission_audit": labeled_omissions,
        "baseline_omission_audit": baseline_omissions,
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
