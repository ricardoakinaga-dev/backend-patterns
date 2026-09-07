# MASTER PROMPT — BACKEND-PATTERNS STATE-OF-THE-ART / TRIPLE-A

You are acting as a Principal Backend Engineer, Distributed Systems Architect, API Architect, Database Architect, Reliability Engineer, Security Engineer, Agent-Skill Designer and Verification Engineer.

Your mission is to inspect, design, implement, validate and harden a production-grade Agent Skill named:

`backend-patterns`

The result must represent a **State-of-the-Art / Triple-A engineering skill**, suitable for repeated use by advanced coding agents such as Codex and compatible with the broader Agent Skills / SKILL.md ecosystem.

This is NOT a task to create a long Markdown cheat sheet.

The skill must encode **engineering judgment, pattern selection, trade-off analysis, failure-mode reasoning, implementation guidance, anti-pattern detection and evidence-based verification**.

The finished skill should behave more like an experienced Principal Backend Engineer than a pattern catalog.

---

# 0. PRIME DIRECTIVE

The `backend-patterns` skill must help an agent answer:

> Given this backend problem, architecture, codebase and operational context, which backend patterns should be used, which should explicitly NOT be used, why, what trade-offs do they introduce, how should they be implemented here, and what evidence demonstrates that the resulting system behaves correctly?

The skill MUST optimize for:

1. correctness;
2. maintainability;
3. evolvability;
4. simplicity;
5. security;
6. reliability;
7. observability;
8. performance where justified;
9. consistency;
10. testability;
11. operability;
12. backward compatibility;
13. failure containment;
14. explicit architectural reasoning;
15. minimum accidental complexity.

Never optimize for pattern count.

Never introduce a pattern solely because it is considered sophisticated.

Patterns are tools, not objectives.

---

# 1. REPOSITORY-FIRST INVESTIGATION

Before modifying anything, inspect the repository thoroughly.

Locate and analyze:

* existing `backend-patterns`;
* `backend-engineering-vNext`;
* `frontend-engineering-vNext`;
* `security-engineering-vNext`;
* `verification-loop-vNext`;
* orchestration skills;
* engineering framework skills;
* architecture-related skills;
* API-related skills;
* database-related skills;
* security-related skills;
* testing-related skills;
* observability/reliability skills;
* AGENTS.md files;
* skill conventions;
* validation scripts;
* schema validators;
* test fixtures;
* evaluation harnesses;
* composition mechanisms;
* capability boundaries;
* existing references and scripts.

Do not assume architecture from filenames.

Inspect the actual implementation.

Build a dependency and responsibility map.

Determine:

* what `backend-patterns` currently owns;
* what neighboring skills own;
* where responsibilities overlap;
* what functionality should remain here;
* what functionality should be delegated;
* whether existing behavior must remain backward compatible.

Do not duplicate responsibilities already implemented better elsewhere.

---

# 2. BASELINE ASSESSMENT

Before implementation, produce an internal baseline audit of the existing skill.

Score it from 0–100 on:

* activation precision;
* scope clarity;
* architectural depth;
* backend breadth;
* pattern-selection quality;
* anti-pattern detection;
* distributed-systems reasoning;
* API design;
* data integrity;
* transaction reasoning;
* concurrency reasoning;
* failure handling;
* resilience;
* security awareness;
* observability;
* performance reasoning;
* verification strength;
* progressive disclosure;
* token efficiency;
* framework independence;
* language independence;
* composability;
* maintainability;
* deterministic behavior;
* evidence requirements.

Record major weaknesses before changing the implementation.

The purpose is to demonstrate measurable improvement rather than merely rewriting the skill.

---

# 3. TARGET ARCHITECTURE

Prefer a compact orchestrating `SKILL.md` plus selectively loaded references and scripts.

Target architecture should resemble:

