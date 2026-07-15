# NA2 Translation Package Builder v30

This builder generates one post-composition translation TSV for **Naruto: Narutimate Accel 2**. It never packages patched BIN or ELF payloads. The surrounding NA2 pipeline composes selected packages first, then applies the generated TSV over the composed files.

This archive contains only `translation_package_builder`. Project-level wrapper and ISO-building scripts remain outside the package.

## Builder metadata

- Version: `30`
- Packaged `mappings.tsv` SHA-256: `f6415ef5a27dbbf0d7f0f555ce7f2092fed149a9502a2086513d25fd922e98db`

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

`slot` and `sequence` mappings read their English bytes from exact UN5 offsets at build time. The only manual English permitted is in `shorten` rows, where the replacement begins with `[S]` because the official UN5 text cannot fit the original NA2 slot. No translation is relocated into spare space and no text pointer is rewritten.

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

- `slot`: copy one exact official UN5 text value into one original NA2 slot.
- `sequence`: pack selected exact `<br>` parts from one official UN5 string into one verified NA2 multi-string block using NUL separators.
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
- `split_br`, `split_br_sequence`, `join_br_parts`
- `flatten_br_slice`
- `append_space`
- `empty`

Arguments use compact key/value syntax, for example:

- `arg1=UN5_TEXTENG@0x708`
- `part=1`
- `parts=2,3;join=<br>`
- `start=13;end=83`

`split_br_sequence` selects official UN5 `<br>` parts listed by `parts=...` and writes them as consecutive NUL-terminated NA2 fragments.

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

The builder rejects malformed flags, duplicate IDs, invalid offsets, invalid source references, malformed transforms, overlapping active mappings, unexpected structural bytes, text exceeding its declared slot or sequence block, malformed target sequences, and invalid named-color conversion. Enabled bad mappings fail the build instead of becoming silent runtime skips.

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

## Version 30 changes

### Packed multi-string message blocks

Several NA2 dialogs are stored as consecutive NUL-terminated fragments inside one fixed-size region. Earlier builder versions treated each fragment as an independent fixed slot and zero-filled the remainder of every original fragment. When an English fragment was shorter than the Japanese one, the inserted zero padding created an early empty string and stopped the renderer before later fragments.

v30 adds `sequence` mode for these verified blocks. A sequence mapping:

- reads exact parts from one official UN5 string;
- writes the selected parts consecutively with one NUL terminator after each part;
- writes one additional NUL after the complete sequence;
- zero-fills only the unused tail of the whole verified block;
- never changes file size or writes outside the declared block.

Generated TSV annotations render the internal separators as `<NUL>` for readability. The literal characters `<NUL>` are not written into the game.

### Memory-card dialog repairs

v30 replaces the broken fragment-by-fragment mappings with four packed sequence mappings:

- `M0857`, `SLPS + 0x3039E0`, exact UN5 no-card notice from `UN5_TEXTENG + 0x29060`:
  `No memory card (PS2) is inserted in <br>MEMORY CARD slot 1.<br>Please insert a memory card (PS2) in<br>MEMORY CARD slot 1.`
- `M0813`, `SLPS + 0x303C40`, the lower unformatted-card notice from parts 0 and 1 of `UN5_TEXTENG + 0x291D0`:
  `The memory card (PS2) in <br>MEMORY CARD slot 1 is unformatted.`
- `M0816`, `SLPS + 0x303CE0`, the separate upper prompt from part 2 of `UN5_TEXTENG + 0x291D0`:
  `Format memory card (PS2)?`
- `M0829`, `SLPS + 0x3046A0`, the exact startup no-card Yes/No prompt from `UN5_TEXTENG + 0x29A10`:
  `No memory card (PS2) is inserted.<br>Please insert a memory card (PS2) in MEMORY CARD slot 1.<br>At least 102 KB of free space is necessary to save Naruto Shippuden: Ultimate Ninja 5 data. Start the game anyway?`

Retired fragment rows `M0814`, `M0815`, `M0817`, `M0830`, and `M0831` are removed. Their old persistent enabled-state entries are harmless because state migration applies only to IDs still present in the current table.

### Naruto Ultimate Jutsu name

The visible `変わらない関係` entry is translated with the exact UN5 name `Unchanging Relationship` from `UN5_TEXTENG + 0x3F60`.

Both verified NA2 copies are covered:

