# NA2 Translation Package Builder v25

This builder produces one post-composition translation TSV for Naruto: Narutimate Accel 2. It never packages or modifies replacement BIN or ELF files.

## Integration model

The surrounding NA2 pipeline composes selected replacement packages first, then applies the generated translation TSV over the composed files. Translation therefore owns no replacement binary and can patch text or pointers inside files supplied by another package.

Project-level scripts are not included. This archive contains only `translation_package_builder`.

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

The builder contains no hardcoded translated prose. It reads all emitted English text from the supplied UN5 binaries at build time. The paired executable disassemblies were used to author and validate numeric mappings, but are not required at runtime and are not included.

## Mapping file

`mappings.tsv` is stored directly in the builder root. It contains exactly these columns:

`mode`, `target`, `target_offset`, `capacity`, `source`, `source_offset`, `pool_offset`, `pool_capacity`, `runtime_base`, `pointer_offsets`, `reason`

Row modes:

- `slot`: copy one NUL-terminated official UN5 string into a verified fixed-capacity NA2 slot.
- `pool`: write official UN5 text into a verified relocation pool and rewrite the listed target-file pointers.
- `unresolved`: retain a known NA2 text target for which no safe official-source mapping has yet been proven.

The mapping file contains only structural data: file identifiers, offsets, capacities, runtime addresses, pointer locations, and status reasons. It contains no translation strings.

## Markup handling

NA2 and UN5 share inline markup, but some named color aliases differ by renderer. v25 does not strip tags and does not emit them blindly.

For each mapped string, the builder reads the original NA2 target text and converts a named UN5 color token only to an equivalent token already used by that NA2 slot:

- UN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` when the target slot uses that token.
- UN5 `<BLACK>` remains `<BLACK>` when the target slot uses it, or becomes `<color000000>` when that is the target slot's verified form.
- `<RED>` is retained only when the target slot also uses `<RED>`.

Generic color tags such as `<color00FFFF>`, icon tags, `<br>`, and other shared markup are preserved unchanged. If a named color token has no verified equivalent in the target string, that mapping is rejected instead of displaying the token literally or guessing.

These markup tokens are structural renderer commands, not translation prose.

## Output

Each run creates:

`translation_package_builder\work\runs\<run id>\`

containing:

- `NA2_APPLY__TRANSLATION__<UTC+3 run id>.tsv`
- `build_summary.json`

The generated translation TSV contains exactly these six columns in this order:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

Readable text patches populate the text columns. Pointer writes, relocation-pool clearing, and other binary-only patches leave them empty.

## Safety behavior

Known clean-source SHA-1 values are checked by default. `-NoStrictHash` disables this only for deliberate experiments.

The builder rejects invalid offsets, malformed source strings, overlapping fixed slots, invalid pointers, undersized relocation pools, and unverified named-color conversions. A fixed-slot mapping whose official source text does not fit is skipped and recorded instead of overrunning adjacent data. No guessed translation text is emitted.

`build_summary.json` records source hashes, translated hashes, patch counts, runtime skips, and unresolved mappings.

## Default targets and aliases

Default selection: `BTL,ETC,SLPS`.

`ELF`, `SLES`, and `EXE` alias `SLPS`. `ALL` selects all targets.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Optional extracted-source folders or ISO files can be supplied through the wrapper parameters defined in `build_na2_translation_package.ps1`.

## Version 25

Version 25 restores the verified v23 mapping expansion on top of v24's corrected Game Mode description boundary.

Restored mappings include:

- the full Simple Display explanation at `BTL.BIN + 0x208E60` instead of the incorrect mid-string v22/v24 target at `0x208EA0`;
- sixteen official Battle/Practice Settings explanations previously reverted to unresolved rows;
- Return-to-screen prompts and Master Mode start-selection text;
- `Linked Mode`, `Manual`, `Auto`, `Yes`, and the relocated official `Ultimate` label.

The final Options description remains limited to 128 bytes. The seven-entry Game Mode description pointer table at `SLPS_258.37 + 0x4B1DE0..0x4B1DFB` remains byte-identical to the clean executable.

The builder now adapts UN5 named color aliases to the verified NA2 markup dialect. This fixes literal strings such as `Practice<WHITE>` without deleting color formatting.

Validated against the supplied clean sources:

- 629 fixed-slot mappings
- 27 relocation entries
- 96 unresolved numeric targets
- 799 generated TSV patch rows
- zero runtime skips
- zero literal `<WHITE>` tokens in translated output
- Game Mode description pointer table unchanged
