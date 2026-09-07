# Testing and adversarial verification patterns

Testing is evidence for an architecture claim, not a ceremony attached after
implementation. This reference routes verification by invariant, boundary,
failure mode, and evidence freshness. It complements the architecture
decision record described in [`decision-matrix.md`](decision-matrix.md) and
does not claim to execute the separate verification or security capabilities.

## Invariant-first workflow

Begin with the behavior that must remain true, then choose the smallest test
that could disprove it. For each important flow, make these facts explicit:

1. **Invariant:** the condition that must hold, such as “a payment is captured
   at most once” or “a user cannot read another tenant's object.”
2. **Boundary:** the transaction, process, service, queue, database, trust,
   API, or version boundary where the invariant can be violated.
3. **Adversary or failure:** duplicate delivery, crash, timeout, race, malformed
   input, stale version, partial migration, or hostile identifier.
4. **Oracle:** the observable result that distinguishes safe behavior from a
   plausible but wrong result.
5. **Evidence scope:** artifact, build/configuration, dataset, environment,
   and test run that support the claim.

An assertion about a log line, response code, or mock call is not an oracle for
data integrity unless it is connected to the durable state and user-visible
semantics. Test the invariant at the owner boundary, not only in a caller's
unit test.

## Evidence levels and freshness

Use the least expensive level that can falsify the claim, then add boundary
tests where the risk warrants it:

| Evidence level | Can establish | Cannot establish alone |
| --- | --- | --- |
| Static/schema/architecture check | Required fields, links, forbidden constructs, dependency direction | Runtime authz, timing, concurrency, deployment, or recovery behavior |
| Unit/property test | Local state rules, parsers, pure policies, invariant examples | Real transaction, broker, database, network, or version interaction |
| Contract/API test | Request/response and event compatibility across versions | Data durability, queue recovery, or downstream operational health |
| Integration test | Boundary behavior with real or faithful dependencies | Production scale, rare races, and all failure timing unless injected |
| Concurrency/failure-injection test | Race, duplicate, timeout, crash, rollback, and recovery semantics | Unmeasured production capacity or a different deployment topology |
| Migration/replay test | Expand/contract, backfill, resume, old/new coexistence, projection rebuild | Safety of untested live data or operator execution |
| Runtime/load/operational exercise | Capacity, SLO, saturation, alert, and runbook claims for the exercised environment | A guarantee outside its workload, configuration, or freshness window |

Evidence is fresh only when the tested artifact, configuration, schema,
dependencies, and relevant assumptions match the claim. Record a content
fingerprint or immutable build identifier with material verification. A
material implementation, schema, policy, deployment, or harness change makes
prior evidence stale; rerun the focused tests and the credible regression
surface. Never convert an old green result into current proof by narration.

## Pattern-to-test selection

The following matrix names the minimum failure surface. Add tests for the
actual invariant and do not omit a row merely because a framework promises a
default behavior.

| Pattern or boundary | Required tests | Adversarial cases and oracle |
| --- | --- | --- |
| Local transaction or Unit of Work | Commit, rollback, constraint failure, nested/error path, transaction scope | Crash or exception after each write; no partial durable state and no hidden commit |
| Outbox or inbox | Atomic write plus pending record, publisher restart, consumer deduplication, poison handling | Commit succeeds while broker call fails; replay publishes/consumes safely and backlog is visible |
| Idempotency key or idempotent consumer | Same key repeated, concurrent same key, different payload with same key, expiry semantics | Duplicate request/message after timeout; at most one effect or explicit conflict, never two silent effects |
| Retry, timeout, circuit, or fallback | Transient failure, permanent failure, exhaustion, backoff/jitter, cancellation, budget propagation | Layered retries under outage; attempts remain bounded and load does not amplify beyond policy |
| Optimistic/pessimistic concurrency | Stale version, conflicting updates, lock timeout/deadlock, retry or user conflict path | Two simultaneous writers; lost update is rejected or merged according to the declared invariant |
| Cache or materialized view | Miss, hit, stale, invalidation, unavailable cache, rebuild, stampede control | Cache disappears or serves stale data; source of truth remains correct and refresh is bounded |
| API or webhook | Schema validation, authn/authz, error contract, pagination, idempotency, compatibility, signature/replay | Changed object/tenant/property ID, malformed body, old client with new server, duplicate and reordered delivery |
| Queue or event workflow | Duplicate, order policy, visibility timeout, dead-letter, restart, schema version, drain/replay | Poison message, broker outage, consumer crash after effect, old/new event coexistence; no silent loss |
| Migration or backfill | Expand/contract, checkpoint, resume, rollback or forward repair, dual-read compatibility, old writers | Interrupt every phase, mixed versions, partial batch, duplicate backfill, lagging replica; invariant remains true |
| Authentication and authorization | Token/channel validation, action/object/property/tenant policy, denial behavior, audit/redaction | Forged claims, altered identifier, cross-tenant object, direct service access, expired credential, low-privilege worker |
| Resource and performance boundary | Limit, quota, timeout, queue/backpressure, representative load, tail latency, saturation | 10× traffic, oversized/deep input, slow dependency, cache cold start, retry storm; system sheds safely |
| Observability and recovery | Context propagation, metric labels, redaction, SLI, alert, runbook action | Failure and recovery events can be correlated without secrets; alert is actionable and outcome is verified |

These tests should observe durable state, emitted outcomes, and bounded
resource use. A mock that always succeeds cannot verify timeout, ordering,
transaction, authorization, or retry claims.

