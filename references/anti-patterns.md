# Backend anti-patterns

An anti-pattern is a recurring design shape whose local convenience hides a
larger correctness, security, operability, or change cost. Detection is not a
verdict from a name alone: the same mechanism can be reasonable at a bounded
scale when its ownership, failure semantics, and evidence are explicit. Use
this catalog during review and migration, then record the selected alternative
through [`decision-matrix.md`](decision-matrix.md). The routing entry is in
[`pattern-index.md`](pattern-index.md).

Every entry uses the same six questions: symptom, cause, danger, detection,
safe alternative, and migration strategy. A migration should preserve public
behavior and invariants while making one boundary clearer at a time.

## God Service

- **Symptom:** One service owns unrelated domains, endpoints, persistence,
  workflows, integrations, and policy decisions; small changes require broad
  tests and releases.
- **Cause:** A central service was the easiest first boundary, or ownership
  was never revisited as features accumulated.
- **Danger:** Change blast radius, conflicting transaction scopes, tangled
  authorization, slow tests, and unclear data ownership make failures hard to
  contain.
- **Detection:** Module dependency graphs show many inward and outward edges;
  handlers reach across domains; the service has unrelated SLOs or frequent
  conflict-heavy releases.
- **Safe alternative:** Start with explicit domain-oriented modules or vertical
  slices inside a modular monolith; extract a service only for a proven
  deployment, scaling, isolation, or ownership force.
- **Migration strategy:** Inventory public contracts and invariants, introduce
  module APIs and ownership tests, move one cohesive flow behind a boundary,
  and measure coupling before considering extraction.

## God Repository

- **Symptom:** One repository exposes every table, query, transaction, and
  domain operation through a broad interface used by unrelated features.
- **Cause:** Centralizing persistence was confused with centralizing ownership;
  generic convenience methods grew without a domain boundary.
- **Danger:** Callers can bypass invariants, transactions become accidental,
  query changes create cross-domain regressions, and authorization is repeated
  or omitted.
- **Detection:** Methods return arbitrary entities or query builders; callers
  compose persistence operations directly; the repository has unrelated
  transaction and tenant rules.
- **Safe alternative:** Give each aggregate or module a narrow data-access port;
  use direct queries when they are clearer and preserve the owner’s invariants.
- **Migration strategy:** Classify methods by owner, lock down cross-owner
  access, replace broad calls with explicit use-case ports, and delete or
  quarantine methods only after callers and tests move.

## Fat Controller

- **Symptom:** HTTP, RPC, or message handlers parse input, authorize, run
  domain rules, query data, publish events, format responses, and recover
  failures in one method.
- **Cause:** The entrypoint was the visible place to add behavior and no
  application boundary was named.
- **Danger:** Transport concerns leak into business rules, authorization is
  inconsistent across entrypoints, transactions are unclear, and behavior is
  difficult to test without the full stack.
- **Detection:** Controllers contain conditional business logic, database
  calls, retries, or broker calls; another entrypoint duplicates the logic.
- **Safe alternative:** Keep the handler thin: validate transport shape,
  invoke a use-case boundary, map a typed result, and delegate policy and
  side-effect ownership.
- **Migration strategy:** Extract one invariant-preserving use case at a time,
  make its transaction and authorization inputs explicit, then route HTTP,
  jobs, and commands through the same boundary.

## Anemic Domain Model when domain logic genuinely exists

- **Symptom:** Domain objects are data bags while workflows, invariants, and
  state transitions live in sprawling services or controllers.
- **Cause:** A simple CRUD model was generalized to a rule-heavy domain, or
  persistence shape was mistaken for domain ownership.
- **Danger:** Legal transitions and invariants are duplicated, bypassed by new
  callers, or applied after a side effect; concurrency behavior becomes
  accidental.
