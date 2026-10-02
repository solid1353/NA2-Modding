# Shadows and off-screen passes

This document records the resident shadow-controller family of retail NA2
(`SLPS-25837`), its off-screen GS packets, and the separate shadow-animation
owner. Addresses are resident `SLPS_258.37` EE addresses unless stated
otherwise; see [address conventions](../game/files/file_identities.md#address-conventions).
Class names are retained only where an embedded descriptor establishes them;
the `0x1800` file tag's original class name is unknown.

## Research coverage

- **Assigned scope:** Concrete shadow and off-screen rendering owners, target
  setup, geometry/projection inputs, queues, model/stage consumers, draw/cleanup
  and per-update animation.
- **Exploration depth:** The resident controller family was traced through
  constructors, geometry production, bucket selection, drain, GS setup,
  compositing and destruction using decompilation and selected instruction/data
  reads. The named animation owner's methods, background list scheduling,
  fighter allocation and common model submission were inspected. All 24 retail stage background payloads were checked for
  the named owner's factory index, covering 1,487 records.
- **Confirmed coverage:** The shared controller emits an off-screen geometry
  pass followed by textured screen rectangles; bucket state is drained per render
  preparation. Target dimensions and corner offsets have concrete pixel units.
  The named animation owner has a separate playback-rate update and scoped draw
  binding. Twelve background controllers and a fighter-owned controller use
  shared target addresses and a borrowed renderer. The named animation factory
  has no direct record in the 24 checked stage payloads.
- **Unresolved or untested:** The physical unit of projection scalar `+0xE0`,
  construction paths selecting modes 2/3, and other indirect consumers remain
  unresolved. Shadow-enabled parts across all model archives were not
  inventoried.
- **Deliberate exclusions and overlap:** The
  [0x1800 descriptor/controller layout](../game/files/ccs_object_types.md#0x1800-descriptor-fields-and-off-screen-pass)
  owns parsing and materialization. [Shadow VU program](shadow_vu_program.md)
  owns the uploaded VU geometry pass. General matrices, model conversion,
  visibility and packet allocation belong to [renderer coordinates](renderer_coordinates.md),
  [model runtime](model_runtime.md), [visibility](visibility.md), and
  [render submission](render_submission.md). Complete-file identities remain in
  [Retail game file identities](../game/files/file_identities.md).
- **Evidence limitations:** Static retail `SLPS_258.37` and the 24 retail stage
  archives only. Ghidra's reconstructed prototypes and vector expressions need
  instruction corroboration; incomplete xrefs do not prove absence of other
  consumers. No visual result or elapsed real-time rate is established.

## Controller drain and target state

**Observation, high confidence:** `FUN_0018B8E0` walks the singly linked controller
list at `gp-0x356C`. `FUN_0018B930` (`0x0018B930..0x0018BC5F`) returns for an empty
bucket head; otherwise it temporarily advances the render scratch pointer at
render-global `+0x1C0` by `0x3E0`, builds the ordered-controller chain, clears
controller `+0x150` and halfword `+0x154`, and restores that pointer. This resets
queued work, not the controller's dimensions, mode, or animation state.

The direct resident caller is `FUN_00108490`: the call at `0x00108598` occurs
after draw preparation and `FUN_00108690`'s gated path, and before
`FUN_00108680` and `FUN_00186000`. The drain call lies outside the branch checking
render-owner `+0x192 & 7`; the branch does not itself suppress this drain.

The following packet constructors establish the target operations independently
of a resource label:

| Function and bounds | Operation established by emitted GS register/value pairs |
| --- | --- |
| `FUN_0018C800`, `0x0018C800..0x0018CBFB` | Copies a viewport from the display object's selected surface through `TEX0_2` into the supplied target through `FRAME_2` (`0x4D`). Shadow callers select source base `display+0x1A4` and format `display+0x1AD`, supply the controller's depth region as the destination in format `0x31`, and emit a textured context-2 sprite (`PRIM=0x316`) spanning `W<<4`, `H<<4`. `ZBUF_2` (`0x4F`) masks depth writes during this copy. |
| `FUN_0018C4C0`, `0x0018C4C0..0x0018C7FF` | Writes color-target `FRAME_2`, `XYOFFSET_2=0`, depth-write mask, supplied RGBA, blend choice and framebuffer mask, then fills `[0,W] x [0,H]`. |
| `FUN_0018CC00`, `0x0018CC00..0x0018CF6F` | Installs the actual geometry target: color `FRAME_2`, `ZBUF_2` with format `0x31` and write mask, centered `XYOFFSET_2`, scissor `[0,W-1] x [0,H-1]`, and `TEST_2=0x70000`. Mode 1 protects the color target's alpha byte with framebuffer mask `0xFF000000`; modes 2/3 omit that mask. |
| `FUN_0018BC60`, `0x0018BC60..0x0018BF83` | Processes an individual bucket on the same color target with a full-target context-2 textured sprite. `TEX0_2` samples it as `PSMCT24` (bit 20), `TEXA=key\|0x8000`, and `TEST_2=(key<<4)\|0x3000B`: alpha test enabled, `GEQUAL` reference `key`, RGB-only alpha-test failure. `FRAME_2` has no framebuffer mask. |
| `FUN_0018BF90`, `0x0018BF90..0x0018C4B7` | Samples the color target through `TEX0_1`, emits `UV` and `XYZ2` rectangle corners, and composites into the controller's previously selected ordered draw environment. |

GS register names and bit positions are checked against the
[PS2SDK general-purpose GS register definitions](https://github.com/ps2dev/ps2sdk/blob/master/common/include/gs_gp.h).
Off-screen work uses context 2; final compositing uses context 1. The copy's UV
bounds come from renderer `+0x250..+0x25C` through `FUN_0010F0C0` and `vftoi4`,
whereas its destination bounds use the controller's target dimensions.

**Observation:** the selected surface is the main depth buffer. Display refresh
`FUN_001065A0` places its base at display `+0x1A4` after the two color-buffer
regions and packs that same base/format into the `ZBUF` value at `+0x1B0`.
`FUN_0010C9D0` returns `+0x1A4`; ordinary draw-state constructor
`FUN_0010C7A0` uses that getter with `+0x1AD` for its depth register.
`FUN_0018C800` therefore copies the existing viewport depth into the controller's
small depth target; it is not an untextured clear. `FUN_0018CC00` then enables
depth comparison (`TEST_2=0x70000`) while masking writes to that copied depth.
The color silhouettes can be tested against scene depth without replacing it.

Here `W=1<<controller[+0x15A]`, `H=1<<controller[+0x15B]` are target pixels.
The color base at `+0x156` is used directly as `TEX0`'s base and shifted right
five for `FRAME`; the depth base at `+0x158` is shifted right five for `ZBUF`.
These are GS base-address conversions, not EE pointers. The constructor's
descriptor-to-address mapping remains in the linked CCS document.

Both constructors initialize mode byte `+0x15C` to 1: the stores are
`0x0018B5DC` and `0x0018B6B8`. The inspected fighter, background-list and named
animation setup retains that default. Modes 2/3 below describe concrete code
branches; a retail construction path selecting them has not been established.

**Observation:** modes 2/3 clear the color target once, append every bucket's
geometry chain, and composite once with no per-bucket alpha conversion. Mode 1
processes buckets separately. Its special case is exactly one bucket whose key
is `0x80`; it skips `FUN_0018BC60` and uses textured black with alpha `0x80`.
The general mode-1 path preserves accumulated alpha while clearing RGB between
buckets, applies `FUN_0018BC60` for each bucket, and composites using the target's
alpha and owner byte `+0x15D`. Queue insertion `FUN_0018B7B0` orders distinct keys
descending; it has fifteen inline slots, reuses equal keys, and reuses an
existing neighboring bucket when full. This is a finite render queue, not an
animation-history buffer.

The mode-1 alpha step samples the RGB result as a 24-bit texture: `TEXA` supplies
bucket alpha for nonzero texels and zero alpha for zero texels, while RGB-only
failure preserves the previous destination alpha. The final special-case
composite likewise samples as `PSMCT24`; the general multi-key composite uses
`PSMCT32` so it can sample the accumulated alpha. The packet values establish
this distinction. The VU geometry pass that produces those texels is decoded in
[Shadow VU program](shadow_vu_program.md#direction-classification-and-extrusion).

## Geometry inputs and renderer ownership

**Observation, high confidence:** a controller embeds its ordered base at
`+0x10`, so the base's renderer slot `+0x3C` is controller `+0x4C`. Both
`FUN_0018B570` and `FUN_0018B650` bind it through `FUN_0010A1D0`, whose
borrowed/owned renderer contract is owned by
[renderer coordinates](renderer_coordinates.md#persistent-transform-state).

The three inspected non-descriptor construction sites (`FUN_00215950`,
`FUN_0039ABB0`, `FUN_003AD9A0`) supply the shared renderer pointer at
`0x0060919C`. A `256x256` target does not itself allocate a separate renderer.
The descriptor constructor receives its renderer from its materialization
caller; its layout and binding remain in the CCS document.

The scoped camera substitution in animation draw `FUN_001BB790`
([renderer coordinates](renderer_coordinates.md#refresh-and-binding-order))
writes only the active environment's `+0x3C` slot. It leaves the shadow
controller's own `+0x4C` binding unchanged, so the shadow geometry producer
continues to use the renderer bound to the controller.

`FUN_0018CF70` (`0x0018CF70..0x0018D737`) is the model-part producer. Beyond the
controller/geometry/strength gates already documented with `0x1800`, its EE
instructions establish this downstream contract:

| Input | Producer operation and downstream use |
| --- | --- |
| Auxiliary object's `+0x0C` | Creates both reciprocal uniform scale and uniform scale matrices. It scales the inverse-model direction, then scales the model-to-device matrix by the original value. Physical model-unit interpretation belongs to model runtime. |
| Model draw scratch `+0x110` | Supplies the model matrix. `FUN_00152138` derives its inverse; the inverse's translation XYZ is cleared before multiplying the environment direction. |
| Environment `+0xD0..+0xDC` and scalar `+0xE0` | Produces inverse-model direction at packet `+0x120` and a scale-adjusted direction times the scalar at packet `+0x130`; packet displacement W is explicitly zero. Mode 3 instead zeros displacement XYZ. A separately scaled direction goes into the bound check at `FUN_001926A0`. |
| Controller renderer `+0x40` and model matrix | Forms the model-to-device matrix before the off-screen remap. This is the configured-display projection path described in renderer coordinates. |
| Renderer bounds `+0x200/+0x204/+0x210/+0x214` and target W/H | Builds a remap with scale `W/(right-left)`, `H/(bottom-top)` and centered origin `((4096-W)/2,(4096-H)/2)`. This matrix, composed with the model-to-device matrix, is copied to packet `+0x80..+0xBF`. |
| Renderer `+0x140`, `+0x20C`, `+0x21C` | Transforms `(0,0,max(8,renderer[+0x20C]),1)` for packet `+0x50`; also supplies the depth-related packet values at `+0x6C/+0x7C`. Their general near/far contract remains in renderer coordinates. |
| Part geometry `+0x34/+0x38` | The DMA REF at packet `+0x150` references that buffer with quadword count `size>>4`; terminal tag is packet `+0x160`. |

Before emitting a packet, the producer checks projected bounds through
`FUN_001926A0(..., scaled_direction, controller_renderer, model_matrix, 0)`.
The check and its limitations are owned by [visibility](visibility.md).
It reserves `0x3E0` scratch bytes and restores the pointer on both rejection
and normal completion. A successful packet allocation is `0x170` bytes;
the queue receives its head and terminal tag through `FUN_0018B700`.

**Observation:** instructions `0x0018D410..0x0018D48C` take the cross product of
the first two model-matrix axes and dot it with the third. A negative result
swaps the two RGBA and blend-state variants used by the geometry packet.
**Inference:** this acts as an orientation-sign correction. The decompiler's unmasked vector
expression incorrectly makes the cross-product result look fully zeroed,
while the instruction at `0x0018D420` is only `vsub.w`.

The referenced upload occupies `0x003C3CA0..0x003C48DF` (`0xC40` bytes),
proven by the producer's size subtraction and DMA REF. Its direction
classification, displacement, transform and depth are decoded in
[Shadow VU program](shadow_vu_program.md#direction-classification-and-extrusion)
and [its transform and fast geometry pass](shadow_vu_program.md#transform-depth-and-the-fast-geometry-pass).
A physical distance unit for scalar `+0xE0` is not established.

## Composite units and corner table

**Observation, high confidence:** `FUN_0018BF90` gets four floating viewport
bounds through `FUN_0010F020`, then `FUN_0010EFE0` calls `FUN_0010BA00`'s
`vftoi4`. The resulting screen coordinates are integers in 1/16-pixel units.
Texture `UV` ends are independently `W<<4`, `H<<4`.

For mode 1, composite count `N` is byte `+0x15E`; modes 2/3 force `N=1`.
The table starts at `0x003FB500 + 8*N*(N-1)/2`. The ten signed integer pairs
occupy exactly `0x003FB500..0x003FB54F`:

| N | Pairs consumed in order |
| ---: | --- |
| 1 | `(0,0)` |
| 2 | `(16,16)`, `(-16,-16)` |
| 3 | `(0,14)`, `(-14,-8)`, `(14,-8)` |
| 4 | `(16,16)`, `(-16,16)`, `(16,-16)`, `(-16,-16)` |

Let `M` be unsigned byte `+0x15F` and `(a,b)` the selected pair. Instructions at
`0x0018C3F8..0x0018C470` compute `sra(M*a,4)` and `sra(M*b,4)` using signed
arithmetic shifts. The first quantity is added to **both coordinates of the
first screen corner**; the second is added to **both coordinates of the second
corner**. They are not an X/Y translation vector. Divide these resulting integer
increments by sixteen for pixel displacement. Thus unequal pair components can
resize a rectangle as well as move it, while UV coverage stays the same.

For the observed two-pass owner setup `M=14`, the two pairs move both corners by
`+14/16` and `-14/16` pixel. For `M=0`, all passes use identical bounds. There is
no frame counter or random sample in this composite routine. Its offsets are
fixed for the controller settings. No clamp of `N` is present before the table
read: the observed table provides counts 1 through 4, and bytes at `0x003FB550`
begin the unrelated string `ccToneShadeAnimRandom`. This establishes table
bounds, not that retail content requests an invalid count.

## Named shadow-animation owner

**Observation, high confidence:** the resident owner constructed by
`FUN_0039B050` has size `0x3C` and vtable `0x005DD220`; its descriptor points to
embedded name `ccBgDrawShadowAnm`. It owns a `0x160`-byte controller at `+0x28`
and a `0x120`-byte animation play object at `+0x2C`. It is distinct from the
`0x180`-byte CCS extended controller.

| Method | Concrete state and operation |
| --- | --- |
| Initializer `FUN_0039ABB0`, `0x0039ABB0..0x0039AFEF` | Resolves animation/configuration arguments; stores a rate multiplier at owner `+0x34`, projection scalar at `+0x38`, and initial play-rate halfword as float at `+0x30`. Creates/binds the play object, sets a frame through `FUN_001BB5C0` with an integer shifted left eight, selects playback through `FUN_001BAD70(...,1)`, and creates the controller. Color target is `(896,0)`, depth region `(960,0)`, size `256x256`; composite count, corner multiplier and alpha are separately supplied arguments. |
| Update `FUN_0039AA20`, `0x0039AA20..0x0039AADB` | Writes play-object halfword `+0x94` from `owner[+0x30] * owner[+0x34] * parent[+0x08]`, converted by `cvt.w.s` and reduced to sixteen bits. If play `+0xFC` is nonzero, calls `FUN_001BB210(play,rate,0)` then `FUN_001BB6F0(play)`. No separate shadow clock increment appears here. |
| Draw `FUN_0039AAE0`, `0x0039AAE0..0x0039AB43` | Saves render environment `+0xCC/+0xE0`, installs this controller and scalar, draws through `FUN_001BB790`, and restores both fields. It does not save or write direction `+0xD0` or strength byte `+0xE4`. |
| Transform refresh `FUN_0039AB50`, `0x0039AB50..0x0039ABAB` | With no transform parent at play `+0x80`, copies the local matrix at `+0x40` into the current matrix at `+0x00` and clears byte `+0x8D`; otherwise calls `FUN_0019C7C0`. |
| Playback selection `FUN_0039AFF0` / `FUN_0039B020` | Calls `FUN_001BAD70(play,1)` / `FUN_001BAEE0(play)` respectively. Detailed shared playback-state semantics belong to animation runtime. |
| Destructor `FUN_003AA340`, `0x003AA340..0x003AA3FB` | Destroys/frees controller through `FUN_0018B4C0(...,1)`, destroys/frees play object through `FUN_001B7570(...,1)`, unlinks the base owner, and optionally frees itself. |

`FUN_0018B4C0` clears the active environment's `+0xCC` if it points to the
destroyed controller, removes that controller from the global list, and destroys
its ordered base through `FUN_0010A0F0`. VRAM target addresses do not identify
heap allocations freed by this method. Per-call scratch restoration and
per-controller destruction are separate lifetimes.

**Observation:** the rate passed to `FUN_001BB210` is in 1/256-animation-frame
units: that callee adds it to player `+0xEC` and publishes integer frame with
`>>8`. The shadow update thus scales an animation-frame increment; it is not
a milliseconds accumulator. It inherits terminal clamping and looping from
[animation runtime](animation_runtime.md), and scheduling from its owner.

## Background controller and fighter consumers

**Observation, high confidence:** resident background constructor
`FUN_003AC7A0` calls `FUN_003AD9A0`, which creates twelve `0x160`-byte controllers
at background owner `+0x10C..+0x138`. All use color `(896,0)`, copied depth
`(960,0)`, size `256x256`, two composites, corner multiplier 14 and alpha
`0x20`. They borrow the same renderer. Each gets an ordered slot five below its
corresponding ordinary draw-list slot from table `0x005D6190`. Separate queues
therefore share target addresses but remain separate ordered passes.

`FUN_003ACBF0` (`0x003ACBF0..0x003ACF13`) sets environment scalar from background
`+0x34` and strength byte `0x80`, then visits all twelve selector lists. It binds
the matching controller for each list and calls each enabled child draw method
at vtable `+0x0C` when child `+0x18` is nonzero. The named shadow-animation draw
temporarily replaces that list controller with its own. The background routine
restores original `+0xCC/+0xE0` and the prior strength, capped to `0x80`, afterward.

`FUN_003ACAD0` (`0x003ACAD0..0x003ACBE3`) independently updates five child lists
at background `+0x74 + 0x10*i`: owner flag bit 0 suppresses this region, and each
child's `+0x1C` must be nonzero before virtual `+0x08` is called. For the shadow
vtable that slot is `FUN_0039AA20`. Draw flag `+0x18` and update flag `+0x1C`
are distinct. `FUN_003AD5E0` destroys these children through virtual `+0x24`,
then `FUN_003ADC60` destroys the twelve list controllers. Factory dispatch
`FUN_003AE220` indexes table `0x005B3970`; slot 27 points to `FUN_0039B050`.
Stage-specific records and battle-level scheduling remain in
[stages](../gameplay/stages.md) and [battle lifecycle](../gameplay/battle_lifecycle.md).

**Observation, exhaustive within these payloads:** the retail
`STAGE/S01.CCS` through `S24.CCS` archives were gzip-decoded and their
background payloads checked using the
[established record framing](../gameplay/stages.md#per-stage-bin_bgdata-factory-census).
The 24 payloads contain 1,487 records and zero entries with factory index 27.
The compiled `ccBgDrawShadowAnm` methods therefore do not establish direct
authorship of that class in these retail stage records. This census covers
those payloads; it does not establish absence from other construction routes
or absence of ordinary background shadows.

**Observation:** fighter resource loader `FUN_00215950` allocates another
`0x160`-byte controller at fighter `+0xE74`, ordered slot `-0x800`, with the same
`256x256`, color/depth, count 2, multiplier 14, and alpha `0x20` setup. It binds
that controller at environment `+0xCC` before finishing model initialization.
`FUN_00215E70` destroys it and clears the owning slot. This is a direct fighter
owner, distinct from the twelve background controllers and the named child.
[Character assets](../game/character_assets.md) and
[battle entities](../gameplay/battle_entities.md) own that loader and lifetime.

**Observation:** common model draw `FUN_00190F40` schedules ordinary geometry
and the shadow auxiliary geometry as separate bits. Auxiliary pointer model
`+0x9C` with flag `+0xA8 & 0x20` enables the latter even when the ordinary-model
branch is not selected. After transform preparation it calls `FUN_0018CF70` at
`0x0019109C`. Animation draw `FUN_001BB790` reaches this common model path for
enabled type-`0x0100` track targets. Detailed model preparation belongs to
[model runtime](model_runtime.md); this establishes the shadow submission route.
