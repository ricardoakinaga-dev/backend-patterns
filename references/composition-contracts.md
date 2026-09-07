# Composition contracts

`backend-patterns` owns architectural pattern judgment. It does not replace
implementation engineering, dedicated security analysis, factual verification,
release authority, or product decisions.

## Handoff shape

When a material design is complete enough to hand off, emit this YAML-shaped
record using the consumer's existing format when one exists:

```yaml
architecture_decision:
  problem:
  constraints: []
  forces: []
  invariants: []
  selected_patterns: []
  rejected_patterns:
    - pattern:
      reason:
  boundaries:
    transaction: []
    trust: []
    consistency:
    retry_and_timeout:
  failure_semantics: []
  security_constraints: []
  observability_requirements: []
  migration_and_compatibility: []
  verification_requirements: []
  unresolved_risks: []
  evidence_requests: []
```

Empty values are unresolved and must be labeled `UNKNOWN`, not filled with
assumptions. The record is a decision handoff, not proof that implementation or
verification occurred.

## Ownership boundaries

| Capability | `backend-patterns` contributes | Escalate/hand off |
|---|---|---|
| implementation | boundaries, patterns, constraints, failure semantics | `backend-engineering-vNext` for code/data/migration execution |
| security | trust-boundary prompts, abuse cases, controls to verify | `security-engineering-vNext` for focused security review |
| verification | claims, invariants, failure scenarios, evidence requests | `verification-loop-vNext` for factual current-artifact verification |
| product/authority | impact and decision questions | product owner or authorized human |

The handoff is optional when the neighboring capability is unavailable. Never
claim that it ran merely because its name appears in a record. Do not create a
circular route in which this skill verifies its own final implementation.

## Trigger thresholds

Escalate security review when the design changes authentication, authorization,
tenant isolation, secrets, sensitive data, external URL fetching, file/object
parsing, webhooks, payments, privileged operations, or service-to-service trust.

Escalate factual verification when a completion claim depends on runtime
behavior, persisted state, public API compatibility, concurrency, migration,
failure injection, or current evidence beyond static inspection.

Escalate implementation engineering when the decision has become an executable
code, schema, migration, deployment, or operational change. Keep the selected
pattern and evidence contract attached to that handoff.

## Anti-circularity rule

The route is:

```text
backend-patterns → implementation engineering → security review (if triggered)
                    → factual verification → repair/retest → final assurance
```

The route may be shortened when a boundary is not applicable, but ownership is
never silently duplicated.

