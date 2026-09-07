# Caching patterns

A cache is a performance or availability optimization over an authoritative
source. It is not a source of truth unless the system explicitly chooses a
cache-like store as the durable owner and accepts the corresponding data model.
Every cache decision must name the source of truth, the invalidation or freshness
mechanism, the tolerated staleness, behavior when the cache is unavailable, and
the stampede policy.

## Problem and forces

Caching trades origin work and latency for memory, invalidation complexity,
stale data, eviction behavior, and a second failure mode. Identify:

- the measured origin cost and repetition that justify caching;
- whether stale, missing, or negative data is safe and for how long;
- update frequency, read/write ratio, hot-key distribution, and item size;
- key scope, tenant/authorization dimensions, and privacy/retention constraints;
- invalidation ownership and failure recovery;
- acceptable cache outage load on the origin; and
- warming, eviction, deployment, and migration behavior.

Do not begin with “add Redis” or a framework annotation. Begin with a measured
hot path and a correctness invariant.

## Patterns and selection

### Cache-aside

On a miss, read the authoritative source, then populate the cache; on a write,
update the source and invalidate or version the cached representation. Cache-aside
is usually the smallest choice because the application can decide which reads
are cacheable and can bypass the cache when it fails.

It is appropriate for reconstructable derived data, repeated reads, and explicit
stale tolerance. It is not sufficient by itself for strict read-after-write
behavior: a concurrent miss, delayed invalidation, or stale replica can still
return old data. Use source versions, request-local read-your-writes routing, or
an explicit freshness contract when required.

### Read-through and write-through

Read-through centralizes miss loading; write-through updates source and cache
through one abstraction. They can reduce duplicated policy when a shared cache
layer owns a stable data shape. They also hide latency, failures, and transaction
boundaries. Use them only when ownership, invalidation, failure behavior, and
observability remain visible to the application and operator.

Do not adopt read/write-through merely because the abstraction looks clean. A
generic layer that cannot express authorization scope, version checks, or partial
failure will produce plausible but unsafe data.

### Write-behind

Write-behind acknowledges a cache write before the authoritative store commits.
It can absorb bursts for explicitly durable, replayable workloads, but it turns
the cache into a queue and creates data-loss, ordering, and recovery obligations.
Do not use it for payments, inventory, authorization, or any operation whose
acknowledgement means durable business state unless the store and recovery
protocol actually provide those guarantees. A durable work queue plus an
idempotent writer is often clearer.

### Local, distributed, and layered caches

A local cache has low latency but per-instance state and uneven invalidation. A
distributed cache improves sharing but adds network failure, capacity, tenancy,
and hot-key concerns. A two-level cache can be useful when measured, but every
layer adds staleness and stampede paths. Bound local memory, entry count, item
size, and TTL; do not assume eviction is a correctness mechanism.

### TTL, versioned keys, and stale-while-revalidate

TTL bounds one kind of staleness but cannot repair a correctness-sensitive update
unless the bound is acceptable. Versioned namespaces or keys make invalidation
cheap and can avoid deleting every old value, but require version ownership and
garbage collection. Stale-while-revalidate can protect latency during origin
slowness if the response explicitly permits stale data, refresh work is bounded,
and errors do not extend staleness forever.

Request memoization is appropriate only within a request or short-lived scope;
do not turn it into cross-user storage accidentally.

## When to use and when not to use

Use a cache when a representative measurement shows repeated expensive work and
the data can be reconstructed or its freshness contract is explicit. Prefer a
read cache for derived data before caching authoritative writes. Use a small
local cache when locality and invalidation are simple; use a shared cache when
the measured hit rate and consistency policy justify the dependency.

Do not cache merely to conceal a slow query that should be indexed or bounded.
Do not cache authorization results without principal, tenant, resource, policy
version, and revocation semantics. Do not cache secrets or sensitive data in a
shared scope without an explicit protection and deletion policy. Do not make a
cache mandatory for a critical write path unless cache failure is handled safely.
Do not call a cache “eventually consistent” without a freshness bound and
invalidation owner. If the origin is fast enough, no cache is the minimum
sufficient architecture.

Alternatives include query/index improvement, materialized views, read replicas,
precomputation, request coalescing, pagination, batching, connection tuning, or
accepting the measured latency. A cache that increases operational risk more than
it reduces origin work is a regression.

## Invalidation, staleness, and stampede control

Choose one primary invalidation contract:

- **write invalidation:** commit the source, then delete or version the entry;
- **write update:** commit the source and update a representation only when the
  ordering and failure recovery are understood;
- **event invalidation:** publish a durable change and tolerate the event delay;
- **bounded TTL:** accept staleness until expiry and make the bound observable.

Deleting after a source commit can race with an earlier read that repopulates a
stale value. Common controls are source versions in the cache value, compare-
and-set updates, invalidation events carrying a monotonic version, or a short
stale window with reconciliation. Do not claim invalidation is instantaneous
across processes without testing the race.