```text
backend-patterns/
├── SKILL.md
├── references/
│   ├── pattern-selection.md
│   ├── architecture-boundaries.md
│   ├── domain-modeling.md
│   ├── api-patterns.md
│   ├── data-access-patterns.md
│   ├── transaction-patterns.md
│   ├── consistency-patterns.md
│   ├── concurrency-patterns.md
│   ├── messaging-patterns.md
│   ├── resilience-patterns.md
│   ├── distributed-systems.md
│   ├── caching-patterns.md
│   ├── idempotency.md
│   ├── security-boundaries.md
│   ├── observability-patterns.md
│   ├── performance-patterns.md
│   ├── migration-patterns.md
│   ├── testing-patterns.md
│   ├── anti-patterns.md
│   ├── decision-matrix.md
│   └── composition-contracts.md
├── scripts/
│   ├── validate-skill.*
│   ├── validate-links.*
│   ├── validate-pattern-index.*
│   └── optional deterministic helpers
├── tests/
│   ├── activation/
│   ├── selection/
│   ├── negative/
│   ├── adversarial/
│   ├── composition/
│   └── regression/
└── README.md                  # only if repository conventions justify it
```

Do not create files merely to satisfy this proposed structure.

Every file must have a purpose.

Avoid documentation fragmentation.

---

# 4. SKILL.MD DESIGN

`SKILL.md` must remain the orchestration layer.

It should NOT become an encyclopedia.

Prefer fewer than approximately 500 lines when practical.

The body should contain:

## Metadata

A precise:

```yaml
---
name: backend-patterns
description: ...
---
```

The description must clearly communicate:

* what the skill does;
* situations that should activate it;
* situations that should not activate it.

Activation must work for implicit intent, not only explicit mentions of "backend patterns".

Examples of likely activation:

* designing backend architecture;
* refactoring backend architecture;
* choosing service boundaries;
* designing APIs;
* deciding transaction strategies;
* implementing asynchronous workflows;
* introducing messaging;
* addressing concurrency;
* deciding cache architecture;
* dealing with distributed consistency;
* designing idempotent operations;
* improving resilience;
* decomposing monoliths;
* deciding repository/service/domain boundaries;
* evaluating architectural anti-patterns.

Avoid over-triggering on trivial backend edits.

---

# 5. CORE EXECUTION MODEL

Every invocation should conceptually follow:

```text
DISCOVER
  ↓
CLASSIFY
  ↓
MODEL CONSTRAINTS
  ↓
IDENTIFY FORCES
  ↓
GENERATE CANDIDATE PATTERNS
  ↓
ELIMINATE UNSUITABLE PATTERNS
  ↓
SELECT MINIMUM SUFFICIENT DESIGN
  ↓
IMPLEMENT / GUIDE
  ↓
VERIFY
  ↓
CHALLENGE
  ↓
REPORT EVIDENCE
```

This workflow is mandatory.

---

# 6. PHASE A — DISCOVER

Before selecting patterns, inspect the actual system.

Determine:

* language;
* framework;
* runtime;
* persistence layer;
* deployment architecture;
* API style;
* messaging infrastructure;
* caching infrastructure;
* concurrency model;
* consistency requirements;
* scale;
* latency requirements;
* throughput requirements;
* reliability expectations;
* security boundaries;
* compatibility constraints;
* migration constraints;
* operational environment.

Never recommend architecture based solely on generic preferences.

---

# 7. PHASE B — PROBLEM CLASSIFICATION

Classify the problem into one or more categories.

Examples:

* domain modeling;
* modularity;
* dependency direction;
* API boundary;
* persistence;
* querying;
* transactional integrity;
* cross-service consistency;
* concurrency;
* asynchronous processing;
* messaging;
* retries;
* workflow coordination;
* resilience;
* caching;
* rate limiting;
* authentication boundary;
* authorization boundary;
* tenant isolation;
* observability;
* scalability;
* performance;
* migration;
* backward compatibility;
* testing;
* deployment evolution.

Classification determines which references should be loaded.

Do not load every reference by default.

---

# 8. PHASE C — MODEL THE FORCES

For every architectural decision, identify the forces influencing it.

Possible forces include:

* consistency;
* availability;
* latency;
* throughput;
* developer cognitive load;
* deployment independence;
* domain ownership;
* failure isolation;
* operational complexity;
* data locality;
* transactional scope;
* retry behavior;
* infrastructure maturity;
* cost;
* team size;
* expected growth;
* blast radius;
* observability;
* testability;
* migration risk.

Do not recommend a pattern without connecting it to forces.

---

# 9. PHASE D — PATTERN CANDIDATES

Support reasoning across at least the following families.

## Architectural structure

