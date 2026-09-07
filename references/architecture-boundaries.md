# Architecture and boundary patterns

## Purpose

This reference helps an agent choose ownership, dependency, module, layer, and
deployment boundaries for a backend. It is a decision aid, not a mandate to
adopt a named architecture. The target is the minimum sufficient architecture:
the least complex set of boundaries that preserves the required invariants,
allows the required change, and can be operated and verified by the team that
owns it.

Architecture is a set of constraints on change and failure. A diagram alone
does not establish ownership, a transaction boundary, a trust boundary, or a
recoverable operational boundary. Those must be stated and enforced.

## When to load

Load this reference when designing or refactoring module boundaries, layering,
ports and adapters, bounded contexts, monolith decomposition, service seams,
dependency direction, or deployment ownership. Also load it when a proposal
adds a queue, event, service, shared package, database boundary, or abstraction
whose main effect is to change coupling.

Do not load it for a local implementation detail with no ownership, dependency,
failure, compatibility, or transaction consequence. If the dominant question
is domain state, API compatibility, persistence, transactions, consistency, or
concurrency, load the corresponding reference from the
[pattern index](pattern-index.md) as well; this file supplies the boundary
context rather than replacing those decisions.

## Problem and forces

The problem is to put behavior and data behind seams that make the important
changes safe without creating more indirection than the system can justify.
Before selecting a pattern, inspect the current code and deployment rather than
inferring architecture from directory names.

Record the forces that actually apply:

- business ownership and the invariants that must change together;
- dependency direction and the modules that must remain independently
  understandable;
- transaction scope, data locality, and the cost of a remote call;
- failure isolation, availability, latency, and throughput;
- independent deployment or scaling needs;
- team ownership, release cadence, and operational capability;
- trust, privilege, tenant, and sensitive-data boundaries;
- migration compatibility with old callers, schemas, and mixed versions;
- observability, repair, and blast-radius requirements;
- cognitive, runtime, testing, and infrastructure cost.

Separate facts from proposals. A service that might scale independently is a
proposal; measured independent scaling pressure is evidence. A layer that looks
clean is not evidence that it prevents an observed defect.

### Boundary questions that must have explicit answers

For every material seam, identify:

1. Who owns the rule, data, and decision?
2. Which dependencies may cross the seam, in which direction, and through what
   contract?
3. Is the call local or remote? If remote, what are timeout, retry, duplicate,
   ordering, and partial-failure semantics?
4. Which changes must be atomic, and where is the transaction boundary?
5. Which actor is trusted at the seam, and where is authorization enforced?
6. What consistency does a caller receive, and how is staleness or conflict
   exposed?
7. How is the seam observed, migrated, rolled back or repaired?

An unresolved answer is a design risk. Preserve it as an explicit unknown in
the decision handoff rather than filling it with a fashionable pattern.

## Minimum sufficient architecture

Start with a cohesive module or modular monolith unless the forces require a
stronger boundary. A practical minimum often contains:

- modules organized around responsibilities or domain capabilities;
- a clear owner for each invariant and piece of mutable data;
- an application/use-case boundary for orchestration and authorization
  decisions;
- domain code only where rules or state transitions deserve a named owner;
- a persistence adapter when it hides a meaningful storage contract or
  variation, not merely because every table needs a wrapper;
- explicit integration adapters at remote or untrusted boundaries;
- one observable path for errors, latency, and side effects.

This shape can use layers, vertical slices, ports, adapters, or a mixture. The
names are secondary to dependency direction and ownership. Add a boundary only
when it buys one or more of the following:

- an invariant can be enforced in one place;
- a likely change can be isolated;
- a trust or privilege transition can be audited;
- a failure can be contained or recovered independently;
- a team can own and release the unit independently;
- a data or resource contract is materially different;
- a test can exercise a meaningful public seam.

The architecture-change budget includes implementation, cognitive, runtime,
operational, migration, and testing cost. A boundary that buys none of these
benefits is ceremony.

