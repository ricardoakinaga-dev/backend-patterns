# Phase 1.1 ExecPlan — Triple-A closure

## Purpose and scope

Upgrade the existing package from static package readiness to reproducible,
adversarial and causally honest architectural-judgment assurance for the
revised prompt in [`master-prompt-v1.1.md`](master-prompt-v1.1.md). Preserve
the legacy package and its BP-01–BP-14 evidence as historical evidence; do not
reuse it as current proof for this phase.

Prompt SHA-256: `712f18add7908cbb05be6a98a04f4729efafa12e00632d7e697a8421094cb6d1`.
Quality bar: [`phase-1.1-quality-bar.json`](phase-1.1-quality-bar.json).

## Current classification

- Profile: `BROWNFIELD`; an existing maintained skill package is being evolved.
- Mode: `FEATURE`, with an `EXPERIMENT` overlay for consumer-model evaluation.
- Stage/activity: `BUILD` / `IMPLEMENT`, with `VERIFY` checkpoints.
- Tier: `T3_SYSTEM`; the change crosses benchmark, evaluator, reports,
  composition and evidence boundaries.
- Risk: `MEDIUM` locally; behavioral and security claims remain bounded by
  unavailable consumer/runtime evidence.
- Authorization: local repository edits and safe evaluation are authorized by
  the user's implementation request; no production, credential, deployment or
  neighboring-repository mutation is authorized.

## Frozen acceptance

The phase must provide, with current evidence:

1. a baseline before edits;
2. at least 60 materially distinct scenarios (target 72+) across the required
   classes and development/adversarial/holdout splits;
3. machine-readable D1–D23 scoring anchors and hard-fail conditions;
4. response-level mutation/sensitivity oracles;
5. an attempted control/treatment model adapter whose unavailable state is
   `BLOCKED`, never fabricated as a score;
6. measured routing/context efficiency, holdout/metamorphic/stability checks,
   and the 20-case final architectural gauntlet;
7. observed composition or a structured capability block, plus a distinct
   backend-runtime capability block;
8. an aggregate gate command and reports with all 30 score dimensions,
   fingerprints, freshness and explicit verdict taxonomy;
9. fresh independent read-only critique with a mutation sentinel.

## Workstreams and ownership

| Lane | Owned paths | Dependency | Status |
|---|---|---|---|
| A — evidence/control | `scripts/run-all-gates.py`, status/fingerprint contracts | frozen bar | complete |
| B — benchmark | `tests/benchmark/`, `scripts/validate-benchmark.py`, relation corpus | frozen bar | complete |
| C — evaluator | response scorer, response mutations and oracle tests | B schema | complete |
| D — routing | context precision, framework/scale/ambiguity/stability checks | B schema | complete |
| E — composition/runtime | observed trace/adapter and runtime harness evidence | composition contract | BLOCKED without host adapters |
| F — assurance | reports, report validator, final integration and critic | A–E | lead |

`.gauntlet/` remains Lead-only ephemeral state and is excluded from the
consumer package. Delegated workers must not edit shared state, reports or
other lanes.

## Validation strategy

Run the focused lane checks first, then:

```text
python3 -B scripts/run-all-gates.py
```

This command must preserve each check's `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`,
`STALE` or `NOT_APPLICABLE` state and exit non-zero unless every required gate
passes. The model and composition runners may return `BLOCKED` when their host
capabilities are absent; that is a limitation, not a quality pass.

## Recovery and next action

The previous Gauntlet run used the old prompt and remains historical. The new
phase must create a separately identified run after the benchmark contract is
integrated. On interruption, inspect Git status, this plan, the lane files,
and current fingerprints before resuming. Do not restart or overwrite a live
worker, and do not accept stale old-report evidence after any package change.

Current next action: capture a fresh independent critic round against the
repaired artifact, then run the final fingerprinted gates and publish the
commit. External model, composition, and runtime execution remain explicitly
blocked until their host adapters exist.

The behavioral adapter boundary uses opaque case IDs and strips gold decision,
routing, mutation, and baseline fields from the model-facing payload. The
private corpus is joined only after response capture for deterministic scoring.

## Residual limitations

No claim of `TRIPLE_A_PROVEN` is permitted until actual consumer-model
control/treatment execution, holdout evidence and causal comparison exist.
A missing host adapter yields `TRIPLE_A_CONDITIONAL` at most. No backend
runtime, database, broker, production deployment or final security authority
is implied by this repository task.
