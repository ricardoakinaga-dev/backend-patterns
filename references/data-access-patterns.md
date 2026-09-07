# Data access and persistence patterns

## Purpose

This reference helps an agent choose persistence boundaries, query shapes, ORM
use, repositories, unit of work, mappers, specifications, read models, views,
direct SQL, and CQRS. It keeps database guarantees visible instead of hiding
them behind abstractions. A data-access pattern is successful when it preserves
integrity, gives the required query behavior, and remains understandable and
operable as schemas evolve.

## When to load

Load this reference when choosing or changing an ORM, SQL strategy, repository,
unit of work, mapper, query object, specification, read model, materialized
view, database view, CQRS split, persistence ownership, indexing, or data
access boundary. Also load it when a performance claim depends on query shape,
when a transaction boundary is unclear, or when a service extraction changes
who can write a table.

Do not load it for a pure in-memory transformation with no persistence
contract. Combine it with [domain modeling](domain-modeling.md) for aggregate
ownership, [transaction patterns](transaction-patterns.md) for atomicity,
[consistency patterns](consistency-patterns.md) for replicas and projections,
and [concurrency patterns](concurrency-patterns.md) for races and locking.

## Problem and forces

The problem is to access data in a way that preserves the source of truth,
constraints, transaction semantics, and query performance without creating
unnecessary indirection. Record the forces:

- invariants, uniqueness, referential integrity, and retention requirements;
- read/write access patterns, cardinality, sorting, filtering, and pagination;
- transaction scope and isolation needs;
- latency, throughput, concurrency, and hot-key behavior;
- schema evolution, migration, backfill, and mixed-version compatibility;
- storage portability versus database-specific capabilities;
- developer productivity and team knowledge;
- security, tenant isolation, sensitive data, and least privilege;
- observability, query diagnosis, and repair;
- operational maturity, cost, and failure recovery.

Never select SQL, NoSQL, ORM, repository, or CQRS as a moral preference. Begin
with the invariant and access pattern, then verify the database can enforce and
serve them at the expected workload.

### Data ownership questions

For each mutable fact, answer:

1. Which boundary is the source of truth?
2. Which operation is allowed to change it?
3. Which constraints are enforced in application code and which in the
   database?
4. What transaction and isolation level protect the invariant?
5. What reads may be stale, and how is staleness represented?
6. Who can query or export the data, by tenant and property?
7. How are schema/data migrations, backfills, repair, and retention handled?
8. What evidence proves the query plan, integrity, and failure behavior?

If two independently deployed owners write the same business record, ownership
is unresolved. A shared database can be a practical modular-monolith choice,
but it is not independent service ownership by itself.

## Pattern selection

### Direct SQL or database-native queries

Use direct SQL when query shape, constraints, joins, windowing, locking,
bulk behavior, or performance needs to be expressed clearly in the database
language. Keep queries parameterized, bounded, reviewed, and tied to a
well-defined read or command contract.

Use database-native features when they are the simplest reliable way to enforce
integrity or meet measured workload requirements. Document the portability and
operational cost.

Do not use raw string concatenation, unbounded query construction, or direct
SQL as an excuse to skip authorization, transactions, migrations, or testing.

### ORM and data mapper

Use an ORM or data mapper when it improves routine mapping, change tracking,
parameterization, migrations, or team productivity without hiding the
database semantics the system relies on. Prefer explicit query boundaries for
important reads and writes.

Know the generated behavior: joins, lazy/eager loading, N+1 queries, null
semantics, identity maps, bulk updates, locking, transaction scope, connection
pooling, and error translation. An ORM is a tool, not a transaction boundary
unless the actual runtime behavior proves that it is.

Reject an ORM when its generated queries cannot meet a measured access pattern,
when its unit-of-work behavior obscures correctness, or when a small set of
database-native queries is clearer and safer. Use a focused escape hatch rather
than abandoning all constraints.

### Active Record

Use Active Record for a small, cohesive application where persistence and
domain behavior naturally live together, queries are straightforward, and the
team accepts the coupling. It can reduce ceremony for CRUD.

Do not use it to imply that every public operation may mutate every column,
that model instances are valid aggregates, or that database persistence
automatically enforces authorization and lifecycle rules. As workflows,
contexts, or query shapes diverge, an application boundary or data mapper may
be safer.

### Repository

Use a repository when it represents a meaningful domain collection or
persistence contract: aggregate loading/saving, ownership, transaction
semantics, storage substitution with real value, or a stable domain-facing
query. Keep method names tied to intent and define consistency and side effects.

Do not add a generic repository that mirrors create/read/update/delete for
every table, returns ORM entities with arbitrary methods, or forces all queries
through a least-common-denominator API. That abstraction preserves
implementation names while hiding query plans, constraints, transactions, and
errors. A direct ORM/query module may be the more honest boundary.

### Unit of work

