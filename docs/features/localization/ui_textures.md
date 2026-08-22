# UI texture translation

This document covers the texture-patcher side of the `localization.ui` catalog
leaf. That leaf atomically selects these official English NUN5 UI containers
and their matching layout/runtime patches; neither side can be enabled alone.
The module derives the containers directly from the canonical NA2 and NUN5
sources and writes them into the unchanged NA2 `DATA/DATA.CVM` member ranges.
No replacement CCS blobs are stored in Git.

## Safety and reproducibility

- `containers.tsv` pins every clean NA2 target and official NUN5 donor member.
- `mappings.tsv` records 210 reviewed texture relationships.
- `strategies.tsv` pins each derived fixed-size replacement hash and its
  decompressed CCS payload hash.
- All 96 derived replacements preserve their original NA2 member size and
  therefore do not move a `DATA.CVM` member or ISO extent. Their fixed ranges
  total 6,297,394 bytes.
- Ninety-two `whole` strategies import the complete NUN5 CCS payload so pixels,
  models, UVs, layout, and animation data remain coupled.
- `HOME.CCS` is a whole donor because its official collection headers,
  Previous Page/Play labels, button prompts, models, UVs, and layout must stay
  coupled. The former texture-only import clipped and displaced those labels.
- `MAPSEL1.CCS` is a whole donor because its stage-picture association/order,
  object layout, models, UVs, and labels must match NUN5 together. The stage
  picture pixels already matched; retaining NA2's structure caused the defect.
- Sixty-one character `3EYE/3???3PCT.CCS` containers import the complete
  official NUN5 Victory-name and ordinary-awakening artwork. Fifty-nine use
  complete donors because those are the only decoded visual changes. Haku and
  Shikamaru remain mapped fixed-capacity exceptions: Haku discards transparent
  canvas and uses seven nearest colors from its NUN5 palette; Shikamaru omits
  only its faintest donor antialias shade. No character texture blobs are
  stored. `ui_layout_victory_names` separately derives NA2's prebuilt name rectangles from
  the official NUN5 frame templates and English width table.
- `3EYE/ENDDEMO.CCS` is mapped so only the complete NUN5 `enddemo01` TEX/CLT
  pair, including the English `WINNER` emblem, replaces the corresponding NA2
  atlas. Its two unrelated background textures and target CCS structure remain
  unchanged.
- Mapped `copy` retains the first container-local TEX palette reference and
  validates paired component signatures before changing the target.
- `MODE2KDV.CCS` is a mapped capacity exception: it retains the NA2 portrait,
  palette, and lower 192 visual rows, then imports the donor's top 64 label rows
  through deterministic nearest-palette-index remapping.
- `CMN/GAUGE.CCS` supplies the shared regional UI atlas. In particular,
  `TEX_xpanel` replaces NA2's Circle/decision and Cross/back legends with
  NUN5's Cross/OK and Triangle/Back legends wherever the common panel is used.
- The NUN5 one-part `OUGI.CCS` layout also requires the paired,
  size-preserving `ui_layout_ultimate_jutsu_label` semantic port in
  the owning `localization.ui` catalog node.

The engine searches deterministic zlib encodings first. Twenty-eight
fixed-capacity members require Zopfli, and indexed-region translations use it
to avoid zlib-version-dependent replacement bytes;
The `builder` package set in `packages.json` pins the verified
`zopfli==0.4.3` implementation. A normal build fails clearly instead of using
different or unpinned output bytes when that dependency is unavailable.

## Commands

Derive and verify every pinned production replacement from the repository root:

```powershell
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Module na228_builder.modules.texture_patcher.engine `
  -ArgumentList @(
    'verify',
    '--package', 'na228_builder/localization/texture_patcher'
  )
```

Regenerate the reviewed Victory texture rows and hashes after an intentional
source or strategy change:

```powershell
python scripts/research/ui_translation/generate_victory_texture_mappings.py --write
```

The internal read-only Victory layout check verifies the stored layout
definitions against their original NA2 and NUN5 derivation.

Write a review-only generated extraction outside the source roots:

```powershell
python -m na228_builder.modules.texture_patcher.engine preview `
  --package na228_builder/localization/texture_patcher `
  --output "work/UI translation/temp/ui_texture_preview"
```

Changing a mapping, strategy, compressor version, or canonical source must
produce the exact pinned payload and replacement hashes or fail. Any intentional
hash change therefore requires explicit review and a pin update; there
is no blob-authoring command or stored binary fallback.

## Evidence and tools

The investigation used the repository's extracted NA2, NUN5, and Brazilian
NUN6 sources; preserved Ghidra exports; a purpose-built CCS parser and texture
decoder; gzip/zlib and Zopfli 0.4.3; and CCSFileExplorerMSF 3.0.0.0 for
independent visual inspection. StudioCCS material under `@tools/old/` was used
as format evidence only; no untrusted historical utility was executed. The
reasoning, inventory, layout comparisons, and historical runtime evidence are
recorded in the linked
[UI knowledge documents](../../knowledge/localization/ui/README.md).
