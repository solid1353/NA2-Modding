# Font resume handoff — 2026-07-25

## Objective and authorization

- Codex task/chat title: `Font`.
- Live selected `TASKS.md` entry: `Implement proper autofit/positions everywhere.`
- Immediate user request under investigation: `your fucking latest patch broke the game. it freezes upon entering the load screen. investigate`
- This immediate request authorizes diagnosis, not an implementation fix.
- The selected task and its existing execution plan remain approved (`qwe` was
  given earlier). The Font workstream policy requires broad shared-renderer
  corrections where appropriate and requires each subtask to be completed,
  committed, and pushed before the next one.
- Current selected/recommended effort: `max`; this is a cross-screen renderer,
  MIPS-helper, savestate, and runtime-transition diagnosis.

## Current phase

Read-only/static diagnosis plus a task-local isolated runtime reproduction.
No canonical Font implementation was changed during this diagnostic turn.
The user issued `zxc` after the maintained launcher was repaired, before the
real component reproduction could be rerun.

## Confirmed completed work

1. Refreshed live repository state, reread the applicable live rules and Font
   workstream policy, and retained the existing approved task scope.
2. Removed the preceding consumed Font handoff and pushed commit `93d7177`
   (`[Font] Remove resumed checkpoint`).
3. Confirmed that the latest suspect Font implementation is pushed commit
   `3d52a14` (`[Font] Port shared NUN5 text fitting and layout`).
4. Confirmed that the ten current copied Font slots contain no Save/Load
   screen. Located the older retained Load-list state:
   `work/Font/reference/20260719_clean_vertical_runtime/states/SLPS-22228 (7978E5A4).03.p2s`.
5. Prepared a six-case task-local component isolation:
   baseline, metrics-only, selected-choice-only, UI passthrough, full UI, and
   combined metrics/selected/UI.
6. The first maintained isolated PCSX2 attempt did not test Font behavior.
   `work/Font/logs/20260725_052812_763_pid16116_948af16c/emulog.txt` proves the
   launcher copied the requested state to an obsolete directory, PCSX2
   reported slot 70 empty, and the later capture action saved a fresh boot
   state. The owned instance then closed successfully.
7. Scripting fixed that maintained interface and pushed `7f64dc5`
   (`[Scripting] Repair clone runtime captures`). `load_state` now uses the
   persistent clone's `sstates` directory, the stale `SaveStates` setting is
   migrated to the real `Savestates = sstates`, and `capture_frame` now obtains
   an owned-clone screenshot without relying on an embedded savestate image.
8. Parsed the clean NA2 ELF layout. Both helper runtime
   `0x003D3E00..0x003D4388` and scratch runtime
   `0x003FAD20..0x003FAD60` are inside the single resident RWX load segment
   beginning at runtime `0x00100000`; this alone does not prove that game code
   never reuses the zero ranges.

## Static findings and open hypotheses

- The shared UI hook at runtime `0x00379A20` writes RA/A0-A3 into one global
  scratch record and dereferences `a1 + 0` / `a1 + 4` before checking whether
  the caller is one of the intended Font families. A Load-specific caller with
  a different argument contract could therefore fail before fallback.
- The UI helper uses one global scratch record while it calls original
  rendering and measurement routines. Re-entry would overwrite saved RA and
  arguments.
- The complete helper block was selected because the clean ELF and 16 sampled
  states were zero and three marker words survived a five-second boot settle.
  That evidence never covered entry into the Save/Load subsystem. If the Load
  transition clears or reuses runtime `0x003D3E00..0x003D4388`, the still-live
  global space/newline/UI hooks will jump into zero or unrelated data and can
  freeze immediately.
- Load text contains ordinary ASCII spaces, so the global space hook at
  `0x001892EC` provides an immediate trigger if its helper at `0x003D42C0` was
  destroyed.
- These are hypotheses, not yet a confirmed root cause. Do not alter the
  canonical Font package until the isolated component run or a frozen user
  state identifies the first failing component.

## Retained task-owned files

- `work/Font/analysis/load_freeze/find_save_load_states.py`
- `work/Font/analysis/load_freeze/state_similarity.json`
- `work/Font/analysis/load_freeze/prepare_component_repro.py`
- `work/Font/analysis/load_freeze/inspect_elf_layout.py`
- `work/Font/artifacts/load_freeze/component_repro/prepared.json`
- `work/Font/artifacts/load_freeze/component_repro/states/`
- `work/Font/operations/load_freeze_component_repro.json`
- `work/Font/build/font-test.iso`
- `work/Font/logs/20260725_052812_763_pid16116_948af16c/emulog.txt`
- Existing broader Font analysis, references, inputs, and artifacts remain
  under `work/Font/`.

The component states use fresh slots and exact byte guards. The operation plan
still uses `capture_state`; on resume, change its task-local generator/plan to
use the new `capture_frame` action for screenshots before rerunning it.

## Commands and results

Failed pre-fix real invocation:

```powershell
& .\scripts\na2\test_launch.ps1 `
  -WorkerRoot 'work/Font' `
  -IsoPath 'work/Font/build/font-test.iso' `
  -OperationPlan 'work/Font/operations/load_freeze_component_repro.json'
```

The invocation remains the same after `7f64dc5`; only screenshot actions in the
JSON should use `capture_frame`.

ELF inspection:

```powershell
python work/Font/analysis/load_freeze/inspect_elf_layout.py
```

It reported the main load segment as file offset `0x100`, runtime
`0x00100000`, file size `0x507380`, memory size `0x5B3F00`, flags `0x7`, and
confirmed that both target ranges are inside it.

## Git and workspace state at stop

- HEAD/origin at checkpoint creation: `7f64dc50575a421c81ba560c72379f1ddb8edfff`
  (`[Scripting] Repair clone runtime captures`).
- Font owns no staged or unstaged canonical implementation paths.
- The task-local `work/Font/` diagnostic files are ignored working artifacts.
- `AGENTS.md` has an unstaged concurrent Scripting hunk updating the clone
  concurrency wording; it is not Font-owned and must remain untouched.
- This handoff is the only Font-owned tracked change to commit for `zxc`.

## Processes, resources, and user input

- No Font PCSX2 process is running.
- The failed pre-fix launcher closed only its authenticated task-owned clone.
- No build, Git, PCSX2, or physical-input resource is held by Font.
- No wakeup is pending.
- A user-created savestate captured while the Load screen is actually frozen
  would be conclusive but is not yet required. If provided under
  `work/__sstates/translation/font/`, copy it into `work/Font/inputs/` before
  analysis and compare helper/scratch/hook bytes without modifying the user
  library.

## Exact resume sequence

1. Reread live `AGENTS.md`, this handoff, live Git status/history, the Font
   policy, the selected `TASKS.md` entry, and Scripting commit `7f64dc5`.
2. Validate that `3d52a14` remains in history, the task-owned component states
   and worker ISO still exist, and no Font PCSX2 instance is retained.
3. Delete this assimilated handoff, commit and push that deletion alone.
4. Update only the task-local component-repro generator/operation to use
   `capture_frame`, regenerate if necessary, and rerun the unchanged maintained
   invocation.
5. Identify the first failing case. If passthrough fails, investigate cave or
   trampoline placement; if full UI fails after passthrough passes, investigate
   UI scratch/caller/re-entry behavior; if metrics-only fails, isolate the
   global metric helpers. Do not implement a canonical fix until diagnosis is
   established or the user explicitly requests one.