Use a unit of work when several changes need a coordinated flush, identity
scope, or explicit commit/rollback boundary. State whether it is merely a
change tracker or also owns the database transaction, and where retries and
side effects occur.

Do not treat a unit of work as a universal distributed transaction or hold it
open across network calls, user interaction, queue waits, or unbounded work.
The database transaction should be short and its isolation deliberate.

### Query objects and specifications

Use a query object for a complex, performance-sensitive, or reusable read
whose filters, joins, ordering, limits, and authorization scope deserve a
named owner. Use a specification when a business predicate is reused across
domain decisions and persistence queries can implement it without changing
its meaning.

Do not turn every filter into a generic query DSL. Query objects should reveal
cost and result shape. Specifications should not silently become arbitrary SQL
or cross tenant boundaries.

### Read models, database views, and materialized views

Use a database view to present a stable relational read shape without copying
data when freshness and query cost are acceptable. Use a materialized view or
read model when repeated joins, denormalization, search, reporting, or
read/write asymmetry justifies derived storage.

Every derived model needs a source of truth, refresh or projection mechanism,
staleness bound, rebuild procedure, schema version, and behavior when it is
unavailable. Do not use a read model as an unacknowledged second source of
truth.

### CQRS

Use CQRS when command and query models have materially different invariants,
scale, shape, ownership, or consistency requirements, or when specialized
projections are a real product capability. Keep the write model authoritative
and make projection lag visible.

Reject CQRS when reads and writes share the same shape, when a few indexes or
queries solve the performance problem, or when the only motivation is that
separation feels cleaner. It adds dual models, synchronization, lag, rebuild,
and operational complexity.

## Repository and ORM trade-offs

Use this test before wrapping an ORM:

- Does the boundary own an invariant, aggregate, transaction, or authorization
  decision?
- Does it hide more than method renaming, such as multiple stores, caching,
  retries, or a stable domain query?
- Does it preserve access to query shape, constraints, and isolation when they
  matter?
- Can its failure, consistency, and side effects be explained to callers?
- Is there evidence that the abstraction will survive a real change?

If all answers are no, use the ORM or direct query in the owning module and
test it through its public behavior. If an abstraction is useful, do not force
it to provide fake portability or a generic interface that erases important
database capabilities.

ORM use still requires:

- explicit transaction ownership and connection lifecycle;
- database-enforced constraints for critical invariants;
- query-plan inspection and N+1 detection;
- bounded result sets, indexes, and pagination;
- safe parameterization and migration review;
- explicit bulk-update and stale-entity semantics;
- error mapping that does not erase uniqueness, conflict, or deadlock signals.

## When to use

Use this reference when persistence is part of correctness, performance,
evolution, security, or operational risk. It is especially important when:

- multiple writes must be atomic;
- a query is slow, unbounded, or difficult to diagnose;
- an ORM abstraction may hide a lock or isolation issue;
- a service/module boundary changes table ownership;
- a read model, projection, or cache introduces staleness;
- a schema or data migration must coexist with old code.

Start with a direct, constrained persistence path. Add repository, unit of
work, mapper, projection, or CQRS only when the stated forces pay for it.

## When not to use

Do not:

- wrap every ORM in a generic repository as a matter of style;
- rely on application validation where a database constraint is required;
- use a unit of work across a remote call or user interaction;
- add CQRS or materialized views before measuring query asymmetry or cost;
- let read models become authoritative by accident;
- share one mutable database across independently owned services without an
  ownership and migration plan;
- use a cache to hide a bad query before inspecting its plan;
- choose a database family without access-pattern, integrity, and operational
  evidence;
- assume an ORM's default transaction or isolation behavior is correct.

## Alternatives and trade-offs

| Need | Smallest credible choice | Stronger choice when justified | Main cost |
| --- | --- | --- | --- |
| Routine CRUD | ORM/Active Record with constraints | Data mapper or domain boundary | Mapping and ceremony |
| Complex read | Focused query or direct SQL | Read model/materialized view | Freshness and rebuild |
| Aggregate persistence | Explicit data access in use case | Repository/unit of work | Abstraction and lifecycle |
| Multiple writes | Local database transaction | Saga or workflow | Compensation and recovery |
| Portability | Small adapter around stable operations | Full repository/port | Least-common-denominator risk |
| Read/write asymmetry | Indexed shared model | CQRS projections | Lag, dual schema, operations |

Portability is not free. A database-specific constraint or query can be the
right choice when correctness and measured behavior matter more than swapping
storage. Conversely, a portability abstraction is valuable when there is a
credible second implementation or long-lived domain boundary, not merely a
theoretical possibility.

## Failure and integrity implications

For each access operation, specify:

- transaction start and commit/rollback boundaries;
- isolation level, lock behavior, and expected conflict/deadlock behavior;
- what happens on connection loss before and after commit;
- uniqueness, foreign-key, check, and non-negative constraints;
- behavior of partial bulk writes and statement retries;
- read behavior when a replica, view, or projection is stale or unavailable;
- recovery after process crash, interrupted migration, or failed backfill.

