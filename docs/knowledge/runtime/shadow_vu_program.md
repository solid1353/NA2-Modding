# Shadow VU program

This document investigates the VU shadow program that retail NA2 (`SLPS-25837`)
uploads from resident `0x003C3CA0..0x003C48DF`. The EE controller, target setup
and compositing belong to [shadow rendering](shadow_rendering.md); this document
owns the uploaded microinstructions and their input/output contract.

## Research coverage

- **Assigned scope:** Decode the bounded resident shadow upload, establish its
  VU inputs, outputs and geometric/depth operations, and distinguish it from
  classifier upload `0x003D11E0`. Connect conditional fast edge-output overlap
  to authored topology, exact batch alternation, emission gates and live storage.
- **Exploration depth:** All `0xC40` stream bytes and all 389 instruction pairs
  were decoded. Complete initialization, classification,
  face, edge, near-plane split, four-plane clip and fan-output families were
  traced. The complete EE producer, direct scene caller, topology packet builder
  and normal/edge helpers were inspected, with instructions corroborating
  decompilation and packet constants. Six selected retail body files supplied
  207 selector-4 shadow parts for bounded topology reconstruction and binary-sign
  emission bounds; live clip inputs, convex-list capacities and preliminary
  kick packet extent were traced beyond the upload decode.
- **Confirmed coverage:** Two MPG blocks upload 389 VU instruction pairs at
  entries `0x000..0x184`. Direction signs select displaced faces and shared-edge
  strips; matrix transformation, perspective division, near-depth caps, four
  XY-plane clips and GIF fan output are established. The EE producer references
  this stream separately from the renderer-initialization classifier upload at
  `0x003D11E0`. Edge-family parity restarts at TOP=0; the conditional 21st
  high-TOP emission overwrites three later clip inputs. The selected reconstructed
  high-TOP batches have at most 16 inputs and 13 emissions. Finite convex
  geometry fits the near/XY lists, and the preliminary kick carries three
  quadwords with no vertex payload.
- **Unresolved or untested:** Exact numerical contact/overflow behavior across
  all VU pipeline cases, character/archive distribution of this topology route,
  the physical unit of the projection scalar, and the purpose of the preliminary
  XGKICK at `0x203` remain unresolved. The possible fast edge-output overlap
  described below has not been connected to an actual retail submission;
  none occurs in the selected reconstruction. Hardware normalization agreement,
  unrestricted asset reachability, damaged-packet effects and exceptional
  clipping-list behavior are not established.
- **Deliberate exclusions and overlap:** Controller scheduling, GS target setup
  and compositing remain in [shadow rendering](shadow_rendering.md). General renderer coordinates,
  geometry conversion and classification remain in [renderer coordinates](renderer_coordinates.md),
  [model runtime](model_runtime.md), [render submission](render_submission.md)
  and [visibility](visibility.md).
- **Evidence limitations:** Static retail evidence only. The resident program is
  analyzed as R5900 EE code; raw upload bytes require VIF/VU decoding rather than
  EE disassembly. Resident EE addresses and VU instruction/data addresses must not
  be conflated. Asset reconstruction uses rounded single-precision arithmetic,
  not retail execution; convex count bounds require finite, intact geometry.
  A physical unit for the shadow projection scalar is not yet established.

## Evidence and address convention

