# Texture palette and material runtime

This document records the resident texture, palette and material runtime of
retail NA2 (`SLPS-25837`). Function names are descriptive Ghidra identities, not
recovered source symbols. All addresses below are resident `SLPS_258.37` EE
addresses unless explicitly identified as file offsets; see
[address conventions](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Runtime texture/CLUT/material binding, sampling/animated texture paths, palette changes and draw-time resource consumers.
- **Exploration depth:** Static tracing of texture/CLUT construction, copies,
  destructors and virtual resource methods; material construction/rebinding and
  two UV consumers; effect frame state and update/draw separation; and two
  palette controllers. Caller searches for the RGB controller covered the
  resident executable, BTL and ETC.
- **Confirmed coverage:** Separate texture and palette resources, ordinary and
  framebuffer-sampling texture paths, per-level transfer descriptors, cached
  palette rebinding behavior, material UV updates/consumption, effect frame
  advancement, and palette mutation/restoration helpers.
- **Unresolved or untested:** Full downstream VU UV/effect-coordinate
  interpretation; named sampling-instance use and borrowed-resource lifetime;
  RGB-controller callers/owned cleanup; reflected-palette scheduler units; and
  the meaning of material `+0x08`.
- **Deliberate exclusions and overlap:** File framing, type parsing and shared
  image-transfer-group layouts belong to [CCS object types](../game/files/ccs_object_types.md)
  and [Resident CCS runtime](../game/files/ccs_runtime.md), including
  [packed material snapshot masks](../game/files/ccs_runtime.md#packed-material-snapshot-masks-and-cursor-ownership).
  ALPHA, TEST and ZBUF composition belongs to
  [Material draw modes and GS state](material_render_modes.md). Geometry and skin
  conversion belong to [Model runtime](model_runtime.md); player clocks and
  curve ownership belong to [Animation runtime](animation_runtime.md); packet allocation,
  submission and DMA lifetime belong to [Render submission](render_submission.md).
- **Evidence limitations:** Static evidence only. Decompiled signatures sometimes
  omit arguments; a function request can resolve to an incorrectly merged
  containing function. No absence of a direct xref proves absence of another
  writer or consumer. Scheduling and visual results are not established by
  static state construction alone.

## Texture state and palette binding

**Observation, high confidence.** The `0x0300` parser `FUN_001B3C70` constructs
an ordinary `0x48`-byte texture through `FUN_001B4470`, or a `0x50`-byte sampling
variant through `FUN_0019E080` when input flags contain `0x20`. Both use
`FUN_0019EAB0` for base initialization. The sampling branch consumes but does
not keep the file pixel payload, forces zero extra levels and format zero,
and changes flags to `(flags & ~1) | 0x58`. This establishes a distinct resource
path rather than ordinary texture-frame animation.

The [type identities and parsing evidence](../game/files/ccs_object_types.md#confirmed-identities)
own the embedded `ccTexChunk` and `ccSamplingTexChunk` names. Bytes at
`0x005D9E70..0x005D9EAF` establish these concrete slots:

| Resource / vtable | `+0x08` destructor | `+0x0C` copy | `+0x10` resource submission |
| --- | --- | --- | --- |
| Ordinary / `0x005D9E90` | `FUN_0019E9C0` | `FUN_0019E8F0` | `FUN_001190D0` |
| Sampling / `0x005D9E70` | `FUN_0019E010` | `FUN_0019DFE0` | `FUN_0019DCD0` |

Base initialization and `FUN_0019E160` establish the following field contract:

| Texture offset | Established role |
| --- | --- |
| `+0x00` | Source directory record. |
| `+0x08` | Packed texture state: base pointer, buffer width, pixel format, log2 dimensions and bit `0x400000000`. `FUN_0019E720` returns this word OR palette `+0x08` when `+0x3C` is nonzero. |
| `+0x10` | Packed mip/filter state, initially `0x20 | (extra_levels << 2)`. |
| `+0x18` | Packed base pointers and widths for levels 1 through 3. |
| `+0x20` | Clamp state initialized to `5` for input flag `0x10`, otherwise zero; consumed as GS register `0x08` in `FUN_001830A0` and `FUN_00195A90`. |
| `+0x28` | Optional array of `extra_levels+1` transfer descriptors, stride `0x20`. Allocation is skipped for input flag `0x40`. |
| `+0x2C` | Shared transfer-group node; layout/lifetime are owned by the linked CCS type document. |
| `+0x30` | Flags retained from input using mask `0x3D`, with later registration/update bits. |
| `+0x32`, `+0x34` | Width and height, each computed as `1 << exponent`. |
| `+0x36`, `+0x37` | Width/height exponents. |
| `+0x38`, `+0x39`, `+0x3A` | Extra-level count, pixel-format byte and another input byte. |
| `+0x3B` | Ownership/group bits: bit 0 owns the descriptor array, bit 1 marks group attachment, bit 2 owns the palette. Construction clears them before setting bit 0 for its allocated array; shallow copy clears all three. |
| `+0x3C` | Palette runtime pointer resolved from the supplied palette record's `+0x2C`; zero when no palette record is supplied. |
| `+0x40` | Concrete vtable. |

`FUN_0019E0D0` converts each level's coordinate pair into a GS base pointer
through `FUN_00112AE0`. `FUN_0019E160` applies those bases both to packed
texture state and to descriptor `+0x10/+0x14` low 14 bits, leaving their high
two bits intact. Level widths halve successively. The inspected packing
branches handle levels 0 through 3; this is not a file-validation guarantee
for arbitrary level counts.

**Observation, high confidence.** `FUN_0019E8F0` makes a shallow texture copy:
it copies the source record, packed state, descriptor pointer, palette pointer,
group pointer and dimensions, then clears all three ownership/group bits at
copy `+0x3B`. `FUN_0019DFE0` adds a clear of sampling copy `+0x48`. A copied
texture therefore shares backing resources without inheriting their ownership.
The inspected copy does not prove how long a particular caller retains them.

The CLUT constructor `FUN_0019F030` initializes palette `+0x08` to
`0x2000000000000000`, clears its descriptor/group pointers at `+0x10/+0x14`,
and delegates storage construction to `FUN_0019EC60`. That helper chooses
`16x16` storage for format byte `0x13`, otherwise `8x2`; it builds one
`0x20`-byte transfer descriptor. Existing
[CLUT parsing and CSM1 ordering](../game/files/ccs_object_types.md#confirmed-identities)
remain owned by the type document.

**Observation, high confidence.** Texture destructor `FUN_0019E9C0` unregisters
flag `+0x30 & 0x80`, destroys the palette only for ownership bit `+0x3B & 4`,
frees owned transfer descriptors and unlinks an attached transfer group.
Sampling destructor `FUN_0019E010` delegates this base cleanup. Palette base
updates through `FUN_0019EB60` write both descriptor low-14-bit base fields
and bits `37..50` of palette `+0x08`; the texture getter composes that palette
word at draw time rather than duplicating it into texture `+0x08`.

## Material binding and coordinate updates

The resource descriptor parsed by `FUN_001B3450` is distinct from the
`0x1C`-byte render material. `FUN_001AD9C0` walks the container's material
list, constructs the latter through `FUN_001ADA60` / `FUN_0019A570`, and
publishes it at the source record's secondary pointer `+0x30`. Its primary
pointer `+0x2C` continues to hold the parsed descriptor. The existing
[CCS handle layers](../game/files/ccs_runtime.md#handle-layers) own this
primary/secondary distinction.

| Render material offset | Construction and binding contract |
| --- | --- |
| `+0x00` | Texture runtime pointer; `FUN_0019A620` installs it. |
| `+0x04` | Cached palette pointer from the texture getter, or zero for an absent texture. |
| `+0x08` | Cleared by binding and shallow material copy `FUN_0019A520`; meaning unresolved. |
| `+0x0C` | Parsed material descriptor. |
| `+0x10` | Alpha multiplier copied from descriptor `+0x0C`; absent descriptor defaults to `1.0`. |
| `+0x14/+0x16` | Coordinate halfwords copied from descriptor `+0x10/+0x12`; absent descriptor defaults to zero. |
| `+0x18/+0x1A` | Coordinate halfwords copied from descriptor `+0x14/+0x16`; absent descriptor defaults to `0x1000`. |

Disassembly `0x0019A5A8..0x0019A5DC` confirms the texture bind takes the
descriptor's texture record `+0x08`, dereferences its primary pointer `+0x2C`,
and treats sentinel `4` as an absent texture. The decompiler omits this
argument on one branch. `FUN_0019A620` always clears cached material `+0x08`
and stores the current texture's palette at `+0x04`.

`FUN_001910E0` multiplies material `+0x10` by render working context
`+0x114` and stores the result in context `+0x118` as the part's alpha.
Instructions `0x001916D0..0x001916E0` and `0x00191BB8..0x00191BCC`
confirm float loads and multiplication in both inspected branches.

Separate rebind consumers `FUN_00198990` (model parts), `FUN_001988D0`
(model material vector), `FUN_00195930` (effect scene child), and
`FUN_001963A0` (effect draw descriptor) replace their texture pointers but
replace the cached palette only when the new getter returns neither zero nor
sentinel `4`. Therefore an absent new palette leaves those callers' old cached
palette in place. This differs from `FUN_0019A620`, which overwrites it with
zero. It is a concrete caller behavior, not a claim about every rebind API.

**Observation, high confidence.** Streamed command `0x0201` in
`FUN_001B5400` reads six optional floats in retail version `>=0x120`, then
resolves a play-table entry holding a pointer vector and signed halfword count.
Every nonzero material in that vector receives four unsigned low-16-bit
fixed-point values, with `4096` representing `1.0`:

| Material offset | Setter | Value from parsed inputs |
| --- | --- | --- |
| `+0x14` | `FUN_001B56A0` | `(a + e*c) * 4096` |
| `+0x16` | `FUN_001B5690` | `[1 - ((1-f)*d + (1-b))] * 4096` |
| `+0x18` | `FUN_001B5680` | `c * 4096` |
| `+0x1A` | `FUN_001B5670` | `d * 4096` |

Here `a,b,c,d,e,f` are fields in reader order, defaulting to `0,1,1,1,0,1`.
The setters only store halfwords; this handler does not upload texture pixels
or palette colors. [Stream frame payloads](../game/files/ccs_runtime.md#frame-payloads)
own flag masks and reader framing. The packed `0x0201` parser writes its
fields under bits `1..0x20` and this handler reads them back under bits
`2..0x40` with the flag word unchanged, a genuine one-bit mismatch that only
the all-fields form (flags zero) avoids; see
[Packed material snapshot masks and cursor ownership](../game/files/ccs_runtime.md#packed-material-snapshot-masks-and-cursor-ownership).

The packed key command `0x0202` branch of `FUN_001B8410` evaluates six scalar
curves through `FUN_001A67D0`, applies the same coordinate formulas, and calls
the four setters for every pointer in its signed-count material vector.
Disassembly `0x001B8B38..0x001B8C64` confirms the `4096` multiplication,
halfword conversion and fan-out. Its curve defaults differ from streamed
snapshots: the first five scalar calls default to zero and the sixth to one.
The key branch does not check each material pointer for zero, whereas the
streamed branch does.

### Model UV consumption

**Observation, high confidence.** The non-flag-4 branches of
`FUN_001910E0` compare material `+0x18/+0x1A` against parsed descriptor
`+0x14/+0x16` as signed halfwords. They use fixed-point ratios
`(current_scale << 12) / initial_scale`, substituting `4096` for a zero
initial scale. A non-unit ratio calls `FUN_00197190`, which obtains source
and destination UV arrays through `FUN_00197F20` and rewrites each pair:

```text
ratio_u = initial_u_scale == 0 ? 4096 : (current_u_scale << 12) / initial_u_scale
ratio_v = initial_v_scale == 0 ? 4096 : (current_v_scale << 12) / initial_v_scale
u_out = ((current_u_offset << 12) + 2048 + ratio_u * ((u_in << 4) - initial_u_offset)) >> 12
v_out = ((current_v_offset << 12) + 2048 + ratio_v * ((v_in << 4) - initial_v_offset)) >> 12
```

Inputs and output halfwords are signed in this body; integer division and
arithmetic shifts precede low-halfword stores. Instructions
`0x001971C0..0x00197238` establish ratio/offset setup, and
`0x001974EC..0x00197544` establish the pair loop. It marks render working
context `+0x266` after the rewrite. `FUN_00192FB0` then emits zero offset
modifiers when that byte is set. Without a rewrite it emits material-minus-
descriptor offset differences instead. This connects the animation setters
to draw-side UV data without implying that every geometry route handles
scaling identically.

The flag-4 route calls `FUN_0018FFB0`. Its instructions
`0x001908D4..0x00190904` send `(current_offset - initial_offset) & 0xFFF`
for both axes to VU slot `0x14`, with unit scale words. That packet does not
read material `+0x18/+0x1A`; downstream VU interpretation is not established
here. Both routes prepare textures and separately cached palettes from the
model's material vector. Geometry selection and vertex-array ownership remain
with [Model runtime](model_runtime.md).

## Draw-time resource and state consumers

The inspected consumers share an ordering: call texture vtable slot `+0x10`,
submit the separately cached CLUT descriptor through `FUN_0010F9B0`, and write
the chosen texture/CLUT state into the draw packet. Texture state and palette
uploads are separate from blend/test state. Descriptor submission gates and
group suppression belong to
[shared image-transfer groups](../game/files/ccs_object_types.md#runtime-tag-0x1000-from-texture-and-clut-construction-image-transfer-group).

| Bounded consumer | Resource and state behavior |
| --- | --- |
| `FUN_00182B50` | Uses current render context texture `+0x128`; caller flags independently gate texture and palette submission. |
| `FUN_001830A0` | For textured draw flags `&0x180`, submits texture and palette unless caller flags suppress them. Writes texture `+0x08` OR palette `+0x08` to register `0x06`, texture `+0x10/+0x18/+0x20` to `0x14/0x34/0x08`, and register `0x3F` with zero. |
| `FUN_00195A90` | Effect draw descriptor `+0x2C/+0x30` holds texture/cached palette. Writes the same four texture registers; missing texture writes zero to all four. If a cached palette exists it is composed into texture state instead of rereading texture `+0x3C`. |
| `FUN_0018E9F0` | Textured full-screen draw uses texture/cached palette at input `+0x10/+0x14`, submitting them before the draw. Uses context-two registers `0x07/0x15/0x35/0x09`. |
| `FUN_001CD7F0` | Caches composed texture state and filter state in another owner at `+0xD8/+0xE0`; optional retention stores texture/palette at `+0xEC/+0xF0`. |

The shared ALPHA, TEST and ZBUF state written beside these resources is
composed as described in
[Material draw modes and GS state](material_render_modes.md#shared-draw-context-and-state-composition).

Effect draw `FUN_00195A90` computes integer alpha as
`int(draw_alpha * frame_halfword) >> 5`, skips values below one, caps at
255, and writes packed color plus that alpha to register `0x01`. Its ALPHA/TEST
composition and opaque/list-order decision are owned by
[Material draw modes and GS state](material_render_modes.md#mode-propagation-and-bounded-direct-callers).

## Effect texture frames

**Observation, high confidence.** A `0x0E00` effect retains one texture binding
and a separate frame table. Parser `FUN_001B2E50` allocates `0x34 + count*8`
bytes and publishes table pointer `+0x30`, count `+0x16`, and packed dimensions
`+0x2C`. Each eight-byte entry supplies two coordinate halfwords and an alpha
halfword at `+0x04`. `FUN_001963F0` copies these to draw descriptor
`+0x3C`, `+0x20`, and `+0x40`, and binds its texture/cached palette at
`+0x2C/+0x30`. Frame selection changes the table entry consumed by the draw;
the inspected step does not select another texture or palette.

In `FUN_00195A90`, index `frame*8` supplies the alpha halfword used by the
draw calculation above. The entry's first two halfwords are emitted into
the VU packet along with the packed dimensions and four floats from the
source effect descriptor `+0x1C..+0x28`. Their complete downstream coordinate
interpretation is unresolved. The source scalar `+0x18` is copied to draw
`+0x24` and consumed in projection calculations. Instructions
`0x001B2EF0..0x001B2F34` establish its signed-halfword-to-float construction
and division by `256` for version `>=0x122`; the decompiler incorrectly
renders its storage as an integer cast.

`FUN_001963F0` also copies source flags bit 5 to draw mode `+0x58` bit 1
(repeat), derives primitive `+0x22` from bit 6, and passes the low three flag
bits as a blend selector to `FUN_00196260`, whose ALPHA/TEST state is owned by
[Material draw modes and GS state](material_render_modes.md#mode-propagation-and-bounded-direct-callers).

### Frame state and advancement

Scene child `FUN_00195A10` embeds the draw descriptor at scene `+0x90`,
sets type `+0x8E` to `0x0E00`, and initializes frame `+0xF6` to zero.
`FUN_001956D0` arms it by writing `0xFFFE`; stop `FUN_001956A0` writes
`0xFFFF` and updates the scene's alpha/flags. Step `FUN_001956E0` follows
this contract, corroborated by instructions `0x001956E0..0x00195750`:

| Current frame | Result of a step |
| --- | --- |
| `0xFFFF` | Returns `-1` without changing the frame. |
| `0xFFFE` | Stores `delta-1`. |
| Ordinary frame | Adds the supplied delta's low halfword and stores a halfword. |
| Result below scene count `+0xB0` | Retains and returns that result. |
| Result at or beyond count | Stores zero if scene `+0xE8 & 2` repeats, otherwise `0xFFFF`. |

Repeat discards overshoot rather than taking a modulo. The comparison treats
the stored frame as unsigned. No rate scalar is consumed by this step.

The inspected draw owners `FUN_001A2000`, `FUN_001BB790`, and scene-group
`FUN_00194180` call `FUN_00195760`. It draws only frames below `0xFFFE`,
refreshes the scene transform, multiplies caller alpha by scene/hierarchy
alpha, and calls `FUN_001961D0` / `FUN_00195A90`. It does not advance the
frame. A separate combined helper `FUN_00195810` draws and increments, but
no caller of that helper is established.

Two update paths do advance the frame. Streamed object command `0x0101`
in `FUN_001B5900` may arm an effect on alpha/position conditions, then calls
`FUN_001956E0(child, 1)` before storing its new transform and alpha.
Packed player `FUN_001BB210` first evaluates typed keys, then, when the
integer part of its fixed-point clock changes, advances every bound
`0x0E00` child by that integer difference before dispatching crossed packed
commands. Consequently draw-call count alone does not establish effect
frame count. Player clock, command crossing and binding ownership remain in
[Animation runtime](animation_runtime.md#advance-and-end-behavior).

## Palette changes and lifetime

Two distinct resident helpers change palette colors. These operate on resident
color words and are not texture-selection animation.

### Reflected entry-range motion

**Observation, high confidence.** `FUN_003B20F0..FUN_003B2270` implement a
`0x28`-byte palette controller with these fields:

| Offset | Role and producer |
| --- | --- |
| `+0x00` | Borrowed palette installed by `FUN_003B21A0`. |
| `+0x04` | Resident color pointer from palette transfer descriptor `+0x04`. |
| `+0x08` | Color count: descriptor's low-28-bit qword count multiplied by four. |
| `+0x0C` | Owned snapshot of those color words. |
| `+0x10/+0x14` | Float accumulator and increment, set by `FUN_003B2250`. |
| `+0x18` | Integer shift, initialized to zero. |
| `+0x1C/+0x20` | Half-open entry range, initialized to the full palette and replaceable through `FUN_003B2260`. |
| `+0x24/+0x25` | Repeat flag and completion byte; constructor sets `1/0`. |

The step `FUN_003B2270` first rewrites every destination entry in the selected
range from the snapshot, reflecting the shifted source index at the range
ends. For a 256-entry palette it maps both indexes through the same
`0x003FB720` CSM1 permutation used by the parser; smaller palettes use direct
indexes. The reflection loop allows five correction attempts before a trap.
It then adds the float increment. Only when the accumulator is strictly
greater than `1.0` does it increment the integer shift once and subtract
`1.0` once. This is one shift per call even if the increment exceeds one.
When the shift reaches twice `range_length-1`, repeat wraps it by that amount;
without repeat the completion byte becomes one. The next call skips a
completed controller. This helper does not itself submit a transfer.

`FUN_0039A150` constructs this controller from a named record in the script
owner's CCS at owner `+0x38`, consumes four scalar arguments after the name,
sets repeat, installs the range and float controls, and attaches its wrapper
to the owner's selected list. Wrapper update `FUN_0039A110` sets controller
increment to `wrapper +0x2C * owner +0x08`, then steps it. Instructions
`0x0039A118..0x0039A134` corroborate that product. The units of owner `+0x08`
and the complete scheduler calling frequency have not been established here.
Vtable `0x005DD280` contains this update at `+0x08`, initializer at `+0x14`
and destructor `FUN_003AA4A0` at `+0x24`. The destructor restores snapshot
colors through `FUN_003B2130`, frees the snapshot/controller, and delegates
wrapper cleanup. It does not own the borrowed palette.

### RGB-table interpolation

**Observation, high confidence; caller ownership unresolved.**
`FUN_003B2580` builds a second controller. It borrows palette pixel storage
when present. If absent it constructs a new `0x28`-byte CLUT at the original
palette base and allocates storage, recording that owned CLUT in controller
`+0x00`. Controller `+0x08` is writable colors, `+0x0C` is an original
snapshot, `+0x10` is a derived target table, and halfword `+0x04` is the
palette width-times-height count. The input vector is copied to `+0x20`.

`FUN_003B28F0` derives each target RGB from a weighted source RGB sum using
three coefficients at `0x005D6260..0x005D6268`, multiplied by controller
`+0x20/+0x24/+0x28`. It preserves source alpha. `FUN_003B2500` rebuilds
that target table. `FUN_003B2760` interpolates each RGB channel using caller
float `t`, `original + t*(target-original)`, again preserving original alpha.
It does not clamp `t` in this body. Instructions `0x003B2894..0x003B28B4`
confirm each color store is followed by a call to `FUN_0010F860` when an
owned CLUT and descriptor exist; that call is inside the entry loop. Borrowed
storage receives no such immediate submission in this helper.

Cleanup `FUN_003B2470` destroys an owned CLUT, copies original colors back,
and frees both tables. The inspected instruction order frees an owned CLUT
before copying through controller `+0x08`; its intended validity for that
branch is not established. No direct `jal` encoding for initialization
`FUN_003B2580` or stepping `FUN_003B2760` was found in resident ELF, BTL or
ETC, and no literal pointer was found in resident ELF. This is a bounded
negative result, not proof that retail cannot reach these helpers through
computed addresses or another unexamined owner.

## Sampling texture resource consumer

**Observation, high confidence.** Sampling virtual method `FUN_0019DCD0`
returns immediately when render width at global context `+0x08` exceeds
`512`. Otherwise it halves current render width and height separately until
each fits texture `+0x32/+0x34`, then builds a textured rectangle from the
current framebuffer to the texture's composed destination state. There is no
time counter or frame-index advance in this method; each call produces work
for the current source framebuffer.

Disassembly `0x0019DD6C..0x0019DDCC` identifies source base at render context
`+0x19C` and format at `+0x1AC`, combined with constants `0x20000` and
`0x664000000`. `FUN_001C81E0` takes composed texture state as destination:
it derives framebuffer register `0x4D` from its base/width/format, sets
scissor `0x41` from its dimensions, and writes source texture register
`0x07`. `FUN_001C85D0` draws source/destination rectangles, with filter flags
supplied by the caller; the sampling method uses zero flags and color
`0x80808080`. This establishes framebuffer sampling into texture storage,
with the width gate and halving behavior above. The packet is inserted into
the supplied draw chain; allocation/chain lifetime belongs to
[Render submission](render_submission.md).

For comparison, ordinary slot `FUN_001190D0` checks texture `+0x28`, passes
`extra_levels+1` in `t0` (`0x001190E4..0x001190F4`), and calls the descriptor
array submission gate. The decompiler omits that fifth argument. Sampling
therefore changes what resource preparation does while preserving the same
draw-consumer virtual interface. Constructor/copy clears sampling `+0x48`,
but no producer or consumer of that additional field is established here.

The asset investigation establishes locally defined `TEX_sampling00` and
`TEX_sampling01` rows in `CMN/EFFECT0X.CCS`, and a startup load set containing
that file. See [Locally filled external-marker rows](../game/files/asset_dependencies.md#locally-filled-external-marker-rows)
and [Common providers and battle preparation](../game/files/asset_dependencies.md#common-providers-and-battle-preparation)
for the file evidence and load edge. Those observations establish available
definitions; this consumer trace does not establish which draw instances
use each named sampling resource.
