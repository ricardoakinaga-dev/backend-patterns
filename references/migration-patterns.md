# Migration patterns

Migration is controlled evolution of data, contracts, ownership, or deployment
behavior while old and new versions may coexist. The goal is to preserve
invariants and recover from partial progress, not merely to make a migration
command exit successfully. Treat schema, API, event, cache, and operational
changes as one compatibility problem when they share readers or writers.

## Problem and forces

Every migration trades rollout speed, lock/downtime budget, implementation
complexity, storage cost, reversibility, and compatibility. Establish:

- source and target representations and their authoritative owners;
- all readers, writers, jobs, reports, caches, event consumers, and external clients;
- data volume, growth, skew, invalid/duplicate values, sensitive fields, and constraints;
- old/new deployment order and how mixed versions behave;
- allowed downtime, lock and resource budget, recovery objective, and loss window;
- backfill correctness, concurrency, and handling of new writes; and
- the authority, monitoring, stop signal, rollback or roll-forward path.

Unknown consumers, backup/restore state, production volume, or destructive
behavior are blockers for a material cutover. Inspect the existing system before
choosing a rewrite; preserve an old mechanism until its reason and dependents are
understood.

## Migration and compatibility implications

### Expand, migrate, contract

The default safe sequence is:

1. **Expand:** add an optional/nullable field, table, index, event field, or
   endpoint without removing the old form. Make the change compatible with old
   readers and writers.
2. **Deploy compatible behavior:** release code that can read old and new state,
   and writes both only when the divergence and repair plan are explicit.
3. **Backfill:** process existing records in bounded, checkpointed, idempotent
   batches; protect concurrent writes and quarantine invalid rows.
4. **Verify and switch:** compare counts/checksums/invariants, optionally dual-read
   or shadow-compare, then make the new representation authoritative behind an
   observable rollout control.
5. **Observe and reconcile:** watch errors, lag, lock/load impact, stale caches,
   downstream contracts, and divergence until the compatibility window closes.
6. **Contract:** remove old reads/writes, columns, events, indexes, bridges, or
   flags only after consumer evidence and an approved recovery path exist.

The steps can be combined only when the same compatibility and recovery evidence
still exists. A destructive one-step migration is not simpler if its failure
requires restoring an untested backup or losing writes.

## Mixed versions and contract evolution

Analyze each transition, not only the final state:

| Dimension | Required question |
|---|---|
| Forward compatibility | Can old readers tolerate new schema/data? |
| Backward compatibility | Can new readers work before all data is converted? |
| Mixed version | What happens when old and new instances read/write together? |
| Contract | Are API, event, export, report, and cache consumers preserved or versioned? |
| Failure compatibility | Can retry, restart, and partial progress continue safely? |

Prefer additive fields, safe defaults, tolerant readers where absence is valid,
explicit semantic versions when meaning changes, and deprecation based on
observed consumer use. A renamed field, changed enum meaning, tightened null
rule, reordered event, or new required state can be breaking even when the
serialized format still parses. Mixed-version tests must cover deployment order,
not just final code.

## Backfills, dual reads, and dual writes

A backfill needs a stable selection order, bounded batch/transaction size,
checkpoint, idempotent write, retry and stop rule, progress/lag metric, and
reconciliation. Define what happens when a source row changes during the
backfill: version check, change capture, re-read, or explicit conflict queue.
Do not mark a batch complete from a log line; verify the committed state.

Dual reads can reveal divergence, but they can double latency and load; sample,
bound, and record comparison without changing the user result until trusted.
Dual writes are dangerous because one write can succeed and the other fail. Use
an outbox, local transaction, durable change capture, or explicit divergence and
repair plan. Never let two stores silently become authoritative.

For event or projection migrations, preserve event identity and replay semantics.
Use an isolated consumer/rebuild path for historical data; prevent replay from
re-sending irreversible notifications, payments, or external commands unless the
effect is explicitly idempotent and intended.

## Recovery, rollback, and roll-forward

Rollback is not automatically safe. Once new columns contain data, new clients
write new semantics, or a destructive transform has run, reverting code may
discard or misread valid state. Choose and exercise one of:

- reversible application/schema rollback with all writes preserved;
- roll-forward repair from a checkpoint or quarantine;
- restore plus replay/reconciliation from a known durable point; or
- coexistence until a corrected migration completes.

Every step needs preconditions, exact scope, transaction/batch boundary, retry
limit, validation query/checksum/invariant, monitoring and abort signal, owner,
and a recovery instruction. On interruption, inspect actual schema/data and job
state before resuming. Never assume the last batch committed or that a backup can
be restored because a backup file exists.

## When to use and when not to use

Use expand/contract, staged ownership transfer, feature flags, shadow traffic,
branch-by-abstraction, or a strangler path when old and new behavior must
coexist. Use a direct migration only when the system is disposable or a bounded
maintenance window and verified recovery make the simpler path safer.