* Layered Architecture
* Modular Monolith
* Hexagonal Architecture
* Ports and Adapters
* Clean Architecture
* Onion Architecture
* Vertical Slice Architecture
* Domain-oriented modules
* Service-oriented architecture
* Microservices
* Event-driven architecture

The skill MUST understand that these are not mutually exclusive in every case.

---

# 10. DOMAIN PATTERNS

Cover when appropriate:

* Entities
* Value Objects
* Aggregates
* Aggregate Roots
* Domain Services
* Application Services
* Domain Events
* Factories
* Specifications
* Policies
* Repositories
* Anti-Corruption Layer
* Bounded Contexts

Avoid forcing full DDD onto simple CRUD systems.

Explicitly distinguish:

```text
DDD useful
vs.
DDD ceremony
```

---

# 11. API PATTERNS

Cover:

* REST resource modeling;
* RPC;
* gRPC;
* GraphQL;
* command endpoints;
* query endpoints;
* API composition;
* pagination;
* filtering;
* sorting;
* versioning;
* error contracts;
* request validation;
* idempotency keys;
* optimistic concurrency;
* conditional requests;
* rate limits;
* async APIs;
* webhook design;
* backward compatibility.

Require stable contracts.

Explicitly reason about API evolution.

---

# 12. DATA ACCESS PATTERNS

Cover:

* Repository;
* Unit of Work;
* Data Mapper;
* Active Record;
* Query Object;
* Specification;
* CQRS;
* read models;
* materialized views;
* database views;
* direct SQL;
* ORM usage;
* transaction boundaries.

The skill must know when repository abstractions add no value.

Never automatically wrap an ORM with redundant layers.

---

# 13. TRANSACTION PATTERNS

Provide strong reasoning about:

* ACID transactions;
* local transactions;
* distributed transactions;
* Saga;
* orchestration;
* choreography;
* transactional outbox;
* inbox pattern;
* compensation;
* retry boundaries;
* deduplication;
* idempotent consumers.

Require explicit transaction boundaries.

For distributed changes, always answer:

```text
What happens if failure occurs after step N but before step N+1?
```

---

# 14. CONSISTENCY PATTERNS

Support:

* strong consistency;
* eventual consistency;
* read-your-writes;
* monotonic reads;
* optimistic concurrency;
* pessimistic locking;
* compare-and-swap;
* version columns;
* conflict detection;
* conflict resolution;
* distributed coordination where truly necessary.

Never hide consistency assumptions.

---

# 15. CONCURRENCY PATTERNS

Cover:

* optimistic locking;
* pessimistic locking;
* leases;
* mutex boundaries;
* database locks;
* advisory locks;
* compare-and-swap;
* immutable data;
* work queues;
* actor-like ownership;
* single-writer patterns.

Detect:

* race conditions;
* lost updates;
* double processing;
* check-then-act bugs;
* TOCTOU problems.

---

# 16. MESSAGING PATTERNS

Cover:

* producer/consumer;
* pub/sub;
* work queues;
* competing consumers;
* dead-letter queues;
* delayed retry;
* poison-message handling;
* transactional outbox;
* inbox;
* idempotent consumer;
* correlation IDs;
* causation IDs;
* event versioning;
* schema evolution.

Explicitly reject the myth of magical "exactly once" processing.

Prefer designs safe under duplicate delivery.

---

# 17. RESILIENCE PATTERNS

Support:

* timeout;
* retry;
* exponential backoff;
* jitter;
* circuit breaker;
* bulkhead;
* load shedding;
* backpressure;
* rate limiting;
* graceful degradation;
* fallback;
* fail-fast;
* health checks;
* readiness checks.

Critical rule:

Never recommend retries without checking idempotency and retry amplification.

Never stack retries blindly across layers.

---

# 18. CACHING PATTERNS

Cover:

* cache-aside;
* read-through;
* write-through;
* write-behind;
* local cache;
* distributed cache;
* request memoization;
* TTL;
* invalidation strategies;
* stampede prevention;
* stale-while-revalidate.

Every cache recommendation must answer:

* source of truth;
* invalidation mechanism;
* stale-data tolerance;
* cache failure behavior;
* stampede behavior.

---

# 19. DISTRIBUTED SYSTEMS REASONING

The skill must recognize relevant distributed-systems realities:

