# Pattern decision matrix

Use this reference for non-trivial cross-family choices. It turns a pattern
name into a bounded decision: the problem, forces, invariants, candidates,
rejected alternatives, complexity cost, failure semantics, and evidence that
would change the conclusion. It is a companion to the routing rules in
[`pattern-index.md`](pattern-index.md) and the handoff ownership in
[`composition-contracts.md`](composition-contracts.md).

## Minimum-sufficient decision rule

Choose the least complex architecture that satisfies the observed requirements
and foreseeable constraints. A pattern earns its complexity only when it
protects an invariant, resolves a measured force, or creates an independently
valuable boundary. “Modern,” “clean,” “scalable,” or “best practice” are not
forces until they are tied to a workload, ownership, failure, compliance, or
compatibility need.

The decision sequence is:

1. Describe the current system and the user-visible problem, including
   brownfield contracts and deployment/version skew.
2. State invariants and boundaries before naming patterns.
3. Separate observed evidence from `INFERRED`, `PROPOSED`, and `UNKNOWN`
   assumptions.
4. Generate a small candidate set, including the simplest viable design.
5. Reject candidates with a concrete mismatch, not a preference.
6. Record complexity, security, operations, migration, and verification cost.
7. Select the smallest candidate that meets the requirements and define the
   evidence that could falsify it.
8. Revisit the choice when the workload, ownership, threat, or contract changes.

## Reusable decision-record schema

Use the following fields for a decision record. The fields align with the
package handoff contract; values may be scalar, list, map, or an explicit
`UNKNOWN`. A record is complete only when each required field has either an
evidence-backed value or a named unresolved risk.

| Field | Required meaning |
| --- | --- |
| `decision_id` | Stable local identifier and revision date or build identity |
| `problem` | User/system outcome to improve, including what is out of scope |
| `constraints` | Existing contracts, data, deployment, team, regulatory, and compatibility limits |
| `forces` | Consistency, latency, throughput, ownership, failure isolation, cost, operability, security, or other forces with evidence status |
| `invariants` | Conditions that must remain true under success, failure, duplicate, race, and migration |
| `candidates` | Small set of plausible patterns, including the minimum baseline |
| `rejected_patterns` | Each rejected candidate and the evidence or force that rules it out |
| `selected_patterns` | Chosen patterns and the boundary each owns; avoid unexplained bundles |
| `complexity_budget` | Implementation, operational, cognitive, migration, runtime, and testing costs plus the benefit purchased |
| `boundaries` | Transaction, trust, consistency, retry/timeout, data, and deployment boundaries |
| `failure_semantics` | Partial commit, duplicate, timeout, ordering, backpressure, recovery, and unknown-outcome behavior |
| `security_constraints` | Authn/authz, object/property/tenant checks, privilege, input, secret, sensitive-data, SSRF, and abuse controls |
| `observability_requirements` | Context, logs, metrics, traces, SLIs/SLOs, alerts, capacity signals, and recovery evidence |
| `migration_and_compatibility` | Expand/contract, version skew, backfill, replay, rollback/repair, and deprecation plan |
| `verification_requirements` | Invariant tests, adversarial cases, harness checks, runtime evidence, and freshness boundary |
| `unresolved_risks` | Explicit unknowns, owner, impact, and decision that would change the design |
| `handoff` | Implementation, security, and factual-verification recipients with claims and evidence requests |

Do not use an empty field to imply safety. `UNKNOWN: no current measurement`
is more honest and more actionable than a guessed latency or a blank security
constraint. A lightweight record is enough for a small choice; large ceremony
is not a substitute for reasoning.

## Comparing candidates

Scorecards are aids, not automatic architecture selectors. Compare candidates
against the same forces and mark the evidence status of each judgment.

### Candidate-row schema

Every important candidate should be comparable using the following reusable
fields. The names are intentionally explicit so a review, validator, or agent
can detect missing negative guidance instead of inferring it from a pattern
name.

