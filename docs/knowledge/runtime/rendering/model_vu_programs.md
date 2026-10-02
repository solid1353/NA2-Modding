# Model VU programs

This document investigates the VU uploads, microprogram entrypoints, geometry
operations and output packets of the retail NA2 (`SLPS-25837`) model renderer.

## Research coverage

- **Assigned scope:** Native model VU upload streams, entrypoint selection, geometry, normal and weight operations, and VU output packet contracts.
- **Exploration depth:** Resident renderer/geometry-producer tracing, descriptor initialization and all 42 distinct nonnull descriptor upload streams; instruction-level interpretation of representative ordinary, packed weighted/rigid, lighting and clipping bodies. Six complete retail body-model payloads were inspected for influence distributions. Selected reader/converter controls were joined to the packed ADC and shared offset consumers; sampled headers were joined to selector producers; palette, batch and selected clipping bounds were traced through their writes and loop endpoints.
- **Confirmed coverage:** Upload boundaries, conditional descriptor selection, shared setup and continuation, weighted position/direction accumulation, direction normalization, representative lighting and GIF packet layouts, projected-triangle sign controls, first-influence strip controls and opposite winding seeds in the selected shared offset consumer, and a complete six-pass clipping/interpolation body. The six inspected body models have one weighted part each; all their observed weight lists sum to 256. Weighted palette addressing represents 64 matrices; the selected clipping body fits up to nine finite convex result vertices. The weighted batching threshold alone does not bound arbitrary influence lists to its packet region.
- **Unresolved or untested:** Character-specific draw histories and later selector-state changes; control semantics beyond the selected consumers and observed 0/1/2 domain; exceptional arithmetic inputs; a full semantic trace of every variant; and asset-level maximum supported influence lists and palette counts. Representable/storage bounds are distinguished from enforced validity contracts.
- **Deliberate exclusions and overlap:** [Model runtime](model_runtime.md) owns CPU model readers, skeletons and morphs; [Render submission](render_submission.md) owns DMA chain lifetimes; [Renderer coordinates](renderer_coordinates.md) owns CPU transform state; [Texture and material runtime](texture_material_runtime.md) owns CPU material state; [Visibility](visibility.md) owns scene and whole-model admission; [Shadow rendering](shadow_rendering.md) owns its separate producer family.
- **Evidence limitations:** Static inspection of retail resident `SLPS_258.37` and a bounded sample of retail NA2 character CCS files. Working function names are analysis names. Ghidra imports the resident executable as `r5900:LE:32:default`; embedded VU instruction pairs must be distinguished from EE instructions and VIF command words. Code and asset presence do not establish measured execution or a roster-wide distribution.

## Evidence conventions