Resident addresses are retail `SLPS_258.37` EE addresses; see
[address conventions](../game/files/file_identities.md#address-conventions).
VU microinstruction addresses below count 64-bit instruction pairs; VU data
addresses count 128-bit quadwords.

**Observation:** the resident bytes cover the complete assigned range through
`0x003C48DF`. The first words are `00 00 00 13 00 00 00 4A`;
the next pair at `0x003C3CA8` is lower `0x01E9018F`, upper `0x000002FF`.
The final quadword at `0x003C48D0` is
`3C 03 00 80 FF 02 00 00 00 00 00 00 00 00 00 00`.
These observations establish the bounded bytes, not their complete semantics.

## Upload boundary and entry families

**Observation, high confidence:** `FUN_0018CF70` constructs a DMA REF at its
packet head. Instructions `0x0018D4E8..0x0018D518` subtract start
`0x003C3CA0` from exclusive end `0x003C48E0`, divide the `0xC40`-byte size by
sixteen, and write QWC `0xC4` plus the source pointer. The source xref is at
`0x0018D518`. This is the geometry producer documented in
[shadow rendering](shadow_rendering.md#geometry-inputs-and-renderer-ownership).
The upload is not EE code; it is decoded from its resident bytes with PCSX2's
VU instruction dispatch/operand tables in `pcsx2/DebugTools/DisVUmicro.h` and
`DisVUops.h`. Sony's *VU User's Manual*, version 3.1, supplies primary ISA
evidence: printed pages 37–38 define MAC lane signs and
sticky status signs; pages 76/81 define FTOI4/ITOF12; pages 44, 48 and 51–52
describe Q latency, branch behavior and the E delay pair. VIF commands and
packed GIF fields are checked against Sony's *EE User's Manual*, version 6.0,
sections 6.3/6.4 and 7.3.2. PCSX2 `VUops.cpp`, `VUflags.cpp`, `Vif_Codes.cpp`,
`Vif_Unpack.cpp`, `Gif_Unit.h` and `GS/GSRegs.h` corroborate the individual
field decodes. These source reads establish instruction semantics only.

The complete bounded VIF parse is:

| Resident address | Word or payload | Decoded boundary |
| --- | --- | --- |
| `0x003C3CA0` | `0x13000000` | FLUSHA |
| `0x003C3CA4` | `0x4A000000` | MPG, destination 0, encoded count 0 means 256 pairs |
| `0x003C3CA8..0x003C44A7` | `0x800` bytes | Entries `0x000..0x0FF` |
| `0x003C44A8` | `0x00000000` | NOP |
| `0x003C44AC` | `0x4A850100` | MPG, destination `0x100`, 133 pairs |
| `0x003C44B0..0x003C48D7` | `0x428` bytes | Entries `0x100..0x184` |
| `0x003C48D8..0x003C48DF` | two zero words | NOP padding |

For entry `i < 0x100`, its resident pair address is `0x003C3CA8 + 8*i`;
otherwise it is `0x003C44B0 + 8*(i-0x100)`. Each pair stores lower instruction
first and upper instruction second. These upload-source addresses are not live
VU code-memory or data-memory addresses.

| VU entry range | Established operation |
| --- | --- |
| `0x000..0x012` | Loads fixed parameter slots, seeds output tags, ends |
| `0x013..0x01D` | Direction-dot classification of an input vector list, ends |
| `0x01E..0x06F` | Triangle geometry pass, perspective divide, winding/state selection, bounds flags and deferred clipping |
| `0x070..0x090` plus `0x091..0x0D2` | Paired-edge pass; differing endpoint classifications produce a displaced four-vertex strip |
| `0x0D3..0x10D` | Near-plane split of deferred homogeneous polygons; ends after draining them |
| `0x10E..0x15E` | Clips each resulting polygon against four XY planes and emits a triangle fan |
| `0x15F..0x184` | Shared homogeneous XY-plane clip helper and intersection continuations |

The upper E bit appears at entries `0x011`, `0x01C`, `0x06E`, `0x08F` and `0x10C`;
each has its following pair present. No instruction pair in the 389-pair
bound sets the upper I bit, so lower words are instructions rather than LOI
float constants.

## Distinction from the VU0 classifier

**Observation:** the separate stream at `0x003D11E0` begins with a DMA tag
word `0x1000002D`; its MPG word is `0x4A5A0000` at `0x003D11EC`, followed by
90 pairs at `0x003D11F0`. The shadow stream begins directly with VIF commands
and is referenced by the shadow producer's render packet. Its XTOP and XGKICK
instructions establish VU1-specific input/output operations. The classifier's
renderer-initialization channel, point predicates and return values belong to
[visibility](visibility.md#vu-point-tests-and-classification). Their shared
entry number 0 does not make them the same program or VU.

## Parameter slots and entry selection

**Observation, high confidence:** the producer writes STCYCL `0x01000404`
and UNPACK `0x6C114184` at packet `+0x20/+0x2C`. Its seventeen consecutive
V4-32 payload quadwords begin at `+0x30`; their fixed destination is VU1 data
slot `0x184`. Entries `0x000..0x011` directly load the following subset.

| VU data slot | Producer packet offset | Loaded value and register |
| --- | --- | --- |
| `0x184` | `+0x30` | `(-(4096-W)/2, -(4096-H)/2, 0, -1)`; later `vf20` in clipping |
| `0x185` | `+0x40` | `((4096+W)/2, (4096+H)/2, 0, 1)`; later `vf21` in clipping |
| `0x186` | `+0x50` | Producer's transformed `(0,0,max(8,near),1)`; later `vf15` for near-plane splitting |
| `0x187` | `+0x60` | `(0,0,0,near)` into `vf7` |
| `0x188` | `+0x70` | `(4095.75,4095.75,0,far)` into `vf8` |
| `0x189..0x18C` | `+0x80..+0xBF` | Remapped model-to-device matrix columns into `vf1..vf4` |
| `0x18D` | `+0xC0` | GIF tag template into `vf16`, copied to slots `0x203` and `0x204` |
| `0x18E` | `+0xD0` | XYZ2 tag template into `vf17`, copied to `0x207`; X halfword is also loaded into `vi2` as the direction-table count |
| `0x18F/0x190` | `+0xE0/+0xF0` | Two RGBAQ A+D payloads into `vf9/vf10` |
| `0x191/0x192` | `+0x100/+0x110` | Two ALPHA_2 A+D payloads into `vf11/vf12` |
| `0x193` | `+0x120` | Inverse-model environment direction into `vf5` |
| `0x194` | `+0x130` | Scale-adjusted direction times projection scalar into `vf6`, with W zero |

Here W/H are target pixel dimensions; near/far and the matrix construction
remain owned by renderer coordinates and shadow rendering. Slot `0x186.zw`
becomes significant in the near-plane split below, rather than supplying a
constant ground height. The producer's mode-3 branch zeros displacement XYZ;
the VU instruction family is shared across the inspected mode branches.

The packet ends its parameter payload with MSCAL entry 0 (`0x14000000`,
producer `0x0018D69C..0x0018D6B8`), then a DMA REF to the part's `+0x34`
topology packet. That packet is constructed by `FUN_0018D740`:

| Packet command / instruction evidence | VU consumer |
| --- | --- |
| UNPACK V4-32 at fixed slot `0x212`, emitted `0x0018DDBC..0x0018DDF0` | Direction/normal table; count is part halfword `+0x0C` |
| MSCNT `0x17000000`, emitted `0x0018DE58..0x0018DE5C` | Resumes after initialization's E delay pair at entry `0x013` |
| Triangles in batches of at most 24, emitted `0x0018DF04..0x0018E038` | Masked signed V4-16 XYZ; first vertex W carries `normal_index + 0x212`, other W values are zero before VIF row handling; MSCAL `0x1E` |
| Endpoint pairs in batches of at most 24, emitted `0x0018E0C0..0x0018E1D0` | Signed V4-16 XYZ; each endpoint W carries its adjacent normal-table slot; MSCAL `0x70` |

The caller `FUN_00190F40` invokes the producer at `0x0019109C` with the
secondary model at scene node `+0x9C` and prepared draw context. Xrefs expose
this direct caller; they do not establish that all retail character archives
contain this topology route. The topology loader's source layout and allocation
contract remain in [model runtime](model_runtime.md#triangle-topology-conversion).

## Direction classification and extrusion

**Observation, high confidence:** entry `0x013` starts at data slot `0x212`,
adds three to the loaded normal count, and uses a pipelined loop with a final
E pair. Upper instructions `0x016/0x019..0x01B` multiply `vf5.xyz` by each
table vector and sum XYZ into an X-lane result. `FMAND` with mask `0x80`
extracts that result's MAC X sign; `ISW.w` writes the value into the table
vector's W word while retaining XYZ. The three extra iterations flush the
pipeline. The stored classification is 0 or `0x80`, not a float normal W.

Triangle entry `0x01E` reads the first vertex's W as a table address, then
reads that table vector's W classification. It converts all three signed XYZ
coordinates with `ITOF12`; when the classification is zero, entries
`0x031..0x033` add displacement `vf6.xyz` to all three. The nonzero branch
skips these additions. W is supplied separately for matrix translation.

Paired-edge entry `0x070` reads the two referenced classifications into
`vi14/vi15`. Equal values skip geometry (`0x086..0x089`). Unequal values enter
`0x091`: it builds the two original endpoints and their displaced copies.
If the first classification is zero, entries `0x092..0x096` reorder these
four positions; otherwise the branch retains the initial order. This makes
edge geometry depend on a classification change across adjacent faces.

**Inference, high confidence:** the combined face and edge paths construct
an extrusion along one supplied direction. They do not project every vertex
onto a fixed floor plane. The source direction is interpreted through the
model's inverse basis; the exact physical unit of the EE projection scalar
still requires the model scale and caller convention, not the VU opcode alone.

The packet builder's STROW values are `(0,0,0,1)` and its triangle STMASK
value is `0x00404000`, with cycle `0x01000303` (`0x0018DE80..0x0018DEB8`).
The first W word therefore retains its table pointer, while the second and
third use row W=1; the VU explicitly replaces the first W after reading its
pointer. The edge pass instead writes W=1 into all four working position
registers at entries `0x07E..0x083`. This corroborates translation use without
treating the packed pointer as a homogeneous float.

**Observation:** the direction table derives from face geometry. The loader
calls `FUN_0018E970` to subtract the first point from the other two, and
`FUN_0018E7B0` computes their integer cross product. `FUN_0018E530` compares
normalized cross-product directions to reuse table entries, then emits scaled
float XYZ and zero W for a new entry. Reversed shared edges are matched by
`FUN_0018E240`; equal face-table indexes remove that shared edge, while
different indexes retain both references. An unmatched edge initially stores
second index `-1-first_index` (`0x0018E478..0x0018E4FC`). The loader can reject
its packet through its construction status; this observation does not establish
that a negative unmatched reference occurs in a submitted retail packet.

## Transform, depth and the fast geometry pass

**Observation, high confidence:** for each input position `p`, entries
`0x034..0x03F` form homogeneous device vector
`h = vf1*p.x + vf2*p.y + vf3*p.z + vf4*p.w`. The edge path repeats the same
four-column operation at `0x097..0x0A7`. The matrix already includes model
scale, current model transform, camera projection and the target XY remap;
the VU does not fetch another camera matrix.

The DIV/MULq sequences divide **XYZ only** by `h.w`. W retains homogeneous
depth for bounds and clipping. For example, pair `0x03B` at resident
`0x003C3E80` has lower `0x81F403BC` (`DIV Q,vf0.w,vf20.w`), and pair `0x040`
at `0x003C3EA8` has upper `0x01C0A61C` (`MULq.xyz vf24,vf20,Q`). The copied
W is supplied by `MOVE.w`, not divided. FTOI4 then converts all fast-path
working lanes; the output W words are subsequently replaced by draw flags.
The resulting packed XYZ2 Z word is the converted projected Z, not the retained
homogeneous W and not a floor height. The clipped path likewise uses
`MULq.xyz` and `FTOI4.xyz` (`0x151/0x155`).

The target-remap matrices change XY and preserve the Z/W axes. Consequently,
the configured projection's reverse depth numerator and homogeneous division
described in [renderer coordinates](renderer_coordinates.md#projection-refresh)
still supply this pass's depth. This bounds the VU-side operation; the original
scene-depth copy and GS depth comparison remain owned by shadow rendering.

**Observation:** projected winding is the X-lane determinant
`(b.x-a.x)*(c.y-a.y) - (c.x-a.x)*(b.y-a.y)`.
For triangles, the decisive upper words are `0x010F71BD` at entry `0x05A`
and `0x010E7BCD` at `0x05B`; the edge path uses `0x0BB/0x0BC`, and the clipped
fan path uses `0x11A/0x11B`. The MAC X-sign mask `0x80` selects one of the
two RGBAQ/ALPHA_2 pairs. Negative sign retains `vf9/vf11`; the other branch
substitutes `vf10/vf12`. It selects raster state rather than simply discarding
one face orientation.

Fast bounds are measured after XYZ division, using the retained W:

| Comparison group | Instruction evidence | Values compared |
| --- | --- | --- |
| Lower bound | Triangle `0x054/0x056/0x058`; edge `0x0BE/0x0C0/0x0C2/0x0C4` | `position.xyw - vf7.xyw`: X>=0, Y>=0, W>=near for ordinary finite values |
| Upper bound | Triangle `0x055/0x057/0x059`; edge `0x0BF/0x0C1/0x0C3/0x0C5` | `vf8.xyw - position.xyw`: X<=4095.75, Y<=4095.75, W<=far for ordinary finite values |

FSSET clears sticky flags before these comparisons; FSAND `0x80` reads the
accumulated sign condition after their pipeline latency (`0x053/0x05D` and
`0x0BD/0x0C9`). Exact signed-zero and exceptional cases retain hardware flag
semantics; the inequalities are finite-value interpretations.

An outside triangle receives ADC=1 on its final vertex and retains its three
**pre-divide** homogeneous vectors in the deferred list starting at slot
`0x18D`. An outside edge strip receives ADC=1 on both final vertices and
retains four vectors. The deferred pointer advances only for those outside
primitives (`0x064..0x066`, `0x0CA..0x0CC`). Inside primitives still use the
fast output chain; subsequent scratch writes overwrite their unretained copy.
Thus the fast bounds do not establish permanent rejection: flagged polygons
enter the following explicit clipping family.

## Near-plane split and four-plane clipping

**Observation, high confidence:** entry `0x0D3` loads lower/upper XY-plane
vectors from slots `0x184/0x185` and near reference `N` from `0x186`. It copies
each deferred triangle or four-vertex strip to `0x1F9`, appends the first point
to close the edge loop, and compares each pair's W against `N.w`
(`0x0E5/0x0E6`, MAC W-sign mask `0x10`). The split writes:

| Vertex/edge case | Stored result |
| --- | --- |
| Point on the nonnegative side of `h.w-N.w` | Original homogeneous point to list `0x1ED` |
| Point on the negative side | Original X/Y with Z=N.z and W=N.w to list `0x1F3` (`SQ.xy` then `SQI.zw`, entries `0x0F1/0x0F3`) |
| Edge whose two signs differ | Full homogeneous intersection to both lists (`0x0F4..0x0FA`) |

For ordinary finite crossing endpoints A/B, the intersection is
`C=A+t*(B-A)`, where `t=(N.w-A.w)/(B.w-A.w)`. The SUB/DIV/MADD sequence
computes all four lanes; no screen-space linear interpolation is substituted.
Both nonempty lists call the same later emitter (`0x100..0x108`).

**Inference, high confidence:** this retains a near-plane depth cap as well as
the portion beyond near. It does not discard the whole negative-W side in the
way a simple near-plane reject would. The cap's X/Y still come from the
homogeneous point; changing W affects their eventual perspective division.
This is a statement about emitted coordinates, not their visible coverage.

The shared emitter calls helper `0x15F` four times:

| Call entry | Plane vector | Sign mask | Finite homogeneous inside condition |
| --- | --- | --- | --- |
| `0x128` | Lower `(-Lx,-Ly,0,-1)` | `0x80`, X | `h.x - Lx*h.w >= 0` |
| `0x130` | Upper `(Ux,Uy,0,1)` | `0x80`, X | `Ux*h.w - h.x >= 0` |
| `0x138` | Lower | `0x40`, Y | `h.y - Ly*h.w >= 0` |
| `0x140` | Upper | `0x40`, Y | `Uy*h.w - h.y >= 0` |

Here `Lx/Ly=(4096-W/H)/2` and `Ux/Uy=(4096+W/H)/2`. These are the small
target's centered boundaries, unlike the fast pass's global GS coordinate
range. The helper alternates polygon buffers `0x1F9` and `0x208`, returns the
output count in `vi4`, and emits nothing when any pass returns zero. It closes
each input polygon by copying its first vertex to the end before walking edges.

At entries `0x165..0x168`, each plane produces
`d(h) = plane.xyz*h.w - h.xyz*plane.w`. Sign checks retain inside points and
add intersections for crossing edges. Continuation `0x179` supplies X-plane
division; `0x176` supplies Y-plane division. The equivalent finite formula is
`C=A+t*(B-A)`, `t=d(A)/(d(A)-d(B))`, applied to all four lanes. The emitted
polygon is therefore clipped before perspective division, preserving its
projected-depth interpolation.

**Bounded observation:** the fast flag includes W>far, but this deferred family
contains no far-plane split or final W<=far rejection. It splits at N.w and
clips only X/Y afterwards. Neither a far-plane rejection nor an additional
Z-plane clipping rule should be inferred from the initial flag alone. No
CLIP/FCAND/FCOR instructions occur in the complete uploaded bound.

## Output packets and bounded storage

**Observation:** the topology builder seeds the triangle fast-output tag with
high word `0x5121C000`, register list `0x555EE`, and loop count equal to the
batch's triangle count. The register sequence is A+D, A+D, XYZ2, XYZ2, XYZ2;
the primitive is context-2 untextured blended triangles (`PRIM=0x243`). The
paired-edge tag uses high word `0x61224000`, register list `0x5555EE`, and
context-2 triangle strip (`PRIM=0x244`). The VU appends the chosen RGBAQ and
ALPHA_2 payloads followed by three or four converted vertices per primitive,
then XGKICKs the output at `TOP+0x49` (`0x069/0x08A`).

The producer supplies these state values before its model-orientation swap:

| Producer mode | `vf9` / `vf10` RGBAQ values | `vf11` / `vf12` ALPHA_2 values |
| --- | --- | --- |
| 1 | `0x80000001` / `0x80000001` | `0x48` / `0x42` |
| 2 | `0x80000040` / `0x80004000` | `0x48` / `0x48` |
| 3 | `0x800000FF` / `0x80000000` | `0x44` / `0x48` |

The constants are corroborated by resident bytes `0x005B5940..0x005B5957` and
producer instructions `0x0018D390..0x0018D48C`. Their selection uses projected
winding; the prior EE orientation-sign swap is described in shadow rendering.
Modes are code branches, not evidence of retail content choosing modes 2/3.

Clipped output uses the fixed template at `0x204`: two A+D state writes at
`0x205/0x206`, then the XYZ2 tag at `0x207` and converted vertices at `0x208`.
The template's primitive is context-2 triangle fan (`PRIM=0x245`). Entry
`0x14E` overwrites its initial low word with 2, clearing EOP on the A+D tag;
entry `0x14C` writes the polygon count plus `0x8000` to the final XYZ2 tag.
The first two vertices receive ADC=1 (`0x154/0x157`), preventing drawing
before a fan has three vertices. XGKICK at `0x15B` submits from `0x204`.
The separate earlier XGKICK from `0x203` at `0x11B` has the bounded extent
described [below](#preliminary-kick-packet-extent); its purpose remains unresolved.

The complete instruction bound establishes the following data-memory uses:

| Data slots | Bounded role |
| --- | --- |
| `0x184..0x194` | Seventeen fixed producer parameter quadwords |
| `0x18D` upward | Deferred homogeneous triangles/strips, reusing parameter-template storage after registers have loaded it |
| `0x1ED` / `0x1F3` | Two near-plane result-list starts |
| `0x1F9` / `0x208` | Alternating polygon clip buffers |
| `0x203..0x207` | Fixed fan/state packet headers and state payloads |
| `0x212` upward | Direction table whose W words become classifications |
| `TOP` onward; output at `TOP+0x49` | VIF double-buffered batch input and fast GIF output |

There are no explicit capacity checks in the decoded VU list-writing loops.
The EE packet builder bounds each face or edge batch at 24 and rejects
direction counts `>=0x1EF` (`0x0018DCA4..0x0018DCBC`); these checks are observed
limits, not a proof of every intermediate clipping-list capacity.

**Bounded storage arithmetic:** the builder selects BASE=0 and OFFSET=`0xC2`
before both batching families (`0x0018DE68..0x0018DE84` and
`0x0018E050..0x0018E068`). A maximum triangle batch occupies 73 input
quadwords and 121 output quadwords: its input is `TOP..TOP+0x48`, and its
fast packet is `TOP+0x49..TOP+0xC1`. These fit the 194-quadword spacing.
An emitted edge uses six output quadwords (`0x0C1..0x0C6`), so 24 emitted
edges would use 145 quadwords including the tag, ending at `TOP+0xD9`.
When TOP=`0xC2`, 21 or more emitted edges would intersect fixed parameter
slots beginning at `0x184`; the maximum range also intersects the deferred
list beginning at `0x18D`. Equal classifications skip emission, so the input
batch count alone does not establish that this overlap occurs. Its actual
retail reachability and effect remain unresolved.

All address, opcode, call and output claims above are bounded to this upload
and its named resident producers/helpers. The selected topology sample below
does not establish the distribution across all character assets or other VU
uploads.

## Edge batch alternation and live overlap

**Observation, high confidence:** the triangle-family preamble writes BASE
`0x03000000` and OFFSET `0x020000C2` at `0x0018DE6C/0x0018DE84`; the edge
preamble repeats them at `0x0018E060/0x0018E068`. Instruction bytes at
`0x0018DE48..0x0018DE97` and `0x0018E040..0x0018E07F` corroborate these writes.
OFFSET clears DBF and sets TOPS to BASE; an execution command copies TOPS to
TOP, then alternates TOPS between BASE+OFFSET and BASE. This command behavior
is also explicit in PCSX2 `Vif_Codes.cpp`, `vifCode_Offset` and
`vuExecMicro`. Consequently, each family's one-based batch numbers
`1,3,5,...` use TOP=0 and `2,4,6,...` use TOP=`0xC2`. The edge reset makes
triangle-batch parity irrelevant to the first edge batch. Skipping geometry
inside a batch does not execute another MSCAL or change that batch's TOP.

The builder emits FLUSH (`0x11000000`) before each batch's TOP-relative
UNPACK, and FLUSHE (`0x10000000`) before its MSCAL. The complete bounded
builder contains no additional edge-emission-count or TOP-dependent size
gate beyond its 24-input-edge limit. Scene submission and controller gates
remain owned by [shadow rendering](shadow_rendering.md#geometry-inputs-and-renderer-ownership).

**Observation:** edge entries `0x071..0x077` separate the input count from
the tag's EOP bit. `ISW.x` at `0x07C` initializes the output tag to zero
loops while retaining EOP. Only unequal classifications reach `0x0BA`
(`0x100B5801`, increment emitted count) and `0x0BC` (`0x0B0B5000`, rewrite
tag X). Equal classifications return through `0x088` without advancing
output pointer `vi6`. Thus an input count of 24 does not force a 24-loop
GIF packet; its actual output is one tag plus six quadwords for each of
the E emitted edges, including edges subsequently marked for clipping.

For TOP=`0xC2`, the tag is at `0x10B` and emitted-edge payloads start at
`0x10C`. The exact overlap progression is:

| Emitted edge, one-based | Fast payload slots | Live-use consequence if reached |
| --- | --- | --- |
| 20 | `0x17E..0x183` | Still below fixed parameters. |
| 21 | `0x184..0x189` | RGBAQ overwrites lower clip plane `0x184`; ALPHA_2 overwrites upper plane `0x185`; the first converted vertex overwrites near reference `0x186`. |
| 22 | `0x18A..0x18F` | Converted vertices reach the beginning of deferred homogeneous storage at `0x18D`. |
| 23 | `0x190..0x195` | Further intersection with deferred storage; initial direction/displacement slots have already been loaded into registers. |
| 24 | `0x196..0x19B` | Maximum fast payload end; direction table `0x212` and fixed fan packet `0x203` are not reached by this fast output. |

**Conditional consequence, high confidence:** `0x08D` enters deferred
processing only when `vi12 != 0x18D`. That continuation reloads `0x184`,
`0x185` and `0x186` at `0x0D3..0x0D5`, after the fast output writes and
XGKICK. Therefore these three slots are live memory, even though other
initial parameters survive in registers. A high-TOP batch emitting at
least 21 edges changes the later clipping inputs if any polygon is deferred.
Without a deferred polygon in that batch, the damaged slots remain until
the next producer's fixed-parameter UNPACK; a later batch in the same
topology packet can still reload them. There is no per-batch repair of
those slots in this builder.

At 22 or more emissions, overlap with retained deferred vertices is also
possible. Every emitted edge first writes four homogeneous scratch vertices
through `vi12` (`0x09F`, `0x0A9..0x0AB`); `0x0CC` retains them by advancing
that pointer only for an outside edge. Subsequent fast writes can replace
earlier retained values when their addresses intersect. Conversely, a
later edge's scratch writes can replace part of the completed fast packet
before its batch-end XGKICK. Which values survive depends on emitted order
and which edges are deferred; arithmetic alone does not identify a damaged
retail packet or its visible result.

## Selected authored shadow topology

**Observation:** the bounded asset sample is exactly six `PL/MODEL/` files below
the retail DATA view: `2NRWBOD1.CCS`, `2SSWBOD1.CCS`, `2SKWBOD1.CCS`,
`2CYBBOD1.CCS`, `2DDRBOD1.CCS` and `2SCOBOD1.CCS`. Version is `0x123` in all six.
Aligned `0xCCCC0800` candidates were checked against their actual directory
record names, selector-4 headers, point/index bounds and the topology reader's
consumed endpoint, which reaches the next typed header in every retained
sample. Declared CCS block lengths were not used as a substitute for handler
consumption; that limitation belongs to
[CCS parsing](../game/files/ccs_runtime.md#parsing-type-dispatch-and-publication).
This is a bounded topology sample, not a full block walk or asset census.

The retained records are 17 `shadow01..shadow17` models in each of the
`MDL_2nrw`, `MDL_2cyb`, `MDL_2ddr` and `MDL_2sco` `00t0/05t0` families,
17 each in `MDL_2ssw00t0` and `MDL_2skw00t0`, 14 each in `MDL_2bir00t0`
and `MDL_2bir05t0`, and nine in `MDL_2kkg00t0`: 207 one-part models in total.
The `2bir` records occur in `2DDRBOD1.CCS`; `2kkg` occurs in `2SCOBOD1.CCS`.
Every retained model has file flags `0x0008`,
selector 4, zero optional byte-list count, 8..24 points and 12..40 triangles.
Character filename selection and loading remain owned by
[character assets](../game/character_assets.md#selection-and-loading-consumers).

**Bounded reconstruction:** the reader's triangle order, first-matching
normal reuse, three cyclic edge insertions and removal-by-last-record swap
were followed in memory. The exact reuse predicate is normalized dot product
`> 0.99609375`, not exact coplanarity (`0x0018E5E8..0x0018E678`, threshold
word `0x3F7F0000`). `FUN_0018E7B0` forms the signed cross product, shifts
it by its fourth argument, then stores signed 32-bit XYZ; the normal call
passes shift 0. Integer cross components in this sample have magnitude at
most 18,259,320. Normalization/dot reconstruction used rounded single-precision
arithmetic; it is not an execution of the retail VU arithmetic. The smallest
observed comparison distance from the reuse threshold was approximately
`8.77e-5`; complete hardware rounding agreement is not claimed.

| Sample family | Reconstructed direction count | Retained edges per part | High-TOP input count | Maximum high-TOP emissions over arbitrary binary table signs |
| --- | --- | --- | --- | --- |
| Both `2nrw` variants | 6..19 | 12..40 | 7, 9 or 16 when a second batch exists | 6, 7 or 13, respectively |
| `2ssw00t0` | 6..19 | 12..40 | 8 or 16 when a second batch exists | 6 or 13, respectively |
| `2skw00t0` | 6..19 | 12..40 | 7, 9 or 16 when a second batch exists | 6, 7 or 13, respectively |
| Both `2cyb` and both `2ddr` variants; `2sco00t0` | 6..19 | 12..40 | 7, 9 or 16 when a second batch exists | 6, 7 or 13, respectively |
| `2sco05t0` | 6..14 | 12..33 | 7 or 9 when a second batch exists | 6 or 7, respectively |
| Both `2bir` variants | 6..10 | 12..20 | No second batch | No high-TOP batch |
| `2kkg00t0` | 6..12 | 12..24 | No second batch | No high-TOP batch |

No reconstructed part has a third batch or unmatched negative adjacency
reference. The paired-edge construction counters satisfy `+0x134 >= +0x138`
in every sample, so the examined construction rejection does not discard
them. The table's last column exhausts binary assignments to the referenced
normal indexes in each high-TOP batch, fixing one sign because complementing
all signs leaves unequal-pair counts unchanged. This gives a conservative
bound independent of whether an actual light direction can produce each
assignment; it does not claim all those assignments are geometrically
reachable.

For an auditable maximum-size example, `MDL_2nrw00t0 shadow09` starts at
decompressed offset `0x265F4`; the selector-4 reader consumes through
`0x2688F`, with the next `0x0100` header at `0x26890`. It has 24 points,
120 indexes, 40 triangles, 19 reconstructed normal entries and 40 retained
edges. Its second batch's 16 normal-index pairs are, in packet order:

```text
(12,11) (13,11) (15,11) (1,11) (13,12) (15,12) (17,13) (16,14)
(18,14) (17,14) (1,14) (18,15) (18,16) (17,16) (17,1) (18,1)
```

At most 13 of those pairs differ for any binary assignment. More basically,
16 input edges cannot produce 21 emissions. **Conclusion for the bounded
reconstruction:** these six files do not supply a high-TOP overlap case.
This does not exclude one in another character, appearance, stage, effect or
other non-excluded retail topology resource. Only the listed body files and
their contained variants were sampled; stages, effect archives and other
body files were not. Nor does this identify an actual submitted packet or
visible artifact in the sampled files.

The construction gates are explicit at `0x0018DC88..0x0018DCD4`: reject
when counter `+0x134 < +0x138`, direction count `>=0x1EF`, edge count zero,
or construction status is nonzero. This final gate does not separately walk
adjacency references to reject unmatched negatives. The sample's nonnegative
references are an asset result, not a general loader guarantee.

For the route into the VU producer, selector 4 supplies model flag `0x08`;
the existing secondary attachment and binding contracts are owned by
[model runtime](model_runtime.md#composition-hierarchy-and-matrix-lifetime).
Instructions and bytes `0x001AD4E0..0x001AD547` establish the relevant
handoff: a flag-`0x08` child's model record is stored at its resolved type-
`0x0100` parent's descriptor `+0x10`. `FUN_00196B40` binds that descriptor
field and publishes node `+0x9C` plus enable bit `+0xA8 & 0x20`
(`0x00196CF4..0x00196D10`, corroborated by resident bytes). Common draw then
selects the producer through those fields. The sampled source topology does
not prove when a particular scene reaches the controller, strength, bounds
and allocation gates documented in shadow rendering.

## Deferred and clipping capacity bounds

**Observation:** triangle batches retain at most `24*3=72` homogeneous
quadwords, `0x18D..0x1D4`; edge batches retain at most `24*4=96`,
`0x18D..0x1EC`. The first near-split list begins immediately afterwards at
`0x1ED`. Scratch writes for an inside primitive reuse the current deferred
pointer without advancing it. Since that primitive itself occupies one of
the 24 inputs, these scratch writes do not require a 25th primitive's storage.
This establishes the deferred-region count bound independently of the
conditional high-TOP fast-output alias described above; it does not repair
that alias.

**Inference, high confidence for finite convex geometry:** the edge scratch
stores are in polygon order `A,B,B+D,A+D`, or the reversed equivalent after
classification-dependent reordering. The decisive store order is homogeneous
registers `vf20/vf21/vf23/vf22` at offsets `0/1/2/3`
(`0x09F`, `0x0A9..0x0AB`). It is the boundary of an affine parallelogram,
rather than the four-vertex strip's raster order. A triangle is convex as
well. An affine matrix preserves this convex parameterization; a linear
half-plane has at most two sign transitions around its boundary. Retaining
inside vertices and two crossing intersections therefore increases a
nonempty polygon's count by at most one per plane.

The near split accordingly produces at most four vertices per triangle
list or five per edge list. For the capped side, X/Y are an affine image of
the split polygon and W is fixed to N.w, so the later XY-plane count bound
still applies; varying intersection Z does not enter those plane predicates.
Both near-list starts are six slots apart. Five vertices plus the helper's
closing copy fit in `0x1ED..0x1F2` or `0x1F3..0x1F8`, preserving the other
list while the first is processed.

Four subsequent XY planes give a conservative maximum of eight vertices
for a triangle result or nine for an edge result. The first helper call
writes `0x208`, the second `0x1F9`, the third `0x208` and the fourth `0x1F9`
(`0x125..0x145`). Nine vertices plus a closing copy fit in
`0x1F9..0x202` or `0x208..0x211`: below packet headers `0x203..0x207` and
direction table `0x212`. The final fan's nine XYZ payloads occupy
`0x208..0x210`. Thus the decoded layout has room for these mathematical
convex-polygon bounds; the original absence of explicit capacity checks is
not by itself evidence of clipping-list overflow.

**Evidence limits:** this bound assumes intact homogeneous vertices,
ordinary finite arithmetic and the established triangle/parallelogram order.
It does not prove behavior after fast-output aliasing, exceptional division,
hardware numerical disagreement or an arbitrary nonconvex/corrupt list.
No unrestricted whole-game clipping-capacity proof is claimed.

## Preliminary kick packet extent

**Observation:** initialization copies the same template to `0x203` and
`0x204` (`0x00D/0x00E`). Its low 64-bit value is `0x1122C00000008002`,
with packed mode, NREG=1, A+D register nibble, NLOOP=2 and EOP=1; its high
64 bits are `0xEEEEEEEEEEEEEEEE`. The producer supplies these words before
MSCAL 0. No decoded instruction subsequently writes `0x203`.

Consequently, provided this template remains intact, XGKICK from `0x203`
at `0x11B` describes exactly three quadwords: its tag, `0x204` interpreted
as an A+D payload, and `0x205` interpreted as another A+D payload. It does
not interpret `0x204` as a second GIF tag, include `0x206`'s ALPHA_2 write,
or reach any XYZ2 payload. The first A+D destination byte is `0xEE` from
the unchanged high half of `0x204`; it is not an XYZ2 register declaration.
PCSX2's `GSState::GIFPackedRegHandlerA_D` masks this to index `0x6E`, but
that emulator decode alone does not establish a retail hardware effect.

The kick precedes stores choosing current polygon state at `0x11C/0x11D`
and possible replacements at `0x122/0x123`. Therefore the instructions alone
do not establish whether the transfer samples `0x205` before or after those
stores. Packet extent and absence of vertex payload are established; exact
transfer timing and the purpose of this preliminary state-only kick remain
unresolved. The later `0x204` kick is still the fan submission documented
above, with its own completed state and vertex packet.