| Field | What the row must explain |
| --- | --- |
| `pattern` | The candidate and the boundary it would own |
| `problem solved` | The concrete failure, cost, or capability this candidate addresses |
| `context` | System state, workload, ownership, and deployment conditions in which it is considered |
| `forces` | Requirements and trade-offs that push toward or away from the candidate |
| `when to use` | Observable conditions that make the candidate proportionate |
| `when NOT to use` | Conditions under which the candidate adds cost without solving the stated problem |
| `benefits` | Invariants, failure isolation, compatibility, or operational gains purchased |
| `costs` | Implementation, runtime, cognitive, operational, migration, and testing burden |
| `failure modes` | Duplicate, race, stale, timeout, partial-commit, overload, or recovery hazards |
| `security implications` | Trust, authn/authz, object/property/tenant, privilege, secret, input, and data effects |
| `operational implications` | Deployment, capacity, alerting, repair, rollback, and ownership changes |
| `testing implications` | Invariant, API, concurrency, replay, migration, adversarial, and harness evidence |
| `migration implications` | Compatibility window, backfill, dual-read/write risk, cutover, resume, and deprecation behavior |
| `observability implications` | Context, metrics, traces, SLIs/SLOs, alerts, and recovery signals |
| `alternatives` | The simpler baseline and other credible choices, with rejection reasons |
| `evidence required` | Exact measurement, test, inspection, or specialist review needed before selection |

The selected row must be accompanied by a rejection record for the strongest
simpler alternative. “When NOT to use” is a first-class decision field, not a
generic warning at the end of a catalog.

| Dimension | Questions to ask | Minimum evidence |
| --- | --- | --- |
| Correctness and invariants | Which state transitions and side effects are protected? | Transaction/concurrency/failure tests at the owner boundary |
| Consistency | What may be stale, reordered, duplicated, or conflicting, and for how long? | Explicit read/write model and conflict/replay evidence |
| Failure containment | Which dependency or process failures remain local? | Timeout, retry, backpressure, crash, and recovery exercise |
| Security | Where are trust, authn/authz, object/property/tenant, secret, and egress boundaries? | Negative authorization, injection/SSRF, privilege, and redaction evidence |
| Operability | How are failure, saturation, stuck work, and data repair detected? | Correlated signals, SLO/alert, dashboard, and runbook test |
| Performance and capacity | What measured latency, throughput, fan-out, query, queue, and resource budget is met? | Representative baseline/load or a clearly stated `UNKNOWN` |
| Migration and compatibility | Can old/new versions and interrupted changes coexist? | Contract, migration, replay, and resume tests |
| Cognitive and team cost | Can owners understand, change, and debug the path? | Dependency map, ownership, review surface, and support burden |
| Testing cost | Can the key failure modes be deterministically reproduced? | Harness controls, known-bad validation, and evidence ledger |

Reject a candidate when it meets a speculative force by adding material cost
while the minimum baseline already satisfies the observed invariants. Record
what new evidence would reopen the candidate.

## Complexity budget

Maintain a qualitative ledger for each candidate. Use `0` for no material
increment, `1` for low and local, `2` for material but bounded, and `3` for
high or system-wide cost. The numbers organize a discussion; they are not a
license to trade away a safety invariant.

| Cost dimension | 0–1 means | 2 means | 3 means |
| --- | --- | --- | --- |
| Implementation | Local code or one clear boundary | Multiple components/contracts | New distributed protocol or major platform |
| Operational | Existing deployment and signals suffice | New runbooks, capacity, or recovery paths | New fleet, broker, data plane, or 24/7 burden |
| Cognitive | Familiar local behavior | New consistency/failure model | Several interacting models and ownership seams |
| Migration | Additive or reversible change | Compatibility window/backfill | Dual systems, replay, or irreversible cutover |
| Runtime | No new hop/state machine | Bounded queue/cache/projection | Distributed coordination or long workflow |
| Testing | Existing test levels cover it | New integration/failure/concurrency harness | Repeated environment, load, replay, or operational proof |

For each nonzero cost, state the benefit and the evidence that justifies it.
The chosen design should fit the team's ability to operate it, not merely its
ability to implement it once. If the design has a high cost in several
dimensions and no measured force, reject it or reduce its scope.

