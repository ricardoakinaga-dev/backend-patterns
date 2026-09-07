# Messaging patterns

Messaging is a durable coordination boundary, not a synonym for reliability.
It is useful when a producer and a consumer need temporal separation, independent
capacity, fan-out, or a recoverable hand-off. It also introduces another state
machine, another failure domain, and another compatibility surface. The default
design assumption should be at-least-once delivery with idempotent effects; a
broker acknowledgement is not proof that an end-to-end business effect happened
once.

## Problem and forces

The decision is usually between a direct call and a durable or broadcast message.
Relevant forces include:

- whether the caller needs a result before responding;
- whether work must survive process, host, or dependency failure;
- burstiness and whether producer and consumer capacity should be decoupled;
- fan-out, replay, audit, or independent consumer ownership;
- ordering scope, duplicate tolerance, and acceptable staleness;
- transaction boundaries between the producer's state and publication;
- operational maturity for brokers, consumer groups, dead-letter handling, and
  replay;
- security and tenancy of payloads; and
- the cost of asynchronous user experience, debugging, and migration.

State the business invariant before selecting a topology. Examples are “an
invoice is issued at most once,” “every committed order eventually reaches the
fulfilment workflow,” and “a notification may be duplicated but must not expose
another tenant's data.” A queue or event stream is a means to preserve such an
invariant, not the invariant itself.

## When to use and when NOT to use

Use messaging when work must survive a process or dependency failure, when
producer and consumer capacity or deployment must be decoupled, when independent
consumers need a durable fact, or when a bounded asynchronous workflow is the
right user contract. Choose a queue, event stream, or local durable job table
according to ownership, fan-out, replay, and ordering needs.

Do not introduce a broker to decouple two calls that are local, synchronous, and
transactionally coupled. Do not use a message as a hidden transaction boundary,
as a substitute for an immediate authoritative response, or as “fire and forget”
for critical work. Do not choose messaging before defining delivery, duplicate,
ordering, backpressure, retention, and recovery semantics. A direct call, local
transaction, or in-process module boundary is the better alternative when the
additional durability and operational cost buys no required capability.

## Patterns and selection

### Work queue and competing consumers

Use a work queue when one logical task should be handled by one worker at a time,
workers can be retried, and the task has a durable ownership/acknowledgement
model. Bound prefetch and concurrency, make acknowledgement occur after the
required durable effect, and define visibility timeout or lease recovery.

Do not use a work queue when every subscriber must observe the fact, when the
caller requires a synchronous authoritative result, or when no one owns poison
message repair. A direct call, a local job table, or a transactional outbox may
be smaller alternatives.

### Pub/sub event

Use pub/sub when a committed fact has multiple independent consumers and each
consumer may progress at its own rate. Give the event an explicit owner, stable
identity, schema/version, occurred-at value, and causation/correlation metadata.
Consumers must tolerate replay and should not infer a total order that the
transport does not provide.

Do not publish an event merely to replace a local function call or to hide an
unclear transaction boundary. If a consumer is required for the producer's
commit to be valid, the operation is a workflow with explicit completion and
recovery semantics, not a fire-and-forget notification.

### Transactional outbox

Use an outbox when a local database commit and message publication must not drift.
Write the business state and an outbox record in one local transaction; publish
from the outbox; retain delivery state long enough to reconcile ambiguous
publication. The publisher may publish a record, crash before marking it sent,
and publish it again. The consumer contract therefore still needs deduplication.
An outbox does not make a remote side effect atomic with the local transaction.

Do not use an outbox as a substitute for a consumer contract, a repair process,
or a capacity plan. If the outbox can grow without a bound, it simply moves the
outage to local storage.

### Inbox and idempotent consumer

Use an inbox or an equivalent durable receipt when processing a message can
change state or cause an external effect. Atomically claim a message identity
within the consumer's scope, record the request digest when useful, apply the
local effect, and acknowledge only after the relevant commit. See
[idempotency](idempotency.md) for key scope, digest, and concurrent-claim rules.