* partial failure;
* unreliable networks;
* duplicate delivery;
* message reordering;
* clock uncertainty;
* stale reads;
* split brain;
* network partitions;
* independent service failure;
* retry storms;
* cascading failure;
* backpressure;
* load imbalance.

Avoid pretending local-process assumptions hold across network boundaries.

---

# 20. SECURITY AS AN ARCHITECTURAL CONSTRAINT

`backend-patterns` is not the security specialist, but it must be security-aware.

Every significant design should consider:

* trust boundaries;
* authentication boundaries;
* authorization;
* object-level authorization;
* property-level authorization;
* tenant isolation;
* least privilege;
* secrets;
* input validation;
* injection;
* SSRF;
* resource exhaustion;
* abuse prevention;
* rate limiting;
* unsafe third-party APIs;
* sensitive-data exposure;
* auditability.

Escalate deep security review to `security-engineering-vNext` when available.

Do not silently assume another skill will catch security defects.

---

# 21. OBSERVABILITY PATTERNS

Production architecture must be observable.

Consider:

* structured logs;
* metrics;
* traces;
* correlation IDs;
* request IDs;
* causation IDs;
* service-level indicators;
* service-level objectives;
* error budgets;
* dashboards;
* actionable alerts.

The skill should ask:

> If this design fails in production, how will an engineer know where and why?

---

# 22. PERFORMANCE PATTERNS

Never perform speculative optimization.

Reason from:

* measured latency;
* measured throughput;
* query plans;
* profiling;
* allocation behavior;
* network calls;
* database calls;
* serialization costs;
* contention;
* queue depth;
* cache hit rates.

Separate:

```text
performance requirement
from
performance guess
```

---

# 23. MIGRATION PATTERNS

Architecture must consider safe evolution.

Support:

* expand/contract;
* parallel change;
* compatibility windows;
* feature flags;
* shadow traffic;
* dual reads;
* dual writes only with explicit risk analysis;
* backfills;
* migration checkpoints;
* reversible migrations;
* strangler pattern;
* branch by abstraction.

Prefer incremental migration over "rewrite everything" unless evidence strongly justifies the rewrite.

---

# 24. PATTERN SELECTION MATRIX

Create a high-quality decision matrix.

Every important pattern should contain:

```text
PATTERN
Problem solved
Context
Forces
When to use
When NOT to use
Benefits
Costs
Failure modes
Security implications
Operational implications
Testing implications
Migration implications
Observability implications
Alternatives
Evidence required
```

This is critical.

A State-of-the-Art skill must teach the agent when NOT to use a pattern.

---

# 25. MINIMUM SUFFICIENT ARCHITECTURE

Introduce the principle:

> Select the least complex architecture that satisfies the actual requirements and foreseeable constraints.

The skill must resist:

* microservice enthusiasm;
* premature CQRS;
* premature event sourcing;
* unnecessary abstraction;
* unnecessary repository layers;
* unnecessary factories;
* unnecessary service objects;
* distributed systems without distributed requirements;
* queues where direct calls suffice;
* caching without demonstrated need;
* sophisticated consistency mechanisms without a consistency problem.

---

# 26. ANTI-PATTERN ENGINE

Create explicit backend anti-pattern recognition.

Include at least:

* God Service;
* God Repository;
* Fat Controller;
* Anemic Domain Model when domain logic genuinely exists;
* distributed monolith;
* shared database across independently deployed services;
* database as integration bus;
* chatty services;
* synchronous chain explosion;
* retry storms;
* cache as source of truth;
* dual-write inconsistency;
* fire-and-forget critical operations;
* hidden transaction boundaries;
* leaky abstractions;
* service locator;
* premature microservices;
* premature CQRS;
* cargo-cult DDD;
* generic repository abuse;
* abstraction for abstraction's sake;
* unbounded queues;
* missing timeouts;
* missing backpressure;
* unversioned events;
* giant shared "common" packages.

For each anti-pattern:

```text
symptom
why it happens
why it is dangerous
how to detect it
safe alternatives
migration strategy
```

---

# 27. RATIONALIZATION DEFENSE

Agents often skip engineering discipline.

Add an explicit anti-rationalization section.

Examples:

| Rationalization                  | Required response                                                                        |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| "It's just a small service."     | Small services still require explicit failure and transaction boundaries where relevant. |
| "Retries will make it reliable." | Verify idempotency and retry amplification first.                                        |
| "Microservices scale better."    | Demonstrate independent scaling or ownership requirement.                                |
| "CQRS is cleaner."               | Demonstrate asymmetric read/write complexity that justifies it.                          |
| "We'll fix observability later." | Production-critical paths require observability before claiming readiness.               |
| "The ORM handles transactions."  | Identify the actual transaction boundary and failure semantics.                          |
| "The broker gives exactly-once." | Design consumers to tolerate duplicates unless semantics are formally proven.            |
| "A repository is best practice." | Demonstrate abstraction value beyond wrapping the ORM.                                   |
| "Eventual consistency is fine."  | Identify which stale states are acceptable and for how long.                             |

Expand this set intelligently.

---

# 28. NEGATIVE GUIDANCE

The skill MUST contain strong "do not" guidance.

Example:

```text
DO NOT:
- introduce a message broker merely to decouple two local modules;
- split services before domain or operational boundaries justify it;
- use distributed transactions casually;
- create retries around non-idempotent operations;
- store secrets in application configuration committed to source control;
- add cache layers without defining invalidation;
- emit domain events before the owning transaction commits unless semantics explicitly require it;
- swallow errors to improve perceived availability;
- implement asynchronous workflows without defining failure recovery.
```

Negative knowledge is as valuable as positive patterns.

---

# 29. DESIGN DECISION RECORD

For non-trivial decisions, produce a lightweight pattern decision record:

```text
Problem:
Constraints:
Forces:
Candidate patterns:
Rejected patterns:
Selected pattern:
Why:
Trade-offs:
Failure modes:
Security impact:
Operational impact:
Migration impact:
Verification:
```

Do not create verbose ADR bureaucracy for trivial changes.

---

# 30. VERIFICATION-FIRST ENGINEERING

No architecture decision is complete merely because code compiles.

Verification must correspond to the pattern.

Examples:

Transactional pattern:

* rollback tests;
* partial-failure tests;
* concurrency tests.

Idempotency:

* duplicate request tests;
* duplicate message tests.

Outbox:

* crash-after-commit scenarios;
* duplicate publication;
* restart recovery.

Retry:

* transient failure;
* permanent failure;
* retry exhaustion;
* jitter/backoff behavior.

Concurrency:

* race tests;
* conflicting updates;
* stale version rejection.

Cache:

* cache miss;
* stale cache;
* cache unavailable;
* stampede conditions.

API:

* compatibility;
* invalid input;
* authorization boundaries;
* pagination boundaries;
* concurrency semantics.

Messaging:

* duplication;
* reorder;
* poison message;
* broker unavailability;
* consumer restart.

---

# 31. ADVERSARIAL VERIFICATION

Create adversarial scenarios that attempt to disprove the architecture.

Ask:

* what if the process crashes here?
* what if the network times out?
* what if the database commits but the broker call fails?
* what if the broker redelivers?
* what if two requests arrive simultaneously?
* what if this dependency becomes slow?
* what if the cache disappears?
* what if a malicious client changes this identifier?
* what if a downstream service returns malformed data?
* what if a deployment contains old and new versions simultaneously?
* what if a migration is interrupted halfway?
* what if traffic increases 10×?
* what if retry traffic amplifies an outage?

Passing happy-path unit tests is insufficient.

---

# 32. FAILURE-MODE MATRIX

For significant flows, reason using:

```text
Component
Failure
Detection
Containment
Recovery
Data integrity impact
User-visible impact
Observability evidence
```

The skill should encourage failure containment rather than assuming failure prevention.

---

# 33. COMPOSITION WITH BACKEND-ENGINEERING-vNEXT

`backend-patterns` should provide architectural pattern judgment.

`backend-engineering-vNext` should remain responsible for broader implementation engineering.

Expected composition:

```text
backend-engineering-vNext
        ↓
backend-patterns
        ↓
implementation
        ↓
security-engineering-vNext
        ↓
verification-loop-vNext
        ↓
repair
        ↓
final assurance
```

Avoid circular orchestration.

Define explicit handoff contracts.

Example backend-patterns output:

```yaml
architecture_decision:
  selected_patterns:
  rejected_patterns:
  invariants:
  transaction_boundaries:
  consistency_model:
  failure_semantics:
  security_constraints:
  observability_requirements:
  verification_requirements:
  unresolved_risks:
```

