# NA2 Translation Package Builder v29

This builder generates one post-composition translation TSV for **Naruto: Narutimate Accel 2**. It never packages patched BIN or ELF payloads. The surrounding NA2 pipeline composes selected packages first, then applies the generated TSV over the composed files.

This archive contains only `translation_package_builder`. Project-level wrapper and ISO-building scripts remain outside the package.

## Builder metadata

- Version: `29`
- Packaged `mappings.tsv` SHA-256: `f9af6c5caa975168a4b1aa609a3d87785c364b4e5c748b4e9ae56b23570413ed`

The README is the canonical home for both values. The builder does not ship one-line `VERSION.txt` or `MAPPINGS_DEFAULT.sha256` files. It reads and validates this metadata directly from `README.md`.

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

Normal `slot` mappings read their English bytes from exact UN5 offsets at build time. The only manual English permitted is in `shorten` rows, where the replacement begins with `[S]` because the official UN5 text cannot fit the original NA2 slot. No translation is relocated into spare space and no text pointer is rewritten.

## Canonical `mappings.tsv`

`mappings.tsv` is the single canonical mapping table. TSV has no worksheet tabs, so `section` is the page/filter key for grouping mappings by screen or mode.

The 12 columns are:

`id`, `enabled`, `section`, `mode`, `target`, `target_offset`, `capacity`, `source_ref`, `transform`, `arguments`, `value`, `reason`

### Stable IDs and enabled state

- `id` is a stable mapping identifier.
- `enabled=1` applies the row.
- `enabled=0` retains the row without applying it.

Enabled flags persist outside the replaceable builder directory at:

`work\translation_builder_state\enabled_state.tsv`

Packaged defaults are distinguished from actual user changes as follows:

1. A user-edited current `mappings.tsv` always wins and refreshes persistent state.
2. An untouched packaged table inherits saved flags by stable `id` only.
3. If no state exists, archived builders under `trash\translation_package_builder_removed_*` are considered only when their own packaged-default hash is available.
4. An archived table that is byte-for-byte identical to its packaged default is skipped because it contains no user edits.
5. Legacy semantic migration is used only for an archived table proven different from its packaged default. An archive without a verifiable default hash is skipped rather than guessed at.
6. Effective flags are written atomically to both `mappings.tsv` and persistent state.

This preserves the v28 repair for the migration defect where the new enabled `M0745` dialog mapping could inherit `enabled=0` from an unchanged, default-disabled v26 relocation fragment.

### Modes

- `slot`: copy exact official UN5 text, optionally through a source-derived transform.
- `shorten`: use the `[S]` replacement in `value`, retaining the exact UN5 source reference for traceability.
- `bytes`: fixed-size structural patch represented as `EXPECTED=>REPLACEMENT` in `value`.
- `unresolved`: retain an investigated but unsafe or unproven mapping without applying it.

There is no `pool` mode. Text stays in its original target slot.

### Source references and transforms

`source_ref` uses `SOURCE@OFFSET`, for example `UN5_TEXTENG@0x29430`.

Supported source-derived transforms:

- `format_arg1`, `format_args`
- `format_prefix_arg2`, `format_suffix_arg2`
- `between_placeholders`, `after_placeholder2`
- `split_br`, `join_br_parts`
- `flatten_br_slice`
- `append_space`
- `empty`

Arguments use compact key/value syntax, for example:

- `arg1=UN5_TEXTENG@0x708`
- `part=1`
- `parts=2,3;join=<br>`
- `start=13;end=83`

`flatten_br_slice` replaces each official UN5 `<br>` with one space and selects a verified character range. It is used to distribute one official loading sentence across NA2's three original fixed slots without embedding manual prose.

## Output

Each run creates:

`translation_package_builder\work\runs\<UTC+3 run id>\`

containing:

- `NA2_APPLY__TRANSLATION__<run id>.tsv`
- `build_summary.json`

The generated translation TSV contains exactly six columns:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

All paths written into generated artifacts are relative. In particular, `build_summary.json` stores the translation TSV as its filename relative to the summary's own run directory, never as a machine-specific absolute path. ISO target paths inside the TSV remain ISO-root-relative.

`build_summary.json` contains only general and aggregate run information:

- builder version, run ID, timezone, and selected targets;
- relative translation TSV reference;
- patch and mapping totals;
- active mapping coverage grouped by mode and section;
- source and translated-file hashes.

Disabled and unresolved rows remain solely in `mappings.tsv`.

## Safety behavior

Known clean-source SHA-1 values are checked by default. `-NoStrictHash` disables those checks only for deliberate experiments.

The builder rejects malformed flags, duplicate IDs, invalid offsets, invalid source references, malformed transforms, overlapping active mappings, unexpected structural bytes, text exceeding its declared slot, and invalid named-color conversion. Enabled bad mappings fail the build instead of becoming silent runtime skips.

### Exact slot boundaries

A text mapping's `capacity` must end inside zero padding belonging to that string. The builder now rejects a declared slot if any nonzero byte appears after the original NUL terminator within that capacity. This prevents a text write from zero-filling adjacent pointer tables or other structural data.

This check directly guards against both v28 regressions fixed in v29:

- `M0776` crossed from the `Credits` string into the Collection movie-pointer table at `SLPS + 0x2FFD1C`.
- `M0792` crossed from the difficulty-reset result string into the Options navigation table at `SLPS + 0x4B2BF0`.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

## Markup handling

The original NA2 target is authoritative for renderer-specific color forms:

- UN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- UN5 `<BLACK>` remains `<BLACK>` or becomes `<color000000>` according to the verified target form.
- `<RED>` is retained only where the target supports it.
- Other shared color, icon, line-break, and control tags are preserved.

## Version 29 changes

### Options help-line regression repair

The existing exact UN5 mappings were already present:

- `Set the Com strength for when in the Free Battle and Practice.`
- `Assign button controls.`

They appeared blank because `M0792` declared a 72-byte slot at `SLPS + 0x4B2BB0` and zero-filled six bytes of the Options navigation pointer table beginning at `SLPS + 0x4B2BF0`.

v29 reduces `M0792` to the actual 64-byte string slot. The pointer table remains unchanged, allowing the existing Difficulty Settings and Control Settings help mappings to be reached again.

### Missing first Theater entry repair

Two separate v28 defects affected the first movie title:

- `M0776` declared a 32-byte `Credits` slot and zero-filled the first movie-title pointer at `SLPS + 0x2FFD1C`.
- `M0770` wrote `Reunion Time I` at `SLPS + 0x2FFB9E`, two bytes before the address actually stored in the movie-title pointer table.

v29 limits `M0776` to 28 bytes, preserving the pointer table, and moves `M0770` to the real pointer target at `SLPS + 0x2FFBA0` with a 64-byte capacity. The original two bytes at `0x2FFB9E-0x2FFB9F` are left untouched. The official UN5 title remains exactly `Reunion Time I`.

### Remaining Naruto Command Chart attacks

Added exact UN5 mappings for the two visible Japanese entries missed by v28:

- `特攻蹴撃` -> `Charging Kick` from `UN5_TEXTENG + 0x51F0`, targeting `SLPS + 0x30CAE0`.
- `分身跳爆打` -> `Clone Jumping Explosion Hit` from `UN5_TEXTENG + 0xA800`, targeting `SLPS + 0x3D9E20`.

The second official UN5 string contains its original trailing space before the NUL terminator; the builder copies it exactly.

### Relative generated paths

`build_summary.json` now writes the translation TSV as a relative filename. Console output also reports the generated TSV relative to the builder's work directory instead of printing an absolute host path.

### Carried-forward baseline

v29 retains the accepted v27/v28 behavior: stable mapping IDs, original-slot text only, traceable `[S]` shortening, no active relocation pools or pointer redirects, the `M0745` migration repair, exact ASCII `ON`/`OFF`, corrected `Yes`, Character Select matchup labels, Music/Options result messages, save-list numbers and `Empty`, and the expanded save/memory-card flow.

The packaged v29 table contains 856 mappings: 846 enabled and 10 disabled. Active mappings comprise 750 `slot` rows and 22 `shorten` rows. Seventy-four enabled `unresolved` entries remain documented but unapplied; all four structural `bytes` rows remain disabled.

## Rolling runtime issue log

This log persists unresolved visual/runtime findings across builder versions. Entries implemented in the current builder remain in the verification section until confirmed in-game.

### Implemented in v29, runtime verification required

- **Options, Difficulty Settings:** bottom blue help line should again show `Set the Com strength for when in the Free Battle and Practice.`
- **Options, Control Settings:** bottom blue help line should again show `Assign button controls.`
- **Collection Movie list:** first entry should again show `Reunion Time I` in the correct list position.
- **Naruto Command Chart:** `特攻蹴撃` should show `Charging Kick`.
- **Naruto Command Chart:** `分身跳爆打` should show `Clone Jumping Explosion Hit`.

### Open

- **Options main-screen graphical labels:** the `Options` logo, difficulty/value, controls, screen, audio, restore, confirm, and back labels remain Japanese in supplied screenshots. They appear to use graphical/CCS resources outside the current text targets and remain untouched pending extracted NA2 and UN5 assets.
- **Collection Movie screen chrome:** the `Collection` title, `Movie` category heading, and play/back prompts remain Japanese and appear to use graphical/CCS resources outside the current text targets.
- **Collection movie-title fit:** exact UN5 titles are present, but several extend beyond the visible right edge. They remain unshortened until a requested shortening or verified UN5 width/scale behavior is applied.
- **Command Chart chrome:** any remaining Japanese heading or back prompt that is graphical rather than string-backed remains outside current scope pending resource extraction.
- **Dynamic save date/time numerals:** retained as unresolved mapping `M0833`; the digits are generated by executable code and still require a verified renderer/code mapping.

PCSX2 application chrome, toolbar text, pause indicators, graphical controller prompts, and emulator toasts are not game translation issues and are not logged here.

## v29 test checklist

1. Build from a clean installed v29 directory and confirm the summary reports builder version 29.
2. Confirm `build_summary.json` contains only a relative TSV filename and no absolute host paths.
3. Enabled migration: preserve external state and verify `M0745=1`; new IDs `M0855` and `M0856` should take their packaged enabled defaults.
4. Options: verify both Difficulty Settings and Control Settings bottom help lines are visible and exact.
5. Collection: verify the first movie row is `Reunion Time I`, all later entries retain their positions, and `Credits` remains visible.
6. Naruto Command Chart: verify `Charging Kick` and `Clone Jumping Explosion Hit` replace the two remaining Japanese attacks.
7. Save/load, Options, Collection, and Command Chart: enter and leave repeatedly and verify no blank text, pointer-table corruption, overlap, white screen, or crash.
8. Generated TSV validation: six columns, fixed-size patches only, and successful composition with the current Font package.

## Integration expectations

- Install/extract this builder as `translation_package_builder` under the NA2 project root.
- Do not copy builder `work` output into the archive.
- Do not add patched `BTL.BIN`, `ETC.BIN`, or `SLPS_258.37` payloads to builder releases.
- The surrounding `na2` workflow owns package composition and ISO application.
- Translation is applied after selected packages so it can safely target their composed files.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Default target selection is `BTL,ETC,SLPS`. `ELF`, `SLES`, and `EXE` alias `SLPS`; `ALL` selects every target.
