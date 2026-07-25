# Font graceful-stop handoff — 2026-07-25

## Task identity and authorization

- Codex task/chat title: `Font`.
- Exact selected task wording from `TASKS.md`: `Implement proper autofit/positions everywhere.`
- Objective: reproduce NUN5/UN5 text measurement, fitting, wrapping, and positioning across NA2 caller families while preserving the accepted near-pixel-identical font.
- Current phase: Practice command-explanation caller family, shared icon-rendering diagnosis.
- Plan approval: approved and still valid (`qwe` standing in this task).
- Current/selected effort: max.
- Recommended effort on resume: max, because the remaining defect requires cross-game renderer disassembly plus guarded runtime comparison.
- Workstream policy: prefer broad renderer-logic ports; solve one caller family at a time; commit and push each completed caller family before starting another.

## Completed before this stop

1. Refreshed the stable Localization boundary and preserved concurrent UI Translation commits.
2. Characterized the NUN5 Practice command-explanation caller and its shared boxed wrapper.
3. Added an incomplete, uncommitted resident implementation for the Practice family:
   - `localization.font.practice_append`
   - `localization.font.practice_measure`
   - `localization.font.practice_explanation`
   - `localization.font.practice_tokens`
   - resident target `na2_btl`
   - test patch `font_practice_explanation`
   - guarded BTL hook at file offset `0x1C4BA0` / runtime `0x00878AA0`
4. Reproduced the NUN5 13-entry Practice token table exactly:
   `<iconUP>`, `<iconDOWN>`, `<iconRIGHT>`, `<iconLEFT>`,
   `<iconCIRCLE>`, `<iconTRIANGLE>`, `<iconSQUARE>`, `<iconCROSS>`,
   `<iconETC0>`, `<iconL1>`, `<iconR1>`, `<iconL2>`, `<iconR2>`.
5. Reproduced NUN5 token-spacing semantics and tag-aware measurement:
   direction icons advance 32 units, face/`ETC0` icons 24, shoulder icons
   30, and ASCII uses the canonical NUN5-derived table.
6. Reproduced the Practice explanation box and vertical block:
   inner X `39.2`, width `364`, height `48`, Y offset `21.2`,
   glyph height `28`, line advance `14`, centered one- and two-line blocks.
7. Generated the resident asset and passed the focused resident tests 2/2.
8. Built the task-owned worker ISO and prepared/captured matched savestate
   regression inputs for slots 2–7.

## Runtime result and unresolved defect

- Wrapping, X origin, one-line vertical placement, and two-line vertical
  centering match NUN5 across the six Practice states.
- Face and shoulder markup icons render.
- Direction-pad tags and `ETC0`/plus tags are missing from Current NA2 in
  slots 5–7.
- Static comparison established that NA2 parser `FUN_00184e60` already
  recognizes `UP`, `DOWN`, `LEFT`, `RIGHT`, and `ETC0`; do not repeat parser
  name-recognition work.
- The next trace is downstream:
  - NA2 `FUN_00186a80` delegates icon size to context callback `+0x7C` using
    parsed icon ID `uGpffff804c`.
  - Inspect the callback installation/implementation and the icon branch in
    NA2 `FUN_00188140`, then compare the NUN5 counterparts around
    `FUN_00187d40` and `FUN_00189640`.
- Likely fault domain: icon ID metric/record lookup or draw dispatch for IDs
  `0xB..0xE` and `0x11`, not tag parsing.
- Prefer a shared NUN5-equivalent icon-renderer correction if evidence shows it
  is safe. Only fall back to caller-local sprite rendering after proving the
  shared route cannot represent these icons correctly.

## Exact first action on resume

1. Re-read live `AGENTS.md`, `TASKS.md`,
   `docs/workstreams/font/README.md`, and this handoff.
2. Refresh Git and validate that the Font hunks listed below remain
   uncommitted and non-overlapping.
3. Delete this assimilated handoff, commit and push only that deletion, as
   required by the graceful-resume rule.
4. Continue at the downstream icon lookup/draw trace:
   `FUN_00186a80` callback `+0x7C` and the icon branch of
   `FUN_00188140`, compared with NUN5.

## Remaining plan

1. Identify and correct the shared direction/`ETC0` icon rendering path.
2. Regenerate the resident asset and rerun focused tests.
3. Recompute the development Localization hash with `bypass_check=1`.
4. Rebuild `work/Font/build/font-test.iso`.
5. Reprepare and recapture Practice slots 2–7.
6. Inspect both NUN5-left / Current-right comparison sheets.
7. If the complete caller family passes:
   - mark the patch runtime-proven;
   - document the exact callers, formula, token table, widths, runtime result,
     and useful negative result in
     `docs/knowledge/localization/font/README.md`;
   - recompute the exact Localization pin with `bypass_check=0`;
   - run generator verification, focused tests, and the full suite;
   - commit `[Font] Port Practice explanation wrapping`;
   - push before beginning the next caller family.