Use the repository's actual conventions if another format already exists.

---

# 34. COMPOSITION WITH SECURITY

When risk thresholds are crossed, hand off to security specialists.

Examples:

* authentication changes;
* authorization;
* multi-tenancy;
* secrets;
* external URL fetches;
* file handling;
* payment flows;
* sensitive data;
* webhook verification;
* privileged operations;
* service-to-service trust;
* untrusted third-party integrations.

Backend-patterns should surface risks, not attempt to replace dedicated security engineering.

---

# 35. COMPOSITION WITH VERIFICATION LOOP

Provide verification-loop-vNext with explicit claims to challenge.

Example:

```text
CLAIM:
duplicate webhook delivery cannot create duplicate order

MECHANISM:
idempotency key + unique database constraint

EXPECTED EVIDENCE:
two identical concurrent requests create one order only
```

This allows verification to test architecture claims rather than merely rerun generic tests.

---

# 36. INVARIANT-FIRST THINKING

Encourage explicit invariants.

Examples:

```text
A payment is captured at most once.

An order transitions only through legal states.

A user cannot access another tenant's objects.

An event is not permanently lost after transaction commit.

Duplicate delivery does not duplicate side effects.

Inventory cannot become negative unless overselling is explicitly supported.
```

Then derive architecture and tests from those invariants.

This should be one of the strongest capabilities of the skill.

---

# 37. FRAMEWORK-INDEPENDENT CORE

The core skill must remain architecture- and language-oriented.

Do not make it:

* Node.js-patterns;
* Python-patterns;
* Java-patterns;
* Go-patterns.

Patterns should transfer across stacks.

Framework-specific examples can exist in optional references where repository conventions justify them.

Potential stacks:

* Python / FastAPI / Django;
* Node / TypeScript / NestJS / Express;
* Java / Spring;
* Go;
* Rust;
* .NET;
* Ruby;
* PHP;
* Odoo.

Framework-specific material must never dominate the core skill.

---

# 38. BROWNFIELD-FIRST REALITY

The skill must work extremely well with existing systems.

Before recommending architectural replacement, identify:

* existing conventions;
* public contracts;
* database constraints;
* dependency graph;
* deployment topology;
* tests;
* migration limitations;
* operational dependencies.

Prefer incremental improvement.

Respect Chesterton's Fence:

Do not remove an existing architectural mechanism before understanding why it exists.

---

# 39. ARCHITECTURE CHANGE BUDGET

Introduce a complexity-budget concept.

Every new abstraction has cost.

For a proposed pattern estimate qualitatively:

```text
Implementation complexity
Operational complexity
Cognitive complexity
Migration complexity
Runtime complexity
Testing complexity
```

The pattern must provide enough benefit to justify its total cost.

---

# 40. MICROservices DECISION GATE

Microservices require explicit justification.

Before recommending them, demand evidence for one or more:

* independent deployment;
* independent scaling;
* fault isolation;
* different reliability requirements;
* strong bounded contexts;
* team ownership boundaries;
* regulatory isolation;
* technology isolation with real benefit.

If these forces are absent, prefer modularity inside a monolith.

---

# 41. CQRS DECISION GATE

CQRS should require evidence such as:

* dramatically different read/write models;
* read scaling pressure;
* complex domain commands;
* multiple specialized projections;
* asynchronous workflows;
* valuable separation of consistency models.

Otherwise reject it.

---

# 42. EVENT SOURCING DECISION GATE

Event sourcing must NOT be treated as default advanced architecture.

Require strong justification such as:

* immutable audit history as core domain requirement;
* temporal reconstruction;
* event-native domain;
* complex state evolution that benefits from event history.

Require discussion of:

* schema evolution;
* event migration;
* projection rebuilds;
* storage growth;
* replay semantics;
* privacy/deletion requirements;
* operational debugging.

---

# 43. DATABASE DECISION QUALITY

Avoid dogma like:

```text
SQL always
NoSQL always
ORM always
raw SQL always
```

Reason from access patterns and guarantees.

Evaluate:

* relational constraints;
* transactional needs;
* query flexibility;
* consistency;
* expected scale;
* indexing;
* partitioning;
* availability requirements;
* operational maturity.

---

# 44. API EVOLUTION

The skill must strongly protect compatibility.

