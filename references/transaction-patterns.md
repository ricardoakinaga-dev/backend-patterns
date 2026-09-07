# Transaction and workflow integrity patterns

## Purpose

This reference helps an agent choose local ACID transactions, explicit
transaction boundaries, distributed transaction protocols, transactional
outbox/inbox, Saga orchestration or choreography, compensation, retries, and
deduplication. Its central question is how a flow preserves business
invariants when a process, database, broker, or remote participant fails at any
point.

Transactions are not synonymous with database calls. A transaction is a
promise about atomicity, visibility, isolation, durability, or workflow
progress at a stated boundary. Name that boundary and the evidence that
supports the promise.

## When to load

Load this reference when one operation writes multiple records, emits a
message, calls another service, schedules work, sends an external effect, or
must recover after a partial failure. Load it when someone proposes
distributed transactions, outbox/inbox, Saga, compensation, a workflow engine,
or “exactly once” behavior.

Do not load it for a pure read or one local write with no cross-boundary effect,
unless the operation's concurrency or durability semantics are unclear. Pair
it with [data access patterns](data-access-patterns.md) for database behavior,
[consistency patterns](consistency-patterns.md) for visibility and lag,
[concurrency patterns](concurrency-patterns.md) for races, and
[messaging patterns](messaging-patterns.md) when that planned reference is
available.

## Problem and forces

The problem is to define what is atomic, what may be temporarily incomplete,
and how a system reaches a safe terminal state after failure. Identify:

- invariants and the state that must change together;
- local transaction support, isolation, lock duration, and write contention;
- number and trust of participants;
- latency, availability, partition, and independent-deployment requirements;
- external effects that cannot be rolled back, such as email or payment capture;
- duplicate, ordering, timeout, retry, and crash behavior;
- compensation semantics and whether users can observe pending/reversed state;
- delivery, storage, retention, and replay operations;
- migration and version skew;
- security, audit, privacy, and evidence requirements.

Never begin with “how do we make it exactly once?” Begin with:

1. What invariant must hold?
2. Which state is authoritative?
3. Which changes can share one atomic resource transaction?
4. What happens if the process stops after each step but before the next?
5. Which effects can be retried, deduplicated, compensated, or repaired?

### Transaction boundary questions

For every write flow, identify:

- transaction owner and start/commit/rollback points;
- reads whose values must be protected and their isolation requirement;
- local state, outbox/inbox/workflow record, and external effects;
- response semantics before and after commit;
- behavior for timeout with unknown commit outcome;
- retry scope, budget, idempotency key, and duplicate handling;
- recovery trigger, operator action, and terminal state;
- telemetry that distinguishes committed, pending, compensated, failed, and
  unknown.

If an answer depends on a remote database call “being inside” a local
transaction, the boundary is not actually atomic.

## ACID and local transactions

Use one local ACID transaction when all changes that must be atomic are within
one database or transactional resource and the latency/locking cost is
acceptable. Make the properties concrete:

- atomicity: which writes commit or roll back together;
- consistency: which constraints and invariants hold at commit;
- isolation: which concurrent observations and anomalies are allowed;
- durability: what “committed” means after process or node failure.

Select isolation for the anomaly to prevent, not by habit. Consider dirty
reads, non-repeatable reads, phantoms, lost updates, write skew, serialization
failures, deadlocks, and lock duration. Database constraints are final guards
for uniqueness, references, check conditions, and non-negative values when
they can express the invariant.

Keep the transaction short. Do not hold database locks while waiting for a
network response, user action, queue, or unbounded computation. If an
external call must influence the decision, persist a durable pending state and
use a workflow or a reservation with expiry.

The ORM, unit of work, or repository may help manage a local transaction, but
the actual connection, isolation, flush, commit, rollback, and error behavior
must be verified. Link to [data access patterns](data-access-patterns.md).

## Distributed transactions

A distributed transaction spans independently failing resources or services.
Choose deliberately among:

### Two-phase commit or XA-style coordination

