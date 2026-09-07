# Idempotency patterns

Idempotency means that repeating the same logical operation does not create an
additional business effect. It is a contract about an operation and its side
effects, not a promise that every request returns the same bytes forever. It is
one of the main defenses against timeouts, duplicate messages, webhook redelivery,
client retries, and process crashes, but it must be scoped, durable, and enforced
at the authoritative boundary.

## Problem and forces

Distributed callers cannot reliably distinguish “the operation did not run” from
“it ran and the response was lost.” At-least-once delivery and concurrent retries
therefore make duplicate execution normal. Forces include:

- the business effect that must occur at most once or be safely repeated;
- caller/principal, tenant, resource, operation, and API-version scope;
- how long retries, delayed messages, replays, and fraud attempts remain possible;
- whether the result can be stored or recomputed;
- the transaction boundary between the idempotency record and the effect;
- concurrent requests using the same or different keys; and
- recovery after a crash between an external effect and local recording.

First make the domain operation safe: a unique business constraint, state
transition check, conditional update, or provider-side idempotency contract may
be stronger than a generic request table. Then add an idempotency mechanism where
the caller and failure model require it.

## Key scope, digest, and result contract

An idempotency key is not globally unique by itself. Its identity should be a
server-defined tuple such as authenticated principal or tenant, operation name,
resource/business scope, API contract version, and the caller-provided key. The
right scope prevents one tenant from replaying or colliding with another tenant's
operation and avoids treating the same random string used for two different
operations as one action.

Store a canonical request digest with the key. Canonicalization must define field
ordering, omitted versus explicit defaults, numeric and text normalization, and
which headers or contextual fields affect the operation. A repeated key with a
different digest is a conflict, not a fresh request. A digest is an integrity and
conflict check, not authentication; authorize the current principal and bind the
scope server-side. Do not put secrets or raw personal data in keys. If an
untrusted caller can choose a high-cardinality key indefinitely, apply quotas and
retention controls.

Retain the key and result for at least the credible retry/replay window, provider
window, message redelivery period, and fraud/incident investigation requirement.
Expiry is a semantic decision: after expiry, the same key may execute again only
if the business contract permits it. Do not choose a short TTL just to reduce
storage and then claim at-most-once behavior.

The response contract matters. Where safe, return the original result or a stable
resource/operation reference. For an in-progress duplicate, return a documented
conflict, accepted/pollable status, or wait within the caller deadline. Do not
run the effect a second time merely because the first response is unavailable.

## Durable implementation and concurrency

A robust request flow is:

1. authenticate and authorize the request;
2. canonicalize the operation input and derive its server-scoped identity/digest;
3. atomically insert or claim the key under a unique constraint;
4. return the recorded result for a completed matching entry, reject a digest
   conflict, and apply an explicit in-progress policy for a concurrent claim;
5. perform the effect within the strongest available transaction boundary;
6. persist the result/resource reference and terminal state before acknowledging
   success; and
7. recover abandoned in-progress entries with a bounded lease or reconciliation
   process, never by assuming a process lock survived a crash.

For a local database effect, the idempotency record, business state, and unique
business constraint can often be committed atomically. For a remote effect,
there is no automatic atomicity between the remote provider and the local record.
Use the provider's idempotency contract, a durable operation state plus polling,
an outbox/inbox workflow, or reconciliation. See [messaging patterns](messaging-patterns.md)
and [transaction patterns](transaction-patterns.md) for the boundary choice.

The concurrency primitive must be durable: unique index/insert, compare-and-swap,
transactional lock, or provider-side token. A process-local mutex only serializes
one instance. A check-then-insert race is not idempotency. If a lease is used,
define expiry, fencing, and what happens when the old holder resumes.

## When to use and when not to use

Use idempotency for mutating APIs, payments, order creation, resource allocation,
webhooks, retried jobs, outbox publishers, and any consumer whose duplicate
delivery can duplicate a non-commutative effect. Propagate a stable operation or
message identity through retries and hops, while preserving each boundary's
scope.

Do not add a generic key table to pure reads or operations that have no stable
logical identity. Do not use an idempotency key as a substitute for authorization,
optimistic concurrency, a unique business constraint, or a correct transaction
boundary. Do not deduplicate all events by a globally unique string if replay,
tenant scope, or event version changes the meaning. Do not silently treat a
changed request body as the old operation. Do not delete records as a “cleanup”
without proving the replay window has closed.

Alternatives or complements include a unique constraint, conditional state
transition, commutative update, provider-side idempotency, operation status
resource, durable inbox, or manual reconciliation. The minimum sufficient choice
is the strongest invariant at the smallest authoritative boundary.

## Failure modes and containment

