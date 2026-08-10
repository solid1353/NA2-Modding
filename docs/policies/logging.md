# Logging and retention

Logs are bounded execution records. They explain what a command did recently,
but they are not an archive and must never be the only copy of reusable project
knowledge.

## General rules

- Write bounded shared workflow logs below `@logs/`, generated task records
  below `@task_logs/<exact task title>/`, and worker build/runtime logs below
  `work/<task title>/logs/`. Do not write files directly in `@logs/` or
  `@task_logs/`.
- Persist only repository-relative paths or configured `@root/...` aliases.
  Machine-specific absolute paths are forbidden.
- Keep enough detail to reproduce or diagnose the operation: inputs, selected
  configuration or selected catalog nodes, result, binary edits, validation, and failure state.
- Generated logs are ignored by Git and may be deleted. Git is not their
  recovery mechanism.
- Before deleting logs, inspect them for confirmed reusable findings and useful
  negative results. Promote those findings into `docs/knowledge/` or canonical
  module-local TSV/README data first.

## Shared task logs

`@task_logs/<exact task title>/` contains non-canonical generated evidence that
agents may share while working on that task. Examples include expensive media
inventories and reproducible analyzer reports. The exact task-title directory
makes ownership explicit; producers must not create anonymous folders directly
below `@task_logs/`.

A task cleans the records it produced or consumed before reporting completion.
It first promotes every reusable conclusion and useful negative result into
tracked knowledge or canonical module data, then deletes redundant reports and
removes empty directories. A generated record may survive task completion only
when canonical documentation names its concrete future use and it remains
expensive or impractical to regenerate. Retention is never a substitute for
knowledge promotion, and another task's concurrently active records are left
untouched.

## Routine `na228` logs

`@logs/na228/` contains:

- `latest.log`: the latest completed operational invocation.
- `rolling.log`: the newest 20 completed operational invocations, stored as
  bounded sections in one file.
- `builds/<build-id>/`: structured configuration records retained only while they
  correspond to the catalog-derived Latest, Previous, normal E2E Test, or
  shifted E2E Test ISO.
- `builds.tsv`: a single atomically replaced `iso` / `build_record` mapping.
  It contains one row for each of those four roles; a row is empty when no
  corresponding retained build record is available. Parallel build completion
  serializes map replacement through `@logs/na228/.builds.lock` and preserves
  active, not-yet-mapped build records.
- `preflight/latest.json`: the atomically replaced successful-build receipt
  used for no-op detection. It records only portable logical labels, the
  deterministic input fingerprint, and the Latest ISO size and SHA-256.
- `preflight/e2e_test_normal.json` and `preflight/e2e_test_shifted.json`: the
  output-specific receipts for the normal and shifted E2E Test variants. Their
  fingerprints include both the resident-payload layout shift and the build role's
  boot-ELF CRC discriminator.
- `manual_tests/<build-id>/`: the latest Manual Test-only configuration record, including
  `manual_test_result.tsv`. It is independent of `builds.tsv` and the Latest
  receipt; a successful Manual Test build replaces the previous Manual Test record.

Help output is not logged. A preflight cache hit reuses the Latest ISO's
structured record. A full verified build always retains its new structured
record as the Latest ISO's latest provenance, even when the staged image is
identical and records `ISO result: unchanged`; the superseded record is then
pruned, so this does not increase retained history. A changed staged image records
`ISO result: updated`; its structured record becomes latest and the previous
latest record rotates with the outgoing ISO. Unreferenced structured records
are deleted only after the complete four-role mapping has been replaced.
Deleting or corrupting the preflight receipt is safe: the next invocation runs
the complete verified build and recreates the receipt only after success.
Manual Test-only builds always perform complete composition, report whether the
Manual Test ISO changed, and record that rotation is disabled and PCSX2 is left
running.

## Worker build and runtime logs

`na228 worker work/<task title>/build/<name>.iso` keeps its operational
`latest.log`/`rolling.log` and structured `builds/<build-id>/` records under
that task's `work/<task title>/logs/`. Worker records never participate in or
prune shared Test/Latest/Previous records. Completed structured worker
records are capped at 20 per task; task cleanup may delete them sooner after
promoting reusable findings.

Persistent command logs must be normalized after transcript capture. They omit
PowerShell transcript boilerplate, replace configured roots with aliases, and
record command mode, start/end time, duration, outcome, ISO result/rotation and
configuration record when applicable. `act` records source-input synchronization.
Configuration validation failures are concise in the development console; the
complete captured Python traceback is retained under `technical_details` in the
same bounded run-log section. Other failures retain their existing transcript
behavior.

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
- Unconfirmed interpretations and future experiments: explicitly labelled
  sections in the relevant domain-owned knowledge document.

When evidence changes a conclusion, update the durable knowledge entry and its
canonical data together. Do not expect a future agent to reconstruct the result
from an ignored historical log.
