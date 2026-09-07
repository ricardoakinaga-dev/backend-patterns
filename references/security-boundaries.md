# Security boundaries

This reference is for architectural decisions that cross a trust boundary or
could expose data, authority, or scarce resources. It supplies security-aware
design prompts and evidence requirements; it is not a substitute for a
specialist security assessment. Load it with the relevant API, transaction,
messaging, migration, or decision reference rather than treating it as a
universal checklist. The routing contract lives in
[`pattern-index.md`](pattern-index.md).

## Ownership and security posture

The architecture decision must name who is trusted, what is protected, and
which component is accountable for each check. A client, queue message,
service identity, database row, cache entry, or claim is data from the
perspective of the receiving boundary until it has been authenticated and
authorized there. A check performed in a UI, gateway, or earlier service may
improve usability or reduce load, but it does not replace the check at the
authority that owns the object or action.

Use these invariants as starting points and tailor them to the system:

- An unauthenticated or expired identity cannot reach a protected operation.
- An authenticated principal can perform only the actions granted to that
  principal in the current context.
- Object, property, and tenant authorization are enforced server-side at the
  resource owner; changing an identifier, field name, or tenant claim cannot
  widen access.
- A service can use only the secrets, data, network destinations, and
  mutation privileges required for its role.
- Invalid, ambiguous, oversized, or hostile input is rejected before it can
  reach an interpreter, parser, expensive operation, or durable side effect.
- Security-relevant decisions leave enough redacted audit evidence to explain
  what happened without creating a new sensitive-data leak.

If an invariant cannot be stated, the design has an unresolved security
decision. Record it as `UNKNOWN` rather than assuming that another layer will
compensate.

## Map trust boundaries before choosing patterns

Draw the data and authority path, including asynchronous and operational
paths. The following default assumptions make omissions visible; they are not
proof that a particular environment is hostile or safe.

| Boundary or actor | Default assumption | Controls to make explicit | Evidence that matters |
| --- | --- | --- | --- |
| Browser, mobile client, or external caller | Untrusted and replayable | Authn, request validation, object/property/tenant authz, rate and body limits | Requests with altered IDs, claims, fields, and replay keys are denied or safely deduplicated |
| Edge proxy or API gateway | Policy enforcement aid, not resource owner | TLS termination assumptions, identity propagation, size/time limits, route policy | Direct-to-service and mixed-version paths enforce the same ownership checks |
| Internal service call | Authenticated transport does not imply authority | Service identity, audience, scoped permission, caller context, timeout, replay behavior | A low-privilege service cannot invoke an administrative action or read another tenant |
| Queue, event, or webhook | Untrusted delivery channel with duplication and delay | Signature/authentication, schema validation, authorization of effect, idempotency, replay window | Forged, stale, duplicated, reordered, and malformed deliveries are handled safely |
| Database, cache, object store, or search index | Trusted for availability/integrity only within its role | Separate credentials, row/tenant constraints, encryption, query parameterization, cache poisoning defenses | A compromised or mis-scoped credential cannot cross the intended data boundary |
| External URL, file, parser, or third-party API | Untrusted input and potentially hostile response | Egress allowlist, URL and redirect policy, parser limits, content validation, timeouts | Private-address, redirect, oversized, malformed, and slow responses do not escape the boundary |
| Operator, migration, or support tooling | Highly privileged and easy to misuse | Separate identity, approval, audit, dry run, bounded scope, break-glass expiry | Tool actions are attributable, constrained, reversible where possible, and reviewed |

For each arrow in the map, answer: who supplies the identity, who owns the
resource, which component makes the authorization decision, what is the
maximum privilege, and what happens if the dependency is unavailable? A
network segment, private hostname, or internal header is not an authorization
model.

## Authentication is only the first boundary

Authentication (authn) establishes an identity or proves possession of a
credential. Validate the issuer, audience, signature or channel proof,
expiration, not-before time, key version, and intended use. Define clock
skew, revocation or session invalidation, refresh behavior, and what happens
when the identity provider is unavailable. Do not accept an unsigned token,
an arbitrary `sub` field, a caller-provided service name, or a gateway header
without a documented and protected propagation path.

For service-to-service calls, bind credentials to a narrowly scoped service
identity and intended audience. Mutual TLS, signed requests, or a token can
authenticate a caller, but each still needs an authorization policy. For
webhooks, verify the provider signature over the exact received bytes, enforce
a timestamp/replay window when supported, and make the resulting operation
idempotent. Authentication failures should fail closed and should not reveal
whether a protected object exists unless that distinction is intentional.

## Authorization must follow ownership

Authorization (authz) is a decision about an action in a context, not merely a
role string. Evaluate the following layers explicitly:

1. **Action authorization:** may this principal invoke this operation?
2. **Object-level authorization:** may it read or mutate this exact object?
3. **Property-level authorization:** may it set, reveal, or transition this
   exact field? A writable DTO is not a permission model.
4. **Tenant or account isolation:** does the object belong to the principal's
   tenant, account, region, or legal scope?
5. **State and policy authorization:** is the operation valid in the current
   lifecycle state, approval level, time window, or risk context?

Load the object through an authorization-aware query or check ownership before
performing a side effect. Re-check at the mutation boundary when a race or
privilege change could invalidate an earlier decision. Prefer a deny-by-default
policy with explicit grants; make authorization outcomes testable and
auditable without logging secrets or sensitive payloads. A policy abstraction
is useful when it centralizes ownership rules; it is harmful when it hides
which component owns the decision.

Tenant isolation needs a concrete mechanism, not a label. Depending on the
storage model, that may be a tenant-scoped query predicate, database row-level
policy, separate database/schema, cryptographic namespace, or a combination.
Test missing, mismatched, forged, defaulted, and cross-tenant identifiers,
including background jobs that have no HTTP caller.

## Least privilege and durable data boundaries

For every component, define the narrowest useful:

- identity and audience;
- database role and tables/columns it may read or mutate;
- secret names and rotation path;
- network egress destinations and protocols;
- queue topics, consumer groups, and administrative actions;
- file/object prefixes and maximum object sizes;
- operational commands and time-limited elevation path.

Separate read and write credentials where the threat model benefits. Keep
privileged migrations and support actions outside the normal application
identity. A service account with broad database access defeats application
authorization if its credentials are stolen. Review permissions when a
pattern adds a worker, projection builder, cache warmer, replay tool, or
cross-service coordinator; those components often become an accidental
privilege bridge.

## Validate inputs at interpreters and side-effect boundaries

Validation should be schema-aware, bounded, and applied after canonicalization
but before interpretation. Prefer allowlists for commands, enum values, URL
schemes, hosts, fields, sort directions, and file types. Enforce length,
depth, item count, numeric range, nesting, and decompressed-size limits. Keep
validation and authorization separate: valid input is not authorized input.

| Exposure | Design control | Adversarial evidence |
| --- | --- | --- |
| SQL, ORM, search, or NoSQL injection | Parameterized values, safe query builders, constrained sort/filter fields; never splice caller text into syntax | Quotes, operators, nested filters, and unexpected field names remain data or are rejected |
| Shell, template, expression, or code injection | Avoid interpreters; use fixed argument arrays and sandboxing; permit only a narrow grammar | Metacharacters, template delimiters, and encoded variants cannot alter execution |
| HTML, JSON, header, or log injection | Contextual output encoding, typed serialization, header allowlists, structured logging | Control characters and markup do not forge fields, responses, or log events |
| Path traversal and unsafe file handling | Resolve inside an approved directory, reject traversal and device paths, inspect content rather than trusting names | Encoded separators, symlinks, archive entries, oversized and polyglot files stay within limits |
| Unsafe deserialization or parser abuse | Use safe formats, explicit schemas, version limits, depth/size/time budgets, and isolated parsers | Unknown types, recursive structures, malformed encodings, and decompression bombs fail safely |
| Mass assignment or over-posting | Explicit writable property list and per-property authorization | Adding an administrative, ownership, price, or tenant field cannot change protected state |

Normalize once, record the normalized form used for the decision, and avoid
different components interpreting the same bytes differently. Reject
ambiguous encodings rather than relying on a later layer to canonicalize them.

## SSRF and third-party trust

Any feature that fetches a caller-influenced URL, follows a redirect, resolves
a hostname, imports a file, or calls a third-party API needs an explicit egress
policy. A robust design generally:

- permits only required schemes and destinations, preferably by identity rather
  than a freely supplied hostname;
- resolves and checks every connection target, including redirect targets,
  against private, loopback, link-local, metadata, and internal ranges;
- controls DNS rebinding and redirect count, and does not treat a first DNS
  result as permanent proof of safety;
- uses separate network credentials and blocks ambient cloud metadata access;
- bounds response size, decompression, parse time, connection time, and total
  work;
- validates the response type and schema before using it in a privileged
  action; and
- records destination class, outcome, latency, and policy decision without
  logging credentials or sensitive bodies.

Do not make a URL safe merely by checking its string prefix. If a third party
can cause a mutation, authenticate the response where possible, bind it to the
requested operation, and define replay, timeout, and compensation behavior.

## Resource abuse and availability