## Candidate patterns and selection gates

Use a small candidate set and reject the rest with reasons. The following
patterns are compatible in many combinations; they are not mutually exclusive.

### Cohesive module or modular monolith

Use when the system benefits from one deployment and local transactions but
needs explicit ownership, dependency direction, or future extraction seams.
Keep module interfaces narrow and make forbidden imports or data access
testable. This is the default for most new work because it preserves locality
while allowing structural discipline.

Do not call a folder hierarchy a modular monolith if any module can freely
write another module's tables, invoke its internals, or bypass its rules.
Shared mutable tables and a shared “common” package that carries business
logic are warning signs, not proof of modularity.

### Layered architecture

Use when the system has stable technical concerns and the layer boundaries
reduce duplication or protect a shared policy. Keep dependencies pointing
toward policy or ownership, and do not force every use case through every
layer.

Reject mandatory controller-service-repository chains when they only rename
data movement, spread one invariant across layers, or make a simple feature
touch many files without a real seam. Vertical slices or cohesive modules may
be clearer for use cases with different data and failure behavior.

### Ports and adapters, hexagonal, clean, or onion architecture

Treat these as a family of dependency-direction techniques, not as a required
number of rings. Use them when core rules must remain independent of transport,
storage, or external systems; when several adapters are real; or when a
long-lived domain contract needs protection from framework churn.

Reject a full port for every trivial library call, an interface that has only
one implementation and no meaningful policy, or a domain core that cannot be
tested without recreating the infrastructure it supposedly excludes. A direct
module boundary can be enough.

### Vertical-slice architecture

Use when features have distinct workflows, data access, and operational
behavior, and localizing a slice reduces cross-cutting coordination. Put the
rules, query shape, endpoint, and tests for a use case near one another while
keeping shared policy explicit.

Reject it when it duplicates authorization, transaction, error, or domain rules
across slices. Share stable policy at a deliberate boundary; do not create
hidden coupling through copy-and-paste.

### Bounded context and anti-corruption layer

Use when terms, invariants, ownership, or models genuinely differ between
subsystems. Translate at the boundary and keep the receiving context's model
under its own control. See [domain modeling](domain-modeling.md) for
aggregate and context questions.

Reject a bounded context label that merely renames technical layers or an
anti-corruption layer that silently copies a foreign model into the local
domain. Translation has a cost and needs a reason such as semantic mismatch,
ownership, or migration isolation.

### Separate service or microservice

Pass this gate only when at least one material force is demonstrated:

- independent deployment is required by ownership or release risk;
- independent scaling is measured or strongly constrained by workload;
- fault isolation has a concrete blast-radius benefit;
- reliability, security, regulatory, or data residency requirements differ;
- a stable bounded context has an owner able to operate it;
- technology isolation provides a specific, measured benefit.

The split must also have an API or event contract, data ownership, timeout and
retry policy, compatibility window, observability, deployment/rollback plan,
and a recovery path for partial completion. Without those, a service split is
usually a distributed monolith: remote calls and operational cost without
independent value.

### Event-driven or asynchronous boundary

Use when decoupled timing, durable work ownership, fan-out, or independent
failure handling is a real requirement. Define delivery, ordering, duplicate,
schema, replay, and poison-message behavior. Load
[transaction patterns](transaction-patterns.md) and the messaging reference
when this boundary carries business effects.

Reject an event or broker between two local operations merely to make a diagram
look decoupled. A direct call or in-process module boundary is safer when the
caller needs immediate success and both operations share a local transaction.

### Decision gates for CQRS and event sourcing

CQRS needs asymmetric read/write models, measured read scaling pressure,
specialized projections, or a meaningful consistency boundary. Otherwise a
single model with well-shaped queries is simpler; see
[data access patterns](data-access-patterns.md).

Event sourcing needs an event history that is itself a domain requirement,
temporal reconstruction, or an event-native model. It adds event schema
evolution, replay, projection rebuilds, storage growth, privacy/deletion, and
debugging obligations. A CRUD system does not justify it merely because events
sound extensible.

