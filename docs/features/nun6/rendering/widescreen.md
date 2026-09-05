# NUN6 widescreen reference

NUN6 is an unofficial modified NUN5 build used as comparative implementation
evidence, not as an implementation specification or visual-quality authority
for NA228. The analyzed source identity is recorded in
[NUN6 reference mod](../source.md#source-identity).

The evidence uses clean resident executables and ADV, BTL, ETC, and MOD
overlays, read-only disassembly, aligned binary comparison, and the companion
[site inventory](widescreen_sites.tsv).

## Research coverage

- **Assigned scope:** NUN6's widescreen implementation and the corresponding
  clean NUN5 and NA2 renderer, rectangle, and direct-layout paths.
- **Exploration depth:** The resident executables and ADV, BTL, ETC, and NUN6
  MOD binaries were compared, all 230 repeated rectangle signatures were
  classified, the 177
  donor selections and 53 exclusions were followed to their callees, all 49
  ADV module references were accounted for, and documented direct-layout
  cohorts were mapped where structural homologs exist.
- **Confirmed coverage:** The five common-renderer edits, 2D scale hook,
  selective rectangle expansion, negative selection evidence, several direct
  HUD, effect, camera, and composite-layout cohorts, and the bounded NA2
  candidate mapping are established statically below.
- **Unresolved or untested:** NA2 runtime scope and visual results, NUN6's
  ambient `f31` value, weak ordinal pairs, remaining isolated coordinate
  changes, unidentified owning screens, and possible camera culling or effect
  corrections remain unresolved.
- **Deliberate exclusions and overlap:** NUN6 is treated as an unofficial donor,
  not a visual specification; current NA2 widescreen behavior and implementation
  belong to [Rendering](../../rendering.md).
- **Evidence limitations:** Ordinal pairing is a triage heuristic, and static
  homologs or donor behavior do not prove safe NA2 patch sites, correct final
  values, complete screen coverage, or acceptable runtime presentation.

## Findings summary

NUN6 implements widescreen through separate renderer layers: primary 3D
projection scaling, a base 2D transform, local 2D counter-scaling, selected
full-screen rectangle expansion, and direct layout corrections. The selected
and excluded sites show that widescreen cannot be implemented safely as one
global aspect-ratio or coordinate replacement.

## Analyzed identities

The NUN6 inputs are identified in
[NUN6 reference mod](../source.md#source-identity). The clean NUN5 and NA2 inputs
are identified in the
[standard game file reference](../../../knowledge/game/files/file_identities.md#executables-and-overlays).

## NUN6 implementation evidence

### Widescreen is embedded in the game files

The analyzed NUN6 PCSX2 PNACH is empty, and its game INI only selects input and
memory-card settings. The local changelog and the authors' project page
explicitly identify widescreen work. The ELF and overlays contain the matching
code edits. This rules out an emulator-only explanation for the analyzed
implementation.

### Five common-renderer constant edits

NUN5 `FUN_0010EED0` is the two-field rendering-state writer:

~~~mips
swc1 f12,0x274(a0)
swc1 f13,0x278(a0)
jr   ra
nop
~~~

NUN6 leaves that writer unchanged. A 32-bit word comparison of NUN5 and NUN6
ELF file range `0x0000D000-0x0000F7FF` finds exactly five edits, all in the
common renderer:

| NUN6 runtime / file | NUN5 -> NUN6 | Confirmed static effect | Clean-NA2 homolog runtime / file |
| --- | --- | --- | --- |
| `0x0010DEB0` / `0x0000E030` | 512 -> 688 | `FUN_0010DD00` changes the reference-width numerator used for both diagonal terms of a temporary projection matrix later composed into renderer matrix `+0x100`. The coefficient grows by `688/512 = 1.34375`. | `0x0010DCA0` / `0x0000DDA0` |
| `0x0010E110` / `0x0000E290` | 2.0 -> 2.3125 | The same function divides renderer field `+0x290` by 2.3125 instead of 2.0 when setting that matrix's second translation term. The resulting term is `2/2.3125 = 0.8648648649` of its old value; the neighboring `+0x28C` term still uses 2.0. | `0x0010DF00` / `0x0000E000` |
| `0x0010EE48` / `0x0000EFC8` | 1.0 -> 0.75 | Shared viewport updater `FUN_0010E670` changes the horizontal parameter passed to `FUN_0010EEA0`; `FUN_0010EEE0` builds the center-based logical-screen matrix at renderer offset `+0x1C0`. | `0x0010EC38` / `0x0000ED38` |
| `0x0010F08C` / `0x0000F20C` | 512 -> 672 | `FUN_0010EEE0` changes only the denominator of the horizontal device-space translation contribution proportional to renderer field `+0x284`. It has no effect when that field is zero; nonzero viewport offsets contribute `512/672 = 0.7619047619` as much translation. | `0x0010EE7C` / `0x0000EF7C` |
| `0x0010F5F8` / `0x0000F778` | 1.0 -> 0.75 | Common render-state constructor `FUN_0010F4F0` changes horizontal projection-scale state passed through `FUN_0010F640` / `FUN_0010E670`, while retaining vertical scale 1.0. The writer stores the pair at `+0x274/+0x278`. | `0x0010F3E8` / `0x0000F4E8` |

The 688 numerator and 0.75 `+0x274` scale multiply to `1.0078125` relative
to NUN5 in the horizontal diagonal of the `+0x100` matrix. That near-cancels
the squeeze, much like the separate 2D hook described below, but 688 also
changes the matrix's vertical diagonal. It is therefore evidence of additional
donor projection/reference-space tuning, not an independently proven generic
16:9 formula.

The `+0x1C0` matrix and `+0x274` field are distinct widescreen layers. Earlier
NA2 runtime history established that changing only the constructor constant at
file `0x0000F4E8` is not persistent. None of the other four clean-NA2 homologs
has been runtime-tested. A proper NA2 implementation must evaluate all five
sites separately rather than treating either 0.75 edit as the complete donor
patch.

### 2D horizontal-scale hook and the `f31` bias

NUN5 `FUN_0010BD20` initializes a 2D transform record with the same caller
value at horizontal-scale offset `+0x10` and vertical-scale offset `+0x14`.
It also initializes horizontal and vertical half-extents 256 and 192 at
`+0x20` and `+0x24`. Consumer `FUN_0010A6B0` copies `+0x10/+0x14`
into the transform matrix before transforming all four corners, which confirms
the scale-field roles.

NUN6 replaces the horizontal-scale store at runtime `0x0010BD6C`, ELF file
`0x0000BEEC`, and the following `lui` with:

~~~mips
j   0x00941820
nop
~~~

The custom module hook performs:

~~~mips
lui   t7,0x3EAF
mtc1  t7,f31             # 0.341796875
add.s f0,f31,f0
swc1  f0,0x10(v0)
lui   v0,0x4380
nop
j     0x0010BD74
nop
~~~

Confirmed effects are:

- vertical scale `+0x14` retains the original caller value;
- horizontal scale `+0x10` receives caller value plus 0.341796875;
- `f31` is left holding 0.341796875; and
- the displaced `lui v0,0x4380` behavior is restored before rejoining.

For the common 1.0 input, NUN6 therefore produces horizontal scale
1.341796875. Exact 4:3-to-16:9 expansion is 1.333333333, so NUN6's value is
0.634765625% larger. That small overfill is confirmed numerically; whether it
is deliberate edge overscan or a tuned raster correction remains an inference.

This local scale is composed with NUN6's separate 0.75 screen-space matrix at
renderer offset `+0x1C0`. The common 2D path's net horizontal scale is
`0.75 * 1.341796875 = 1.00634765625`. Static matrix composition therefore
shows that the hook nearly cancels the base screen-space squeeze for
transform-based 2D while retaining 0.634765625% horizontal overfill. Preserving
ordinary 2D width is a strongly supported purpose; the small excess remains
donor tuning rather than a derived 16:9 requirement.

The corresponding clean-NA2 sequence occurs first at runtime
`0x0010BB58-0x0010BB60`, in `FUN_0010BB10`; the replaceable store begins
at runtime `0x0010BB5C`, ELF file `0x0000BC5C`. This is a structural
homolog, not yet a validated NA2 patch site.

NUN5 has four static calls to this initializer:

| Caller | Uniform-scale input | Rotation input | Static behavior |
| --- | --- | --- | --- |
| `FUN_001A43C0` | constant 1.0 | constant 0 | Constructs one fixed-scale draw record. |
| `FUN_0021B330` | object `+0x58` | object `+0x5C` | Draws the generic animated 2D-transform object. |
| `FUN_00258FD0` | object `+0x58` | object `+0x5C` | Reuses the same animated object type from a second rendering context. |
| `FUN_00318780` | object `+0x80` | object `+0x84` | Draws another transform object initialized at scale 1.0 and able to interpolate scale toward 1.0. |

The shared animated type initializes scale to 1.0 by default, but
`FUN_0021A3F0` may load an arbitrary starting scale from caller data and
`FUN_0021A970` updates it through linear, sinusoidal, quadratic, and pulse-like
transitions. NUN6 therefore applies its additive horizontal bias to non-1.0
values as well as the common 1.0 case. Donor parity and exact multiplicative
4/3 counter-scaling are visually equivalent only at a specially chosen input,
not throughout those transitions.

`f31` is not a module-wide constant. The same `MOD.BIN` writes
`0x3F7FFFFF` (about 0.99999994) at file `0x00001878` and 1.0 at
file `0x000018B4` as scratch values in another routine, without restoring the
widescreen value. That routine is reachable through a NUN6 BTL tail jump at
BTL file `0x0006CC64`, live `0x00733964`, so the writes cannot be dismissed as
unreferenced payload. The 177 paired rectangle edits introduce exactly 50 ELF,
35 ADV, and 92 BTL reads of `f31`, but no local setter at those sites. They do
not establish which module writer most recently ran. The intended
vertical-origin value, its lifetime, and its visual purpose therefore require
a runtime trace.

### Selective full-screen draw expansion

The common NUN5 sequence begins a four-float `x, y, width, height` draw setup
with:

~~~mips
mtc1 zero,f12
lui  v0,0x4400           # 512.0
...
mov.s f13,f12
~~~

At selected sites NUN6 changes both ends of that setup:

~~~mips
jal   0x009417F0
lui   v0,0x4400           # preserved delay-slot instruction
...
mov.s f13,f31
~~~

The live `MOD.BIN` helper at `0x009417F0`, file `0x000017F0`, is:

~~~mips
lui  v0,0xC300            # -128.0
mtc1 v0,f12
lui  v0,0x4440            # 768.0
nop
jr   ra
nop
~~~

All 177 selected donor-backed sites originally construct
`x = 0, y = 0, width = 512, height = 384`. NUN6 statically changes them to
`x = -128, y = ambient f31, width = 768, height = 384`. The widescreen
transform hook writes 0.341796875 to `f31`, but other module code can replace
it with approximately 1.0; an exact patched `y` value cannot be claimed from
static control-flow evidence alone.

`FUN_00184E60` stores those four floats at draw-record offsets
`+0x10/+0x14/+0x18/+0x1C`; `FUN_00184580` transforms the origin and adds
the independently scaled width and height to construct four vertices.
`FUN_0035F410` independently confirms the same argument order by emitting
vertices at `(x,y)`, `(x+width,y)`, `(x,y+height)`, and
`(x+width,y+height)`.

The NUN6 renderer's screen-space matrix scales about logical center
`(256,192)`. At horizontal scale 0.75 its exact logical mapping is
`x' = 0.75 * (x - 256) + 256 = 0.75x + 64`. An unchanged
`x=0,width=512` rectangle would therefore occupy only `64..448`. NUN6's
`x=-128,width=768` rectangle maps to `-32..544`, supplying 32 logical
pixels of overdraw on both sides. Exact edge-to-edge compensation would be
`x=-85.333333,width=682.666667`; NUN6 deliberately or empirically uses
12.5% more width than that minimum.

Every donor-backed helper call has a corresponding
`mov.s f13,f12 -> mov.s f13,f31` edit:

| Program | Matching NUN5 sequences | NUN6 expanded | NUN6 left unchanged |
| --- | ---: | ---: | ---: |
| Resident ELF | 63 | 50 | 13 |
| `ADV.BIN` | 56 | 35 | 21 |
| `BTL.BIN` | 98 | 92 | 6 |
| `ETC.BIN` | 13 | 0 | 13 |
| **Donor-backed total** | **230** | **177** | **53** |

The 53 exclusions are not one homogeneous draw cohort. Following each setup's
paired `mov.s f13,f12` to its direct callee gives:

| Unchanged downstream callee | ELF | ADV | BTL | ETC | Total | Meaning |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `FUN_0010E670` | 13 | 3 | 6 | 1 | 23 | Renderer/viewport-state initialization, not a rectangle allocator. |
| `FUN_00184E60` | 0 | 18 | 0 | 12 | 30 | Genuine 512-by-384 draw records deliberately left unchanged by NUN6. |

`FUN_0010E670` stores viewport bounds and scale state, calls the two-field
renderer writer, and rebuilds its center transform. Replacing those 23 origins
with the rectangle helper would change rendering-state setup rather than fill
a 2D background. The other 30 sites form the high-value negative visual cohort:
they use the same draw allocator as many selected sites, so only subsystem and
on-screen semantics—not opcode shape or callee identity—can decide whether NA2
should preserve them.

The selected paths feed five draw-record families:

| NUN5 callee | Selected sites | Static role |
| --- | ---: | --- |
| `FUN_00184E60` | 75 | Allocates an active 0x24-byte 2D draw record and stores `x/y/width/height`. |
| `FUN_00184D20` | 29 | Sibling 0x24-byte draw-record allocator with a different record type/color transition. |
| `FUN_00184DC0` | 2 | Sibling 0x24-byte draw-record allocator with an additional transition parameter. |
| `FUN_00314620` | 62 | Allocates a larger 0x50-byte draw record and stores the same four geometry floats. |
| `FUN_0035F410` | 9 | Emits the four rectangle vertices directly from `x/y/width/height`. |

NUN6's new `MOD.BIN` contains another five helper calls and five paired
`f13 <- f31` edits for its own custom paths. They have no direct NUN5/NA2
counterpart and are not part of the 177-site porting cohort.

This helper is only one part of a multipurpose module. A complete aligned
J/JAL-difference sweep found 135 resident references to 63 `MOD.BIN` targets,
49 ADV references to 15 targets, and 150 BTL references to 40 targets; ETC has
none. The repeated non-widescreen targets inspected nearby implement ID
translation and gameplay/state logic. Only `0x009417F0` is tied to the
full-screen signature, and only `0x00941820` is tied to the paired bias/state
change. Unattributed module targets remain unattributed rather than being
classified as widescreen by proximity.

The ADV subset is no longer unattributed. The 49 references resolve exactly to
35 calls to the full-screen helper plus 14 one-site trampoline targets. The
direct-layout section below accounts for all 14: one composite-strip origin,
five -2048 coordinate stores, four three-section/state initializers, and the
four camera-UI preservation/bias stubs at live `0x00949AA0-0x00949AF0`.
This exhaustion result applies only to ADV; it does not classify the resident
or BTL module targets.

The complete helper-signature selection and proposed NA2 counterparts are in
[`widescreen_sites.tsv`](widescreen_sites.tsv).

#### Address convention

Live MWo3 files include their `0x40`-byte header at the header's load base, so
a complete-file offset maps as `live_base + file_offset`. The existing
Ghidra overlay imports omit that header and label the same instruction
`0x40` lower. For example, the live NUN6 helper is `0x009417F0`, while
the header-omitting Ghidra address is `0x009417B0`. The inventory records
complete-file offsets and live addresses; its function names come from the
header-omitting Ghidra projects.

### Direct layout corrections outside the helper inventory

The 230-row inventory intentionally covers only the repeated full-screen
rectangle signature. NUN6 also edits individual UI routines directly. The
first fully attributed cohort is BTL `FUN_0072CA00`, identified by its embedded
`ccNinkaBase` and `ccNinkaMain` strings. A complete word comparison from that
function's entry through the next function finds exactly eight NUN5-to-NUN6
edits:

| NUN6 BTL file / Ghidra address | NUN5 -> NUN6 operation | Static role in `FUN_0072CA00` | Clean-NA2 homolog |
| --- | --- | --- | --- |
| `0x00065E88` / `0x0072CB48`; `0x00065ED4` / `0x0072CB94` | 375 -> 514, twice | Changes the common starting horizontal coordinate for both the special last item and the indexed items in the first five-item animation loop. | `FUN_00716E90`: file `0x00063158`, Ghidra `0x00717018`; file `0x000631A4`, Ghidra `0x00717064` |
| `0x00065F40` / `0x0072CC00`; `0x00065F58` / `0x0072CC18` | Store x=0 -> materialize and store x=-128 | Reuses the call delay slot to move the first animated object's x coordinate from 0 to -128 without growing the function. | File `0x00063210`, Ghidra `0x007170D0`; file `0x00063228`, Ghidra `0x007170E8` |
| `0x00065F94` / `0x0072CC54` | subtract 2.5 -> subtract 132 | Moves the paired animated object's x coordinate left by an additional 129.5 logical units. | File `0x00063264`, Ghidra `0x00717124` |
| `0x00066098` / `0x0072CD58` | interpolation endpoint 160 -> 40 | Moves the ordinary-item endpoint in the second six-item animation loop 120 units left. | File `0x000633B4`, Ghidra `0x00717274` |
| `0x000662EC` / `0x0072CFAC` | special-item endpoint 10 -> -104 | Moves that loop's special-item endpoint 114 units left. | File `0x000633EC`, Ghidra `0x007172AC` |
| `0x0006637C` / `0x0072D03C` | final x addend 50 -> 168 | Moves the separately drawn first sub-element 118 units right. | No instruction-level homolog: NA2 constructs this sub-element through an object path and uses `interpolated_x + 90` at file `0x00063504`, Ghidra `0x007173C4`. |

These paired left/right changes are confirmed coordinate behavior and are
consistent with a widened result/rank-style layout. The exact on-screen
identity and visual quality still require runtime observation. They prove that
donor parity cannot be obtained from the rectangle helper and common renderer
constants alone. The seven NA2 locations above are structural port candidates,
not approved patch sites; the nonhomologous last operation needs a
semantic/runtime port rather than an ordinal constant replacement.

BTL `FUN_00732B90` is a second fully attributed direct cohort. Its
`TEX_xgauge` string and sprite setup identify a mirrored battle-gauge draw
routine. The function contains exactly two NUN5-to-NUN6 word differences:

| NUN6 BTL file / Ghidra address | NUN5 -> NUN6 | Clean-NA2 homolog |
| --- | --- | --- |
| `0x0006BED0` / `0x00732B90` | Default/left anchor 120 -> 30 | `FUN_0071CAF0`, file `0x00068C30`, Ghidra `0x0071CAF0` |
| `0x0006BF28` / `0x00732BE8` | Mirrored/right anchor 392 -> 480 | File `0x00068C88`, Ghidra `0x0071CB48` |

The routine reuses the selected anchor for its gauge pieces, associated text,
and icon draws; the second player path negates horizontal sprite scale. NUN6
therefore increases the anchor separation from 272 to 450 logical units while
preserving mirrored drawing. This is a bounded-HUD repositioning correction,
not a full-screen rectangle expansion. Both NA2 words are exact structural
homologs, but their final values still need a 16:9 runtime capture because the
clean NA2 assets and surrounding layout are not assumed identical to NUN5.

Three more BTL routines have coherent side-dependent horizontal edits and
exact clean-NA2 structural homologs. Their screen identity is not exposed by a
string, so they remain isolated runtime batches rather than release-ready
sites:

| NUN6 function and BTL sites | NUN5 -> NUN6 coordinate behavior | Clean-NA2 function and file sites |
| --- | --- | --- |
| `FUN_006CA180`: `0x00003544` / `0x006CA204`; `0x0000356C` / `0x006CA22C` | Side-dependent bases 96 -> 6 and 416 -> 464 before the latter path's unchanged subtraction of 30. The result feeds the x argument of repeated sprite/text draws. | `FUN_006B7100`: `0x000032C4` / `0x006B7184`; `0x000032EC` / `0x006B71AC` |
| `FUN_00724F20`: `0x0005E290` / `0x00724F50`; `0x0005E2A0` / `0x00724F60` | Object field `+0x30` is initialized to 66 or 446 in NUN5 and -16.5 or 528 in NUN6; field `+0x34` remains 340. | `FUN_0070F700`: `0x0005B870` / `0x0070F730`; `0x0005B880` / `0x0070F740` |
| `FUN_007307AC`: `0x00069B58` / `0x00730818`; `0x00069B68` / `0x00730828` | Side-dependent object field `+0x30` changes from 6/506 to -31/536; field `+0x34` remains 10. | `FUN_0071A8F0`: `0x00066A9C` / `0x0071A95C`; `0x00066AAC` / `0x0071A96C` |

The direction of every pair moves opposite-side positions outward, which makes
widescreen intent a strong inference. Static evidence does not identify the
owning screen or prove that NA2 should use the donor's exact asymmetric
distances. `FUN_00724F20` also contains five later NUN6 content/index changes;
only its two coordinate-field edits are classified here.

A further NUN6 BTL list/selection renderer changes horizontal draw constants
92 -> 50 and 304 -> 336 in `FUN_0089EA80`, then changes a right-side control
base from 356 -> 420 in overlapping exports `FUN_0089ECB0` /
`FUN_0089ECF0` while leaving the corresponding left base at 356. These are
exactly three differences in BTL file range `0x001D7DC0-0x001D842F`, at files
`0x001D7EBC`, `0x001D7F70`, and `0x001D8164`. They are confirmed horizontal
layout changes, but the first renderer has no reliable instruction-level NA2
match and the screen identity is unresolved. This cohort belongs in runtime
attribution, not an ordinal port list.

Coordinate differences alone are not classified as widescreen. For example,
BTL `FUN_0073E340` changes only sprite field `+0x54` from y=300 to y=342, and
`FUN_0073E750` changes three draw/text y values from 303/294/300 to
345/334/342. Those four vertical-only edits may be another NUN6 layout fix,
but they provide no static evidence of horizontal 16:9 compensation and are
excluded from the widescreen port plan pending runtime attribution.

ADV has direct horizontal cohorts as well. The code island between
`FUN_00721770` and `FUN_00721B40` contains exactly five NUN5-to-NUN6 word
differences in file range `0x0005AAB0-0x0005AE7F`:

| NUN6 ADV file / Ghidra address | NUN5 -> NUN6 | Confirmed use |
| --- | --- | --- |
| `0x0005ACC4` / `0x00721984`; `0x0005AD30` / `0x007219F0` | Draw x argument 120 -> -30, twice | Passes the same left-side x coordinate to two sprite draws. |
| `0x0005ACF4` / `0x007219B4` | Draw x argument 256 -> 128 | Repositions the intervening sprite draw. |
| `0x0005AD7C` / `0x00721A3C` | Repeated-sprite x increment 272 -> 144 | Feeds the x argument used in the following repeated draws. |
| `0x0005ADF0` / `0x00721AB0` | Draw x argument 492 -> 576 | Moves the final sprite draw right. |

The neighboring `FUN_00721770` contains the `ccAdvFunctionHelp` string, so a
function-help UI association is plausible, but neither the string nor a clean
NA2 instruction-level homolog is proven for this exact code island. Treat the
five edits as one semantic/runtime batch. Their mixed left, center, and right
movement is confirmed layout behavior; copying an ordinal constant without
first identifying the NA2 draw routine is not justified.

One ADV effect family supplies a different kind of widescreen evidence. Across
the complete NUN5/NUN6 `ADV.BIN` pair, exactly five words change from
`lui v0,0x43D7` (430.0) to `lui v0,0x4402` (520.0):

| NUN6 file / live address | Operation | Clean-NA2 file / Ghidra address |
| --- | --- | --- |
| `0x0008EFC0` / `0x00755CC0` | Add 430 -> 520 to a generated sprite record's x field `+0x50`. | `0x0008C5E8` / `0x007404A8` |
| `0x0008F0E8` / `0x00755DE8` | Same x-field addition in the paired path. | `0x0008C710` / `0x007405D0` |
| `0x0008F338` / `0x00756038` | Same x-field addition in another paired draw path. | `0x0008C948` / `0x00740808` |
| `0x0008F468` / `0x00756168` | Same x-field addition in its paired path. | `0x0008CA78` / `0x00740938` |
| `0x0008F5B0` / `0x007562B0` | Initialize object x field `+0x34` to 430 -> 520. | `0x0008CBC0` / `0x00740A80` |

The surrounding symbols and data identify `ccAdvFootEffectSmoke`, and the
first four operations compute sprite x from transformed/local coordinates
before applying the shared base. This is an exploration effect/camera-space
correction, not a bounded HUD anchor. All five clean-NA2 counterparts retain
430.0 and match the local instruction structure, but they must be tested as a
single foot-effect batch while moving in multiple exploration directions and
across camera transitions. A UI-only widescreen implementation would miss this
class of correction.

The ADV camera UI is a fully identified direct-layout cohort. Its shared data
contains both `ccAdvGauge` and `TEX_adv_camera`. A complete aligned word
comparison over donor file range `0x000F2D80-0x000F364F` finds exactly twelve
NUN5-to-NUN6 differences, all of which participate in moving sprite-record x
coordinates roughly 100 logical units left while retaining their y values:

| Camera-UI role | NUN6 ADV file / Ghidra sites and operation | Clean-NA2 structural homolog |
| --- | --- | --- |
| Four rotated gauge sprites in `FUN_007B9AB0` / `FUN_007B9AF0` | Files `0x000F2EA8` and `0x000F2EAC`, Ghidra `0x007B9B68` and `0x007B9B6C`, change the shared x addend 0.01 -> -100. File `0x000F2EC0` / Ghidra `0x007B9B80` replaces the following y-add instruction with a jump to module live `0x00949AC0`; the module reconstructs `y + 0.01` and returns after the displaced region. | `FUN_007A0680` / `FUN_007A06C0`: files `0x000EC878`, `0x000EC87C`, and `0x000EC890`; Ghidra `0x007A0738`, `0x007A073C`, and `0x007A0750` |
| Gauge origin in `FUN_007B9CE0` / `FUN_007B9D20` | File `0x000F3110` / Ghidra `0x007B9DD0` changes x 20 -> -80. File `0x000F3118` / Ghidra `0x007B9DD8` replaces the matching y=20 store with a jump to module live `0x00949AA0`, which restores that unchanged y store before returning. | `FUN_007A0890` / `FUN_007A08D0`: files `0x000ECAC0` and `0x000ECAC8`; Ghidra `0x007A0980` and `0x007A0988` |
| Six camera texture/bar x baselines in the same renderer | Files `0x000F31B8`, `0x000F3208`, `0x000F32DC`, `0x000F33D0`, `0x000F3420`, and `0x000F34E8`; Ghidra `0x007B9E78`, `0x007B9EC8`, `0x007B9F9C`, `0x007BA090`, `0x007BA0E0`, and `0x007BA1A8`. The values change respectively 126 -> 25.5, 126 -> 25.5, 125 -> 25, 126 -> 25.5, 126 -> 25.5, and 123 -> 22.75; their paired y constants are unchanged. | Files `0x000ECB68`, `0x000ECBB8`, `0x000ECC8C`, `0x000ECD80`, `0x000ECDD0`, and `0x000ECE98`; Ghidra `0x007A0A28`, `0x007A0A78`, `0x007A0B4C`, `0x007A0C40`, `0x007A0C90`, and `0x007A0D58` |
| Radial camera-selector x calculation in `FUN_007BA230` / `FUN_007BA270` | File `0x000F3644` / Ghidra `0x007BA304` replaces `f1=0` with a jump to module live `0x00949AF0`. The module sets `f1=-100` and returns to the existing `x = 74 + 28*sin(angle) + f1` calculation; the later y calculation is unchanged. | `FUN_007A0DE0` / `FUN_007A0E20`: file `0x000ED04C`, Ghidra `0x007A0F0C` |

The trampolines are preservation devices, not additional visual effects: they
free an occupied instruction slot for the new x bias while recreating the
displaced, unchanged y operation. This cohort is stronger than an anonymous
coordinate cluster because the texture identity, record fields, clean-NA2
functions, and horizontal-only behavior all agree. Port it as one camera-UI
runtime toggle and validate the rotating markers, both gauge bars, and the
selector together; omitting any subset leaves internally inconsistent camera
chrome.

NUN6 also rewrites composite ADV strip geometry rather than changing isolated
anchors. In `FUN_00759D60`, eight words form one coordinated patch:

| NUN6 ADV file / Ghidra address | NUN5 -> NUN6 operation | Clean-NA2 counterpart in `FUN_007443B0` |
| --- | --- | --- |
| `0x00093104` / `0x00759DC4` | First record horizontal extent 90 -> -85. | `0x00090548` / `0x00744408` |
| `0x00093164` / `0x00759E24` | Second record x 90 -> 0.03125. | `0x000905A4` / `0x00744464` |
| `0x000931B0` / `0x00759E70` | Third extent `422 - texture_width` -> `1688 - texture_width`. | `0x000905F0` / `0x007444B0` |
| `0x000931DC` / `0x00759E9C` | Third x `texture_width + 90` -> `texture_width + 0.03125`. | `0x0009061C` / `0x007444DC` |
| `0x00093234` / `0x00759EF4` | Following fill width 512 -> 2048. | `0x00090674` / `0x00744534` |
| `0x00093258` / `0x00759F18` | Store x=0 -> jump to module live `0x00949910`. The module computes and stores `texture_width - 160`, then returns to live `0x00759F5C`. | `0x00090698` / `0x00744558` |
| `0x000932F4` / `0x00759FB4` | A later fill width 512 -> 2048. | `0x000906D8` / `0x00744598` |
| `0x0009330C` / `0x00759FCC` | Store x=0 -> store the module-computed `texture_width - 160` value retained in `f28`. | `0x000906F4` / `0x007445B4` |

The clean-NA2 function is a strong structural homolog: it builds the same
sequence of draw records and retains the NUN5 values. NUN6 deliberately uses
negative/flipped and four-times-wider extents, near-zero seams, and a shared
left bias. These values must be ported as one strip-composition algorithm;
applying only the 512 -> 2048 edits would leave its seams and origin wrong.
The exact owning screen remains unresolved statically.

A related three-section list/menu backdrop is exposed through overlapping
entries `FUN_0075A780`, `FUN_0075A790`, and `FUN_0075A7D0`. NUN6 changes each
section's horizontal extent from 512 to 2048. The first x=0 store becomes a
jump to module live `0x00949A10`, which stores `f20 - 224` in both the draw
record and `f28`; the next two x=0 stores reuse `f28`. The complete six-site
mapping is:

| Role | NUN6 ADV sites | Clean-NA2 sites |
| --- | --- | --- |
| Three width edits | File `0x00093B90`, `0x00093C04`, `0x00093C60`; Ghidra `0x0075A850`, `0x0075A8C4`, `0x0075A920` | File `0x00090F58`, `0x00090FC8`, `0x00091024`; Ghidra `0x00744E18`, `0x00744E88`, `0x00744EE4` |
| Shared x-bias introduction and two reuses | File `0x00093BA4`, `0x00093C10`, `0x00093C70`; Ghidra `0x0075A864`, `0x0075A8D0`, `0x0075A930` | File `0x00090F6C`, `0x00090FD4`, `0x00091034`; Ghidra `0x00744E2C`, `0x00744E94`, `0x00744EF4` |

The clean candidates are the structurally matching `FUN_00744D50` /
`FUN_00744D60` and `FUN_00744DA0` family. Nearby input and list-entry routines
establish a menu/list context, but not a unique screen name. Runtime testing
must exercise all callers. This pair of cohorts also explains one purpose of
`MOD.BIN`: its trampolines synthesize float biases that do not fit in the
original instruction slots. An NA2 implementation needs equivalent injected
code or a larger semantic hook; a constants-only patch cannot reproduce it.

Two additional ADV routines use the same three-record construction with a
dynamic horizontal bias. In the first, overlapping NUN6 entries
`FUN_00721560` / `FUN_007215A0` build three adjoining draw records from the
object at `param_1+0x2C`. Each record's horizontal extent changes from 512 to
2048. The first x=0 store jumps to module live `0x009499B0`, which computes
`f21 - 224`, writes that value to record field `+0x50`, and retains it in
`f28`; the next two records store the retained `f28` value. The exact mapping
is:

| Role | NUN6 ADV sites | Clean-NA2 sites |
| --- | --- | --- |
| Three width edits | File `0x0005A94C`, `0x0005A9B4`, `0x0005AA04`; Ghidra `0x0072160C`, `0x00721674`, `0x007216C4` | File `0x00058F94`, `0x00058FF8`, `0x00059048`; Ghidra `0x0070CE54`, `0x0070CEB8`, `0x0070CF08` |
| Dynamic x-bias introduction and two reuses | File `0x0005A960`, `0x0005A9C0`, `0x0005AA14`; Ghidra `0x00721620`, `0x00721680`, `0x007216D4` | File `0x00058FA8`, `0x00059004`, `0x00059058`; Ghidra `0x0070CE68`, `0x0070CEC4`, `0x0070CF18` |

Clean NA2 `FUN_0070CDB0` / `FUN_0070CDF0` builds the same three records and
retains all six NUN5 operations. The `f21` value is half of the routine's
dynamic `param_1+0x0C` float, so this is not interchangeable with the fixed
`f20 - 224` menu-backdrop hooks above. It must be ported and tested as a
separate semantic cohort; the owning screen remains unresolved statically.

The second dynamic-bias cohort begins at overlapping NUN6 entries
`FUN_0075B860` / `FUN_0075B8A0`. Ghidra cannot decompile those entries because
the module jump breaks its recovered control flow, but the instruction stream
unambiguously constructs the same three records. Their widths change from 512
to 2048, while module live `0x009499E0` replaces the first x=0 store with
`f20 - 224` and leaves that value in `f28` for the next two records:

| Role | NUN6 ADV sites | Clean-NA2 sites |
| --- | --- | --- |
| Three width edits | File `0x00094C34`, `0x00094CA8`, `0x00094D04`; Ghidra `0x0075B8F4`, `0x0075B968`, `0x0075B9C4` | File `0x00091E2C`, `0x00091E9C`, `0x00091EF8`; Ghidra `0x00745CEC`, `0x00745D5C`, `0x00745DB8` |
| Dynamic x-bias introduction and two reuses | File `0x00094C48`, `0x00094CB4`, `0x00094D14`; Ghidra `0x0075B908`, `0x0075B974`, `0x0075B9D4` | File `0x00091E40`, `0x00091EA8`, `0x00091F08`; Ghidra `0x00745D00`, `0x00745D68`, `0x00745DC8` |

Clean NA2 `FUN_00745C60` / `FUN_00745CA0` supplies the exact instruction-level
homolog and retains all six NUN5 operations. The following NUN6 input routine
`FUN_0075BAB0` and clean input routine following `FUN_00745E90` corroborate
the family mapping, but do not expose a unique screen name. This is therefore
another independently toggleable runtime batch rather than justification for
globally replacing three-record sequences.

The same three-section pattern occurs again in ADV `FUN_007B5EE0`. Its three
widths change from 512 to 2048 at files `0x000EF2B4`, `0x000EF328`, and
`0x000EF384` (Ghidra `0x007B5F74`, `0x007B5FE8`, and `0x007B6044`). The first
x=0 store at file `0x000EF2C8` / Ghidra `0x007B5F88` jumps to module live
`0x00949A40`; that trampoline computes `f20 - 224`, stores it as x, and keeps
it in `f28`. Files `0x000EF334` and `0x000EF394` (Ghidra `0x007B5FF4` and
`0x007B6054`) replace the other two x=0 stores with `f28` stores.

Clean NA2 `FUN_0079CD30` is the exact structural family member. Its width
sites are files `0x000E8EFC`, `0x000E8F6C`, and `0x000E8FC8` (Ghidra
`0x0079CDBC`, `0x0079CE2C`, and `0x0079CE88`); its x stores are files
`0x000E8F10`, `0x000E8F78`, and `0x000E8FD8` (Ghidra `0x0079CDD0`,
`0x0079CE38`, and `0x0079CE98`). This is a second runtime batch, not evidence
that every 512-wide record should be expanded.

The following setup sequence uses five more module trampolines to turn five
horizontal coordinate pairs from `[0, 512]` into `[-2048, 2048]`. Each
left-side x=0 store becomes a jump to a module stub that stores -2048.0 in
object field `+0xE0`; its paired `lui` changes 512.0 to 2048.0. The y field
`+0xE4` and intervening setup/draw calls are unchanged.

| Side | NUN6 ADV file / Ghidra sites | Clean-NA2 file / Ghidra sites |
| --- | --- | --- |
| Left, 0 -> -2048 through module live `0x00949950-0x00949990` | `0x000EF4E0` / `0x007B61A0`; `0x000EF5A0` / `0x007B6260`; `0x000EF5F4` / `0x007B62B4`; `0x000EF6B4` / `0x007B6374`; `0x000EF708` / `0x007B63C8` | `0x000E9118` / `0x0079CFD8`; `0x000E91D8` / `0x0079D098`; `0x000E922C` / `0x0079D0EC`; `0x000E92EC` / `0x0079D1AC`; `0x000E9340` / `0x0079D200` |
| Right, 512 -> 2048 | `0x000EF508` / `0x007B61C8`; `0x000EF5C8` / `0x007B6288`; `0x000EF61C` / `0x007B62DC`; `0x000EF6DC` / `0x007B639C`; `0x000EF730` / `0x007B63F0` | `0x000E9140` / `0x0079D000`; `0x000E9200` / `0x0079D0C0`; `0x000E9254` / `0x0079D114`; `0x000E9314` / `0x0079D1D4`; `0x000E9368` / `0x0079D228` |

The clean sequence follows `FUN_0079CF00` and uses the same y values and call
order. NUN6 leaves an earlier `[0, 512]` pair at y=374 unchanged, so even
inside this one routine the correct selection is semantic: only the five
specified layers receive the larger span.

Finally, the donor immediately changes a following draw from
`x=32, width=448, height=60` to `x=-32, width=640, height=64` at files
`0x000EF780`, `0x000EF7A0`, and `0x000EF7A8` (Ghidra `0x007B6440`,
`0x007B6460`, and `0x007B6468`). The arguments feed one rectangle/sprite draw
after asset handle 31 is selected. No exact clean-NA2 instruction-level
homolog was found, so this three-word donor batch requires screen attribution
and a semantic NA2 equivalent rather than address translation.

`FUN_007CE520` generalizes the coordinate-pair technique across a state
switch. At file `0x00107898` / Ghidra `0x007CE558`, NUN6 replaces the original
`lui a1,0x008B` with a jump to module live `0x00949A70`. The module loads
-2048.0 into `f28`, reconstructs the displaced `lui`, and returns to live
`0x007CE59C`. Selected switch arms can then replace `x=0` stores with
`swc1 f28,+0xE0` without adding instructions. Their paired x=512 constants
become 2048.

The selection is especially informative because the switch contains three
otherwise parallel six-pair blocks:

| Donor block | Left-side file / Ghidra sites | Right-side file / Ghidra sites | NUN6 disposition |
| --- | --- | --- | --- |
| Asset/state 31 path | `0x107940` / `0x007CE600`; `0x107994` / `0x007CE654`; `0x107A54` / `0x007CE714`; `0x107AA8` / `0x007CE768`; `0x107B68` / `0x007CE828`; `0x107BBC` / `0x007CE87C` | `0x107968` / `0x007CE628`; `0x1079BC` / `0x007CE67C`; `0x107A7C` / `0x007CE73C`; `0x107AD0` / `0x007CE790`; `0x107B90` / `0x007CE850`; `0x107BE4` / `0x007CE8A4` | All six `[0,512]` pairs become `[-2048,2048]`. |
| Asset/state 32 path | `0x107CFC` / `0x007CE9BC`; `0x107D50` / `0x007CEA10`; `0x107E10` / `0x007CEAD0`; `0x107E64` / `0x007CEB24`; `0x107F24` / `0x007CEBE4`; `0x107F78` / `0x007CEC38` | `0x107D24` / `0x007CE9E4`; `0x107D78` / `0x007CEA38`; `0x107E38` / `0x007CEAF8`; `0x107E8C` / `0x007CEB4C`; `0x107F4C` / `0x007CEC0C`; `0x107FA0` / `0x007CEC60` | Deliberately remains `[0,512]`; all 12 words are identical to NUN5. |
| Asset/state 33 path | `0x1080B8` / `0x007CED78`; `0x10810C` / `0x007CEDCC`; `0x1081CC` / `0x007CEE8C`; `0x108220` / `0x007CEEE0`; `0x1082E0` / `0x007CEFA0`; `0x108334` / `0x007CEFF4` | `0x1080E0` / `0x007CEDA0`; `0x108134` / `0x007CEDF4`; `0x1081F4` / `0x007CEEB4`; `0x108248` / `0x007CEF08`; `0x108308` / `0x007CEFC8`; `0x10835C` / `0x007CF01C` | All six `[0,512]` pairs become `[-2048,2048]`. |

The three blocks use the same y sequence—374/380, 300/370, and 290/296—so
the untouched middle arm is strong negative evidence against widening by
instruction pattern alone. The selected arms also change their final draws:
asset 31 changes `x=32, width=448, height=60` to `x=-32, width=640, height=60`
at files `0x00107C30` and `0x00107C50` (Ghidra `0x007CE8F0` and
`0x007CE910`); asset 33 changes the same original geometry to
`x=-20, width=576, height=60` at files `0x001083A8` and `0x001083C8`
(Ghidra `0x007CF068` and `0x007CF088`). Asset 32 keeps the original
32/448/60 geometry.

Clean NA2 `FUN_007B4780` contains the same three-block state structure. The
strong candidates for the selected first and third blocks are:

| Clean block | Candidate left-side file / Ghidra sites | Candidate right-side file / Ghidra sites |
| --- | --- | --- |
| First | `0x100998` / `0x007B4858`; `0x1009EC` / `0x007B48AC`; `0x100AAC` / `0x007B496C`; `0x100B00` / `0x007B49C0`; `0x100BC0` / `0x007B4A80`; `0x100C14` / `0x007B4AD4` | `0x1009C0` / `0x007B4880`; `0x100A14` / `0x007B48D4`; `0x100AD4` / `0x007B4994`; `0x100B28` / `0x007B49E8`; `0x100BE8` / `0x007B4AA8`; `0x100C3C` / `0x007B4AFC` |
| Third | `0x1010E0` / `0x007B4FA0`; `0x101134` / `0x007B4FF4`; `0x1011F4` / `0x007B50B4`; `0x101248` / `0x007B5108`; `0x101308` / `0x007B51C8`; `0x10135C` / `0x007B521C` | `0x101108` / `0x007B4FC8`; `0x10115C` / `0x007B501C`; `0x10121C` / `0x007B50DC`; `0x101270` / `0x007B5130`; `0x101330` / `0x007B51F0`; `0x101384` / `0x007B5244` |

NA2's middle block at files `0x00100D3C-0x00100FE0` is the structural
counterpart of the donor exclusion and should remain unselected until runtime
evidence contradicts that mapping. The final NA2 draws use different assets
and call shapes, so the donor's two rectangle edits have no exact
instruction-level NA2 homolog. Port the selected state behavior, then derive
the NA2 decoration geometry from captures rather than copying the handle-31
and handle-33 words.

### What the selection proves

The 53 exclusions are negative evidence against a global search-and-replace.
Identical instruction spelling does not mean identical visual purpose. NUN6
treats some matching paths as edge-filling layers and deliberately leaves
others bounded.

`ETC.BIN` is especially useful negative evidence: NUN6 changes only 26 bytes
in that overlay relative to NUN5 and routes none of its 13 matching sequences
through the helper. Extras/menu coverage is therefore resident-ELF work,
intentionally unchanged, or incomplete; the static evidence cannot choose
between those explanations.

## Mapping the donor selection to NA2

NA2 contains exactly the same signature population as NUN5: 63 resident, 56
ADV, 98 BTL, and 13 ETC sequences. This makes ordinal pairing useful, but not
conclusive.

For each ordinal pair, the inventory compares 24 surrounding aligned
instructions, excluding the two signature instructions. J/JAL words are
reduced to opcode, non-SPECIAL words to their upper 16 bits, and SPECIAL words
remain exact. This ignores relocated immediates while retaining instruction
and register shape.

| Program | Mean shape match | Minimum | Pairs below 0.75 |
| --- | ---: | ---: | ---: |
| Resident ELF | 0.848 | 0.208 | 17 |
| `ADV.BIN` | 0.926 | 0.417 | 8 |
| `BTL.BIN` | 0.934 | 0.500 | 10 |
| `ETC.BIN` | 0.942 | 0.750 | 0 |

The metric is a triage heuristic, not proof of function identity or rendering
purpose. All 230 candidates need guard-byte verification. The 35 pairs below
0.75 additionally require function-level review before any port; localized UI
and code-structure changes account for several of the weakest resident pairs.

## Unresolved findings

- Runtime evidence has not established a primary-renderer scope that survives
  every state transition.
- NUN6 applies its separate 0.75 base screen transform through a shared updater;
  NA2 still needs runtime evidence to decide whether that transform must be
  primary-scoped or shared with secondary render states.
- NUN6's 688 reference width, 2.3125 second translation divisor, and 672
  viewport-offset denominator are confirmed but have no NA2 runtime evidence;
  their object scope and visual purpose remain partly unresolved.
- NUN6's ambient `f31` dependency is statically unsafe: at least three module
  writes compete for the register, so its selected rectangles' live `y` value
  and visual rationale are unresolved.
- The 2D horizontal scale and rectangle API are now statically identified, but
  the reason NUN6 uses slight horizontal overfill instead of exact 4:3-to-16:9
  expansion remains unverified.
- Thirty-five ordinal NA2 pairs have weak local structural similarity and need
  manual function mapping.
- Direct UI work is not exhausted by the helper inventory. One eight-word BTL
  cohort is fully attributed; other isolated NUN6 coordinate changes still
  require function-level attribution before they can be classified or ported.
- NUN6 itself may have incomplete or aesthetically different coverage. Its
  exclusions are evidence to investigate, not a promise that NA2 should look
  identical.
- Wider cameras may require culling or effect fixes not represented by the
  signature inventory.