| Failure | Result | Containment |
|---|---|---|
| Same key with different request | ambiguous intent or privilege confusion | canonical digest conflict and audit-safe rejection |
| Two first requests race | duplicate work/effect | atomic claim/unique constraint and explicit in-progress response |
| Crash after effect before record | retry repeats effect | same transaction/provider token/outbox or reconciliation |
| Crash after claim before effect | key stuck processing | lease/checkpoint/recovery state and bounded takeover |
| Response lost after commit | caller retries | return stored result or operation status |
| Key expires during delayed replay | duplicate business action | retention based on actual replay window and business invariant |
| Scope too broad | cross-tenant collision or replay | principal/tenant/operation/resource scope enforced server-side |
| Scope too narrow | duplicate effect across clients/hops | propagate stable business operation identity |
| Dedup store unavailable | unsafe write or outage | fail closed, durable fallback, or explicit non-idempotent mode |
| External provider duplicates | local record says once, provider did twice | provider token, provider reconciliation, compensating process |
| Key flooding | storage/resource exhaustion | quotas, auth-bound limits, bounded payload/digest, retention controls |
| Poisoned result replay | wrong or sensitive response repeated | validate stored result, encrypt/redact, version response contract |

Exactly-once business behavior is not implied by a key. It is proven only across
the boundaries that participate in the claim. A local unique constraint can prove
one narrow effect; it cannot prove an email, payment, broker publication, and
local write all happened once without a corresponding external protocol.

## Security implications

Authorize before returning a previously stored result, and ensure the stored
result is bound to the same principal/tenant and resource scope. Treat keys,
digests, operation IDs, and replay endpoints as attacker-controlled inputs. Use
constant-time or safe comparisons where appropriate, limit length and cardinality,
protect records at rest, and redact request bodies/results from logs. Prevent
cross-tenant lookup, key enumeration, unauthorized polling, replay after account
revocation, and abuse of long retention. A digest must not be treated as a
signature; use authenticated context and message verification where required.
Escalate payments, privileged actions, webhook verification, and sensitive data
through [composition contracts](composition-contracts.md).

## Operational implications

Operate idempotency storage as business state: capacity, retention, encryption,
partitioning, backup, cleanup, and recovery need owners. Measure in-progress
age, conflict rate, duplicate-hit rate, claim contention, storage growth, lease
takeovers, reconciliation backlog, and provider mismatch. Provide a safe query
and repair path that does not expose payloads or allow arbitrary replay. Document
how operators recover abandoned entries and decide whether a remote effect
actually happened before retrying.

## Migration and compatibility implications

Adding idempotency to an existing write API changes duplicate behavior and may
need a compatibility window. Introduce storage and telemetry first, then accept
keys for new clients or a versioned operation contract; retain the old unsafe path
only with explicit rate/deadline controls and no false guarantee. Mixed client
versions must agree on canonicalization, response semantics, scope, and retention.

If a message or API version changes the logical operation, include the version in
the scope or define a migration mapping; never reuse a key under a different
meaning. Backfill existing operations only from authoritative identifiers and
reconcile ambiguous historical effects before enabling automatic retries. Schema
and retention changes should follow [migration patterns](migration-patterns.md).

## Observability implications

Propagate an operation ID and correlation/causation IDs, but log only scoped,
redacted identifiers. Record key claim outcome, digest conflict, duplicate hit,
in-progress response, terminal status, attempt number, lease age, effect/provider
reference, and reconciliation result. Distinguish a legitimate duplicate from
an attack or client bug. Trace the same logical operation across retries without
counting every attempt as a new business request; report both request attempts
and unique operations.

## Testing implications

Test sequential and concurrent identical requests, same key/different body,
different tenants/scope, response loss and retry, crash at each claim/effect/
record boundary, lease expiry and takeover, dedup-store outage, provider timeout
and ambiguous commit, expiry, replay, malformed input, authorization changes,
and storage cleanup. Use real uniqueness/transaction behavior for integration
tests; mocks cannot prove race safety. Assert one durable business effect, stable
result semantics, safe in-progress behavior, correct telemetry, and no cross-
tenant read. For consumers, combine duplicate/out-of-order delivery tests with
the [messaging patterns](messaging-patterns.md) failure cases.

## Evidence requirements

Before recommending idempotency, name the logical operation, effect invariant,
key scope, canonicalization/digest rule, retention window, concurrent-claim
mechanism, external-effect boundary, and recovery owner. Evidence should include:

- a unique/atomic concurrent-claim test that produces one intended effect;
- same-key/same-input replay and same-key/different-input conflict results;
- crash or fault-injection results for every effect/record ordering;
- provider or downstream duplicate behavior and reconciliation evidence;
- expiry/retention, restart/takeover, storage outage, and abuse-limit tests;
- mixed-version contract evidence for key/digest/response semantics; and
- current metrics and an operator procedure for ambiguous outcomes.

A table with an idempotency key column is not proof. If the external effect,
concurrency race, or replay window is untested, state the guarantee as partial
and keep the unresolved boundary visible.
