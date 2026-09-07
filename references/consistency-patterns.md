# Consistency and staleness patterns

## Purpose

This reference helps an agent state what readers and writers may observe when
data is replicated, cached, projected, asynchronous, or concurrently changed.
It covers strong consistency, read-your-writes, monotonic reads, eventual and
bounded staleness, optimistic conflict handling, reconciliation, and
coordination. It exists to prevent “eventual consistency” from becoming an
unbounded excuse for incorrect behavior.

Consistency is a contract per operation or view. A system may use strong
consistency for inventory reservation, read-your-writes for a user-facing
command, and eventual consistency for a search index. Name each one.

## When to load

Load this reference when choosing primary versus replica reads, caching,
projections, materialized views, asynchronous events, CQRS, conflict
resolution, cross-service visibility, or distributed coordination. Load it
when a requirement uses words such as current, immediate, synchronized,
eventual, stale, ordered, or consistent without defining them.

Do not load it for a purely local immutable value or a read whose source and
consumer are clearly in one atomic transaction. Combine it with
[transaction patterns](transaction-patterns.md) for commit/publication
boundaries, [concurrency patterns](concurrency-patterns.md) for races, and
[data access patterns](data-access-patterns.md) for replicas, indexes, and
read models.

## Problem and forces

The problem is to provide a truthful visibility and conflict contract at an
acceptable cost. Identify:

- which invariant requires immediate agreement;
- read latency, availability, throughput, and partition tolerance;
- replication, cache, projection, and network topology;
- user experience for pending, stale, or conflicting state;
- write contention, conflict frequency, and resolution authority;
- ordering, causality, clocks, and retry/replay behavior;
- data sensitivity and tenant isolation across derived stores;
- operational ability to measure lag, repair divergence, and rebuild views;
- migration and mixed-version behavior.

Ask for a bound, not a slogan:

- How fresh must this result be?
- Is read-your-writes required for the actor or session?
- Which stale state is safe, for how long, and with what UI/API signal?
- What happens when two valid writes conflict?
- Which source is authoritative after a projection or cache failure?
- What evidence demonstrates the promised bound under load and failure?

### Consistency is not one property

Separate:

- atomicity: whether a set of writes commits together;
- isolation: what concurrent transactions can observe;
- freshness: how old a returned value may be;
- ordering: whether related operations are observed in causal order;
- read-your-writes: whether a writer can observe its own committed change;
- monotonic reads: whether one reader moves backward in observed versions;
- durability: whether a committed value survives failure;
- convergence: whether replicas eventually agree, and under what assumptions.

A design can be durable but stale, fresh but non-atomic, or eventually
convergent but unable to resolve concurrent semantic conflicts.

## Consistency models and selection

### Strong or linearizable reads

Use when a read must reflect the latest committed value in a defined scope,
such as authorization state, financial balance, unique allocation, or a
critical workflow transition. Read from an authoritative boundary or use a
protocol that provides the same guarantee.

Strong consistency costs latency, coordination, availability during partitions,
or throughput. Do not apply it to every search or dashboard when bounded
staleness is sufficient.

### Serializability and constraint-backed consistency

Use a local transaction with suitable isolation and database constraints when
the invariant is local to one transactional resource. This is generally
stronger and simpler than a distributed lock or custom coordination protocol.
See [transaction patterns](transaction-patterns.md).

Do not claim serializable behavior from a default isolation setting or from
sequential tests. Verify the actual database and driver semantics.

### Read-your-writes

Use when a caller should see its own committed command, such as after changing
a profile or submitting an order. Route the next read to the authoritative
store, carry a session/version token, or wait until a projection reaches the
required revision.

Do not promise read-your-writes if the UI or API silently reads a lagging
replica. If the result is pending, return a status that says so.

### Monotonic reads and causal visibility

Use a session token, version watermark, causal metadata, or sticky routing
when a reader must not move backward or observe a consequence before its cause.
This matters for timelines, workflow status, and multi-step clients.

Do not invent timestamps as causal proof. Wall clocks can skew and equal
timestamps do not establish order.

### Eventual or bounded staleness