- **Detection:** Search for repeated state predicates, setters that permit
  illegal transitions, and service methods that manipulate another object's
  internals. Do not flag a genuinely simple data-centric domain merely because
  it lacks rich objects.
- **Safe alternative:** Put behavior and invariants with the aggregate or
  policy owner; use a transaction/application service to coordinate external
  effects without hiding domain rules.
- **Migration strategy:** Identify one high-value invariant, introduce a
  behavior method with characterization tests, migrate callers, and leave
  straightforward CRUD as data-oriented code where no domain rule exists.

## Distributed monolith

- **Symptom:** Several deployed services must release together, make long
  synchronous chains, share assumptions or schemas, and fail as one unit.
- **Cause:** Processes were split before ownership, data, reliability, or
  deployment boundaries were real.
- **Danger:** Network failure and version skew are added without independent
  autonomy; diagnosis, testing, and rollback become harder than in a monolith.
- **Detection:** A service cannot run or deploy without sibling services; a
  change requires coordinated releases; requests traverse many mandatory hops.
- **Safe alternative:** Consolidate tightly coupled paths into a modular
  monolith or define real service contracts, ownership, and failure semantics.
- **Migration strategy:** Map call and data dependencies, shorten critical
  chains, introduce compatible contracts, then either recombine a cohesive
  slice or grant an extracted boundary independent data and release control.

## Shared database across independently deployed services

- **Symptom:** Services write each other's tables, coordinate through implicit
  foreign keys, or require a shared migration schedule despite separate
  releases.
- **Cause:** The database was treated as the easiest integration surface or
  extraction happened before data ownership was designed.
- **Danger:** Any service can violate another's invariants; locks, schema
  changes, backups, and outages create a hidden global coupling.
- **Detection:** Cross-service table writes, direct queries into another
  service's schema, or deploys blocked by a shared migration.
- **Safe alternative:** One owner per mutable data set, explicit API or event
  contracts, and an outbox/inbox or reconciliation path for asynchronous
  effects.
- **Migration strategy:** Assign ownership, add compatibility views or APIs,
  dual-read only with measured reconciliation, move writes behind the owner,
  and remove cross-owner credentials after consumers migrate.

## Database as integration bus

- **Symptom:** Services poll tables, triggers, or transaction logs as an
  undocumented message channel; status rows act as commands without delivery
  semantics.
- **Cause:** A broker was unavailable, or durable integration was needed before
  an explicit event contract was designed.
- **Danger:** Ordering, retries, retention, ownership, schema evolution, and
  poison-message handling are implicit; polling can overload the source.
- **Detection:** Consumers infer events from row changes, query another
  service's operational tables, or cannot identify message identity and
  causation.
- **Safe alternative:** Use an explicit broker/event contract or a transactional
  outbox with a documented publisher and idempotent consumer.
- **Migration strategy:** Define event identity and version, backfill an
  outbox from an authoritative source, run old and new paths with
  reconciliation, then remove polling and revoke cross-schema access.

## Chatty services

- **Symptom:** One user action makes many small synchronous calls, repeated
  lookups, or per-item remote requests.
- **Cause:** Service boundaries mirror tables or teams rather than use cases;
  no bulk or composition contract exists.
- **Danger:** Latency tails, partial failure, retry amplification, network cost,
  and dependency availability multiply with fan-out.
- **Detection:** Trace fan-out and call count grow with item count; p95/p99 is
  dominated by remote calls; one dependency outage disables unrelated reads.
- **Safe alternative:** Co-locate a cohesive read path, add bounded bulk/query
  endpoints, cache derived data with an explicit source of truth, or use a
  durable asynchronous workflow for non-critical work.
- **Migration strategy:** Measure call graph and latency, batch the hottest
  path, set deadlines and concurrency budgets, then revisit the service seam
  using real data rather than intuition.

## Synchronous chain explosion

- **Symptom:** A request waits on a long chain of mandatory services, each with
  its own timeout and retry; one slow leaf makes the whole request fail.