Check:

* additive vs breaking changes;
* old clients;
* version skew;
* deployment skew;
* schema evolution;
* event evolution;
* default values;
* tolerant readers where appropriate;
* deprecation windows.

For distributed deployments assume mixed versions can coexist.

---

# 45. OPERABILITY GATE

Before claiming production readiness, ask:

```text
How is this deployed?
How is it rolled back?
How is failure detected?
How is it debugged?
How is data repaired?
How are stuck workflows recovered?
How are queues drained?
How are migrations resumed?
How is a bad release contained?
```

Architecture without operability is incomplete.

---

# 46. PRODUCTION READINESS SCORECARD

Create a scorecard covering at least:

* correctness;
* data integrity;
* concurrency safety;
* API stability;
* security;
* failure handling;
* retry safety;
* idempotency;
* observability;
* operability;
* scalability;
* performance;
* migration safety;
* testability;
* simplicity.

Do not claim Triple-A based solely on documentation quality.

---

# 47. TEST THE SKILL ITSELF

Do not only test code examples.

Test the skill's reasoning behavior.

Create fixtures/prompts for:

### Positive activation

Examples:

* "Design the transaction flow for order creation and Kafka publishing."
* "Should we split this monolith into microservices?"
* "How should duplicate Stripe-style webhooks be processed?"
* "Refactor this backend into safer module boundaries."
* "We keep getting duplicate jobs after retries."

### Negative activation

Examples:

* rename a variable;
* fix typo;
* update README;
* trivial isolated formatting;
* simple frontend styling.

### Pattern-selection tests

Verify that expected patterns are recommended under suitable conditions.

### Pattern-rejection tests

Verify that sophisticated patterns are rejected where unnecessary.

### Adversarial tests

Attempt to make the skill recommend:

* microservices for a tiny application;
* event sourcing for CRUD;
* retries on unsafe non-idempotent writes;
* repository wrapping an ORM with no abstraction benefit;
* distributed locking where database uniqueness suffices.

The skill should resist.

---

# 48. EVALUATION RUBRIC

Build a deterministic evaluation rubric where possible.

Evaluate responses against:

```text
Correct trigger
Correct problem classification
Constraints discovered
Forces identified
Reasonable candidate set
Rejected alternatives explained
Minimum sufficient solution selected
Failure modes identified
Security implications addressed
Observability addressed
Verification requirements specified
No unjustified complexity introduced
```

Create measurable pass/fail conditions whenever practical.

---

# 49. RED-TEAM THE SKILL

After implementation, attack the skill itself.

Try to induce:

* cargo cult;
* overengineering;
* underengineering;
* generic recommendations;
* pattern name-dropping;
* framework bias;
* unnecessary microservices;
* inappropriate event sourcing;
* hidden consistency assumptions;
* missing transaction boundaries;
* unsafe retries;
* fake observability;
* security blindness;
* verification theater.

Repair weaknesses discovered.

Repeat until major failure classes are closed.

---

# 50. NO VERIFICATION THEATER

Forbidden conclusions:

* "looks correct";
* "appears production-ready";
* "should work";
* "seems robust";
* "tests would likely pass".

Require evidence.

Evidence may include:

* unit tests;
* integration tests;
* concurrency tests;
* property tests;
* contract tests;
* failure-injection tests;
* runtime tests;
* static analysis;
* schema validation;
* architecture tests;
* deterministic skill evals.

---

# 51. QUALITY GATES

The skill cannot be declared complete until all applicable gates pass.

## Gate A — Structure

* valid SKILL.md;
* correct metadata;
* references reachable;
* no orphan files.

## Gate B — Activation

* positive triggers work;
* negative triggers stay quiet;
* ambiguous triggers behave sensibly.

## Gate C — Knowledge

* major backend pattern families covered;
* meaningful negative guidance included;
* anti-pattern catalog included.

## Gate D — Judgment

* demonstrates pattern selection;
* demonstrates pattern rejection;
* minimizes unnecessary complexity.

## Gate E — Distributed systems

* partial failures;
* retries;
* duplication;
* ordering;
* consistency;
* concurrency;
* recovery addressed.

## Gate F — Security

* trust boundaries;
* auth/authz;
* SSRF;
* injection;
* abuse/resource consumption;
* third-party trust considered where applicable.

