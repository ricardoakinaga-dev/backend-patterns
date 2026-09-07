# Concurrency and race-control patterns

## Purpose

This reference helps an agent prevent lost updates, duplicate effects,
check-then-act races, time-of-check/time-of-use bugs, deadlocks, split
ownership, and unsafe work claims. It covers database constraints and atomic
updates, optimistic and pessimistic locking, compare-and-swap, leases,
fencing, queues, actor-like single writers, immutable data, and idempotent
processing.

The goal is not to eliminate concurrency. It is to define who may change a
resource, which version is valid, how conflicts are reported, and how progress
continues after a worker or process fails.

## When to load

Load this reference when two or more requests, workers, processes, services,
replicas, retries, or operators can observe or mutate related state. Load it
for inventory, balances, quotas, job claims, uniqueness, conditional API
updates, idempotency, distributed locks, leases, or “only one worker” claims.

Do not load it for immutable data or a single-threaded local transformation
with no shared state. Combine it with [transaction patterns](transaction-patterns.md)
for commit and retry boundaries, [consistency patterns](consistency-patterns.md)
for visibility and conflicts, [data access patterns](data-access-patterns.md)
for constraints and query behavior, and [api patterns](api-patterns.md) for
conditional requests and idempotency contracts.

## Problem and forces

The problem is to make concurrent operations safe while preserving throughput,
latency, availability, fairness, and recoverability. Record:

- resource identity and the invariant being protected;
- number of writers and whether they share a process, database, or network;
- conflict frequency, hot keys, critical-section duration, and fairness needs;
- acceptable retry, wait, rejection, queueing, and user-visible conflict;
- worker crash, lease expiry, partition, clock skew, and duplicate behavior;
- transaction isolation, index/constraint support, and data locality;
- ordering, backpressure, capacity, and starvation risk;
- authorization, tenant scope, and who may claim or release work;
- migration behavior while old and new workers coexist;
- observability and evidence needed to distinguish a race from a dependency
  failure.

Start with the invariant and a concrete interleaving. If two calls can both
pass a check before either writes, the design is concurrent whether the code
looks sequential.

### Race inventory

Look explicitly for:

- check-then-act: both callers observe availability and both allocate;
- lost update: a stale read overwrites a newer write;
- duplicate effect: retry or redelivery performs the business action twice;
- TOCTOU: authorization, file, or resource state changes between check and use;
- write skew: separate rows satisfy local checks but violate a cross-row rule;
- double claim: workers process the same job after lease or acknowledgment
  ambiguity;
- stale ownership: an old worker continues after its lease expires;
- deadlock: concurrent locks are acquired in incompatible order;
- starvation or thundering herd: one actor is repeatedly delayed while retries
  amplify contention.

## Selection patterns

### Database constraints and atomic statements

Use a unique, foreign-key, check, exclusion, or non-negative constraint when
the invariant is expressible in the authoritative database. Prefer one
conditional or atomic statement such as “decrement only if remaining is
positive” over a separate read and write.

This is often the smallest and strongest control for uniqueness, quotas, and
simple state guards. Handle constraint/conflict errors deliberately; do not
turn them into generic success.

Do not rely on a check in application code when concurrent writers can bypass
it, and do not use a constraint as a substitute for a multi-step domain
workflow it cannot express.

### Optimistic locking and compare-and-swap

Use a revision, version column, entity tag, or expected-state predicate when
conflicts are infrequent, work is short, and rejecting stale work is cheaper
than holding locks. A successful update changes the version atomically:

1. read state and revision;
2. compute the intended change;
3. update only when the revision still matches;
4. treat zero rows or a failed precondition as a conflict;
5. retry only after a fresh read and only if the operation remains safe.

Do not blindly retry a business command after a conflict. The new state may
change the decision. Return a conflict, merge intentionally, or re-evaluate
under a fresh transaction.

### Pessimistic database locking

Use row or key-range locks when conflicts are common, the critical section is
short, and waiting is preferable to rejecting work. Lock the authoritative
rows inside a bounded transaction, acquire locks in a consistent order, and
set lock/deadline limits.

Do not hold locks across network calls, user interaction, queue waits, or
unbounded computation. Do not assume a lock on one row protects a predicate
unless the database/isolation/index semantics prove it.

### Advisory locks

Use an advisory lock only when the protected identity is clear, the lock
service/database has the required ownership and failure semantics, and the
critical section is bounded. Document what resource it guards and how a
crashed owner releases it.

An advisory lock is not a durable business state or a substitute for a unique
constraint. If it is connection-scoped, verify pooling behavior. If it is
process-scoped, it cannot protect against another process.

### Leases and fencing tokens

Use a lease when work ownership must expire after worker failure and the
resource cannot be kept under one database transaction. Issue a lease with
expiry, renewal, and a monotonically increasing fencing token. Every protected
write must reject a stale token; expiry alone is not protection because an old
worker may continue after a pause or network partition.

