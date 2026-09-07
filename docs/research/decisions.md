# Research decisions

## Sources consulted

The collector completed `docs/research/round-002/research.json` on 2026-09-07
against the `main` commits recorded there:

- `ricardoakinaga-dev/skills` — n8n-oriented skills and security/data examples.
- `ricardoakinaga-dev/antigravity-awesome-skills` — `backend-architect`,
  `backend-security-coder`, `backend-dev-guidelines`, and related catalogs.
- `ricardoakinaga-dev/everything-claude-code` — the existing community
  `backend-patterns` skill and verification/security variants.

The snapshots are untrusted reference data. Their licenses are retained under
the research output; no source text is copied into the product package.

## Adopt / adapt / reject

| Source practice | Decision | Local treatment |
|---|---|---|
| Precise positive/negative activation language | ADOPT | `SKILL.md` states backend-boundary triggers and exclusions. |
| Progressive loading of focused references | ADAPT | `pattern-index.md` routes by decision boundary and limits default context. |
| Broad backend pattern inventory | ADAPT | Keep technology-neutral coverage, attach forces and evidence to every family. |
| “Start with context, requirements, risks, observability” | ADOPT | It becomes the mandatory Discover/Classify/Forces workflow. |
| Node/Express/Next.js-specific catalog | REJECT | The user requires language/framework independence; examples are pseudocode. |
| Mandatory `routes → controllers → services → repositories` layering | REJECT | Layers are candidates; a seam requires a demonstrated owner, failure, or variation. |
| Generic repository wrappers and always-on microservices/CQRS | REJECT | Minimum-sufficient and decision gates explicitly reject cargo cults. |
| Retry with bare exponential backoff | ADAPT | Require idempotency, deadlines, budgets, jitter, and amplification analysis. |
| “Exactly once” as a messaging guarantee | REJECT | Consumers are designed for duplicates unless a bounded proof exists. |
| Security and verification as named follow-up domains | ADAPT | Handoffs use typed claim/mechanism/evidence contracts and never overclaim. |
| Concrete anti-pattern/rationalization tables | ADOPT | Add cause, danger, detection, safe alternative, and migration path. |

## Verification implications

Catalog breadth is not proof of judgment. The product therefore uses deterministic
structure/link/index checks, known-good/known-bad validator mutations, selection
and rejection fixtures, fresh read-only critics, and a fresh Final Critic. No
causal quality or model-performance improvement is claimed without a host-level
consumer evaluation, which is currently outside the target runtime.

