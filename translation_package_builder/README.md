# NA2 Translation Package Builder v21

This builder produces one post-composition translation TSV for Naruto: Narutimate Accel 2. It does not package or modify replacement BIN or ELF files.

## Purpose and integration

The surrounding NA2 build pipeline composes selected replacement packages first, then applies the generated translation TSV over the composed files. Translation therefore does not own any replacement binary and can safely patch text or pointers inside files supplied by another package.

The builder itself owns only translation discovery and mapping data. Project-level apply/build scripts are outside this archive.

## Source and target scope

The builder reads these clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

It reads official English data from:

- UN5 `PRG/BTL.BIN`
- UN5 `PRG/ETC.BIN`
- UN5 `PRG/TEXTENG.BIN`
- UN5 `SLES_556.05`

The builder contains no hardcoded translated prose. Runtime text is read from the supplied NA2 and UN5 binaries using numeric mappings. Executable disassembly may be used while authoring or validating mappings, but it is not required to run the builder and is not included.

## Mapping data

All structural mappings are stored in `data/mappings.tsv`. It contains exactly these columns:

`mode`, `target`, `target_offset`, `capacity`, `source`, `source_offset`, `pool_offset`, `pool_capacity`, `runtime_base`, `pointer_offsets`, `reason`

Supported row modes:

- `slot`: copies one NUL-terminated official source string into a fixed-capacity NA2 slot.
- `pool`: writes an official source string into a verified relocation pool and rewrites one or more pointer locations in the same target file.
- `unresolved`: records a known NA2 text target that still lacks a verified structural mapping.

Offsets, capacities, runtime bases, and pointer locations are numeric structural data. `mappings.tsv` contains no translation text.

## Generated output

Each run creates:

`translation_package_builder\work\runs\<run id>\`

The run directory contains:

- `NA2_APPLY__TRANSLATION__<UTC+3 run id>.tsv`
- `build_summary.json`

The generated translation TSV contains exactly these six columns in this order:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

Readable text patches populate both text columns. Pointer writes, cleared relocation bytes, and other binary-only patches leave them empty.

## Validation and failure behavior

Known clean-source SHA-1 values are checked by default. `-NoStrictHash` disables that check only for deliberate experiments.

A fixed-slot mapping is skipped when its official source text cannot fit safely. Invalid offsets, overlapping slots, malformed strings, bad pointers, and undersized relocation pools fail or are reported rather than guessed. `build_summary.json` records source hashes, translated hashes, patch counts, runtime skips, and unresolved mappings.

## Default targets and aliases

Default selection: `BTL,ETC,SLPS`.

`ELF`, `SLES`, and `EXE` alias `SLPS`. `ALL` selects all targets.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Optional extracted-source folders or ISO files can be supplied through the wrapper parameters documented in `build_na2_translation_package.ps1`.

## Version 21

Version 21 used the paired UN5/NA2 Practice screens and both executable disassemblies to validate additional fixed slots, enum tables, and pointer call sites. It corrected one previously wrong official-source mapping, added safe relocation entries where official text exceeds the original slot, and reduced the unresolved mapping set without adding translation prose to the builder.

Validated against the supplied clean sources:

- 359 fixed-slot mappings
- 26 relocation entries
- 349 unresolved numeric targets
- 470 generated patch rows
- zero runtime skips
