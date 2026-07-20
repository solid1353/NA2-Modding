# UI translation binary-patcher patch set

This patch set holds size-preserving executable changes that are inseparable from
the NUN5 UI container import but do not belong inside `DATA.CVM`.

Its 86 guarded edits are donor-first: 47 copy bytes directly from canonical
NUN5 files (39 from the ELF, seven from `BTL.BIN`, and one from `ETC.BIN`).
Another 24 store the exact values of NUN5's stage-width formula in NA2's
different inline-record layout. The remaining 15 are documented NA2-specific
ports where the equivalent NUN5 behavior has a different instruction or data
topology, or where NA2 intentionally needs a different value.

## UI-BTL-001: one-part OUGI label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. The official English
NUN5 and Brazilian NUN6 versions both use one 128x64 label and one-part
construction behavior. The whole-container `OUGI.CCS` import supplies that
one-part model, UV, texture, and animation layout.

At BTL file offset `0xB5E80`, NA2 contains `02 00 42 2A`
(`slti v0,s2,2`). `UI-BTL-001` replaces it with `01 00 42 2A`
(`slti v0,s2,1`) to port the donor's one-part behavior into NA2's loop. The
canonical NUN5 ELF, BTL, ETC, and ADV files do not contain that exact four-byte
instruction, so this row correctly remains an authored semantic port rather
than claiming an arbitrary donor copy. It preserves the file size and is
runtime-proven with the imported one-part container.

Validate and inspect the planned edit from the repository root:

```powershell
python -m na2_patcher.modules.binary_patcher.engine validate `
  --package na2_patcher/modules/binary_patcher/patch_sets/ui_translation `
  --root na2=@source_na2

python -m na2_patcher.modules.binary_patcher.engine plan `
  --package na2_patcher/modules/binary_patcher/patch_sets/ui_translation `
  --root na2=@source_na2 `
  --patch UI-BTL-001