Use only when participants support a mature protocol, the consistency need is
strong enough to justify coordinator and blocking risk, the participant set is
small and stable, and operations can handle recovery logs and in-doubt
transactions.

Reject it for arbitrary external APIs, long-running business workflows,
high-partition environments, or teams without operational evidence. It does
not make non-transactional side effects reversible and can amplify resource
contention and availability failures.

### Saga

Use a Saga when a business process spans local transactions and can reach a
valid outcome through forward steps and compensating actions. Each step commits
locally; the process records progress and advances or compensates based on
durable outcomes.

Compensation is a new business operation, not a time machine. A captured
payment may be refunded; an email cannot be unsent; an inventory release may
fail; a published fact may require a correcting fact. Model pending,
compensated, rejected, and manual-review states explicitly.

#### Orchestration

Use orchestration when a coordinator should own sequencing, timeouts,
retries, compensation, policy, and visibility. It is easier to inspect and
change centrally, but the coordinator becomes a critical workflow component
and must be highly available, idempotent, and recoverable.

#### Choreography

Use choreography for a small number of loosely coupled, stable reactions where
event ownership and termination are obvious. It can reduce a central
coordinator but makes global ordering, cycles, progress, and failure diagnosis
harder as participants grow.

Reject choreography when no one owns completion, when events create hidden
synchronous dependencies, or when operators cannot determine the current step.
Reject orchestration when the coordinator merely forwards calls without
durable state or recovery semantics.

### Direct synchronous call

Use a direct call when the caller needs the result now, the dependency is
reliable enough, the operation is bounded, and failure semantics are explicit.
This is often simpler than a Saga for a read or a local validation.

Do not call a remote system inside a local transaction and imply atomicity.
Choose whether the local state is pending before the call, whether the call is
idempotent, and how a timeout is reconciled.

## Transactional outbox

Use a transactional outbox when a local state change and a durable message or
integration command must not diverge. In one local transaction:

1. validate and update the authoritative state;
2. insert an outbox row containing event/command type, version, payload or
   reference, stable ID, aggregate/ordering key, and causation metadata;
3. commit both or neither.

A relay then claims pending rows, publishes them, records attempt/outcome, and
retries or dead-letters safely. The relay can crash after publishing and
before marking sent, so consumers must tolerate duplicate delivery. The
outbox is at-least-once publication machinery, not proof of exactly once.

Define:

- whether payload or a refetch is authoritative after schema evolution;
- ordering scope and behavior under concurrent commits;
- claim lease, visibility timeout, and ownership fencing;
- retry backoff, poison handling, dead-letter, replay, and retention;
- how a permanently invalid event is repaired without blocking all work;
- what happens when the database or broker is unavailable;
- how publication status relates to user-visible pending/completed state.

Do not publish an event before commit when consumers may observe state that
will roll back. Do not put an unbounded payload or secret in the outbox without
retention, privacy, and access controls.

## Inbox and idempotent consumer

Use an inbox when a consumer must apply a message and acknowledge it without
duplicating the local effect. In one local transaction:

1. validate the message identity, version, sender, and authorization;
2. insert a durable inbox record with a unique message or effect key;
3. apply the state change or record the durable next action;
4. commit;
5. acknowledge only after the commit.

A duplicate then becomes a safe no-op or a replay of the recorded result. A
unique key is the integrity guard; an in-memory seen-set is only an
optimization. Define deduplication scope and retention long enough to cover
retries, replay, and business risk. If the same message can legitimately be
replayed for a new effect, separate message identity from business operation
identity.

An inbox does not solve a non-idempotent external side effect performed after
the local commit. Wrap that effect in an outbox/workflow or use a provider
operation key and reconciliation.

## Saga state and failure timeline

For each Saga, list the durable state and the outcome after every step. At
minimum answer:

| Failure point | Required design answer |
| --- | --- |
| Before step N starts | Can the step be retried or skipped? |
| After step N commits, before acknowledgment | How is completion discovered and deduplicated? |
| After the next step is not accepted | Which state is pending, and who retries? |
| A compensation fails | Is there retry, alternate compensation, manual review, or a terminal failure? |
| A later event arrives out of order | Which version or state transition rejects or defers it? |
| The coordinator restarts | Where is progress read, and how are leases fenced? |
| A participant deploys a new version | Which schema and semantics are compatible? |