- **Cause:** Synchronous composition was used for every dependency, including
  work that could be deferred or locally owned.
- **Danger:** Deadline exhaustion, cascading failure, retry storms, poor user
  feedback, and ambiguous partial effects.
- **Detection:** Trace depth and critical-path hops keep increasing; the sum of
  downstream budgets exceeds the user budget; no step can be resumed safely.
- **Safe alternative:** Keep correctness-critical boundaries short, use
  asynchronous workflows with durable state for deferrable work, and define
  explicit compensation or pending status.
- **Migration strategy:** Classify each hop by user necessity and invariant,
  collapse or batch local calls, add a durable workflow for deferred effects,
  and test mixed success, timeout, and resume paths.

## Retry storms

- **Symptom:** During an outage, request volume or dependency load increases
  because multiple layers retry the same failing operation.
- **Cause:** Retries were added as a generic reliability feature without
  ownership, idempotency, budget, jitter, or coordination.
- **Danger:** A recoverable transient outage becomes a sustained overload;
  non-idempotent effects duplicate and healthy dependencies are pulled down.
- **Detection:** Attempt rate exceeds business-operation rate; synchronized
  retry intervals, rising queue age, and circuit oscillation appear in traces.
- **Safe alternative:** One bounded retry owner, finite deadline, exponential
  backoff with jitter, idempotent effect, circuit/bulkhead, and load shedding.
- **Migration strategy:** Inventory retries end to end, disable duplicate layers,
  add attempt/correlation metrics, classify errors, and prove behavior under a
  dependency outage before restoring any retry budget.

## Cache as source of truth

- **Symptom:** Correctness depends on a cache entry, cache writes are treated
  as the durable mutation, or cache loss causes unrecoverable state loss.
- **Cause:** A fast read path was promoted to persistence, or invalidation was
  harder than writing the cache directly.
- **Danger:** Eviction, corruption, stale reads, split-brain values, and cache
  outages become data loss or authorization exposure.
- **Detection:** There is no authoritative rebuild path, TTL changes business
  state, or operators cannot explain a cache miss without data loss.
- **Safe alternative:** Keep an authoritative store; use cache-aside,
  read-through, or a rebuildable materialized view with explicit stale-data
  policy.
- **Migration strategy:** Identify and repair the source of truth, write new
  mutations durably first, backfill/rebuild the cache, and test total cache
  loss before removing the old path.

## Dual-write inconsistency

- **Symptom:** One operation writes two stores, services, or schemas directly;
  one write can succeed while the other fails and reconciliation is informal.
- **Cause:** A new model or integration was introduced without a transaction,
  outbox, ownership, or staged migration plan.
- **Danger:** Divergent state, duplicate effects, untraceable repairs, and
  business decisions based on whichever copy was read.
- **Detection:** No shared operation identity, mismatch metric, replay/reconcile
  tool, or defined source of truth exists; code has two independent writes.
- **Safe alternative:** One durable owner plus an outbox/consumer, or a local
  atomic transaction with a rebuildable derived view. Use dual writes only as a
  bounded migration phase with explicit reconciliation.
- **Migration strategy:** Declare the source of truth, instrument mismatches,
  make writes idempotent, backfill the derived side, compare before cutover,
  and remove the second authoritative write.

## Fire-and-forget critical operations

- **Symptom:** A critical mutation launches a background task and immediately
  reports success without durable intent, status, or recovery ownership.
- **Cause:** Asynchrony was used to hide latency or simplify error handling.
- **Danger:** Process death, queue rejection, lost exceptions, duplicate retries,
  and false success leave the user or business with no reliable outcome.
- **Detection:** No durable job ID, outbox row, acknowledgement, pending state,
  retry policy, or operator path exists for the launched work.
- **Safe alternative:** Commit durable intent, return an explicit pending state,
  and process through a bounded queue with idempotency and visible recovery.