Use eventual consistency for derived search, analytics, notifications, or
other views where temporary lag is safe and the source of truth remains
available. Define a maximum tolerated lag or an explicit “may be stale”
contract where product behavior depends on it.

Eventual does not mean unbounded. Define convergence trigger, retry/replay,
dead-letter, reconciliation, and behavior when the source changes again before
the projection catches up.

### Conflict detection and resolution

Use expected versions, compare-and-swap, conditional writes, or explicit
conflict responses when silent last-write-wins could lose business intent.
Return enough information for a client or workflow to re-read and decide.

Use deterministic merge or conflict-free data types only when operations are
actually commutative, associative, and safe for the domain. A mathematical
merge does not decide whether a payment, permission, or reservation conflict
is acceptable.

Avoid last-write-wins for business facts unless loss of the earlier write is
explicitly acceptable and the clock/version semantics are trustworthy.

## Consistency controls

Select the smallest control that proves the required model:

- one local transaction and database constraint;
- primary/authoritative read for selected commands;
- read-your-writes token or session affinity;
- expected revision and conditional update;
- outbox plus projection watermark;
- inbox/deduplication for repeated events;
- bounded cache TTL with invalidation or revalidation;
- reconciliation and repair for derived data;
- single-writer or explicit coordination for one hot resource.

Distributed coordination is a last-resort control for a demonstrated
cross-process ownership problem. It adds leases, fencing, failure detection,
clock or partition assumptions, and operational recovery. A local uniqueness
constraint or atomic update is usually safer.

## When to use

Use this reference when:

- a read can come from a different store, replica, cache, or projection;
- a workflow returns before all effects are complete;
- concurrent valid writes can conflict;
- an API or product requirement says current, immediate, ordered, or pending;
- a cache or read model changes visibility;
- a service boundary separates commit from observation;
- a migration introduces dual reads, dual writes, or reconciliation.

Make the consistency model part of the API, event, domain, and operator
contract. A model hidden behind an implementation detail will be violated by
the next caller.

## When not to use

Do not:

- label a system eventual without a staleness, convergence, and repair story;
- read from a replica after a write when read-your-writes is promised;
- use last-write-wins for non-commutative business decisions by default;
- add a distributed lock when a database constraint or conditional update
  protects the invariant;
- use a cache as the source of truth;
- treat a projection's successful build as proof that it will stay current;
- claim causal or ordered behavior from timestamps alone;
- hide pending, stale, or conflict states behind a generic successful response;
- use strong global coordination when a local consistency boundary is enough.

## Alternatives and trade-offs

| Requirement | Smallest credible choice | Stronger choice when justified | Main cost |
| --- | --- | --- | --- |
| Local invariant | ACID transaction and constraint | Serializable/conditional command | Contention and retries |
| Actor sees own write | Authoritative read or revision token | Causal/session routing | Routing/state complexity |
| Derived search/reporting | Eventual projection with lag metric | Bounded wait or rebuildable index | Freshness and operations |
| Concurrent edit | Expected version/conflict response | Domain merge or single writer | User/reconciliation complexity |
| Cross-process ownership | Durable queue/unique update | Lease/fencing/coordination | Failure and split-brain risk |
| Expensive repeated read | Cache-aside with explicit staleness | Invalidation plus read model | Invalidation and cost |

If a stronger model does not change an accepted user or integrity outcome,
choose the simpler one and document the tolerated staleness or conflict.

## Failure and integrity implications

For every consistency boundary, analyze:

- primary commit succeeds but replica/projection/cache update fails;
- a read races with a write or reads from an older replica;
- a projection receives duplicate, late, or out-of-order events;
- a cache serves stale or unauthorized data;
- a network partition produces divergent writes or delayed acknowledgments;
- a reconciliation job runs twice or repairs the wrong version;
- an old and new schema or event interpretation coexist.

Define authoritative state, repair direction, conflict policy, and user-visible
status. A projection may be rebuilt; a lost source-of-truth write may not be.
Do not acknowledge a workflow as complete merely because one derived store
updated.

For each guarantee, name the anomaly it prevents and the anomaly it permits.
For example, a read-your-writes token may prevent a writer from seeing an
older version while still permitting another reader to observe stale data.