Persist step identity, attempt, deadline, result, compensation status, and
causation/correlation identifiers. Make the workflow resumable without
requiring an operator to infer progress from logs.

## Retry boundaries and deduplication

Retry only a bounded, transient failure when:

- the operation has a deadline and budget;
- idempotency or a unique effect key is established;
- the error is classified as transient rather than validation, authorization,
  conflict, or permanent poison;
- backoff and jitter avoid synchronized load;
- retrying cannot exceed downstream capacity or business limits;
- the terminal outcome is observable and repairable.

Do not stack independent retries at client, gateway, service, ORM, relay, and
provider layers. One layer should own the budget or coordinate nested budgets.
Never retry a non-idempotent external effect solely because the response timed
out; use provider idempotency or reconciliation.

## When to use

Use this reference when:

- multiple writes must commit together;
- a committed local change must produce a durable message or callback;
- a consumer must survive duplicate or replayed delivery;
- a workflow crosses services, databases, or non-transactional providers;
- a timeout leaves commit status unknown;
- a business process needs pending, compensation, retry, or manual repair.

Choose a local transaction first when it covers the actual invariant. Choose a
workflow protocol only for the part that truly crosses a local atomic
boundary.

## When not to use

Do not:

- use a distributed transaction because a local transaction boundary is
  inconvenient;
- call remote services under database locks or pretend local ACID spans them;
- add an outbox for a non-durable notification that can be safely recomputed
  without a business effect;
- use a Saga when one local transaction or a direct idempotent call suffices;
- use choreography when progress and compensation have no clear owner;
- treat compensation as guaranteed rollback;
- acknowledge a message before durable handling;
- rely on an in-memory dedupe cache for integrity;
- claim exactly-once processing from a broker setting alone;
- retry after unknown commit without an idempotency or reconciliation plan.

## Alternatives and trade-offs

| Need | Smallest credible choice | Stronger choice when justified | Main cost |
| --- | --- | --- | --- |
| Atomic local writes | One short ACID transaction | Serializable/constraint-backed command | Locking and conflict cost |
| Publish committed change | Direct publish when loss is acceptable | Transactional outbox | Relay, lag, dedupe, retention |
| Consume duplicates safely | Natural idempotent update | Inbox/unique effect record | Storage and cleanup |
| Two bounded remote steps | Direct idempotent call | Orchestrated Saga | Durable workflow and compensation |
| Many independent reactions | Stable event choreography | Central orchestrator | Event topology or coordinator |
| Strong multi-resource commit | Local redesign or workflow | Two-phase commit | Blocking, coordinator, recovery |

Use the least powerful protocol that preserves the invariant. If the selected
protocol introduces pending states, lag, compensation, or manual repair, make
those part of the product and operational contract rather than hiding them.

## Failure and integrity implications

This section is mandatory for every material transaction decision. Walk the
flow step by step and answer the question: what happens if failure occurs
after step N but before step N+1?

Include:

- crash before begin, during write, after database commit, and before response;
- connection loss, serialization failure, deadlock, constraint failure, and
  unknown commit;
- broker publish before/after acknowledgment and relay restart;
- duplicate, delayed, reordered, malformed, and permanently failing messages;
- external provider timeout after accepted effect;
- coordinator restart, lease expiry, split ownership, and compensation failure;
- cleanup, replay, reconciliation, and manual repair.

The invariant, authoritative state, user-visible state, and operator evidence
must agree. A system may temporarily be pending or compensating, but it must
not silently report complete when the effect is unknown.

## Security implications

Transactions and workflow messages carry authority. Specify:

- which identity and authorization decision is bound to the command;
- whether an actor can replay, cancel, compensate, or resume another tenant's
  workflow;
- least-privilege database, broker, relay, and provider credentials;
- message authenticity, schema validation, and anti-replay controls;
- secret, personal, payment, and tenant-data retention in transactions,
  outboxes, inboxes, logs, and dead letters;