- **Migration strategy:** Introduce a job record/outbox in the owning
  transaction, expose status and failure semantics, drain old in-memory tasks,
  and reconcile operations that were reported successful without proof.

## Hidden transaction boundaries

- **Symptom:** A framework, ORM, repository, or helper silently starts/commits
  transactions; callers cannot tell which writes are atomic.
- **Cause:** Convenience defaults and nested abstractions concealed the unit
  of work.
- **Danger:** Partial updates, commits before authorization or event creation,
  locks held too long, and false rollback assumptions.
- **Detection:** Tests pass only with a request context, transaction calls are
  absent from use cases, or logs cannot show commit/rollback outcomes.
- **Safe alternative:** Name the transaction owner at the use-case boundary,
  pass an explicit unit of work, and keep external calls outside it unless the
  semantics require otherwise.
- **Migration strategy:** Trace actual begin/commit behavior, add rollback and
  partial-failure tests, expose the boundary in the API, then remove nested
  implicit transactions one flow at a time.

## Leaky abstractions

- **Symptom:** A module, repository, or service claims a stable interface while
  callers depend on database errors, ORM types, transport headers, or provider
  quirks.
- **Cause:** The abstraction was named before its invariant and ownership were
  defined, or a pass-through wrapper was mistaken for a boundary.
- **Danger:** Internal changes become public breaking changes; error, security,
  consistency, and performance assumptions escape their owner.
- **Detection:** Callers import lower-level types, inspect provider-specific
  errors, or need hidden flags to get correct behavior.
- **Safe alternative:** Expose domain-relevant operations and error semantics;
  put provider translation at the edge and document the guarantees that are
  intentionally visible.
- **Migration strategy:** Inventory leaked dependencies, add a contract test,
  translate one class of leak at a time, and reject new calls that bypass the
  owner.

## Service locator

- **Symptom:** Code resolves dependencies from a global registry or ambient
  container instead of receiving them explicitly.
- **Cause:** Global lookup looked easier than dependency wiring, especially in
  tests or plugin systems.
- **Danger:** Hidden dependencies, runtime-only failures, accidental shared
  state, privilege confusion, and tests that pass because the locator is
  overconfigured.
- **Detection:** Methods have few parameters but call a registry; behavior
  changes with global initialization order or environment.
- **Safe alternative:** Constructor/function injection with explicit ports;
  keep a composition root for wiring and scoped lifetimes.
- **Migration strategy:** Add explicit parameters while retaining a temporary
  adapter, test missing dependencies, migrate callers, then restrict the
  locator to the composition root or remove it.

## Premature microservices

- **Symptom:** A small or uncertain product is split into independently
  deployed services without independent scaling, ownership, reliability, or
  isolation needs.
- **Cause:** Microservices were treated as a maturity signal or assumed to
  scale every dimension automatically.
- **Danger:** Network failure, deployment skew, distributed data, observability,
  security, and operational cost arrive before the domain boundaries are known.
- **Detection:** One team changes all services together, services share a
  database, calls form a synchronous chain, or the proposed benefit is only
  “future scale.”
- **Safe alternative:** A modular monolith with explicit boundaries and a
  measured extraction seam; see the gate in
  [`decision-matrix.md`](decision-matrix.md).
- **Migration strategy:** Restore module ownership and contract tests, consolidate
  tightly coupled services when safe, or extract one proven boundary with its
  own data, SLO, identity, and release process.

## Premature CQRS

- **Symptom:** Separate command/query models, buses, projections, or eventual
  consistency are introduced for ordinary CRUD without asymmetric pressure.
- **Cause:** CQRS was selected because it sounds cleaner or advanced, not
  because read/write concerns require different models.
- **Danger:** Projection lag, rebuilds, duplicate handlers, reconciliation, and
  query complexity obscure simple transactional behavior.
- **Detection:** Read and write shapes are nearly identical; no read scaling,
  consistency, or domain-command force is measured.
