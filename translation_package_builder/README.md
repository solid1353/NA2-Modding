# NA2 Translation Package Builder v20

This builder produces one post-composition translation TSV. It does not package or modify replacement BIN or ELF files.

## Source scope

The builder reads all relevant official source files:

- NA2 `PRG/BTL.BIN`
- NA2 `PRG/ETC.BIN`
- NA2 `SLPS_258.37`
- UN5 `PRG/BTL.BIN`
- UN5 `PRG/ETC.BIN`
- UN5 `PRG/TEXTENG.BIN`
- UN5 `SLES_556.05`

The builder contains no hardcoded translated prose. Readable source and replacement text is extracted from the supplied NA2 and UN5 binaries at build time. Entries without a verified official source offset are skipped and listed in the run summary.

## Mapping data

All structural mappings are stored in `data/mappings.tsv`. It contains exactly these columns:

`mode`, `target`, `target_offset`, `capacity`, `source`, `source_offset`, `pool_offset`, `pool_capacity`, `runtime_base`, `pointer_offsets`, `reason`

The row modes are:

- `slot`: maps one fixed-capacity NA2 text slot to an official UN5 source string.
- `pool`: places an official UN5 string in a relocation pool and rewrites one or more pointers.
- `unresolved`: records an NA2 target for which no verified official source mapping is currently known.

Offsets and pointer locations are numeric structural data. `mappings.tsv` contains no translated strings. Multiple pointer offsets in one pool row are comma-separated.

## Output

Each run creates one directory:

`translation_package_builder\work\runs\<run id>\`

That directory contains both:

- `NA2_APPLY__TRANSLATION__<UTC+3 timestamp>.tsv`
- `build_summary.json`

The generated translation TSV contains exactly these columns in this order:

`path`, `offset`, `expected_hex`, `replacement_hex`, `source_text`, `replacement_text`

Text columns are populated for readable text patches. Pointer writes, cleared pool bytes, and other binary-only segments leave them empty.

## Default targets

`BTL,ETC,SLPS`

`ELF`, `SLES`, and `EXE` are accepted aliases for `SLPS`. `ALL` selects all targets.

## Direct use

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1'
```

Optional parameters support extracted source folders or ISO files:

```powershell
& '.\translation_package_builder\build_na2_translation_package.ps1' `
    -Na2Folder '.\source\NA2' `
    -Un5Folder '.\source\UN5' `
    -Apply 'BTL,ETC,SLPS'
```

Strict SHA-1 validation is enabled for the known source set. `-NoStrictHash` disables that validation for deliberate experiments.

## Runtime records

`build_summary.json` records the generated TSV path, source hashes, translated hashes, applied counts, runtime skips, and unresolved mappings.

## Version 20

The structural mapping store was converted from nested JSON to one auditable TSV. All 339 fixed-slot mappings, 20 relocation-pool entries, and 373 unresolved targets were preserved. Translation generation and output format are unchanged.