Availability is a security property when an actor can consume shared capacity.
Budget work at each boundary: request bytes, decompressed bytes, parser depth,
database rows, query time, outbound calls, fan-out, concurrent jobs, queue
age, retries, memory, CPU, and storage. Apply per-principal and global limits
where both are needed. Pagination must have a maximum page size; batch and
export operations need an asynchronous or quota-controlled path when they can
otherwise monopolize workers.

Timeouts are finite budgets, not just client preferences. Bound retries and
backoff, add jitter, and avoid multiplying attempts across layers. Use
backpressure or load shedding when the protected dependency cannot accept more
work. A rate limit without an observable rejection reason, recovery path, and
fairness policy is difficult to operate and easy to bypass with many
identities.

## Secrets, sensitive data, and auditability

Minimize collection first. Classify data by sensitivity, purpose, tenant, and
retention; then decide where it may be stored, cached, replicated, exported,
and logged. Never commit secrets or place raw credentials, bearer tokens,
private keys, passwords, or full sensitive payloads in logs, traces, metrics,
URLs, exception messages, fixtures, or analytics labels. Redaction must be
structural and tested, not a best-effort substring filter.

Use an approved secret store or runtime injection path, rotate credentials,
revoke compromised keys, and ensure old versions do not remain usable longer
than intended. Encryption in transit or at rest does not replace access
control, minimization, or deletion. Tenant identifiers may themselves be
sensitive; use stable pseudonymous identifiers for telemetry when raw values
are unnecessary.

Security audit events should answer who or what acted, on which resource
class, under which policy/version, with what outcome and request/correlation
context. Keep audit records tamper-resistant and access-controlled. Do not
turn auditability into payload retention by default.

## Failure semantics and evidence

Security controls need failure behavior. Authentication and authorization
errors normally fail closed. A policy service outage should not silently become
allow; if a documented break-glass path exists, it must be narrow, time-bound,
audited, and separately authorized. When a control rejects before a mutation,
the mutation must not occur. When a downstream failure happens after a local
commit, use the transaction or outbox contract to prevent an untracked
privileged effect; see [`transaction-patterns.md`](transaction-patterns.md)
and [`messaging-patterns.md`](messaging-patterns.md).

Before calling a security-sensitive design ready, collect evidence at the
boundary that owns the decision:

| Claim | Minimum useful evidence |
| --- | --- |
| A protected operation requires a valid identity | Expired, wrong-audience, invalid-signature, missing-credential, and mixed-version tests |
| A principal cannot cross object/property/tenant boundaries | Altered identifier, field, tenant, role, and concurrent-recheck tests |
| Inputs cannot reach an unsafe interpreter | Injection corpus, parser-limit tests, and code review of the final sink |
| External fetching cannot reach internal resources | Egress policy tests covering redirects, DNS changes, private ranges, oversize, and timeout |
| Privilege is least sufficient | Permission inventory, negative authorization tests, and credential-scope inspection |
| Sensitive data is not exposed | Redaction tests for logs/traces/errors, fixture scan, retention/access review |
| Abuse is contained | Rate/size/concurrency/load tests, retry amplification test, and alert/recovery evidence |

Static review can establish that a control is designed; it cannot prove the
runtime policy, deployment, credential, or network behavior. Mark those claims
as needing runtime or specialist verification.

## Specialist escalation and handoff

Escalate to `security-engineering-vNext` when the design changes
authentication, authorization, tenant isolation, secrets, sensitive data,
external URL fetching, file or object parsing, webhooks, payments, privileged
operations, or service-to-service trust. Escalate even when the local design
looks conventional; the threshold is the boundary, not the perceived
complexity.

The architecture handoff should carry the trust boundaries, identities,
authorization predicates, least-privilege assumptions, abuse cases, evidence
requests, and unresolved risks. Use the package's
[`composition-contracts.md`](composition-contracts.md) shape and do not claim
that a specialist review occurred merely because the handoff was written.
Implementation and factual verification remain separate routes; the overall
composition is described by [`pattern-index.md`](pattern-index.md).

## Security rejection rules

Reject or pause a design when it:

- trusts client-supplied ownership, tenant, role, price, or state fields;
- authenticates a caller but never authorizes the exact object and action;
- relies on a gateway-only check while the service is reachable another way;
- uses a broad service credential because a narrow one is inconvenient;
- accepts arbitrary URLs, redirects, file types, queries, or scripts without a
  bounded policy;
- retries a privileged or non-idempotent effect without duplicate protection;
- logs raw credentials or sensitive payloads in order to aid debugging;
- treats an internal network, broker, or database as a trust boundary that
  needs no validation; or
- claims security readiness without evidence for the changed boundary.

The minimum sufficient security design is the smallest set of controls that
protects the stated assets and invariants at every actual trust boundary. Add
complexity when the threat or evidence requires it; do not add security-shaped
abstractions that cannot be tied to a boundary, a failure mode, or a test.
