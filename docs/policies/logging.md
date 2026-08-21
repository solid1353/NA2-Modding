# Logging and retention

Logs are bounded execution records. They explain what a command did recently,
but they are not an archive and must never be the only copy of reusable project
knowledge.

## General rules

- Write bounded shared workflow logs below `@logs/`, generated task records
  below `@task_logs/<exact chat title>/`, and cache-build/runtime logs below
  `@work/<chat title>/logs/`. Do not write files directly in `@logs/` or
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
- `preflight/registry.json`: the atomically replaced shared verified-build
  registry used by Latest, Manual, E2E, and cache builds. Each
  fingerprint entry records its deterministic byte-affecting state, ISO
  SHA-256, and verification time. Image records keyed by SHA-256 own verified
  size and portable physical locations, so distinct fingerprints with identical
  output reuse the same image.
- `preflight/records/<fingerprint>/`: reusable structured provenance for each
  registry entry. Registry entries, provenance records, and cached images are
  capped at 20; retained locations per image are independently capped at 20.
- `manual/<build-id>/`: the latest Manual-only configuration record, including
  `build_result.tsv`. It is independent of `builds.tsv`; a successful Manual
  build replaces the previous Manual record.

Help output is not logged. An exact registry hit clones the matching structured
provenance into the invocation's role-specific build record without repeating
assembly. A full verified physical build first moves its unique candidate into
`@cache/isos/<SHA-256>.iso` and registers it. Promotion then updates a
user-facing build role by creating or atomically replacing a hardlink to the
canonical hash-named image. Cache validation uses the canonical cache image
directly and creates no task-owned ISO or hardlink. Latest rotation similarly
replaces Previous with a hardlink to the outgoing Latest image and synchronizes
both locations in the registry.
If a destination is locked, the invocation reports pending and the hash-named
ISO remains available for launch. The next request with the same fingerprint
retries promotion naturally through the cache hit.
Physical incoming candidates use exclusive activity locks; the next physical
build removes unlocked crash leftovers before creating its own candidate.
Deleting or corrupting the registry is safe: the next invocation runs the
complete verified build and recreates it only after success.
Manual-only builds require an exact fully verified composition, which may be
reused from the shared registry. They report whether the Manual ISO changed and
record that rotation is disabled and PCSX2 is left running.

## Cache build and runtime logs

`na228 build -c <configuration>` keeps its operational
`latest.log`/`rolling.log` and structured `builds/<build-id>/` records under the
acting chat's `@work/<chat title>/logs/` when `NA228_TASK_WORK_ROOT` is set. It
participates in the shared verified-build registry and returns its canonical
cached ISO path without creating a separate output. Cache builds never
participate in or prune shared Test/Latest/Previous role records. Completed
structured cache-build records are capped at 20 per chat; task cleanup may
delete them sooner under the retention rules.

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