Do not rewrite everything to avoid understanding current contracts. Do not drop a
column, tighten a constraint, delete a field, or change event meaning in the same
release that introduces the replacement unless the compatibility and recovery
proof is equivalent. Do not backfill without a checkpoint or let a migration
share unbounded resources with serving traffic. Do not use a feature flag as a
rollback plan for an irreversible data transform. Do not call a migration safe
because staging has fewer rows or because the tool reported success.

Alternatives include a new table/view with cutover, a compatibility adapter,
versioned endpoint/event, online index build, deferred cleanup, or accepting a
temporary parallel representation. Choose based on observed consumers, lock
budget, data integrity, and recovery—not on a preference for one migration tool.

## Failure modes and containment

| Failure | Impact | Containment and recovery |
|---|---|---|
| Old code sees new required state | outage or rejected writes | additive expand step, compatibility tests, safe defaults |
| New code sees unconverted row | incorrect/null behavior | dual-read/default policy, backfill gate, quarantine |
| Backfill crashes mid-batch | partial data and uncertain progress | idempotent batch, checkpoint, committed-state verification |
| Source changes during backfill | stale target or lost update | version check/change capture/reconciliation |
| Lock/index load exceeds budget | serving outage | online/batched operation, throttling, abort signal |
| Dual write diverges | two truths | outbox/change capture, divergence metric, repair owner |
| Rollback after semantic change | data loss or invalid reads | roll-forward/restore/replay plan, preserve old data |
| Cache/projection remains stale | inconsistent user view | versioned invalidation/rebuild and freshness evidence |
| Event replay repeats side effect | duplicate email/payment/action | isolated replay, idempotency, side-effect filter |
| Consumer omitted from inventory | silent break after contract removal | usage telemetry, compatibility window, delayed contract |
| Backup cannot restore | irrecoverable incident | restore drill and current artifact evidence |
| Partial cutover is hidden | repair cannot target scope | explicit migration state, checkpoint and progress metrics |

## Security implications

Treat migrations as privileged data operations. Restrict who can run, pause,
resume, inspect, redrive, or contract them; audit actions and redact sensitive
values. Preserve tenant boundaries, encryption, retention, deletion, and least
privilege in temporary tables, backfill workers, logs, backups, and comparison
paths. Validate transformed input and prevent injection through dynamic names or
queries. Do not copy sensitive data into a shadow store without its access and
deletion policy. A recovery tool that bypasses authorization is a new production
attack surface. Escalate sensitive, regulatory, payment, tenancy, or destructive
changes through [composition contracts](composition-contracts.md).

## Operational implications

Publish a migration runbook with owner, preflight checks, capacity/lock budget,
batch size and pause control, progress and lag, stop signals, communication,
backup/restore dependency, and recovery commands. Monitor serving latency/errors,
locks, resource use, batch throughput, remaining work, invalid/quarantined rows,
divergence, cache freshness, event lag, and downstream compatibility. Use canary
or bounded batches where possible. Draining a queue, flushing a cache, or
restoring a backup is an operational event, not an invisible implementation
detail.

## Observability implications

Give each migration and batch a stable run/checkpoint ID. Record source/target
versions, selected key range, rows attempted/succeeded/failed/quarantined,
checksums/counts, retry count, batch duration, lock/wait time, resource use,
divergence, cutover state, and last safe point. Correlate data changes to
application version and feature flag. Alert on stalled progress, error/invalid
rate, lock budget, lag, divergence, stale projections/caches, and unexpected
consumer behavior. Keep operator telemetry separate from sensitive row content.

## Testing implications

Apply the migration to isolated representative data including empty, boundary,
large, duplicate, null, invalid, skewed, and sensitive-shaped cases. Test every
old/new deployment order and mixed reader/writer combination; verify API/event/
cache contracts. Exercise batch retry, restart after partial progress,
concurrent source updates, lock/load limits, duplicate backfill, quarantine and
repair, cutover, rollback where genuinely safe, and approved roll-forward or
restore/replay. Measure duration, locks, throughput, resource use, and recovery
in a representative environment. Validate that the harness catches a deliberately
corrupted or incomplete target; a migration tool's exit code is not enough.

## Evidence requirements

Before execution, require an inventory of readers/writers, compatibility matrix,
invariants, data profile, lock/downtime budget, batch/checkpoint design,
observability, authority, and recovery path. Before claiming completion, require:

- forward/backward/mixed-version compatibility results;
- schema, count/checksum, uniqueness, referential, and business-invariant checks;
- backfill progress, retry/restart, concurrent-write, and reconciliation evidence;
- measured duration, locks, load, error behavior, and serving impact;
- cache, projection, event, API, and downstream contract verification;
- rollback/roll-forward/restore/replay evidence appropriate to the chosen path;
- security/access/audit and sensitive-data cleanup evidence; and
- current telemetry plus a documented last-safe-point recovery procedure.

“The migration ran” proves only that a command returned. Without current data,
compatibility, recovery, and operational evidence, the migration remains
unverified and the contract should not be retired.