## Gates for high-complexity patterns

### Microservices

Microservices are justified only when a real boundary needs independent
deployment, independent scaling, fault isolation, different reliability or
regulatory treatment, strong bounded context, team ownership, or technology
isolation with a concrete benefit. One qualifying force is necessary, not
sufficient: data ownership, API/event contracts, service identity, SLOs,
observability, migration, and failure recovery must also be explicit.

Before selecting microservices, answer:

- Which service owns each mutable data set and invariant?
- Which deployment and version combinations must coexist?
- What happens when a call times out after the remote side commits?
- What is synchronous versus durable asynchronous work?
- How are authz, tenant boundaries, retries, queue backpressure, and secrets
  enforced per service?
- How are traces, queue age, SLOs, releases, and data repair operated?
- What evidence proves independent scaling, release, or fault isolation is
  valuable in this workload?

Reject microservices for a small application when the same team releases all
components together, the services share a database, the proposed benefit is
only future scale, or the main effect is more network calls. Prefer a modular
monolith with explicit modules and extraction seams, then revisit after
measurements or ownership changes. This is a rejection of the current gate,
not a claim that microservices are universally wrong.

### CQRS

CQRS requires an asymmetric read/write problem: dramatically different models,
read scaling pressure, complex domain commands, multiple specialized
projections, asynchronous workflows, or a valuable separation of consistency
models. A separate command/query path adds projection lag, rebuild, duplicate,
schema, and operational costs.

Reject CQRS for ordinary CRUD when read and write shapes are similar, one
transactional model satisfies the SLO, and no measured read/write or
consistency force exists. Start with focused queries, indexes, and a clear
transaction boundary. If later evidence supports CQRS, introduce one
rebuildable read model behind a compatibility contract and test lag, stale
reads, replay, authorization, and recovery.

### Event sourcing

Event sourcing requires event history to be a core domain capability, such as
immutable audit history, temporal reconstruction, an event-native domain, or
state evolution that materially benefits from replay. It is not a default
upgrade from CRUD.

The record must address event schema evolution, migration and upcasting,
projection rebuilds, storage growth, replay semantics, privacy and deletion,
concurrency, operational debugging, and how a wrong event is corrected. Reject
event sourcing for a simple CRUD service whose real requirement is only an
audit log, analytics feed, or asynchronous notification; an append-only audit
record or transactional outbox may satisfy those needs with less runtime and
testing cost.

## Reusable rejection examples

| Situation | Tempting choice | Why it is rejected now | Minimum sufficient choice |
| --- | --- | --- | --- |
| Small CRUD product, one team, one database | Microservices | No independent deployment/scaling or fault-isolation evidence; adds network and data failure | Modular monolith with module ownership and contract tests |
| CRUD reads and writes have the same model | CQRS | No asymmetric load, projection, or consistency force | Transactional model with measured queries and indexes |
| Need an audit trail for a few changes | Event sourcing | Audit is a derived requirement; replay/privacy/storage costs are disproportionate | Append-only audit records plus an outbox if integration is needed |
| Two local modules need decoupling | Broker and remote calls | A process boundary creates failure and operational cost without independent lifecycle | In-process module interface and explicit transaction ownership |
| Non-idempotent payment call occasionally times out | Generic retry | Retry may duplicate the payment and amplify the outage | Provider idempotency key, bounded retry owner, reconciliation state |
| Read endpoint is slow once per day | Distributed cache everywhere | No baseline, invalidation/source-of-truth plan, or measured cache need | Profile query plan and add the smallest index/query fix |
| Service wants to publish after a database write | Direct dual write | Commit and publish can diverge; no recovery evidence | Local transaction plus transactional outbox and idempotent consumer |
| One shared utility package contains domain models | Giant common package | Consumers become release-coupled and ownership is ambiguous | Narrow stable contract package or local ownership |

The examples are defaults for the stated conditions. New evidence can change
the answer, but it must update the forces, costs, and verification plan rather
than merely rename the pattern.

## Production readiness scorecard

