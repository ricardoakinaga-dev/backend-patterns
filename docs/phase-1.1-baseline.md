# Phase 1.1 baseline — backend-patterns Triple-A closure

Status: frozen before changes for the revised user prompt.

## Evidence identity

- Observation date: 2026-09-07 (America/Sao_Paulo)
- Target: `/home/ricardo/Área de trabalho/backend-patterns`
- Prompt: `pasted-text-1.txt`
- Prompt SHA-256: `712f18add7908cbb05be6a98a04f4729efafa12e00632d7e697a8421094cb6d1`
- Existing tracked prompt SHA-256: `8fde66033c5d11c33705fa9887cf303fd5ca12062e97cca8871d1d02902e8b5b`
- Current package artifact fingerprint: `30cc14c948c77a473ecb0435f403656ead8dc5d1ae4da8b4a98faf71daff6afd`
- Current commit: `cf24fe6`

## Current measurable state

| Measure | Baseline |
|---|---:|
| `SKILL.md` lines | 273 |
| Topic references, including index | 21 |
| Routed topic references | 20 |
| Deterministic scenarios | 26 |
| Declared known-bad mutations | 26 |
| Unit tests | 10 passed |
| Static validators | 5 passed |
| Model execution | NOT_RUN |
| Runtime/consumer execution | NOT_RUN |
| Causal control/treatment delta | NOT_RUN |
| Real composition | NOT_RUN |

## Executed baseline checks

The following commands ran against commit `cf24fe6` before this phase's edits:

```text
python3 -B scripts/validate-skill.py                         PASS
python3 -B scripts/validate-links.py                         PASS
python3 -B scripts/validate-pattern-index.py                 PASS
python3 -B scripts/validate-composition.py                   PASS
python3 -B scripts/validate-framework-independence.py        PASS
python3 -B tests/run_evals.py                                PASS (26)
python3 -B tests/run_known_bad.py                            PASS (26/26)
python3 -B -m unittest discover -s tests -p 'test_*.py'      PASS (10)
```

These checks prove package structure, fixture integrity, and controlled
rejection of static mutations. They do not prove consumer-model behavior,
causal improvement, real composition, or backend runtime behavior.

## Baseline limitations and required improvement

The existing package is strong at package readiness, but its evidence is
mostly deterministic and static. The revised prompt requires a larger,
structured judgment benchmark; machine-readable rubric and results; response
mutations and sensitivity oracles; development/adversarial/holdout splits;
metamorphic and stability checks; context-routing measurement; an aggregate
validation command; explicit status/verdict taxonomy; and an honest attempt at
model/control-treatment execution. No score or Triple-A claim is made by this
baseline.

Baseline score: 0/100
Baseline verdict: NOT_READY
