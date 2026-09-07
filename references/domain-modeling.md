# Domain modeling and state ownership

## Purpose

This reference helps an agent decide where business rules, state transitions,
policies, and domain vocabulary should live. It covers entities, value objects,
aggregates, services, events, factories, specifications, repositories,
bounded contexts, and anti-corruption layers without treating Domain-Driven
Design ceremony as a default.

The goal is explicit ownership of invariants. A domain model is useful when it
makes an illegal state harder to create, makes a rule easier to change, or
makes a business decision observable and testable. A data structure with
business nouns is not automatically a domain model.

## When to load

Load this reference when a change introduces or modifies business rules,
lifecycles, state machines, policies, aggregates, domain events, bounded
contexts, or ownership of mutable domain state. Also load it when deciding
whether a CRUD flow needs a richer model or whether a proposed DDD pattern is
ceremony.

Do not load it for a pure projection, a mechanical schema mapping, or a
transport-only validation change unless the change alters a domain invariant.
Combine it with [architecture boundaries](architecture-boundaries.md) for
module ownership, [transaction patterns](transaction-patterns.md) for atomic
effects, and [concurrency patterns](concurrency-patterns.md) for simultaneous
commands.

## Problem and forces

The problem is to express rules and state transitions in an owner that callers
cannot casually bypass. The model must remain understandable while satisfying
the forces that actually exist:

- number and volatility of business rules;
- invariants that span fields, records, or external participants;
- lifecycle complexity and illegal transitions;
- frequency and shape of concurrent commands;
- data ownership and transaction locality;
- need for audit history, temporal reconstruction, or domain events;
- integration with a model whose terms or rules differ;
- performance, query shape, and persistence constraints;
- team vocabulary, cognitive load, and expected change;
- authorization, tenant, privacy, and audit requirements.

Start with examples and invariants, not pattern names. State facts such as
“a captured payment cannot be captured again” or “a reservation expires before
allocation,” then identify the smallest owner capable of enforcing them.

### Domain questions that must have explicit answers

For each important rule, identify:

1. Which state and facts does the rule inspect?
2. Which operation is allowed to change them?
3. What must be true before and after the operation?
4. Can one local transaction enforce the rule?
5. What happens when two commands race or a command is retried?
6. Who is authorized to request the change?
7. Which side effects are immediate, deferred, duplicate-safe, or compensatable?
8. How can a caller, operator, or verifier observe and repair a failure?

If a rule crosses an independently owned process, it is not made atomic by
calling a remote service from inside a method. Move to the transaction and
consistency references and name the protocol.

## Minimum domain model

Use the least modeling that gives a single, testable home to the actual rules.
For a simple CRUD resource, that may be:

- a validated input type;
- database constraints and a small application operation;
- a state transition guard;
- a direct query with explicit authorization.

Add domain concepts when they buy clarity or protection:

- a value object for a value with validation, equality, or behavior;
- an entity when identity and lifecycle matter;
- an aggregate root when several pieces of state must change under one
  consistency boundary;
- a policy or specification when a rule is named, reused, or independently
  tested;
- a domain service when a rule is domain-owned but does not naturally belong
  to one entity or aggregate;
- an application service for use-case sequencing, authorization orchestration,
  transactions, and integration calls;
- a repository when persistence semantics must be hidden behind a domain-owned
  collection boundary;
- a domain event when a meaningful state transition must be handled by
  another domain operation or durable integration;
- a factory when creation has nontrivial invariants or multiple valid shapes.

The application service should coordinate; it should not become a second
domain model that scatters decisions across controllers, repositories, and
integration code.

## Pattern selection

### Entities and value objects

Use an entity when identity persists through attribute changes and behavior is
about its lifecycle. Use a value object when value, not identity, is the
meaning: it should be immutable where practical and validate its own
representation and operations.

Do not make every database row an entity or every scalar a class. A value
object that only forwards a primitive adds ceremony. An entity with setters for
every field makes invalid transitions easy.

### Aggregates and aggregate roots

Use an aggregate to define a consistency and transaction boundary around state
that must obey invariants together. Let an aggregate root control changes to
its internal members. Reference another aggregate by identity rather than
loading a graph that is not required for the command.

An aggregate is a business boundary, not automatically a table, object graph,
or one-to-one relation. Keep it small enough for common commands to complete
within a bounded transaction and for concurrent updates to remain possible.
Split it when unrelated rules, contention, ownership, or lifecycle make the
boundary expensive.

Do not use an aggregate to solve a query-shape problem, to justify a giant
object graph, or to force unrelated records into one transaction. A database
constraint may be the better final guard for uniqueness or non-negativity.

### Domain services and application services

Use a domain service for a domain decision that needs multiple domain
concepts but has no natural single owner, such as a pricing policy involving
several value objects. Keep it deterministic and domain-focused where
possible.

Use an application service for a use case: load state, authorize the actor,
invoke domain behavior, persist the result, and publish or schedule effects.
It owns orchestration and transaction placement, not the meaning of the rule.

