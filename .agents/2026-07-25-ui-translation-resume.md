# UI Translation resume handoff — 2026-07-25

This is a dated, non-authoritative restart checkpoint. Re-read live
`AGENTS.md`, `TASKS.md`, the current Git state, and
`docs/workstreams/ui_translation/README.md` before resuming.

## Task and authorization

- Codex task/chat title: `UI Translation`.
- Exact live `TASKS.md` entry:

  ```text
  ### [UI Translation](docs/workstreams/ui_translation/README.md)
  - [Investigate](work/__sstates/translation/UI)
      * Deal with remaining issues (items, awakenings, etc.).
  ```

- Objective: finish the remaining NUN5-to-NA2 UI texture/placement mismatches,
  using canonical NUN5 donors by default and evidence-backed NA2-specific
  binary patches only when required.
- Current phase: implementation is at a coherent committed boundary; three
  final paired visual checkpoints are awaiting explicit user confirmation.
- Selected effort: `max`.
- Approval state: approved and in progress (`qwe` was given); plan approval
  remains valid on resume unless live drift changes the outcome.
- Stop reason: the scheduled `ui-translation-graceful-stop` heartbeat fired.
  No substantive or atomic operation was in flight.

## Current plan and next action

1. Keep each retained mismatch pair and final candidate until the user
   explicitly confirms that screen is fixed.
2. On confirmation, remove that pair's task-owned input copies, final candidate
   state/screenshot, and rows from `work/UI translation/mismatched_pairs.tsv`
   and `work/UI translation/retained_candidates.tsv`.
3. Commit and push each accepted screen cleanup separately if it changes
   tracked files; task-owned ignored evidence cleanup needs no Git commit by
   itself.
4. Continue the next remaining UI mismatch one at a time, preferring a broad
   shared correction when one proven cause covers multiple screens.

Exact first action on resume:

1. Re-read this handoff and live policy/state.
2. Confirm Git drift, especially Font's concurrent Localization work.
3. If resumption is sound, delete this handoff and commit/push that deletion.
4. Apply any user acceptance received for the three pairs below; otherwise
   wait for that visual decision rather than repeating analysis or tests.

## Awaiting user confirmation

The user was shown a single NUN5-left / Current-NA2-right grid containing:

1. Character Select footer, `Select Color` / `Random`
   - original pair:
     `work/UI translation/inputs/sstates/remaining_02_character_select_color_random/`
   - final state:
     `work/UI translation/artifacts/sstates/character-select-footer-patched.p2s`
     (11,336,181 bytes)
   - final screenshot:
     `work/UI translation/artifacts/screenshots/character-select-footer-final.png`
     (334,052 bytes)
   - implementation commit: `f1609d0`
2. Options, `Cancel`
   - original pair:
     `work/UI translation/inputs/sstates/remaining_07_options_cancel_placement/`
   - final state:
     `work/UI translation/artifacts/sstates/options-cancel-donor.p2s`
     (12,045,865 bytes)
   - final screenshot:
     `work/UI translation/artifacts/screenshots/options-cancel-donor.png`
     (88,275 bytes)
   - implementation commit: `67649e2`
3. Music Options, complete `SELECT button: Return to Defaults` group
   - original pair:
     `work/UI translation/inputs/sstates/remaining_08_music_options_select_placement/`
   - final state:
     `work/UI translation/artifacts/sstates/music-options-select-shared.p2s`
     (12,740,293 bytes)
   - final screenshot:
     `work/UI translation/artifacts/screenshots/music-options-select-shared.png`
     (244,170 bytes)
   - implementation commit: `f99c366`
   - the same patch also applies the homologous X-coordinate correction to the
     Controls compositor; Music supplied the retained runtime pair.

The current mismatch inventory contains only those three rows. Visual
inspection found the requested texture-placement defects corrected. Animated
or overflowing help text is outside this texture-only scope.

## Completed work at the current boundary

- `02624a0` — numeric item-status labels.
- `0c96594` — fixed item-status labels.
- `8516e5b` — battle mash prompts.
- `17e7701` — Victory artwork.
- `f1609d0` — Character Select footer prompts.
- `67649e2` — shared Cancel prompts.
- `f99c366` — shared Options Select legends.
- The user explicitly confirmed awakenings fixed. The task-owned awakening
  duplicates were removed: 78 files / 494,020,717 bytes. The original shared
  savestate library under `work/__sstates/` was untouched.

Current committed Localization checkpoint at `f99c366`:

```text
localization B74E71769372814F11DF5E39FF4DA880EFEBC62E9B4DC1F0985535B99EA9EE0B bypass_check=0
```

Font was already sent the stable `f99c366` handoff. Do not resend routine
acknowledgments.

## Evidence and tests

Latest shared Select correction:

- Canonical patch: `UI-ELF-009`.
- Four exact NUN5 donor instruction copies change paired icon/label X from
  `230.0` to `200.0` in the Controls and Music compositors.
- Package validation: 7 targets, 9 groups, 98 patches, 407 edits.
- Focused exact donor/provenance tests: 2/2 passed.
- Texture suite: 35/35 passed.
- Isolated staged-tree suite: 120 passed, 3 expected skips.
- A rejected common-prompt-table probe did not move the target and was
  discarded; the useful negative result and final function/range mappings were
  promoted into canonical knowledge.

