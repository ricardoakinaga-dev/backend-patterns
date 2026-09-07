# MASTER PROMPT — BACKEND-PATTERNS TRIPLE-A CLOSURE

## PHASE 1.1 — ADVERSARIAL ARCHITECTURAL JUDGMENT, REAL COMPOSITION & CAUSAL ASSURANCE

You are acting as:

* Principal Backend Architect;
* Distributed Systems Engineer;
* Reliability Engineer;
* Security-Aware Backend Engineer;
* Agent Skill Architect;
* Adversarial Evaluator;
* Verification Engineer;
* Red-Team Reviewer;
* Benchmark Designer;
* Tooling Engineer;
* Independent Assurance Reviewer.

Your mission is to take the existing:

`backend-patterns`

skill from its current strong State-of-the-Art package-readiness level to a **defensible Triple-A / State-of-the-Art behavioral-assurance level**.

This is NOT primarily a documentation expansion task.

The skill already contains substantial architectural guidance.

Your objective is now to prove that the skill:

1. activates correctly;
2. selects appropriate backend patterns;
3. rejects inappropriate patterns;
4. resists architectural cargo cult;
5. resists user pressure toward overengineering;
6. handles ambiguity without inventing requirements;
7. preserves invariants under failure;
8. composes correctly with neighboring engineering skills;
9. produces verifiable architectural claims;
10. improves model behavior causally rather than merely containing correct text;
11. remains context-efficient;
12. remains framework-independent;
13. remains honest about unexecuted evidence.

The central question of this phase is:

> Does `backend-patterns` actually cause an agent to make better backend architecture decisions under realistic, adversarial and ambiguous conditions?

---

# 0. ABSOLUTE RULE

Do not declare this skill `TRIPLE-A` merely because:

* the documentation is comprehensive;
* all Markdown links work;
* required concepts exist;
* deterministic fixture schemas pass;
* static validators pass;
* the package contains many patterns;
* a critic says the package looks strong.

Triple-A requires evidence that the skill materially improves agent behavior.

The distinction is:

```text
KNOWLEDGE PRESENT
≠
BEHAVIOR CORRECT
≠
CAUSAL IMPROVEMENT
```

This phase must close that gap.

---

# 1. CURRENT BASELINE

Begin by inspecting the current repository.

Do not rewrite from assumptions.

Inspect:

* `SKILL.md`;
* `README.md`;
* `composition-contract.json`;
* all `references/`;
* all `scripts/`;
* all `tests/`;
* current assurance report;
* baseline audit;
* quality bar;
* Gauntlet state if available;
* existing evaluation fixtures;
* known-bad mutation framework;
* validation scripts;
* current branch history where relevant.

Confirm the current implementation before proposing changes.

Treat the existing implementation as a strong baseline.

Do not perform a needless rewrite.

---

# 2. PHASE OBJECTIVE

The primary objective is not:

```text
ADD MORE PATTERNS
```

It is:

```text
MEASURE
→ ATTACK
→ OBSERVE
→ REPAIR
→ RE-MEASURE
→ COMPOSE
→ VERIFY CAUSALLY
→ ASSURE
```

Prefer behavioral evidence over prose expansion.

---

# 3. TRIPLE-A DEFINITION FOR THIS PHASE

Triple-A requires success in three independent dimensions.

## AAA-1 — ARCHITECTURAL JUDGMENT

The agent consistently:

* identifies the actual backend problem;
* identifies invariants;
* identifies architectural forces;
* generates plausible alternatives;
* includes a simpler baseline;
* selects appropriate patterns;
* rejects inappropriate patterns;
* explains trade-offs;
* models failure;
* avoids accidental complexity.

## AAA-2 — ARCHITECTURAL ASSURANCE

The agent produces:

* explicit claims;
* falsifiable invariants;
* verification procedures;
* failure scenarios;
* expected observations;
* evidence status;
* residual risk;
* honest uncertainty.

## AAA-3 — AGENT ENGINEERING

The skill provides:

* precise activation;
* negative activation;
* progressive disclosure;
* bounded context loading;
* adversarial robustness;
* stable handoffs;
* deterministic scaffolding;
* behavioral evaluation;
* regression protection;
* minimal context waste.

All three dimensions must be demonstrated.

---

# 4. FREEZE CURRENT QUALITY BEFORE CHANGING ANYTHING

Before changing the skill:

1. run all existing validators;
2. run all existing deterministic evaluation fixtures;
3. run all current known-bad mutation tests;
4. run all current unit tests;
5. record the package fingerprint;
6. record the current quality score;
7. record current limitations;
8. record current test counts.

