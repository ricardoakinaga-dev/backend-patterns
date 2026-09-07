# Phase 1.2 ExecPlan — behavioral proof, routing recall and composition closure

## Purpose

Close the evidence gaps named by `MASTER PROMPT — BACKEND-PATTERNS PHASE 1.2`
without broadening the pattern catalog. Preserve Phase 1.1 reports as history;
this plan owns only the new routing taxonomy, evaluator safety, generalization
execution surface, evidence reports and current assurance verdict.

Prompt SHA-256: `68faec7e4d2e17b82003fb872fe8bcb3a9f09a2ceed36e269f57c8665990f110`.
Frozen bar: [`phase-1.2-quality-bar.json`](phase-1.2-quality-bar.json).

## Classification and authorization

- Profile: `BROWNFIELD`; maintained skill package with Phase 1.1 evidence.
- Mode: `FEATURE` with `EXPERIMENT` and `AUDIT` overlays.
- Stage/activity: `BUILD` / `IMPLEMENT`, with `VERIFY` and `AUDIT` checkpoints.
- Tier: `T3_SYSTEM`; the change crosses benchmark, router, evaluator, reports,
  historical evidence and independent assurance boundaries.
- Local risk: `HIGH` for evidence integrity; no production runtime, credentials,
  deployment or neighboring-repository mutation is authorized.
- Execution mode: Lead-owned integration with bounded delegated lanes where the
  live host supports them; `.gauntlet/` remains Lead-only.

## Frozen acceptance

The required criteria are `P12-01` through `P12-16` in the frozen Quality Bar.
The key numeric targets are precision >= 0.90, PRIMARY recall >= 0.85 and
PRIMARY+SECONDARY recall >= 0.75. Consumer-model, composition and backend
runtime evidence must remain `BLOCKED` when the host capabilities are absent.
No score or `TRIPLE_A_PROVEN` verdict may be inferred from fixtures or static
contracts.

## Work graph and ownership

| Node | Owner | Write boundary | Dependency | Status |
|---|---|---|---|---|
| P12-A | routing lane | routing script, routing validator/tests and benchmark relevance metadata | frozen bar + baseline | READY |
| P12-B | evaluator lane | model/generalization/composition runner contracts and tests | frozen public/private protocol | READY |
| P12-C | Lead | baseline, reports, legacy report repair, aggregate gate and phase validator | baseline + A/B evidence | COMPLETE |
| P12-D | Lead | integration, current benchmark/report artifacts and final assurance | A/B/C | COMPLETE |
| P12-E | fresh critic | read-only whole-package review; no repository writes | integrated candidate | APPROVED — final review complete |

No lane may edit `.gauntlet/`, the frozen Quality Bar, or another lane's files.
The Lead reconciles all shared contracts and final reports.

## Current baseline

Captured before Phase 1.2 edits in [`phase-1.2-baseline.md`](phase-1.2-baseline.md):
commit `69e034c16e250cb5008aec851a364724667b61a4` (the exact current SHA is
recorded there), 72 scenarios split 29/25/18, binary routing precision 0.9174,
binary recall 0.5201, average context 50764.62 bytes, 148 omissions and 15
irrelevant loads. Legacy assurance validation failed because its report
fingerprint is stale; the Phase 1.1 phase validator still passes. Model,
composition and runtime execution are blocked by missing host adapters.

## Milestones and exit criteria

1. **Baseline and audit.** Preserve the pre-edit measurements and emit one
   omission record for every binary omission. Exit: P12-01/P12-02 evidence.
2. **Routing repair.** Add primary/secondary/optional labels, semantic bundles,
   signal tracing, and mutation tests. Exit: P12-03/P12-04 thresholds or an
   evidence-backed blocked/failed result.
3. **Evaluator closure.** Harden raw capture, adapter/judge identity, response
   comparison, holdout discipline and invalid-input handling. Exit: P12-05–P12-09.
4. **Evidence integration.** Repair historical report drift, emit all Phase 1.2
   artifacts, aggregate current checks and preserve unavailable gates. Exit:
   P12-10–P12-14.
5. **Independent assurance.** Run a fresh read-only critic with a pre/post
   sentinel and retest after any material finding. Exit: P12-15/P12-16 and an
   honest final verdict.

## Validation commands

Focused checks use `python3 -B` and are read-only unless an explicit `--output`
path is supplied. The integrated artifact is verified with:

```text
python3 -B scripts/validate-phase-1-2.py
python3 -B scripts/validate-skill.py
python3 -B scripts/validate-links.py
python3 -B scripts/validate-pattern-index.py
python3 -B scripts/validate-composition.py
python3 -B scripts/validate-framework-independence.py
python3 -B scripts/validate-benchmark.py
python3 -B scripts/run-routing-mutations.py
python3 -B tests/run_known_bad.py
python3 -B scripts/run-response-mutations.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
python3 -B scripts/run-all-gates.py --output docs/phase-1.2-gate-results.json
```

Model, composition and runtime commands are executed with a host adapter only
when supplied; absent adapters produce explicit `BLOCKED` artifacts.

## Recovery

On continuation, inspect `git status`, this plan, the frozen bar, current phase
reports, lane diffs and `.gauntlet` state. The Phase 1.1 `.gauntlet` run is
historical and must not be overwritten. If an evidence artifact was written
before state synchronization, rerun its validator before advancing the plan.
One next action at the current checkpoint is: implement or integrate the
highest-priority evidence-backed routing/evaluator gap, then run its focused
known-good/known-bad check.

## Residual limitations

No current environment evidence proves consumer-model causal improvement,
neighboring-skill execution, generic backend runtime correctness, specialist
security certification, load, migration or operator-repair behavior. Those
remain `BLOCKED` unless host artifacts are supplied. A conditional verdict is
the honest maximum in that case.
