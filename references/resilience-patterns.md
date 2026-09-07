# Resilience patterns

Resilience is the ability to preserve important invariants and contain harm when
dependencies are slow, unavailable, overloaded, incorrect, or partitioned. It
is not the same as making every request return success. A resilient design may
reject early, degrade a non-critical feature, defer work, or expose an honest
partial result so that correctness and recovery remain possible.

## Problem and forces

Every remote call adds latency, an ambiguous outcome, and an independent failure
mode. The relevant forces are:

- user or workflow deadlines and acceptable partial results;
- dependency failure probability, tail latency, and recovery time;
- whether an operation is safe to retry or can be made idempotent;
- shared resource limits such as threads, connections, memory, queues, and rate
  limits;
- consistency and durability requirements;
- whether overload should be queued, rejected, degraded, or shed;
- blast radius across callers and dependency layers; and
- the observability and operator control needed during an incident.

Start with a dependency graph and a failure budget. For each edge, state the
deadline, cancellation behavior, retry owner, maximum work, fallback semantics,
and user-visible result. If those are unknown, adding a retry or breaker is
premature.

## Timeouts and deadlines

Put a finite timeout on every network, storage, lock, and queue operation unless
the operation is explicitly bounded by a stronger enclosing deadline. Prefer a
monotonic end-to-end deadline propagated through calls over unrelated per-hop
timeouts. Each attempt must use only the remaining budget, including connection
setup, serialization, and response handling. Cancel abandoned work where the
runtime and dependency support it; a timeout that leaves the server processing
unbounded work is only a client-side illusion.

Use a timeout when a dependency can become stuck or slow and the caller has a
meaningful recovery path. Do not use a tiny timeout to hide capacity problems,
or an infinite timeout because “the database will eventually respond.” Do not
choose a deadline from a mean latency; use measured tail latency plus a stated
error budget and validate it under load.

## Retries, budgets, backoff, and jitter

Retry only a classified transient failure, only while the operation's deadline
remains useful, and only when repeating the operation is safe. A retry policy
must define the maximum elapsed time, attempts, total work, and response to
permanent failure. Prefer server-provided retry hints only within a local safety
cap. Exponential backoff without a cap, deadline, or jitter is not a complete
policy.

Use a retry budget as a finite resource. A token bucket, a bounded fraction of
successful traffic, or an equivalent policy can prevent recovery traffic from
overrunning a failing dependency. Bound retries per request and globally; pause
or shed retries when the budget is exhausted. Full or decorrelated jitter avoids
synchronization; verify the actual distribution rather than assuming a library
default is safe.

Analyze amplification across layers. If a request may be attempted `a` times by
each of `n` stacked layers, the worst-case downstream attempts can approach
`a^n`, before fan-out and queue redelivery are included. Assign retry ownership
to one layer where possible. Do not put independent “helpful” retries in a
client, gateway, service, ORM, broker, and job worker without a combined budget.

Never retry validation, authentication, authorization, deterministic conflicts,
unsupported operations, or a known non-idempotent write. See
[idempotency](idempotency.md) before retrying a mutation. A timeout is an
ambiguous outcome, not evidence that the operation did not happen.

## Circuit breakers and failure isolation

A circuit breaker can stop calls to a dependency that is demonstrably failing,
allowing recovery and protecting callers. Define what counts as a failure, the
sampling window, minimum volume, open duration, half-open probe limit, and
fallback. Breakers are local observations, not a distributed truth about a
service. They should not oscillate on sparse traffic or conceal a dependency
that is returning semantically invalid data.

Use bulkheads to isolate pools by tenant, dependency, operation class, or
priority when resource contention would otherwise let one failure consume all
capacity. Bound connections, worker concurrency, queue depth, memory, and
response buffering. Do not create so many pools that the sum exceeds the host or
downstream limits; a bulkhead without a capacity model is another overload path.

## Backpressure, overload, and load shedding

Backpressure makes demand respect capacity. Propagate bounded queue capacity,
limit in-flight work, reject or defer excess requests, and slow producers when
consumers are saturated. A full queue must have a deliberate policy: return a
retryable rejection, accept into durable storage, drop only explicitly
best-effort work, or switch to a safe degraded mode. Never let an unbounded
queue, thread pool, connection pool, or batch grow until the process dies.

Rate limits protect a principal or shared dependency; concurrency limits protect
the resource from work that is individually slow; load shedding protects the
system by sacrificing lower-value work. State the scope, identity, fairness,
burst allowance, and response contract for each. Prefer graceful degradation for
non-critical features, but fail closed when omission would violate authorization,
financial, safety, or data-integrity invariants.

## Fallbacks, degradation, and health signals

A fallback is a different product behavior, not a generic success response. It
must identify its source, staleness, confidence, and limits. Use a cache or
replica only when its freshness and authority are acceptable; see
[caching patterns](caching-patterns.md). Do not return fabricated defaults that
look authoritative, swallow errors, or report success before a required durable
effect exists.

Separate liveness, readiness, and dependency health. A process can be alive but
unable to accept work, or ready for one class of traffic while another dependency
is unavailable. Health checks must be bounded, authenticated where exposed, and
unable to create a synchronized probe storm.

## When to use and when not to use

Use these patterns when a real dependency boundary, variable load, or failure
mode can be named and the system has a recovery action. Combine a deadline with
bounded work, backpressure, observability, and an explicit invariant.