## When to use

Use this reference's guidance when the proposed change affects at least one of:

- who owns a business rule or mutable record;
- which dependencies can be called or imported;
- where transactions, trust, or consistency change;
- whether work crosses a process or network boundary;
- deployment, scaling, fault isolation, or operational ownership;
- public compatibility or a migration seam.

Prefer an incremental boundary in a brownfield system. First map current
callers, contracts, database constraints, deployments, tests, and the reason
for an existing mechanism. This is the practical form of Chesterton's Fence:
understand a boundary before removing it.

## When not to use

Do not introduce or expand architecture because:

- a named style is popular or appears more “enterprise”;
- a small CRUD path has no domain complexity, independent scaling, or failure
  boundary;
- an interface only wraps one ORM call without hiding policy or variation;
- a queue replaces a local call without an async requirement;
- a service split preserves a shared database and synchronous call chain;
- CQRS, event sourcing, or a cache is added without an observed driver;
- a generic shared package is used to avoid deciding ownership;
- “future scale” is the only stated reason and no workload or boundary is
  known.

Do not confuse more directories, more processes, or more interfaces with more
modularity. If the proposed design cannot name an invariant, owner, change,
failure, or trust boundary it improves, reject it.

## Alternatives and trade-offs

| Need | Smallest credible choice | Stronger choice when evidence demands it | Main cost |
| --- | --- | --- | --- |
| Keep related rules consistent | Cohesive module and local transaction | Aggregate or explicit domain boundary | More modeling and coordination |
| Separate likely changes | Modular monolith with narrow interfaces | Independently deployed service | Network, compatibility, and operations |
| Isolate infrastructure | Direct adapter in a module | Ports and adapters around a stable core | Indirection and contract maintenance |
| Coordinate background work | In-process task with durable state | Queue and worker with recovery | Delivery, dedupe, and operations |
| Support different read shape | Query object or read query | CQRS projection/read model | Staleness, rebuilds, and dual models |
| Preserve foreign semantics | Explicit mapper | Anti-corruption layer/context boundary | Translation and synchronization |

If two alternatives meet the same invariants, choose the one with lower
total complexity and a reversible migration path. Record why the stronger
option was rejected; otherwise a future reader may mistake it for an omission.

## Failure and integrity implications

Architecture must make failure location and ownership visible. For each
boundary, write the outcome for:

- a timeout before the callee accepts the request;
- a timeout after the callee commits but before the caller receives a response;
- a process crash after local state changes but before a remote effect;
- a duplicate request, event, or retry;
- an old and new version running at the same time;
- a dependency that is slow, malformed, unavailable, or partially degraded.

Local boundaries may share an ACID transaction when the invariant requires it.
Remote boundaries cannot borrow that atomicity; use an explicit protocol and
recovery path. See [transaction patterns](transaction-patterns.md),
[consistency patterns](consistency-patterns.md), and
[concurrency patterns](concurrency-patterns.md) for detailed controls.

Do not claim “exactly once” because a call path has one nominal invocation.
The design must be safe when delivery and completion are observed more than
once. Every cross-boundary effect needs an owner, durable state or replay
strategy, and a way to detect and repair stuck work.

## Security implications

Treat every process, module, queue, database, file, and third-party integration
as a possible trust transition. Identify:

- authentication at the external boundary and service identity at internal
  boundaries;
- authorization by actor, action, resource, tenant, and relevant state;
- object- and property-level access checks, not only route-level checks;
- least-privilege credentials and ownership of secrets;
- input validation and output filtering at trust boundaries;
- injection, SSRF, unsafe deserialization, resource exhaustion, and data
  exfiltration paths;
- whether shared tables, logs, events, caches, or common packages cross tenant
  or sensitivity boundaries.

