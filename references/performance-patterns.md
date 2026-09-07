# Performance patterns

Performance work is a measured change to latency, throughput, resource use, or
capacity under a defined workload. It is not a collection of fast-looking
techniques. Separate a requirement (“p95 response under this workload is below
the stated bound”) from a guess (“this cache or asynchronous path should be
faster”), and preserve correctness while improving the measured bottleneck.

## Problem and forces

Performance decisions trade CPU, memory, I/O, network, storage, concurrency,
freshness, operational complexity, and cost. Establish:

- the user or workflow latency and throughput objective, including tail percentiles;
- workload shape, concurrency, payload size, skew, burst, and read/write mix;
- correctness, ordering, durability, and freshness constraints;
- resource budgets for CPU, memory, connections, queues, storage, and network;
- scaling unit and bottleneck ownership; and
- whether the result must hold during warm-up, failure, deploy, or recovery.

Do not optimize a local benchmark while the real path is dominated by a query,
remote call, lock, queue, serialization, or capacity limit. Start with a
representative baseline and a hypothesis that can be disproved.

## Measurement before selection

Capture the current behavior with a workload that reflects production shape or
clearly states its limits. Record request rate, concurrency, payloads, cache
state, data volume, distribution/skew, environment, versions, configuration,
warm-up, duration, and repetition. Measure p50, p95, p99 or other relevant
tails, throughput, error/timeouts, and resource utilization. Averages hide the
queueing and tail behavior users experience.

Use query plans and row/byte counts for data access; profiling or sampling for
CPU/allocation hotspots; traces for cross-boundary latency; and queue/connection
metrics for contention. Keep the measurement path visible and avoid profiling
that changes the bottleneck without accounting for it. Run enough independent
trials to distinguish noise from a change, and preserve the baseline artifact.

## Useful patterns and trade-offs

### Reduce work at the right boundary

Select only needed data, filter early, use appropriate indexes/partitioning,
batch calls, eliminate N+1 access, paginate bounded results, and avoid repeated
serialization or network hops. Validate with the query plan and production-like
cardinality. An index that helps one query can increase write cost and memory;
pagination that uses offset can degrade at large depth; batching can increase
tail latency or transaction size.

### Improve locality and reuse

Use request memoization, measured caching, precomputation, or materialized views
when repeated work and freshness semantics justify them. Caching must name source
of truth, invalidation, staleness, failure, and stampede behavior; see
[caching patterns](caching-patterns.md). Do not use cached results to hide a
correctness or authorization defect.

### Bound concurrency and queueing

Parallelism can improve throughput until CPU, connections, downstream capacity,
locks, or memory saturate. Use bounded worker pools, connection pools, queue
depth, and per-dependency concurrency. Queueing can smooth bursts only when
there is a capacity and recovery policy; an unbounded queue turns latency into
data loss or an outage. Asynchronous processing changes user semantics and needs
durable completion and replay rules.

### Shape data and interfaces

Read models, denormalization, compression, streaming, bulk endpoints, and
specialized storage can reduce work, but each adds consistency, migration, and
operational cost. Use the smallest data shape that satisfies the access pattern.
Do not introduce CQRS, a new datastore, or a distributed system solely to move a
benchmark number without evidence that the existing boundary is the bottleneck.

### Admission control and graceful degradation

Rate limits, load shedding, priority, smaller payloads, and partial responses
can protect tail latency at saturation. Define which work may be rejected or
degraded and preserve security and correctness. Performance that is achieved by
silently dropping durable work is not an improvement.

## When to use and when not to use

Use a performance pattern when a measured baseline shows a material gap, the
target is explicit, and the change has a credible mechanism. Prefer the least
complex change that moves the bottleneck while preserving observable behavior.

Do not optimize before finding a bottleneck. Do not assume horizontal scaling
fixes a serialized lock, hot key, database limit, or downstream quota. Do not
increase concurrency without measuring saturation and tail latency. Do not
trade durability, authorization, or data correctness for a faster response without
an explicit product decision. Do not present a warm-cache microbenchmark as a
capacity result. If the requirement is already met with headroom, extra tuning
is complexity without evidence.

Alternatives include query/schema repair, removing an unnecessary call, reducing
payloads, changing a contract, adding capacity, accepting latency, or moving
non-critical work to a durable queue. A simpler code path often beats a new
abstraction whose overhead cannot be measured.

## Failure modes and containment