```

Evidence and the broader container/layout analysis are recorded in
`docs/plans/ui_translation.md`.

## UI-BTL-002: localized stage-name rectangles and width fitting

NA2 and NUN5 store the same 24 `(stage_id, index)` pairs in the same order:

- NA2 BTL file offset `0x20FC10`: 24 records of 16 bytes, with an inline
  `(u, v, width, height)` rectangle after the two key words;
- NUN5 BTL file offset `0x215680`: 24 records of 8 bytes containing the two
  matching key words.

NUN5 obtains the localized rectangle separately through `FUN_003d4120`. Its
English language table is the 24-entry rectangle range at NUN5 ELF file offset
`0x4DDB90`. The NUN5 draw path also fits names wider than 214 pixels with
`min(1.0, 214.0 / width)`; copying only the rectangles would therefore preserve
the clipping visible in NA2.

`UI-BTL-002` reproduces both parts without adding a jump or overwriting a code
cave. In the NA2 table, every second key word is exactly the matched loop index.
The only other code consumer at BTL file offset `0x606BC` is changed from loading
that redundant word to `move s0,s1`. The freed word in each record stores the
precomputed single-precision NUN5 scale. The original code initialized both
axes to `1.0` by loading `f14` and copying it to `f15`. At BTL file offset
`0x61570`, the `mtc1` destination changes from `f14` to `f15` so vertical
scale stays at `1.0`; at `0x6157C`, the former `mov.s f15,f14` becomes
`lwc1 f14,4(v1)` so only horizontal scale receives the precomputed fit. The
remaining 24 rectangle fields are copied from the hash-pinned NUN5 ELF table.

The patch is 51 individually guarded edits: 24 rectangle rows copy NUN5's
English ELF table, 24 scale rows store the exact result of NUN5's width formula,
and three code rows adapt NA2's inline-record topology. A temporary application verified
that all 24 stage keys remain unchanged and match NUN5, every rectangle equals
the official English table, every scale equals the NUN5 formula, all changed
bytes stay inside declared ranges, and the 2,237,184-byte BTL size is unchanged.
Runtime comparison is still required before promotion from `approved_for_test`.

## UI-ELF-001: localized character-name atlas rectangles

The character-name renderers do not obtain their rectangles from
`CHARSEL1.CCS`. NA2 `FUN_0037d410` reads one 96-entry table at EE `0x005D4E70`
(ELF file offset `0x4D4F70`). NUN5's corresponding name helper
`FUN_0038c350` calls localized accessor `FUN_003d45d0`; language index zero in
the accessor's pointer table resolves to the official English range at EE
`0x005DDC50` (ELF file offset `0x4DDDD0`).

Each record is four signed 16-bit values `(u, v, width, height)`. Forty-four of
the 96 English records already match NA2; the other 52 change widths,
coordinates, or blank sentinels to match the imported English name atlases.
Copying the complete 768-byte English range is the minimal complete fix shared
by Character Select, VS, the battle HUD, and Battle Set. The edit is range-hash
guarded at both source and destination and preserves the ELF size.

The nearby NUN5 `FUN_0038c3a0` range at file offset `0x4DC120` is deliberately
not used. It is the separate uniform 38x46 character-portrait grid consumed by
NUN5's counterpart of NA2 `FUN_0037d470`. An earlier test build copied that
range and produced the stacked name fragments captured at runtime; the
localized accessor and call-site pairs disprove that source selection.

## UI-ELF-002: localized Options label rectangles

Importing the complete NUN5 `OPTION.CCS` is not sufficient by itself. The main
Options renderer supplies atlas rectangles from the boot ELF:

- NA2 `FUN_0038c160` reads five menu-label records at EE `0x005D52E0` and
  six difficulty-label records at EE `0x005D5310`;
- NUN5 `FUN_0039dba0` obtains the homologous English records through
  `FUN_003d43a0` and `FUN_003d43f0`, whose English tables begin at EE
  `0x005DDB90` and `0x005DDBC0`.

Both renderers use the same five screen positions and `0.9` scales. Their arrow
rectangle is also byte-identical. The remaining difference is the 96-byte
rectangle block: five menu labels, an eight-byte zero separator, and six
difficulty labels. `UI-ELF-002` copies that complete official English block from
NUN5 ELF file offset `0x4DDD10` to NA2 ELF file offset `0x4D53E0`. Source and
destination ranges are hash guarded and the ELF size is preserved.

## UI-ELF-003: difficulty-value sprite routing

The NUN5 rectangles alone fix the five main Options labels, but the widest
difficulty value still fragments unless it is drawn through the same alternate
sprite object used by NUN5. The homologous renderers differ in one predicate:

- NA2 `FUN_0038c160` selects the alternate object for indices `0` and `5`;
- NUN5 `FUN_0039dba0` selects it for indices `0`, `4`, and `5`.

At NA2 EE `0x0038C30C` (ELF file offset `0x28C40C`), `UI-ELF-003`
replaces the existing `index == 5` test with `index >= 4`, while retaining the
following `index == 0` test. For the renderer's proven valid domain `0..5`, the
resulting set is exactly `{0, 4, 5}`. The edit changes two instructions, keeps
the original branch targets and delay slots, and preserves the ELF size.

A paused, identity-checked PINE write matched the two original words exactly
and verified the eight-byte readback. After one redraw, the corrupt selected
value became a clean centered `INSANE`; captures of `HARD`, `EASY`, and
`SIMPLE` also rendered cleanly, including both arrow endpoints.

## UI-BTL-004: localized Practice Settings prompt layout

The VS-screen Practice Settings prompt needs both the English atlas rectangle
and the localized horizontal anchor. The corresponding renderers provide exact
cross-build evidence:

- NA2 `FUN_006c0cc0` uses the static rectangle `(1, 281, 112, 22)` at BTL
  file offset `0x20C9D8` and passes X=`60.0` at file offset `0xCFA0`;
- NUN5 `FUN_006d4170` calls localized accessor `FUN_003d46c0`, whose English
  table resolves to ELF file offset `0x4DE0E0`, and passes X=`100.0`.

`UI-BTL-004` copies the official NUN5 rectangle `(0, 280, 176, 24)` from its
ELF and copies the structurally equivalent `lui v0,0x42c8` instruction from
NUN5 BTL file offset `0xD500`. Both edits are exactly guarded, preserve BTL
size, and remain confined to the Practice Settings path.

The two edits were applied to a paused Current runtime and read back exactly.
After one redraw, the sprite object reported X=`276`, Y=`356`, size `176x24`,
and UV `(0,280)`. The archived screenshot shows the full label and Square icon
at the same bottom-left position as the NUN5 target.

## UI-BTL-005: localized VS confirmation labels, inputs, and prompts

The battle-confirmation Customize screen retains Japanese regional rectangle
tables even after importing the NUN5 VS texture container. `UI-BTL-005` copies
the exact English NUN5 rectangles for:

- `Customize Jutsu` and its Circle prompt;
- `Battle Settings` and its Square prompt;
- the two-arrow control;
- all three Jutsu input glyphs;
- the one-part `Jutsu1` and `Jutsu2` labels.

NUN5's Jutsu helper offsets its 62x26 label by 26 pixels and the three input
glyphs by 40 pixels. NA2's static draw path lacks those additions. A 16-byte
NA2 helper is installed in verified loaded zero padding at BTL file offset
`0x70`, the label path calls it at `0x9188`, and the two structurally equivalent
40-pixel accumulator instructions are copied from NUN5 BTL offsets `0x974C`
and `0x9750` into `0x91BC..0x91C3`. The localized 160x24 Battle Settings prompt
is drawn at the official X=`94` through the constant at `0xCFD8`.

The NUN5 renderer passes X=`260` for `Customize Jutsu`, but guarded testing
showed that transplanting this constant into NA2's different draw path wraps
the prompt around the left edge. X=`255`, encoded at BTL file offset `0xCF70`,
is the closest non-wrapping NA2 equivalent. Together with NUN5's exact
`(0,232,168,24)` rectangle, it fully exposes the Circle icon and places the
complete prompt like the paired NUN5 capture. The rejected X=`260` write is not
retained.

All 14 edits were matched against their original bytes, written through
PINE, read back exactly, and captured from user-provided slot 7. They restored
both Jutsu labels, the two arrows and Circle input graphics, and both bottom
prompts.

The later submenu-suppression wrapper was rejected: the NUN5 reference retains
the Jutsu1/Jutsu2 graphics beneath the open selector, while the wrapper removed
them and left unrelated garbage visible. Its code-cave write and call hook are
removed; the runtime-proven 14 texture/placement edits remain unchanged.

This patch changes texture selection, placement, and submenu visibility only.
It does not change or evaluate command-name text or font rendering.

## UI-BTL-006: localized Round label layout

NA2 constructs `Round` from two Japanese 38x38 glyph rectangles at X=`216`,
Y=`44`, and scale `1.4`. NUN5 uses one English 94x30 rectangle at X=`256`,
Y=`24`, with scale `1.2` and a Y=`64` render constant.

`UI-BTL-006` copies the exact NUN5 rectangle from ELF file offset `0x4DE110`,
zeros the unused second-glyph record, ports the differently stored X/Y fields,
and copies the four structurally equivalent scale/render instruction ranges
from NUN5 BTL into NA2 offsets `0xCCB4`, `0xCD5C`, `0xCD64`, and `0xCDA4`.
Eight guarded live writes were read back exactly. The resulting one-part label
matches the paired NUN5 capture; small frame-to-frame outline differences are
the screen's normal pulsation.

## UI-ETC-001: localized Shop currency-label layout

Importing the complete NUN5 `SHOP.CCS` supplies the correct English atlas, but
NA2's Shop renderer still copies its Japanese currency rectangles from
`ETC.BIN`. The corresponding 24-byte tables are:

- NA2 ETC file offset `0x30300`, loaded at EE `0x006E4200`;
- NUN5 ETC file offset `0x292F0`, loaded at EE `0x006EFFF0` in NUN5.

The first eight-byte panel record is already identical. `UI-ETC-001` copies
only the remaining 16 bytes, replacing `(169,385,42,26)` and
`(213,385,18,26)` with NUN5's official full `Money` rectangle
`(169,385,62,26)` and `Ryo` rectangle `(321,449,30,22)`. It does not change the
money value or its formatting logic.

The exact range was written through PINE at EE `0x006E4208` and read back
successfully. After a hidden redraw of preserved slot 3, both labels rendered
in full and the existing seven-digit `9999999` value remained visible. The
source and destination `ETC.BIN` files are size/hash pinned and remain
untouched.

The later Money-X and Ryo-Y anchor copies were unrelated to the reported
`Bonus Game` label and changed a screen the user had already accepted. They
are removed. Static comparison shows the complete NUN5 `SHOP.CCS` donor
already carries the exact Bonus Game model/anchor; the small capture difference
is normal label pulsation and does not justify another binary edit.

## UI-ELF-005: localized Mode Select START layout

The whole NUN5 `MODESEL1.CCS` import supplies the English START artwork, but
NA2's static rectangle still selected only `(1,397,206,22)` and drew it at
X=`130`. That truncates the 254-pixel English label visible in preserved slot 1.
NUN5 `FUN_003972e0` obtains rectangle `(1,393,254,26)` from localized accessor
`FUN_003d4bc0` (English table entry at ELF offset `0x4DE318`) and draws it at
X=`150`.

`UI-ELF-005` copies that exact eight-byte rectangle into NA2 ELF offset
`0x504710`. The X constant at NA2 offset `0x285F28` is an authored
same-register port from `130` to `150`: the corresponding NUN5 instruction
writes `v1`, while NA2's following instruction consumes `v0`, so copying the
four instruction bytes verbatim would be incorrect. Both edits preserve ELF
size and are statically verified for the user-requested runtime pass.

## UI-ELF-006: localized Controls Vibration-label rectangle

The whole NUN5 `CMN/GAUGE.CCS` import supplies the English `TEX_xmenu`
artwork, but NA2's boot-ELF table still selects the Japanese rectangle
`(1,69,42,22)` at file offset `0x4D53C0`. NUN5's localized table selects
`(64,88,64,20)` at file offset `0x4DEA28`.

`UI-ELF-006` copies that exact eight-byte NUN5 rectangle into the homologous
NA2 table. It changes only the graphical Vibration label selection; surrounding
OFF/On text and font rendering are outside scope. Both ranges are guarded and
the ELF size is preserved.

Inspect all thirteen UI companion patches together:

```powershell
python -m na2_patcher.modules.binary_patcher.engine validate `
  --package na2_patcher/modules/binary_patcher/patch_sets/ui_translation `
  --root na2=@source_na2 `
  --root nun5=@source_nun5

python -m na2_patcher.modules.binary_patcher.engine plan `
  --package na2_patcher/modules/binary_patcher/patch_sets/ui_translation `
  --root na2=@source_na2 `
  --root nun5=@source_nun5 `
  --patch UI-BTL-001 `
  --patch UI-BTL-002 `
  --patch UI-BTL-003 `
  --patch UI-BTL-004 `
  --patch UI-BTL-005 `
  --patch UI-BTL-006 `
  --patch UI-ETC-001 `
  --patch UI-ELF-001 `
  --patch UI-ELF-002 `
  --patch UI-ELF-003 `
  --patch UI-ELF-004 `
  --patch UI-ELF-005 `
  --patch UI-ELF-006
```
