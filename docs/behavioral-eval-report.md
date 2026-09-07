# Behavioral evaluation report

Status: BLOCKED.

model_execution: BLOCKED

The runner was executed with:

    python3 -B scripts/run-behavioral-eval.py

It found no consumer-model adapter. The required host capability is an
adapter that invokes the same model in control and treatment lanes and returns
JSON response records for the 72-scenario corpus. The unavailable evidence is
the control/treatment response set, D1–D23 scores, pairwise judgments,
holdout behavior, and a causal treatment delta. No behavioral score is
reported and TRIPLE_A_PROVEN is ineligible.

The implemented protocol sends the same sanitized task projection to control
and treatment, records model/status/timestamp fields, and routes captured
responses through scripts/score-responses.py. Each request uses an opaque
`case-NNN` identifier and contains only the prompt, current facts, unknowns,
invariants, and forces. The answer key, stance/family, title, reference
labels, required signals, mutation metadata, and simpler-baseline text are
held in the private scoring corpus and are never sent in the model payload;
adapter responses are remapped from opaque IDs only after capture. The scorer
explicitly marks execution as NOT_INFERRED; a fixture or model label cannot
stand in for a model run.

Machine result: docs/behavioral-eval-results.json.