| Failure or false conclusion | Impact | Containment |
|---|---|---|
| Benchmark uses unrealistic data/cache state | false capacity claim | representative data, cold/warm runs, stated limitations |
| Average improves but tail worsens | timeouts and poor user experience | percentile targets, concurrency/load measurement |
| Unbounded parallelism | downstream/resource collapse | hard concurrency, queue, and deadline limits |
| “Fast” cache hides stale/unsafe data | correctness or data exposure | source/invalidation/security contract and failure tests |
| Batching enlarges transaction | locks, retries, and tail spikes | bounded batches, commit scope, lock/load measurement |
| New index/read model raises write cost | throughput regression elsewhere | read/write workload comparison and capacity budget |
| Compression/serialization shifts CPU bottleneck | lower throughput or tail | end-to-end resource measurement |
| Queue masks overload | growing age and unrecoverable backlog | depth/age limits, admission control, drain test |
| Optimization changes ordering/durability | lost or reordered effects | invariant tests and explicit semantic contract |
| Profiling changes behavior | wrong hotspot | low-overhead sampling and repeated trials |
| Autoscaling reacts too late | oscillation and overload | lead indicators, warm capacity, recovery test |
| One tenant/hot key dominates | unfairness and noisy neighbor | quotas, partitioning, priority, isolation |

## Security implications

Performance controls can become abuse controls or abuse surfaces. Bound payloads,
query depth, page size, regex/parse cost, fan-out, concurrency, and expensive
operations per principal/tenant. Ensure caches, read models, and batching retain
authorization and tenant isolation. Do not disable validation, auditing, or
encryption to improve a benchmark. Treat compression and error detail as
potential information leaks. Test resource exhaustion from adversarial inputs,
not only well-behaved traffic, and escalate sensitive-data or privilege changes
through [composition contracts](composition-contracts.md).

## Operational implications

Define capacity indicators, saturation thresholds, autoscaling behavior, warm-up,
backpressure, error budget, cost budget, and rollback/disable controls. Operators
need dashboards for latency distributions, throughput, resource use, queue/lock/
connection pressure, cache state, and error class. A performance change should
have a safe feature flag or rollout boundary when it changes load distribution.
Document how to revert an index/read model/cache, drain queued work, and recover
after a partial rollout. Test under deploy, cold start, dependency failure, and
recovery; a steady-state result is not enough.

## Migration and compatibility implications

Performance work often changes query shape, indexes, payloads, pagination, cache
keys, read models, or asynchronous semantics. Roll out additive schema/index
changes first, support mixed application versions, backfill with bounded load,
then switch reads or contracts and retire old structures after evidence. Maintain
API and event compatibility while new and old clients coexist. A dual-read or
shadow path must not double expensive work without a budget; a dual-write path
needs divergence detection and repair. See [migration patterns](migration-patterns.md).

Do not make a breaking pagination, consistency, or freshness change merely to
improve a benchmark; expose it as a versioned contract and measure both modes.

## Observability implications

Instrument request and dependency latency distributions, throughput, error and
timeout rate, queue depth/age, in-flight work, CPU, memory, allocation/GC where
relevant, connection pools, lock waits, database rows/bytes, cache hit/freshness,
serialization/compression cost, and per-tenant skew. Correlate a changed path to
its workload and configuration. Keep business outcome and resource metrics
separate so a lower response time cannot hide more errors or dropped work.
Alert on tail/SLO breach, saturation, backlog growth, and error-budget burn.

## Testing implications

Use repeatable performance and load tests with representative workload, data
volume, cache state, concurrency, and environment. Compare distributions rather
than one timing; record errors, timeouts, resource limits, and recovery after
saturation. Add query-plan/index checks, integration tests for batching and
transactions, cache and queue failure tests, concurrency/race tests, and API
contract tests for any changed semantics. Include cold start, mixed versions,
large/skewed inputs, hot keys, and dependency slowdown. Test known-bad controls:
the harness should fail when a limit is removed or correctness is sacrificed.

## Evidence requirements

Before recommending an optimization, require a reproducible baseline, target
threshold, workload description, bottleneck evidence, correctness/freshness
constraints, resource/cost budget, and rollback path. Evidence should include:

- repeated before/after latency percentile, throughput, error, and resource results;
- query plan/profiling/trace evidence connecting the change to the bottleneck;
- saturation and recovery behavior at and beyond expected load;
- adversarial payload, tenant skew, cold-cache, and dependency-failure results;
- mixed-version and migration/backfill impact where data or contracts changed;
- observability evidence for the new bottleneck and regression signals; and
- a current comparison artifact with environment and limitations recorded.

“It is faster locally,” lower average latency, or a larger instance is not proof
of a production performance improvement. If the workload, tail, or failure
behavior was not measured, keep the claim at hypothesis level.