Do not add a circuit breaker to compensate for missing timeouts; a breaker does
not stop a request that never completes. Do not add retries to compensate for a
wrong transaction boundary, a saturated database, or a non-idempotent side
effect. Do not make every path asynchronous merely to hide latency. Do not use a
fallback that violates the consistency or security contract. For a local module
with no failure boundary, a direct call and ordinary error handling are usually
the minimum sufficient design.

Alternatives include reducing dependency count, co-locating a transaction,
precomputing a projection, using a durable work queue, increasing capacity,
fixing a query, or explicitly accepting an outage. A resilience mechanism is
justified by measured risk and a defined response, not by its name.

## Failure modes and containment

| Failure or mistake | Result | Containment |
|---|---|---|
| Missing or infinite timeout | stuck work consumes resources | finite deadline, cancellation, bounded pools |
| Retry of a non-idempotent mutation | duplicate charge/order/effect | idempotency key, deduplication, or no retry |
| Layered retries | retry storm and dependency collapse | one owner, shared deadline, global budget |
| No jitter | synchronized bursts after outage | full/decorrelated jitter and load test |
| Breaker too sensitive | healthy traffic rejected or flapping | minimum sample, tuned window, bounded probes |
| Breaker too permissive | outage propagates before opening | tail/error signal, bulkhead, explicit thresholds |
| Unbounded queue/concurrency | memory exhaustion and long recovery | hard limits, backpressure, load shedding |
| Unsafe fallback | stale/forged result appears authoritative | label freshness, fail closed for critical paths |
| Timeout without cancellation | orphaned work continues downstream | propagate cancellation and enforce server limits |
| Health check fan-out | outage creates probe storm | cached/bounded checks, separate probe budget |
| Retry after deadline | useless late effects or response mismatch | check remaining deadline before each attempt |
| Rate limit by untrusted identity | bypass or tenant starvation | authenticated scope and fair resource partition |

## Security implications

Resilience controls are security controls as well as availability controls. Rate
limits, concurrency caps, payload limits, and circuit breakers reduce abuse and
resource exhaustion, but their keys must not permit a caller to evade isolation.
Do not retry authentication failures or expose dependency details in fallback
responses. Ensure degraded paths retain authorization, tenant filtering, audit
events, and input validation. Keep secrets and sensitive payloads out of retry
logs and traces; retries can multiply exposure. Validate third-party retry hints
and never let an untrusted response choose an unbounded delay or redirect work
to an arbitrary destination. Escalate authentication, authorization, SSRF,
webhook, or sensitive-data changes through [composition contracts](composition-contracts.md).

## Operational implications

Operators need controls to pause retries, change traffic priority, lower
concurrency, open a breaker, drain queues, disable a non-critical feature, and
restore normal operation without a restart. Define SLOs and error budgets for
latency, errors, freshness, and queue age. Alert on saturation and retry rate,
not only on HTTP error counts. Document dependency ownership, capacity limits,
breaker state interpretation, and a recovery drill. A fallback that cannot be
distinguished from primary data will make diagnosis slower and repair riskier.

## Migration and compatibility implications

Adding a timeout or retry changes externally visible timing and traffic. Roll out
with bounded configuration, feature flags, shadow measurement, and a rollback or
roll-forward procedure. Mixed client versions may use different deadlines or
retry semantics, so the server must remain safe during the compatibility window.
When introducing idempotency, accept old clients without silently replaying
unsafe writes; use an explicit versioned contract or a safe no-retry path.
Changing a queue, breaker, or rate-limit key can move load between tenants and
must be observed during rollout. Configuration defaults are part of the
interface; record and test them.

## Observability implications

Propagate request and causation IDs plus the absolute deadline, but do not log
credentials or full sensitive payloads. Measure attempt number, retry reason,
remaining budget, backoff, timeout/cancellation, breaker state and transitions,
bulkhead occupancy, queue depth/age, rate-limit decisions, shed/degraded count,
dependency latency distributions, error class, and terminal outcome. Distinguish
the original request from retry work in traces and metrics so amplification is
visible. Alert on exhausted budgets, rising tail latency, saturation, and
recovery failure; a low error rate with a high retry rate is not healthy.

## Testing implications

Test transient, permanent, malformed, slow, timeout, connection-reset, and
ambiguous-outcome failures. Verify no retry for unsafe or non-retryable errors,
the exact attempt/deadline/budget bounds, jitter distribution, cancellation, and
fallback honesty. Exercise stacked dependencies for amplification, breaker
open/half-open behavior, bulkhead isolation, queue full behavior, rate-limit
fairness, load shedding, restart/recovery, and traffic recovery after an outage.
Use representative load to observe tail latency and resource saturation; a unit
test that verifies “retry three times” cannot prove system resilience.

## Evidence requirements

Require a dependency failure map, measured baseline tails or a documented
uncertainty, a selected timeout/deadline, retry classification and budget, and a
clear degraded/failed response before calling a resilience design complete.
Evidence should include:

- a failure-injection result for slow, unavailable, and ambiguous dependencies;
- a duplicate-effect test for every retried mutation;
- measured retry amplification across the real call chain and proof that bounds
  hold under concurrent load;
- backpressure/overload results showing bounded memory, queue, concurrency, and
  recovery behavior;
- breaker, bulkhead, rate-limit, and fallback tests with telemetry assertions;
- mixed-version rollout evidence for changed timing or retry contracts; and
- a current operator procedure for pause, drain, repair, and recovery.

Static configuration or a passing happy-path request cannot prove a timeout,
retry budget, or fallback is safe. Treat unmeasured capacity, cancellation, and
recovery as unresolved risk.