Use a monotonic server-side time or authoritative lease service. Treat renewal
failure as loss of ownership. Bound work and make completion idempotent.

Do not use a lease without fencing for a destructive or irreversible effect.
Wall-clock expiry without a stale-owner check is vulnerable to split brain.

### Work queues and single-writer ownership

Use a durable work queue, partitioned stream, or actor-like single writer when
serializing commands for one key simplifies ordering, conflict, or hot-state
management. Define partition key, ownership, delivery, backpressure, poison
handling, replay, and rebalancing.

This trades immediate parallelism for ordered ownership. It is useful when
commands are naturally keyed, but a queue does not remove the need for durable
state, deduplication, and a database constraint at the final write.

Do not put unrelated keys in one serial queue, create an unbounded queue, or
use a worker queue to hide a missing transaction boundary.

### Immutable and append-only state

Use immutable facts, append-only records, or event logs when concurrent writes
can coexist as separate facts and a deterministic fold or reconciliation can
derive current state. This can reduce lost updates, but it moves complexity to
validation, ordering, compaction, privacy, and conflict resolution.

Do not call append-only storage conflict-free when two facts can violate a
business invariant such as double capture or over-allocation. The fold or
constraint still needs an owner.

### Idempotency and duplicate suppression

Use a durable idempotency key or unique effect record when the same command or
message may arrive more than once. Scope the key to the operation, bind it to
an input fingerprint, store the outcome or durable status, and make retention
cover the retry/replay risk.

Idempotency controls duplicate effects; it does not serialize different valid
commands or solve stale decisions. Link to [transaction patterns](transaction-patterns.md)
for inbox/outbox placement.

## Choosing a race control

Choose based on the invariant and contention:

| Situation | First candidate | Reject or escalate when |
| --- | --- | --- |
| Unique value or simple quota | Database constraint/atomic update | Rule spans non-local effects |
| Rare conflict, short command | Version/CAS | Rejection is unacceptable or conflicts are frequent |
| Frequent conflict, small local section | Bounded pessimistic lock | Work needs network calls or long computation |
| Worker crash must release work | Durable lease plus fencing | Protected target cannot reject stale owners |
| Per-key ordering is primary | Partitioned queue/single writer | Queue lag or cross-key invariants dominate |
| Duplicate delivery | Unique effect/inbox/idempotent operation | External effect lacks provider idempotency/reconciliation |
| Concurrent facts are mergeable | Append-only/merge strategy | Merge can violate a business invariant |

Do not combine optimistic and pessimistic controls casually. State which one is
the final integrity guard and how the others affect throughput or user
experience.

## When to use

Use this reference when:

- correctness depends on two simultaneous actions not both succeeding;
- a read influences a later write;
- retries, queues, or timeouts can repeat work;
- workers claim, renew, complete, or release shared work;
- a public API needs expected-version or idempotency semantics;
- a migration changes the number or behavior of writers;
- a cache or replica can make a decision from stale state.

Model the concurrency boundary at the same place as the invariant whenever
possible. A local atomic write is preferable to a distributed lock that only
coordinates application intent.

## When not to use

Do not:

- use an in-memory mutex for a multi-process or multi-instance invariant;
- add a distributed lock where a database uniqueness/conditional update is
  sufficient;
- hold a database lock across a remote call or long-running workflow;
- retry conflicts without re-reading and re-evaluating the business decision;
- use a lease without fencing tokens for irreversible writes;
- trust client timestamps or client-provided versions as authority;
- assume queue partitioning provides exactly-once effects;
- treat sequential unit tests as proof of race safety;
- serialize every operation globally when per-key ownership is sufficient;
- make idempotency keys optional for effects that clients must safely retry.

## Alternatives and trade-offs

| Need | Smallest credible choice | Stronger choice when justified | Main cost |
| --- | --- | --- | --- |
| Enforce uniqueness | Database unique constraint | Serialized domain workflow | Wait/queue and recovery |
| Avoid lost update | Version/CAS | Pessimistic lock or single writer | Conflicts or contention |
| Protect a hot row | Atomic update | Partitioned ownership/queue | Lag and routing |
| Claim background work | Atomic claim plus timeout | Lease with fencing | Renewal and stale-owner control |
| Repeatable command | Durable idempotency record | Full workflow state | Storage and retention |
| Merge concurrent facts | Append-only plus fold | Domain conflict coordinator | Reconciliation and privacy |

The stronger pattern must buy a measurable reduction in a named failure or
contention problem. If the invariant fits one database statement, do not add a
distributed coordinator.

## Failure and integrity implications

For each protected operation, write the interleaving and the post-failure
state:

- two callers read the same version;
- one commits while the other is waiting or times out;
- a worker claims work and crashes before or after the side effect;
- a lease expires while the old worker is paused;
- a stale worker resumes after a new owner starts;
- a lock holder dies, a deadlock is detected, or a connection is returned to a
  pool unexpectedly;
