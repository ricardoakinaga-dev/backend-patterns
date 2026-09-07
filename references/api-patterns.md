# API and external contract patterns

## Purpose

This reference helps an agent design stable HTTP, RPC, GraphQL, command,
query, asynchronous, and webhook interfaces. It treats an API as a contract
between independently changing parties, not as a serialization of internal
objects. The decision must cover semantics, compatibility, authorization,
failure, idempotency, concurrency, operations, and evidence.

## When to load

Load this reference when adding or changing a public or cross-service endpoint,
event-like callback, command/query contract, pagination/filtering behavior,
error shape, versioning policy, idempotency key, conditional request, or
asynchronous workflow boundary.

Do not load it for a private function whose callers, release, and failure
semantics are controlled in one local module unless the function is becoming a
real boundary. Combine it with [architecture boundaries](architecture-boundaries.md)
for ownership, [transaction patterns](transaction-patterns.md) for side
effects, [consistency patterns](consistency-patterns.md) for read guarantees,
and [concurrency patterns](concurrency-patterns.md) for conditional updates.

## Problem and forces

The problem is to expose a useful contract that remains safe while clients,
servers, data, and deployments evolve independently. Identify the forces:

- client diversity, version skew, and unknown future consumers;
- resource semantics versus task or command semantics;
- latency, payload size, round trips, and partial availability;
- validation, error recovery, and user-visible status;
- authentication, authorization, tenant isolation, and abuse limits;
- idempotency, duplicate delivery, retries, and timeout ambiguity;
- read consistency, conditional mutation, and conflict handling;
- observability, supportability, and privacy;
- deployment, schema, event, and deprecation migration cost.

Do not choose REST, RPC, GraphQL, or a vendor format from taste. First state
who calls, what it needs to cause or learn, how long the operation may take,
what must be atomic, and what the caller can safely retry.

### Contract questions that must have explicit answers

For each operation, define:

1. Who is the caller and what trust level is established?
2. What intent or resource does the operation represent?
3. Which inputs are required, bounded, normalized, and rejected?
4. What response means accepted, completed, pending, rejected, or unknown?
5. Which state and side effects can change, and within which transaction?
6. What errors are stable and actionable without leaking sensitive data?
7. Can the request be replayed, and what key or constraint makes it safe?
8. What consistency and concurrency guarantee does a read or write provide?
9. How are old clients supported while the contract evolves?
10. Which logs, metrics, traces, and audit facts prove the behavior?

If the answer to completion is ambiguous after a timeout, design a status
query or idempotent replay path. Do not force clients to guess whether a side
effect happened.

## Contract-first patterns

### Resource-oriented APIs

Use resource-oriented modeling when clients manipulate durable resources with
standard lifecycle semantics. Make identifiers stable, relationships explicit,
and state transitions legal. Use HTTP methods or equivalent verbs consistently,
but do not pretend every business command is a generic update.

Use explicit command endpoints when the action has domain semantics that a
partial field update would obscure, such as capture payment, approve claim, or
reserve inventory. The command should state preconditions, authorization,
idempotency, and resulting state.

Do not expose storage tables as the public model. A database column rename,
foreign key, or internal status is not automatically a compatible API change.

### RPC and gRPC-style contracts

Use RPC when the operation is naturally a procedure, clients are known, a
strong schema and generated contract reduce ambiguity, or low-latency
service-to-service calls matter. Define deadlines, status semantics, retries,
version skew, and authorization as part of the contract.

Do not use a fast binary interface to hide an unstable domain boundary. A
remote procedure is still a network call: it can time out after committing,
return malformed data, or be retried by multiple layers.

### GraphQL and composed query interfaces

Use a query composition interface when consumers need related views with
different field shapes and the team can govern schema ownership, authorization,
complexity, and resolver behavior. Make field-level authorization and bounded
depth/cost explicit.

Do not use flexible querying to avoid deciding ownership, to expose every
internal field, or to tolerate unbounded fan-out. A focused resource or query
endpoint may be safer and easier to cache, authorize, and operate.

### Query, command, and asynchronous operation separation

Keep reads free of unintended writes and commands explicit about side effects.
For long-running work, return an accepted or pending representation with a
stable operation identifier and a status endpoint or callback contract. The
operation state needs a terminal result, retry behavior, expiry, and a repair
path.

Do not return success before the promised state is durable, and do not return a
generic 200 response that makes pending, rejected, and completed
indistinguishable. If an endpoint only enqueues work, say so.

### Pagination, filtering, and sorting

Choose offset pagination for small, stable, human-oriented result sets where
page numbers matter and drift is acceptable. Choose cursor or keyset
pagination for large or changing collections where stable traversal and
bounded query cost matter. Define ordering, cursor expiry, ties, and deletion
behavior.

Bound page size, filter complexity, sort fields, expansion depth, and total
work. Authorize the collection and each returned object; never assume a
filtered query is a tenant boundary. Do not offer arbitrary query language
because the client might eventually need it.

### Errors and validation

