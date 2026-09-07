# Observability patterns

Observability is the ability to explain a system's externally meaningful
behavior from its emitted evidence. This reference covers production signals,
operator questions, performance-adjacent measurements, alerting, and recovery
for backend designs. It complements the pattern-routing contract in
[`pattern-index.md`](pattern-index.md); load the more specific transaction,
messaging, resilience, caching, migration, or testing reference when that
boundary is central.

## Start with operator questions

Signals are useful only when they answer a decision or shorten recovery. For
each critical flow, write the questions an operator must answer without
attaching a debugger to production:

1. Was the request, message, or scheduled job accepted?
2. Which version, route, tenant class, actor class, and dependency path handled
   it?
3. Where did time accumulate: queue, application, lock, database, network,
   serialization, or downstream service?
4. Did the system produce the intended durable effect, no effect, or an
   ambiguous partial effect?
5. Are failures isolated, retrying, duplicated, delayed, or amplifying load?
6. Is the issue local to one tenant, partition, region, release, dependency,
   or capacity pool?
7. What action is safe now: rollback, disable, shed, drain, replay, repair,
   migrate, or wait?

If a design cannot answer these questions, it is not production-ready even if
its happy path is correct. Observable does not mean "many logs"; it means
evidence is correlated, bounded, interpretable, and connected to a recovery
action.

## The signal model

Use logs, metrics, and traces as complementary evidence rather than competing
telemetry brands.

| Signal | Best question | Minimum shape | Common failure |
| --- | --- | --- | --- |
| Structured logs and audit events | What happened, with which outcome and decision context? | Event name, time, severity, service/version, operation, outcome, correlation, causation, error class, bounded dimensions | Free text cannot be joined; payloads leak secrets; every retry looks like a new business operation |
| Metrics | How often, how slow, how full, and how saturated is the system? | Counters, rates, histograms, gauges, and bounded labels tied to an SLI or capacity budget | High-cardinality labels, averages hiding tails, success-only metrics, or no denominator |
| Traces | Where did a request or message spend time and cross boundaries? | Trace/span identity, parent or async link, operation, timing, status, dependency attributes, sampled errors | Missing async links, broken propagation, or sampling that hides rare failures |

The same operation may produce one business correlation identity and several
attempts, spans, and log events. Preserve that distinction: a retry is not a
new order, a redelivery is not a new payment, and a trace is not a durable
business record.

## Correlation and context propagation

At each ingress, accept a caller-supplied correlation value only as untrusted
metadata; generate a valid value when absent or malformed. Propagate context
through synchronous calls, queues, scheduled work, outbox records, and
recovery tools. A useful context model separates:

- `request_id`: one inbound request or delivery attempt;
- `trace_id` and `span_id`: one distributed diagnostic tree or span;
- `correlation_id`: one business operation across attempts and asynchronous
  steps;
- `causation_id`: the event, command, or attempt that caused this action;
- `operation_id`: a durable idempotency or workflow identity when one exists;
- release, environment, service, and tenant class dimensions.

Do not put bearer tokens, raw personal data, unbounded user input, or an
unbounded tenant ID in context. Use a stable pseudonym or approved class when
the raw value is not required. Preserve context across retries but increment an
attempt number and record the reason. Preserve causation when a message is
redelivered; otherwise operators cannot distinguish a duplicate effect from a
new command.

## Structured event design

Every critical event should have a stable event name and typed fields. A
practical baseline is:

```text
timestamp, severity, service, version, environment,
event_name, operation, outcome, duration_ms,
request_id, trace_id, correlation_id, causation_id, attempt,
route_or_consumer, dependency, status_code_or_error_class,
tenant_class, actor_class, queue_or_partition, retryable,
data_effect, policy_decision
```

Emit only fields needed for diagnosis, audit, or aggregation. Keep success,
rejection, timeout, cancellation, duplicate, and unknown-outcome outcomes
distinct. Record the boundary and error class at which a failure was observed;
do not flatten all downstream failures into `500`. Normalize stack traces and
exception messages before storage, and test redaction as a behavior. Security
and sensitive-data rules are defined in
[`security-boundaries.md`](security-boundaries.md).