Resident EE addresses refer to retail `SLPS_258.37`; see
[address conventions](../../game/files/file_identities.md#address-conventions). VU instruction
addresses and VU data slots are separate address spaces and will be identified
explicitly. Findings concern the inspected static paths and do not prove that
every descriptor or geometry mode is used by a particular retail character.

## Initial upload boundaries

**Observation:** packed producer `FUN_0018ffb0` and ordinary setup producer
`FUN_00192ae0` calculate a descriptor address as
`0x005BEEC0 + 0x10 * (context_halfword_1f0 + context_byte_264 + context_byte_265)`.
They emit a REF tag pointing to descriptor `+0x08`, with QWC derived from
descriptor `+0x0c >> 4`. Descriptor `+0x00` supplies the GIF register list,
and `+0x04` supplies the VU instruction entrypoint ORed into `MSCAL`.

**Observation, high confidence:** static initializer `FUN_005d6a30` writes
the table's entrypoints and lengths. For example, instructions
`0x005D6B04..0x005D6B44` set descriptor `0x005BEEC0` entrypoint to zero
and calculate length `0x280` from EE stream start `0x003BDD90` and exclusive
end `0x003BE010`. Thus the imported zero lengths are pre-initialization data,
not proof that drawing skips the upload. The last descriptor entrypoint write
in this initializer is at `0x005BF734`, descriptor index 135 (`+0x04`).
The inspected descriptor range is therefore `0x005BEEC0..0x005BF73F`,
including gaps and null-pointer entries; these are not assigned geometry names.

The descriptor-selected nonnull streams inspected in
`0x003BDD90..0x003CEA2F` upload at VU instruction `0`, with further `MPG`
segments at instruction `0x100` for programs longer than 256 pairs.
Instruction pairs are eight bytes: lower word first, upper word second.
For example `0x003BDD94` contains `0x4a4f0000`, uploading 79 pairs at
instruction zero, while `0x003C86C4` contains `0x4a000000`, uploading 256,
followed at `0x003C8ECC` by `0x4ad40100`, uploading 212 more at `0x100`.
The zero `MPG` count means 256, not zero. All extents here count actual pairs;
rounded DMA payload lengths also include command words and padding.

**Observation:** the frame prefix at EE `0x003CEA30..0x003D11DF` installs
the following shared VU1 instruction regions. [Render submission](render_submission.md#frame-chain-and-vif1-submission)
owns how that prefix enters the frame DMA chain.

| `MPG` word address | VU instruction start | Pair count | Last instruction |
| --- | --- | --- | --- |
| `0x003CEA34` | `0x300` | 92 | `0x35b` |
| `0x003CED1C` | `0x35c` | 252 | `0x457` |
| `0x003CF504` | `0x458` | 215 | `0x52e` |
| `0x003CFBC4` | `0x52f` | 239 | `0x61d` |
| `0x003D0344` | `0x61e` | 137 | `0x6a6` |
| `0x003D0794` | `0x6a7` | 95 | `0x705` |
| `0x003D0A94` | `0x706` | 139 | `0x790` |
| `0x003D0EF4` | `0x791` | 91 | `0x7eb` |

The prefix finishes with `BASE 0` and `OFFSET 0x200` at
`0x003D11D0/0x003D11D4`. Upload destinations are instruction indexes, not
resident EE addresses or VU data slots. Shared code is above the replaceable
low program region; this address relationship is established by the uploads.
It does not assign every shared body to the model renderer.

Ghidra's resident import does not expose these pairs as VU disassembly. The
resident bytes are decoded with the PCSX2 source tables in
`pcsx2/DebugTools/DisVUmicro.h`, `DisVUops.h` and `DisVU1Micro.cpp`.
`VU1microInterp.cpp` corroborates the upper I bit (lower word is an immediate
float) and E bit; `Vif_Codes.cpp` corroborates `MPG` count and address units.

The packed producer additionally uploads the matrix palette described in
[Model runtime](model_runtime.md#packed-geometry-influences-and-matrix-palette);
its VU consumer is described below.

## Packed influence evaluation

**Observation, high confidence:** the low programs at EE `0x003C86C0`
(468 pairs), `0x003C9580` (398), `0x003CA210` (372) and `0x003CADD0`
(364) include weighted and rigid palette paths. Each body is selected through
the common descriptor table. In the first body, VU instructions
`0x008..0x00e` read TOP, the header Z lane and header
Y endpoint; doubling Z in a 16-bit integer register distinguishes the first
rigid batch's `0xc000` marker from the weighted batch's `0x8000` marker.
The rigid branch begins at instruction `0x0fd`; subsequent continuation
entrypoints preserve the chosen setup instead of interpreting every batch as
a fresh first batch.

The weighted converter `FUN_001ae950` emits these interleaved inputs relative
to the batch TOP. Control, direction and position use influence index `i`;
UV uses logical-vertex index `v`, already occupying the slot needed after
compaction. The producer's instructions establish the VIF words.

| Slot relative to TOP | Input meaning in the inspected weighted path | Producer command |
| --- | --- | --- |
| `0` | Header; logical-vertex endpoint is `4 * vertex_count + 1` in Y | `0x6c01c000` |
| `1 + 4*i` | X: low-nine-bit weight shifted left four; Y: palette address `0x50 + 4 * bone_index`; Z: influence count at a list start, one thereafter | `0x6900c001` plus count |
| `2 + 4*v` | Masked per-vertex UV halfwords; later used by compacted logical vertices | `0x7500c002` plus count |
| `3 + 4*i` | Three signed byte direction components and a fourth control byte | `0x6e008003` plus count |
| `4 + 4*i` | Float XYZ position | `0x68008004` plus count |

VIF cycling scatters the streams into these interleaved slots. Producer
evidence is `0x001AEAA4..0x001AEB98`, `0x001AECE0..0x001AECF0`,
`0x001AEE90..0x001AEED0` and `0x001AF038..0x001AF09C`. The CPU reader,
influence terminators and original halfword position scaling are owned by
[Model runtime](model_runtime.md#packed-geometry-influences-and-matrix-palette).

**Observation — arithmetic:** in the `0x003C86C0` body, VU instructions
`0x02d..0x04d` load a list count, matrix address, weight, direction and
position. They transform position by the matrix's XYZ columns plus translation
(`MULAx`, `MADDAy`, `MADDAz`, `MADDw`), transform direction by XYZ columns
without translation, and multiply **both** results by the weight before adding
to separate accumulators. Weight conversion is `ITOF12` of the shifted value,
so the decoded multiplier is `encoded_low_nine_bits / 256`. Direction bytes
are converted by `ITOF0`; they are not first divided by 64 in this VU loop.

For example, the `MADDx.xyz` upper words at EE
`0x003C88BC/0x003C88CC` are the two weighted accumulator writes in this
body. The equivalent position/direction pair is at VU `0x049/0x04b` in
the `0x003C9580` body and `0x045/0x047` in `0x003CADD0`. Thus weighting
the direction is repeated evidence across program variants.

VU `0x04e..0x054` computes the direction sum's squared XYZ length, obtains
its reciprocal square root through `ERSQRT`/`WAITP`/`MFP`, and multiplies the
sum by that reciprocal. It writes normalized direction and accumulated
position into a compacted four-slot logical-vertex record at
`0x056/0x058`. The output endpoint uses logical vertices, while the input
cursor advances once per influence. The loop performs no division of position
by a weight sum. Zero-length direction handling is not established as an
asset-level contract.

**Observed distinction:** this VU weighted-direction accumulation differs
from [Property geometry and CPU skinning](model_runtime.md#property-geometry-and-cpu-skinning),
whose inspected CPU direction loop omits the position weight multiplier.
Neither route's arithmetic should be substituted for the other.

**Observation — rigid path:** VU `0x0fd..0x11e` reads the shared matrix
address from header W, loads its four columns, composes them with the global
position matrix, and separately combines its three direction columns with
the global direction matrix. VU `0x11f..0x127` obtains three reciprocal square
roots used in direction setup. The rigid packet producer supplies
`0x50 + 4 * selector` in header W (`0x001AFAC0..0x001AFAC4`,
`0x001AFB98..0x001AFBA0`). This is a separate single-matrix path; its
vertex stream does not contain per-influence weights.

## Entrypoint selection and continuation

The resident direct callers of dispatcher `FUN_001910e0`
are `FUN_00190f40` and `FUN_001994f0`. The dispatcher directly calls ordinary
setup `FUN_00192ae0`, material/entrypoint setup `FUN_00192740`, and packed
delegate `FUN_0018ffb0`. These edges locate the program selection in the
model draw family; they are not an overlay-wide or indirect-caller census.

**Observation:** the descriptor index is assembled in `FUN_001910e0`.
Context halfword `+0x1f0` starts as the bounded visibility result minus one,
then gains two when runtime flag `0x10000` is set. Context byte `+0x264`
starts at zero, becomes four for the ordinary direction/light setup, or eight
for the alternate attachment path. Its optional increment by `0x10` is gated
by draw-base byte `+0x124`, a selector below five and an odd `+0x1f0`.
This gate selects the longer clipping bodies. Instructions
`0x00191308..0x001913A0` and `0x0019165C..0x00191690` establish these writes.

Context byte `+0x265` adds `0x18` for packed model flag `0x04` and `0x30`
for CPU-evaluated property model flag `0x0800`. It can first gain `0x48`
from the selected runtime flag mode, which also writes `-1.0` or `+1.0` to
context `+0x11c` (`0x00191574..0x0019162C`). The corresponding programs
must be distinguished even when their upload pointers are shared.

The selected mode comes from runtime flag bits `0x01800000` shifted by 23
when context alpha `+0x114` is below `0.9921875`, or bits `0x00600000`
shifted by 21 otherwise. Mode 1 adds the bank and writes `-1.0`; mode 2
adds it and writes `+1.0`. These are instruction-derived selection values,
not names assigned to those flag fields.

| Descriptor indexes | Static selection and upload relationship |
| --- | --- |
| `0..3` | Four short ordinary bodies at `0x003BDD90`, `0x003BE020`, `0x003BE3A0`, `0x003BE640`; entry zero |
| `4..7` | Ordinary direction/light bodies at `0x003BF2A0`, `0x003BF890`, `0x003BFE70`, `0x003C0230`; entry zero |
| `8..11` | Two alternate bodies, pointers repeated by index parity (`0x003C24B0` / `0x003C1B10`) |
| `12..15` | No upload pointer; shared-code entrypoints `0x61f` / `0x6a8` by parity |
| `16..19`, `20..23` | Two longer clipping bodies (`0x003C2890`, `0x003C3250`), repeated pointers across four selectors |
| `24..31` | Packed direction/light bodies (`0x003C9580` / `0x003C86C0`); pointer selected by parity |
| `32..35` | Packed alternate bodies (`0x003CADD0` / `0x003CA210`) |
| `36..39` | No upload pointer; shared-code entrypoints `0x459` / `0x35c` |
| `48..59` | Property-evaluated ordinary/alternate programs; CPU output supplies float geometry |
| `60..63` | No upload pointer; shared-code entrypoints `0x707` / `0x792` |
| `72..135` | Parallel descriptor bank selected by the additional `0x48`; shared clipping pointers and separate direction/packed variants, with shared-code entrypoints in the corresponding positions |

This table records selectors and byte evidence; it does not invent names for
the visibility-result variants or claim every slot is reached by a character.
The initialized table has further empty slots in each bank.

**Observation:** ordinary setup `FUN_00192ae0` uploads 17 vectors beginning
at VU data slot zero and starts shared instruction `0x304` (`0x14000304`).
Shared VU `0x304..0x31e` loads global position columns from slots `0..3`,
direction columns from `8..0xa`, and vectors from `4..7` and `0xc..0x10`.
It computes componentwise sums of squared direction-column components and
obtains three reciprocal square roots. This setup does not itself apply a
per-vertex position or emit geometry. It ends with E at `0x31d` and a delay
pair at `0x31e`.

The ordinary geometry chain contains `MSCNT` (`0x17000000`), so drawing
continues after a program's E pair rather than issuing `MSCAL` for every batch.
For example the short `0x003BDD90` body finishes its draw at VU `0x047/0x048`,
then its continuation `0x049..0x04e` reads the next TOP/header and branches
back to `0x00a`. The packed `0x003C86C0` body's rigid draw finishes at
`0x1c5/0x1c6`, then `0x1c7..0x1d3` uses the next header to continue rigid
processing or switch back to weighted initialization. Its weighted draw has
the corresponding continuation at `0x0f2..0x0fc`. Matrix setup and batch
continuation therefore have distinct lifetimes within the uploaded program.

## Shared direction-offset programs

**Observation:** the null-upload descriptor groups above use GIF register
list `0x5fff`: three NOP slots followed by XYZ2. Their shared bodies change
position using the input direction as an offset. This is a separate operation
from using direction to calculate RGB in the ordinary lighting programs.

At shared VU `0x61f`, setup loads scalar `s` from data slot `0x14.x`.
Instructions `0x625..0x635` multiply the global position matrix's three XYZ
columns by `s`, convert the input direction with `ITOF0`, and accumulate
those scaled columns times direction before adding the ordinary `ITOF12`
position and translation. In mathematical notation, the homogeneous result
is `M * [p + s*n, 1]`, where `p` and `n` denote these converted inputs.
It then divides by W and emits XYZ2. The `0x6a8` body applies the same
position-offset construction and additionally checks plane flags.
The float-property entries `0x707/0x792` consume float position and direction
without those ordinary conversions; `0x713..0x719` is the corresponding
accumulation at `0x707`.

Shared packed entry `0x35c` has the same first-header split between weighted
and rigid palette paths as the replaceable packed programs. Its weighted
loop at `0x380..0x3ab` accumulates position and direction with the encoded
weights, normalizes direction, and compacts logical vertices. VU
`0x3ac..0x3b7` then combines the compacted position and normalized direction
using columns scaled by data slot `0x17.x`. Its rigid branch at `0x3e9`
composes the palette matrix and uses data slot `0x18.w` for its scaled
position columns, with `ITOF0` direction input at `0x41d`.
Entry `0x459` also has weighted and rigid paths (`0x479..0x4a4` and
`0x52f`), followed by the direction-offset position construction.
These entries reuse the frame-installed code; their zero upload pointer
does not mean a missing geometry program.

The scalar writers and their higher-level rendering purpose are not inferred
from these calculations. CPU setup `FUN_00192740` supplies the ordinary
slot `0x14.x` value from renderer `+0x138`; its slot `0x15` also supplies
the selected descriptor register list and triangle-sign parameters.

## Projected-triangle sign controls

**Observation, high confidence:** the additional `0x48` descriptor bank
selects bodies with projected-XY edge calculations and sign-dependent XYZ2
controls. For example, ordinary body `0x003C48F0` subtracts successive
post-divide positions, scales XY edges, and uses `OPMULA`/`OPMSUB` to form
the cross-product sign (`0x01f..0x030`, `0x038..0x042`). `FMAND 0x20`
extracts the MAC Z sign bit; that value is added to the source-derived
integer control before writing XYZ2 W (`0x036..0x037`, `0x047..0x048`).
PCSX2 `VUflags.cpp` and `VUops.cpp` corroborate the bit and cross-product
operation. Even with destination `vf0`, `OPMSUB` produces MAC flags.

CPU setup `FUN_00192740` writes context `+0x11c` into data slot `0x15.x`
and `-1.0` into `0x15.w`. This body loads both, multiplies its XY edges by
the X scalar and flips that scalar by W as the strip advances. Thus the
dispatcher's `+1.0/-1.0` selects the initial sign convention while the
program accounts for alternating strip winding. The sign contribution is
added to an integer derived with `+0x7fff`; it can affect XYZ2's ADC bit
through that addition, rather than through a direct bit-15 OR.

Packed parallel body `0x003CB950` combines this sign contribution with
the rolling plane flags and source control adjustment. For example,
`0x0c0..0x0cc` includes cross-product flags, `FMAND 0x20`, the flag ANDs,
and additions before its W writes. The inspected short base ordinary body
`0x003BDD90` lacks this edge/cross-product family. The selected 0/1/2 control
consumers are derived in [Source strip controls](#source-strip-controls-and-their-selected-consumers);
this does not assign every source byte across every variant.

## Geometry, direction and GIF output

**Observation, high confidence:** the short ordinary program at
`0x003BDD90` uses signed fixed-point XYZ converted by `ITOF12`, four matrix
columns in `vf1..vf4`, and `DIV Q, vf0.w, transformed.w`. XYZ is multiplied
by Q and converted with `FTOI4`; UV XY is converted with `ITOF12` and
multiplied by the same Q. Its alpha lane is converted to float, multiplied
by the setup scalar, then converted back to integer. Evidence is VU
`0x00e..0x024` and the one-vertex final path `0x040..0x046`.
The float-position property body at `0x003BE8B0` uses
`MULAx`/`MADDAy`/`MADDAz` directly on float XYZ (`0x00e..0x012`).

The ordinary direction/light program at `0x003BF2A0` converts its three
direction bytes with `ITOF0`, multiplies them by `vf5..vf7`, clamps each
result component against zero, then uses `vf9..vf11` to form RGB and adds
`vf12` (`0x01c..0x032`). It applies an upper RGB limit from `vf12.w`, then
`FTOI0`. This establishes a direction-driven color operation; the CPU writer
of those light/ambient parameters belongs to the material/renderer owners.
Packed `0x003C86C0` performs the same two matrix stages after normalizing its
weighted direction; its inspected color conversion clamps through immediate
`255` before `FTOI0` (VU `0x068..0x08b`). Neither sequence establishes an
inverse-transpose normal transform for arbitrary nonuniform matrices.

The alternate ordinary bodies do not perform that full RGB matrix chain.
For example, `0x003C24B0` loads the direction coefficients from data slot
`0x16`, scales them by immediate `1/64` (VU `0x003..0x00a`), converts
direction bytes with `ITOF0`, and forms a scalar dot product in Y
(`0x01f..0x022`). It clamps that result against zero and uses it in the
texture-field arithmetic. The float-property alternate body at
`0x003C17B0` uses float direction and the unscaled coefficients
(`0x004..0x009`, `0x017..0x01c`). This is evidence for different direction
scaling across these routes, not a universal byte-to-normal convention.

**Observation — alternate output passes:** ordinary `0x003C24B0` writes
both the usual UV-derived STQ and a second texture vector whose Y is the
clamped direction dot product plus coefficient W; its X/Z are set through
`MR32.xz vf0` (`0x02f..0x033`, `0x03e..0x048`). The latter vector therefore
has S zero and Q one in the inspected path. At `0x054..0x05d`, the program
kicks state packet `0x20`, sets the geometry header's register list to
`0x512f` and kicks it, then kicks state packet `0x30`, changes the same
header to `0x5ff2` and kicks it again. The second list is STQ, NOP, NOP,
XYZ2, consuming the extra texture vector in the first slot. The first pass
consumes the usual STQ/RGBA slots. Thus one geometry batch is submitted twice
with distinct state and register selection.

The ordinary alternate continuation at `0x05f..0x079` copies the previous
batch's last two four-vector output records into the next output region and
adds two to the new header count; that region's header begins at TOP `+0xc9`
to precede the copied records. The `0x003C1B10` and float-property
`0x003C17B0` bodies contain the same two-kick and two-record continuation
families. Their plane-flag operations are additional to this two-pass layout.

Packed alternate `0x003CADD0` also changes the same batch's list from
`0x512f` to `0x5ff2`, with a state-packet `0x30` kick between its two
geometry kicks (`0x090..0x097`). Its weighted continuation copies the last
two output records before the next batch TOP, places the new header at
TOP `-8`, and increments its count by two (`0x0a2..0x0bc`); the rigid
continuation has the matching family at `0x14b..0x165`. The ordinary
TOP `+0xc9` continuation location must therefore not be used for this packed
body.

**Observation — packet layout:** descriptor word `0x512f` names four packed
GIF registers in nibble order: NOP, STQ, RGBA, XYZ2. Word `0x512a` replaces
NOP with FOG and leaves the other three slots in the same order. These
register identities are corroborated by PCSX2 `GS/GSRegs.h`. STQ carries
perspective-correct S/T and Q; XYZ2 receives the post-divide `FTOI4` XYZ
words. RGBA receives the resulting integer color lanes.

The short ordinary body creates its output header at TOP `+0xd1`, puts the
four output slots after it, and kicks that header with `XGKICK vi1` at
VU `0x047`. For the one-vertex path the STQ, RGBA and XYZ2 writes are at
VU `0x045`, `0x043` and `0x046`. It copies the output count from header X;
the first GIF slot is ignored when the selected register nibble is NOP.

The packed body instead compacts logical vertices and overwrites their input
UV/direction/position slots with STQ/RGBA/XYZ2. It updates header Y/Z from the
descriptor/setup vector and kicks the batch TOP itself (`XGKICK vi3` at
`0x0f0`, or `0x1c5` on the rigid path). This is an in-place output contract,
distinct from the ordinary output region at TOP `+0xd1`.

Control values written to XYZ2 W contribute its ADC bit, bit 15 of that
32-bit lane. PCSX2's packed XYZ2 consumer uses it to suppress the current
primitive while advancing strip vertex history.
The VU combines source strip controls with computed plane flags; this is not
equivalent to a single model-level visibility decision. Packed instructions
`0x098..0x0c1` include the `0x7f31` control adjustment, rolling flag ANDs
and W writes before the final kick. The selected control consumers are
derived below.

## Source strip controls and their selected consumers

**Observation — preserved input:** weighted reader `FUN_001ae190` keeps one
attribute dword per influence. Converter `FUN_001ae950` copies those dwords
unchanged into the `0x6e008003` stream (`0x001AECE0..0x001AECF0`,
`0x001AEE50..0x001AEE78`). In the `0x003C86C0` weighted body,
`LQ.w vf17,2(vi2)` at VU `0x037` takes W from the **first influence** of
each logical vertex. Subsequent direction loads, transforms and normalization
write only XYZ; `SQ.xyzw vf17,-2(vi4)` at `0x058` therefore preserves that
first influence's control in the compacted logical-vertex record. Controls
on later influences are not substituted for it or combined with it.
The consumed byte is the converter input **after** any CPU strip normalization;
`FUN_001aff20` can call `FUN_001ae430` between reading and converting. Original
asset order and controls therefore cannot be substituted for the final packet.

**Observation — base packed ADC:** the source byte `c` is loaded from the
compacted direction/attribute W lane, then the integer operations compute

`XYZ2.W = (c - 0x7f31 - R) mod 65536`.

Here `R` is the rolling AND of the current and previous two vertices' X/Y/W
comparison masks. Each mask ANDs MAC sign bits from `vf13 - projected_position`
and `projected_position - vf14`, using mask `0xd0`; setup loads `vf13/vf14`
from slots `0x0c/0x0d`. XYZ has undergone perspective division while W retains
the homogeneous value. This is a sign-bit contract, including boundary and
signed-zero sensitivity, rather than an assertion about exceptional arithmetic.
The initial previous masks are `0xd0`. VU `0x089..0x0a4` advances the rolling
AND; `0x098/0x09a/0x09d` is a repeated control read/adjust/write, and
`0x0a9..0x0c1` drains the final three pipelined vertices with the same equation.
The one- and two-vertex tails at `0x0c2..0x0ef` retain this calculation.

| First-influence control | W when `R == 0xd0` | ADC bit | Selected base-body effect |
| --- | --- | --- | --- |
| `0` | `0x7fff` | clear | permits the strip's current primitive kick |
| `1` | `0x8000` | set | advances strip vertex history while suppressing its primitive kick |
| `2` | `0x8001` | set | same ADC result as 1 in this body |

A focused read of `2NRTBOD1.CCS`'s weighted part at decompressed `0x12bb68`
joins this to the previously inspected payload: its first logical controls are
`1,1,0,0,2,2,0,1,1,0,0,1,1,0,0,2,2,0`. All later-influence controls match
their own list's first control in this part, and its payload still ends at
`0x130f00`. The paired nonzero markers provide the two history vertices needed
at strip starts. This is a source observation for one selected part; optional
normalization may change these pairs and their order before VU consumption.

**Derived bound:** for `c` in the observed domain `{0,1,2}`, any `R` that is
a proper subset of `0xd0` leaves bit 15 set: the smallest resulting value is
`0x800f` (`c=0`, `R=0xc0`). Thus control 0 permits a kick only when all three
rolling masks retain all X/Y/W bits. This body does not interpolate a triangle
that crosses one of these comparisons. The GS strip-history behavior is
corroborated by PCSX2 `GSState.cpp`'s packed XYZ2 and skipped triangle-strip
handling; ADC suppression does not discard the input vertex from strip history.

**Observation — why 1 and 2 remain distinct:** shared packed offset entry
`0x35c` reads the same first-influence control after compaction. At
`0x3b9..0x3c0`, a nonzero control becomes `2*c - 3`, is transferred with
`MFIR.w` and converted with `ITOF0.w`, then multiplied by the setup value
`-1.0`. Control 1 sets the rolling projected-edge factor to `+1.0`; control 2
sets it to `-1.0`. Both retain a nonzero control for ADC suppression. Control 0
takes `0x3c1..0x3cc`: the program evaluates the projected XY determinant using
the previous two positions and that factor, flips the factor for the following
strip vertex, and changes `c` to 1 when its selected MAC X sign bit is clear.
The subsequent `0x3cd..0x3d9` uses the same `0x7f31` and rolling-mask equation.
The rigid path repeats this at `0x426..0x446`, consuming its per-vertex W byte.
This establishes opposite strip-winding seeds in this consumer; it does not
assign coordinate-independent clockwise/counterclockwise names.

CPU strip normalization treats a nonzero first-attribute control as the start
of a run and scans from its third vertex through following zero controls.
`FUN_001ae430` examines `(run_start + inserted_vertices) & 1`: it corrects
control 1 on even parity and control 2 on odd parity, reversing a run and
switching 1/2 when the endpoint parity permits, otherwise inserting a duplicate
first vertex. These producers corroborate the strip-start/parity interpretation;
[Model runtime](model_runtime.md#ordinary-geometry-and-strip-conversion) owns
the normalization and array changes. The short ordinary VU body at
`0x003BDD90` instead reads its ordinary packet's control W and adds `0x7fff`
(`0x010..0x015`), also separating 0 from the two nonzero markers at ADC bit 15.
Neither consumer proves that all variants use identical winding calculations
or that every byte outside the observed domain is invalid.

## Clipping and interpolated output

**Observation, high confidence:** the complete 309-pair program at
`0x003C2890` preserves transformed homogeneous positions, float colors and
texture data before projection. It forms plane-sign masks using MAC flags,
keeps masks for successive strip vertices and marks selected triangles for
further work. VU `0x054..0x070` saves/restores its working state in fixed
data slots `0x72..0x74`; `0x083..0x08e` copies three vertices into scratch
slots starting at `0x77`.

VU `0x08f..0x0bf` makes six calls to the same polygon pass at `0x0ef`,
alternating scratch starts `0x77` and `0x95`. It uses vectors loaded into
`vf30/vf31` from setup slots `0x0f/0x10`, and sign masks `0x20`, `0x40`,
`0x80` for the Z, Y, X comparisons. The pass copies retained vertices and
inserts a new vertex when an edge changes side. Its intersection routines
at `0x11c`, `0x121`, `0x126` calculate a Q ratio from the relevant coordinate
and W differences; `0x129..0x130` applies that same Q to homogeneous position,
color and texture-field differences and stores all three interpolated vectors.
This is evidence of clipping and attribute interpolation, not merely a
whole-triangle reject flag.

When a pass returns zero vertices the caller skips further processing for
that triangle. Otherwise `0x0cc..0x0ec` projects the result, converts color
and XYZ, writes a four-register GIF packet starting at data slot `0xb3`,
and kicks it. The first two XYZ2 controls are marked to start the new strip.
Scratch starts `0x77/0x95/0xb3` are 30 slots apart; this spacing alone does
not prove a general maximum polygon count or an overflow guard. The selected
pass's count and closing-edge writes provide the tighter bound below.

The longer neighboring program at `0x003C3250` is 327 pairs and includes
direction/light work before a homologous interpolation family. The full
plane/intersection derivation above is bounded to `0x003C2890`; it should
not be assumed for every short or packed variant without its own body trace.

### Selected clipping scratch bound

**Observation — exact loop bounds:** the caller seeds exactly three vertices,
each with three vectors, at `0x083..0x08f`. On entering the polygon pass,
`0x0ef..0x0f1` computes `input_end = input_start + 3 * input_count`.
`0x0f2..0x0f8` copies the first three-vector vertex to that endpoint so the
last edge can read its successor without a separate wrap branch. The loop
reads one edge per input vertex and finishes when its cursor equals that
endpoint (`0x131`). An inside vertex increments the output count once and
stores three vectors (`0x10d..0x110`); an edge whose endpoint signs differ
increments it once more for an intersection (`0x12c..0x130`). There is no
comparison against a numeric scratch capacity in this complete pass.

**Inference, bounded to finite convex geometry:** clipping a convex polygon
against one linear half-space adds at most one vertex to its total. Starting
from the selected triangle, the six passes can therefore produce at most
`4,5,6,7,8,9` vertices. This is derived from the producer's triangle and
the consumer's retained-vertex/intersection rules, not the asset sample.
The largest pass input is eight vertices; its nine records including the
closing copy occupy 27 slots. The final nine-vertex result also occupies
27 slots. Both fit the 30-slot intervals `0x77..0x94` and `0x95..0xb2`;
the last pass returns to `0x77`, with its last possible result slot `0x91`.
The largest closing copy is in `0xad..0xaf` in the sixth pass's input buffer.

The final producer writes one GIF header plus four slots per result vertex
at `0x0c0..0x0ec`. At nine vertices its maximum written slot is
`0xb3 + 4*9 = 0xd7`. The count written into the header is the pass's returned
count with the two `0x4000` additions at `0x0c7/0x0c8`; the first two XYZ2 W
lanes are overwritten with nonzero ADC at `0x0e7/0x0e8`. Count bounds and
endpoint writes thus account for both polygon scratch and emitted packet.
This proves conditional space sufficiency for this selected body. It does
not prove behavior for nonfinite arithmetic, a nonconvex input polygon,
or a general ten-vertex interface; none is established as a retail input.

## Packed palette and influence storage bounds

**Observation — palette representation:** the weighted converter extracts
six index bits (`byte_7 >> 2`) and emits `0x50 + 4*index`; the VU loads four
successive matrix vectors at that address (`0x02e`, `0x032..0x035`). Its
addressable matrix starts are consequently `0x50..0x14c`, with final vector
at `0x14f`: 64 matrices. Packed producer `FUN_0018ffb0` emits exactly
`count` matrices under the palette upload described in
[Model runtime](model_runtime.md#packed-geometry-influences-and-matrix-palette)
(`0x00190500..0x00190520`, `0x001905D0..0x001905E0`; selected-list branch
`0x001905EC..0x00190618`); its VIF NUM field is `(count << 2) & 0xff`.
Counts 1 through 63 request their four-vector matrix totals; count 64 encodes
NUM zero, which VIF interprets as 256 vectors.
Thus 64 is representable, even though the earlier sample stops at 43.

This is not a reader-enforced maximum. The loader's optional palette list
allocates `0x40` bytes but copies the declared byte count without a visible
`<=0x40` check. The draw producer likewise has no corresponding count guard;
larger counts make its emitted matrix total disagree with the eight-bit VIF
NUM after wrapping. A declared count of zero is separately significant: the
producer selects the composition child count instead. No asset-level validity
contract for oversized lists or a zero-child packed draw is established here.
[Model runtime](model_runtime.md#packed-geometry-influences-and-matrix-palette)
owns that CPU list and composition ownership. The rigid converter's shared
selector is a separate source dword; its `0x50 + 4*selector` producer does not
apply the weighted six-bit extraction. No corresponding rigid-selector range
check is established, so the weighted index field alone cannot bound every
rigid source selector.

**Observation — packed batch regions:** converter table `0x005BF988` holds
BASE values `0x158`, `0x23a`, `0x31c`. `FUN_001ae950` selects them by batch
index modulo three, then emits OFFSET zero and `STCYCL 0x0104`
(`0x001AEA68..0x001AEAC4`). Each region has `0xe2` slots before the next
base, or through `0x3fd` for the final region. Palette vector `0x14f` precedes
the first base by eight slots. In the weighted layout the furthest position
write for `I` influences is TOP `+4*I`, while compacted output needs through
TOP `+4*V` for `V` logical vertices. Remaining inside one such region therefore
requires `I <= 56` (and `V <= 56`); this is a storage bound for the inspected
layout, not a limit enforced by its reader or a maximum list-length promise.

The batching rule in
[Model runtime](model_runtime.md#packed-geometry-influences-and-matrix-palette)
includes a vertex and all its influences before checking `3*(I+V)+1 > 0xda`,
so it never splits a list. The converter's two passes both supply total vertex
count in `a2` (instructions `0x001AE974/0x001AE984` and
`0x001AEA34/0x001AEA4C`); both loop continuations reload that count
(`0x001AE9E4`, `0x001AF0A0`).
The reader increments a dword list count until the source terminator and
the converter narrows that count to the emitted halfword. VU
`0x036..0x045` subtracts from the loaded count and traverses all influences
without a numeric maximum check.

**Derived limitation:** the helper's threshold does not by itself ensure
`I <= 56` for arbitrary lists. For example, two lists of 30 influences give
`I=60,V=2`, still below its stop threshold, but require TOP `+0xf0` and exceed
the region. This is a counterexample to inferring universal capacity from
the helper, not an observed retail asset or execution. For lists limited to
the sample's one/two influences, a threshold-crossing batch has `I+V <=75`
and `I <=50`, so its observed input shape fits this region. Rigid conversion
separately caps each batch at `0x36` vertices (`0x001AFB20..0x001AFB30`).
These distinct bounds leave the general supported influence-list domain open.

## Representative retail body payloads

**Observation:** six main body models were read from retail files in `PL/`
below the retail DATA view.
Each CCS has version `0x123`. Offsets below refer to its decompressed bytes,
not its gzip wrapper. The model header's file flags are `0x3804` in all six,
selecting the packed model reader; the listed mode and palette count are
separate header fields. [Character assets](../../game/character_assets.md) owns
the character-file organization, and [Model runtime](model_runtime.md#packed-geometry-influences-and-matrix-palette)
owns the CPU reader contract.

| CCS file | Body model and header offset | Mode | Palette matrices | Rigid / weighted parts | Total logical vertices |
| --- | --- | --- | --- | --- | --- |
| `2NRTBOD1.CCS` | `MDL_2nrt00t0 body`, `0x1247e8` | `0x0440` | 20 | 19 / 1 | 3,062 |
| `2NRVBOD1.CCS` | `MDL_2nrv00t0 body`, `0x17be10` | `0x0440` | 20 | 19 / 1 | 3,062 |
| `2SKRBOD1.CCS` | `MDL_2skr00t0 body`, `0x117ff4` | `0x0240` | 26 | 19 / 1 | 3,588 |
| `2SCOBOD1.CCS` | `MDL_2sco00t0 body`, `0x17c434` | `0x0440` | 24 | 17 / 1 | 3,998 |
| `2SCVBOD1.CCS` | `MDL_2scv00t0 body`, `0x172bf8` | `0x0440` | 24 | 18 / 1 | 4,282 |
| `1NRTBOD1.CCS` | `MDL_1nrt00t0 body`, `0x608c` | `0x0440` | 43 | 30 / 1 | 6,677 |

The complete part payloads were consumed using the inspected reader's rigid
and weighted layouts. Every weighted list terminated, its list count matched
the part's logical-vertex count, and the final payload position in each model
was followed by chunk type `0xcccc0200`. This cross-check bounds the counts
to complete models rather than an arbitrary scan window.

| CCS file | Weighted logical vertices | Influence records | One / two influences per vertex | Highest referenced palette index | Exclusive model payload end |
| --- | --- | --- | --- | --- | --- |
| `2NRTBOD1.CCS` | 976 | 1,457 | 495 / 481 | 19 | `0x130f00` |
| `2NRVBOD1.CCS` | 976 | 1,457 | 495 / 481 | 19 | `0x188528` |
| `2SKRBOD1.CCS` | 1,329 | 2,182 | 476 / 853 | 25 | `0x127818` |
| `2SCOBOD1.CCS` | 1,507 | 2,392 | 622 / 885 | 23 | `0x18d584` |
| `2SCVBOD1.CCS` | 804 | 1,121 | 487 / 317 | 23 | `0x182cc0` |
| `1NRTBOD1.CCS` | 2,628 | 4,382 | 874 / 1,754 | 42 | `0x236d4` |

Across these 8,220 weighted logical vertices, every sum of the encoded
low-nine-bit weights is 256. Combined with the VU's observed `/256` conversion,
this establishes unit-sum position weights for this sample without a VU
weight-sum division. The sample contains one- and two-influence lists only;
that does not establish a two-influence format limit. Likewise, the largest
observed palette has 43 matrices; the code-derived representation and storage
bounds above are separate from this sample distribution.

Two influence records in the `2SCOBOD1.CCS` weighted part have weight zero;
their complete lists still sum to 256. The fourth attribute byte takes only
values 0, 1 and 2 in these 12,991 influence records. Their selected ADC and
strip-winding consumers are derived above; this sample does not establish a
permitted domain for every variant.

**Observation — route variation within files:** `2NRTBOD1.CCS` also contains
weapon model `MDL_w2kn00t0 weapon` at `0x152b00`, with flags `0x3801`, one
part and mode `0x1000`, selecting the ordinary reader. `1NRTBOD1.CCS` contains
`MDL_1nrt00t0 eye1`, `MDL_1nrt00t0 eye2` and `MDL_1nrt00t0 mou1` at
`0x34a0`, `0x3c10` and `0x4380`; their flags and mode are zero and each has
one part. These header observations establish that a body's CCS file need
not use one geometry route for all its models. They do not establish which
VU descriptor each model selects when drawn.

### Sampled headers joined to descriptor selection

**Observation — selector producer:** `FUN_001b0c40` extracts two three-bit
fields from the mode halfword at shifts 6 and 9, turns nonzero fields into
`field - 1`, and places them in runtime flags at shifts 21 and 23
(`0x001B0F68..0x001B0FF4`). For a zero field it instead chooses value 1 when
the parsed flags include `0x804` or `0x80`, otherwise zero. Version `0x123`
also maps mode bit `0x1000` to runtime flag `0x10000`. These are the exact
flags consumed by the descriptor dispatcher's factor-dependent bank choice.
Runtime constructor `FUN_001992a0` copies them to instance `+0x18`, and
`FUN_00198290` copies instance `+0x18` to draw context `+0x20c` immediately
before selection. [Model runtime](model_runtime.md) owns general parsing and
instance construction; this join concerns only their VU selectors.

The following derives initial selector outcomes for the named sampled models,
conditional on admission to `FUN_001910e0`, copied flags remaining unchanged,
and the ordinary direction branch at `+0x264 == 4` rather than an active
alternate attachment for the body/weapon rows. It is not an observed draw.

| Selected source model | Shift-21 / shift-23 values | Base selector and geometry contribution | Conditional descriptor outcome |
| --- | --- | --- | --- |
| Five sampled packed bodies with flags `0x3804`, mode `0x0440` | `0 / 1` | Constructor clears the ordinary box pointer; null-box dispatch chooses classification 2, hence `+0x1f0=1`; direction `+4`, packed `+24` | Factor `>=0.9921875`: index 29, stream `0x003C86C0`; below it: index 101, stream `0x003CB950`, initial sign scalar `-1.0` |
| `2SKRBOD1.CCS` body, flags `0x3804`, mode `0x0240` | `0 / 0` | Same null-box, direction and packed contributions | Index 29 on either side of that factor threshold |
| `2NRTBOD1.CCS` weapon, flags `0x3801`, mode `0x1000` | `1 / 1` from zero-field defaults | Retained classification 1 or 2 plus mode's `+2` gives `+0x1f0=2` or 3; direction `+4`; ordinary route | Parallel bank: index 78 or 79; classification 2 plus enabled draw-base `+0x124` selects index 95 instead |
| `1NRTBOD1.CCS` eye1/eye2/mou1, flags/mode zero | `0 / 0` | Retained classification 1 or 2 gives `+0x1f0=0` or 1; direction contribution zero | Index 0 or 1; classification 2 plus enabled draw-base `+0x124` selects index 17 instead |

Bytes at descriptor 29 (`0x005BF090`) and 101 (`0x005BF510`) confirm
the two body upload pointers. Companion descriptors 78/79 at
`0x005BF3A0/0x005BF3B0` point to `0x003C6F90/0x003C7290`; clipped weapon
descriptor 95 at `0x005BF4B0` points to `0x003C3250`, and clipped eye
descriptor 17 at `0x005BEFD0` points to `0x003C2890`.
The packed branch calls `FUN_0018ffb0` before
reaching the ordinary `+0x10` clipping-selector gate
(`0x001915E8..0x00191610` versus `0x0019165C..0x00191690`). Thus that gate
cannot redirect this packed-body row to the long ordinary interpolation body.
The ordinary companion rows retain their classifier dependency; the sampled
CCS headers alone cannot decide which retained classification occurs.

Draw admission precedes these selectors. Dispatcher `0x00191114..0x00191138`
rejects an empty instance or context factor below `1/128`; a non-null box's
zero classification also returns before packet selection. The ordinary route
then applies the per-part material-factor threshold, while the packed delegate
sets its factor from the first part and emits the packed part chains without
that ordinary loop. [Visibility](visibility.md#ordinary-model-draw-boundary)
owns scene enable and box-classifier gates, and
[Texture and material runtime](texture_material_runtime.md) owns those material
factors. Later flag setters, attachment state, factor values, classifier results
and actual model draw histories remain necessary before assigning a descriptor
to a specific retail scene.

## Remaining evidence gaps

- The descriptor table and dispatcher establish selection formulas, not
  character-specific draw histories. The sampled header join constrains initial
  flags and conditional descriptor outcomes; it does not identify later flag
  changes, factor values, attachment state or an ordinary companion's retained
  visibility classification.
- The selected base packed and shared offset consumers establish the roles
  of controls 0, 1 and 2, including first-influence ownership and optional
  normalization. Other source values, every variant's winding convention and
  exact exceptional sign/boundary behavior remain outside this derivation.
- The companion ordinary, property and parallel-bank streams were decoded
  across their complete upload extents, but the semantic derivations above
  remain tied to their named representative bodies. The six-plane
  interpolation trace is complete for `0x003C2890`; it is not a claim that
  every packed body creates clipped vertices.
- Zero-length or cancelling direction sums, exceptional W/Q inputs and
  arbitrary nonuniform matrices are not established asset-level contracts.
  The code's reciprocal square roots and perspective divisions alone do not
  prove those inputs occur or are handled uniformly.
- Weighted palette addressing represents 64 matrices, but unchecked producer
  counts and rigid dword selectors do not establish a universal asset-validity
  bound. The reader's unsplit list count and batching threshold leave general
  supported influence limits unresolved; the 56-influence region bound is a
  storage condition, not an observed maximum list length.
- The selected clipper's nine-vertex bound depends on finite convex triangle
  clipping through its six linear planes. The body has no numeric output-capacity
  guard; arithmetic degeneracies, rounding and other clipping bodies require separate
  evidence before extending this space-sufficiency claim.
