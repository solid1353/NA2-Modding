# Visibility bounds and culling

This document owns the retail NA2 (`SLPS-25837`) decisions that reject or retain
geometry before drawing, and the bounds and render-state inputs used by those
decisions.

## Research coverage

- **Assigned scope:** Retail visibility decisions: model/scene bounds, frustum/clip tests, stage/particle/shadow visibility, camera inputs and bounds updates.
- **Exploration depth:** Bounded resident static tracing covers box parsing and
  attachment, model extrema and instance construction, the VU0 upload and all
  90 classifier instructions, all 22 resident direct-call sites, renderer
  limit producers, morph ordering, textured effects and particle suppression.
- **Confirmed coverage:** Box endpoint/midpoint layout, attachment and lifetime;
  model default-bound accumulation and packed-parser limitation; ordinary
  eight-corner X/Y/W rejection and classifications 0/1/2; background state
  gates; controller-specific off-screen inputs; particle distance and draw gates.
- **Unresolved or untested:** Entry-0 additional-point register lifetime and
  possible later microprogram writes; bounds writers beyond the inspected construction/morph paths; exhaustive
  indirect-call, other-overlay and lower primitive-clipping coverage. Exact
  VU boundary behavior beyond the recorded sign-bit contract is unobserved.
- **Deliberate exclusions and overlap:** [CCS object types](../../game/files/ccs_object_types.md)
  owns resource identity and parsing; [Model runtime](model_runtime.md) owns
  geometry and skeleton evaluation; [Renderer coordinates](renderer_coordinates.md)
  owns matrix construction; [Battle camera](../../gameplay/session/battle_camera.md) owns
  gameplay camera decisions; [Shadow rendering](shadow_rendering.md) and
  [Particle runtime](particle_runtime.md) own those producers and draw passes;
  [Render submission](render_submission.md) owns downstream packet scheduling.
- **Evidence limitations:** Static inspection of retail
  `SLPS_258.37` establishes static data and branch contracts; direct-call byte
  searches also cover `BTL.BIN` and `ETC.BIN`. No execution or live-memory
  observation is claimed. Imported xref/function gaps prevent whole-program
  absence claims; ordinary plane equations abstract VU floating-point flags.

## Evidence conventions

