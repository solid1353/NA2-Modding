# Translation Comparison Report

Compared translated files from `build/Current.iso` against untouched source files under `source/NA2.iso.files/`.

## Tools Used

- PowerShell
- `scripts/extract_iso_file.ps1`
- `scripts/compare_translation_files.ps1`
- `scripts/extract_changed_string_slots.ps1`

No disassembler was used for this comparison pass.

## Inputs

- Source `source/NA2.iso.files/PRG/BTL.BIN` vs build `work/translation_compare/build_current/BTL.BIN`
- Source `source/NA2.iso.files/PRG/ETC.BIN` vs build `work/translation_compare/build_current/ETC.BIN`
- Source `source/NA2.iso.files/SLPS_258.37` vs build `work/translation_compare/build_current/SLPS_258.37`

## Outputs

- `work/translation_compare/reports/translation_compare_summary.tsv`
- `work/translation_compare/reports/translation_compare_regions.tsv`
- `work/translation_compare/reports/changed_string_slots.tsv`

## Binary Summary

| File | Size Match | Diff Bytes | Diff Regions | First Diff | Last Diff | Changed English-Looking String Slots |
| --- | --- | ---: | ---: | --- | --- | ---: |
| `BTL.BIN` | yes | 14200 | 224 | `0x1DBAB0` | `0x20B7FF` | 314 |
| `ETC.BIN` | yes | 9169 | 237 | `0x24F50` | `0x2F8D7` | 336 |
| `SLPS_258.37` | yes | 15947 | 341 | `0x2FBAE0` | `0x506FB5` | 513 |

All three translated files currently preserve original file size.

## Immediate Observations

- The control/practice settings strings from the screenshot are in `BTL.BIN`, starting around `0x208A30`.
- Many English strings are byte-budget constrained. Example: `Control Settings` already uses 16 bytes; fullwidth SJIS `Ｃｏｎｔｒｏｌ　Ｓｅｔｔｉｎｇｓ` would be far too large without relocation or shorter wording.
- Several translations are understandable but rough or abbreviated: `Base Cam`, `Event Cam`, `Sand Masters`, `Evil Ones`, `Guts Weight`, `Kumo Scroll`, `Cmd Display`, `Dmg Display`.
- The previous patch appears to be fixed-width replacement work, not a pointer/relocation strategy. Polishing should preserve each slot's byte budget unless we intentionally build relocation support.

## Screenshot-Relevant BTL Strings

| Offset | Bytes | Current Text |
| --- | ---: | --- |
| `0x208A30` | 16 | `Control Settings` |
| `0x208A50` | 14 | `Basic Commands` |
| `0x208A80` | 11 | `1P Commands` |
| `0x208AA0` | 11 | `2P Commands` |
| `0x208AF0` | 17 | `Practice Settings` |
| `0x208B10` | 23 | `Simple Display Settings` |
| `0x208BB0` | 21 | `Return to Mode Select` |
| `0x208BE0` | 26 | `Return to Character Select` |

## Suggested Next Step

Create a candidate polish table from `changed_string_slots.tsv` with columns for `NewText`, `Reason`, and byte-length validation. Start with visible UI strings in `BTL.BIN`, then move to `SLPS_258.37`, then `ETC.BIN`.