Use a stable error contract with a machine-readable category/code, safe human
message, field or resource context where appropriate, correlation identifier,
and retryability or remediation semantics. Keep internal stack traces,
credentials, SQL, tenant existence, and sensitive policy details out of
responses.

Validate syntax, size, type, and shape at the trust boundary. Domain and
database constraints remain necessary because internal callers, races, and
replays can bypass transport validation. Distinguish malformed input,
unauthorized action, conflict, dependency failure, and unknown completion.

## API evolution

Assume old and new clients and servers coexist. Prefer additive changes:

- add optional request fields with safe defaults;
- add response fields without changing the meaning of old fields;
- preserve existing enum meanings and error semantics;
- tolerate unknown fields or values where doing so is safe;
- publish a compatibility window and deprecation owner;
- version events and schemas when a consumer cannot safely tolerate change;
- use feature flags or capability negotiation for behavior changes.

Treat the following as potentially breaking:

- removing or renaming a field, endpoint, enum, or error code;
- changing nullability, units, default meaning, ordering, or authorization;
- narrowing accepted input or page/filter limits without a compatibility plan;
- changing whether an operation is synchronous, idempotent, or eventually
  consistent;
- reusing an identifier or event type for a different semantic.

Choose path, header, media-type, schema, or capability versioning based on
consumer and deployment needs. A version label does not solve mixed-version
behavior; define how long versions coexist, how telemetry identifies them,
and how old data and retries are interpreted.

Do not promise “backward compatible” solely because a schema compiler accepts
both documents. Compatibility includes semantics, authorization, errors,
timeouts, side effects, pagination, consistency, and operational behavior.

## Idempotency and conditional concurrency

For a side-effecting request that may be retried, accept an idempotency key
with a defined scope, retention, request fingerprint, result replay behavior,
and conflict behavior when the same key is reused with different parameters.
Enforce uniqueness in durable storage where the effect is owned; an in-memory
map is not sufficient across processes or restarts.

For updates based on a previously read representation, use an expected version,
conditional request, or equivalent compare-and-swap. Return a conflict or
precondition failure when the version is stale; do not silently overwrite a
newer write.

An idempotency key prevents duplicate effects for the defined operation; it
does not prove business equivalence across different keys or different
endpoints. Link the mechanism to [concurrency patterns](concurrency-patterns.md)
and [transaction patterns](transaction-patterns.md).

## Webhooks and asynchronous callbacks

Treat a webhook as an at-least-once, delayed, duplicated, reordered, and
possibly forged request unless the contract proves otherwise. Sign a canonical
payload, bind verification to a key and timestamp policy, and provide replay
protection appropriate to the threat model. Consumers should authenticate the
sender, deduplicate by stable event identity, validate schema and state
transitions, and acknowledge only after durable handling or durable enqueue.

Publish event type, version, event ID, causation/correlation ID, occurred time,
delivery attempt, ordering scope, retry schedule, dead-letter behavior, and
retention. Never make a critical workflow depend on an unbounded
fire-and-forget callback with no reconciliation.

The producer should make publication durable with a transactionally owned
outbox when the event reflects committed state; see
[transaction patterns](transaction-patterns.md). “Exactly once delivery” is
not a safe consumer assumption.

## When to use

Use this reference when an interface is consumed across a trust, process,
deployment, or ownership boundary, or when clients must survive independent
evolution. Apply the full contract questions for:

- public endpoints and SDK-facing APIs;
- service-to-service commands and queries;
- webhooks, callbacks, event envelopes, and operation status APIs;
- pagination, filtering, and error contracts;
- idempotent writes and optimistic concurrency.

Start with the smallest stable operation that satisfies the use case. A
well-defined direct call can be more durable than a generalized API platform.

## When not to use

Do not:

- expose internal entities or ORM models as a contract;
- add a version segment for every minor change without a compatibility need;
- use GraphQL, RPC, a broker, or a gateway solely to appear modern;
- make every update a generic PATCH when the operation is a named command;
- return 202 or enqueue work without status, retry, expiry, and recovery
  semantics;
- rely on client retries for a non-idempotent operation;
- accept unbounded page size, filter expressions, nesting, or response
  expansion;
- treat route-level authentication as object-level authorization;
- infer completion from a timeout or swallow a conflict as a success;
- call an endpoint backward compatible while changing state or error meaning.

## Alternatives and trade-offs

| Need | Smallest credible choice | Stronger choice when justified | Main cost |
| --- | --- | --- | --- |
| One known client and operation | Typed local/RPC contract | Versioned public API | Compatibility and support burden |
| Durable resource lifecycle | Resource-oriented endpoint | Resource plus explicit commands | More contract surface |
| Variable read shape | Focused query endpoints | Governed GraphQL/composition layer | Complexity, auth, and query cost |
| Large changing collection | Bounded cursor pagination | Search/read model | Indexing, lag, and rebuild cost |
| Retryable side effect | Durable idempotency record | Workflow/operation resource | Retention and cleanup |
| Long-running work | Operation status resource | Callback/webhook plus reconciliation | Delivery and security burden |