- a message or API request is duplicated, reordered, or retried;
- an authorization or resource check changes before use;
- a migration introduces old and new writers with different guards.

Define the final integrity mechanism, not just the coordination attempt. For
example, a lease says who may try; a fencing token and conditional write say
whether the attempt is still valid. A version says stale work is rejected; it
does not decide how the caller recovers. A queue orders work; it does not make
the consumer idempotent.

## Security implications

Concurrency controls protect authorization-sensitive resources too. Specify:

- which actor/tenant owns the resource and who may claim, update, cancel, or
  release it;
- whether a caller can choose another tenant's idempotency, lock, job, or
  partition key;
- how stale clients and workers are rejected after permission revocation;
- whether locks, leases, queue metadata, and errors leak resource existence;
- least privilege for lock/queue/database operations;
- limits against lock hoarding, lease renewal abuse, queue flooding, and
  retry amplification;
- audit records for privileged claims, manual unlocks, force-completions, and
  conflict resolutions.

Never accept a client-provided fencing token or revision without binding it to
the authoritative owner and resource. Escalate access-control, tenancy,
payment, destructive-operation, or abuse risks through the
[composition contract](composition-contracts.md).

## Operational implications

Define and monitor:

- conflict, retry, deadlock, lock wait, and timeout rates;
- critical-section and transaction duration;
- queue depth, oldest age, per-key hot partitions, and backpressure;
- lease age, renewal failures, fencing rejects, and stale-owner attempts;
- duplicate suppression, in-flight work, poison messages, and recovery time;
- starvation, fairness, and capacity under contention;
- safe drain, pause, reassign, unlock, replay, and repair procedures.

Set bounded deadlines and do not let a retry loop consume all worker or
database capacity. When an operator force-releases a lease or resolves a
conflict, record the actor, reason, prior owner/version, and resulting state.

## Migration and compatibility implications

Changing concurrency control is a mixed-version risk. Use a compatible
sequence:

1. identify all current writers, readers, workers, and manual tools;
2. add the durable version, unique constraint, status, lease, or fencing field;
3. deploy readers/writers that understand both old and new state;
4. instrument rejected stale work and duplicate paths;
5. switch one writer or partition at a time;
6. reconcile in-flight work and verify no old writer can bypass the guard;
7. remove legacy locks, retries, or writers after the compatibility window.

Do not enable a new optimistic check while an old writer still performs an
unguarded update. Do not change key partitioning without a plan for in-flight
messages and ownership transfer. Test rolling deployment with old and new
workers concurrently.

## Observability implications

Emit structured, privacy-safe context:

- resource/key fingerprint, tenant-safe owner, operation, actor class;
- expected and actual revision or fencing token outcome;
- lock/lease owner, acquisition/wait/renewal/release result;
- queue partition, delivery attempt, message/effect ID, and dedupe result;
- conflict reason, retry count, backoff, timeout, and terminal outcome;
- commit status, side-effect status, and correlation/causation identifiers.

Metrics should expose contention and correctness, not only throughput. Alert on
fencing rejects, stale-owner attempts, duplicate effects, lock age, queue age,
conflict spikes, and retry amplification. Do not log secret keys or full
business payloads merely to debug a race.

## Testing and verification evidence

Concurrency claims require concurrent evidence:

- deterministic two-writer tests for lost update, check-then-act, write skew,
  and uniqueness;
- database integration tests for atomic statements, constraints, isolation,
  lock order, deadlock/serialization retry, and stale-version rejection;
- API tests for concurrent idempotency-key requests and conditional updates;
- worker tests for duplicate claim, crash after claim/effect, lease expiry,
  fencing, rebalancing, restart, poison, and backpressure;
- property or stress tests with controlled scheduling and repeated seeds;
- authorization tests for cross-tenant keys, stale permissions, and manual
  force actions;
- migration tests with old/new writers, in-flight work, and interrupted
  ownership transfer;
- telemetry assertions for conflict, dedupe, stale-owner, and recovery paths.

Avoid sleeps as the only race test. Control barriers, transactions, clocks, or
fake schedulers where possible, then supplement with load/stress runs. Inspect
the persisted outcome and external effects; a test that merely sees one
successful response cannot prove only one effect occurred.

The verification handoff should state the invariant, schedule/interleaving,
control, expected persisted state/effects, exact command, executed status,
freshness, and limitation. Use the shape in the
[composition contract](composition-contracts.md), and link to
[transaction patterns](transaction-patterns.md) for crash/retry behavior.

## Decision output

Record the resource and invariant, race class, selected final guard, supporting
coordination, contention assumptions, timeout/retry/idempotency policy,
authorization scope, migration compatibility, operational signals, rejected
alternatives, and concurrent evidence. A lock or queue name without a
stale-owner, duplicate, and recovery story is not a concurrency decision.
