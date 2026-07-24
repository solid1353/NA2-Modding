# String translation resume handoff — 2026-07-24

## Objective and task

- Codex task/chat title: `String translation`
- Live selected task:
  - `[Investigate](work/__sstates/translation/strings)`
  - `Redo the translation from scratch, using existing data as a reference, touching only what is displayed with the help of savestates. Not everything is translated currently (MAX Damage label, etc.).`
- Immediate user request at interruption: reread the savestate-comparison presentation rule and re-report the savestate corpus correctly.
- User then issued `zxc`; stop after preserving this checkpoint.

## Phase, effort, and approval

- Current phase: approved task, post-refactor savestate evidence reporting.
- Recommended effort: High. The remaining translation redo spans 104 matched screens across multiple game sections and requires quote-aware mapping edits, fit/placement validation, and focused runtime verification.
- Approval state:
  - The mapping-schema/refactor work was approved with `qwe` and completed earlier.
  - The user explicitly said translation changes are allowed in this task but instructed not to redo the translations yet.
  - The current savestate report is read-only analysis and presentation, not a translation change.
  - The user stated `qwe for all future pushes`; live `AGENTS.md` independently requires automatic commits and pushes for completed changes.

## Completed

- Re-read the complete live `AGENTS.md`, `TASKS.md`, and `docs/workstreams/string_translation/README.md`.
- Corrected the earlier reporting approach after identifying the live rule:
  - matched savestate screenshots must be shown as readable, section-labeled grids;
  - reference/donor must be on the left;
  - current/target must be on the right;
  - each matched pair must occupy one adjacent row;
  - large sets must be split by section/screen semantics.
- Inventoried the read-only user savestate corpus at `work/__sstates/translation/strings`:
  - 104 NUN5 savestates;
  - 104 clean-NA2 savestates;
  - 1 Current savestate;
  - 26 standalone screenshots.
- Read the 1.99 GiB savestates in place under the large-input exception and copied their embedded screenshots, rather than duplicating the full savestates.
- Preserved provenance for 235 copied screenshots.
- Generated 26 section-labeled comparison grids under the task-owned work directory.
- Confirmed checkpoint 084 visibly pairs NUN5 `MAX` with clean NA2 `最大`.
- Confirmed the live mapping table has no `最大`/`MAX` entry; the existing `Damage` mapping is a different Practice-setting string.
- Identified a donor-side trap: a NUN5 memory-card screenshot displays literal `TestSaveLoadMsgEng5`; it is debug/internal text and must not be imported blindly.
- Confirmed there is only one Current savestate; it is Character Select and is not a valid matched counterpart for the 104 official NUN5/clean-NA2 pairs.

## Retained task-owned artifacts

The task owns `work/String translation/`.

- `work/String translation/README.md`
  - documents why the large savestates were read in place;
  - records retained-input purpose and the required left/right comparison convention.
- `work/String translation/inputs/sstates/provenance.tsv`
  - 235 data rows;
  - records input kind, game, checkpoint, user-library source, byte sizes, copied relative path, and SHA-256.
- `work/String translation/inputs/sstates/paired_screenshots/`
  - 104 NUN5 screenshots;
  - 104 clean-NA2 screenshots;
  - 1 Current screenshot.
- `work/String translation/inputs/sstates/standalone_screenshots/`
  - 12 NUN5 memory-card-format screenshots;
  - 12 clean-NA2 memory-card-format screenshots;
  - 2 common PCSX2 savestate-failure screenshots.
- `work/String translation/artifacts/savestate_report/`
  - 26 PNG grids:
    - `01_load_save_001_004.png`
    - `02_mode_select_005_009.png`
    - `03_mode_save_010_014.png`
    - `04_options_015_019.png`
    - `05_options_020_024.png`
    - `06_collection_025_028.png`
    - `07_collection_029_032.png`
    - `08_collection_033_037.png`
    - `09_collection_038_041.png`
    - `10_shop_042_046.png`
    - `11_shop_047_050.png`
    - `12_practice_051_055.png`
    - `13_practice_056_061.png`
    - `14_opponent_062_066.png`
    - `15_opponent_067_070.png`
    - `16_commands_071_075.png`
    - `17_commands_076_080.png`
    - `18_commands_081_083.png`
    - `19_battle_084_087.png`
    - `20_battle_088_090.png`
    - `21_results_091_095.png`
    - `22_results_096_099.png`
    - `23_startup_100_104.png`
    - `24_memory_card_format_01_04.png`
    - `25_memory_card_format_05_08.png`
    - `26_memory_card_format_09_12.png`