## Gate G — Reliability

* timeout;
* retry;
* backpressure;
* overload;
* recovery;
* observability.

## Gate H — Verification

* architecture claims map to evidence.

## Gate I — Composition

* backend-engineering-vNext integration;
* security handoff;
* verification-loop handoff.

## Gate J — Maintainability

* progressive disclosure;
* minimal duplication;
* clear ownership.

---

# 52. TRIPLE-A DEFINITION

For this task, Triple-A means:

## AAA — Architectural Intelligence

The skill makes expert-level architectural decisions rather than listing patterns.

## AAA — Assurance

Every important recommendation produces verifiable engineering claims.

## AAA — Agent Engineering

The skill is optimized for agent consumption:

* precise activation;
* progressive disclosure;
* bounded context usage;
* deterministic workflows;
* explicit exits;
* anti-rationalization;
* composability.

The skill must satisfy all three.

---

# 53. DEFINITION OF DONE

Do NOT claim completion unless:

1. existing implementation was audited;
2. repository conventions were respected;
3. backend-patterns has clear scope;
4. SKILL.md activation is precise;
5. progressive disclosure is implemented;
6. core pattern families are covered;
7. anti-patterns are encoded;
8. negative guidance exists;
9. transaction reasoning exists;
10. consistency reasoning exists;
11. concurrency reasoning exists;
12. distributed failure reasoning exists;
13. resilience reasoning exists;
14. security constraints exist;
15. observability is included;
16. migration safety is included;
17. minimum-sufficient-architecture principle exists;
18. pattern-selection matrix exists;
19. verification requirements exist;
20. adversarial tests exist;
21. skill-level evaluation exists;
22. composition contracts exist;
23. backend-engineering-vNext composition works or is demonstrably specified;
24. security-engineering-vNext handoff works or is demonstrably specified;
25. verification-loop-vNext handoff works or is demonstrably specified;
26. regression tests pass;
27. validation scripts pass;
28. no unexplained critical risks remain.

---

# 54. FINAL ASSURANCE REPORT

At completion produce:

```text
BACKEND-PATTERNS STATE-OF-THE-ART ASSURANCE REPORT

Baseline score:
Final score:

Files created:
Files modified:
Files removed:

Architecture:
Activation model:
Progressive disclosure:
Pattern families:
Anti-pattern coverage:

Selection tests:
Rejection tests:
Adversarial tests:
Regression tests:

Backend-engineering-vNext composition:
Security-engineering-vNext composition:
Verification-loop-vNext composition:

Security review:
Reliability review:
Distributed-systems review:
Operability review:

Known limitations:
Residual risks:

Evidence:
Commands executed:
Relevant outputs:

Final score:
/100

Verdict:
NOT READY
READY
STATE-OF-THE-ART
TRIPLE-A
```

Do not assign `TRIPLE-A` unless the evidence supports it.

---

# 55. EXECUTION MODE

Work autonomously through:

```text
DISCOVER
→ AUDIT
→ DESIGN
→ IMPLEMENT
→ VALIDATE
→ TEST
→ COMPOSE
→ ADVERSARIAL EVALUATION
→ REPAIR
→ REGRESSION
→ FINAL ASSURANCE
```

Do not stop after planning.

Do not stop after writing SKILL.md.

Do not stop after tests first pass.

Continue through verification and hardening.

When a defect is found:

```text
OBSERVE
→ IDENTIFY ROOT CAUSE
→ REPAIR
→ ADD REGRESSION COVERAGE
→ RE-RUN RELEVANT GATES
```

---

# 56. FINAL PRINCIPLE

The finished `backend-patterns` skill should cause an agent to behave as if an experienced Principal Backend Engineer were reviewing the architecture and repeatedly asking:

> What problem are we actually solving?

> What invariants must never be violated?

> What is the simplest architecture that preserves those invariants?

> Where are the transaction and trust boundaries?

> What happens under concurrency?

> What happens under partial failure?

> What happens when this operation executes twice?

> What happens while old and new versions coexist?

> How will we detect failure in production?

> How will we recover?

> What evidence proves the design works?

If the skill cannot reliably drive those questions and turn their answers into implementation constraints and verification evidence, it is not yet State-of-the-Art.

Begin by inspecting the repository and existing skills.

Do not assume.

Measure first.

Then build.