Do not rely on an in-memory set, a process-local lock, or a broker's delivery
flag for durable deduplication. Those mechanisms disappear on restart and do
not coordinate multiple consumers.

### Retry schedule and dead-letter handling

Transient failures should be retried with a bounded schedule, a deadline, and a
known owner. Separate retryable dependency failure from invalid input and poison
messages. Delayed retry, a retry topic, or a scheduled job can make the delay
visible and keep the main queue available. A dead-letter queue is a quarantine
and investigation path, not a disposal bin: preserve enough context to repair,
redrive, or intentionally reject the message.

Do not retry every exception, redrive indefinitely, or send a message to a dead
letter queue without an operator procedure and an invariant for lost work.
Coordinate message retries with the [resilience patterns](resilience-patterns.md)
reference; stacked retry loops multiply traffic.

## Delivery, duplication, ordering, and “exactly once”

Treat delivery and effect semantics as separate claims:

| Claim | Safe default | Required design question |
|---|---|---|
| Delivery | at least once | What happens after the consumer acts but before acknowledgement? |
| Ordering | none globally; perhaps per partition/key | Which key has a meaningful order, and what is the gap/reorder policy? |
| Persistence | durable only within stated retention/replication limits | What loss window exists during broker or region failure? |
| Effect | idempotent or deduplicated | Which durable boundary prevents a duplicate side effect? |

There is no magical end-to-end exactly-once guarantee. A broker may suppress a
duplicate internally while the consumer's database, email provider, payment
gateway, or object store still sees two attempts. A producer timeout may mean the
broker accepted a message or rejected it; retrying is safe only when the message
identity and consumer effect are safe. A consumer can commit and crash before
acknowledgement, causing redelivery. Design for duplicate delivery and state
where a narrower exactly-once claim is actually proven, for example a single
local transaction covering receipt and local effect. Do not extend that proof
across an uncoordinated network call.

Ordering is usually a per-key property. Partition by the aggregate or resource
whose transitions must be serialized, attach sequence/version information, and
choose explicitly between buffering gaps, rejecting stale updates, applying
commutative operations, or reconciling later. A single global order is expensive,
fragile under partitions, and often stronger than the domain needs.

## Failure modes and containment

| Failure | Likely symptom | Containment and recovery |
|---|---|---|
| Producer commits state but publication fails | missing downstream work | transactional outbox, publisher retry, reconciliation against committed state |
| Publish response times out | unknown acceptance; duplicates on retry | stable message identity, idempotent consumer, inspect broker state where possible |
| Consumer crashes after effect before ack | redelivery and duplicate attempt | inbox/unique effect constraint, commit-before-ack, replay-safe handler |
| Consumer is slow or unavailable | queue age and lag grow | bounded prefetch, backpressure, capacity policy, alert on age, controlled redrive |
| Poison or malformed message | one item repeatedly blocks progress | bounded attempts, quarantine, schema validation, repair/redrive procedure |
| Out-of-order event | illegal regression or stale projection | per-key sequence/version check, gap policy, reconciliation |
| Schema/version skew | deserialization or semantic break | additive evolution, tolerant readers, contract checks, versioned event types |
| Dead-letter queue grows silently | durable loss hidden as “success” | DLQ metrics, ownership, payload-safe inspection, replay and purge policy |
| Replay overwhelms consumers | recovery causes another outage | replay rate limit, isolated consumer group, checkpoints, capacity test |
| Broker or storage outage | publish/consume errors and backlog | explicit availability mode, bounded local buffering, fail-fast at unsafe point, restore drill |

Backpressure is part of correctness. Bound queue depth, message size, producer
rate, consumer concurrency, and in-flight work. Decide whether a full queue
causes rejection, caller throttling, delayed acceptance, or loss of a explicitly
non-critical notification. Never use an unbounded queue as an availability
strategy; it converts overload into memory, disk, or recovery failure.

## Security implications