An internal module is not trusted merely because it is in the same repository.
When the design changes authentication, authorization, tenancy, sensitive data,
webhooks, payments, external URL fetching, file parsing, privileged actions,
or service-to-service trust, attach the security handoff described in the
[composition contract](composition-contracts.md). This reference surfaces
constraints; it does not certify the security design.

## Operational implications

Every new boundary creates an owner and an operational contract. Specify:

- deployment order and mixed-version compatibility;
- health versus readiness behavior;
- timeouts, retry budgets, backpressure, load shedding, and dependency limits;
- logs, metrics, traces, correlation/causation identifiers, and ownership;
- dashboards and alerts that distinguish user failure from dependency failure;
- rollback versus roll-forward when data or messages have crossed the seam;
- how operators drain queues, replay work, repair data, and confirm recovery;
- capacity assumptions, cost limits, and the failure blast radius.

An architecture is not ready if its operator cannot determine which boundary
failed, whether state committed, what work is safe to replay, or how to stop
amplification. Link the evidence request to the operational owner, not only to
the implementation team.

## Migration and compatibility implications

Prefer branch-by-abstraction, expand/contract, and an end-to-end vertical slice
over a simultaneous rewrite. A boundary migration should normally proceed as:

1. characterize current behavior and contracts;
2. introduce a compatible seam or adapter;
3. move one coherent use case and its data ownership;
4. observe old and new paths separately;
5. backfill or reconcile with checkpoints;
6. remove the old path only after consumers, recovery, and rollback windows are
   closed.

Avoid dual writes unless ownership, ordering, reconciliation, failure recovery,
and an exit plan are explicit. During mixed versions, additive fields,
tolerant readers, versioned events, and compatible defaults are safer than a
flag day. A service extraction that leaves both services writing the same
business table has not completed an ownership migration.

## Observability implications

For every boundary, emit enough structured context to answer:

- which request, command, event, or workflow instance crossed it;
- which owner and version handled it;
- what latency, outcome, retry attempt, and dependency state occurred;
- which data version, idempotency key, causation ID, and correlation ID apply;
- whether the result is committed, pending, rejected, stale, or unknown;
- where a repair or compensation can be found.

Measure boundary health rather than only process health: dependency latency and
error rate, queue age, retry volume, dead letters, projection lag, contract
errors, authorization denials, and reconciliation drift. Do not put secrets or
sensitive payloads in traces or logs; use redaction and stable opaque IDs.

## Testing and verification evidence

A boundary decision needs evidence proportionate to its risk. Useful evidence
includes:

- architecture tests for forbidden dependencies, ownership, and data access;
- contract tests for public calls, events, errors, versions, and defaults;
- integration tests through the real persistence or messaging boundary;
- failure injection for timeout, crash, duplicate, reorder, and partial
  completion;
- migration tests with old/new versions, interrupted backfills, and recovery;
- authorization and tenant-isolation tests at the actual resource boundary;
- concurrency tests where multiple callers can cross the seam;
- operational smoke tests for startup, readiness, telemetry, drain, replay, and
  repair;
- measured load or query evidence when scaling or performance is part of the
  argument.

Static diagrams and passing unit tests do not prove deployment independence,
failure isolation, or compatibility. Distinguish planned evidence from
executed evidence and report limitations. The verification handoff should name
the claim, mechanism, scenario, expected state/effects, telemetry, and command
or procedure, as described in the [composition contract](composition-contracts.md).

## Compact decision procedure

Use this sequence before recommending a boundary:

1. State the problem and invariants in domain terms.
2. Map current ownership, callers, data, transactions, trust, and failure.
3. List the forces that make a stronger seam valuable.
4. Compare the smallest local design with only the stronger candidates that
   address those forces.
5. Reject candidates whose costs are not paid by a stated requirement.
6. Define transaction, consistency, retry, compatibility, security,
   observability, migration, and recovery semantics.
7. Name the first coherent slice and the evidence that can falsify the choice.

Cross-family decisions should be recorded using the decision record in
SKILL.md and the [composition contract](composition-contracts.md); do not
replace reasoning with a pattern name.
