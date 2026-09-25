# UI texture translation

This document covers the texture-patcher side of the internal `localization.ui`
patch and custom artwork compatibility with Japanese. The English language
choice includes the localized UI containers and their matching layout/runtime
patches together.

The 108 reviewed compressed CCS replacements are maintained individually under
`@builder/patches/localization/ui/assets/`. A build verifies each asset against
the compressed and decompressed hashes in `assets.tsv`, then packs
them deterministically into the inserted `PRG/228_UI.BIN`. It does not modify
`DATA/DATA.CVM`, read NUN5, or use a derivation cache.

## Known JP issues

`features.localization: "jp"` is experimental. These issues remain unresolved:

- Mod Settings custom graphics have incorrect colors and transparency because
  their pixel indices do not match the Japanese palettes.
- Rematch artwork overwrites parts of the Japanese results labels and has
  incorrect colors and transparency. Its prompt shows Triangle, while its
  Circle binding conflicts with the native Japanese confirm action.
- Custom texture text remains English.

## Runtime routing

`PRG/228_UI.BIN` begins with one sector containing a fixed-size index. Each row
stores a normalized logical-path hash, the member's starting sector, its sector
count, and its decompressed size. Every compressed CCS member begins on a sector
boundary and retains its reviewed fixed-size gzip stream.

The resident localization payload intercepts the native open, gzip-size, and
file-size calls in both CCS loading coordinators. A path present in the pack
index opens `CDV:PRG/228_UI.BIN`, seeks to the indexed member, and supplies that
member's sizes to the unchanged native read, gzip, task, parser, publication,
and cleanup pipeline. A path absent from the index uses the original
`DATA.CVM` open and metadata functions unchanged.

The localized memory-card lower panel uses NUN5's `(8,230,496,144)`
geometry. Body and choice placement belong to
[Font](font.md#caller-specific-contracts).

## Maintained inputs

- `assets.tsv` records each packed path and its accepted compressed and
  decompressed hashes.
- `assets/<container_id>.ccs.gz` is the exact fixed-size compressed CCS member
  consumed by ordinary project and release builds.

Whole-container assets preserve the coupled pixels, models, UVs, layout, and
animation data. The mapped exceptions retain only the reviewed NA2 structures
or regions described by their strategy and mapping rows. In particular,
`3EYE/ENDDEMO.CCS`, `MODE2KDV.CCS`, Haku's Victory container, and Shikamaru's
Victory container remain bounded mapped replacements. `CMN/GAUGE.CCS` supplies
the shared regional prompt atlas, and the NUN5 one-part `OUGI.CCS` remains
paired with the Ultimate Jutsu layout work in the same internal patch.

ENDDEMO's mapped replacement includes the English emblem's
`MDL_win`, `MDL_win_f`, `ANM_end_win01`, and `ANM_end_win02` alongside its
atlas. The derivation remaps donor object references by filename and object
name while preserving unrelated NA2 sections and the compressed member size.

## Research authoring

Research tooling under `@scripts/research/ui_translation/` can rederive the
accepted assets from pinned clean NA2 and NUN5 sources when a texture
translation is intentionally changed. Production code does not import that
tooling. Its `ui_texture_data/` directory retains the target, donor, mapping,
strategy, and derivation evidence needed for that work. Any intentional asset
change must update its reviewed hashes and checked-in replacement together.

## Evidence and tools

The asset investigation used the repository's extracted NA2 and NUN5 sources,
preserved Ghidra exports, the maintained CCS parser and texture decoder,
gzip/zlib and Zopfli 0.4.3, and CCSFileExplorerMSF 3.0.0.0 for independent
visual inspection. The reasoning, inventory, layout comparisons, and retail
runtime evidence are recorded under `docs/knowledge/localization/ui/` and
`docs/knowledge/game/files/ccs_runtime.md`.