Earlier Options boundary:

- Full repository suite: 167/167 passed.

Canonical findings and implementation paths include:

- `docs/knowledge/localization/function_map.tsv`
- `docs/knowledge/localization/ui/character_select.md`
- `docs/knowledge/localization/ui/options.md`
- `na2_patcher/features/localization/README.md`
- `na2_patcher/features/localization/binary_patcher/patches.tsv`
- `na2_patcher/features/localization/binary_patcher/edits.tsv`
- `na2_patcher/tests/test_texture_patcher.py`

Tools used: Git, PowerShell, Python/unittest, the repository's
`na2_patcher`/worker-build workflow, Ghidra exports already preserved under the
configured analysis tree, and the task-owned PCSX2 clone plus maintained PINE
savestate screenshot extraction.

## Git and concurrent work

State at graceful-stop inspection:

```text
branch: master
HEAD: f99c366525c74c3936691513b7d673f30783e3f3
origin/master: f99c366525c74c3936691513b7d673f30783e3f3
owned staged paths: none
owned unstaged canonical paths: none
```

The following nine unstaged paths belong to concurrent Font work and must be
preserved:

```text
na2_patcher/features/localization/resident_patcher/assets/font_renderer_resident.bin
na2_patcher/features/localization/resident_patcher/edits.tsv
na2_patcher/features/localization/resident_patcher/fragments.tsv
na2_patcher/features/localization/resident_patcher/patches.tsv
na2_patcher/features/localization/resident_patcher/relocations.tsv
na2_patcher/features/localization/resident_patcher/targets.tsv
na2_patcher/profiles/current/features.tsv
na2_patcher/tests/test_resident_patcher.py
scripts/research/localization/generate_font_renderer.py
```

At inspection, Font's working profile row was
`49B06C1165B0B651F6CDA7B0E7F53745090C4262BBFB94E324D7294A3A0C20F5`
with `bypass_check=1`. Do not replace it with the committed UI pin or stage any
Font hunk. Refresh immediately before every Git action.

## Task-owned work and retained artifacts

The existing user-directed task root is `work/UI translation/`. It is retained
as-is for resume; no normal end-of-task cleanup was performed.

Subtree inventory at stop:

| Subtree | Files | Bytes |
|---|---:|---:|
| `artifacts/` | 282 | 2,258,849,250 |
| `build/` | 4 | 7,713,718,272 |
| `inputs/` | 144 | 836,909,400 |
| `logs/` | 246 | 9,000,219 |
| `pcsx2/` | 289 | 469,198,034 |
| `runtime_baselines/` | 19 | 2,083,390,954 |
| `runtime_cases/` | 204 | 653,353,378 |
| `temp/` | 498 | 1,493,270,857 |
| all other named subtrees | retained | inspect before any later cleanup |

The four retained worker ISOs are:

```text
work/UI translation/build/character-select-footer.iso  1,928,429,568 bytes
work/UI translation/build/items-live-test.iso          1,928,429,568 bytes
work/UI translation/build/items-pair.iso               1,928,429,568 bytes
work/UI translation/build/victory-final.iso             1,928,429,568 bytes
```

Do not clean any retained file solely because it looks old. Resume the
screen-by-screen retention policy first, then assess artifacts only when their
concrete future use is resolved.

## Processes, exclusive resources, and automation

- `Get-Process` found no running PCSX2 process at stop.
- No task-owned build, test, PINE, Git, or file-write operation was running.
- No exclusive runtime resource remains held.
- `work/UI translation/pcsx2/` is preserved as the inactive task-owned clone.
- Protected user PCSX2 state was not accessed or changed.
- The `ui-translation-graceful-stop` heartbeat was changed from `ACTIVE` to
  `PAUSED` after firing, so it cannot trigger again.
- Notifications are muted in `.agents/notifications.json`; no notification is
  sent for this stop.

## User decisions and workstream rules to preserve

- Fix issues one subtask at a time, commit and push each finished screen, then
  move to the next.
- Prefer broad changes over selective fixes when one verified shared cause
  exists.
- Keep NUN5 reference on the left and Current NA2 on the right in every paired
  screenshot checkpoint; show the actual images and inspect them closely.
- Retain each mismatch state/pair and tracking entry until the user explicitly
  confirms it fixed, then remove both the evidence and entry.
- UI Translation fixes textures and their placement; font/string overflow is
  outside this workstream.
- Prefer verified NUN5 donor bytes. Record the evidence and reason for any
  NA2-specific replacement bytes.
- Use only the task-owned PCSX2 clone, hidden/muted, and never control the
  protected user PCSX2 or another workstream's process.

## Required user input and uncertainties

- Required input: accept or reject each of the three displayed pairs.
- If a pair is rejected, the user's visual callout defines the next bounded
  correction; do not repeat already-proven analysis or reapply a fix that is
  already present.
- The live worktree may advance while the machine is asleep because Font owns
  concurrent Localization changes. Reconcile their committed handoff before
  touching `features.tsv`.
- The existing task directory spelling is `work/UI translation/`, while the
  current task title is `UI Translation`; preserve the user-established path
  and do not rename it during resume without a new explicit instruction.

Restart/reboot is safe after this handoff is committed and pushed. There is no
remaining live operation or known process hazard.
