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
  libraries. Copy selected files with provenance into the task's `inputs/`
  tree. If the required state was not supplied, ask for that exact state rather
  than navigating to or manufacturing a substitute.
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

## Worker ISOs and savestate provenance

- Worker processes never open shared Latest, Previous, Manual Test, or E2E Test
  ISO paths. Use an independent full copy under
  `work/<task>/inputs/isos/`; symlinks and hardlinks are forbidden.
- Treat each NA2 savestate batch and its runtime dependencies as one intake
  bundle. Before implementation or runtime iteration, preserve:
  - the compatible independent ISO;
  - its SHA-256, serial, and CRC;
  - hashes of every resident/overlay payload whose addresses are imported;
  - either the matching payload-builder record and `symbol_map.tsv`, or complete
    independently verified resident-symbol overrides for the selected closure.
- Copy rotation-sensitive records into
  `work/<task>/inputs/runtime-records/<payload-sha256>/` while available and link
  them from the batch provenance.
- A state/ISO pair is not injection-ready when required payload identity or
  linking metadata is absent. Ask immediately for the smallest exact replacement
  input; do not substitute the newest shared ISO or create a replacement build.
- Before using a savestate to validate file-backed overlays or resident payloads,
  determine whether loading it restores the modified executable regions. If it
  does, use an exact guarded conversion or a user-supplied post-build state.
- Retain ISO copies and runtime metadata while an active compatible batch/test
  needs them. Remove superseded images only after no active case references
  them; preserve compact provenance records.

## Agent ISO builds

Use only:

```powershell
na228 worker work/<exact task title>/build/<name>.iso
```

- Worker builds stage beside the requested output and keep operational and
  structured records under `work/<task>/logs/`.
- They do not touch Latest/Previous, Manual/E2E Test outputs, shared preflight,
  promotion, shared records, PNACH, GameSettings, or PCSX2 state.
- Build only when an available compatible savestate reaches the target without
  navigation, when testing boot/startup behavior needs no navigation, or when
  the user explicitly requests the build.
- Temporary/hypothesis ISOs remain task-owned only while they have a named use
  and are deleted when no longer useful.

Current shared-build and user-facing command behavior is documented by
`na228 help`, [`../../scripts/README.md`](../../scripts/README.md), and
[`../../e2e/README.md`](../../e2e/README.md), not redefined here.

## Direct-PINE candidate injection

Direct injection is development evidence, not integrated-build or release
acceptance. Every development injection candidate compiles and links
`src/hot_reload_message.c`, installs its visible marker call, and treats that
source as a rebuild input; the marker never enters normal profile or release
composition.

Agent savestate-based C iteration uses only:

```powershell
scripts/injection/inject_candidate.ps1 `
  -SourceId <source> `
  -Entry <symbol> `
  -OverlayPlan work/<task>/<plan>.json `
  -IsoPath work/<task>/inputs/isos/<matching>.iso `
  -StateSlot <slot> `
  -PinePort <task-port>
```

- The command builds/links canonical C and the task-owned overlay plan, reloads
  the supplied state and waits for completion, applies guarded writes through
  PINE while paused, refreshes execution caches, and restores the prior VM state.
- Do not invoke its internal build/apply stages separately for agent runtime
  testing. Do not transport candidates through PNACH, cheat-folder sync,
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
- Create a new savestate only when the state itself is a required artifact.
