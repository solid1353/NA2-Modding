# NA2 Translation Package Builder v22

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

The builder rejects invalid offsets, malformed source strings, overlapping fixed slots, invalid pointers, and undersized relocation pools. A fixed-slot mapping whose official source text does not fit is skipped and recorded instead of overrunning adjacent data. No guessed translation text is emitted.

`build_summary.json` records source hashes, translated hashes, patch counts, runtime skips, and unresolved mappings.

## Default targets and aliases

Default selection: `BTL,ETC,SLPS`.

`ELF`, `SLES`, and `EXE` alias `SLPS`. `ALL` selects all targets.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Optional extracted-source folders or ISO files can be supplied through the wrapper parameters defined in `build_na2_translation_package.ps1`.

## Version 22

Version 22 expands v21 using the paired NA2/UN5 executable disassemblies and verified parallel data-table structure. It adds only numeric official-source mappings that fit existing slots or use already verified relocation rules. One ambiguous character-name candidate was deliberately left unresolved rather than guessed.

The mapping file moved from `data\mappings.tsv` to root `mappings.tsv`.

Validated against the supplied clean sources:

- 596 fixed-slot mappings
- 26 relocation entries
- 112 unresolved numeric targets
- zero runtime skips
