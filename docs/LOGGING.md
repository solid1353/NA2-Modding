# Logging and retention

Logs are bounded execution records. They explain what a command did recently,
but they are not an archive and must never be the only copy of reusable project
knowledge.

## General rules

- Write logs only below `@logs/`, grouped by workflow or task. Do not write
  files directly in the log root.
- Persist only repository-relative paths or configured `@root/...` aliases.
  Machine-specific absolute paths are forbidden.
- Keep enough detail to reproduce or diagnose the operation: inputs, selected
  profile or patches, result, binary edits, validation, and failure state.
- Generated logs are ignored by Git and may be deleted. Git is not their
  recovery mechanism.
- Before deleting logs, inspect them for confirmed reusable findings and useful
  negative results. Promote those findings into `docs/knowledge/` or canonical
  module-local TSV/README data first.

## Routine `na2` logs

`@logs/na2/` contains:

- `latest.log`: the latest completed operational invocation.
- `rolling.log`: the newest 20 completed operational invocations, stored as
  bounded sections in one file.
- `builds/<build-id>/`: structured profile records retained only while they
  correspond to `@build/Current.iso` or `@build/Previous.iso`.
- `builds.tsv`: a single atomically replaced `iso` / `build_record` mapping.
  It always contains rows for `@build/Current.iso` and
  `@build/Previous.iso`; the latter record is empty when no corresponding
  retained build record is available.

Help output is not logged. A verified candidate identical to `Current.iso`
records `ISO result: unchanged` in the command log and does not retain another
full structured profile record. A changed candidate records
`ISO result: updated`; its structured record becomes current and the previous
current record rotates with the outgoing ISO. Unreferenced structured records
are deleted only after the complete two-ISO mapping has been replaced.

Persistent command logs must be normalized after transcript capture. They omit
PowerShell transcript boilerplate, replace configured roots with aliases, and
record command mode, start/end time, duration, outcome, ISO result/rotation when
applicable, profile record, PNACH actualization status, and enabled cheats.

## Other task logs

Task-specific analysis, extraction, and patch logs may remain while they support
active work or immediate review. At task completion:

1. Identify records that are exact generated copies of canonical mappings,
   patch sets, or build plans.
2. Promote confirmed function roles, caller/callee relationships, state-machine
   behavior, address/file-offset mappings, runtime observations, media layouts,
   and important negative tests into tracked knowledge.
3. Verify that every required binary edit is represented by canonical patch data
   with its original bytes, replacement bytes, offset, and reason.
4. Delete redundant generated logs directly. Do not create a replacement trash
   archive.

Large inventories are allowed when their structured contents avoid expensive
rediscovery. Size alone is not a reason to split or delete a useful record.

## Knowledge routing

- Confirmed cross-cutting findings: `docs/knowledge/<topic>.md`.
- Structured data owned by one module: beside that module, referenced from the
  knowledge index.
- Durable supporting inventories or visual evidence:
  `docs/knowledge/<topic>/`.
- Unconfirmed interpretations and future experiments: `docs/HYPOTHESES.md`.

When evidence changes a conclusion, update the durable knowledge entry and its
canonical data together. Do not expect a future agent to reconstruct the result
from an ignored historical log.