For durable audit events, include the actor or service identity class,
resource class and stable identifier, authorization policy/version, action,
outcome, and source context. Keep business audit history separate from noisy
diagnostic logs so sampling and retention cannot erase accountability.

## Metrics and SLIs

Select metrics from user and operator promises, not from whatever a library
exports. Useful families include:

- request, message, and job rate; accepted, rejected, failed, cancelled,
  duplicated, and unknown outcomes;
- latency histograms for end-to-end, queue wait, handler, lock wait, database,
  serialization, and outbound dependency time;
- saturation: CPU, memory, file descriptors, connection pools, worker slots,
  thread/event-loop lag, queue depth and oldest age;
- correctness and workflow state: invariant violations, reconciliation
  mismatches, outbox/inbox backlog, dead-letter count, replay count, and stuck
  workflows;
- retries, timeout rate, circuit state, load shedding, rate-limit rejections,
  cache hit/miss/stale/error, and stream or consumer lag; and
- capacity-adjacent cost: database calls per request, fan-out count, payload
  size, storage growth, and external call volume.

Prefer bounded labels such as route class, outcome, dependency name, release,
region, and tenant class. Never use raw request IDs, user IDs, arbitrary URLs,
exception messages, or unbounded event names as metric labels. Histograms or
quantiles are needed for latency tails; averages alone can declare a healthy
system while p99 users time out.

An SLI needs a defined numerator, denominator, population, window, and
exclusion policy. Examples are successful authorized requests divided by all
eligible requests, p95 latency under a stated threshold, or work items below
an age threshold. An SLO is the target over a window; an error budget is the
remaining tolerated failure and should inform release, rollback, or repair
decisions. Do not call an internal process metric an availability SLI without
connecting it to the user-visible promise.

## Traces across synchronous and asynchronous paths

Create spans at public ingress, meaningful domain operations, queue publish and
consume, database calls, locks, cache operations, and external calls. Keep
span names low-cardinality and attach bounded attributes. Link a consumer span
to the producer span or event causation when there is no single parent-child
tree. Mark retries and redeliveries explicitly.

Trace sampling must retain errors, slow operations, policy rejections, and
rare workflow states. Tail sampling or durable counters may be needed when a
sampled trace cannot explain a low-frequency but high-impact failure. Traces
are diagnostic evidence, not a guarantee that every event is retained; use
metrics and durable records for completeness claims.

## Performance-adjacent operational evidence

Performance guidance must distinguish a measured requirement from a guess.
Before changing architecture or adding a cache, queue, read model, or
parallelism, capture a baseline for the affected workload:

| Area | Measure | Decision it supports |
| --- | --- | --- |
| User latency | p50/p95/p99 end-to-end and by dependency stage | Whether the tail is a requirement and where the budget is spent |
| Throughput | requests/jobs per time unit and concurrency | Capacity, scaling, and admission-control needs |
| Database | query count, query latency, rows scanned, lock wait, pool wait, plan shape | Index, batching, transaction, or query-shape changes |
| Network and serialization | outbound calls, fan-out, payload size, encode/decode time | API composition, batching, compression, or boundary changes |
| Queue/workflow | depth, oldest age, service rate, retry and dead-letter rate | Backpressure, worker capacity, priority, and recovery design |
| Cache | hit, miss, stale, eviction, fill latency, stampede indicators | Whether caching helps and how failure or invalidation behaves |
| Runtime resources | CPU, memory, allocations, file descriptors, event-loop or thread delay | Resource limits, leak detection, and safe concurrency |

Use a workload representative of tenant mix, payload shape, cache state, and
failure conditions. A benchmark that excludes cold starts, lock contention,
retries, or downstream latency is not evidence for production capacity.
Record the measurement window, build, configuration, dataset, and sampling
method. Any material architecture or workload change invalidates the old
baseline for the changed claim.

