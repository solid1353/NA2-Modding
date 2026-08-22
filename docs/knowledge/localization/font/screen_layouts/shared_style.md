# Shared Font style and matched-screen baseline

Cross-screen evidence for the global selected-style dispatcher and the final matched-screen baseline.

## Global selected-style default

Evidence date: 2026-08-01.

The first candidate covered only NA2 runtime `0x00379150`. User isolation
testing proved that it corrected roughly half of the game while the selected
`Back to Game Mode Screen` row in the Character Select five-row modal retained
NA2's displacement. Clean call tracing shows that row enters runtime
`0x00382610`, which calls separate state-aware selected primitive
`0x00379040`. The two-central-primitive candidate fixed additional screens,
but the supplied `Save data?` comparison remained displaced because shared
save/load runtime `0x001E6CE0` inlines both selected passes and calls neither
central primitive.

The complete boundary requires a function-level semantic scan, not a search
for one instruction encoding. Across clean `SLPS_258.37`, `ADV.BIN`,
`BTL.BIN`, and `ETC.BIN`, exactly six functions combine gray `0xFF808080`, an
X `-1.0`/Y `-2.0` selected pass, and the text renderer. All six are in the
boot ELF:

- `FUN_00379040` / runtime `0x00379040`: state-aware central primitive;
- `FUN_00379150` / runtime `0x00379150`: caller-colored central primitive;
- `FUN_00379C30` / runtime `0x00379C30`: fixed two-choice primitive;
- `FUN_001E6060` / runtime `0x001E6060`: shared two-record list component;
- `FUN_001E6370` / runtime `0x001E6370`: three-record save/load slot row;
- `FUN_001E6CE0` / runtime `0x001E6CE0`: shared Save/Load, overwrite, and
  return-to-title Yes/No component.

The overlays contain callers but no seventh implementation. NUN5 homologs
`FUN_001EBEE0` and `FUN_001ECAD0` replace the corresponding NA2 two-choice
logic with NUN5 helper `FUN_00392920`, which creates selected markup with
shadow enabled. NUN5 `FUN_001EC0B0`, however, retains the manual three-record
sequence; normalizing NA2 `FUN_001E6370` is intentional because the requested
result is one global stable-origin rule, not a claim that every NUN5 caller was
internally rewritten.

The implementation applies one formula through three storage-ABI adapters:
shadow `(x+1,y+2)`, selected glyph `(x,y)`. Boot-ELF files `0x279168` and
`0x279278`, guarded by `80CA848F80FF0234`, call the same 48-byte register
adapter after the central primitives save X/Y in `f21/f20`. Seven exact gray
record-draw calls in `FUN_001E6060`, `FUN_001E6370`, and `FUN_001E6CE0` call
one 56-byte record adapter before their untouched native `(-1,-2)` step.
Boot-ELF file `0x279D30`, guarded by `A0FFBD275000BFFF`, redirects the fixed
two-choice primitive to a typed C dispatcher: selected rows use corrected
`FUN_00379150`, ordinary rows use native `FUN_00378F50`, and the original
renderer context, record pointers, order, and colors are preserved.

NUN5's larger renderer and markup helpers remain binary-incompatible with
NA2, so no NUN5 machine-code block is transplanted. No string bytes are
written. Every screen-specific Font patch is temporarily disabled while the
user verifies this isolated global behavior; no agent runtime or screenshot
test is performed.

## Matched-screen baseline

Ten timestamp-matched NUN5/NA2 savestate pairs supplied on 2026-07-24 provided
the initial cross-screen baseline. Their embedded 640x480 screenshots were
measured with fixed dark-ink bounds on manually verified crops. Those
measurements support relative screen comparison, not replacement of renderer
metrics recovered from code.

| Screen family | Initial NA2 result | Durable conclusion |
| --- | --- | --- |
| Practice pause list | Long label clipped | Caller needed fitting or corrected advances. |
| Control Settings | Long and short rows made the correct fit decisions | Existing boxed-fit boundary passed. |
| Command Chart | Long move name clipped | Caller needed fitting or corrected advances. |
| Practice explanations | Descriptions clipped on one line | Caller needed wrapping and layout behavior. |
| Practice Settings | Rows fit at the wrong local origin | Positioning was caller-local. |
| Quit confirmation | Body clipped; choices were misaligned | Body wrapping and shared modal layout were separate concerns. |
| Character Select confirmation | Choices matched the same modal defect | The repeated defect was shared, not screen-specific. |
| Collection confirmation | Choices matched the same modal defect | The repeated defect was shared, not screen-specific. |
| Collection Movie list | Long entries did not wrap | List-specific wrapping was required. |
| No-memory-card prompt | Only three clipped lines were visible | System-prompt wrapping was required. |

Across 20 identical black-text samples, median NA2 differences from NUN5 were
-2 pixels in visible width, -2 pixels in visible height, `0.850782x` total
dark-ink pixels, and `1.018280x` dark-ink density inside the smaller bounds.
The font was therefore not a uniformly enlarged or uniformly heavier raster.
String-dependent width errors and caller-dependent vertical offsets proved
that one global scale, tracking, X, or Y correction could not establish
parity.

Selected and ordinary rows can enter different renderer paths even when they
display the same text. A matched ordinary row therefore does not establish the
selected result, or vice versa. Maintained E2E plans deliberately capture both
states, and a caller-family correction is validated against both together.

The three confirmation screens reproduced the same choice geometry: NUN5
placed `Yes` and `No` about 25 pixels apart vertically, while NA2 placed them
about 43 pixels apart and shifted both left. This justified one shared modal
correction. The baseline also separated raster appearance from missing
wrapping: improving glyphs alone could not fix Practice explanations,
confirmation bodies, Collection lists, or system prompts. Earlier screens with
different scrolling-help animation phases were excluded from alignment
comparisons. The domain sections above record the resulting caller-family
implementations and accepted outcomes.