Use this as a coverage map, not a weighted excuse to average away a required
failure. Each row is `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, or `UNKNOWN` with a
current artifact identity and a concrete evidence reference. A non-applicable
row needs a reason.

| Dimension | Readiness question | Minimum evidence shape |
|---|---|---|
| Correctness | Do legal flows and errors match the contract? | Public-boundary success and negative cases |
| Data integrity | Are invariants preserved across commit, crash and retry? | Constraint/transaction/failure evidence |
| Concurrency safety | Are races, lost updates and duplicate effects controlled? | Concurrent requests/messages plus durable-state inspection |
| API stability | Can old and new consumers coexist as promised? | Contract/version-skew compatibility checks |
| Security | Are trust, authn/authz, tenant and sensitive-data controls enforced? | Negative authorization, input/egress and redaction evidence |
| Failure handling | Are dependency, process and partial failures contained? | Timeout, crash, malformed dependency and recovery tests |
| Retry safety | Are retries bounded, non-amplifying and replay-safe? | Attempt budget/backoff/jitter and outage exercise |
| Idempotency | Do repeated requests/events produce the declared effect? | Same/different payload and concurrent replay tests |
| Observability | Can an operator locate and classify failure? | Correlated logs, metrics, traces, SLI and alert evidence |
| Operability | Can the system deploy, roll back/forward, repair and drain? | Runbook/recovery exercise and ownership evidence |
| Scalability | Does the design preserve the required capacity boundary? | Representative workload, saturation and recovery evidence |
| Performance | Does measured latency/resource use meet the requirement? | Query/profile/load result with distribution and conditions |
| Migration safety | Can interrupted and mixed-version changes recover safely? | Expand/contract, checkpoint, resume and compatibility tests |
| Testability | Can important claims be deterministically disproved? | Known-good/known-bad harness and failure injection |
| Simplicity | Is each added abstraction paid for by a real force? | Rejected baseline, complexity budget and ownership review |

## Failure-mode matrix

For every significant flow, record the rows below. “Handled by the framework”
is not a value; name the actual control and its evidence.

| Component | Failure | Detection | Containment | Recovery | Data integrity impact | User-visible impact | Observability evidence |
|---|---|---|---|---|---|---|---|
| owner/boundary | crash, timeout, duplicate, race, malformed input, overload, or version skew | signal and owner | timeout, transaction, isolation, limit or load shed | retry, replay, compensation, repair, resume or operator action | lost, duplicated, stale, conflicting, or preserved state | error, pending, conflict, degraded result, or transparent recovery | log/metric/trace/event/alert and freshness |

The matrix must be specific enough to drive a test and a recovery procedure.
Use [`testing-patterns.md`](testing-patterns.md) for pattern-specific oracles
and [`observability-patterns.md`](observability-patterns.md) for signal design.

## Evidence and handoff

The final record should link each material selection to an evidence request:
transaction and concurrency tests for atomicity, duplicate/replay tests for
idempotency, mixed-version and migration tests for compatibility, security
negative tests for trust boundaries, and operational/load evidence for
capacity. Use [`testing-patterns.md`](testing-patterns.md) and
[`observability-patterns.md`](observability-patterns.md) for those evidence
shapes.

When the choice changes implementation, schema, deployment, authentication,
authorization, tenant isolation, secrets, sensitive data, external fetching,
webhooks, payments, or service-to-service trust, hand off the applicable
claims and evidence requests to implementation engineering and/or
`security-engineering-vNext`. Hand off current-artifact and runtime claims to
`verification-loop-vNext`. The handoff is a request, not proof that those
reviews ran; preserve that distinction in the record.

## Decision stop conditions

Do not select a pattern when the problem, owner, invariant, or required
evidence is unknown and the missing fact could materially change the design.
Perform safe discovery and measurement first. If progress must continue, mark
the selection `PROPOSED`, bound the reversible experiment, and state the
decision that will confirm or reject it. A decision is complete only when the
minimum sufficient architecture, rejected alternatives, complexity budget,
security/operations implications, migration path, and verification evidence
are all visible to the next owner.
