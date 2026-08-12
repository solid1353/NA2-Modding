# Logging and retention

Logs are bounded execution records. They explain what a command did recently,
but they are not an archive and must never be the only copy of reusable project
knowledge.

## General rules

- Write bounded shared workflow logs below `@logs/`, generated task records
  below `@task_logs/<exact chat title>/`, and worker build/runtime logs below
  `work/<chat title>/logs/`. Do not write files directly in `@logs/` or
  `@task_logs/`.
- Persist only repository-relative paths or configured `@root/...` aliases.
  Machine-specific absolute paths are forbidden.
- Keep enough detail to reproduce or diagnose the operation: inputs, selected
  configuration or selected catalog nodes, result, binary edits, validation, and failure state.
- Generated logs are ignored by Git and may be deleted. Git is not their
  recovery mechanism.

## Retention

Task-owned logs may remain while they support active work or immediate review.
Before reporting completion, clean task-owned records:

1. Identify exact generated copies of canonical mappings, patch sets, or build
   plans.
2. Promote reusable conclusions—including confirmed roles, mappings, runtime
   observations, media layouts, and useful negative results—into tracked
   knowledge or canonical module data.
3. Verify that every required binary edit is represented by canonical patch data
   with its original bytes, replacement bytes, offset, and reason.
4. Delete disposable records and resulting empty directories.
5. Retain a record only when canonical documentation names a concrete future use
   and regeneration is expensive or impractical.

Large inventories may remain when their structure avoids expensive rediscovery;
size alone does not justify splitting or deleting them.

## Shared task logs

`@task_logs/<exact chat title>/` contains non-canonical generated evidence that
agents may share while working in that chat. Examples include expensive media
inventories and reproducible analyzer reports. The exact chat-title directory
makes ownership explicit; producers must not create anonymous folders directly
below `@task_logs/`.

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
- `manual/<build-id>/`: the latest Manual-only configuration record, including
  `manual_result.tsv`. It is independent of `builds.tsv` and the Latest
  receipt; a successful Manual build replaces the previous Manual record.

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
Manual-only builds always perform complete composition, report whether the
Manual ISO changed, and record that rotation is disabled and PCSX2 is left
running.

## Worker build and runtime logs

`na228 worker [--ephemeral] work/<chat title>/build/<name>.iso` keeps its
operational `latest.log`/`rolling.log` and structured `builds/<build-id>/`
records under that chat's `work/<chat title>/logs/`. Ephemeral worker records
include the verified virtual output size and SHA-256 and mark the output as not
retained; no ISO is written. Worker records never participate in or prune shared
Test/Latest/Previous records. Completed structured worker records are capped at
20 per chat; task cleanup may delete them sooner under the retention rules.

Persistent command logs must be normalized after transcript capture. They omit
PowerShell transcript boilerplate, replace configured roots with aliases, and
record command mode, start/end time, duration, outcome, ISO result/rotation and
configuration record when applicable.
Configuration validation failures are concise in the development console; the
complete captured Python traceback is retained under `technical_details` in the
same bounded run-log section. Other failures retain their existing transcript
behavior.

## Knowledge routing

- Confirmed cross-cutting findings:
  `docs/knowledge/<domain>/<topic>.md`.
- Structured data owned by one module: beside that module, referenced from the
  knowledge index.
- Durable supporting inventories or visual evidence:
  `docs/knowledge/<domain>/<topic>/`.

When evidence changes a conclusion, update the durable knowledge entry and its
canonical data together. Do not expect a future agent to reconstruct the result
from an ignored historical log.
