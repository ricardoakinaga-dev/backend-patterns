# ExecPlan — `backend-patterns` State-of-the-Art / Triple-A

## Purpose and outcome

Build the self-contained `backend-patterns` Agent Skill requested in
[`master-prompt.md`](master-prompt.md). The package must behave as a principal
backend architecture decision aid: inspect the actual system, identify forces
and invariants, generate and reject candidates, select the minimum sufficient
design, define implementation constraints, and map claims to current evidence.

The outcome is a package at the workspace root with `SKILL.md`, routed
references, deterministic validation scripts, tests/fixtures, README, and a
`docs/` evidence trail. The package must not depend on the construction harness
or neighboring skills at consumption time.

## Scope and exclusions

In scope: the full user prompt; framework-independent backend architecture
judgment; API/data/transaction/consistency/concurrency/messaging/resilience/
caching/distributed-systems/security/observability/performance/migration/
testing guidance; anti-pattern and rationalization defense; composition
contracts; skill-level fixtures and validation; adversarial hardening; final
assurance evidence.

Out of scope: implementing a backend runtime, deploying services, changing
neighboring skills, publishing/installing globally, live security certification,
production mutation, or claiming host-model superiority without an executed
consumer evaluation.

## Current state and classification

- Project profile: `GREENFIELD` (the target directory had no implementation).
- Primary work mode: `FEATURE`; overlays: `REFACTOR` is not applicable because
  there is no target implementation, while `EXPERIMENT` is reserved for model
  evaluation and is not a product dependency.
- Lifecycle: `BUILD` after repository inspection and bar freeze.
- Activity: `IMPLEMENT` with `PLAN`/`VERIFY` checkpoints.
- Engineering tier: `T3_SYSTEM` because this is a multi-file capability package
  with architectural contracts, evaluation fixtures, and long-lived reuse.
- Risk: `MEDIUM`; blast radius: `SYSTEM` for consumers of the skill, local and
  reversible in this workspace. No production authority is requested.
- Git: absent in the target; Gauntlet uses filesystem fingerprints.
- Primary limitation: no target runtime exists for executing model behavior;
  deterministic corpus/structure checks plus fresh read-only criticism will be
  used, with the limitation reported rather than converted into PASS.

## Frozen quality bar

The authoritative bar is [`quality-bar.json`](quality-bar.json), version `v1`.
It must not be weakened to match implementation. Required criteria are BP-01
through BP-14. Evidence that predates a material mutation is stale and must be
rerun.

## Architecture and ownership

| Area | Owner | Contract |
|---|---|---|
| `SKILL.md`, `README.md`, `docs/` | Lead | compact orchestration, public scope, plans and evidence |
| `references/` | Reference builders | one topic per file, linked from `pattern-index.md`, no orphan files |
| `scripts/` | Validation builder | stdlib-only deterministic checks, non-zero on required failure |
| `tests/` | Evaluation builder | fixtures, schema checks, known-bad mutations, no model claims |
| shared index/schema | Lead | frozen names/IDs before parallel writing |
| `.gauntlet/` | Lead only | ephemeral multi-round state; never a consumer dependency |

No worker may edit another lane's owned files, alter the bar, change the
Gauntlet state, or spawn descendants. The Lead integrates and verifies every
returned artifact.

## Milestones and exit criteria

### M1 — Repository audit, research, and bar (complete)

Evidence: target inspection, baseline audit, copied prompt hash, three-source
research report, and frozen quality bar. Exit: the scope and evidence methods
are rejectable and no material unknown blocks local implementation.

### M2 — Package contract and orchestrator

Create `SKILL.md`, `README.md`, `references/pattern-index.md`, composition
contract, and the first version of the decision-record/failure-matrix schemas.
Exit: metadata, activation boundaries, core workflow, minimum-sufficient rule,
handoff boundaries, and progressive-disclosure routes are explicit.

### M3 — Reference knowledge lanes

Implement the disjoint reference families listed in the index. Each file must
state problem/context/forces/use/not-use/costs/failure/security/operations/
testing/migration/observability/alternatives/evidence where its domain applies.
Exit: index coverage, links, framework independence, and no placeholder content.

### M4 — Deterministic validation and skill fixtures

Implement `scripts/validate-skill.py`, `validate-links.py`,
`validate-pattern-index.py`, and tests/fixtures for activation, selection,
negative routing, adversarial cases, composition, and regression. Exit:
known-good package passes and each validator rejects a controlled known-bad
mutation in an isolated copy.

### M5 — Integration, red-team, and repair

Run the real validators, copied-package checks, static bias scans, and fresh
critics against the frozen bar. Repair the largest material gap only with a
discriminating hypothesis; rerun focused and regression checks after every
material change. Exit: integrated artifact has current evidence and no required
criterion remains missing.

### M6 — Final assurance

Run a fresh Final Critic with a sealed packet and mutation sentinel, inspect the
final report, and record limitations. Exit: use `PASS`/`READY`/`STATE-OF-THE-ART`
only where evidence supports it; never claim `TRIPLE-A` from static coverage
alone.

## Execution order and recovery

1. Keep the original prompt and bar immutable.
2. Initialize the Gauntlet state after M1; the Lead is its only writer.
3. Freeze the shared pattern index and composition contract.
4. Parallelize only disjoint reference and fixture lanes.
5. Integrate by inspecting every changed file and running link/index checks.
6. Capture a filesystem fingerprint before each read-only critic and verify it
   afterward; a mutation invalidates that critic's judgment.
7. If a check fails, preserve the output, classify the failure, change one
   justified hypothesis, and rerun the focused check before regressions.
8. On interruption, inspect current files and `.gauntlet/state.json` before
   resuming; do not restart a live agent or rewrite history.

## Traceability and handoffs

`BP-*` criteria are the quality-bar IDs. References map to user prompt sections
in `pattern-index.md`; fixtures map to criteria and exact oracle text. The
package emits typed decision records with selected/rejected patterns, forces,
invariants, boundaries, failure semantics, security, observability, migration,
and verification requirements. Security and verification handoffs are
optional capabilities, not hidden dependencies.

## Progress log

- 2026-09-07: inspected empty target and neighboring local capability sources.
- 2026-09-07: read the complete user prompt and saved it byte-for-byte.
- 2026-09-07: completed three-source community research at pinned commits.
- 2026-09-07: froze `docs/quality-bar.json` v1 and began implementation.
- 2026-09-07: integrated the orchestrator, 20 routed references, composition
  contract, validators, fixtures, and deterministic contract tests.
- 2026-09-07: Gauntlet round 1 rejected the missing assurance report and
  incomplete known-bad execution; the Critic was invalidated after cache drift.
- 2026-09-07: repaired the gaps, executed 26/26 known-bad mutations, and
  obtained clean Critic approval for package/artifact readiness at round 2.

## Recovery checkpoint

This is a frozen traceability checkpoint, not a live TODO list. The package and
evidence are at `FINAL_GAUNTLET` readiness after exact known-bad target/diagnostic
binding, the false-target regression, the non-tautological diagnostic oracle,
the current assurance report, and the corrected plan text. The live phase,
evidence freshness, final Critic result, and finish verdict are authoritative
only in `.gauntlet/state.json` and its history; this document deliberately does
not duplicate a mutable next-action claim. The latest static checkpoint is:
all deterministic gates pass, 26/26 known-bad mutations pass with 26
declarations verified, 10 contract tests pass, and the isolated consumer copy
passes without docs, the construction harness, neighboring skills, or site
packages. No external effects or irreversible actions are pending.
