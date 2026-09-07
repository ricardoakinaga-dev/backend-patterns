# Distributed-systems patterns

Crossing a process or network boundary changes the failure model. Messages can
be delayed, duplicated, reordered, dropped, or accepted without a response;
machines can disagree about time; a healthy component can be unreachable; and a
partition can leave two participants with incompatible observations. This
reference is for reasoning about those facts before selecting coordination,
consistency, or availability mechanisms.

## Problem and forces

The central question is not “which distributed pattern is fashionable?” It is
“which invariant must hold when the participants cannot observe one another
reliably?” Identify:

- the authoritative owner of each piece of state;
- the consistency a user or workflow actually requires;
- the failure and recovery domains;
- latency, throughput, availability, and data-loss objectives;
- the ordering scope and conflict policy;
- clock, lease, and replication assumptions;
- trust boundaries and cross-service authorization; and
- operator ability to detect, reconcile, and repair divergence.

Prefer a local transaction, a modular monolith, or a single-writer boundary when
the requirement does not need independent failure, scaling, ownership, or
deployment. A network call is not justified by architectural fashion. Every
additional participant consumes a complexity budget in testing, observability,
deployment skew, and recovery.

## Distributed realities

### Partial failure and ambiguous outcomes

A timeout tells the caller that it lacks an observation, not what the remote side
did. The remote operation may have committed, the response may have been lost,
or a partition may prevent either side from learning the result. Treat retries as
potential duplicate operations; use a scoped idempotency key or a queryable
operation record for mutations. Do not infer “failed” from “no response” and then
perform a compensating action that could undo a successful one.

Define each boundary's failure semantics: detection signal, containment, durable
state impact, user-visible result, retry/reconciliation action, and operator
evidence. See [resilience patterns](resilience-patterns.md) for deadlines,
retry budgets, and overload controls and [idempotency](idempotency.md) for
duplicate effects.

### Partitions and consistency

Choose a consistency model per invariant, not per product slogan. Strong
consistency may be appropriate for a uniqueness or balance decision; read-your-
writes or monotonic reads may be enough for a user workflow; eventual
consistency may be appropriate for search or analytics if the staleness bound
is explicit. State which reads can be stale, for how long, and how a client
recognizes pending or conflicting state.

A partition policy must say which operations remain available, which are rejected,
and how divergent writes are reconciled. Do not promise both unrestricted writes
and conflict-free strong invariants without a coordination or ownership cost.
Use a single authoritative writer, conditional version check, quorum-like
protocol, or explicit conflict-resolution policy only when its failure and
operational costs are understood.

### Ordering and concurrency

Global order is rarely necessary and is expensive to preserve across independent
participants. Define order per aggregate, account, partition, or causal chain.
Use monotonic sequence numbers or versions owned by the source; reject stale
updates, buffer bounded gaps, or apply commutative operations. A wall-clock
timestamp is not a sequence number, and arrival order is not business order.

For concurrent writes, choose one of optimistic version checks, a bounded lease
with fencing, a single-writer queue, a local transaction, or a domain-specific
merge. A process-local mutex does not protect a multi-instance deployment. A
distributed lock does not prevent a paused holder from acting after its lease
expires unless downstream writes enforce a fencing token.

### Clock uncertainty

Clocks drift, can jump, and are not necessarily synchronized across services.
Use monotonic time for elapsed durations and deadlines; use a trusted source or
logical/sequence version for ordering and business state. Treat wall-clock times
as observations with uncertainty, not proof of causality. TTLs, leases, and
“latest timestamp wins” conflict resolution require an explicit skew bound and
failure behavior. If the bound cannot be established, do not use time alone to
protect correctness.

Logical clocks, causal metadata, or source-owned versions can express happened-
before relationships more reliably than timestamps. They still require bounded
storage, propagation, and a policy for missing or malicious metadata.

### Coordination, leadership, and split brain

Leader election or a lease can reduce competing writers, but a leader is not
authoritative merely because it believes it is leader. Use a fencing token or
monotonically increasing epoch that the protected resource checks. Define lease
renewal, expiry, network partition behavior, startup recovery, and what happens
when two candidates temporarily believe they are active. Do not build an
application-level election on best-effort clocks and unverified heartbeats.

If a database uniqueness constraint, conditional update, or single-owner queue
already enforces the invariant, prefer it to a general distributed lock. If
coordination cannot be made safe under pause, partition, or delayed messages,
reject or serialize the operation instead of pretending the lock is reliable.

## When to use and when not to use

Use distributed coordination, replication, or event-driven state when there is a
demonstrated need for independent failure/scaling/ownership, cross-region
availability, durable asynchronous work, or a bounded consistency trade-off.
Use the smallest mechanism that names its authority, failure detector, duplicate
behavior, ordering, conflict policy, and recovery path.

Do not use a distributed lock for ordinary CRUD when a local conditional write or
unique constraint suffices. Do not use a global transaction merely to avoid
designing compensation or reconciliation. Do not treat a service call as a
transaction, a timeout as a rollback, a timestamp as a lock, or a replica as the
source of truth without evidence. Do not split a module into services if the
only benefit is a different folder or an unmeasured belief that “distributed
scales.”

Alternatives include a modular monolith, local ACID transaction, single-writer
ownership, outbox plus idempotent consumers, a versioned read model, or a
human/operator reconciliation flow. A simpler alternative is preferable when it
preserves the invariant with lower failure surface.