- **Safe alternative:** One transactional model with focused queries, indexes,
  and a direct API until a documented CQRS gate is satisfied.
- **Migration strategy:** Measure read/write load and model mismatch, introduce
  one rebuildable read model behind a compatibility path, and retain the
  authoritative write model until the projection is proven.

## Cargo-cult DDD

- **Symptom:** Aggregates, value objects, domain events, factories, and bounded
  contexts appear by naming convention while the domain has no corresponding
  invariants or ownership problems.
- **Cause:** Practices were copied without identifying the business rules they
  protect.
- **Danger:** Ceremony, indirection, slower delivery, false boundaries, and
  domain language that does not match user behavior.
- **Detection:** Every table has an aggregate, every constructor a factory,
  and no decision can explain the invariant or conflict it prevents.
- **Safe alternative:** Use the simplest domain model that protects real rules;
  keep CRUD data direct when the domain is genuinely data-centric.
- **Migration strategy:** Map actual invariants and workflows, remove unused
  ceremony behind characterization tests, and retain only concepts that change
  a decision, boundary, or proof obligation.

## Generic repository abuse

- **Symptom:** A universal `get/save/delete` interface is applied to every
  entity and hides query shape, transaction ownership, and consistency needs.
- **Cause:** Repository was adopted as a best practice rather than for a
  meaningful aggregate or persistence substitution boundary.
- **Danger:** Leaky abstractions, N+1 queries, impossible generic semantics,
  accidental writes, and loss of database constraints or query visibility.
- **Detection:** Generic methods dominate call sites, return persistence models,
  accept arbitrary predicates, or require escape hatches for common queries.
- **Safe alternative:** Use explicit query objects/ports for real access
  patterns, direct SQL/ORM where appropriate, and repositories only when they
  protect an ownership or aggregate boundary.
- **Migration strategy:** Measure query and transaction behavior, replace the
  highest-risk generic calls with named operations, preserve contract tests,
  and remove the generic layer when no unique value remains.

## Abstraction for abstraction's sake

- **Symptom:** Interfaces, factories, adapters, service classes, or indirection
  exist without a second implementation, boundary, policy, or testable gain.
- **Cause:** Future-proofing and pattern naming were valued above current
  constraints and change evidence.
- **Danger:** Cognitive load, more failure paths, slower debugging, and an
  abstraction that freezes the wrong API.
- **Detection:** The abstraction forwards every call unchanged and no decision
  depends on it; callers need to navigate several files for one behavior.
- **Safe alternative:** Keep the direct implementation until substitution,
  ownership, isolation, or contract pressure justifies a seam.
- **Migration strategy:** Record the actual reason each seam exists, inline
  low-value pass-throughs with tests, and introduce a narrower boundary only
  when a measured force recurs.

## Unbounded queues

- **Symptom:** Producers can enqueue without a size, age, rate, or storage
  limit; workers fall behind while the system reports accepted work.
- **Cause:** Queueing was used to hide overload or an implicit durable buffer was
  mistaken for capacity.
- **Danger:** Memory/storage exhaustion, unbounded user-visible delay, stale
  work, retry amplification, and a difficult recovery decision.
- **Detection:** No queue-depth/oldest-age SLO, maximum retention, admission
  control, poison policy, or drain/replay procedure exists.
- **Safe alternative:** Bounded queues with backpressure, quotas, expiry or
  prioritization, dead-letter handling, and an explicit overload response.
- **Migration strategy:** Measure producer/consumer rates, set finite capacity
  and rejection semantics, drain or quarantine excess work, and test sustained
  overload and restart recovery.

## Missing timeouts

- **Symptom:** Network, database, lock, parser, or queue operations can wait
  indefinitely or inherit an unsafe default.
- **Cause:** Timeout ownership was left to a library or considered an
  implementation detail.