- audit requirements for capture, refund, permission, export, and manual repair;
- protection against resource exhaustion through unbounded retries, queues, or
  workflow fan-out.

A unique idempotency key is not an authorization check. A consumer must verify
the event's source and permitted effect before applying deduplication or
business logic. Escalate high-impact trust and privilege changes through the
[composition contract](composition-contracts.md).

## Operational implications

Operate the protocol as a state machine, not a collection of background
tasks. Define:

- transaction duration, lock waits, commit latency, and conflict rate;
- outbox/inbox backlog, oldest age, retry attempts, dead letters, and replay;
- Saga step age, compensation rate, manual-review count, and terminal failure;
- provider idempotency/reconciliation status and unknown outcomes;
- relay/consumer leases, fencing, restarts, and capacity;
- safe pause, drain, replay, skip, quarantine, and repair procedures;
- retention and deletion for completed transaction/workflow records.

Alerts should distinguish a transient backlog from a poison message, a stuck
lease, a failed compensation, and a database outage. Recovery must be
idempotent and leave an audit trail.

## Migration and compatibility implications

Introduce integrity patterns incrementally:

1. identify current effects, duplicate risks, and authoritative state;
2. add durable identifiers, constraints, and status columns compatibly;
3. write outbox/inbox records without changing consumer meaning;
4. deploy consumers that handle old and new envelopes and duplicates;
5. backfill or reconcile unfinished effects with bounded checkpoints;
6. switch publication or workflow ownership;
7. remove unsafe direct paths only after telemetry and recovery are proven.

Version event and workflow schemas. Keep old consumers able to ignore additive
fields and keep new consumers able to interpret old messages during the
compatibility window. Never replay historical messages into code that gives
them a different semantic without a version-aware migration strategy.

## Observability implications

Every transaction or workflow instance should be traceable through:

- transaction/operation, message, outbox, inbox, Saga, correlation, and
  causation identifiers;
- participant, step, attempt, lease, deadline, and schema version;
- state before/after, commit/publish/ack outcome, and retry classification;
- latency, queue age, lock wait, backoff, dead-letter, compensation, and
  reconciliation result;
- redacted business key and tenant-safe ownership metadata.

Metrics should make loss, duplication, staleness, and stuck progress visible:
commit failures, unknown outcomes, duplicate suppression, outbox age, inbox
conflicts, event lag, workflow duration, compensation failures, and repair
volume. Do not rely on logs alone for backlog or recovery alerts.

## Testing and verification evidence

Use pattern-specific evidence:

- local transaction rollback, constraint, isolation, deadlock, and serialization
  tests;
- crash-after-commit-before-publish tests for outbox;
- relay restart, duplicate publish, reorder, poison, dead-letter, replay, and
  retention tests;
- inbox duplicate and concurrent-consumer tests with a real unique constraint;
- Saga step timeout, retry exhaustion, compensation success/failure, restart,
  lease/fencing, and manual-recovery tests;
- unknown provider outcome and reconciliation tests;
- mixed-version event/schema and migration interruption tests;
- security tests for forged messages, cross-tenant workflow access, replay,
  secret leakage, and abuse limits;
- observability assertions for every terminal and recoverable state.

Evidence must observe database state, emitted messages, provider calls,
duplicates, user-visible status, and telemetry. A unit test that calls a
mocked broker cannot prove crash recovery or outbox atomicity. State the exact
failure injection, expected invariant, evidence freshness, and limitation in
the handoff described by the [composition contract](composition-contracts.md).

## Decision output

Record the invariant, transaction owner, local atomic scope, distributed
participants, selected protocol, rejected protocols, state machine, failure
after each step, idempotency/deduplication key, compensation and repair plan,
security constraints, operational signals, migration/version strategy, and
executed or planned proof. Cross-link to [consistency patterns](consistency-patterns.md)
for pending/stale semantics and [concurrency patterns](concurrency-patterns.md)
for locks, versions, leases, and ownership.