## Alerts, dashboards, and recovery

An actionable alert has a symptom, threshold or burn-rate condition, owner,
deduplication key, severity, link to the relevant dashboard/runbook, and a
safe first action. Alert on user impact, impending exhaustion, and unbounded
recovery debt; do not page on every retry or transient log line. A dashboard
should make the causal path visible: traffic, errors, latency, saturation,
dependency health, queue age, release, and recent control changes.

Define recovery before the incident. Depending on the pattern, the runbook may
include:

- rollback or disable a feature flag while preserving compatible contracts;
- rate-limit or shed optional work while protecting correctness-critical work;
- open a circuit or stop a consumer without losing durable messages;
- drain, pause, replay, or quarantine a queue/dead-letter item with duplicate
  safety;
- reconcile or repair a partial effect using an authoritative source;
- resume an interrupted migration from a checkpoint;
- invalidate or bypass a cache without treating it as the source of truth; and
- capture a bounded diagnostic snapshot, then restore normal sampling.

The recovery action must state its data-integrity impact and how success is
verified. "Restart the service" is not a recovery plan for an unknown commit
or an unbounded queue.

## Failure-mode observability

Use this reasoning shape for every significant flow:

| Component or boundary | Failure signal | Containment | Recovery evidence |
| --- | --- | --- | --- |
| Request handler | Error/timeout/unknown outcome and latency tail | Finite deadline, validation, idempotency, bounded fan-out | Repeated request has one durable effect or a visible reconciliation state |
| Database or lock | Pool/lock wait, deadlock, constraint conflict | Transaction scope, timeout, bounded concurrency | Rollback/commit outcome and invariant check are observable |
| Broker or outbox | Publish failure, backlog, duplicate, consumer lag | Durable pending state, retry limit, dead-letter/quarantine | Restart/replay drains safely without silent loss |
| Downstream dependency | Timeout, rate-limit, malformed response, circuit open | Bulkhead, backpressure, fallback with explicit semantics | Recovery is visible and does not amplify traffic |
| Cache or index | Miss, stale, eviction, unavailable, rebuild lag | Source-of-truth read path and bounded rebuild | Correctness survives cache loss and repair is measurable |
| Migration or mixed release | Version mismatch, rejected schema, checkpoint stall | Expand/contract, compatibility window, feature flag | Old/new clients and interrupted steps are tested and reported |

Unknown outcomes deserve their own counter and alert path. A timeout after a
remote commit must not be counted as a clean failure if reconciliation is
required.

## Observability anti-patterns and tests

Reject telemetry that is decorative rather than diagnostic:

- a health endpoint that checks only process liveness while the critical
  dependency is unusable;
- logs with no stable event name, correlation, outcome, or release context;
- raw payloads and identifiers copied into telemetry without a sensitivity
  review;
- a metric with unbounded labels or only an average latency;
- retry counters that cannot distinguish attempts from business operations;
- traces that stop at the queue or hide the database/lock wait that dominates
  the tail;
- alerts with no owner or recovery action; and
- dashboards that show green infrastructure while the user-visible SLO burns.

Test observability as part of the feature. Assert that a request, duplicate
delivery, timeout, authorization denial, partial failure, retry exhaustion,
queue replay, and migration interruption emit the expected bounded context and
outcome. Include redaction tests, label-cardinality checks, trace propagation
tests, alert rule tests, and a recovery exercise using the actual runbook
action. Evidence of emitted telemetry must be current for the artifact and
configuration under review; old dashboards or logs do not prove a changed
path remains observable.

## Composition boundary

Attach observability requirements to the architecture decision: required
correlation and causation fields, SLIs/SLOs, capacity signals, alert triggers,
recovery actions, and evidence requests. Use the shared
[`composition-contracts.md`](composition-contracts.md) handoff shape. A
reference can specify what must be measured, but it cannot claim that a
consumer's runtime, deployment, dashboards, or alerting actually satisfy the
requirement without current evidence from that environment.