- Total retained task-work size: 123,999,643 bytes across 263 files.

These artifacts have a concrete future use in the pending savestate-driven translation redo and must not be cleaned during restart recovery.

## Tools and commands already used

- PowerShell:
  - read live policy/task files;
  - inventoried savestates and screenshots;
  - checked Git state;
  - measured file counts and sizes;
  - searched the quote-aware TSV evidence without modifying it.
- Bundled Python 3:
  - `zipfile` to read embedded `Screenshot.png` files;
  - `hashlib` and `csv` to generate provenance;
  - Pillow 12.2.0 to render the paired grids.
- A single escalated Python execution was required because the Windows sandbox denied the write inside the task-owned `work/String translation/` directory.

## Git and file state

- HEAD at checkpoint creation: `4d0b01c0a30d8e2249e66aa1b3d02d5dcbed1e20`
- Branch: `master`, tracking `origin/master`.
- The worktree was clean before this handoff was added.
- The only tracked path to commit for the graceful stop is this handoff.
- The task-owned `work/String translation/` artifacts are ignored working data and must remain uncommitted.
- No canonical mapping, engine, profile, task-index, source, ISO, PNACH, or binary file was modified during this report preparation.
- The read-only user savestate library remains untouched.

## Running processes, resources, and wakeups

- No PCSX2 instance was launched by this task.
- No ISO build, Git transaction, promotion, physical input session, or other exclusive project resource is active.
- Existing `python` and `pwsh` processes predate this checkpoint and were not launched or claimed by this reporting step; do not terminate them on this task's behalf.
- No task wakeup or monitoring automation is pending.
- `.agents/notifications.json` is currently muted, so no completion/blocker notification should be sent.

## Remaining work

1. On resume, read this handoff plus live `AGENTS.md`, `TASKS.md`, the String translation workstream policy, Git state, and `work/String translation/`.
2. Validate that the retained grids and provenance still exist and that the user library remains untouched.
3. Delete this handoff, commit, and push that deletion before continuing, as required by the resume rule.
4. Visually inspect representative generated grids, especially:
   - first load/save grid;
   - `19_battle_084_087.png` for `MAX`/`最大`;
   - startup grid;
   - memory-card-format grids.
5. Re-report the corpus using the actual retained PNG grids embedded in the response, grouped by their existing semantic sections. Do not return another unstructured textual file list.
6. Show the single Current Character Select screenshot separately and explicitly state that it is not a matched counterpart.
7. Include the report facts:
   - 209 savestates / 1.99 GiB;
   - 26 standalone screenshots / 20.36 MiB;
   - 104 complete NUN5-versus-clean-NA2 pairs;
   - one unmatched Current state;
   - `MAX` versus `最大` at checkpoint 084;
   - the `TestSaveLoadMsgEng5` donor trap;
   - the evidence limitations below.

## Required user input

- Nothing is required to finish the corrected savestate report.
- Future translation/runtime validation will need Current-build savestates or runtime access at the exact screens being changed, because the present corpus mostly compares official NUN5 with clean Japanese NA2.

## Uncertainties and limitations

- The 104 pairs prove screen visibility and official donor/clean-target correspondence; they do not prove Current-build regression behavior.
- Only one Current state exists and it covers Character Select.
- The report used embedded savestate screenshots; it did not load all 209 savestates in PCSX2.
- The generated grids still need a representative visual QA pass before presentation.

## Exact first action on resume

Read and assimilate this handoff with the live rules and Git/work state, verify drift, then delete and commit/push the handoff before visually checking the retained grids.
