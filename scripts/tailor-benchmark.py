#!/usr/bin/env python3
"""Make generated benchmark decisions and mutation diagnostics scenario-specific.

The corpus contains a hand-reviewed seed set plus generated extension cases.
This maintenance script only rewrites the extension IDs (101 and above) and
keeps their facts, unknowns, invariants, forces, and labels intact.  Keeping
the tailoring declarative makes it possible to audit whether diversity is
semantic rather than an accidental string variation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "tests" / "benchmark" / "scenarios.json"


# id: preferred patterns, rejected patterns, simpler comparison, injected
# failure, evidence axis, and the diagnostic emitted by the mutation oracle.
PROFILES = {
    "SU-101": ("durable idempotency key", "unique operation-result constraint", "single durable invoice write", "client timeout after invoice commit", "key retention and replay lookup", "duplicate invoice risk is no longer bounded"),
    "SU-102": ("reserved password-reset worker pool", "bounded export concurrency", "one shared worker pool with admission control", "export load consumes the shared pool", "pool reservation and latency isolation", "optional export work can starve password reset"),
    "SU-103": ("cache-aside with a five-minute freshness budget", "single-flight refresh with database fallback", "measured database query path", "cache eviction or outage during a catalog read", "p99 improvement and stale-read bound", "cache failure can corrupt or over-age catalog data"),
    "SU-104": ("additive address field with translation", "telemetry-gated contract retirement", "old response shape kept during a compatibility window", "old and new clients overlap during the rollout", "client-version coverage and rollback safety", "mixed clients lose a valid address representation"),
    "SR-101": ("modular monolith with local transactions", "explicit seams before extraction", "one deployable admin with module boundaries", "a service boundary adds a network failure", "team ownership and deployment pressure", "service count is increased without an operational driver"),
    "SR-102": ("one transactional read/write model", "indexed query paths for the admin", "the existing relational model", "a projection lags a committed admin write", "read-after-write behavior and projection cost", "CQRS adds lag without a stated read/write asymmetry"),
    "SR-103": ("append-only audit table", "current-state model plus actor history", "current-state storage with an audit trail", "an audit record must be retained or redacted", "audit queries, privacy retention, and replay need", "event history replaces a source of truth without a temporal requirement"),
    "SR-104": ("in-process domain notification", "outbox only when a durable consumer exists", "a local post-commit callback", "the shared transaction fails after notification setup", "atomicity, consumer ownership, and broker operations", "a broker boundary weakens local atomicity without an async consumer"),
    "NE-101": ("map ownership and deployment drivers", "retain the modular monolith pending evidence", "the current cohesive service", "a proposed split crosses transaction or authorization ownership", "independent deploy, data ownership, and fault isolation", "a service boundary is selected before its driver is known"),
    "NE-102": ("measure read-after-write and lag tolerance", "start with the existing query model", "a direct read model with explicit freshness", "a dashboard projection serves stale financial state", "freshness budget, correction UX, and projection cost", "CQRS is chosen before the dashboard consistency contract exists"),
    "NE-103": ("define the tenant isolation and key model", "pilot scoped indexes before partitioning", "one schema with explicit tenant predicates", "a tenant query or cache key crosses the boundary", "tenant cardinality, isolation, and migration scope", "partitioning is chosen before tenant ownership and isolation are defined"),
    "NE-104": ("measure write volume and hotspot distribution", "exhaust indexing and vertical scaling first", "the current single-shard transaction path", "a shard key creates a cross-shard write", "write rate, hotspot skew, and transaction locality", "sharding is selected from projected scale without measured pressure"),
    "NE-105": ("assign an owner and data contract", "keep a modular boundary while ownership is clarified", "one authoritative customer record", "two services mutate shared customer truth", "ownership, change cadence, and consistency obligations", "service extraction duplicates mutable customer ownership"),
    "NE-106": ("define RTO/RPO and compensation budget", "map workflow states before choosing Saga", "the current workflow with explicit recovery states", "a fulfillment step commits before the workflow times out", "recovery objective, compensation budget, and side-effect safety", "Saga is selected before the recovery objective is known"),
    "NE-107": ("measure freshness and read-after-write need", "keep inventory authority separate from search", "the authoritative inventory transaction", "search shows stock after the authoritative state changed", "freshness tolerance, index lag, and oversell protection", "eventual search consistency is accepted before the inventory invariant is defined"),
    "NE-108": ("inspect delivery, ordering, and acknowledgment semantics", "design deduplication around observed broker behavior", "a durable local queue with explicit retries", "the broker redelivers an event after an ambiguous acknowledgment", "delivery semantics, duplicate rate, and effect idempotency", "exactly-once behavior is assumed from broker delivery"),
    "BF-101": ("compatibility adapter with contract telemetry", "expand-contract response rollout", "the existing payload contract", "old and new clients parse different address shapes", "client-version coverage, deprecation, and rollback", "a breaking payload change is shipped before old clients retire"),
    "BF-102": ("modular boundary before extraction", "ownership map with a compatibility view", "the shared schema with one owner", "two prospective services write the same table", "ownership, coupling, and migration sequence", "services are split while mutable schema ownership remains shared"),
    "BF-103": ("characterization tests around query results", "incremental SQL seam with rollback", "the current ORM behavior captured by tests", "the refactored query changes a caller-visible result", "result compatibility, query cost, and rollback", "a wholesale SQL rewrite changes behavior without characterization evidence"),
    "BF-104": ("versioned decoder with tolerant reads", "quarantine for unsupported payloads", "the current consumer with explicit version handling", "an old producer sends a payload after the consumer deploys", "payload-version coverage, ordering, and quarantine recovery", "old event versions are dropped during mixed deployment"),
    "BF-105": ("dual-read with a verified transition", "idempotent backfill with reconciliation", "the legacy payment field kept during migration", "a retry observes two payment representations", "backfill parity, duplicate protection, and rollback", "a destructive payment-field rename loses compatibility or deduplication"),
    "BF-106": ("capture query behavior before changing SQL", "compatibility tests for legacy callers", "the existing query shape with measurements", "a legacy caller depends on a brittle result shape", "caller coverage, latency baseline, and error parity", "SQL is optimized or removed without evidence from its consumers"),
    "BF-107": ("persist explicit workflow transitions", "reconcile in-flight steps before resume", "the current state machine with durable checkpoints", "a worker restarts after an external step may have committed", "state recovery, duplicate effects, and operator visibility", "workflow state is inferred from logs and a side effect is replayed blindly"),
    "BF-108": ("route one capability through an anti-corruption seam", "measure parity before cutover", "the legacy monolith kept behind a narrow seam", "legacy and replacement paths disagree during migration", "parity, ownership, and cutover rollback", "a big-bang rewrite creates an unverified compatibility break"),
    "FD-101": ("idempotent delivery key with a status record", "outbox/inbox boundary for retry", "one send attempt with durable outcome state", "the worker crashes after the email provider accepts the message", "provider deduplication, retry ownership, and outcome lookup", "the email side effect is repeated after a post-commit crash"),
    "FD-102": ("query remote outcome before retry", "pending state with reconciliation", "one remote call with durable request state", "the remote system commits before the client timeout", "timeout classification, idempotency, and reconciliation", "an ambiguous remote timeout is treated as a failed side effect"),
    "FD-103": ("inbox claim keyed by event ID", "atomic fulfillment transition", "a single delivery handler with durable deduplication", "two webhook deliveries race for the same event", "signature verification, atomic claim, and duplicate effect", "concurrent duplicate deliveries can create two fulfillments"),
    "FD-104": ("one deadline-aware retry budget", "load shedding after dependency failure", "fail fast after the first bounded attempt", "client, API, and worker retries overlap during an outage", "retry amplification, dependency recovery, and backpressure", "independent retry layers multiply load during the outage"),
    "FD-105": ("single-flight refresh with bounded stale serving", "jittered expiry and origin protection", "one origin read after cache expiry", "many requests miss the cache at once", "origin load, freshness bound, and rebuild recovery", "cache expiry causes an unbounded refresh stampede"),
    "FD-106": ("quarantine poison events without blocking healthy work", "preserve ordering after an operator decision", "a consumer that retries only recoverable messages", "an invalid event sits before a valid event in the partition", "partition progress, quarantine, and replay authorization", "a poison message blocks later work or is silently skipped"),
    "FD-107": ("checkpointed idempotent backfill", "parity gate before contraction", "an additive migration that can pause safely", "the backfill stops while old and new workers coexist", "checkpoint integrity, resume behavior, and parity", "the migration contracts before an interrupted backfill is verified"),
    "FD-108": ("transactional outbox", "relay with duplicate-safe consumption", "one database transaction without publication", "the database commit and broker publish fail in different orders", "publication durability, relay recovery, and consumer deduplication", "a direct dual write loses or duplicates a publication"),
    "SEC-101": ("tenant-scoped authorization at object lookup", "deny-by-default policy tests", "the current handler with an explicit tenant predicate", "a caller requests another tenant's object identifier", "authorization boundary, tenant context, and denial audit", "object access is authorized by identifier without tenant scope"),
    "SEC-102": ("signature verification with a replay window", "event-ID deduplication", "a verified webhook handler with one durable claim", "an attacker replays a valid webhook after the first delivery", "signature policy, replay window, and duplicate effect", "a valid signature is accepted without freshness or deduplication"),
    "SEC-103": ("egress proxy with a destination allowlist", "bounded response and redirect policy", "a deny-by-default URL fetch boundary", "a submitted URL resolves to a protected network address", "destination validation, redirect handling, and resource budget", "arbitrary URL fetching can reach protected network resources"),
    "SEC-104": ("server-side tenant authorization with a job budget", "redacted export plus audit trail", "a bounded export of the caller's authorized records", "a privileged export request spans an unauthorized tenant", "authorization, export scope, and resource fairness", "the client selects export scope without server-side authorization"),
    "SEC-105": ("identity plus action/resource authorization", "policy evaluation at the service boundary", "network reachability with explicit authorization", "an internal caller reaches an endpoint without the required action", "identity claims, policy enforcement, and denial telemetry", "network location is treated as sufficient authorization"),
    "SEC-106": ("structured redaction at emission", "secret scanning in tests and CI", "safe structured logs without raw request bodies", "an exception or debug field contains a credential", "redaction coverage, log access, and false-negative detection", "secrets are exposed because redaction happens only downstream"),
    "SEC-107": ("pagination with a per-tenant resource budget", "cancelable asynchronous report job", "a bounded synchronous query with measured limits", "one tenant submits a query that exhausts shared capacity", "query cost, fairness, and cancellation recovery", "an unbounded report query can monopolize shared resources"),
    "SEC-108": ("tenant-scoped cache key and migration", "invalidation by tenant and schema version", "the source-of-truth query without a shared cache", "a cache entry created for one tenant is read by another", "key migration, tenant isolation, and invalidation", "a user-only cache key permits cross-tenant data exposure"),
    "OP-101": ("correlated state machine with unknown-outcome handling", "operator reconciliation before replay", "an operator runbook over durable workflow state", "an external step may have committed while the workflow is pending", "diagnosis, outcome reconciliation, and safe repair", "a pending side effect is retried without classifying its outcome"),
    "OP-102": ("quarantine with approval and audit trail", "idempotent replay tooling", "manual inspection before requeue", "a malformed event is replayed with an unsafe transformation", "approval authority, replay idempotency, and quarantine visibility", "operators can requeue poison events without authorization or audit"),
    "OP-103": ("checkpoint integrity verification", "idempotent resume with a parity gate", "the last verified migration checkpoint", "a backfill resumes from a corrupted or stale checkpoint", "checkpoint validation, parity evidence, and contraction safety", "migration resumes from an unverified offset and corrupts data"),
    "OP-104": ("separate report pool with load shedding", "visible deferred work with retry-after", "the checkout pool protected by admission control", "report load saturates resources needed by checkout", "shed threshold, fairness, and recovery queue", "optional reports consume checkout capacity without a shed boundary"),
    "OP-105": ("freeze rollout and compare error/data evidence", "rollback only after compatibility checks", "the last known-compatible version", "a recovery decision is made while error cause and data state are unknown", "root-cause evidence, mixed-version safety, and rollback scope", "rollback or roll-forward is chosen from an unclassified failure"),
    "OP-106": ("privacy-safe correlation fields", "burn-rate alert with trace sampling", "the existing logs enriched with actionable identifiers", "a slow webhook cannot be connected to its tenant-safe outcome", "correlation coverage, privacy, and alert actionability", "latency alerts lack the fields needed to diagnose or recover an event"),
    "OP-107": ("idempotent event claim with a replay window", "operator approval and convergence checks", "one live consumer with durable event state", "replay and live delivery process the same shipment concurrently", "replay authorization, ordering, and duplicate effect", "live and replay paths can apply the same shipment effect twice"),
    "OP-108": ("bounded fallback contract with a product threshold", "runbook separating transient and permanent errors", "fail-closed pricing when the freshness contract is unknown", "pricing is slow while checkout is deciding whether stale data is safe", "staleness threshold, retry budget, and operator recovery", "an unbounded stale price or retry loop can affect a financial commit"),
}


REJECTIONS = {
    "SU-101": ("blind retry after timeout", "client-only deduplication"),
    "SU-102": ("shared unbounded worker pool", "arrival order as fault isolation"),
    "SU-103": ("cache as catalog authority", "unbounded stale cache"),
    "SU-104": ("replace the address shape in one release", "retire old clients without telemetry"),
    "SR-101": ("ten-service split for professionalism", "network call per local module"),
    "SR-102": ("projection pipeline without a lag need", "separate command/query stores by default"),
    "SR-103": ("event sourcing for actor metadata", "rebuild projections without a temporal requirement"),
    "SR-104": ("Kafka for same-process notification", "eventual consistency without a consumer"),
    "NE-101": ("split by team aspiration", "boundary before data ownership"),
    "NE-102": ("CQRS before a freshness contract", "implicit stale financial views"),
    "NE-103": ("partition before tenant ownership", "shared cache key without tenant scope"),
    "NE-104": ("shard from projected scale", "cross-shard transactions by default"),
    "NE-105": ("extract the shared table immediately", "duplicate mutable customer truth"),
    "NE-106": ("choose Saga before the recovery target", "retry every workflow step until success"),
    "NE-107": ("eventual search for stock authority", "CQRS without an inventory invariant"),
    "NE-108": ("assume exactly-once from the broker", "retry side effects without deduplication"),
    "BF-101": ("breaking payload rewrite", "version flag without a retirement plan"),
    "BF-102": ("split services over shared writes", "duplicate schema without an owner"),
    "BF-103": ("rewrite ORM queries wholesale", "performance claim without a baseline"),
    "BF-104": ("drop old event versions", "assume all producers deploy together"),
    "BF-105": ("rename the payment field destructively", "backfill without duplicate protection"),
    "BF-106": ("optimize SQL by intuition", "remove a legacy shape without caller evidence"),
    "BF-107": ("restart the workflow from its first step", "infer state from logs only"),
    "BF-108": ("big-bang rewrite", "share mutable internals indefinitely"),
    "FD-101": ("send then mark complete", "retry email without provider deduplication"),
    "FD-102": ("treat timeout as failure", "retry the non-idempotent remote call"),
    "FD-103": ("process every webhook delivery", "dedupe only in process memory"),
    "FD-104": ("retry at every layer", "retry until the dependency recovers"),
    "FD-105": ("expire every key at once", "refresh without origin protection"),
    "FD-106": ("block the partition forever", "skip the poison event silently"),
    "FD-107": ("restart the backfill from zero", "drop the old column during mixed versions"),
    "FD-108": ("direct dual write", "publish before the database commit"),
    "SEC-101": ("authorize by object ID alone", "trust the client tenant header"),
    "SEC-102": ("accept unsigned webhooks", "verify the signature after the side effect"),
    "SEC-103": ("fetch arbitrary URLs directly", "validate only the URL scheme"),
    "SEC-104": ("let the client choose tenant scope", "run an unbounded synchronous export"),
    "SEC-105": ("treat network reachability as authorization", "trust an internal caller role"),
    "SEC-106": ("log the raw request for debugging", "redact only in a downstream dashboard"),
    "SEC-107": ("run an unbounded report query", "use one global timeout as fairness control"),
    "SEC-108": ("reuse a user-only cache key", "flush globally instead of isolating tenants"),
    "OP-101": ("poll forever", "retry the pending side effect blindly"),
    "OP-102": ("requeue malformed events indefinitely", "bypass approval and audit"),
    "OP-103": ("resume from a guessed offset", "contract before parity evidence"),
    "OP-104": ("let reports consume the checkout pool", "hide rejected work behind retries"),
    "OP-105": ("rollback on error rate alone", "roll forward while root cause is unknown"),
    "OP-106": ("log full payloads to debug latency", "alert on averages only"),
    "OP-107": ("replay every event concurrently", "disable deduplication during replay"),
    "OP-108": ("serve indefinitely stale pricing", "retry price calls without a deadline"),
}


def transform(rows: list[dict]) -> list[dict]:
    seen = set()
    for scenario in rows:
        identifier = str(scenario.get("id", ""))
        if not identifier or not identifier.split("-")[-1].isdigit() or int(identifier.split("-")[-1]) < 101:
            continue
        if identifier not in PROFILES:
            raise ValueError(f"missing tailoring profile for {identifier}")
        seen.add(identifier)
        preferred_a, preferred_b, baseline, failure, measure, diagnostic = PROFILES[identifier]
        rejected_a, rejected_b = REJECTIONS[identifier]
        decision = scenario["expected_decision"]
        decision["preferred"] = [preferred_a, preferred_b]
        decision["rejected"] = [rejected_a, rejected_b]
        decision["evidence_requirements"] = [
            f"resolve this unknown before selection: {scenario['unknowns'][0]}",
            f"inject {failure} and record detection and recovery behavior",
            f"measure {measure} before accepting the change",
        ]
        invariant = scenario["invariants"][0]
        unknown = scenario["unknowns"][0]
        scenario["required_signals"] = [
            f"state the invariant for {scenario['title']}: {invariant}",
            f"preserve the unknown and its decision impact: {unknown}",
            f"compare {preferred_a} with {baseline}",
            f"define the failure boundary: {failure}; measure {measure}",
        ]
        mutations = scenario.get("known_bad_mutations", [])
        if len(mutations) != 1:
            raise ValueError(f"expected one mutation for {identifier}")
        mutations[0]["diagnostic"] = diagnostic
    expected = {key for key in PROFILES if int(key.split("-")[-1]) >= 101}
    if seen != expected:
        raise ValueError(f"tailoring coverage mismatch: missing={sorted(expected - seen)} extra={sorted(seen - expected)}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="write to this path; defaults to scenarios.json")
    parser.add_argument("--check", action="store_true", help="verify all generated IDs have profiles without writing")
    args = parser.parse_args()
    rows = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    transformed = transform(rows)
    if not args.check:
        destination = (ROOT / args.output) if args.output and not args.output.is_absolute() else (args.output or SCENARIOS)
        destination.write_text(json.dumps(transformed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "profile_count": len(PROFILES), "wrote": not args.check}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