The stronger option is justified only when it reduces a stated client,
performance, compatibility, or operational problem. Record rejected options and
the assumptions that would reopen them.

## Failure and integrity implications

For each operation, walk the timeline:

1. validation and authorization;
2. durable transaction start;
3. local state change;
4. outbox or side-effect record;
5. response or acceptance;
6. downstream processing and completion.

Ask what the caller sees if the process crashes or the network times out
between every step. Explicitly cover duplicate requests, duplicate callbacks,
late callbacks, out-of-order events, partial response bodies, downstream
commit-before-timeout, and retry exhaustion.

Define whether an operation is atomic, accepted-but-pending, best-effort, or
compensatable. A response code alone is insufficient if it does not map to a
durable state the caller can query. Use stable conflict and precondition
semantics for races; do not overwrite a newer version silently.

## Security implications

An API is a trust boundary. Specify:

- authentication method, credential audience, rotation, and failure behavior;
- authorization by actor, tenant, resource, operation, field, and state;
- canonicalization before signature or policy decisions;
- input size, depth, upload, query, and rate limits;
- protection from injection, SSRF, unsafe parsing, replay, and request
  smuggling where applicable;
- secret and sensitive-data redaction in errors, logs, traces, cursors, and
  examples;
- webhook signature verification, timestamp/replay policy, and sender
  identity;
- audit events for privileged, financial, administrative, and data-export
  actions.

Object-level authorization must run after resolving the requested resource and
before returning it. A predictable identifier is not permission. Escalate
material auth, tenancy, webhook, payment, secret, or untrusted-input changes
through the [composition contract](composition-contracts.md).

## Operational implications

Define:

- deadlines and server-side timeout behavior;
- retryability and client retry guidance without causing amplification;
- rate limits, quotas, concurrency limits, and load-shedding behavior;
- dependency and database budgets for each endpoint;
- health/readiness semantics and whether a dependency is critical or optional;
- rollout, version coexistence, deprecation, and rollback/roll-forward;
- support procedures for stuck operations, duplicate effects, and reconciliation;
- ownership for schema changes, SDKs, documentation, and consumer notices.

An API that returns a useful error but cannot be traced to a request, operation,
dependency, or persisted state is not operable. Do not expose unbounded
diagnostic detail just to aid support.

## Migration and compatibility implications

Use an expand/contract sequence:

1. inventory consumers, traffic, versions, and semantic dependencies;
2. add a compatible field, endpoint, event version, or capability;
3. deploy readers that tolerate old and new forms;
4. dual-read or translate only with explicit disagreement telemetry;
5. migrate producers and clients gradually;
6. measure usage and error behavior during the deprecation window;
7. remove the old contract only after ownership and rollback authority agree.

Avoid dual writes from the API layer when one authoritative owner can emit a
durable change. If a response model changes while old clients remain, keep
stable meanings and use a translation adapter. Test old client/new server,
new client/old server where the deployment strategy allows either pairing.

## Observability implications

Emit structured request and operation telemetry with:

- request, correlation, and causation identifiers;
- endpoint/operation, contract version, client capability, and actor class;
- latency distributions, status/error category, retry attempt, and rate-limit
  outcome;
- resource or operation identifier in a privacy-safe form;
- idempotency key fingerprint and deduplication result where relevant;
- expected version, conflict result, consistency mode, and pending/completed
  status;
- downstream dependency timing and durable side-effect status.

Measure contract errors, authorization denials, duplicate suppression, timeout
rate, retry volume, pagination abuse, operation age, webhook delivery lag,
dead letters, and version usage. Never log raw credentials, signed payloads,
personal data, or unbounded request bodies by default.

## Testing and verification evidence

Required evidence depends on the claim, but commonly includes:

- schema and contract tests for requests, responses, errors, events, and
  version compatibility;
- API tests for authentication, object/property authorization, validation,
  limits, pagination boundaries, and safe errors;
- duplicate and concurrent idempotency tests with the real uniqueness boundary;
- stale-version and conditional-request tests that prove lost updates are
  rejected;
- timeout, retry, cancellation, partial-response, and dependency-malformed
  response tests;
- webhook signature, replay, duplicate, reorder, poison, and restart tests;
- old/new mixed-version and deprecation tests;
- performance/load tests for query complexity, page limits, tail latency, and
  rate-limit behavior;
- observability assertions for correlation, audit, and pending/failed state.

Inspect persisted state and side effects, not only status codes. A static schema
check cannot prove authorization or idempotency. Each verification handoff
should state the contract claim, mechanism, adversarial input or failure,
expected response/state/telemetry, exact procedure, freshness, and limitation;
see the [composition contract](composition-contracts.md).

## Decision output

Record the caller, intent, trust boundary, contract style, inputs/limits,
response states, error semantics, transaction and consistency boundary,
idempotency/concurrency mechanism, compatibility window, security constraints,
operational owner, migration steps, telemetry, alternatives rejected, and
executed or planned evidence. Link to [data access patterns](data-access-patterns.md)
when query shape drives the contract and to [resilience patterns](resilience-patterns.md)
when timeout/retry behavior is part of the promise.