## Adversarial verification questions

For each significant flow, attempt to disprove the design with the relevant
questions:

- What if the process crashes after the database commits but before the broker
  call, response, acknowledgement, or cache update?
- What if a network timeout hides a remote commit and the caller retries?
- What if the broker redelivers, reorders, delays, or corrupts a message?
- What if two requests arrive simultaneously with the same or conflicting
  state?
- What if a dependency becomes slow, rate-limits, returns malformed data, or
  remains unavailable until retry exhaustion?
- What if the cache disappears, returns stale data, or all keys expire at once?
- What if a malicious client changes an object ID, tenant, property, URL,
  pagination cursor, or role claim?
- What if old and new clients, services, schemas, or event versions coexist?
- What if a migration or backfill stops halfway and restarts twice?
- What if traffic, payload size, fan-out, queue depth, or tenant skew increases
  tenfold?
- What if retry traffic amplifies the original outage or a dead-letter replay
  repeats a privileged effect?

Each question needs an oracle: a denied access, one durable effect, an explicit
conflict, bounded attempts, a durable pending state, a resumed checkpoint, an
alert, or another observable result. “The test did not throw” is not an oracle.

## Harness integrity and known-bad validation

A test harness can lie through weak assertions, skipped fixtures, permissive
timeouts, or a broken mutation path. Treat the harness as a system under test.
For a deterministic validation package, maintain both a known-good fixture and
controlled known-bad variants. The validator must pass the good fixture and
reject each bad variant for the intended reason. A bad variant must be
isolated from the real artifact so the validation run cannot damage the
working package.

Harness checks should include:

- remove or invert a critical assertion and prove the test fails;
- alter a required schema field, link, trigger, rejection rule, or anti-pattern
  entry and prove the validator reports the right defect;
- ensure fixture discovery does not silently skip files, tests, or malformed
  cases;
- use fixed seeds, controlled clocks, bounded polling, and explicit cleanup;
- fail on swallowed exceptions, unexpected retries, leaked resources, and
  unhandled task failures;
- capture the actual artifact fingerprint, command, environment, and result;
  and
- rerun the relevant validator after every material harness or artifact change.

For concurrency and failure injection, control the interleaving or record it
so a failure can be reproduced. Prefer barriers, deterministic schedulers,
fault hooks, and unique isolated resources to arbitrary sleeps. A flaky test
is evidence that the harness or the system has an unresolved timing boundary,
not permission to increase a timeout until it passes.

## API, migration, replay, and compatibility evidence

API tests must cover valid and invalid inputs, authorization boundaries, stable
error shapes, pagination limits, conditional or versioned writes, idempotency,
and old-client/new-server plus new-client/old-server compatibility where the
deployment model allows version skew. Test that sensitive fields cannot be
read or mass-assigned merely because they appear in a serialized object.

Migration tests must use representative old data, nulls, duplicates, large
partitions, and unexpected enum or schema values. Exercise expand, backfill,
cutover, cleanup, pause, resume, rollback or forward repair, and concurrent
writes. A migration that succeeds once on an empty database is not migration
evidence.

Replay tests must distinguish a diagnostic replay from a business retry. Give
each event its original identity and causation, then verify idempotency,
authorization, ordering policy, and privacy/deletion behavior. Do not replay
production-sensitive data into an uncontrolled fixture or treat a successful
publish as proof of a successful consumer effect.

## Security and observability tests

Security tests should target the owner boundary: invalid credentials, wrong
audience, expired identity, altered object and tenant IDs, unauthorized
properties, direct internal calls, SSRF destinations, injection payloads,
oversized inputs, rate exhaustion, and secret/log redaction. Negative tests
are first-class evidence; a test that only proves an authorized admin path is
not tenant isolation proof. Use the dedicated security handoff when the
thresholds in [`security-boundaries.md`](security-boundaries.md) are crossed.

Observability tests should verify request/trace/correlation/causation
propagation through retries and async delivery, bounded metric labels,
redaction, distinct duplicate/timeout/unknown outcomes, useful latency and
queue metrics, and alert/runbook behavior. Verify the recovery effect, not
just that a notification was emitted. The operational signal contract is in
[`observability-patterns.md`](observability-patterns.md).

## Test selection and completion claims

Use a small evidence ledger for each architecture claim. Its fields are
observable facts rather than a blank form:

| Field | Required content |
| --- | --- |
| Claim | One falsifiable statement about behavior or readiness |
| Invariant | The state or boundary that must remain true |
| Evidence command or run | Exact test, validator, workload, or inspection that ran |
| Artifact identity | Build, commit, fingerprint, schema, and configuration scope |
| Result | Pass, fail, blocked, or unknown with the relevant output |
| Limits | Unexercised topology, scale, failure timing, or authority |
| Next action | Focused rerun, repair, specialist review, or explicit acceptance |

Do not claim “production-ready,” “secure,” “exactly once,” “no data loss,” or
“race-free” from a happy-path unit suite. The claim must match the evidence
level and include unresolved risks. Documentation can specify the required
test; it cannot report that the test passed without a run.

## Composition boundary

Pass selected patterns, invariants, failure scenarios, test oracles, and
evidence freshness requirements to `verification-loop-vNext` when current
runtime or artifact verification is needed. Keep implementation execution in
the implementation engineering capability and security review in the security
capability. The shared ownership and handoff rules are in
[`composition-contracts.md`](composition-contracts.md). This reference
strengthens a verification request; it does not self-approve the package or
replace an independent critic.
