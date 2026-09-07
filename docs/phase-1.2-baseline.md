# Backend Patterns Phase 1.2 — Baseline

Captured before Phase 1.2 source edits on 2026-09-07 (America/Sao_Paulo).
The new prompt was read from the user attachment and is bound by SHA-256
`68faec7e4d2e17b82003fb872fe8bcb3a9f09a2ceed36e269f57c8665990f110`.

## Artifact identity

| Field | Baseline |
|---|---|
| Commit | `69e034c16e250cb5008aec851a364724667b61a4` |
| `SKILL.md` SHA-256 | `89626c960f104b2fa1549f67b1ea814631831d6fe95f2eb8db14242a9e21e53f` |
| Benchmark SHA-256 | `1b01914abffa1dd2d710b0c9e631786e468cd9b03d23bbce49a7ec07e24bf9f2` |
| Rubric SHA-256 | `cd87521db83758394e2b15ba84c196b0581c878082d963f6465670a700ab3b06` |
| Relations SHA-256 | `353fc53580e6ddf726a354dcd191232807c4c976cb6a09b6b935b1de73b573fe` |
| Full pre-edit package SHA-256 | `8819afd5f2dee411309429575223cbcdad61950e4b0118aaf3abbf4457b080bf` |
| Router/package routing SHA-256 | `8894c1dba9a40426ff69fa7e3e69ba5ba439496ffd7487452884b58e0875ad89` |
| `SKILL.md` size | 16,243 bytes |
| Reference count | 21 Markdown files in `references/` (20 routed pattern references plus composition contracts) |

The full pre-edit package fingerprint is computed over the tracked `SKILL.md`,
`README.md`, `composition-contract.json`, `references/`, `scripts/` and
`tests/` tree at the baseline commit with length-delimited path/content hashing;
the routing fingerprint is retained separately for the narrower pre-edit
measurement scope.

## Corpus and deterministic checks

- 72 benchmark scenarios: 29 development, 25 adversarial, 18 holdout.
- Families: 16 `SHOULD_USE`, 16 `SHOULD_REJECT`, and 8 each for
  `NEED_MORE_EVIDENCE`, `BROWNFIELD`, `FAILURE_DRIVEN`,
  `SECURITY_SENSITIVE`, and `OPERABILITY`.
- 26 legacy fixture scenarios and 26/26 known-bad declarations executed.
- 15 response-level mutation oracles passed.
- 13 Python unit tests passed.
- Static, links, pattern-index, composition-contract, framework-independence,
  benchmark, legacy fixture and unit checks passed.

## Routing baseline

The current text-only router measured:

| Metric | Value |
|---|---:|
| Binary reference precision | 0.9174 |
| Binary reference recall | 0.5201 |
| Average selected context | 50,764.62 bytes |
| Median selected context | 49,476 bytes |
| P95 selected context | 80,691 bytes |
| Average references selected | 2.1528 |
| Irrelevant loads | 15 |
| Omitted relevant references | 148 |
| Scenarios with at least one omission | 63 |

The omission audit must inspect all 148 pairs before treating recall as a
router defect. The binary labels may contain depth-only references that belong
in `SECONDARY` or `OPTIONAL` rather than `PRIMARY`.

## Execution states

| Surface | Baseline status | Evidence boundary |
|---|---|---|
| Consumer model control/treatment | `BLOCKED` | No host adapter supplied; no scores or causal delta exist. |
| Generalization response execution | `BLOCKED` | Structural relations exist; no model response capture exists. |
| Real composition | `BLOCKED` | No neighboring-skill adapter or observed trace exists. |
| Backend runtime | `BLOCKED` | No executable service/runtime harness exists. |
| Legacy `docs/assurance-report.md` validator | `FAIL` | Report package fingerprint is stale at baseline. |
| Phase 1.1 validator | `PASS` | Historical phase artifact remains internally valid. |

## Existing verdict and residual risk

The previous report's evidence-bounded verdict was `TRIPLE_A_CONDITIONAL`.
This baseline does not upgrade it. A model, runtime or composition claim would
be invalid until the corresponding host evidence is captured. The main Phase
1.2 risk is improving recall by loading everything or by relabeling expected
references without an omission-level audit.

## Baseline commands

The baseline commands were run with `python3 -B`, including the package
validators, benchmark validator, response mutations, generalization gates,
behavioral/composition/runtime runners and the aggregate runner. Raw baseline
JSON was written outside the repository under `/tmp/backend-patterns-phase12-*`
to avoid changing the pre-edit worktree. The aggregate was `BLOCKED` with
12 `PASS`, 0 `FAIL`, 0 `NOT_RUN`, and 4 `BLOCKED` phase checks; the separate
legacy assurance validator failed for the stale report fingerprint above.
