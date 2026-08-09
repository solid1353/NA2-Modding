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
- User savestates and screenshots under either installation are read-only input
  libraries. Outside maintained E2E, savestates may be copied with provenance
  and inspected only as immutable diagnostic evidence; agents do not create,
  modify, convert, patch, load, replay, or inject through them. Maintained E2E
  is the only agent-executed savestate path and applies only to selected visual
  validation.
- Builds, direct game-selector launches, and `workshop input [profile]` are
  user-facing operations. Agents use the isolated commands described below.
- Build commands and single-ISO launch commands do not probe or close existing
  PCSX2 processes.

## Task-owned PCSX2 runtime

Create the runtime only with:

```powershell
@pcsx2_scripts/copy_worker.ps1 -WorkerRoot work/<exact task title>
```

- The command copies the immutable `@pcsx2_clean` template and required shared
  BIOS into `work/<task>/pcsx2/`. Do not assemble the base runtime manually or
  modify/populate the clean template.
- Copy additional shared assets only when the task/test concretely requires
  them. Assign a PINE port unique among live agent instances and operate only
  this task-owned copy.
- If an old task-owned runtime exists, its owning task audits it before reuse.
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

- Worker processes never open shared Latest, Previous, Manual Test, or E2E Test
  ISO paths. Use an independent full copy under
  `work/<task>/inputs/isos/`; symlinks and hardlinks are forbidden.
- Preserve the independent ISO's SHA-256, serial, CRC, applicable build record,
  payload hashes, and symbol map before relying on it for runtime evidence.
- Do not substitute the newest shared ISO when the required identity or linking
  metadata is absent. Ask for the smallest exact missing input.
- Retain compact provenance records, but delete disposable ISO copies after the
  selected validation and evidence extraction.

## Agent ISO builds

Use only:

```powershell
na228 worker work/<exact task title>/build/<name>.iso
```

- Worker builds stage beside the requested output and keep operational and
  structured records under `work/<task>/logs/`.
- They do not touch Latest/Previous, Manual/E2E Test outputs, shared preflight,
  promotion, shared records, PNACH, GameSettings, or PCSX2 state.
- Build only when the selected validation genuinely requires image assembly or
  runtime execution. The ISO is an internal agent validation artifact, never a
  user testing ground or deliverable.
- Do not build or launch an ISO merely to prepare user verification. After the
  selected validation and evidence extraction, delete the ISO whether
  validation passes or fails.

Current shared-build and user-facing command behavior is documented by
`na228 help`, [`../../scripts/README.md`](../../scripts/README.md), and
[`../../e2e/README.md`](../../e2e/README.md), not redefined here.

## Direct-PINE candidate injection

Direct injection is development evidence, not integrated-build or release
acceptance. Every development injection candidate compiles and links
`src/hot_reload_message.c`, installs its visible marker call, and treats that
source as a rebuild input; the marker never enters normal profile or release
composition.

- Agents do not use `scripts/injection/inject_candidate.ps1` for validation
  because it loads a savestate. Do not invoke its internal build/apply stages
  separately or transport candidates through PNACH, cheat-folder sync,
  install/restore state, or filesystem watchers.
- `scripts/injection/watch.ps1` is user-only live-editing convenience. Agents do
  not run or depend on it.

## Screenshots and evidence

- Extract `Screenshot.png` from an existing savestate when that frame is enough;
  do not create a complete state solely to obtain a screenshot.
- For a fresh runtime frame, run
  `@pcsx2_scripts/pine.py screenshot` against the task-owned PINE port and poll
  that worker's `snaps/` tree for the new PNG.
- Do not use window capture, screenshot hotkeys, window messages, or
  foregrounding as substitutes.
- Agents do not create savestates outside maintained E2E.