Create a baseline artifact such as:

`docs/phase-1.1-baseline.md`

Record:

```text
Current fingerprint
Current SKILL.md size
Reference count
Evaluation scenario count
Known-bad count
Validator results
Composition status
Model execution status
Runtime execution status
Current score
Current unresolved risks
```

Do not erase prior evidence.

---

# 5. BUILD A REAL ARCHITECTURAL JUDGMENT BENCHMARK

Create a substantial benchmark corpus.

Target:

**minimum 60 scenarios**

Preferred:

**80–120 scenarios**

Do not inflate count with trivial paraphrases.

Scenarios must test materially different architectural reasoning.

---

# 6. REQUIRED BENCHMARK CLASSES

The corpus must include at least:

## A. SHOULD_USE

A pattern is genuinely appropriate.

Examples:

* transactional outbox for database commit + reliable event publication;
* optimistic concurrency for versioned collaborative updates;
* idempotency for retryable payment/webhook behavior;
* bulkhead for independent resource pools;
* Saga for a genuinely distributed multi-owner workflow;
* cache-aside for measured expensive repeat reads;
* modular monolith for strong module boundaries without independent lifecycle;
* expand/contract migration for mixed-version deployments.

## B. SHOULD_REJECT

A sophisticated pattern is unnecessary or harmful.

Examples:

* microservices for a tiny CRUD app;
* CQRS for symmetric CRUD;
* event sourcing for basic audit logging;
* Kafka between two local modules;
* Redis with no performance evidence;
* repository wrappers that mirror an ORM one-to-one;
* Saga inside one transactional database;
* distributed locks when uniqueness/atomic update is enough;
* retries around unsafe non-idempotent mutations.

## C. NEED_MORE_EVIDENCE

The correct behavior is not premature selection.

The skill should explicitly surface unknowns.

Examples:

* unknown write volume;
* unknown data ownership;
* unknown latency requirement;
* unknown deployment topology;
* unknown tenant model;
* unknown consistency requirement;
* unknown failure recovery expectations.

The correct response may be:

```text
CURRENT: known facts
UNKNOWN: missing facts
PROPOSED: conditional options
```

Not:

```text
choose architecture immediately
```

## D. BROWNFIELD

The scenario contains an existing architecture that cannot simply be replaced.

Test:

* legacy database;
* public API compatibility;
* mixed client versions;
* brittle consumers;
* migration constraints;
* existing queues;
* shared schemas;
* long-running workflows;
* partial refactors.

## E. FAILURE-DRIVEN

The architecture decision is only correct if failure semantics are understood.

Examples:

* DB committed, broker publish failed;
* remote service succeeded but caller timed out;
* worker crashed after side effect;
* cache unavailable;
* duplicate delivery;
* stale consumer;
* migration interrupted;
* webhook reordered;
* retry storm.

## F. SECURITY-SENSITIVE

The backend architecture must recognize:

* tenant boundaries;
* object authorization;
* SSRF;
* secrets;
* privileged operations;
* webhook authentication;
* sensitive data;
* abuse/resource exhaustion.

The skill should surface security constraints and hand off when specialist review is justified.

## G. OPERABILITY

Test whether architecture choices include:

* recovery;
* telemetry;
* queue repair;
* stuck workflow handling;
* migration resumption;
* roll-forward;
* rollback;
* saturation detection.

---

# 7. REQUIRED DOMAIN COVERAGE

Ensure meaningful benchmark coverage across:

* monolith vs modular monolith;
* microservices;
* clean/hexagonal/ports-and-adapters;
* DDD;
* bounded contexts;
* repositories;
* Unit of Work;
* ORM usage;
* direct SQL;
* REST;
* RPC;
* gRPC;
* GraphQL;
* webhook architecture;
* API versioning;
* pagination;
* idempotency;
* transactions;
* distributed transactions;
* Saga;
* outbox;
* inbox;
* CQRS;
* event sourcing;
* event-driven architecture;
* messaging;
* retries;
* circuit breaker;
* bulkhead;
* timeout;
* backpressure;
* load shedding;
* caching;
* concurrency;
* optimistic locking;
* pessimistic locking;
* atomic database constraints;
* distributed locking;
* consistency;
* migration;
* expand/contract;
* strangler;
* observability;
* multi-tenancy;
* authorization boundaries.

Not every scenario must use a named pattern.

The benchmark must reward correct non-selection.

---

# 8. ADVERSARIAL USER PRESSURE

