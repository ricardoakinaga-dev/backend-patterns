# Backend Patterns Phase 1.2 — Behavioral Evaluation

Status: `BLOCKED` for consumer-model execution; this report is updated from
the current Phase 1.2 evaluator artifact. It never treats fixtures or
deterministic response oracles as consumer-model behavior.

## Protocol

The evaluator projects only `prompt`, `current_facts`, `unknowns`, `invariants`
and `forces` to opaque `case-NNN` identifiers. Expected decisions, family,
split, rubric signals, recommended references, mutation diagnostics, simpler
baselines and all scoring metadata remain private until after raw response
capture. Control and treatment must use the same model, task/tool context and
execution settings; treatment alone may load `backend-patterns` through the
host's normal skill-consumption path.

## Current observation

- Result: `BLOCKED`.
- Command: `python3 -B scripts/run-behavioral-eval.py --output docs/behavioral-eval-results-v1.2.json`.
- Reason: no consumer-model adapter was supplied by the host.
- Required capability: an adapter that invokes the same model in control and
  treatment lanes and returns JSON response records.
- Missing evidence: raw control/treatment responses, absolute scores, blind
  pairwise judgment, causal delta, model identity and adapter identity/version.
- Verdict impact: behavioral quality is `UNKNOWN/BLOCKED`; `TRIPLE_A_PROVEN`
  remains ineligible.
- Current artifact fingerprints: corpus `1b01914abffa1dd2d710b0c9e631786e468cd9b03d23bbce49a7ec07e24bf9f2`;
  package `67954c6ec40e7682226e55f79cd5a5f989458f643ddaa0d2ade5cabfa0259332`.

The evaluator protocol itself is deterministic evidence: opaque-ID mapping,
gold-field rejection, duplicate/missing-lane validation, raw-capture-before-
scoring ordering and fingerprint checks pass in `tests.test_phase12_evaluator`.
Those checks validate the harness boundary, not model behavior.

## Validity rules

An adapter result is valid only when it records real model execution, opaque
case IDs, both lanes, raw capture before scoring, model/package/corpus
fingerprints, and materially equivalent non-skill context. Unknown IDs,
private/gold fields, missing lanes, duplicate lanes, fixture substitution or
post-hoc expected-answer fields are invalid evidence.

## Required staged runs

Smoke (10–12 cases), development (29), adversarial (25), and holdout (18) are
separate runs. Holdout is frozen before first execution and cannot be used to
tune the skill before its first result. When a host adapter is supplied, raw
captures and scorer results are stored as separate artifacts and joined only
after capture.

## Current next action

Supply a host adapter satisfying the protocol, then run smoke first. Until
that external capability exists, keep the result `BLOCKED` and continue only
deterministic evaluator, routing, generalization-structure and evidence work.