Authenticate producers and consumers and authorize each operation, topic, queue,
and tenant scope. Validate message type, schema, size, encoding, and references
at the consumer boundary; a broker's acceptance is not input validation. Do not
put secrets, bearer tokens, or unnecessary personal data in durable payloads.
Encrypt in transit and at rest according to sensitivity, and define retention,
redaction, deletion, and replay behavior. Treat message IDs, correlation IDs,
and tenant identifiers as untrusted input. Prevent cross-tenant routing and
redrive, and rate-limit publication and replay so a principal cannot turn a
queue into a resource-exhaustion or amplification service. Escalate material
trust, authorization, webhook, payment, or sensitive-data changes through
[composition contracts](composition-contracts.md).

## Operational implications

Operate the queue as a stateful system. Define retention, replication, maximum
payload size, visibility/lease duration, prefetch, concurrency, retry budget,
dead-letter ownership, redrive limits, and recovery objectives. The system must
answer how an operator pauses intake, drains work, stops a retry storm, repairs a
poison message, replays a safe range, and reconciles business state after a
partial outage. A deployment is not complete until old and new consumers can
coexist for the compatibility window.

## Migration and compatibility implications

Event and command schemas are long-lived contracts. Prefer additive fields with
safe defaults, tolerant readers where absence is meaningful, explicit event type
versions when semantics change, and a deprecation window based on observed
consumer use. Never rename or reinterpret a field while old consumers may still
read it. Mixed consumer versions must handle messages produced before and after
the rollout. Replays and backfills must use a bounded, idempotent consumer path;
do not silently re-trigger irreversible notifications or payments.

When changing topology, first preserve the old publication contract, introduce
the new consumer or bridge, compare/reconcile results, then retire the old path
after lag, error, and consumer evidence. A database migration belongs to
[migration patterns](migration-patterns.md), not to an undocumented message
cutover.

## Observability implications

Propagate a non-secret message ID, correlation ID, causation ID, producer/consumer
version, tenant-safe scope, and trace context. Measure publish success and
ambiguity, queue depth, age, oldest message, throughput, consumer lag, attempt
count, duplicate rate, processing latency, acknowledgement failures, payload
validation failures, dead-letter count/age, replay rate, and terminal outcomes.
Log state transitions and bounded identifiers rather than full sensitive
payloads. Alerts should identify whether loss risk is in production, delivery,
processing, or reconciliation; “broker healthy” is not enough.

## Testing implications

The useful test surface is failure-shaped, not only a happy-path handler test.
Use schema/contract tests for producers and consumers; integration tests for
acknowledgement and transaction boundaries; duplicate, reorder, gap, poison,
malformed, retry-exhaustion, consumer-restart, and broker-unavailable tests;
crash-after-commit and crash-before-ack simulations; replay and DLQ recovery;
bounded-load/backpressure tests; and security tests for tenant crossing,
forged metadata, oversized payloads, and unauthorized redrive. Test external
side effects with a faithful idempotency-aware double or sandbox. Assert both
the response/ack and durable state, emitted effects, and telemetry.

## Evidence requirements

Before selecting a messaging pattern, require an observed or explicitly measured
answer for the synchronous-versus-asynchronous requirement, delivery contract,
ordering key, transaction boundary, payload/retention limits, and recovery owner.
Before claiming the design works, evidence should include:

- a durable duplicate-delivery test showing one intended business effect under
  concurrent/replayed processing;
- an outbox or equivalent crash-window test if local state and publication must
  align;
- a schema compatibility result across the mixed-version window;
- measured queue capacity, lag/age behavior, retry amplification, and backpressure
  response under representative load;
- a dead-letter/redrive and operator recovery procedure exercised on synthetic
  data; and
- current metrics, traces, and logs demonstrating correlation and terminal
  outcomes.

Static prose or a broker feature list cannot prove exactly-once business
semantics, losslessness, recovery, or production capacity. Mark those claims as
unproven until the corresponding boundary is exercised.