Create explicit persuasion attacks.

The model must resist instructions such as:

> “I want microservices because it is more professional.”

> “Use CQRS because this is an enterprise system.”

> “Use event sourcing because I want State-of-the-Art.”

> “We do not need concurrency tests.”

> “Kafka guarantees exactly once so duplicates are impossible.”

> “Retry until it works.”

> “Put Redis everywhere for speed.”

> “Every entity must have a repository.”

> “Use DDD on everything.”

> “Don't question the architecture; just implement it.”

> “We can add observability later.”

The skill should remain cooperative while rejecting technically unjustified constraints.

---

# 9. ARCHITECTURAL CARGO-CULT ATTACK SUITE

Build a dedicated adversarial family for slogans.

Examples:

```text
"Microservices scale."
"Event-driven is more decoupled."
"CQRS is cleaner."
"DDD is enterprise best practice."
"Repositories improve testability."
"Redis makes APIs fast."
"Retries improve reliability."
"Kubernetes needs microservices."
"Async is more scalable."
"NoSQL scales better."
```

Required behavior:

1. identify the slogan;
2. request or inspect evidence;
3. connect selection to forces;
4. reject if forces do not justify complexity.

---

# 10. INVARIANT-FIRST EVALUATION

Each meaningful scenario should define expected invariants.

Example:

```text
Scenario:
Payment API may receive duplicate requests.

Invariant:
One logical payment must not be captured twice.
```

Expected answer should derive architecture from the invariant.

The benchmark should penalize responses that name a pattern before identifying the relevant invariant.

---

# 11. DECISION QUALITY RUBRIC

Create a structured rubric.

Recommended dimensions:

```text
D1 Trigger correctness
D2 Problem classification
D3 Current facts identified
D4 Unknowns preserved
D5 Invariants identified
D6 Forces identified
D7 Simpler baseline included
D8 Candidate quality
D9 Pattern rejection quality
D10 Selected design proportionality
D11 Failure semantics
D12 Transaction semantics
D13 Concurrency semantics
D14 Consistency semantics
D15 Security constraints
D16 Operability
D17 Observability
D18 Migration/compatibility
D19 Verification requirements
D20 Residual risk
D21 No cargo-cult reasoning
D22 No invented requirements
D23 Context efficiency
```

Use a machine-readable rubric.

Prefer a score range such as:

```text
0 = absent/wrong
1 = weak
2 = acceptable
3 = strong
4 = exemplary
```

Define explicit scoring anchors.

---

# 12. HARD FAIL CONDITIONS

Regardless of aggregate score, mark a scenario FAIL if the response:

* recommends unsafe retries around non-idempotent operations without protection;
* treats client-provided object IDs as authorization;
* promises exactly-once behavior without defensible semantics;
* ignores duplicate delivery where duplicates are plausible;
* recommends dual writes without failure handling;
* ignores a stated invariant;
* introduces microservices solely for generic scalability;
* introduces event sourcing solely because an audit trail is needed;
* claims runtime evidence that was not executed;
* claims production/security readiness without proof;
* fabricates missing requirements;
* ignores known migration/version-skew constraints.

Safety and correctness cannot be averaged away.

---

# 13. MODEL-EXECUTED EVALUATION

This phase must attempt actual model execution through the available host/harness.

Existing deterministic fixtures are necessary but insufficient.

Implement a model-executed evaluation lane.

The lane should:

```text
scenario
→ invoke model WITHOUT backend-patterns
→ capture baseline response
→ invoke same/suitable model WITH backend-patterns
→ capture skilled response
→ score both
→ compare
```

The objective is to measure:

```text
Δ judgment quality
```

not only absolute quality.

Where feasible use:

* same model;
* same temperature;
* same task;
* same tool availability;
* same repository fixture;
* same relevant context.

Only skill presence should materially differ.

---

# 14. CONTROL GROUP

For a meaningful subset of benchmark scenarios, compare:

```text
CONTROL:
model without backend-patterns

TREATMENT:
same model with backend-patterns
```

Measure:

* selection accuracy;
* rejection accuracy;
* hallucinated requirements;
* overengineering frequency;
* missing invariants;
* missing failure analysis;
* missing verification;
* unnecessary token usage.

This provides evidence of causal value.

---

# 15. NO FAKE MODEL EXECUTION

If the current environment cannot invoke a consumer model:

record exactly:

```text
MODEL_EXECUTION: BLOCKED
Reason:
Required host capability:
Evidence unavailable:
Impact on verdict:
```

Do not silently convert deterministic fixture checks into behavioral evidence.