Do not create a service class for every noun or every CRUD endpoint. A service
that merely forwards to one repository is indirection unless it is an
intentional use-case boundary, authorization seam, or future variation point.

### Policies and specifications

Use a policy or specification when a business decision has a name, multiple
callers, a changing rule, or useful independent evidence. Keep the input and
decision semantics clear, especially around missing, stale, or unauthorized
data.

Do not use a generic specification abstraction to hide arbitrary query
language or to build a boolean expression tree no one can explain. A focused
function or query object is often the smaller alternative.

### Factories

Use a factory when construction must choose a valid subtype, normalize a
complex value, apply a creation policy, or produce an aggregate with required
initial state. Keep persistence hydration distinct when stored historical data
may not satisfy today's creation rules.

Do not add factories for constructors that have no invariant or variation.
Factories must not silently call remote systems or perform unbounded work while
pretending to be pure creation.

### Domain events

Use a domain event to name a meaningful fact after a state transition, such as
OrderPlaced or ReservationExpired. Events can update local policies,
projections, or integrations, but their timing and durability must be explicit.

If an external effect must not be lost after the owning transaction commits,
record an integration event or outbox entry in the same local transaction and
relay it afterward; see [transaction patterns](transaction-patterns.md).
Do not publish from a pre-commit in-memory hook and assume the event reflects
durable state. Do not use events to hide a synchronous invariant that must be
checked before the command succeeds.

### Repositories

Use a repository when the domain needs a persistence-independent collection
boundary, when aggregate loading/saving has meaningful semantics, or when
ownership and transaction behavior must be kept out of callers.

Do not create one repository per table by reflex. A repository that exposes
every ORM method, leaks query objects, or cannot state its consistency and
transaction semantics is a persistence wrapper, not a useful domain boundary.
See [data access patterns](data-access-patterns.md) for the detailed
repository/ORM trade-off.

### Bounded contexts and anti-corruption layers

Use a bounded context when the same term, identity, or workflow has different
meaning, invariants, ownership, or release pressure in different parts of the
system. Use an anti-corruption layer to translate foreign concepts rather than
letting a remote schema become the local domain model.

Do not declare contexts solely because teams use different folders or because a
system has many tables. A translation layer has maintenance cost and can
preserve a bad foreign model if its mapping is not explicit.

## Domain ceremony restraint

Use the following diagnostic before adding a DDD construct:

- What concrete invariant or change does it protect?
- Which caller currently bypasses or duplicates the rule?
- What is the smallest owner that makes the bypass difficult?
- Does the construct reduce or increase the number of concepts a maintainer
  must hold in mind?
- Can the construct be tested through a stable boundary?

Prefer no aggregate, repository, event, factory, or domain service when a
single local validation plus a database constraint already enforces the rule.
Prefer an aggregate or explicit policy when rules genuinely exist; an anemic
model is not virtuous if callers can create impossible states. The choice is
about behavior and invariants, not about maximizing object count.

## When to use

Use domain modeling when:

- a business rule is duplicated or bypassed by multiple entry points;
- legal and illegal state transitions need a single owner;
- a command must protect an invariant across several fields or records;
- domain terms differ across integrations or teams;
- audit, policy, or temporal behavior is part of the product;
- concurrency and retries make “just update the row” unsafe;
- a change needs a durable boundary between business decisions and transport or
  persistence.

For a CRUD path, start with the smallest model and add behavior when a
specific rule demands it. For a complex path, state the invariant first and
let the model follow.

## When not to use

Do not use full DDD ceremony when:

- the resource is CRUD with no meaningful domain rule beyond schema validation;
- the proposed entity only mirrors a table and has no behavior;
- a repository only renames ORM calls;
- a domain event is used as an in-process callback for an immediate invariant;
- a value object adds no validation, semantics, or safety;
- an aggregate would load unrelated records and create a hot contention point;
- a bounded context or anti-corruption layer merely renames a DTO;
- a factory hides a trivial constructor;
- the real problem is query performance, API evolution, or deployment
  isolation rather than domain ownership.

Reject both cargo-cult DDD and cargo-cult anemic models. The correct test is
whether the chosen owner makes the invariant clear, enforceable, and
verifiable.

## Alternatives and trade-offs

| Problem | Smallest credible choice | Richer choice when justified | Main cost |
| --- | --- | --- | --- |
| Validate one value | Boundary validation and database constraint | Value object with behavior | More types and mapping |
| Protect a lifecycle | Guarded application operation | Entity or aggregate state machine | Model and persistence coordination |
| Coordinate one use case | Application function/service | Domain service plus application service | More ownership vocabulary |
| Persist an owned cluster | Direct data access in one transaction | Repository around an aggregate | Abstraction and loading rules |
| Notify another action | Direct call when atomic and local | Domain event plus outbox/consumer | Duplication, lag, and recovery |
| Translate foreign semantics | Explicit mapper | Anti-corruption layer/context | Translation drift and testing |

Select the richer option only when the smaller one cannot preserve an
invariant, isolate a change, or produce the required evidence. Keep the chosen
model compatible with actual query and migration needs; a pure conceptual
model that cannot be persisted or operated is incomplete.

