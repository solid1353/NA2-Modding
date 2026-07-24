# Logging and retention

Logs are bounded execution records. They explain what a command did recently,
but they are not an archive and must never be the only copy of reusable project
knowledge.

## General rules

- Write bounded shared workflow logs below `@logs/`, shared generated
  workstream records below `@workstream_logs/<exact task title>/`, and worker
  build/runtime logs below `work/<task title>/logs/`. Do not write files
  directly in `@logs/` or `@workstream_logs/`.
- Persist only repository-relative paths or configured `@root/...` aliases.
  Machine-specific absolute paths are forbidden.
- Keep enough detail to reproduce or diagnose the operation: inputs, selected
  profile or patches, result, binary edits, validation, and failure state.
- Generated logs are ignored by Git and may be deleted. Git is not their
  recovery mechanism.
- Before deleting logs, inspect them for confirmed reusable findings and useful
  negative results. Promote those findings into `docs/knowledge/` or canonical
  module-local TSV/README data first.

## Shared workstream logs

`@workstream_logs/<exact task title>/` contains generated evidence that is
shared across tasks in one workstream but is not canonical project knowledge.
Examples include expensive media inventories and reproducible analyzer reports.
The exact workstream-title directory makes ownership explicit; producers must
not create anonymous folders directly below `@workstream_logs/`.

A task cleans the records it produced or consumed before reporting completion.
It first promotes every reusable conclusion and useful negative result into
tracked knowledge or canonical module data, then deletes redundant reports and
removes empty directories. A generated record may survive task completion only
when canonical documentation names its concrete future use and it remains
expensive or impractical to regenerate. Retention is never a substitute for
knowledge promotion, and another task's concurrently active records are left
untouched.

## Routine `na2` logs

`@logs/na2/` contains:

- `latest.log`: the latest completed operational invocation.
- `rolling.log`: the newest 20 completed operational invocations, stored as
  bounded sections in one file.
- `builds/<build-id>/`: structured profile records retained only while they
  correspond to `@build/NA2.28 - Current.iso` or
  `@build/NA2.28 - Previous.iso`.
- `builds.tsv`: a single atomically replaced `iso` / `build_record` mapping.
  It always contains rows for the configured current and previous ISO files;
  the previous record is empty when no corresponding retained build record is
  available.
- `preflight/current.json`: the atomically replaced successful-build receipt
  used for no-op detection. It records only portable logical labels, the
  deterministic input fingerprint, and the Current ISO size and SHA-256.
- `candidates/<build-id>/`: the latest candidate-only profile record, including
  `candidate_result.tsv`. It is independent of `builds.tsv` and the Current
  receipt; a successful candidate build replaces the previous candidate record.

Help output is not logged. A preflight cache hit reuses the Current ISO's
structured record. A full verified build always retains its new structured
record as the Current ISO's latest provenance, even when the candidate is
identical and records `ISO result: unchanged`; the superseded record is then
pruned, so this does not increase retained history. A changed candidate records
`ISO result: updated`; its structured record becomes current and the previous
current record rotates with the outgoing ISO. Unreferenced structured records
are deleted only after the complete two-ISO mapping has been replaced.
Deleting or corrupting the preflight receipt is safe: the next invocation runs
the complete verified build and recreates the receipt only after success.
Candidate-only builds always perform complete composition, report whether the
Candidate ISO changed, and record that rotation and PCSX2 shutdown were both
disabled.

## Worker build and runtime logs

`na2 -t work/<task title>/build/<name>.iso` keeps its operational
`latest.log`/`rolling.log` and structured `builds/<build-id>/` records under
that task's `work/<task title>/logs/`. Worker records never participate in or
prune shared Candidate/Current/Previous records. Completed structured worker
records are capped at 20 per task; task cleanup may delete them sooner after
promoting reusable findings.

Each agent PCSX2 launch uses a unique run directory under the same worker log
root. PCSX2's file log is redirected there. A portable `pcsx2-instance.json`
is created immediately after launch and normally removed after targeted
shutdown. It records the PID/start time, validated window handle, ISO identity,
task-owned card and paths, unique PINE port, and the hash of a launch-local
ownership capability without persisting that capability or absolute paths. If
ownership is lost, the wrapper leaves the process and runtime directory
untouched and reports the retained runtime location. A descriptor left there is
diagnostic only because the capability is gone.

Persistent command logs must be normalized after transcript capture. They omit
PowerShell transcript boilerplate, replace configured roots with aliases, and
record command mode, start/end time, duration, outcome, ISO result/rotation and
profile record when applicable. An on-demand `na2 act` run records PNACH
actualization status and enabled cheats.

## Other task logs

Task-specific analysis, extraction, and patch logs may remain while they support
active work or immediate review. Before reporting task completion:

1. Identify records that are exact generated copies of canonical mappings,
   patch sets, or build plans.
2. Promote confirmed function roles, caller/callee relationships, state-machine
   behavior, address/file-offset mappings, runtime observations, media layouts,
   and important negative tests into tracked knowledge.
3. Verify that every required binary edit is represented by canonical patch data
   with its original bytes, replacement bytes, offset, and reason.
4. Delete every disposable generated log directly and remove resulting empty
   directories.
5. Retain a log only for a named concrete future use recorded in canonical
   documentation; never retain it merely as history.

Large inventories are allowed when their structured contents avoid expensive
rediscovery. Size alone is not a reason to split or delete a useful record.

## Knowledge routing

- Confirmed cross-cutting findings:
  `docs/knowledge/<domain>/<topic>.md`.
- Structured data owned by one module: beside that module, referenced from the
  knowledge index.
- Durable supporting inventories or visual evidence:
  `docs/knowledge/<domain>/<topic>/`.
- Unconfirmed interpretations and future experiments: `docs/HYPOTHESES.md`.

When evidence changes a conclusion, update the durable knowledge entry and its
canonical data together. Do not expect a future agent to reconstruct the result
from an ignored historical log.
