# Font Priority 3 Jutsu-selector resume

## Objective and state

- Workstream: Font.
- Selected task: the approved Continuous `Layout/autofit epic`.
- Current subtask: Priority 3, replacement ss3–ss6 Jutsu-selector defect.
- Phase: runtime candidate tuning; stopped at the user's request until explicitly
  resumed.
- Recommended effort: Max.
- Approval: the epic and current implementation plan remain approved. The user
  authorized exactly `ss3 -> Cross -> ss4 -> Circle -> ss5 -> Cross -> ss6`.
- Do not begin another priority before this one reaches its commit, push, and
  report boundary.

## Recoverable canonical changes

The incomplete Font implementation is isolated in:

- stash identity: `a370cbfffdd2a55d8b8353e4fc7802a7578c4f7c`
- stash selector at creation: `stash@{0}`
- stash subject: `[Font] Checkpoint Priority 3 Jutsu selector`
- base HEAD: `0e55e0ec`

The stash contains only:

- `docs/knowledge/localization/font/README.md`
- `docs/workstreams/font/epics/ss2-6-layout/README.md`
- `na228_builder/features/localization/runtime_injector/c_fragments.tsv`
- `na228_builder/features/localization/runtime_injector/sources/font_v2_core.c`

Verify by object ID, not by assuming `stash@{0}` still points to the same
entry. Keep the stash until its four paths apply cleanly and are verified.
Unrelated Project-owned `games.json`/path-loader/launcher changes were left in
the shared worktree and were neither stashed nor reverted.

## Completed work and decisions

- Pushed pending PCSX2 commit
  `98b8911cc Add PINE pad pulse command (AI-assisted)` to configured
  `origin/pine-reload-patches`. Normal configured pushes have standing
  authorization and must never be presented as a user approval gate.
- Replaced the ineffective three-setter hypothesis with the exact Jutsu-row
  text caller.
- Exact NA2 draw:
  - BTL file `0x9178`
  - Ghidra `0x006BCF9C`
  - live MWo3 `0x006BCFDC`
  - guard `5020060C00000000`
  - native target `0x00188140`
- Exact NUN5 homolog:
  - row compositor `FUN_006CFE70`
  - boxed-renderer call at Ghidra `0x006D02DC`
  - box `186 x 32`
  - two-line limit
  - start-horizontal, center-vertical
  - origin relative to NA2: left X `-7`, right X `-4`, Y `-10`
- Added a bounded C entry/callback that copies at most 255 source bytes, wraps
  through the accepted native-measure helper, draws through the shared Font v2
  session, and restores renderer position.
- Reduced the task-owned overlay to one guarded caller write:
  `work/Font/operations/jutsu_names_overlay.json`.
- The first working runtime candidate wrapped `Naruto Uzumaki Combo Attack` as
  `Naruto Uzumaki` / `Combo Attack` in both visible states without overflow.
- Pixel comparison at NUN5 resolution showed the first line 3 pixels high and
  the second line 8 pixels high. The active newline hook scales a path whose
  effective pre-scale advance is 28 units, not the shared 40-unit nominal
  value used to derive session scale.
- The untested checkpoint candidate changes the configured Jutsu line advance
  to `28.571428f` so the effective output advance becomes 20 units, and adds a
  six-unit multiline-only Y compensation to retain the first-line origin.
- Promoted the exact disassembly, hashes, geometry, caller guard, runtime
  result, and remaining uncertainty to canonical Font knowledge in the stash.
- Updated the active epic state in the stash from the obsolete
  balanced-wrapper/three-call description to the exact one-call candidate.

## Runtime evidence and retained inputs

- Batch:
  `work/Font/inputs/sstates/batches/2026-07-30-ss1-10/`
- Paired screenshots:
  `work/Font/inputs/screenshots/batches/2026-07-30-ss1-10/`
- NUN5 targets:
  - `ss05_NUN5.png`
  - `ss06_NUN5.png`
- Compatible task ISO:
  `work/Font/inputs/isos/NA2.28-2D8AE8A6.iso`
- ISO SHA-256:
  `57F8E2FAF1DBFC9381C5E2BA0C183B87FC7A26971EEBF41B8B59FD76ED99B5A1`
- Worker clone: `work/Font/pcsx2/`
- PINE port: `28015`
- First wrapped ss5 capture:
  `work/Font/pcsx2/snaps/SLOP-NA228 [_]/SLOP-NA228 [_]_SLOP-NA228_20260730092232.png`
- Measured 22.222222 candidate ss5:
  `work/Font/pcsx2/snaps/SLOP-NA228 [_]/SLOP-NA228 [_]_SLOP-NA228_20260730092923.png`
- Measured 22.222222 candidate ss6:
  `work/Font/pcsx2/snaps/SLOP-NA228 [_]/SLOP-NA228 [_]_SLOP-NA228_20260730093456.png`
- Font's task-owned PCSX2 process was stopped during this checkpoint. No user
  or other workstream PCSX2 process was inspected or controlled.

## Commands and results

The last successful standard candidate command was:

```powershell
& .\scripts\injection\test.ps1 `
  -SourceId font_v2_core `
  -Entry localization.font.v2.jutsu_draw_entry `
  -OverlayPlan work\Font\operations\jutsu_names_overlay.json `
  -IsoPath work\Font\inputs\isos\NA2.28-2D8AE8A6.iso `
  -StateSlot 3 `
  -PinePort 28015
```

It linked two fragments and two resident imports, loaded ss3 paused, and
applied one memory range plus one guarded write. The exact authorized inputs
then reached ss5 and ss6. Fresh images were requested only through
`scripts/pcsx2/pine.py screenshot`.

The next compile was blocked before touching PCSX2 by concurrent Project work:

```text
ValueError: Game 'config' has an invalid build postfix: None
```

At the stop boundary, Project's uncommitted `games.json` stored build
configuration beside `builds.entries`, while
`na228_builder/project_paths.py` still iterated the complete `builds` object as
game definitions. Project was sent the exact regression and was actively
finishing that approved migration. Font did not edit Project-owned files.

`git diff --check` passed for the four stashed Font paths before checkpointing.
No permanent candidate test was added because the final runtime behavior is not
yet accepted.

## Remaining work

1. Obtain Project's committed/pushed stable path-loader boundary and confirm the
   standard injection command works again.
2. Restore only stash object
   `a370cbfffdd2a55d8b8353e4fc7802a7578c4f7c`.
3. Relaunch the hidden task-owned worker on port `28015`.
4. Run the standard command from supplied ss3, then the exact authorized
   Cross, Circle sequence to ss5.
5. Capture ss5 through PINE and compare at normalized 640-by-480 resolution.
6. If necessary, tune only Jutsu multiline advance/Y compensation; do not
   broaden the caller or disturb single-line rows.
7. Press the final authorized Cross, capture ss6, and verify every visible name
   stays within the selector.
8. After matching, add the canonical `patches.tsv`/`edits.tsv` Jutsu patch row
   for BTL file `0x9178`, validate, commit, and push only Font-owned changes.
9. Compose and visibly deliver the required NUN5-left/current-right ss5/ss6
   grid, clear its pending state in the next Font-owned commit, then continue
   Priority 4 under Continuous mode.

## Exact first resume action

Re-read live rules and Font/epic policies, refresh Git, and verify Project's
catalog migration is stable. Delete this handoff and commit/push that deletion
before implementation resumes. Then apply stash object
`a370cbfffdd2a55d8b8353e4fc7802a7578c4f7c`, verify exactly the four listed
paths, and rerun the standard injection command from supplied ss3.
