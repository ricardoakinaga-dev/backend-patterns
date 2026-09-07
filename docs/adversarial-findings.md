# Adversarial findings

## Current status

The structural and deterministic adversarial gates pass. Consumer-model
execution, runtime backend execution, and real composition remain
BLOCKED/NOT_RUN.

## Coverage

- 72 unique scenarios across SHOULD_USE, SHOULD_REJECT,
  NEED_MORE_EVIDENCE, BROWNFIELD, FAILURE_DRIVEN, SECURITY_SENSITIVE, and
  OPERABILITY.
- Splits: 29 development, 25 adversarial, 18 holdout.
- 13 metamorphic groups and 16 decision-stability groups.
- Every group has an explicit axis, relation, and expected behavior in
  `tests/benchmark/relations.json`; structural relation presence is validated
  before any response-level execution is attempted.
- Generated extension cases use scenario-specific preferred/rejected choices,
  comparison baselines, evidence axes, and mutation diagnostics. The
  validator reports a maximum decision-component frequency of 3 and 72
  distinct mutation diagnostics.
- Twenty final architectural gauntlet cases, including premature/justified
  microservices and CQRS, retry safety, dual-write/outbox, locking versus
  constraints, duplicate webhooks, tenant authorization, interrupted
  migration, cache stampede, retry storm, unknown remote outcome,
  mixed-version APIs, event-sourcing pressure, and operator recovery.
- Framework tags cover Python/FastAPI, Django, Node/TypeScript, NestJS,
  Java/Spring, Go, .NET, PHP, and Odoo-like systems.

## Response-level causal oracle

The 15 mutation cases pass. They cover unsafe retry, direct dual write,
unsupported exactly-once, missing authorization, migration compatibility,
duplicate delivery, ignored invariants, unjustified microservices,
unjustified event sourcing, fabricated requirements, missing recovery,
cache safety, retry amplification, unsupported readiness, and an unknown
remote outcome treated as a known failure.

Each oracle now requires the safe baseline itself to score `PASS` with no hard
failure. The mutated response must then produce the declared hard-fail tag or
a measurable score decrease. Both lanes receive the exact same serialized task
context and its SHA-256 is recorded, so the context is a fixed covariate rather
than baseline-only prompt augmentation. Every mutation declares its operator
and preserved contract; the runner rejects broad replacements below a 0.65
sequence-ratio or token-Jaccard shape threshold. It is a deterministic
evaluator-sensitivity test, not evidence that a language model produced either
response.

## Model-evaluation covariate boundary

The behavioral runner now projects each corpus case into an opaque public
request containing only the task prompt, current facts, unknowns, invariants,
and forces. It removes stance/family, title, split, reference labels,
required signals, hard-fail tags, relation labels, known mutations, and the
simpler-baseline answer before any adapter call. The private answer key is
used only after capture for scoring. `tests/test_behavioral_payload.py`
asserts this boundary and rejects adapter output that bypasses opaque IDs.

This prevents the evaluator from claiming causal model evidence from leaked
labels; it does not turn the absent adapter into behavioral execution.

Machine result: docs/response-mutation-results.json.
