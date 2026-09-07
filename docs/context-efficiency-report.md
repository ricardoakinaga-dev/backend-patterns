# Context-efficiency report

Status: PASS for the deterministic routing measurement.

The text-only router was run against all 72 scenarios. It reads the task
title, prompt, current facts, unknowns, invariants, forces, and required
signals. It does not read `family`, `domains`, or `recommended_references`.

    python3 -B scripts/run-context-efficiency.py

| Measure | Result |
|---|---:|
| Scenarios | 72 |
| Target precision | 0.90 |
| Reference precision | 1.0 |
| Reference recall | 0.9972 |
| Average selected context | 82,030 bytes |
| Irrelevant references | 0 |
| Omitted relevant references | 1 |

The labels are curated scenario-to-reference relevance labels and are not
router inputs. This is a precision-first routing result: omissions are
reported explicitly rather than hidden behind a perfect recall claim. It is
not a model-quality result. The complete per-scenario evidence, routing input
declaration, and package fingerprint are in
docs/context-efficiency-results.json.
