# Backend Patterns Phase 1.2 — Generalization

Status: structural corpus coverage `PASS`; minimality is `NOT_DEFINED`; response
execution is `BLOCKED` without a real consumer-model capture.

## Frozen corpus

The benchmark contains 72 scenarios split into 29 development, 25 adversarial
and 18 holdout cases. It contains 13 explicit metamorphic groups, 16 stability
groups and a 20-case final gauntlet. The corpus, router and skill fingerprints
must be frozen before the first holdout result.

## Current structural evidence

`python3 -B scripts/run-generalization-gates.py --output
docs/generalization-results-v1.2.json` confirms the relation schemas, holdout
size and final-gauntlet structure. The artifact records 13 metamorphic groups,
16 stability groups and 20 final-gauntlet cases. This proves corpus structure
only; it does not prove a model changed its architecture decision under altered
forces.

## Required response evidence

When a valid capture exists, the runner must report holdout first result,
metamorphic relation outcomes, paraphrase/framework/scale stability,
simple-versus-complex minimality, ambiguity/unknown preservation and any
framework-swap differences. A failed holdout is preserved before repair; any
repair gets a new regression outside holdout and a second timestamped result.

Current status for holdout, metamorphic, stability, framework swaps, scale
sensitivity and ambiguity response execution: `BLOCKED` because no
consumer-model response file exists. Minimality is `NOT_DEFINED` until a
consumer model supplies simple-versus-complex responses. Structural relation
validation remains `PASS`; response comparison is `NOT_RUN` rather than an
inferred score.