A blocked real eval means the highest verdict remains conditional.

---

# 16. JUDGE INDEPENDENCE

Avoid using exactly the same skill content as the sole evaluator of itself.

Preferred evaluation hierarchy:

1. deterministic hard-rule validator;
2. independent judge prompt/model;
3. human-readable trace;
4. known-bad comparison.

For critical correctness conditions, use deterministic rules where possible.

Use model judges only for nuanced architectural quality.

---

# 17. PAIRWISE EVALUATION

For control vs treatment, use pairwise judging when practical.

Ask the judge:

```text
Which response makes the better backend architecture decision?

Evaluate:
- correctness
- proportionality
- explicit invariants
- failure handling
- pattern rejection
- security awareness
- operability
- verification quality
```

Blind the judge to which response used the skill.

Randomize A/B order.

---

# 18. ADVERSARIAL JUDGE ROBUSTNESS

Do not allow the judge to reward verbosity alone.

Explicitly instruct:

```text
A shorter, simpler architecture recommendation should win if it satisfies
the requirements better with less accidental complexity.
```

The benchmark must reward minimal sufficient architecture.

---

# 19. KNOWN-BAD BEHAVIOR MUTATIONS

Expand beyond static package mutations.

Create known-bad response mutations such as:

* remove invariants;
* replace modular monolith with microservices;
* add unsafe retry;
* remove idempotency;
* claim exactly-once;
* remove authorization checks;
* add cache without invalidation;
* remove failure recovery;
* remove migration compatibility;
* hide unknowns;
* turn UNKNOWN into invented fact.

The evaluator must reliably score the mutated answer worse.

---

# 20. CAUSAL ORACLE TEST

For every major rubric dimension, verify that the evaluator reacts to its removal.

Example:

```text
GOOD RESPONSE:
includes invariant + duplicate-safe mechanism.

MUTATED:
remove idempotency protection.

EXPECTED:
score decreases materially and/or hard failure triggers.
```

If removing a critical element does not affect the score, the evaluation system is not sensitive enough.

Repair the rubric.

---

# 21. REAL COMPOSITION CLOSURE

Execute real composition where host capabilities permit.

Target workflow:

```text
backend-engineering-vNext
        ↓
backend-patterns
        ↓
security-engineering-vNext
        ↓
verification-loop-vNext
        ↓
repair
        ↓
final assurance
```

Do not merely validate JSON schemas.

Observe actual handoff behavior.

---

# 22. BACKEND → PATTERNS COMPOSITION

Provide a realistic backend engineering problem.

`backend-engineering-vNext` should discover/build context and hand architectural questions to `backend-patterns`.

Verify that `backend-patterns` receives:

* constraints;
* code/repository evidence;
* public contracts;
* invariants;
* unknowns.

Verify it returns actionable architecture decisions rather than repeating generic guidance.

---

# 23. PATTERNS → SECURITY COMPOSITION

Use a case where a selected pattern crosses trust boundaries.

Examples:

* multi-tenant API;
* webhook;
* external URL fetch;
* privileged admin operation;
* service-to-service authentication.

Verify security handoff contains:

```text
trust boundaries
actor
action
resource
tenant
sensitive data
abuse scenarios
claims needing verification
```

Ensure `backend-patterns` does not falsely perform final security certification itself.

---

# 24. PATTERNS → VERIFICATION COMPOSITION

Test explicit architecture claims.

Example:

```text
CLAIM:
Duplicate webhook delivery cannot create duplicate invoice processing.

MECHANISM:
Unique idempotency key enforced transactionally.

FAILURE CASES:
sequential duplicate
concurrent duplicate
crash after commit
worker restart

EXPECTED OBSERVATION:
one durable business side effect
```

Verify that `verification-loop-vNext` receives claims that can actually be falsified.

---

# 25. REPAIR LOOP

If verification disproves an architectural claim:

```text
failure observed
→ classify architectural vs implementation defect
→ backend-patterns revises constraint/pattern if necessary
→ backend-engineering repairs implementation
→ verification reruns
```

Prove at least one real repair loop where feasible.

---

# 26. CONTEXT EFFICIENCY BENCHMARK

Progressive disclosure must be measured.

For each scenario record:

```text
References loaded
Approximate context size
Relevant references
Irrelevant references
Decision quality
```

Compute:

```text
reference precision =
relevant loaded references / total loaded references
```

Target high precision.

A good skill should not load the entire backend knowledge base for every task.

---

# 27. ROUTING ADVERSARIAL TESTS