- `M0858`: `ETC + 0x284C0`
- `M0859`: `SLPS + 0x4AE030`

### Carried-forward repairs

v30 retains all v29 fixes: Options help-line pointer preservation, the first Theater entry restoration, `Charging Kick`, `Clone Jumping Explosion Hit`, relative generated paths, the `M0745` migration repair, original-slot text only, traceable `[S]` shortening, and no relocation pools or pointer redirects.

The packaged v30 table contains 854 mappings: 844 enabled and 10 disabled. Active mappings comprise 745 `slot` rows, 4 `sequence` rows, and 21 `shorten` rows. Seventy-four enabled `unresolved` entries remain documented but unapplied; all four structural `bytes` rows remain disabled.

## Rolling runtime issue log

This log persists unresolved visual/runtime findings across builder versions. Entries implemented in the current builder remain in the verification section until confirmed in-game.

### Implemented in v30, runtime verification required

- **Standard no-card notice:** the lower dialog should show the complete exact UN5 no-card and insertion message instead of mostly Japanese text.
- **Unformatted-card dialog:** the lower notice should show `The memory card (PS2) in MEMORY CARD slot 1 is unformatted.` and the upper prompt should show `Format memory card (PS2)?`.
- **Startup no-card Yes/No prompt:** the complete exact UN5 prompt should appear instead of stopping after `No memory card (PS2) is inserted in`.
- **Naruto Command Chart:** `変わらない関係` should show `Unchanging Relationship`.

### Carried from v29, runtime verification still required

- **Options, Difficulty Settings:** bottom blue help line should show `Set the Com strength for when in the Free Battle and Practice.`
- **Options, Control Settings:** bottom blue help line should show `Assign button controls.`
- **Collection Movie list:** first entry should show `Reunion Time I` in the correct list position.
- **Naruto Command Chart:** `特攻蹴撃` should show `Charging Kick`.
- **Naruto Command Chart:** `分身跳爆打` should show `Clone Jumping Explosion Hit`.

### Open

- **Startup no-card choice capitalization:** later replace the visible `Yes` and `No` labels with uppercase `YES` and `NO`; intentionally not included in v30.
- **Options main-screen graphical labels:** the `Options` logo, difficulty/value, controls, screen, audio, restore, confirm, and back labels remain Japanese in supplied screenshots. They appear to use graphical/CCS resources outside the current text targets and remain untouched pending extracted NA2 and UN5 assets.
- **Collection Movie screen chrome:** the `Collection` title, `Movie` category heading, and play/back prompts remain Japanese and appear to use graphical/CCS resources outside the current text targets.
- **Collection movie-title fit:** exact UN5 titles are present, but several extend beyond the visible right edge. They remain unshortened until a requested shortening or verified UN5 width/scale behavior is applied.
- **Command Chart chrome:** any remaining Japanese heading or back prompt that is graphical rather than string-backed remains outside current scope pending resource extraction.
- **Dynamic save date/time numerals:** retained as unresolved mapping `M0833`; the digits are generated by executable code and still require a verified renderer/code mapping.

PCSX2 application chrome, toolbar text, pause indicators, graphical controller prompts, and emulator toasts are not game translation issues and are not logged here.

## v30 test checklist

1. Build from a clean installed v30 directory and confirm the summary reports builder version 30.
2. Confirm `build_summary.json` contains only a relative TSV filename and no absolute host paths.
3. Enabled migration: preserve external state and verify `M0745=1`; redesigned `M0813`, `M0816`, and `M0829` should preserve their stable-ID flags, while new `M0857`-`M0859` use packaged defaults.
4. Standard no-card notice: verify all four exact UN5 text parts are visible and no Japanese fragment remains.
5. Unformatted-card dialog: verify the complete lower notice and separate upper `Format memory card (PS2)?` prompt.
6. Startup no-card prompt: verify the complete message reaches `Start the game anyway?` and the existing mixed-case `Yes` / `No` labels remain unchanged for now.
7. Naruto Command Chart: verify `Unchanging Relationship`, `Charging Kick`, and `Clone Jumping Explosion Hit` are visible in the active entries.
8. Options and Collection: verify the v29 help-line and first-Theater-entry repairs remain intact.
9. Re-enter save/load screens repeatedly and verify no blank text, early termination, overlap, white screen, or crash.
10. Generated TSV validation: six columns, fixed-size patches only, relative summary reference, and successful composition with the current Font package.

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
