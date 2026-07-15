# NA2 Translation Package Builder v27

This builder generates one post-composition translation TSV for Naruto: Narutimate Accel 2. It never packages patched BIN or ELF payloads. The surrounding NA2 pipeline composes selected packages first, then applies the generated TSV over the composed files.

This archive contains only `translation_package_builder`. Project-level wrapper and ISO-building scripts remain outside the package.

## Source and target scope

Clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

Official UN5 sources:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `PRG/TEXTENG.BIN`
- `SLES_556.05`

Normal `slot` mappings read their English bytes from exact UN5 offsets at build time. The only manual English permitted is in `shorten` rows, where the replacement begins with `[S]` and exists because the official UN5 text cannot fit the original NA2 slot safely. No translation is relocated into spare space and no text pointer is rewritten.

## Compact `mappings.tsv`

`mappings.tsv` remains the single canonical mapping table. TSV has no worksheet tabs, so the `section` column is the page/filter key for grouping mappings by screen or mode. The v27 schema removes the relocation-only columns and combines sparse fields, reducing the table from 19 columns to 12:

`id`, `enabled`, `section`, `mode`, `target`, `target_offset`, `capacity`, `source_ref`, `transform`, `arguments`, `value`, `reason`

### Stable IDs and enabled state

- `id` is a stable mapping identifier.
- `enabled=1` applies the row.
- `enabled=0` keeps the row in `mappings.tsv` but does not apply it.

Enabled flags persist outside the replaceable builder directory at:

`work\translation_builder_state\enabled_state.tsv`

The builder distinguishes an untouched packaged `mappings.tsv` from a user-edited one using `MAPPINGS_DEFAULT.sha256`:

1. A user-edited current table always wins and updates persistent state.
2. After the builder is replaced, the packaged defaults inherit matching saved flags by stable `id`.
3. On first migration, the builder can recover flags from the newest `trash\translation_package_builder_removed_*\mappings.tsv`, including explicit user-disabled rows from the old v26 schema through semantic matching.
4. The effective flags are written back atomically to `mappings.tsv`.

This persistence is implemented inside the builder and does not depend on Codex wrapper behavior.

### Modes

- `slot`: copy exact official UN5 text, optionally using a source-derived transform.
- `shorten`: use the `[S]` replacement in `value` while retaining the exact UN5 source reference for traceability.
- `bytes`: fixed-size structural patch represented as `EXPECTED=>REPLACEMENT` in `value`.
- `unresolved`: retain a investigated but unsafe/unproven mapping in the canonical table without applying it.

v27 has no `pool` mode. Existing v25/v26 relocations were returned to their original targets. Text that does not fit is explicitly shortened at the original slot instead of being moved elsewhere.

### Source references and transforms

`source_ref` uses `SOURCE@OFFSET`, for example `UN5_TEXTENG@0x29430`.

Supported source-derived transforms include:

- `format_arg1`, `format_args`
- `format_prefix_arg2`, `format_suffix_arg2`
- `between_placeholders`, `after_placeholder2`
- `split_br`, `join_br_parts`
- `append_space`
- `empty`

Arguments use compact key/value syntax, for example:

- `arg1=UN5_TEXTENG@0x708`
- `part=1`
- `parts=2,3;join=<br>`

Transforms select or assemble bytes from official UN5 strings. They do not contain translated prose.

## Output

Each run creates:

`translation_package_builder\work\runs\<UTC+3 run id>\`

containing:

- `NA2_APPLY__TRANSLATION__<run id>.tsv`
- `build_summary.json`

The generated translation TSV contains exactly six columns:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

`build_summary.json` now contains only general and aggregate run information:

- builder version, run ID, timezone, selected targets;
- patch and mapping totals;
- active mapping coverage grouped by mode and section;
- source and translated-file hashes.

Individual disabled and unresolved rows are not copied into the summary. Their sole authoritative location is `mappings.tsv`.

## Safety behavior

Known clean-source SHA-1 values are checked by default. `-NoStrictHash` disables those checks only for deliberate experiments.

The builder rejects malformed flags, duplicate IDs, invalid offsets, invalid source references, malformed transforms, overlapping active mappings, unexpected structural bytes, text that exceeds its declared slot, and invalid named-color conversion. Enabled bad mappings fail the build instead of silently disappearing into a runtime-skips list.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

## Markup handling

NA2 and UN5 share generic inline markup, but named color aliases can differ between renderers. The original NA2 target remains the authority:

- UN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- UN5 `<BLACK>` remains `<BLACK>` or becomes `<color000000>` according to the verified target form.
- `<RED>` is retained only where the target supports it.
- Other shared color, icon, line-break, and control tags are preserved.

## Version 27 changes

### Revalidated corrections

- `ON` and `OFF` were rechecked at the binary level. NA2 originally stores CP932 katakana at the four affected targets; v26/v27 write exact ASCII `ON` and `OFF` from UN5. Their remaining visual letter spacing is renderer/font behavior, not fullwidth SJIS replacement data.
- Fixed the remaining Japanese `Yes` at `SLPS_258.37 + 0x504670`.
- Fixed blank `Reunion Time I` by replacing the complete prefixed NA2 slot from `0x2FFB9E` rather than leaving the two-byte control prefix in front of ASCII text.
- Preserved the structural trailing space after `Play Time`.
- Changed the Command Chart property label from `Charge Chakra` to exact UN5 `Charge`.

### Character Select and Options

- Added exact `1P vs. 2P`, `1P vs. COM`, `COM vs. 2P`, and `COM vs. COM`, restoring the missing period and removing fullwidth SJIS labels.
- Added `Back to Game Mode Screen`.
- Added Music Settings volume, output-mode, and reset-result text.
- Added the Options difficulty-reset result.

### Save and memory-card UI

- Replaced the three loading-list ruby glyphs with exact UN5 `1`, `2`, and `3`.
- Replaced the unused-slot ruby string with exact UN5 `Empty`.
- Added save completion, create-new-data, overwrite warning/prompt, return-to-title, and no-loadable-data strings.
- Added saving progress using the original NA2 fragments; fragments that cannot hold official UN5 text are visibly `[S]` shortened.
- Added the full unformatted-card flow while preserving NA2's separate notification and confirmation steps.
- Added formatting progress/completion and save-area creation progress/completion.
- Added missing-card, missing-game-data, and create-game-data states.
- Long save/memory-card text remains in original slots. No spare-space relocation or pointer rewrite is used.

The save date and elapsed-time numerals are generated by executable code rather than stored in the translated string slots. A verified ASCII-renderer/code mapping was not proven safely in v27, so that single code-level issue remains an `unresolved` row in `mappings.tsv`. Static slot numbers and `Empty` are translated now.

### Removal of relocation behavior

- Removed all active text pools and pointer rewrites.
- Disabled the four v26 MIPS redirects that depended on relocated dialog fragments.
- Rebuilt the Free Battle/Practice dialog fragments in their original slots.
- Converted former long relocations into exact original-slot mappings where they fit.
- Converted the remaining oversized entries into traceable `[S]` mappings.

### Mapping and summary maintenance

- Added stable IDs and persistent enabled-state handling.
- Replaced the sparse v26 table with the compact 12-column schema.
- Added `section` grouping for practical filtering instead of pretending a TSV can contain worksheet tabs, because file formats remain stubbornly literal.
- Removed individual disabled, unresolved, and runtime-skip records from `build_summary.json`.

## v27 test checklist

1. Character Select: all four matchup labels use ASCII and include `vs.`; `Back to Game Mode Screen` is English; confirmation `Yes` is English.
2. Command Chart: `Charge` appears instead of `Charge Chakra`; `[S]` entries remain readable and do not corrupt adjacent strings.
3. Practice settings: inspect all four ON/OFF copies. The output bytes are ASCII; note renderer spacing separately from translation data.
4. Collection: `Reunion Time I` is visible; long shortened title remains in its original slot; quit confirmation uses English `Yes`.
5. Music/Options: verify the three Music Settings messages and difficulty-reset result.
6. Save list: slots show `1`, `2`, `3`, and `Empty`; `Play Time` has a separator before the elapsed time.
7. Normal save/load: overwrite, saving, save completion, create data, missing card, no loadable data, incompatible-data, and return-to-title states.
8. Unformatted card: notification, format prompt, formatting, completion, missing save area, creation prompt, creation, and completion in NA2's actual sequence.
9. Regression: enter and leave affected screens repeatedly; verify no blank text, pointer corruption, white screen, or crash.
10. Enabled persistence: disable one harmless mapping, build once, replace the builder directory with a clean v27 copy, build again, and verify the same ID remains disabled.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Default target selection is `BTL,ETC,SLPS`. `ELF`, `SLES`, and `EXE` alias `SLPS`; `ALL` selects all targets.