## Git state at stop

- HEAD: `68973fd` (`[UI Translation] Checkpoint graceful stop`).
- Branch: `master`, synchronized with `origin/master`.
- Staged paths: none.
- Font-owned unstaged paths:
  - `na2_patcher/features/localization/resident_patcher/assets/font_renderer_resident.bin`
  - `na2_patcher/features/localization/resident_patcher/edits.tsv`
  - `na2_patcher/features/localization/resident_patcher/fragments.tsv`
  - `na2_patcher/features/localization/resident_patcher/patches.tsv`
  - `na2_patcher/features/localization/resident_patcher/relocations.tsv`
  - `na2_patcher/features/localization/resident_patcher/targets.tsv`
  - `na2_patcher/profiles/current/features.tsv`
  - `na2_patcher/tests/test_resident_patcher.py`
  - `scripts/research/localization/generate_font_renderer.py`
- Current development profile row before the stop:
  `localization	D32250E91DA1A46D91BC3C593BC4BE09D1E3C51C9292CE968F0CBA8A14FE915B	1`
- Do not commit these incomplete implementation hunks merely because of this
  stop.

## Generated asset and validation state

- Resident asset size: 3,115 bytes.
- Resident asset SHA-256:
  `7AB264E6CCD5877E26D68537A260075A6C0791C2F889B186615D45C2C28AF81D`.
- `fragments.tsv` SHA-256:
  `065EF2986ACEF099AB34B87B0885BC2445E7F0984BBCF7077EFB18053A08954B`.
- `relocations.tsv` SHA-256:
  `D4F1C399ADDB1A3A00728FA192742A230467BD22989214E9DC5059E3033BA85E`.
- Focused resident tests: 2/2 passed after the latest generator output.
- Worker build record:
  `work/Font/logs/builds/20260725_142952_571_pid32044/`.
- Worker build PRG/228 size/SHA:
  `4720` /
  `5849F126A848B2EB16A6F19E1D53D9FB8842F677CF9F79A98C07A97E0F8DD003`.
- Worker BTL SHA:
  `A490EAF3453B31E3B6A8C7B72F3214255AD1A0BA138E8D3A1E1EE8A5DB759212`.
- Worker boot identity: `SLOP-NA228`, CRC `D61F47C5`.

## Retained task-owned artifacts

- Workstream root: `work/Font/`.
- Worker ISO: `work/Font/build/font-test.iso`.
- Build record:
  `work/Font/logs/builds/20260725_142952_571_pid32044/`.
- Practice preparation/capture scripts:
  - `work/Font/analysis/autofit_everywhere/prepare_practice_explanation_v1.py`
  - `work/Font/analysis/autofit_everywhere/capture_practice_regression.ps1`
  - `work/Font/analysis/autofit_everywhere/make_practice_comparisons.py`
- Practice regression root:
  `work/Font/artifacts/autofit_everywhere/practice_explanation_v1/`.
- Prepared metadata:
  `prepared-02.json` through `prepared-07.json`, plus `prepared.json`.
- Prepared states:
  `states/current-02.p2s` through `states/current-07.p2s`, plus
  `states/current.p2s`.
- Matched screenshots:
  `screenshots/nun5-02.png` through `nun5-07.png`,
  `screenshots/current-02.png` through `current-07.png`, and retained source
  images `source-02.png` through `source-07.png`.
- Paired comparison sheets:
  `screenshots/comparison-02-04.png` and
  `screenshots/comparison-05-07.png`.
- The broader pre-existing `work/Font/analysis/`,
  `work/Font/artifacts/`, `work/Font/inputs/`, and `work/Font/temp/` trees
  remain untouched; they contain earlier workstream evidence and are not part
  of graceful-stop cleanup.

## Files read for the current trace

- `AGENTS.md`
- `TASKS.md`
- `docs/workstreams/font/README.md`
- `docs/workstreams/font/plan.md`
- `docs/knowledge/localization/font/README.md`
- `project-paths.json`
- `@analysis/disassembly/NA2/exports/SLPS_258.37/SLPS_258.37.c`
- `@analysis/disassembly/NUN5/exports/SLES_556.05/SLES_556.05.c`

## Processes, resources, and user input

- No Font PCSX2 process is running.
- No build, promotion, Git, or atomic file operation is running.
- No exclusive shared resource is held.
- The task-owned PCSX2 clone and all captured artifacts are retained under
  `work/Font/`.
- Required user input: none.
- Restart or machine reboot is safe after this handoff is committed and pushed.
