# Runtime testing runbook

This runbook owns exact safety and execution procedures for NA2 builds, PCSX2,
savestate intake, direct-PINE injection, and runtime screenshots. Read it
only when those operations are part of the task. Validation selection and patch
acceptance remain canonical in
[`../policies/testing.md`](../policies/testing.md).

## PCSX2 installation

- `@pcsx2_dev` is the only PCSX2 installation agents may use. Do not create,
  copy, select, launch, or control another PCSX2 installation or runtime,
  including `@pcsx2_fork` or a chat-owned copy.
- `@pcsx2_dev` remains protected and user-owned. Agents may read it or copy
  individual evidence from it, but do not create, modify, move, delete, or link
  anything inside it unless the user explicitly requests the exact action.
- An explicit PCSX2 operation uses `@pcsx2_dev` and authorizes only the exact
  requested operation. It does not authorize probing, closing, or otherwise
  controlling an existing PCSX2 process.

## Runtime ISO provenance

- For agent PCSX2 operations, do not open shared Latest, Previous, Manual, or
  E2E Test ISO paths directly. Create a task-owned hardlink under
  `work/<chat title>/inputs/isos/` to the selected verified hash-cache image.
- Preserve the linked ISO's SHA-256, serial, CRC, applicable build record,
  payload hashes, and symbol map before relying on it for runtime evidence.
- Do not substitute the newest shared ISO when the required identity or linking
  metadata is absent. Ask for the smallest exact missing input.
- The task-owned ISO hardlink is disposable. Delete it after the selected
  validation and evidence extraction. Retain only required captures and compact
  provenance outside that disposable path.

## Agent ISO builds

Use only:

```powershell
na228 worker [--configuration <id>] work/<exact chat title>/build/<name>.iso
```

- Worker builds use `test` unless `--configuration <id>` is supplied. They keep
  operational and structured records under `work/<chat title>/logs/` and share
  exact verified identities with all other build roles through the central
  registry.
- Worker output paths are hardlinks to canonical hash-named cache images. Delete
  the task-owned output link after evidence extraction unless retention was
  explicitly requested; do not delete the bounded shared cache image.
- They do not touch Latest/Previous, Manual/E2E Test outputs or their role
  records, promotion, PNACH, GameSettings, or PCSX2 state.

Current shared-build and user-facing command behavior is documented by
`na228 help`, [`../../scripts/README.md`](../../scripts/README.md), and
[`../../e2e/README.md`](../../e2e/README.md), not redefined here.

## User-provided input recordings

This procedure applies only when the user provides an input recording for the
task. Use explicit, separate capture paths below the acting chat's workspace;
never omit the capture path and thereby use Workshop's default.

Before implementation, capture the configured baseline:

```powershell
ws <game> -s <recording> work/<exact chat title>/captures/<recording>/baseline
```

If the completed implementation changes game logic, build the selected worker
ISO after all earlier checks pass, then capture the candidate through the same
command using the worker ISO path as its target:

```powershell
ws work/<exact chat title>/build/<name>.iso `
  -s <recording> `
  work/<exact chat title>/captures/<recording>/candidate
```

Use the same explicit `-mc <card>` on both commands when the recording depends
on a nondefault memory card. Compare the task-relevant baseline and candidate
savestates and screenshots, report the observed result, and then apply the
normal worker-ISO and artifact-retention cleanup rules.

## Screenshots and evidence

- Extract `Screenshot.png` from an existing savestate when that frame is enough;
  do not create a complete state solely to obtain a screenshot.
- For a fresh runtime frame, run
  `@pcsx2_scripts/pine.py screenshot` against the explicitly authorized
  `@pcsx2_dev` PINE port and poll that installation's `snaps/` tree for the new
  PNG.
- Do not use window capture, screenshot hotkeys, window messages, or
  foregrounding as substitutes.