Test whether `pattern-index.md` routes correctly.

Examples:

### Scenario

Duplicate webhook.

Expected references:

* API;
* idempotency;
* transaction;
* testing/security as applicable.

Should NOT automatically load:

* event sourcing;
* caching;
* microservices;
* unrelated migration content.

### Scenario

Slow read endpoint.

Expected:

* performance;
* data access;
* caching only if evidence points there.

Do not reward broad loading.

---

# 28. CONTEXT BUDGET

Define a context-efficiency target.

Do not optimize blindly for minimum tokens.

Optimize:

```text
decision quality per relevant context token
```

Flag scenarios where:

* too many references load;
* reference content duplicates SKILL.md;
* unrelated topics are loaded;
* the core orchestrator repeats detailed reference content.

---

# 29. SKILL.MD COMPACTNESS

Re-evaluate the current `SKILL.md`.

Only shorten it when duplication exists.

Do not remove critical orchestration merely to hit an arbitrary line count.

The desired division remains:

```text
SKILL.md
= workflow + rules + gates + routing + exit contract

references/
= deep backend knowledge
```

---

# 30. REFERENCE QUALITY AUDIT

Audit all reference files for:

* duplicated content;
* contradictory rules;
* weak negative guidance;
* framework bias;
* vague claims;
* missing failure semantics;
* missing verification;
* broken routing;
* excessive verbosity.

Consolidate only when quality improves.

Do not perform broad rewrites without evidence.

---

# 31. FRAMEWORK-INDEPENDENCE RED TEAM

Challenge the skill using multiple stacks.

At minimum:

* Python/FastAPI;
* Django;
* Node/TypeScript;
* NestJS;
* Java/Spring;
* Go;
* .NET;
* PHP;
* Odoo-like modular backend.

The architecture decision should remain stable when the architectural forces are equivalent.

Framework idioms may differ.

Architectural principles should not.

---

# 32. LANGUAGE-BIAS TEST

Create paired scenarios with identical requirements implemented in different ecosystems.

Compare recommendations.

Example:

```text
same order workflow
Python version
Java version
Go version
```

Unexpected architectural drift should be investigated.

---

# 33. SCALE SENSITIVITY

Test that recommendations change appropriately with evidence.

Example set:

```text
SYSTEM A:
1 team
5k requests/day
single DB

SYSTEM B:
12 teams
500k requests/sec
regional isolation
independent release requirements
```

Microservices should not receive the same decision in both cases.

The skill must respond to forces, not keywords.

---

# 34. AMBIGUITY SENSITIVITY

Create scenarios where one missing fact materially changes the answer.

Example:

```text
"We need to split the service."

UNKNOWN:
whether independent deployment is required.
```

The skill should identify the decision-critical unknown.

Score negatively if it guesses.

---

# 35. FAILURE MATRIX EVAL

For high-risk scenarios require:

```text
Component
Failure
Detection
Containment
Recovery
Data impact
User impact
Evidence
```

Do not require the full matrix for trivial cases.

Use proportionality.

---

# 36. RETRY AMPLIFICATION TEST

Include at least one multi-layer retry scenario:

```text
client retries 3x
API retries 3x
worker retries 5x
dependency degraded
```

The skill should identify multiplicative retry amplification.

It should recommend one bounded retry owner where appropriate.

---

# 37. UNKNOWN OUTCOME TEST

Include timeout-after-remote-commit scenarios.

The skill must distinguish:

```text
FAILURE
vs
UNKNOWN OUTCOME
```

and introduce reconciliation/idempotency/query semantics where appropriate.

This is an important marker of distributed-systems maturity.

---

# 38. CONCURRENCY RED TEAM

Include:

* lost update;
* double booking;
* inventory decrement race;
* duplicate job;
* check-then-act;
* lock expiration;
* CAS conflict;
* two concurrent webhook deliveries.

Prefer datastore atomicity/constraints when simpler than distributed coordination.

---

# 39. DATA-INTEGRITY PRIORITY

The skill must never optimize availability or speed by silently sacrificing an invariant.

Examples:

```text
duplicate billing
negative inventory
cross-tenant access
lost committed event
illegal state transition
```

These are hard failures.

---

# 40. MIGRATION RED TEAM

Test:

* old/new schema coexistence;
* partial migration;
* backfill restart;
* event schema evolution;
* API version skew;
* rollback after irreversible data change;
* dual-write divergence.

The skill should prefer reversible/incremental strategies.

---

# 41. OPERABILITY RED TEAM

Create a stuck workflow scenario.

Ask:

```text
How does the operator:
find it?
diagnose it?
resume it?
repair its data?
prevent recurrence?
```

A design without these answers is not production-complete.

---

# 42. SECURITY BOUNDARY RED TEAM

Include cases where architecture reasoning must detect:

* IDOR/object authorization;
* tenant boundary leakage;
* privileged action;
* insecure webhook trust;
* SSRF;
* secret leakage;
* unbounded expensive query;
* abusive retry endpoint.

Correct response should surface constraints and escalate specialized review when warranted.

---

# 43. CALIBRATION

The skill must distinguish:

```text
SAFE
LIKELY SAFE
UNKNOWN
HIGH RISK
BLOCKED
```

Avoid excessive certainty.

Explicitly reward calibrated uncertainty.

---

# 44. COMPARATIVE SCORE

Produce both:

```text
ABSOLUTE_SKILL_SCORE
```

and:

```text
CONTROL_TO_SKILL_IMPROVEMENT
```

Example:

```text
Control average: 68/100
Skill average: 91/100
Δ: +23

Overengineering rate:
Control: 31%
Skill: 7%

Unsafe retry rate:
Control: 14%
Skill: 1%

Invented-requirement rate:
Control: 19%
Skill: 3%
```

Do not fabricate these numbers.

Only report executed measurements.

---

# 45. TARGET THRESHOLDS

Recommended Triple-A thresholds:

## Activation

```text
positive trigger recall >= 95%
negative trigger precision >= 95%
```

## Selection/rejection

```text
critical decision accuracy >= 95%
hard safety failure rate = 0
```

## Adversarial

```text
cargo-cult resistance >= 95%
user-pressure resistance >= 95%
```

## Unknown handling

```text
decision-critical unknown preservation >= 95%
invented requirement rate <= 2%
```

## Architecture quality

```text
invariant identification >= 95%
failure-semantics coverage >= 90%
verification-contract coverage >= 95%
```

## Context routing

```text
reference routing precision >= 85%
```

These thresholds may be refined if a better methodology is justified.

Do not lower thresholds merely to pass.

---

# 46. REGRESSION GATE

Every bug found during this phase must create regression coverage.

Required loop:

```text
OBSERVE FAILURE
→ MINIMIZE FAILURE CASE
→ IDENTIFY ROOT CAUSE
→ REPAIR SKILL / REFERENCE / ROUTER / EVAL
→ ADD REGRESSION
→ RUN LOCAL GATES
→ RUN FULL SUITE
```

Do not patch prompts without adding evidence.

---

# 47. OVERFITTING DEFENSE

Do not optimize the skill only for the current benchmark.

Use:

* held-out scenarios;
* paraphrased variants;
* hidden permutations;
* framework swaps;
* changed scale;
* changed ownership;
* changed failure assumptions.

Maintain a holdout set that is not used during repair.

---

# 48. HOLDOUT EVALUATION

Split scenarios into:

```text
development
adversarial repair
holdout
```

Do not inspect/modify the skill against holdout expected answers after the benchmark is frozen.

Use the holdout only for final evaluation.

---

# 49. METAMORPHIC TESTING

Create pairs where one fact changes.

Example:

```text
A:
single process, single DB

B:
independently deployed services, separate DB ownership
```

Expected architecture decision should change appropriately.

Other metamorphic dimensions:

* low → high traffic;
* one tenant → multi-tenant;
* synchronous → durable async requirement;
* low criticality → financial side effect;
* single region → regulatory regional isolation.

This tests whether reasoning follows forces.

---

# 50. MINIMALITY TEST

For suitable scenarios compare:

```text
simple correct design
vs
complex correct design
```

The skill should prefer the simpler design unless the complex design provides a requirement-backed benefit.

This is essential for Triple-A.

---

# 51. DECISION STABILITY

Run semantically equivalent prompts with different wording.

Architecture decisions should remain broadly stable.

Unexpected variance may indicate keyword-driven behavior.

---

# 52. EVIDENCE FRESHNESS

Evaluation reports must record:

* model identity where available;
* execution date;
* skill fingerprint;
* scenario corpus fingerprint;
* judge version;
* harness version where available.

Do not mix stale evidence with current package claims.

---

# 53. ASSURANCE ARTIFACTS

Create or update:

```text
docs/
  phase-1.1-baseline.md
  behavioral-eval-report.md
  composition-evidence.md
  context-efficiency-report.md
  adversarial-findings.md
  triple-a-assurance-report.md
```

Only create files that contain real evidence.

---

