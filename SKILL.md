---
name: backend-patterns
description: Framework-independent backend architecture judgment for designing or refactoring APIs, service/module boundaries, domain models, data access, transactions, messaging, concurrency, consistency, resilience, caching, migrations, and operational behavior. Use when a backend decision crosses a runtime, data, contract, failure, or ownership boundary; do not use for trivial local edits, documentation-only work, visual/frontend work, or final security/release approval.
---

# Backend patterns

Act as a principal backend architecture reviewer, not a pattern catalog. The
objective is the **minimum sufficient design**: solve the actual problem while
preserving correctness, maintainability, evolvability, simplicity, security,
reliability, observability, performance where justified, compatibility,
testability, operability, and failure containment.

A pattern is never a goal. A sophisticated pattern must earn its complexity by
solving a demonstrated requirement, ownership problem, failure boundary, or
measured constraint.

## Activate and decline

Activate when the task materially involves one or more of:

- backend architecture, module/service boundaries, dependency direction, or a
  monolith decomposition;
- API/resource/RPC/webhook contracts, compatibility, pagination, errors, or
  idempotency;
- domain invariants, transactions, persistence, queries, migrations, or data
  ownership;
- asynchronous workflows, messaging, retries, concurrency, consistency,
  caching, performance, overload, or recovery;
- trust boundaries, authorization/tenancy, sensitive data, or backend
  observability and operability.

Do not activate for a variable rename, typo, README-only edit, isolated
formatting/configuration change with no backend boundary, frontend/visual work,
or final security certification, release approval, or system-wide product
architecture authority. A technology name alone is not a trigger. For a small
backend change, keep this workflow proportional: inspect the boundary, choose
the smallest applicable reference, make one decision record if needed, and run
one focused check.

## Non-negotiable reasoning rules

1. Inspect the real connected path before naming a pattern. A folder named
   `service`, an ORM, a diagram, or a framework default is not evidence of the
   runtime boundary.
2. Label facts as `CURRENT`, `PROPOSED`, or `UNKNOWN`. Never turn a missing
   schema, caller, requirement, dependency, or operational fact into a guess.
3. State the invariant first. Examples: “a payment is captured at most once”,
   “a tenant cannot read another tenant's object”, or “a committed event is not
   permanently lost”. Derive boundaries and tests from it.
4. Make transaction, trust, consistency, compatibility, timeout, retry,
   cancellation, and observability boundaries explicit. Local-process
   assumptions do not cross a network boundary.
5. Prefer the simplest architecture that satisfies the requirements and
   foreseeable constraints. Reject ceremony, abstractions, brokers, queues,
   caches, microservices, CQRS, and event sourcing without a demonstrated need.
6. Enforce authorization with a server-side **default deny** policy over actor,
   action, resource, and tenant; a client-supplied identifier is not proof of
   access. Treat duplicate delivery, partial failure, stale reads, reordering,
   mixed versions, clock uncertainty, and concurrent callers as normal cases
   when the boundary can experience them.
7. No claim is complete without evidence appropriate to the pattern. A compile,
   happy-path unit test, static keyword match, or explanation is not runtime,
   persistence, security, concurrency, migration, or recovery proof.

## Required execution loop

Follow this sequence. Stop early only when a stage is genuinely inapplicable
and record why.

```text
DISCOVER
  → CLASSIFY
  → MODEL CONSTRAINTS AND TRUST
  → IDENTIFY FORCES AND INVARIANTS
  → GENERATE CANDIDATES (include the simpler baseline)
  → ELIMINATE UNSUITABLE PATTERNS
  → SELECT THE MINIMUM SUFFICIENT DESIGN
  → DEFINE CONTRACTS, FAILURE AND RECOVERY
  → IMPLEMENT / GUIDE
  → VERIFY THE PUBLIC OR PERSISTENT BOUNDARY
  → CHALLENGE ADVERSARIALLY
  → REPORT DECISION, EVIDENCE, LIMITATIONS AND NEXT ACTION
```

### 1. Discover the actual system

Map only what can change the decision: language/runtime/framework, entry point,
transport, persistence and constraints, deployment topology, messaging/cache,
concurrency model, callers/consumers, public contracts, auth/tenant context,
configuration, migrations, tests, operational owner, and recovery path. Follow
one representative request/job through routing, validation, authorization,
application/domain rules, persistence, external adapters, wiring, and response
or event emission. Preserve the existing fence until its reason is understood.

### 2. Classify and load selectively

Choose every applicable problem family, but load only the references that fit:
`references/pattern-index.md` is the routing contract. Typical combinations
are API + data + transaction + idempotency for a write; messaging + resilience
+ distributed systems for a worker; security + observability for a privileged
boundary; migration + testing for a compatibility change.

### 3. Model constraints, forces and invariants