## Security implications

Stale or cross-tenant data is a security defect, not merely a consistency
trade-off. Specify:

- whether authorization decisions read authoritative state or a lagging view;
- tenant and object scope in replicas, caches, projections, and repair jobs;
- cache keys that include all security-relevant dimensions;
- invalidation on permission, membership, or deletion changes;
- privacy and retention behavior for event history and derived stores;
- conflict messages that do not reveal another tenant's state;
- integrity/authenticity of version, watermark, cursor, or causal tokens;
- access and audit controls for reconciliation and manual repair.

Do not use an eventual authorization projection for a security-sensitive
revocation without a bounded and verified containment strategy. Escalate
material identity, authorization, tenancy, privacy, or secret exposure through
the [composition contract](composition-contracts.md).

## Operational implications

Operate consistency as measurable state:

- projection, replica, and cache lag distributions and oldest age;
- stale-read, read-your-writes miss, conflict, and retry rates;
- duplicate/out-of-order event counts and dead letters;
- reconciliation drift, repair duration, failed rows, and unresolved conflicts;
- primary/replica health, failover behavior, and recovery convergence;
- cache hit/miss, invalidation failure, stampede, and unauthorized-hit signals;
- watermark/version progression and workflow pending age.

Define an alert threshold and response for each freshness or convergence
promise. Operators need to know which store is authoritative, whether it is
safe to replay, and whether a repair can overwrite newer data.

## Migration and compatibility implications

Introduce a new consistency model explicitly:

1. document the current model and observed anomalies;
2. add versions, watermarks, status fields, or compatible read paths;
3. deploy readers that understand stale/pending/conflict results;
4. backfill projections and measure lag/drift;
5. dual-read with disagreement telemetry only for a bounded migration;
6. switch authoritative reads or writers with a rollback/repair plan;
7. remove the old path after convergence and consumer compatibility are proven.

Avoid dual writes when a single owner can publish a durable change. If they are
necessary, define ordering, retry, reconciliation, and how divergent writes
are resolved. Do not migrate from strong to eventual semantics without
changing the contract and tests that relied on immediate visibility.

## Observability implications

Every response or internal read should be diagnosable by:

- source store and authority;
- data version, revision, watermark, event sequence, or snapshot time;
- freshness/lag estimate and consistency mode;
- correlation/causation, request, command, and tenant-safe resource IDs;
- conflict, stale, pending, retry, and repair status;
- cache/projection key class without exposing sensitive values.

Use traces to connect source commit to projection or cache observation. Emit
metrics for the promised SLO, not only implementation activity. Never put raw
session tokens, private event payloads, or tenant-sensitive values in logs.

## Testing and verification evidence

Evidence should attack the claimed model:

- concurrent read/write tests that expose permitted and forbidden anomalies;
- read-your-writes and monotonic-read tests across replicas or simulated lag;
- projection duplicate, reorder, delay, gap, replay, and rebuild tests;
- cache stale, invalidation, unavailable, stampede, and tenant-key tests;
- conflict detection/resolution tests with two valid writers;
- partition, failover, timeout, retry, and reconciliation tests;
- migration tests for dual-read/write disagreement and mixed schema versions;
- authorization tests against stale membership, revoked access, and cross-tenant
  derived data;
- measured lag, convergence, and load evidence for stated bounds.

A unit test that reads one in-memory map cannot prove replica freshness,
projection convergence, or cache isolation. Inspect source and derived state,
user-visible semantics, and telemetry. Record the invariant, permitted
staleness/anomaly, adversarial scenario, exact procedure, executed status, and
limitation in the handoff described by the
[composition contract](composition-contracts.md).

## Decision output

Record the operation-level consistency contract, authoritative source, forces,
selected model/control, permitted anomalies and staleness bound, conflict
policy, security scope, operational SLO, migration/reconciliation plan,
observability, rejected stronger/weaker alternatives, and evidence. Link to
[transaction patterns](transaction-patterns.md) for commit-to-publication
gaps and to [concurrency patterns](concurrency-patterns.md) for version,
single-writer, lock, and lease controls.