# 54. MACHINE-READABLE RESULTS

Create machine-readable evaluation outputs.

Example:

```json
{
  "skill_fingerprint": "...",
  "model": "...",
  "scenario_count": 80,
  "passed": 76,
  "failed": 4,
  "hard_failures": 0,
  "control_score": 71.4,
  "skill_score": 93.1,
  "delta": 21.7
}
```

Use the actual repository conventions.

---

# 55. CI / LOCAL VALIDATION

Where repository scope allows, provide one command that executes the complete package validation.

Example concept:

```text
python3 scripts/run-all-gates.py
```

The command should aggregate:

* structural validation;
* links;
* index;
* framework independence;
* composition schema;
* deterministic fixtures;
* known-bad mutations;
* unit tests;
* behavioral eval availability/status;
* report freshness.

Do not hide failures.

---

# 56. STATUS TAXONOMY

Use explicit states:

```text
PASS
FAIL
NOT_RUN
BLOCKED
STALE
NOT_APPLICABLE
```

Never treat `NOT_RUN` as success.

---

# 57. VERDICT TAXONOMY

Use:

```text
NOT_READY
PACKAGE_READY
STATE_OF_THE_ART
AAA_CANDIDATE
TRIPLE_A_CONDITIONAL
TRIPLE_A_PROVEN
```

`TRIPLE_A_PROVEN` requires real behavioral evidence.

---

# 58. TRIPLE_A_PROVEN GATE

Do NOT declare `TRIPLE_A_PROVEN` unless all of the following are satisfied:

1. static package gates pass;
2. deterministic evals pass;
3. known-bad oracles pass;
4. behavioral model execution occurred;
5. treatment materially outperforms control or satisfies a justified absolute bar;
6. critical safety failures equal zero;
7. adversarial pattern rejection meets threshold;
8. unknown handling meets threshold;
9. holdout evaluation meets threshold;
10. context routing is efficient;
11. composition was observed or the verdict explicitly excludes composition proof;
12. evidence fingerprint is current;
13. no unresolved critical architectural defect remains.

---

# 59. CONDITIONAL VERDICT RULE

If model execution or real composition cannot be executed because the host lacks capabilities:

Do not block useful engineering work.

Complete everything else.

Then report:

```text
TRIPLE_A_CONDITIONAL

Blocking evidence:
- host model execution unavailable
- real composition unavailable

Everything required to execute those final gates is implemented.
```

That is acceptable.

Pretending the missing evidence exists is not.

---

# 60. CRITIC GATE

After repairs:

invoke or emulate an independent read-only critic if supported.

The critic must evaluate:

* benchmark validity;
* evaluator sensitivity;
* package integrity;
* overfitting risk;
* false assurance;
* claimed vs actual evidence;
* Triple-A eligibility.

The critic must not modify the package.

---

# 61. MUTATION SENTINEL

Protect the integrity of read-only evaluation.

Before critic:

```text
fingerprint repository
```

After critic:

```text
fingerprint repository
```

If unexpected mutation occurs:

```text
CRITIC_RESULT = INVALID
```

Do not count it as approval.

Ignore generated caches/temp files using a deliberate deterministic policy.

---

# 62. FINAL ARCHITECTURAL GAUNTLET

Before final verdict, run a compact high-risk suite containing at least:

1. premature microservices;
2. justified microservices;
3. premature CQRS;
4. justified CQRS;
5. unsafe retry;
6. safe idempotent retry;
7. direct dual write;
8. transactional outbox;
9. distributed lock temptation;
10. atomic DB constraint alternative;
11. duplicate webhook;
12. multi-tenant auth boundary;
13. interrupted migration;
14. cache stampede;
15. retry storm;
16. unknown-outcome remote call;
17. mixed-version API deployment;
18. event sourcing temptation;
19. justified event sourcing;
20. operator recovery.

No critical scenario may silently fail.

---

# 63. FINAL REPORT

Produce:

# BACKEND-PATTERNS TRIPLE-A ASSURANCE REPORT

Include:

```text
Previous score:
Current score:

Previous verdict:
Current verdict:

Package fingerprint:
Benchmark fingerprint:

Static gates:
Deterministic evals:
Known-bad mutations:
Behavioral model eval:
Control score:
Skill score:
Delta:

Activation:
Selection:
Rejection:
Ambiguity handling:
Invariant reasoning:
Failure reasoning:
Security awareness:
Operability:
Migration:
Verification quality:
Context efficiency:

Cargo-cult resistance:
User-pressure resistance:
Hard safety failures:
Invented requirement rate:

Holdout results:
Metamorphic results:
Decision stability:

Backend-engineering-vNext composition:
Security-engineering-vNext composition:
Verification-loop-vNext composition:
Observed repair loop:

Files changed:
Regressions added:

NOT_RUN:
BLOCKED:
Residual risks:

Triple-A gate results:

Final verdict:
```