Unless explicitly marked otherwise, addresses below are resident
`SLPS_258.37` EE addresses; see
[address conventions](../../game/files/file_identities.md#address-conventions).
Decompiler output is corroborated with instructions where vector operations or
type recovery affect the conclusion.

## Box ownership and lifetime

**Observation, high confidence:** `FUN_001ADBF0` (`0x001ADBF0–0x001ADD0F`)
reads a `0x20`-byte payload containing the box record, linked target record and
six floats. Its allocated `0x40`-byte descriptor carries endpoints at `+0x10`
and `+0x20`, both with W = 1, and their component-wise midpoint at `+0x30`,
also with W = 1. Scalar `lwc1`/`swc1` and `add.s`/`div.s` instructions at
`0x001ADC80–0x001ADCF4` confirm these are float copies and arithmetic, despite
the decompiler's integer casts.

The descriptor is a temporary attachment, linked through container `+0x44`.
`FUN_001AD240`, bounded box-list loop `0x001AD308–0x001AD350`, resolves the
linked target through `FUN_001AD960`. If the target descriptor exists and is
neither null nor sentinel 4, it copies all three vectors to target `+0x10`
through `FUN_001AD8F0` (`0x001AD8F0–0x001AD95F`). It then clears the box
record's `+0x2C` runtime pointer, frees the temporary descriptor through
`FUN_001A9730`, and clears container `+0x44`. Thus drawing consumes bounds
inside the target descriptor, rather than retaining the parsed `BOX` object.

**Observation, high confidence:** `FUN_001B0C40` constructs model-descriptor
bounds even without a later explicit box attachment. The loader passes
one shared six-integer extrema accumulator, initialized to alternating
`+0x10000` and `-0x10000`. The parser passes that accumulator and model scale
to `FUN_0019B3A0`, targeting model descriptor `+0x10`.
`FUN_0019B3A0` (`0x0019B3A0–0x0019B48F`) converts each endpoint integer to
float and multiplies it by `model_scale / 4096`. Its midpoint uses the signed
integer expression `(min + max) >> 1` before conversion, so it need not equal
the floating midpoint bit-for-bit. All three W components are 1.

`FUN_001B0790` updates all six extrema from signed 16-bit XYZ triplets in
the rigid part's position array. `FUN_001ADD80` does the same for either its
six-byte position triplets or its eight-byte position records, according to
part `+0x2C`. `FUN_0018D740` accumulates signed XYZ while reading its
eight-byte records, using an `if / else if` minimum/maximum chain per axis.
The packed converter `FUN_001AFF20` receives the outer accumulator as an
extra register argument but its inspected instructions do not consume or
forward it. Therefore passing the accumulator does not prove every parser
updates it. [Model runtime](model_runtime.md) owns the packed-converter
details and its model-flag bypass.

## Ordinary model draw boundary

The ordinary object constructor `FUN_00196B40` creates its primary model
instance at scene child `+0x94` and an optional off-screen model instance at
`+0x9C`. Both use `FUN_001992A0`. The instance's `+0x04` box pointer initially
addresses model descriptor `+0x10`; it is cleared when model flags `+0x48`
have either bit in mask `0x804`. This is a construction-time bypass of the
ordinary bounds decision, not evidence that those flags disable every
geometry clipping operation.

**Observation, high confidence:** `FUN_00190F40` updates the child transform,
computes the inherited draw factor when child `+0x8C` bit 0 is set, and permits
the primary model only when child `+0xA8` bits 2–3 equal 3 and the resulting
factor is at least `1/128`. Off-screen geometry instead requires a non-null
child `+0x9C` and child `+0xA8` bit 5. The two paths are independently selected.

`FUN_001910E0` returns for an empty model or draw-context factor below
`1/128`. It forms a matrix at draw context `+0x80` from render-state `+0x40`
and the current model transform. If instance `+0x04` is null, it assigns
classification 2 at context `+0x224`. Otherwise it calls `FUN_001926A0` with
that box, the resident vector at `0x005BED40`, render state and the matrix,
passing VU entry value `0x1F`. Classification 0 returns before model-part
packet production. Nonzero results survive this whole-model gate.

The retained classification also affects later packet selection: context
`+0x1F0` begins as classification minus 1, with another +2 when model flag
`0x10000` is set. The VU classification below distinguishes rejection,
containment in the larger coordinate limits and retained geometry requiring
the other packet variant.

### Bounds lifetime across transform and morph work

`FUN_001992A0` binds instance `+0x04` directly to descriptor `+0x10`
(`0x00199354–0x0019936C`), rather than copying a world-space box. The ordinary
draw path transforms those local corners with the current model-to-device
matrix. Movement therefore changes the classified points through the matrix;
it does not require this path to rewrite the stored local endpoints.

**Observation, bounded scope:** the whole-model classifier call at
`0x00191268` and zero-result branch at `0x00191278` precede part preparation
and the modifier hook at `0x00191794`. That hook can dispatch the morpher
`FUN_00197570`. Its inspected position-edit branch modifies draw positions
and can rescale source position arrays, but writes no endpoint/midpoint
vectors and performs no new whole-model classifier call. Thus this draw's
classification is decided before its morph edits. [Model runtime](model_runtime.md#morph-control-and-geometry-ownership)
owns the geometry mutation; these observations do not prove that every other
resource or animation callback leaves bounds unchanged.

## Shared VU wrapper and off-screen inputs

**Observation, high confidence:** `FUN_001926A0`
(`0x001926A0–0x0019273B`) loads the following exact register contract, invokes
`vcallmsr`, waits, then returns VU integer register `vi1`:

| Input | VU register | Source |
| --- | --- | --- |
| VU entry selection | encoded control register 27, printed `vc11` | fifth integer argument (`t0`) |
| Two render-state vectors | `vf13`, `vf14` | render state `+0x220`, `+0x230` |
| Two render-state vectors | `vf15`, `vf16` | render state `+0x200`, `+0x210` |
| Matrix | `vf1–vf4` | fourth argument, four consecutive qwords |
| Bounds endpoints | `vf18`, `vf19` | first argument `+0x00`, `+0x10` |
| Additional vector | `vf20` | second argument |

No CPU-side plane comparison occurs inside the wrapper. The instruction at
`0x001926C8` is `ctc2 t0,vc11`, followed by `vcallmsr` at `0x001926FC`;
the fifth argument selects the microprogram entry rather than a CPU-side
plane mask. The ordinary extra vector at `0x005BED40` is four zero floats.

**Observation, high confidence:** `FUN_0018CF70` uses the same wrapper for
off-screen model geometry. It first requires the render environment's
`+0xCC` controller, nonzero controller `+0x15C`, model geometry packet length
and nonzero environment `+0xE4` strength. It builds a matrix from controller
render-state pointer `+0x4C` and the current scene-child transform, constructs
an extra vector from the environment direction and strength, and selects
VU entry 0. A zero result skips packet production and restores the
scratch allocation cursor; nonzero results proceed to the controller queue
through `FUN_0018B700`. This path uses its controller's render state, so
ordinary view visibility is not the sole decision for off-screen geometry.

## VU point tests and classification

**Observation, high confidence:** renderer initialization `FUN_00105FC0`
selects DMA channel 0 through `FUN_001507F8(0)` and submits the stream at
`0x003D11E0` through `FUN_00150B28` (`0x00106074–0x001060B4`). The channel
table at `0x003F7640` resolves index 0 to VIF0 DMA registers `0x10008000`.
The stream's `0x4A5A0000` MPG command at `0x003D11EC` uploads 90 VU0
instructions to entry 0. Their resident bytes occupy
`0x003D11F0–0x003D14BF`; entry `0x1F` corresponds to `0x003D12E8`.
The resident bytes were decoded using PCSX2's VU instruction tables in
`pcsx2/DebugTools/DisVUmicro.h` and `DisVUops.h`, with MAC sign-bit
semantics corroborated in `VUflags.cpp`.
These are static instruction semantics, not an emulator observation.

Entry `0x1F` writes the eight XYZ combinations of endpoint vectors
`vf18/vf19` into VU0 data slots 0–7, then sets the point count to 8.
The common loop starts at entry `0x34` (`0x003D1390`). It loads each point
and forms `P = vf1 * X + vf2 * Y + vf3 * Z + vf4`; translation is multiplied
by `vf0.w = 1`. Endpoint W values and the stored box midpoint are not used
in these corner transforms.

For each point, the program multiplies limit-vector X/Y by projected `P.w`
and keeps their W components as the depth limits. Four `SUBA.xyw`
instructions at `0x003D1408–0x003D1427` produce sign bits for the lower
and upper larger limits (`vf13/vf14`) and viewport limits (`vf15/vf16`).
Mask `0xD0` selects X, Y and W sign bits. There is no separate projected-Z
predicate in this program.

For ordinary finite values away from signed-zero/underflow boundaries, the
viewport decision is equivalent to requiring at least one tested point on
the inside of each of these six planes independently:

| Plane | Inside sign represented by the VU subtraction |
| --- | --- |
| Left | `P.x > viewport_left * P.w` |
| Right | `P.x < viewport_right * P.w` |
| Top | `P.y > viewport_top * P.w` |
| Bottom | `P.y < viewport_bottom * P.w` |
| Near | `P.w > near` |
| Far | `P.w < far` |

**Inference from the instructions, high confidence:** this is a conservative
corner/plane rejection. It does not require one corner to satisfy all six
planes; different corners can supply different inside bits. It does not
perform occlusion testing. Exact contact behavior follows VU subtraction
sign bits, so CPU effect-path equality behavior must not be substituted.

The viewport inside masks are ORed over all points into `vi10`; the larger
limit masks are ANDed into `vi9`. The final instructions
`0x003D1488–0x003D14AF`, including their branch delay slots, return:

| `vi1` | Established meaning |
| --- | --- |
| 0 | Viewport aggregate mask differs from `0x0DD0`: at least one plane has no inside point. |
| 1 | Viewport mask is complete and every tested point is inside every larger-limit plane (`vi9 == 0xD0`). |
| 2 | Viewport mask is complete, but that larger-limit containment mask is incomplete. |

Entry 0 instead prepares 16 point slots and branches into the same loop.
Slots 0–7 use endpoint XYZ; slots 8–15 use `vf20/vf21` XYZ. The first two
upper instructions write only those registers' W lanes (`ADD.w`), and the
wrapper loads `vf20` but does not initialize `vf21`. This bounded static
evidence establishes the extra point count and shared predicate, but does
not establish a self-contained endpoint-plus-direction extrusion. No exact
shadow extent or visible defect is inferred from it; additional VU register
lifetime or microprogram writes remain unresolved.

## Renderer limits and matrix ownership

The classifier's four limit vectors are renderer `+0x200/+0x210` (device
viewport X/Y) and `+0x220/+0x230` (larger limits, X/Y initialized to 0 and
4095), each carrying near/far in W. Their construction and refresh are owned by
[renderer coordinates](renderer_coordinates.md#persistent-transform-state); the
viewport setter `FUN_0010E460` does not rewrite the larger-limit XY pair.

**Observation, bounded scope:** ordinary model and the background callers
listed below compose renderer `+0x40` with an object matrix before invoking the
classifier. The off-screen path also uses its controller renderer `+0x40`.
The classifier takes the supplied matrix and never reads renderer `+0xC0`;
that matrix's construction, copy and unresolved consumers are owned by
[renderer coordinates](renderer_coordinates.md#persistent-0x0c0-and-bounded-alias-tracing).

## Bounded resident caller inventory

The exact direct-call word for `FUN_001926A0` is `0x0C0649A8`.
Byte searches of resident `SLPS_258.37`, `BTL.BIN` and
`ETC.BIN` found 22 resident sites and no matching direct call in either
overlay. The resident import exposes two alias copies of every site; those
are deduplicated below. Xrefs agree with the resident byte inventory. These
counts concern this direct opcode only and do not exclude indirect calls or
other visibility routines.

The background owners below use entry `0x1F` and zero extra vector. Their
matrices combine renderer `+0x40` with child, owner or placement transforms;
the table identifies inline bounds and placement differences. The ordinary
model and off-screen rows retain their distinct contracts above. Renderer
pointer `0x0060919C` is the common default for these background owners;
`FUN_00393AC0` instead reads the
current submission context's renderer at context `+0x3C`.

| Caller / call site | Bounds and decision ownership |
| --- | --- |
| `FUN_001910E0` / `0x00191268` | Ordinary model draw gate; classification is retained for packet choice. |
| `FUN_0018CF70` / `0x0018D10C` | Off-screen geometry, entry 0 and controller renderer; described above. |
| `FUN_00392430` / `0x003924B0` | Owner-inline bounds at `+0x60`, matrix built from position `+0x130`; gates subsequent ray queries and owner `+0x144` visibility flag. |
| `FUN_00393AC0` / `0x00393B10` | Bounds pointer `+0x50`, owner transform `+0x10`; returns the wrapper's result through the tail return. |
| `FUN_00394040` / `0x003940B4` | Owner-inline bounds `+0x10`, position `+0xE0`; gates ray queries, screen placement and owner `+0xF8` flag. |
| `FUN_003957C0` / `0x00395828` | If primary instance exists, rejection returns before `FUN_00190F40`; otherwise calls ordinary draw directly. |
| `FUN_00395DD0` / `0x00395E38` | First composition child's primary instance box; retained result permits `FUN_00194180` aggregate draw. |
| `FUN_00397E60` / `0x00397EFC` | Per-element box in `0xE0`-stride children; writes element `+0xD4` and runs `FUN_00397BC0` only when retained. |
| `FUN_00398510` / `0x00398570` | Writes owner `+0x54`; retained result advances angle and updates child transform. |
| `FUN_003997C0` / `0x00399820` | Writes owner `+0xB0`; retained result advances phase by owner `+0xA4` times parent `+8`, evaluates rotation and rewrites child local matrix. |
| `FUN_0039B910` / `0x0039B970` | Writes owner `+0x3C`; retained result advances and wraps two UV coordinates using parent `+8`. |
| `FUN_0039C160` / `0x0039C1D8`, `0x0039C228` | Two child boxes; owner `+0x28` becomes true if either survives. Both rejection results skip the following countdown, random draws and cloth transform work. |
| `FUN_0039E710` / `0x0039E7CC` | One shared model's box, tested per `0x30`-stride placement; retained placements update the child transform and draw. |
| `FUN_003A08C0` / `0x003A0998` | Loops `0x40`-stride placement matrices and `0xE0`-stride children; rejection clears child `+0xD4`, retained result draws. |
| `FUN_003A1020` / `0x003A1080` | Writes owner `+0x50`; retained result permits a camera-distance comparison against owner `+0x44` and then `FUN_003A1150`. |
| `FUN_003A1D60` / `0x003A1DC0` | Writes owner `+0x9C`; retained result advances angle, transforms the model and updates its auxiliary geometry owner. |
| `FUN_003A27C0` / `0x003A2820` | Writes owner `+0x28`; retained result advances countdown/trigger branch and child draw factor. |
| `FUN_003A2930` / `0x003A2990` | Records owner `+0x28`, then updates UV parameters and calls ordinary draw regardless of this result. |
| `FUN_003A4920` / `0x003A4988` | Optional primary-instance box; rejection returns before ordinary draw. |
| `FUN_003A4EF0` / `0x003A4F60` | Optional composition; first child's primary-instance box gates aggregate draw. |
| `FUN_003A7430` / `0x003A7520` | A separate owner-range gate precedes the optional model-box decision; retained result permits auxiliary-owner update and ordinary draw. |

**Observation, high confidence:** the class identity for the rotation owner is
`ccBgRotateSky`: method `0x00398510` appears at `0x005DD3A8`, table head
`0x005DD3A0` points to descriptor `0x005D6138`, which points to the name at
`0x005B3900`. The UV owner is `ccBgUVAnm`: method `0x0039B910` at
`0x005DD1C8`, table head `0x005DD1C0`, descriptor `0x005D6048`, name at
`0x005B3818`. These type/data chains corroborate background ownership;
the table does not assign unproved class names to the other rows.

**Inference, high confidence within these methods:** visibility can govern
state advancement, not only whether packets are submitted. A rejected
`ccBgRotateSky` or `ccBgUVAnm` does not execute its angle/UV increment in that
method. `FUN_0039C160` similarly bypasses its countdown and PRNG calls when
both boxes reject. This says nothing about other callbacks modifying those
same owners.

## Animated textured-effect rejection

`FUN_00195760` first requires a valid frame selector below `0xFFFE`, updates
the transform and inherited factor, then passes the effect to
`FUN_001961D0` / `FUN_00195A90`. The latter derives its effective intensity
from the factor and selected frame value, converts it to integer and shifts
right five. Values below 1 return, and values above 255 clamp to 255.

**Observation, high confidence:** after composing the effect matrix through
the current renderer, `FUN_00195A90` compares the resulting translation W
against renderer `+0x20C` and `+0x21C`. Below the first or above the second
skips packet allocation; equality survives. This is a depth rejection using
the same render-state limits loaded into the model wrapper, but this effect
path does not call `FUN_001926A0`. An optional effect field `+0x24` changes
the depth projection calculation before this decision. Whole-scene or
particle-population visibility cannot be inferred from this one effect path.

## Particle visibility layers

**Observation, high confidence:** distance suppression is separate from the
box classifier. When emitter byte `+0x37` is set, `FUN_0034C610`
(`0x0034C6D8–0x0034C748`) measures XYZ distance from each visual's position
`+0x10` to its supplied reference vector. Below emitter `+0x188` or above
`+0x18C` sets visual suppression byte `+0x81`; the inclusive interval clears
it. With the emitter option clear, this branch does not rewrite that byte.
The distance branch does not skip the later particle update routines.
[Particle runtime](particle_runtime.md#distance-suppression-and-alpha-processing)
owns the reference-vector producer, configured thresholds and alpha formulas.

Manager draw `FUN_0034FFD0` first requires manager byte `+0x52`. It walks
each emitter's constructed `0xA0`-stride particle elements. Element byte
`+0x7D` suppresses one submission and is cleared; otherwise
`FUN_0034B5A0` requires a non-null visual, nonzero visual active byte `+0x80`
and clear suppression byte `+0x81`. History snapshots submit through the
same visual draw slot. These gates precede the concrete visual's culling.

Vtable `0x005DCAC0` selects `FUN_0034B6F0` at draw slot `+0x10`;
that method checks visual `+0x80` again and calls `FUN_0034AD60`.
Its resource-kind selector dispatches:

| Selector | Draw consumer and established visibility boundary |
| --- | --- |
| 0 | `FUN_00195A90`: intensity and translation-W depth rejection described above. |
| 1 | `FUN_00194180`: composition children of type `0x100` go to ordinary-model drawing and `0xE00` to animated textured-effect drawing. |
| 2 | `FUN_001BB790`: scene entries require entry byte `+0x0A & 4`; eligible `0x100`/`0xE00` entries use the same two draw consumers. |
| `0x12` | `FUN_00190F40`: the ordinary-model enable/factor and box gates described above. |

`FUN_001BB790` can also draw its linked compositions when scene byte
`+0xF7 & 0x20` is set, and its attached action/particle manager when scene
`+0xF8` is nonzero. Its scoped renderer substitution
([renderer coordinates](renderer_coordinates.md#refresh-and-binding-order))
applies to these draws, so the camera inputs of a particle's scene resource
need not be the renderer used by its manager.

**Inference, bounded scope:** this population has no single common frustum
box at the inspected manager submission boundary. Visibility combines
manager/visual gates, optional distance suppression and the selected
resource draw path. [Particle runtime](particle_runtime.md#concrete-visual-update-and-draw)
owns resource construction, history and frame advancement; rejecting a
draw here does not by itself establish that particle lifetime or playback
has stopped.