Write the forces that pull in different directions: consistency, availability,
latency, throughput, data locality, ownership, failure isolation, deployment
independence, team and infrastructure maturity, cost, cognitive/operational/
testing/migration complexity, compatibility, security, and recovery. Separate a
measured requirement from a performance guess. Name the invariants and legal
state transitions before selecting a pattern.

### 4. Generate and eliminate candidates

Always include the current design (if safe), a simpler local alternative, and
only then more elaborate candidates. For each candidate ask:

- What problem does it solve here, and what evidence supports that problem?
- Which forces does it improve, and which costs does it add?
- Who owns the invariant, data, error translation, recovery and operation?
- What happens after a crash, timeout, retry, duplicate, reorder, race,
  cancellation, partial commit, dependency outage, or mixed deployment?
- How are authorization, sensitive data, auditability and resource abuse
  handled? How can the design be tested at the real boundary?
- What is the migration, rollback/roll-forward and last safe point?

Reject a candidate when its driver is a slogan, its failure semantics are
unknown, its complexity budget is unjustified, or a smaller design satisfies
the frozen requirements. See [`decision-matrix.md`](references/decision-matrix.md)
for the complete comparison schema and hard gates.

### 5. Select and define the boundary contract

The selected design must name:

- caller/producer, consumer, trust level, actor, resource, action and tenant;
- input limits and validation; success shape; stable redacted errors;
- data owner, constraints/indexes, transaction/isolation boundary, and
  allowed partial state;
- consistency model, staleness tolerance, conflict policy, ordering and
  idempotency/deduplication scope;
- timeout/deadline, retry budget/backoff/jitter, cancellation, backpressure,
  circuit/bulkhead/load-shed behavior and recovery/repair;
- logs/metrics/traces, correlation/causation IDs, SLI/SLO/alert and operator
  diagnosis;
- compatibility window, rollout, migration/backfill, rollback or roll-forward;
- evidence that can distinguish a known-good artifact from a known-bad one.

If the operation is a conditional update, prefer an atomic constraint or
**compare-and-swap** at the datastore boundary over a check-then-act pre-check.
If an external effect is required, define whether it occurs **after commit**,
through an outbox, or through an explicit pending/reconciliation state.

## High-risk decision gates

Use these defaults unless evidence establishes a stronger need:

- **Microservices:** require independent deployment, independent scaling,
  fault isolation, materially different reliability/regulatory needs, strong
  bounded-context ownership, or technology isolation with real benefit. If not,
  prefer a modular monolith or a well-owned module.
- **CQRS:** require asymmetric read/write models, read scaling pressure,
  specialized projections, complex commands, or intentionally different
  consistency models. A separate query class is not CQRS by itself.
- **Event sourcing:** require immutable audit/temporal reconstruction or an
  event-native domain. Before selecting, address schema evolution, replay,
  projection rebuilds, growth, privacy/deletion, and operational debugging.
- **Repositories/ports/factories:** add them only when they isolate a volatile
  dependency, protect an invariant, enable a real test/variation, or clarify
  ownership. Wrapping an ORM one-for-one is not abstraction value.
- **Retries:** first prove safe replay or an idempotency/deduplication boundary;
  then set deadline, attempt budget, exponential backoff and jitter. Avoid
  stacked retries and calculate amplification under outage.
- **Caches:** name the source of truth, key/scope, invalidation, staleness
  tolerance and stampede control. A cache is never the only durable source
  unless that is an explicit product decision.
- **Messaging:** assume at-least-once behavior, duplicate delivery,
  reordering, poison messages and broker unavailability. Use outbox/inbox or
  reconciliation when the failure mode requires it; never promise magical
  exactly-once processing.

## Decision record

For a non-trivial choice, emit a concise record and keep it attached to the
implementation/verification handoff:

```text
Problem and desired outcome:
Current evidence and unknowns:
Constraints and forces:
Invariants and legal states:
Candidates (including the simpler baseline):
Rejected candidates and why:
Selected pattern/design:
Complexity budget: implementation / runtime / operations / cognition / tests / migration:
Boundaries: trust / authorization / data / transaction / consistency / retry:
Failure modes, containment and recovery:
Security and sensitive-data impact:
Observability and performance evidence:
Compatibility, rollout and migration:
Verification procedures and expected observations:
Unresolved risks, authority and revalidation trigger:
```

## Negative guidance and anti-rationalization

Do not introduce a broker to decouple two local modules, split services before
ownership or operations justify it, use distributed transactions casually,
retry an unsafe mutation, add a cache without invalidation, emit an event before
the owning transaction commits without explicit semantics, swallow errors,
hide transaction boundaries behind framework magic, fire-and-forget a critical
operation, treat a client identifier as authorization, or defer observability
and recovery until after production readiness. Do not call a design robust,
production-ready, secure, or verified because it “looks correct”.