## Failure and integrity implications

For each command, describe the state before and after, the invariant that must
hold, and the behavior when:

- validation fails before a write;
- the database commits only part of a multi-write operation;
- a process crashes after state changes but before an event or external call;
- the command is retried with the same or a different idempotency key;
- two commands race for the same aggregate or unique resource;
- an event arrives late, twice, or out of order;
- a related aggregate or foreign context is unavailable or stale.

An aggregate boundary can protect only state that participates in its
transaction. Cross-aggregate or cross-service rules require a database
constraint, explicit coordination, a consistency contract, or a compensating
workflow. Do not claim that domain language alone makes a distributed rule
atomic.

Use state transitions with explicit allowed edges and terminal behavior. Keep
illegal transitions rejected rather than silently normalized. If compensation
is possible but not reversal, name the user-visible state and the operator
repair path.

## Security implications

Domain rules do not replace authorization. A valid command by one actor may be
invalid for another actor, tenant, resource owner, or lifecycle state. Enforce
authorization on the actor, action, resource, tenant, and relevant properties
at the application boundary, then enforce domain invariants below it.

Consider:

- whether identity is stable and unforgeable across contexts;
- whether a tenant or resource ID supplied by a caller is scoped to the actor;
- whether policies leak sensitive existence or pricing information;
- whether domain events contain personal, payment, secret, or tenant data;
- whether replay, export, or projection rebuild violates deletion or retention
  rules;
- whether a factory or deserializer accepts untrusted types or state.

When the model affects authentication, authorization, tenancy, secrets,
payments, privileged operations, sensitive events, or external trust, use the
security handoff in the [composition contract](composition-contracts.md).
This reference defines prompts and invariants, not a final security review.

## Operational implications

Every important domain transition needs an operational story:

- how a stuck or invalid transition is detected;
- how a failed event, projection, or compensation is retried or repaired;
- which state is authoritative when a projection disagrees;
- how operators inspect a history without exposing sensitive data;
- how a manual repair preserves invariants and auditability;
- how a new rule behaves during mixed-version deployment;
- how contention, aggregate size, and hot keys affect capacity.

Do not make the domain layer swallow integration failures to preserve a
“successful” command. Return a durable pending or failed state when that is
the real result, and make recovery observable.

## Migration and compatibility implications

Evolve the model by preserving old behavior while introducing the new owner:

1. inventory current states, callers, stored values, and bypass paths;
2. encode the invariant in a compatible guard or database constraint;
3. migrate one command or entry point to the new owner;
4. backfill or normalize data with an idempotent, checkpointed procedure;
5. compare old and new decisions where safe and reconcile differences;
6. remove duplicate rule paths only after clients and data are covered.

Do not apply today's creation factory blindly to historical records. Version
stored state or event schemas when semantics change. During mixed versions,
accept additive fields and preserve legal old transitions until the rollout
closes. If an event name or state meaning changes, make the compatibility and
replay plan explicit.

## Observability implications

Observe decisions and transitions, not only exceptions. For important commands,
capture structured fields such as:

- aggregate or resource identity in a privacy-safe form;
- actor, tenant, command, state-before, state-after, and rule outcome;
- version or expected revision used for concurrency;
- idempotency key, correlation ID, causation ID, and retry attempt;
- event/outbox ID and publication or projection status;
- rejection reason categories without leaking sensitive policy details;
- duration and dependency outcomes.

Metrics should expose transition failure rate, conflict rate, duplicate
suppression, pending workflow age, projection lag, compensation rate, and
repair volume. Avoid logging full domain objects or personal data by default.

## Testing and verification evidence

The evidence should prove behavior at the owner that claims it:

- unit or property tests for value semantics, policies, and legal transitions;
- aggregate tests for invariants, rejection, and state changes;
- database integration tests for unique, foreign-key, check, and non-negative
  constraints that back the model;
- concurrency tests for conflicting commands and stale versions;
- integration tests for outbox, event, projection, and compensation behavior;
- authorization and tenant tests at the application boundary;
- replay and migration tests for historical state and mixed versions;
- failure injection for crash-after-commit, duplicate event, late event, and
  unavailable dependency;
- contract tests for domain events or external commands.

A passing unit test on an entity does not prove that every caller uses it, that
the database protects the invariant, or that events are durable. Verification
must exercise the public command path and inspect persisted state, side
effects, and telemetry. The handoff should state the claim, mechanism,
counterexample attempted, and evidence status as required by the
[composition contract](composition-contracts.md).

## Decision output

For a non-trivial model, record the rule, current bypasses, forces, selected
owner, rejected ceremony, invariant, transaction boundary, authorization
boundary, retry/duplicate semantics, migration plan, observability, and
verification evidence. Link to [transaction patterns](transaction-patterns.md),
[consistency patterns](consistency-patterns.md), and
[concurrency patterns](concurrency-patterns.md) when the model depends on
their guarantees. A pattern name without this record is not a domain decision.
