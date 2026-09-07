# Backend pattern index

This index is the package's routing contract. Read `SKILL.md` first, identify
the dominant decision boundary, then load only the relevant reference(s).
References are judgment modules, not a checklist to dump into every task.

## Loading contract

Every reference should answer, for its boundary:

1. What problem does the pattern solve?
2. Which forces make it useful or unnecessary?
3. What is the smallest alternative?
4. What can fail, duplicate, race, leak, or become stale?
5. What security, operational, migration, observability, and testing evidence
   is required before claiming the design works?

| Decision boundary | Reference | Load when |
|---|---|---|
| ownership, modules, dependency direction, service seams | [architecture-boundaries](architecture-boundaries.md) | designing/refactoring boundaries or layers |
| domain rules and state ownership | [domain-modeling](domain-modeling.md) | domain logic, invariants, aggregates, policies |
| external/public interfaces | [api-patterns](api-patterns.md) | REST/RPC/GraphQL/webhooks, versioning, errors |
| persistence and query shape | [data-access-patterns](data-access-patterns.md) | ORM/SQL/repository/query/read-model decisions |
| local atomicity and cross-boundary effects | [transaction-patterns](transaction-patterns.md) | multi-write flows, outbox/inbox, Saga |
| staleness and conflict semantics | [consistency-patterns](consistency-patterns.md) | strong/eventual consistency, reads, conflicts |
| concurrent mutation and ownership | [concurrency-patterns](concurrency-patterns.md) | locks, CAS, races, work ownership |
| queues, events, brokers, workflows | [messaging-patterns](messaging-patterns.md) | async processing and delivery semantics |
| dependency failure and overload | [resilience-patterns](resilience-patterns.md) | timeouts, retries, breakers, backpressure |
| network/process failure | [distributed-systems](distributed-systems.md) | partial failure, partitions, ordering, clocks |
| derived data and acceleration | [caching-patterns](caching-patterns.md) | cache, invalidation, stampede, stale reads |
| replay and duplicate effects | [idempotency](idempotency.md) | idempotency keys, consumers, retries, webhooks |
| trust and privilege boundaries | [security-boundaries](security-boundaries.md) | authn/authz, tenancy, input, secrets, SSRF, abuse |
| production signals and diagnosis | [observability-patterns](observability-patterns.md) | logs, metrics, traces, SLOs, alerts, repair |
| measured capacity and latency | [performance-patterns](performance-patterns.md) | profiling, query plans, load, resource budgets |
| safe change over time | [migration-patterns](migration-patterns.md) | schema/API/event migrations, rollout, backfill |
| proof and failure injection | [testing-patterns](testing-patterns.md) | choosing tests and evidence for selected patterns |
| known failure shapes | [anti-patterns](anti-patterns.md) | review, red-team, migration from unsafe designs |
| cross-family trade-offs | [decision-matrix](decision-matrix.md) | comparing candidates and recording a decision |
| specialist boundaries and evidence handoff | [composition-contracts](composition-contracts.md) | security/backend/verification collaboration |

## Required decision record

For any non-trivial choice, emit a compact record using the template in
[`SKILL.md`](../SKILL.md): problem, constraints, forces, invariants,
candidates, rejected candidates, selected pattern, cost budget, boundaries,
failure/security/operations/migration implications, evidence, and unresolved
risk. A pattern name without this reasoning is not a recommendation.

## Coverage map

| User requirement family | Primary reference(s) | Proof fixture family |
|---|---|---|
| architecture/domain | architecture, domain, decision | selection, rejection |
| API/data/transactions | API, data, transaction, idempotency | API/data/concurrency |
| consistency/concurrency | consistency, concurrency, distributed | adversarial |
| messaging/reliability | messaging, resilience, distributed | retry/duplicate/recovery |
| caching/performance | caching, performance, observability | failure/measurement |
| security/tenancy | security, composition | security/negative |
| migration/compatibility | migration, API, testing | migration/regression |
| verification/operability | testing, observability, composition | composition/regression |
| anti-pattern defense | anti-patterns, decision matrix | rejection/adversarial |

