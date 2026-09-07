# `backend-patterns`

`backend-patterns` is a framework-independent Agent Skill for choosing backend
architecture patterns with explicit trade-offs, rejection criteria, failure
semantics, security boundaries, operational concerns, and verification evidence.
It is intentionally an orchestrator: the compact [`SKILL.md`](SKILL.md) routes
to focused references instead of forcing every task through a catalog.

## Package map

- [`SKILL.md`](SKILL.md): activation, workflow, decision gates, handoff and exit.
- [`references/pattern-index.md`](references/pattern-index.md): progressive-
  disclosure routing and coverage map.
- [`references/decision-matrix.md`](references/decision-matrix.md): reusable
  comparison schema and complexity gates.
- [`references/testing-patterns.md`](references/testing-patterns.md):
  invariant-first and adversarial evidence selection.
- [`references/composition-contracts.md`](references/composition-contracts.md):
  bounded handoffs to implementation, security and verification specialists.
- [`composition-contract.json`](composition-contract.json): machine-readable
  ownership and handoff contract.
- [`scripts/`](scripts/): offline structural, link and index validators.
- [`scripts/validate-assurance-report.py`](scripts/validate-assurance-report.py):
  workspace-only completeness check for the evidence report.
- [`tests/`](tests/): fixture corpus, executable known-bad mutations, and
  deterministic checks for the skill's routing and reasoning contract.

## Use

Read `SKILL.md`, classify the backend decision, then load the smallest relevant
reference(s) from the index. Produce a decision record for material choices and
ask what evidence would disprove the design. The package does not require a
framework, database, broker, model runtime, or neighboring skill to be usable.

## Validate

```bash
python3 scripts/validate-skill.py
python3 scripts/validate-links.py
python3 scripts/validate-pattern-index.py
python3 scripts/validate-composition.py
python3 scripts/validate-framework-independence.py
python3 tests/run_known_bad.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/run_evals.py
python3 scripts/validate-assurance-report.py  # workspace evidence, not consumer runtime
```

These commands prove package structure, navigation, index coverage, and fixture
integrity, and controlled rejection of every declared known-bad mutation. They
do not execute an LLM or certify a consuming production system. The assurance
report validator is intentionally a workspace-level evidence check and is not a
runtime or security certification.