A database transaction protects only the participating database resources. It
does not make a cache update, message publish, email, or remote call atomic.
Use [transaction patterns](transaction-patterns.md) for outbox, inbox, and
workflow choices.

If a query result is used for a subsequent write, make the expected version or
locking semantics explicit. A check followed by an unguarded update is a
race, even when both statements are close together in code.

## Security implications

Data access is a privilege boundary even inside one process. Specify:

- credentials, roles, connection scope, and least privilege;
- tenant and resource filters enforced at the owning query/command boundary;
- whether a caller can alter fields that are not exposed in the API;
- protection against injection, unsafe dynamic sort/filter, and path traversal;
- encryption, masking, retention, deletion, and export behavior;
- whether logs, query traces, backups, projections, and views expose sensitive
  data;
- whether replicas, analytics stores, or derived models inherit access rules.

Do not assume a repository or ORM enforces object-level authorization. Test
queries with another tenant's identifiers, missing scopes, and property
updates. Escalate material data sensitivity, tenancy, secrets, privilege, or
injection concerns through the [composition contract](composition-contracts.md).

## Operational implications

Specify:

- pool limits, timeouts, cancellation, retry policy, and retry amplification;
- indexes, query plans, cardinality assumptions, storage growth, and hot keys;
- lock waits, deadlocks, slow queries, connection exhaustion, and saturation
  alerts;
- schema ownership, migration locking, backfill checkpoints, and repair tools;
- backup/restore expectations and how derived data is rebuilt;
- failure behavior when the primary, replica, view, or projection is degraded;
- operator procedures for stuck transactions, poisoned data, and reconciliation.

Do not automatically retry a transaction after an unknown commit. The retry
must be safe for the operation and distinguish serialization/deadlock retry
from a permanent constraint or authorization failure.

## Migration and compatibility implications

Use an expand/contract migration for schema and access changes:

1. add nullable or compatible schema elements and required indexes;
2. deploy readers that handle old and new shapes;
3. deploy writers that preserve old consumers or dual-read with telemetry;
4. backfill in bounded, resumable, idempotent batches;
5. validate counts, constraints, checksums, and business invariants;
6. switch ownership or reads with a reversible control;
7. remove old columns, queries, indexes, or adapters after the window closes.

Avoid dual writes unless the source of truth, ordering, reconciliation, crash
recovery, and termination condition are explicit. Do not make a new model
authoritative merely because it has received a few successful writes. For
service extraction, one owner should write each business fact; a shared
database is not a substitute for an ownership contract.

## Observability implications

Measure persistence behavior at the boundary:

- query/operation name, table or logical resource, duration and row count;
- transaction outcome, isolation, retry reason, deadlock/serialization conflict;
- pool usage, wait time, lock age, slow-query samples, and error category;
- projection/view refresh time, lag, rebuild progress, and reconciliation drift;
- migration version, batch checkpoint, rows processed, failed rows, and
  invariant checks;
- tenant-safe correlation, command, request, and trace identifiers.

Redact values and parameters that contain secrets or personal data. Prefer
stable query fingerprints and bounded samples. Logs should distinguish a
rejected constraint from an unavailable database and a stale projection.

## Testing and verification evidence

Use evidence that reaches the actual persistence boundary:

- integration tests for constraints, transactions, isolation, rollback, and
  error mapping;
- query tests with realistic cardinality, indexes, pagination, and plans;
- tests for N+1, lazy-load failure, bulk-update semantics, and null/empty cases;
- concurrent update, deadlock, lock timeout, and stale version tests;
- security tests for tenant scope, object/property authorization, injection, and
  sensitive-data exposure;
- migration tests from representative old states, mixed versions, interrupted
  batches, retry, rollback/roll-forward, and repair;
- projection/read-model tests for duplicate, reorder, lag, rebuild, and missing
  source data;
- measured workload evidence for any claim about latency, throughput, or scale;
- backup/restore or reconstruction evidence when data recovery is material.

A mocked repository test does not prove that the ORM generated the right
query, the database enforced the invariant, or a transaction rolled back.
Inspect persisted state, side effects, query metrics, and known-bad cases. Mark
planned evidence separately from commands actually executed; the handoff
format is defined in the [composition contract](composition-contracts.md).

## Decision output

Record the source of truth, ownership, access patterns, selected persistence
style, rejected abstraction, constraints, transaction/isolation boundary,
consistency and staleness contract, security scope, migration/rollback plan,
operational signals, query evidence, and unresolved risk. Link to
[domain modeling](domain-modeling.md) when aggregate ownership drives the
choice, to [consistency patterns](consistency-patterns.md) for replicas and
read models, and to [concurrency patterns](concurrency-patterns.md) for
locks or compare-and-swap.
