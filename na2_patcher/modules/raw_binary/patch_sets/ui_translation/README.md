# UI translation raw-binary patch set

This patch set holds size-preserving executable changes that are inseparable from
the NUN5 UI container import but do not belong inside `DATA.CVM`.

## UI-BTL-001: one-part OUGI label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. The official English NUN5
and Brazilian NUN6 versions both use one 128x64 label and the same one-iteration
construction loop. The whole-container `OUGI.CCS` import supplies that one-part
model, UV, texture, and animation layout.

At BTL file offset `0xB5E80`, NA2 contains `02 00 42 2A`
(`slti v0,s2,2`). NUN5 and NUN6 contain `01 00 42 2A`
(`slti v0,s2,1`) at the structurally equivalent instruction. `UI-BTL-001` makes
that exact four-byte replacement. It preserves the file size and is disabled by
default until the combined texture/code build is runtime-tested.

Validate and inspect the planned edit from the repository root:

```powershell
python -m na2_patcher.modules.raw_binary.engine validate `
  --package na2_patcher/modules/raw_binary/patch_sets/ui_translation `
  --root na2=@source/NA2.iso.files

python -m na2_patcher.modules.raw_binary.engine plan `
  --package na2_patcher/modules/raw_binary/patch_sets/ui_translation `
  --root na2=@source/NA2.iso.files `
  --patch UI-BTL-001
```

Evidence and the broader container/layout analysis are recorded in
`docs/plans/ui_translation.md`.
