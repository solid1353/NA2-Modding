# Menu Input Runtime Knowledge

This record preserves runtime behavior that was previously available only in
dated binary-patcher logs. The canonical per-screen results are in
[`runtime_tests.tsv`](runtime_tests.tsv).

## Save/load handler family

All four tests used runtime-proven `regional_input_selectable_modal`
(evidence `ELF-M008`) as the baseline. It is the generic selectable-list/modal
decoder already confirmed in Collection, Shop, Free Battle, Practice, and the
Main Menu leave dialog.

The candidate family is:

- `regional_input_save_load_parent` (evidence `ELF-M001`): save/load and
  memory-card parent controller; six input-mask edits.
- `regional_input_save_load_confirmation` (evidence `ELF-M002`): save/load
  confirmation child handler; two input-mask edits.
- `regional_input_save_load_acknowledgment` (evidence `ELF-M003`): save/load
  acknowledgment child handler; one input-mask edit.

Each candidate was tested independently and produced no changes in the 13-screen title/load/save matrix. The three candidates together changed these screens correctly:

- title-screen load menu;
- Main Menu confirm-save prompt;
- Main Menu save menu;
- save menu shown while leaving the Main Menu.

The combined build did not change title-menu input, confirm-load, overwrite
prompts, or accept-only completion prompts.
`regional_input_selectable_modal` continued to handle the Main Menu leave
confirmation correctly in every test.

The durable conclusion is an interaction result, not proof that every
candidate is individually necessary. Do not enable
`regional_input_save_load_parent`,
`regional_input_save_load_confirmation`, or
`regional_input_save_load_acknowledgment` alone or classify one as
runtime-proven from these tests. A future minimization test should examine
candidate pairs before promoting the family.

## Save/load slot-row visibility

The current user-supplied `ss1` for boot CRC `D5AA8B06` shows three occupied
records in the Save modal. Static analysis identifies boot-ELF
`FUN_001e6370` as the shared three-record Save/Load row renderer. Its primary
draw loop ends at runtime address `0x001E6970` (ELF file offset `0xE6A70`) with
clean instruction `slti v1,s2,3`, encoded as `03 00 43 2A`.

The earlier occupancy scan still examines all three records, while
`FUN_001e69b0` separately owns selection and navigation. Consequently changing
only the draw-loop bound to `slti v1,s2,1` limits visible rows without deleting
or rewriting save data and without changing the native three-slot selection
logic. `ELF-Q010` implements that guarded edit. Confidence is **high** for the
static ownership and scope; the visible one-row result remains pending runtime
confirmation.

The same handler tests Down at runtime `0x001E6AA0` (ELF file `0xE6BA0`) and
Up at runtime `0x001E6AE0` (ELF file `0xE6BE0`). Each successful branch changes
the selected-slot field at object offset `0x10`, clears its transition field at
`0x18`, and plays sound `0x35`. Replacing only the two input-mask results with
zero makes both branches unreachable while leaving confirm, cancel, occupancy,
and save execution unchanged. Confidence is **high** for the static control
flow; absence of movement and sound remains pending runtime confirmation.

The one-record layout keeps the lower instruction panel but replaces the
three-row upper frame. `FUN_001e57b0` constructs that frame at runtime
`0x001E588C` through `0x001E58A4` (ELF files `0xE598C` through `0xE59A4`). Its
X/Y/width/height change from `58/10/400/224` to `146/90/224/96`, making it a
compact centered panel visibly detached above the unchanged lower panel.

In `FUN_001e6370`, the shared date/play-time X constant at runtime `0x001E6468`
(ELF file `0xE6568`) changes from `108.0` to `45.0`, and the row base Y at
runtime `0x001E6484` (ELF file `0xE6584`) changes from `14.0` to `20.0`. The
slot-number X at runtime `0x001E64B8` (ELF file `0xE65B8`) remains outside the
viewport, suppressing both its selected and ordinary draw passes without
changing shared localization draw hooks. The separator predicate at runtime
`0x001E6788` (ELF file `0xE6888`) remains the always-false `s2 < 0`. Confidence
is **high** for the constructor and renderer ownership and exact guarded
constants. The independent `MDL_xkun1` slot cursor is no longer meaningful
after navigation is disabled; its `FUN_001bb790` draw call at runtime
`0x001E6CA4` (ELF file `0xE6DA4`) is replaced with a NOP while its existing
state updates and lifetime remain intact. The raised compact visual result
remains pending user review.

## No-save-data confirmation exit

The save-mode "No Narutimate Accel v2.28 data found" confirmation is memory-card
status `0x0C`, not status `0x2C`. Its No branch resets the save controller to
the initial save prompt after runtime `0x001E4588` (ELF file `0xE4688`).
`ELF-Q010-22` replaces that reset with the controller's existing nonzero exit,
so the enclosing menu resumes instead of reopening the prompt. The user
confirmed the corrected runtime behavior on 2026-08-05. Two earlier candidates
at file `0xE47A4` were ineffective because that address belongs to the unrelated
status-`0x2C` branch; neither candidate was retained.

## Static-analysis index

The module already retains the reusable subroutine and regional comparison data:

- [`function_map.tsv`](function_map.tsv) maps NA2/NUN5 functions, file offsets,
  input masks, scope, and evidence.
- `features.localization` in `@builder/catalog/catalog.modcat` records the
  selectable regional-input nodes; `@builder/catalog/edits.json` records
  the exact
  guarded byte edits they reference.
- This document and the linked evidence tables record runtime classification
  and review conclusions.
- [`binary_evidence.tsv`](binary_evidence.tsv) records import and validation
  provenance.
- [`runtime_tests.tsv`](runtime_tests.tsv) records the complete four-test
  runtime matrix.

The catalog and edit store remain the executable definition; the three evidence
tables beside this document are canonical research evidence. This document is
the interpretation and navigation layer, not a second patch definition.

## Provenance

The matrices were observed on 2026-07-16 local time in four test builds
represented by the former `@logs/raw_binary_patcher/save_load_*` run
directories. Their UTC build timestamps and exact candidate sets are retained
in [`runtime_tests.tsv`](runtime_tests.tsv).