Prevent stampedes with request coalescing/single flight, per-key leases, bounded
refresh concurrency, staggered/jittered expiry, prewarming for known hot keys,
and stale-while-revalidate where safe. A lease must have crash/expiry handling
and must not allow an expired holder to overwrite a newer value. Negative caching
can protect an origin from repeated misses but needs a short, policy-aware TTL;
otherwise a newly created resource remains invisible.

## Failure modes and containment

| Failure | Risk | Containment |
|---|---|---|
| Stale value after update | wrong user-visible state or authorization | source version, scoped invalidation, bounded freshness, reconciliation |
| Cache unavailable | origin overload or critical path failure | bypass policy, origin capacity headroom, circuit breaker, fail closed where required |
| Stampede on expiry/outage | synchronized origin surge | single flight, jitter, bounded refresh, load shedding |
| Hot key | one shard/lock saturates | key distribution, replication/read fan-out, per-key concurrency cap |
| Cache outage during write | acknowledged data not durable | write source first or durable queue; never imply commit from cache only |
| Stale repopulation race | invalidation is undone | versioned values/conditional write or event sequence |
| Wrong key scope | cross-tenant or cross-user data leak | authenticated scope in key and security tests |
| Unbounded item/namespace growth | memory/storage exhaustion | size limits, eviction policy, quotas, namespace cleanup |
| Poisoned/malformed cache value | repeated errors or unsafe deserialization | validate/version values, safe encoding, delete/quarantine bad entries |
| Warm-up load | deployment or recovery outage | gradual warming, admission control, origin budget |

Cache failure behavior is policy-specific. A public, non-sensitive product list
may bypass to the origin; an authorization decision may fail closed; a stale
status page may serve a labeled last-known result. Never use a cache error as a
reason to return data from another tenant or an unverified default.

## Security implications

Construct keys from server-controlled resource identity plus the authenticated
principal/tenant and all policy dimensions that affect the result. Do not trust a
client key to establish isolation. Prevent key collisions, cache poisoning, and
confused-deputy reads; validate authorization again at the origin when the cache
contract cannot prove it. Encrypt sensitive values, restrict cache access, set
retention/deletion behavior, avoid secrets in keys and logs, and consider whether
invalidation/replay events reveal private changes. Bound object sizes and request
fan-out to resist resource exhaustion. Security-sensitive caching changes merit
the specialist route in [composition contracts](composition-contracts.md).

## Operational implications

Define capacity, eviction, replication, failover, connection limits, timeouts,
TTL/refresh limits, namespace ownership, and origin fallback before rollout.
Operators need a safe way to flush or version a namespace, disable reads/writes,
throttle warming, inspect a redacted key/value class, and reconcile after loss.
Flushing a cache can be a production load event; treat it as an incident action,
not a harmless fix. Preserve origin headroom for a cold-cache state.

## Migration and compatibility implications

Version cache keys or namespaces when value shape, authorization dimensions, or
serialization changes. During mixed versions, readers must reject or understand
old values safely; a new reader should be able to miss and refill from the
source. Prefer a staged namespace and gradual warming over a global flush. If a
source schema changes, update source reads/writes and cache representation in an
expand/contract sequence; see [migration patterns](migration-patterns.md).

Dual cache writes are acceptable only as an explicitly bounded warm-up or
comparison technique with a source of truth and failure policy. They must not
silently become dual authoritative stores. Backfills and replays must not expose
partial or unauthorized data.

## Observability implications

Measure hit/miss/negative-hit rate by safe key class, origin load, origin latency
and tail, cache latency/error rate, entry age/staleness, refresh success, stampede
coalescing, hot keys, evictions, memory/bytes, item size, connection saturation,
and bypass/fail-closed decisions. Correlate invalidation version and source
version without logging sensitive values. Track user-visible freshness and
reconciliation lag; hit rate alone can rise while users receive wrong data.
Alert on miss storms, stale-age bounds, origin saturation, cache error rate, and
namespace growth. Make cache bypass and degraded behavior visible in traces.

## Testing implications

Test miss, hit, expiry, invalidation ordering, stale repopulation race, version
conflict, negative-cache expiry, stampede, hot key, cache unavailable/slow,
origin unavailable, restart/eviction, mixed value versions, namespace flush, and
recovery. Test tenant/principal key separation and cache poisoning. Under load,
measure origin protection, refresh concurrency, tail latency, and recovery from
a cold cache. For write paths, verify durable source state even when cache
operations fail. Assert freshness and authorization behavior, not just returned
values.

## Evidence requirements

Before choosing a cache, require a measured baseline, source-of-truth statement,
freshness/staleness budget, invalidation owner and mechanism, cache-failure
policy, key-scope design, and stampede/capacity plan. Evidence should include:

- representative hit-rate, latency, origin-load, item-size, and tail measurements;
- stale-data and invalidation-race tests with the stated bound;
- stampede and cold-start results with bounded origin load;
- cache outage, eviction, failover, and recovery tests;
- security/tenant isolation and sensitive-data retention evidence;
- mixed-version value/key compatibility and migration cleanup evidence; and
- current telemetry showing freshness, bypass, origin protection, and repair.

An in-memory demo or a high hit rate cannot prove correctness, isolation, or
survivability. If the origin behavior during cache failure has not been measured,
the cache is an unverified dependency rather than a resilience mechanism.
