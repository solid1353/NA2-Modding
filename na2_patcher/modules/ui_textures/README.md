# UI texture translation module

This module derives the selected official English NUN5 UI containers directly
from the canonical NA2 and NUN5 sources and writes them into the unchanged NA2
`DATA/DATA.CVM` member ranges. No replacement CCS blobs are stored in Git.

## Safety and reproducibility

- `containers.tsv` pins every clean NA2 target and official NUN5 donor member.
- `mappings.tsv` records 76 reviewed texture relationships.
- `strategies.tsv` pins each derived fixed-size replacement hash and its
  decompressed CCS payload hash.
- All 34 derived replacements preserve their original NA2 member size and
  therefore do not move a `DATA.CVM` member or ISO extent. Their fixed ranges
  total 5,274,398 bytes.
- Thirty-one `whole` strategies import the complete NUN5 CCS payload so pixels,
  models, UVs, layout, and animation data remain coupled.
- `HOME.CCS` is a mapped structural exception: it keeps NA2's collection
  models, UVs, layout, and animation data, and copies only the five official
  English TEX/CLT pairs used by the visible collection labels.
- `MAPSEL1.CCS` is a mapped structural exception: it starts from NA2 and copies
  only the paired NUN5 TEX/CLT data for the stage-name atlas and Stage Select
  label. NA2's stage-picture atlases and CCS structure remain unchanged.
- Mapped `copy` imports retain the first word of every NA2 TEX section because
  it is a container-local palette-object reference; pixel data after that word
  and the complete paired CLT payload come from NUN5.
- `MODE2KDV.CCS` is a mapped capacity exception: it retains the NA2 portrait,
  palette, and lower 192 visual rows, then imports the donor's top 64 label rows
  through deterministic nearest-palette-index remapping.
- `CMN/GAUGE.CCS` supplies the shared regional UI atlas. In particular,
  `TEX_xpanel` replaces NA2's Circle/decision and Cross/back legends with
  NUN5's Cross/OK and Triangle/Back legends wherever the common panel is used.
- The NUN5 one-part `OUGI.CCS` layout also requires the paired,
  size-preserving `UI-BTL-001` semantic port in
  `na2_patcher/modules/raw_binary/patch_sets/ui_translation/`.

The engine searches deterministic zlib encodings first. Five fixed-capacity
members require Zopfli; `na2_patcher/requirements.txt` pins the verified
`zopfli==0.4.3` implementation. A normal build fails clearly instead of using
different or unpinned output bytes when that dependency is unavailable.

## Commands

Install the pinned patcher dependency:

```powershell
python -m pip install -r na2_patcher/requirements.txt
```

Derive and verify every pinned production replacement from the repository root:

```powershell
python -m na2_patcher.modules.ui_textures.engine verify
```

Write a review-only generated extraction outside the source roots:

```powershell
python -m na2_patcher.modules.ui_textures.engine preview `
  --output work/temp/ui_texture_preview
```

Changing a mapping, strategy, compressor version, or canonical source must
produce the exact pinned payload and replacement hashes or fail. Any intentional
hash change therefore requires explicit review and a profile-pin update; there
is no blob-authoring command or stored binary fallback.

## Evidence and tools

The investigation used the repository's extracted NA2, NUN5, and Brazilian
NUN6 sources; preserved Ghidra exports; a purpose-built CCS parser and texture
decoder; gzip/zlib and Zopfli 0.4.3; and CCSFileExplorerMSF 3.0.0.0 for
independent visual inspection. StudioCCS material under `@utils/old/` was used
as format evidence only; no untrusted historical utility was executed. The
reasoning, inventory, layout comparisons, and historical runtime evidence are
recorded in `docs/plans/ui_translation.md`.
