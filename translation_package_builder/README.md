# NA2 Translation Package Builder v28

This builder generates one post-composition translation TSV for **Naruto: Narutimate Accel 2**. It never packages patched BIN or ELF payloads. The surrounding NA2 pipeline composes selected packages first, then applies the generated TSV over the composed files.

This archive contains only `translation_package_builder`. Project-level wrapper and ISO-building scripts remain outside the package.

## Builder metadata

- Version: `28`
- Packaged `mappings.tsv` SHA-256: `318c8d866cdda2ff32e8e9171d38e966212d1f26c29444253b63b40bfa635607`

The README is the canonical home for both values. v28 no longer ships one-line `VERSION.txt` or `MAPPINGS_DEFAULT.sha256` files. The builder reads and validates this metadata directly from `README.md`.

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

Normal `slot` mappings read their English bytes from exact UN5 offsets at build time. The only manual English permitted is in `shorten` rows, where the replacement begins with `[S]` because the official UN5 text cannot fit the original NA2 slot safely. No translation is relocated into spare space and no text pointer is rewritten.

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

v28 distinguishes packaged defaults from actual user changes as follows:

1. A user-edited current `mappings.tsv` always wins and refreshes persistent state.
2. An untouched packaged table inherits saved flags by stable `id` only.
3. If no state exists, archived builders under `trash\translation_package_builder_removed_*` are considered only when their own packaged-default hash is available.
4. An archived table that is byte-for-byte identical to its packaged default is skipped because it contains no user edits.
5. Legacy semantic migration is used only for an archived table proven different from its packaged default. An archive without a verifiable default hash is skipped rather than guessed at.
6. Effective flags are written atomically to both `mappings.tsv` and persistent state.

This fixes the v27 migration defect where the new enabled `M0745` dialog mapping could inherit `enabled=0` from an unchanged, default-disabled v26 relocation fragment. A byte-identical v26 default now has no authority over redesigned v27/v28 mappings.

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

`flatten_br_slice` replaces each official UN5 `<br>` with one space and selects a verified character range. v28 uses it to distribute one official loading sentence across NA2's three original fixed slots without embedding manual prose.

## Output

Each run creates:

`translation_package_builder\work\runs\<UTC+3 run id>\`

containing:

- `NA2_APPLY__TRANSLATION__<run id>.tsv`
- `build_summary.json`

The generated translation TSV contains exactly six columns:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

`build_summary.json` contains only general and aggregate run information:

- builder version, run ID, timezone, and selected targets;
- patch and mapping totals;
- active mapping coverage grouped by mode and section;
- source and translated-file hashes.

Disabled and unresolved rows remain solely in `mappings.tsv`.

## Safety behavior

Known clean-source SHA-1 values are checked by default. `-NoStrictHash` disables those checks only for deliberate experiments.

The builder rejects malformed flags, duplicate IDs, invalid offsets, invalid source references, malformed transforms, overlapping active mappings, unexpected structural bytes, text exceeding its declared slot, and invalid named-color conversion. Enabled bad mappings fail the build instead of becoming silent runtime skips.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

## Markup handling

The original NA2 target is authoritative for renderer-specific color forms:

- UN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- UN5 `<BLACK>` remains `<BLACK>` or becomes `<color000000>` according to the verified target form.
- `<RED>` is retained only where the target supports it.
- Other shared color, icon, line-break, and control tags are preserved.

## Version 28 changes

### Builder packaging cleanup

- Removed `VERSION.txt`.
- Removed `MAPPINGS_DEFAULT.sha256`.
- Moved the canonical version and packaged mapping hash into this README.
- Added strict README metadata parsing so missing or malformed release metadata fails visibly.

### Enabled-state migration repair

- Fixed the `M0745` v26-to-v27 migration defect.
- Persistent state now merges by stable ID only.
- Archived mappings are ignored when byte-identical to their own packaged defaults.
- Legacy semantic migration is attempted only for a table proven to contain changes.
- New or redesigned mappings therefore retain their v28 packaged flags when the old installation had no actual user edits.

### Save/load loading message

The Japanese three-line loading warning shown below the save list is replaced using the exact official UN5 sentence:

`Loading from memory card (PS2). Please do not remove memory card (PS2), controller, or reset/switch off the console.`

The official `<br>` is flattened to one space and the sentence is sliced across the three existing NA2 slots. No manual translation, relocation, or slot expansion is used.

### Naruto Command Chart

Added exact UN5 mappings for the visible Naruto command page:

- `Naruto Uzumaki Combo Attack`
- `Great Ball Rasengan`
- `Flying Shadow Rising Attack`
- `Clone Jutsu: Head Split`
- `Whirlwind Kick`
- `Demon Wind Charging Transformation`
- `Charging Rasengan`
- `Nindo Attack`
- `Demon Wind Assault`
- `Jumping Express`
- `Rising Windmill`
- `Flying Shadow Attack`
- `Instant Hand Bullet`

Also resolved the category labels to exact UN5 `Combo` and `Charge`, and mapped the remaining static duplicate `Naruto` labels that use the same verified source string.

### Carried-forward v27 baseline

v28 retains the accepted v27 behavior: stable mapping IDs, original-slot text only, traceable `[S]` shortening, no active relocation pools or pointer redirects, exact ASCII `ON`/`OFF`, corrected `Yes`, visible `Reunion Time I`, Character Select matchup labels, Music/Options result messages, save-list numbers and `Empty`, and the expanded save/memory-card flow.

The packaged v28 table contains 854 mappings: 844 enabled and 10 disabled. Active mappings comprise 748 `slot` rows and 22 `shorten` rows. Seventy-four enabled `unresolved` entries remain documented but unapplied; all four structural `bytes` rows remain disabled.

## Rolling runtime issue log

This log persists unresolved visual/runtime findings across builder versions. An entry is removed from the open section only after a verified fix, rather than vanishing because a new ZIP was born and developed selective amnesia.

### Resolved in v28

- **Save/load list, lower message panel:** Japanese loading text replaced from official UN5 across the original three slots.
- **Naruto Command Chart:** visible move names, `Combo`, `Charge`, and static `Naruto` labels mapped from exact UN5 sources.
- **Enabled-state migration:** unchanged v26 defaults can no longer disable redesigned `M0745`.

### Open

- **Options main screen:** the `Options` logo, difficulty/value, controls, screen, audio, restore, confirm, and back labels remain Japanese in the supplied screenshots. Existing translated BTL text does not affect these rendered labels, which indicates a separate graphical/CCS resource path, likely the referenced `option.ccs` inside DATA.CVM. The required NA2 and UN5 resource payloads are outside the current builder source set. Left untouched until those assets are extracted and structurally compared.
- **Collection Movie screen chrome:** the `Collection` title, `Movie` category heading, and play/back prompts remain Japanese and appear to use graphical/CCS resources outside the current text targets. Left untouched pending verified donor and target assets.
- **Collection movie-title fit:** exact UN5 titles are already present, but several extend beyond the visible right edge. They remain unshortened. This is a text-fit/renderer candidate and must be solved by reproducing verified UN5 width/scale behavior, not by altering official strings.
- **Command Chart chrome:** any remaining Japanese heading or back prompt that is graphical rather than string-backed remains outside current scope pending resource extraction.
- **Dynamic save date/time numerals:** retained as unresolved mapping `M0833`; the digits are generated by executable code and still require a verified renderer/code mapping.

PCSX2 application chrome, toolbar text, pause indicators, and emulator toasts are not game translation issues and are not logged here.

## v28 test checklist

1. Build from a clean installed v28 directory and confirm the summary reports builder version 28.
2. Enabled migration: with an unchanged archived v26 default and no persistent state, verify `M0745` remains enabled.
3. Existing state: leave `work\translation_builder_state\enabled_state.tsv` in place, build once, and verify `M0745=1` is preserved while new v28 IDs adopt packaged defaults.
4. Save list: slots show `1`, `2`, `3`, and `Empty`; the lower loading warning is fully English and adjacent data is intact.
5. Naruto Command Chart: verify the character label, `Combo`, `Charge`, and all thirteen visible move names.
6. Options: confirm no regression or blank labels. Remaining Japanese graphical labels are expected and logged above.
7. Collection: confirm all movie titles remain exact UN5 text; record clipping only as renderer fit, not as a translation shortening request.
8. Regression: repeatedly enter and leave save/load, Command Chart, Options, and Collection screens; verify no blank text, overlap corruption, white screen, or crash.
9. Generated TSV validation: six columns, fixed-size patches only, and successful composition with the current Font package.

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