## Failure modes and containment

| Failure | What it invalidates | Containment and recovery |
|---|---|---|
| Network timeout after remote commit | outcome is unknown | operation ID, idempotent retry, status query, reconciliation |
| Message duplication | one event becomes two effects | durable deduplication and unique effect constraint |
| Message reordering | stale transition overwrites newer state | per-key version/sequence and gap policy |
| Partition | participants disagree about availability/state | explicit reject/accept policy and conflict repair |
| Replica lag | stale or missing read | consistency-aware routing and freshness indicator |
| Clock skew/jump | bad expiry, order, or conflict choice | monotonic elapsed time, source version, skew bounds |
| Expired lease holder resumes | two writers act | fencing token checked by authoritative resource |
| Split brain | conflicting leaders write | quorum/epoch/ownership enforcement, safe halt |
| Retry storm | failure becomes overload | deadline, one retry owner, budget, jitter, backpressure |
| Unequal partition load | hot key or shard overload | bounded ownership, repartition plan, admission control |
| Repair/replay repeats irreversible effect | recovery causes new damage | dry run, idempotency, isolated replay, explicit side-effect policy |
| Schema/deployment skew | old/new participants misinterpret state | additive contract, compatibility window, staged cutover |

Backpressure must cross the boundary. A service that accepts work faster than it
can durably own it is not available; it is accumulating recovery debt. Propagate
deadlines, limit fan-out and in-flight calls, reject when the authoritative store
cannot accept work, and separate high-value traffic from best-effort traffic.

## Security implications

Every service boundary is a trust boundary even inside one network. Authenticate
the caller, authorize the specific resource and operation, bind tenant scope to
the authenticated principal, and validate all remote data as untrusted. Do not
trust client-supplied tenant IDs, sequence numbers, timestamps, leadership
claims, or idempotency keys without server-side scoping and enforcement. Protect
service credentials and fencing/epoch metadata, prevent replay where a message
or command is sensitive, and rate-limit fan-out, reconciliation, and replay.
Avoid cross-service data exposure in traces and repair tooling. Escalate material
service trust, tenant, authorization, secret, or sensitive-data changes through
[composition contracts](composition-contracts.md).

## Operational implications

Record topology, ownership, failure domains, replication lag, clock/skew
assumptions, lease/epoch state, and repair authority. Operators need a way to
pause writes, isolate a partition, drain or replay work, reconcile divergent
records, and verify that the old leader cannot write. Recovery procedures must
start from observed state rather than assuming the last log line committed.
Define RPO/RTO-like objectives in terms the system can measure, including data
loss window, stale-read window, queue age, and convergence time. A healthy local
process is not evidence that the distributed workflow is healthy.

## Migration and compatibility implications

Assume mixed versions during rollout. Add fields and states before requiring
them, keep old readers safe, and make new writers compatible with old consumers.
Version events and commands when meaning changes, not only when serialization
changes. Preserve operation IDs and deduplication semantics across bridges and
replays. When moving ownership, establish the new writer, fence or drain the
old writer, reconcile the handoff, and only then remove the old path.

Dual writes across services create a new distributed consistency problem. Prefer
an outbox, a single source of truth, or a replayable projection. If dual writes
are unavoidable, define divergence detection, repair, ordering, and retirement
before rollout. Schema and data evolution should follow
[migration patterns](migration-patterns.md).

## Observability implications

Propagate request, operation, correlation, causation, and trace identifiers with
tenant-safe redaction. Emit source-owned versions, epochs/fencing tokens,
consistency mode, read freshness, retry/attempt count, deadline remaining, and
partition or reconciliation state. Measure dependency reachability separately
from dependency correctness; track replication lag, stale-read rate, duplicate
rate, out-of-order/gap count, conflict count, convergence time, queue age,
leader changes, rejected writes, and repair outcomes. Logs from one service are
not enough to establish a cross-service transaction; correlate the full causal
path.

## Testing implications

Use integration and failure-injection tests for delay, loss, duplication,
reordering, partition, restart, replica lag, leader pause, lease expiry, clock
skew/jump, schema skew, and concurrent writes. Test the authoritative resource's
fencing/conditional-write check, not only the coordinator. Exercise retry
amplification and bounded backpressure under load. Test conflict resolution,
reconciliation, replay, and recovery from a partially completed workflow. Run
contract tests with old and new versions together. Assert durable state, user
outcomes, emitted effects, and telemetry. A unit test with an always-reliable
in-memory network cannot prove distributed safety.

## Evidence requirements

Before selecting a distributed pattern, require a written ownership and
consistency model, failure matrix, ordering scope, clock/lease assumptions,
recovery authority, and mixed-version plan. Before claiming correctness, obtain:

- a duplicate, timeout, and ambiguous-outcome test proving no unsafe duplicate
  side effect;
- a partition or dependency-isolation result showing the documented availability
  and consistency behavior;
- an ordering/concurrency result for stale, concurrent, and out-of-order updates;
- a clock/lease/fencing test under pause and skew assumptions;
- measured overload, retry amplification, lag, and convergence behavior;
- compatibility results for old/new participants and replayed messages; and
- an exercised reconciliation or recovery procedure with current telemetry.

Do not infer safety from a diagram, a successful local integration test, or a
vendor claim of “distributed” or “exactly once.” If clock bounds, partition
behavior, or recovery evidence are unavailable, the design remains an explicit
unverified proposal.
