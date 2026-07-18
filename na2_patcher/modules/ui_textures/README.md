# UI texture translation module

This module imports the selected official English NUN5 UI containers into the
fixed-size NA2 `DATA/DATA.CVM` member ranges. Normal profile builds consume the
hash-pinned blobs under `blobs/`; they do not recompress assets or depend on a
GUI tool.

## Safety and reproducibility

- `containers.tsv` pins every clean NA2 target and official NUN5 donor member.
- `mappings.tsv` records the 76 intentional texture relationships and validates
  that the donor has no additional decoded visual changes outside that scope.
- `strategies.tsv` pins each fixed-size replacement blob and its decompressed CCS
  payload.
- All 34 replacements preserve their original NA2 member size and therefore do
  not move any `DATA.CVM` member or ISO extent.
- Thirty-three containers carry the complete NUN5 CCS payload, including matching
  models, UVs, layout, and animation data. `MODE2KDV.CCS` is the sole capacity
  exception: it retains the NA2 palette and lower 192 visual rows and imports the
  donor's top 64 label rows after nearest-palette-index remapping.
- `CMN/GAUGE.CCS` supplies the shared regional UI atlas. In particular,
  `TEX_xpanel` replaces NA2's Circle/決定 and Cross/戻る legends with NUN5's
  Cross/OK and Triangle/Back legends everywhere the common panel is used.
- The NUN5 one-part `OUGI.CCS` layout also requires the paired, size-preserving
  `UI-BTL-001` raw-binary patch in
  `na2_patcher/modules/raw_binary/patch_sets/ui_translation/`.

## Commands

Verify the pinned production inputs from the repository root:

```powershell
python -m na2_patcher.modules.ui_textures.engine verify
```

Write a review-only extraction outside the source roots:

```powershell
python -m na2_patcher.modules.ui_textures.engine preview `
  --output work/temp/ui_texture_preview
```

`author` is a maintainer command for regenerating blobs after an intentional
mapping or source change. It uses deterministic zlib searches and optionally
Zopfli when the normal candidates do not fit. Regenerated hashes must be reviewed
and pinned explicitly in `strategies.tsv`.

## Evidence and tools

The investigation used the repository's extracted NA2, NUN5, and Brazilian NUN6
sources; a purpose-built CCS parser and texture decoder; gzip/zlib and Zopfli for
authoring; CCSFileExplorerMSF 3.0.0.0 for independent visual inspection; and the
StudioCCS source tree under `@utils/old/` as CCS format evidence only. No tool from
the untrusted historical utilities tree was executed. The reasoning, asset
inventory, capacity results, layout comparison, and remaining runtime gate are in
`docs/plans/ui_translation.md`.