---

# 64. REQUIRED FINAL SCORE DIMENSIONS

Score 0–100:

```text
Activation precision
Activation recall
Scope discipline
Progressive disclosure
Context efficiency
Architecture judgment
Pattern selection
Pattern rejection
Invariant reasoning
Distributed-systems reasoning
Transaction reasoning
Concurrency reasoning
Consistency reasoning
API reasoning
Messaging reasoning
Resilience reasoning
Security awareness
Observability
Operability
Migration safety
Anti-pattern resistance
Cargo-cult resistance
User-pressure resistance
Ambiguity handling
Verification quality
Behavioral evidence
Composition quality
Framework independence
Regression robustness
Evidence honesty
```

Provide both individual scores and an overall score.

---

# 65. DO NOT OPTIMIZE FOR SCORE

The score must describe the evidence.

The implementation must not be distorted merely to increase the score.

If the skill genuinely deserves 94, report 94.

If the model-execution environment is blocked, say so.

Assurance credibility is more important than a nominal 100/100.

---

# 66. PRINCIPAL ENGINEER TEST

At the end ask:

Does this skill make the consumer agent repeatedly ask:

```text
What problem actually exists?

What invariant cannot be violated?

Which requirement is observed and which is merely assumed?

What is the smallest design that protects the invariant?

Why is this pattern justified?

Why are the alternatives rejected?

What happens if this runs twice?

What happens if two callers race?

What happens if one side commits and the other fails?

What happens if the dependency becomes slow?

What happens during mixed versions?

How is the system recovered?

How will production expose failure?

What evidence could prove this decision wrong?
```

If not, continue repairing.

---

# 67. FINAL EXECUTION LOOP

Execute autonomously:

```text
DISCOVER CURRENT STATE
→ FREEZE BASELINE
→ BUILD BENCHMARK
→ BUILD RUBRIC
→ BUILD CONTROL/TREATMENT LANE
→ BUILD MUTATION ORACLES
→ RUN STATIC GATES
→ RUN BEHAVIORAL EVALS
→ ANALYZE FAILURES
→ REPAIR SKILL
→ ADD REGRESSIONS
→ RUN HOLDOUT
→ RUN METAMORPHIC TESTS
→ RUN CONTEXT-EFFICIENCY TESTS
→ RUN REAL COMPOSITION
→ RUN REPAIR LOOP
→ RUN FINAL GAUNTLET
→ RUN INDEPENDENT CRITIC
→ VERIFY SENTINEL
→ PRODUCE ASSURANCE REPORT
```

Do not stop after planning.

Do not stop after benchmark creation.

Do not stop after the first passing run.

Do not stop after improving documentation.

The phase is complete only after the evidence closure has been attempted.

---

# 68. REPAIR PRIORITY

When failures appear, prioritize:

```text
1. Unsafe architectural behavior
2. Incorrect pattern selection
3. Failure to reject overengineering
4. Invented requirements
5. Missing invariant/failure reasoning
6. Composition defects
7. Routing/context inefficiency
8. Documentation polish
```

Do not polish prose while correctness defects remain.

---

# 69. EXPECTED OUTCOME

A successful implementation should move `backend-patterns` from:

```text
State-of-the-Art package
+
AAA candidate
```

to:

```text
behaviorally validated architecture skill
+
adversarially resistant judgment
+
causally measured improvement
+
real compositional engineering contract
+
evidence-backed Triple-A status
```

---

# 70. FINAL DIRECTIVE

Do not make `backend-patterns` larger merely to make it look more advanced.

Make it:

* harder to fool;
* harder to push into overengineering;
* better at saying no;
* better at preserving uncertainty;
* better at protecting invariants;
* better at reasoning about failure;
* better at choosing simple architecture;
* better at handing off verifiable claims;
* better at loading only relevant knowledge;
* measurably better than the same agent without the skill.

The final goal is not:

> “This repository contains excellent backend architecture documentation.”

The final goal is:

> “A capable coding agent using this skill reliably demonstrates Principal-level backend architectural judgment, and the repository contains reproducible evidence supporting that claim.”

Begin now.

Inspect the current repository first.

Preserve what is already strong.

Measure before modifying.

Then close the evidence gap.
