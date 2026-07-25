# UI Translation resume — 2026-07-25

## Active task

- Codex task title: `UI Translation`
- Exact selected `TASKS.md` work:

  ```text
  ### [UI Translation](docs/workstreams/ui_translation/README.md)
  - [Investigate](work/__sstates/translation/UI)
      * Deal with remaining issues (items, awakenings, etc.).
  ```

- Current phase: approved implementation, stopped at a safe boundary by the
  user's `zxc`.
- Recommended/selected effort: `ultra`.
- Approval state: approved (`qwe`); resume does not need a new approval.
- Workstream policy:
  - solve one subtask at a time and commit/push it before the next;
  - prefer broad changes over selective fixes.

## Completed checkpoints

- Paired item-status labels were fixed, validated, documented, tested, committed,
  and pushed in `646192a` (`[UI Translation] Localize paired item-status labels`).
- UI-BTL-009 contains three guarded canonical NUN5 donor copies plus the
  ABI-safe pair renderer/layout port.
- Focused tests and the isolated worker ISO build passed for that checkpoint.
- Worker ISO retained for the next runtime check:
  `work/UI translation/build/items-pair.iso`.
- The previous resume handoff was assimilated and removed in `1e7a163`.
- Current recurring policy commits are `3323032` (sequential completion) and
  `3a3ce58` (prefer broad corrections).

## Current incomplete subtask

Only the broad numeric item-status layout is in progress. Single/fixed item
layouts have not started. No canonical file for the numeric correction has been
changed.

The current numeric hypothesis matches the inspected NUN5 objects:

- Health: position `(65, 192)`, offsets `(-20, -30)`, value `10`.
- Chakra: position `(149, 159)`, offsets `(64, -63)`, value `50`.
- Bubble geometry: x-scale `1.25`, y-scale `1.0`, quarter-turn, common origin
  `(-33, -33)`.
- Canonical NUN5 records: Health `0x81`, Chakra `0x82`, Recovery `0x8D`.
- Digit offsets: `-36/-27/-18`, `-32/-22`, and `-26`.
- Lower Y bias: `0x11` (the older `0x13` attempt was wrong).

Task-local exact-guard patch plans and offline-patched states:

- `work/UI translation/runtime-items-v26-numeric-slot03-patches.json`
  (39 patches).
- `work/UI translation/runtime-items-v26-numeric-slot07-patches.json`
  (34 patches; pair-regression case).
- `work/UI translation/artifacts/sstates/items-v26-offline-slot03.p2s`
  (14,363,046 bytes).
- `work/UI translation/artifacts/sstates/items-v26-offline-slot07.p2s`
  (16,164,969 bytes).
- `work/UI translation/temp/patch_item_state.py` generated the patched states.
- `work/UI translation/temp/inspect_item_objects.py` verified the Slot 03
  objects against the values above and found the Slot 07 pair object at
  `(80.062, 202)` with offsets `(-20, -30)`.

References:

- NUN5 numeric:
  `work/UI translation/inputs/sstates/library/Character Items/SLES-55605 (C071D4C1).03.png`
- Original NA2 numeric:
  `work/UI translation/inputs/sstates/library/Character Items/SLPS-22228 (6D94D520).03.png`
- NUN5 pair regression:
  `work/UI translation/inputs/sstates/library/Character Items/SLES-55605 (C071D4C1).07.png`
- Previously accepted pair:
  `work/UI translation/artifacts/screenshots/items-v20b-slot07.png`
  and `work/UI translation/artifacts/sstates/items-v20-slot07.p2s`.

## Runtime state and exact next action

No UI-owned PCSX2 clone process was running at this checkpoint. During the
final post-push verification, an external protected PCSX2 process appeared as
PID `32760` under `@pcsx2_user`. It is not owned by UI Translation: leave it
running and do not inspect, control, or terminate it. Only the protected clone
workflow may be used; do not access or control `@pcsx2_user`,
`@pcsx2_clean`, or another PCSX2 process.

Scripting fixed clone savestate routing and added guarded direct
`capture_frame` in pushed commit `7f64dc5`
(`[Scripting] Repair clone runtime captures`). The UI runtime plan already uses
that action:

`work/UI translation/runtime-items-v26-numeric.json`

Its outputs are:

- `work/UI translation/artifacts/screenshots/items-v26-slot03.png`
- `work/UI translation/artifacts/screenshots/items-v26-slot07.png`
- `work/UI translation/artifacts/runtime/items-v26-numeric.json`

The exact first substantive action after refreshing live policy and Git is:

```powershell
& .\scripts\na2\test_launch.ps1 `
  -WorkerRoot 'work/UI translation' `
  -IsoPath 'work/UI translation/build/items-pair.iso' `
  -OperationPlan 'work/UI translation/runtime-items-v26-numeric.json' `
  -WaitSeconds 1
```

Then inspect the two output images thoroughly as matched checkpoints: NUN5
reference first, Current NA2 second. Confirm both numeric alignment and the
already-accepted pair regression before touching canonical data.

The earlier maintained run used `capture_state`; it failed because PCSX2
produced a valid savestate without embedded `Screenshot.png`. It also exposed
that the launcher used the wrong INI spelling `SaveStates` instead of
`Savestates`. Both maintained-path defects are addressed by `7f64dc5`. Do not
revive the old direct-PINE/task-local runtime bypass.

## Intended canonical implementation after visual validation

If both screenshots validate:

1. Generalize the UI-BTL-009 shared item helper/call ABI so numeric and pair
   layouts use the broad shared correction without duplicating the fix.
2. Move numeric ownership out of the UI-BTL-009 compatibility rows.
3. Add UI-BTL-010 with verified NUN5 donor copies for records `0x81`, `0x82`,
   and `0x8D`, plus only the NA2 port code needed for numeric top/lower/digit
   layout.
4. Update canonical knowledge/tests and the Localization feature pin.
5. Run focused tests, build the isolated worker ISO if still warranted, produce
   the final NUN5/NA2 pair, inspect it, then commit and push this numeric screen
   fix separately before starting single/fixed item layouts.

Do not commit a visual hypothesis merely because the offline object values
match. The direct screenshots are the acceptance evidence.

## Git and concurrent state

- Implementation HEAD before the handoff: `7f64dc5`
  (`[Scripting] Repair clone runtime captures`).
- General concurrently committed the Scripting-wait policy as `b30224d`
  before the first handoff commit `d65a763`.
- Uncommitted concurrent file at stop: `AGENTS.md`.
- Its current remaining diff is not UI-owned and updates only the
  clone-concurrency language. Preserve it exactly; do not stage it in a UI
  commit.
- Stage and commit only this handoff file.
- `.agents/notifications.json` contains `"muted": true`; therefore no
  Notifications-task message is required for this stop.

## Restart checklist

1. Read live `AGENTS.md`, `TASKS.md`, and
   `docs/workstreams/ui_translation/README.md`.
2. Refresh `git status --short --branch` and recent history; preserve concurrent
   changes.
3. Assimilate this handoff, then delete it and commit/push that deletion before
   resuming substantive work.
4. Run the exact guarded `capture_frame` plan above.
5. Present/inspect the paired checkpoints and continue the already-approved
   numeric item-status subtask from the next incomplete step.