- **Danger:** Worker starvation, connection exhaustion, synchronous chain
  collapse, and no bounded recovery point.
- **Detection:** Traces contain open-ended spans; callers have no remaining
  deadline; outage tests hang or consume all workers.
- **Safe alternative:** Propagate a finite end-to-end deadline and allocate
  explicit budgets to each dependency, with cancellation and cleanup.
- **Migration strategy:** Inventory blocking operations, add timeout metrics and
  failure tests, choose budgets from the user SLO, and remove infinite or
  contradictory defaults.

## Missing backpressure

- **Symptom:** Producers continue at full speed while workers, dependencies, or
  storage are saturated; concurrency grows without bound.
- **Cause:** Throughput was optimized locally, or queueing/retry was used
  without a feedback signal.
- **Danger:** Cascading overload, latency collapse, memory growth, and loss of
  the ability to protect correctness-critical work.
- **Detection:** Queue age, in-flight work, retry count, pool wait, or memory
  rises while admission remains unchanged.
- **Safe alternative:** Bounded concurrency, admission control, rate limits,
  load shedding, queue capacity, priority, and explicit producer feedback.
- **Migration strategy:** Add saturation metrics and a safe cap, classify work
  by criticality, reject or defer excess work, and verify recovery after load
  returns to normal.

## Unversioned events

- **Symptom:** Event consumers assume one payload shape; producers change fields,
  meanings, or required values in place.
- **Cause:** Events were treated as internal structs rather than durable public
  contracts that outlive a deployment.
- **Danger:** Old consumers fail, silently misinterpret data, or produce wrong
  side effects during mixed-version rollout and replay.
- **Detection:** No schema identity/version, compatibility policy, unknown-field
  behavior, or fixture for old events exists.
- **Safe alternative:** Versioned schemas with additive evolution where possible,
  tolerant readers only where safe, explicit deprecation, and contract tests.
- **Migration strategy:** Add version metadata, support old and new readers,
  dual-publish or transform through a bounded window, replay representative
  events, then retire the old version with an observed consumer inventory.

## Giant shared “common” packages

- **Symptom:** A shared library contains unrelated domain models, utilities,
  policies, clients, and constants; every consumer releases because one package
  changed.
- **Cause:** Duplication was feared more than coupling, and the package became
  the easiest place to put cross-cutting code.
- **Danger:** Hidden dependency cycles, synchronized releases, accidental
  policy changes, framework coupling, and a broad blast radius.
- **Detection:** Consumers import unrelated namespaces, dependency upgrades are
  coordinated, or a small change forces many rebuilds and deployments.
- **Safe alternative:** Keep a small stable platform kernel for genuinely
  cross-cutting contracts; prefer local code or explicit versioned packages for
  domain ownership.
- **Migration strategy:** Map dependency and release coupling, split by stable
  ownership, publish narrow compatibility packages, migrate consumers, and
  delete the giant package only after an import scan proves it is unused.

## Anti-rationalization prompts

Use these prompts when a proposal sounds attractive but its evidence is thin:

- “It is small” does not remove transaction, trust, timeout, or recovery
  boundaries; scale the controls, not the reasoning away.
- “The broker/database/framework handles it” requires a testable contract for
  duplicate, timeout, ordering, commit, and version behavior.
- “We can fix observability later” is not acceptable for a production-critical
  path whose failures would otherwise be ambiguous.
- “A repository is best practice” requires an abstraction benefit beyond
  forwarding ORM calls.
- “Microservices/CQRS/DDD will scale or stay clean” requires a named force,
  rejected simpler alternative, complexity budget, and evidence plan.

The safe alternative is not always removal. It is the smallest design that
preserves the invariant, states the failure semantics, and can be operated and
verified. Use [`observability-patterns.md`](observability-patterns.md) for the
signals that expose an anti-pattern in production and
[`testing-patterns.md`](testing-patterns.md) for adversarial proof.
