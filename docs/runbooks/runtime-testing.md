# Runtime testing runbook

This runbook owns exact safety and execution procedures for NA2 builds, worker
PCSX2, savestate intake, direct-PINE injection, and runtime screenshots. Read it
only when those operations are part of the task. Validation selection and patch
acceptance remain canonical in
[`../policies/testing.md`](../policies/testing.md).

## User installations and protected inputs

- `@pcsx2_dev` and `@pcsx2_stable` are protected user-owned installations.
  Agents may read/copy from them but do not create, modify, move, delete, link,
  launch, or control them unless the user explicitly requests the exact action.
- An explicit ISO-launch request uses `@pcsx2_dev` by default; use stable only
  when the user requests it or the approved task is a stable compatibility or
  release check. That authorization covers the launch only.
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
  ISO paths. Use an independent full copy under
  `work/<chat title>/inputs/isos/`; symlinks and hardlinks are forbidden.
- Preserve the independent ISO's SHA-256, serial, CRC, applicable build record,
  payload hashes, and symbol map before relying on it for runtime evidence.
- Do not substitute the newest shared ISO when the required identity or linking
  metadata is absent. Ask for the smallest exact missing input.
- Retain compact provenance records, but delete disposable ISO copies after the
  selected validation and evidence extraction.

## Agent ISO builds

Use only:

```powershell
na228 worker [--ephemeral] work/<exact chat title>/build/<name>.iso
```

- Worker builds stage beside the requested output and keep operational and
  structured records under `work/<chat title>/logs/`.
- `--ephemeral` requires a destination that does not already exist, performs the
  same preflight and full verified build against a streamed virtual overlay,
  and records and prints the ISO size and SHA-256 without creating `.building`
  or destination ISO files. Use it when the evidence is the build identity
  rather than the image itself.
- They do not touch Latest/Previous, Manual/E2E Test outputs, shared preflight,
  promotion, shared records, PNACH, GameSettings, or PCSX2 state.

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
