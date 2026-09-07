# Backend Patterns Phase 1.2 — Adversarial Findings

This is the Phase 1.2 finding register. Baseline observations are preserved;
resolved deterministic findings are closed only with current rerun evidence.

## F12-01 — routing recall gap

- Evidence: 72-scenario text router measured precision `0.9174`, binary recall
  `0.5201`, 148 omitted binary references, 15 irrelevant loads.
- Risk: the router can omit depth needed for transaction, observability,
  compatibility, API, resilience and data decisions while appearing precise.
- Status: `CLOSED` for the implementable deterministic surface. The current
  route reaches 1.0000 precision, 1.0000 PRIMARY recall and 1.0000
  PRIMARY+SECONDARY recall on the evaluator taxonomy; all 148 baseline pairs
  remain enumerated in `docs/routing-error-analysis.md`. One OPTIONAL depth
  omission is retained by policy.

## F12-02 — stale historical assurance report

- Evidence: `python3 -B scripts/validate-assurance-report.py` failed because
  `docs/assurance-report.md` has a stale package fingerprint.
- Risk: a historical report could be mistaken for current evidence.
- Status: `CLOSED`; the report fingerprint was repaired after source
  integration and `validate-assurance-report.py` passes.

## F12-03 — consumer-model evidence unavailable

- Evidence: `scripts/run-behavioral-eval.py` returns `BLOCKED` with no adapter.
- Missing: actual control/treatment responses, scores and causal delta.
- Status: `BLOCKED`, not a model-quality PASS.

## F12-04 — real composition unavailable

- Evidence: `scripts/run-composition-eval.py` returns `BLOCKED` with no trace or
  adapter.
- Status: `BLOCKED`, not contract-execution evidence.

## F12-05 — backend runtime unavailable

- Evidence: `scripts/run-runtime-gates.py` returns `BLOCKED` without a service,
  persistence/dependency harness, load/concurrency, migration/security or
  operator-repair evidence.
- Status: `BLOCKED`; runtime correctness remains separate from model behavior.

## Deterministic safety baseline

The benchmark validator, 26/26 known-bad fixture oracles, 15 response-level
mutation oracles and 13 unit tests pass at baseline. Those results validate
harness/package behavior only; they do not close F12-03–F12-05.

## Phase 1.2 deterministic additions

- Routing causal mutations: `PASS` (8/8), including gold-field invariance and
  load-all rejection.
- Behavioral protocol tests: `PASS` for malformed/opaque/duplicate-lane and
  raw-capture validation; actual model execution remains `BLOCKED`.
- Generalization structure: `PASS`; response execution remains `BLOCKED`.
- Real composition: `BLOCKED` because no executable neighboring-skill adapter
  or observed trace exists.
- Backend runtime: `BLOCKED` because no service/runtime harness exists.
