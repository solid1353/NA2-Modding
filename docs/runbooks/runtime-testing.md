# Runtime testing runbook

This runbook owns exact safety and execution procedures for NA2 builds, worker
PCSX2, savestate intake, direct-PINE injection, and runtime screenshots. Read it
only when those operations are part of the task. Validation selection and patch
acceptance remain canonical in
[`../policies/testing.md`](../policies/testing.md).

## User installations and protected inputs

- `@pcsx2_dev` is the protected user-owned installation. Agents may read/copy
  from it but do not create, modify, move, delete, link, launch, or control it
  unless the user explicitly requests the exact action.
- An explicit ISO-launch request uses `@pcsx2_dev`. That authorization covers
  the launch only.
- Builds, direct game-selector launches, and `workshop input [profile]` are
  user-facing operations. Agents use the isolated commands described below.
- Build commands and single-ISO launch commands do not probe or close existing
  PCSX2 processes.

## Chat-owned PCSX2 runtime

Create the runtime only with:

```powershell
@pcsx2_scripts/copy_worker.ps1 -WorkerRoot work/<exact chat title>
```

- The command copies the immutable `@pcsx2_fork` template and required shared
  BIOS into `work/<chat title>/pcsx2/`. Do not assemble the base runtime manually or
  modify/populate the fork template.
- Copy additional shared assets only when the task/test concretely requires
  them. Assign a PINE port unique among live agent instances and operate only
  this chat-owned copy.
- If an old chat-owned runtime exists, its owning chat audits it before reuse.
  Promote needed inputs, evidence, configuration, or generated results, delete
  the obsolete runtime, recreate it with the maintained copy command, and add
  only needed assets. Never replace another task's runtime.
- Agent PCSX2 stays hidden. Use the maintained worker launcher in no-GUI mode;
  it must verify that the launched process owns no visible top-level windows.
  If visibility cannot be suppressed and verified, terminate only that newly
  launched worker process and fail the launch.
- Do not use keyboard/window-message automation or PINE to navigate emulator or
  game menus. A visible runtime is permitted only when the user must personally
  inspect or interact with it; state the required user action before launch.

## Worker ISOs and runtime provenance

- Worker processes never open shared Latest, Previous, Manual, or E2E Test
  ISO paths directly. Create a task-owned hardlink under
  `work/<chat title>/inputs/isos/` to the selected verified hash-cache image.
- Preserve the linked ISO's SHA-256, serial, CRC, applicable build record,
  payload hashes, and symbol map before relying on it for runtime evidence.
- Do not substitute the newest shared ISO when the required identity or linking
  metadata is absent. Ask for the smallest exact missing input.
- Agent-created PCSX2 workers and their ISO hardlinks are disposable task
  artifacts. Before completing the task, stop the worker and delete its
  `pcsx2/` copy and ISO hardlink. Retain only required captures and compact
  provenance outside those disposable paths.

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

## Screenshots and evidence

- Extract `Screenshot.png` from an existing savestate when that frame is enough;
  do not create a complete state solely to obtain a screenshot.
- For a fresh runtime frame, run
  `@pcsx2_scripts/pine.py screenshot` against the task-owned PINE port and poll
  that worker's `snaps/` tree for the new PNG.
- Do not use window capture, screenshot hotkeys, window messages, or
  foregrounding as substitutes.