When a rationalization appears, answer with evidence:

| Rationalization | Required question |
|---|---|
| “It is a small service.” | Which transaction, failure and trust boundaries still exist? |
| “Retries make it reliable.” | Is replay safe, bounded, observable and non-amplifying? |
| “Microservices scale better.” | Which component must scale/deploy/fail independently? |
| “CQRS is cleaner.” | What asymmetric read/write pressure or consistency need exists? |
| “The ORM handles transactions.” | Where exactly does commit/rollback occur under failure? |
| “The broker gives exactly once.” | What duplicate-safe consumer and evidence exist? |
| “A repository is best practice.” | What responsibility or testable seam does it add? |
| “Eventual consistency is fine.” | Which stale states are acceptable, for how long, and to whom? |
| “We will add telemetry later.” | How will a failure be detected, localized and recovered now? |

Use [`anti-patterns.md`](references/anti-patterns.md) for symptoms, causes,
detection, safer alternatives and migration paths.

## Verification contract

Derive tests from invariants and failure modes, not a fixed test pyramid. At a
minimum, choose the applicable cases from [`testing-patterns.md`](references/testing-patterns.md):

| Pattern/claim | Evidence that should be requested |
|---|---|
| transaction/atomicity | rollback and partial-failure injection; durable state |
| idempotency/outbox/inbox | sequential/concurrent duplicates; crash-after-commit; replay |
| concurrency | race, stale version, lock/CAS/constraint conflict |
| retry/resilience | transient/permanent/slow failure, exhaustion, amplification, jitter |
| cache | miss, stale entry, invalidation, unavailable cache, stampede |
| API/auth | compatibility, invalid input, authz matrix, pagination, error contract |
| messaging | duplicate/reorder/poison/dead-letter/broker outage/restart |
| migration | prior data, mixed versions, interruption/restart, checksum, recovery |
| architecture | connected public path, ownership, dependency direction, no duplicate path |

Challenge the design with crashes, timeouts, malformed dependencies, concurrent
requests, old/new versions, 10× traffic, cache loss, malicious identifiers,
retry storms, partial migration, and operator recovery. The failure matrix is
`component → failure → detection → containment → recovery → data/user impact →
observability evidence`.

For each required check, label evidence as executed/current or explicitly
`NOT_RUN`, `BLOCKED`, or `STALE`; a plan, hash, or explanation cannot substitute
for an observation through the **public boundary** or the durable state it
claims to protect.

## Behavioral assurance when evaluating this skill

When changing or auditing `backend-patterns` itself, use the benchmark and
scoring contract under `tests/benchmark/` in addition to package validators.
Keep development, adversarial-repair, and holdout scenarios distinct; record
the scenario, model, prompt/package/corpus/judge fingerprints, loaded
references, approximate context size, response, score, and status. A static
fixture or response oracle proves harness behavior, not consumer-model quality.

Attempt a same-model control/treatment comparison when a consumer-model
adapter is available. If it is not available, record `MODEL_EXECUTION:
BLOCKED` with the missing capability, reason, evidence unavailable, and impact
on the verdict. Never turn `NOT_RUN` into a score, or call a package
`TRIPLE_A_PROVEN` without executed behavioral, holdout, and causal evidence.

Use the explicit result states `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, `STALE`,
and `NOT_APPLICABLE`, and the verdict states `NOT_READY`, `PACKAGE_READY`,
`STATE_OF_THE_ART`, `AAA_CANDIDATE`, `TRIPLE_A_CONDITIONAL`, and
`TRIPLE_A_PROVEN`. Hard safety failures remain failures regardless of an
aggregate score. Prefer the smallest design when equivalent evidence supports
it, and report calibration (`SAFE`, `LIKELY SAFE`, `UNKNOWN`, `HIGH RISK`, or
`BLOCKED`) rather than invented certainty.

For every material routing benchmark, record relevant and irrelevant
references and compute `relevant / loaded` precision. Test metamorphic pairs,
semantic paraphrases, scale changes, framework swaps, and simple-versus-
complex alternatives so the evaluator does not reward verbosity or keywords
alone.

## Composition and exit

Use [`composition-contracts.md`](references/composition-contracts.md) to hand
off an architecture decision to `backend-engineering-vNext`, escalate a
security boundary to `security-engineering-vNext`, and pass explicit claims to
`verification-loop-vNext`. These capabilities are optional and their execution
must be observed; naming a handoff is not proof that it happened.

Before reporting, state selected/rejected patterns, invariants, boundaries,
trade-offs, evidence actually collected, checks not run, limitations,
residual risks, authority status, and one next action. A final architectural
decision is complete only when the required implementation and verification
owners can act on a concrete contract; documentation alone is not assurance.
