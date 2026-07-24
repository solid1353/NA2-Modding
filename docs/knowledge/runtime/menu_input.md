# Menu Input Runtime Knowledge

This record preserves runtime behavior that was previously available only in dated binary-patcher logs. The canonical per-screen results are in `../localization/runtime_tests.tsv`.

## Save/load handler family

All four tests used runtime-proven `ELF-M008` as the baseline. `ELF-M008` is the generic selectable-list/modal decoder already confirmed in Collection, Shop, Free Battle, Practice, and the Main Menu leave dialog.

The candidate family is:

- `ELF-M001`: save/load and memory-card parent controller; six input-mask edits.
- `ELF-M002`: save/load confirmation child handler; two input-mask edits.
- `ELF-M003`: save/load acknowledgment child handler; one input-mask edit.

Each candidate was tested independently and produced no changes in the 13-screen title/load/save matrix. The three candidates together changed these screens correctly:

- title-screen load menu;
- Main Menu confirm-save prompt;
- Main Menu save menu;
- save menu shown while leaving the Main Menu.

The combined build did not change title-menu input, confirm-load, overwrite prompts, or accept-only completion prompts. `ELF-M008` continued to handle the Main Menu leave confirmation correctly in every test.

The durable conclusion is an interaction result, not proof that every candidate is individually necessary. Do not enable `ELF-M001`, `ELF-M002`, or `ELF-M003` alone or classify one as runtime-proven from these tests. A future minimization test should examine candidate pairs before promoting the family.

## Static-analysis index

The module already retains the reusable subroutine and regional comparison data:

- `../localization/function_map.tsv` maps NA2/NUN5 functions, file offsets, input masks, scope, and evidence.
- `patches.tsv` records runtime classification and review conclusions.
- `edits.tsv` records exact guarded byte edits.
- `../localization/binary_evidence.tsv` records import and validation provenance.
- `../localization/runtime_tests.tsv` records the complete four-test runtime matrix.

The patch and edit tables remain executable module data; the three evidence tables under `docs/knowledge/localization/` are canonical research evidence. This document is the interpretation and navigation layer, not a second patch definition.

## Provenance

The matrices were observed on 2026-07-16 local time in four test builds represented by the former `@logs/raw_binary_patcher/save_load_*` run directories. Their UTC build timestamps and exact candidate sets are retained in `../localization/runtime_tests.tsv`.
