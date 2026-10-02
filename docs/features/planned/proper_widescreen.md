# Proper widescreen

Provisional research for proper Hor+ 16:9 integration. Nothing here is
implemented; the basic horizontal-scale patch is described in
[Rendering](../rendering.md#native-169-horizontal-scale).
The comparative donor evidence and mapped NA2 candidates are in the
[NUN6 widescreen reference](../nun6/rendering/widescreen.md) and its
[site inventory](../nun6/rendering/widescreen_sites.tsv).

## Research coverage

- **Assigned scope:** Proper Hor+ 16:9 integration, including primary-renderer
  ownership, projection and 2D separation, mapped draw sites, bounded HUD,
  culling and shadows.
- **Exploration depth:** Read-only GhidrAssist inspection covers renderer
  construction, refresh, registration, destruction, scoped copies, both local
  2D transform branches, all four indexed local-initializer callers, all 174
  resident/BTL/ETC inventory signatures and their actual direct callees, four
  direct HUD/layout cohorts, the ordinary visibility gate and shadow geometry
  and composite inputs. Neighboring retail findings also establish selected-list
  clipping and framebuffer-sampling width limits, linked below.
- **Confirmed coverage:** Projection and 2D coefficients have different
  consumers; primary-source identity does not encompass every scoped draw;
  twenty inventory setups are viewport updates and 154 are draws; bounded
  HUD, mixed 2D/3D attachments, and borrowed shadow state need distinct
  applicability decisions. Geometry expansion does not replace selected-list
  clipping, and framebuffer sampling has a separate width gate. One gauge-site
  mapping error is corrected.
- **Unresolved or untested:** A final primary-scope rule across all screens,
  2D/edge-fill policy, anonymous draw ownership, twenty-seven weak ordinal
  mappings, remaining visibility paths, off-screen VU vector lifetime and final
  visual results remain unresolved. No proper-widescreen implementation is established.
- **Deliberate exclusions and overlap:** Retail internals belong to the linked
  renderer, HUD, draw, visibility and shadow knowledge documents; donor-mod
  evidence belongs to the NUN6 reference. This document owns their implications
  for NA228. The design document remains a draft.
- **Evidence limitations:** Static source evidence establishes field writes
  and bounded call paths, not visual quality, every indirect consumer or the
  safety of a complete widescreen implementation. Full retail identities are
  in [Retail game file identities](../../knowledge/game/files/file_identities.md).

The following findings concern candidate applicability. They do not select or
implement the remaining design choices.

## Contract

Proper widescreen means Hor+ 16:9 rather than stretched 4:3 or a crop that
loses vertical scene content.

| Layer | Required result |
| --- | --- |
| Output | Present the frame as 16:9 separately from game-memory geometry. |
| 3D projection | Gain horizontal field of view while retaining vertical composition. |
| Full-bleed 2D | Extend intended fades, masks, and backdrops to both new edges. |
| Bounded 2D | Preserve HUD, menu, text, prompt, and logo proportions and place them deliberately. |
| Cameras and effects | Keep culling, particles, shadows, cutscenes, and special cameras correct in the newly visible area. |
| Video | Give FMVs an explicit pillarbox, crop, or replacement policy instead of stretching them. |

## Implementation direction

- Replace the broad shared-writer patch with a persistent primary-renderer
  scope proven across renderer refreshes and state transitions.
- Treat primary 3D scale, the base 2D transform, transformed-2D counter-scale,
  full-bleed rectangles, bounded UI, cameras, effects, and media as separate
  layers.
- Use reference-mod full-bleed sites only after identifying their NA2 draw
  purpose and confirming the result at runtime.
- Do not copy reference-mod code or state whose lifetime and ownership are not
  established for NA2.

## Renderer refresh is broader than one object

Clean NA2 `SLPS_258.37` has one indexed direct caller of the scale writer:
`FUN_0010E460`, at call site `0x0010EC30`. The updater also stores logical
viewport fields `+0x284/+0x288/+0x28C/+0x290` and rebuilds the distinct
centered 2D matrix at `+0x1C0` through `FUN_0010EC90` / `FUN_0010ECD0`.
The direct-reference count is bounded to this import; it is not a proof that
there are no unindexed or indirect calls.

`FUN_0010F2E0` constructs a renderer and registers it through
`FUN_0010F1E0`. Registration stores the previous head in object `+0x268`
and replaces the `gp-0x3624` head with that object. In
`FUN_0010F210`, instructions `0x0010F21C-0x0010F25C` walk this list,
reload each renderer's viewport and scale fields, and call `FUN_0010E460`
at `0x0010F24C` before following `+0x268`.

This is high-confidence static evidence that the current writer replacement
forces 0.75 on every renderer updated through this path. Persistence alone
does not establish primary-renderer scope. A primary-only candidate must
distinguish the state owner before selecting the coefficient; the linked-list
refresh must retain each other state's intended values. Which state should
receive that selection remains unresolved here.

Renderer construction, ownership and lifetime are owned by
[Persistent transform state](../../knowledge/runtime/renderer_coordinates.md#persistent-transform-state)
and [2D draw ownership](../../knowledge/runtime/draw_2d_owners.md). Their
implications for widescreen:

- Context identity and renderer identity differ: a context can borrow an
  existing renderer, so selecting every new context would include contexts
  sharing one renderer.
- The default renderer can be identified through `0x0060919C`, but the boot
  calls alone do not prove it is the only primary scene renderer.
- Embedded renderers and additional owned or borrowed contexts defeat a
  single-allocation assumption; their screen and pass roles remain to be
  attributed.
- A resource-linked renderer is registered through the same constructor, so a
  global scale replacement reaches it too.
- A borrowed 2D draw owner such as `FUN_001834B0` refreshes the default
  renderer's viewport with scales 1/1, so constructor-only selection cannot
  express all later ownership.

`FUN_0010F140` removes a renderer from the `+0x268` list, and
`FUN_0010F280` calls that unlinker before optional deallocation. Renderer
selection therefore needs a lifetime rule, not a remembered heap address.
`FUN_001065A0`, call `0x00106F30`, refreshes the whole list after updating
display dimensions and register packets. This establishes a display-refresh
gate; it does not establish how often that gate executes.

A scoped state lifetime is established by
[renderer binding order](../../knowledge/runtime/renderer_coordinates.md#refresh-and-binding-order).
`FUN_001BB790` saves the active context's renderer when scene play object
`+0x10C` supplies a camera, lazily allocates a `0x2B0` copy at scene
`+0x110`, copies the saved state through `FUN_001BB9D0`, temporarily binds
that copy, refreshes its camera and draws, then restores the previous pointer.
The copy includes projection scales and the 2D matrix; this path performs no
constructor/list registration. Consequently, a primary selection based only
on registered-pointer identity would miss these scoped scene states. A scale
inherited from the primary source can propagate through the copy, but a final
scope rule must distinguish that inheritance from unrelated renderer owners.

## Projection, reference coordinates and 2D are separate decisions

The retail renderer investigation is owned by
[Renderer and coordinate systems](../../knowledge/runtime/renderer_coordinates.md).
The following source sites identify the particular decisions exposed by the
donor comparison. ELF file offsets in this table equal resident addresses minus
`0x000FFF00`.

| NA2 resident / ELF file site | Source fact established in this pass | Candidate applicability |
| --- | --- | --- |
| `0x0010ECC0` / `0x0000EDC0` | Stores projection scales at renderer `+0x274/+0x278`. `FUN_0010DAF0` uses them in matrices `+0x40`, `+0x100`, `+0x140` and `+0x180`. | Horizontal 0.75 with vertical 1 is the existing basic projection candidate. Scoping remains unresolved. |
| `0x0010DCA0` / `0x0000DDA0` | The 512 reference-width numerator supplies both horizontal and vertical diagonal values in the temporary matrix composed into `+0x100`. `+0x2A0` separately stores the device-width focal coefficient. | Donor 688 changes both reference-space axes, so it is not a pure horizontal field-of-view correction. |
| `0x0010DF00` / `0x0000E000` | The reference-space vertical translation is viewport height `+0x290 / 2`; horizontal translation uses width `+0x28C / 2`. | Donor 2.3125 changes reference-space vertical placement. Its necessity for NA2 remains undecided. |
| `0x0010EC38` / `0x0000ED38` | The updater supplies independent 1/1 base 2D scales through `FUN_0010EC90` after writing 3D scales. | A base 2D squeeze is an additional choice; the current writer patch does not implement it. |
| `0x0010EE7C` / `0x0000EF7C` | `FUN_0010ECD0` divides the horizontal viewport-origin contribution by 512 when composing logical coordinates into GS coordinates. A zero origin makes this contribution zero. | Donor 672 changes nonzero viewport translation, not the ordinary zero-origin width scale. |
| `0x0010F3E8` / `0x0000F4E8` | The constructor supplies projection scales 1/1 to `FUN_0010F430`, which forwards them to the shared updater. | A one-time constructor change is broader than primary ownership and does not cover later explicit 1/1 updates. |
| `0x0010BB5C` / `0x0000BC5C` | Local 2D initializer stores the caller's uniform scale into horizontal `+0x10` after storing it into vertical `+0x14`. | Donor additive bias and exact proportional counter-scaling are distinct candidate behaviors. |

`FUN_0010DAF0` also constructs matrix `+0xC0` from focal length,
display width/height, near/far values and the view matrix without loading
`+0x274/+0x278` for that matrix. Consequently, the current scale patch does
not widen every projection representation. The consumer of `+0xC0` must be
identified before classifying this as a culling fault; the independent matrix
is an observation, premature culling is a hypothesis.

`FUN_0010E270` projects world data through renderer `+0x100` into logical
screen output, while `FUN_0010E320` reconstructs a world point from
`x-256`, `y-192`, depth, focal field `+0x2A0` and inverse view `+0x80`.
That reconstruction contains no division by `+0x274/+0x278`. Matching the
forward and reverse coordinate paths is a separate applicability question for
screen-attached effects; a visible fault is not established by this inspection.

## Exact 2D compensation versus donor tuning

For a proposed centered base 2D horizontal scale `s=0.75`, the donor
reference establishes the logical map `x' = 0.75(x-256)+256`. Mathematical
edge-to-edge compensation therefore gives logical bounds
`[-85 1/3, 597 1/3]`, a width of `682 2/3`. These are derived candidate
coordinates, not values already implemented by NA228. The base 2D transform
and `+0x274` projection scale remain independent.

Under that proposed base transform, a transform record's uniform scale `q`
can retain its pre-existing logical rectangle span with local horizontal scale
`q / 0.75 = 4q/3`. In contrast, the donor hook uses `q + 0.341796875`,
giving net scale `0.75q + 0.25634765625`. The two formulas differ during
scale animations; at `q=0`, the additive formula still has nonzero horizontal
extent. This describes logical geometry before output presentation; it does
not establish the proportions of a physical displayed sprite. This algebra
does not decide whether the donor intentionally wants that behavior. NA2's
scale animations and caller ownership must determine where either candidate
applies, especially for framebuffer effects which can require full-frame
coverage rather than bounded-sprite sizing.

The donor rectangle helper's `x=-128,width=768` exceeds exact compensation
by 12.5% and maps to `[-32,544]` under the proposed base transform.
The donor's ambient `f31` vertical origin and its competing writers are
documented in the [NUN6 reference](../nun6/rendering/widescreen.md#2d-horizontal-scale-hook-and-the-f31-bias).
Neither overfill nor ambient-register state establishes the final NA2 policy.

The complete indexed NA2 caller set of `FUN_0010BB10` was inspected:

| Retail caller | Scale and owner evidence | Applicability |
| --- | --- | --- |
| `FUN_001A0B80`, call `0x001A18EC` | Initializes the `0x1D00` framebuffer-blur parameter's local draw record with constant scale 1 and rotation 0; its retail descriptor is established in [CCS object types](../../knowledge/game/files/ccs_object_types.md#confirmed-identities). | Full-frame effect coverage and bounded-sprite proportions are different requirements. Other resource types in this large materializer are outside this claim. |
| `FUN_00214170`, call `0x002141B4` | Uses object scale `+0x58`, rotation `+0x5C`, context `+0x40`, and caller-provided half-extents/offsets from `+0x84..+0x90`. | A common initializer change reaches animated, caller-sized geometry, not just 512-wide defaults. |
| `FUN_00250690`, call `0x002506E4` | Uses the same fields from a referenced object at parent `+0x2C`. | The same transform can be drawn through another owner; its second occurrence is not a separate scale policy. |
| `FUN_0030DC30`, call `0x0030DC94` | Uses object scale `+0x80`, rotation `+0x84`, a local record at `+0x40`, and a selected context in `manager+0x2950+index*0x40`; restores the previous context after drawing. | Counter-scaling must account for the selected context's base transform rather than assuming the default context. |

`FUN_0010A520` obtains the renderer from context `+0x3C`; both its
untextured and textured branches install local X/Y scale, rotation and origin,
compose with renderer `+0x1C0`, then transform all four corners. This verifies
the candidate's transform route and context dependency. Complete bounded-draw
classification is owned by [2D draw ownership](../../knowledge/runtime/draw_2d_owners.md).

That investigation's [clipping ownership](../../knowledge/runtime/draw_2d_owners.md#clipping-and-coordinate-ownership)
also establishes that normal render-list finalization installs the selected
renderer viewport's scissor. Expanded geometry therefore does not, by itself,
establish expanded visible coverage. Proper-widescreen selection must account
for the draw list and its viewport as well as the rectangle's transform.

## Visibility and off-screen rendering

[Visibility bounds and culling](../../knowledge/runtime/visibility.md) establishes
the ordinary model gate and the shared VU wrapper. The instruction range
`0x00191230-0x0019127C` in retail `FUN_001910E0` composes renderer
`+0x40` with the model transform and sends that matrix to `FUN_001926A0`,
which receives viewport vectors `+0x200/+0x210` and secondary bounds
`+0x220/+0x230`. Classification zero skips the subsequent model packets.
Thus the ordinary inspected gate receives the horizontally scaled device
projection. The independent `+0xC0` matrix is not evidence that this gate
uses a narrow frustum. Exact VU comparisons and other visibility paths remain
with the visibility owner.

That owner's [VU classification](../../knowledge/runtime/visibility.md#vu-point-tests-and-classification)
now establishes the ordinary entry `0x1F` as a conservative eight-corner
viewport/depth decision using projected X/Y/W and the supplied limit vectors.
Results distinguish rejection (0), containment inside the larger limits (1)
and retained geometry requiring the other packet variant (2). This supports
the scaled-matrix applicability above without a blanket frustum-expansion
change. Off-screen entry 0 uses sixteen points, but its additional-vector
lifetime and complete geometric meaning remain unresolved.

[Shadow rendering](../../knowledge/runtime/shadow_rendering.md) establishes a
different ownership constraint. Named shadow owner `FUN_0039ABB0` creates
a controller through `FUN_0018B650` using the default renderer pointer at
`0x0060919C`, then chooses a 256-by-256 target. This pass borrows the
renderer; the smaller target does not establish a separate renderer-list node.

`FUN_0018CF70` obtains that renderer through controller `+0x4C`, composes
its `+0x40` with model geometry, uses the shared visibility wrapper with
VU entry 0, and remaps floating viewport bounds into the chosen off-screen
dimensions. It separately consumes `+0x140` in constructing the projection
vector. `FUN_0018BF90` composites the texture over bounds obtained from
the same renderer through `FUN_0010EFE0`; its target UV dimensions are
independent of those destination bounds.

The proper-widescreen implication is that primary projection, shadow geometry,
target remapping and final composite bounds must agree even when they share
one state object. Selecting the default renderer cannot, by itself, exclude
this shadow pass from the scale change. No target-size expansion or shadow
correction is selected by the current evidence. The off-screen VU extra-vector
meaning and remaining content-specific consumers remain unresolved.

The shadow owner's [binding evidence](../../knowledge/runtime/shadow_rendering.md#geometry-inputs-and-renderer-ownership)
also shows that the scoped camera copy changes the active context `+0x3C`
without replacing shadow controller `+0x4C`. Ordinary scene drawing and its
shadow producer can therefore retain different renderer bindings during that
scope; a final inheritance rule must account for both.

The [sampling texture consumer](../../knowledge/runtime/texture_material_runtime.md#sampling-texture-resource-consumer)
is another framebuffer dependency: `FUN_0019DCD0` returns when render width
exceeds 512, and otherwise halves width and height independently until they
fit the texture. This establishes a constraint on any candidate that changes
render dimensions. It does not establish a fault for projection-only widening
or justify a sampling change.

## Bounded review of the rectangle inventory

The [donor site inventory](../nun6/rendering/widescreen_sites.tsv) contains a
bounded population of 174 NA2 resident, BTL and ETC setups relevant to this
pass. Each was reread through MCP for 128 bytes beginning at the candidate
instruction. All 174 still contain `mtc1 zero,f12`, the 512.0 materialization
and paired `mov.s f13,f12`; decoding the following live JAL operand establishes
the actual NA2 downstream family below. This is current source-byte evidence,
independent of ordinal similarity. It verifies setup/callee shape, not the
screen identity or suitability of a widescreen edit.

| Program | Viewport updater `0x0010E460` | Draw `0x00183F10` | Draw `0x00183DF0` | Draw `0x00183E80` | Draw `0x00309C50` | Immediate draw `0x00353850` | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Resident `SLPS_258.37` | 13 | 30 | 14 | 1 | 5 | 0 | 63 |
| `BTL.BIN` | 6 | 19 | 7 | 1 | 57 | 8 | 98 |
| `ETC.BIN` | 1 | 12 | 0 | 0 | 0 | 0 | 13 |

The twenty viewport setups are unsuitable for rectangle-origin expansion:
they establish a rendering state rather than allocate or draw a fill. The
remaining 154 are draw setups. The donor selects all 142 resident/BTL draw
setups in this population and leaves all twelve ETC draw setups unchanged.
The latter remain a semantic decision for NA2; their draw callee and geometry
alone do not justify either widening or preserving them. Source-byte checks
do not resolve the twenty-seven weak resident/BTL ordinal mappings flagged
by the reference inventory.

The twelve ETC draw-setup file offsets are `0xC920`, `0x1010C`,
`0x10470`, `0x13184`, `0x13FE0`, `0x142E8`, `0x1E9AC`,
`0x1EC28`, `0x1ECD4`, `0x20330`, `0x23AB4` and `0x244F8`.
The excluded viewport setup is file `0x10708`. The inventory owns the full
row/address mapping; these offsets define the fully checked negative cohort.
No ETC screen attribution is inferred here.

Retail [2D draw ownership](../../knowledge/runtime/draw_2d_owners.md) establishes
that the common four-slot consumer transforms an origin with `+0x1C0` and
multiplies width/height by the matrix diagonals. Its confirmed global fade,
table-selected opacity transitions and playback covers are screen-sized
coverage candidates. Slot phase and color behavior stay independent of
geometry. The same document distinguishes float immediate rectangle
`0x00353850` from integer rectangle `0x00353F40`: neither API itself means
full-screen. Its direct BTL cohort includes a full-frame Practice Settings draw
at live `0x00882320` and a bounded panel draw at live `0x0087D2B8`.
The repeated 512-by-384 inventory is therefore only one subset of the
immediate API's caller population.

## Bounded HUD and mixed-coordinate candidates

[Battle HUD](../../knowledge/gameplay/battle_hud.md) identifies the root owners
and their inherited layout, so donor coordinate pairs can now be separated
from full-frame fills. Overlay sites below give complete-file offsets and
preserved addresses `D`; live NA2 addresses equal `D+0x40`. Current bytes,
not an imported function label, determine each candidate instruction.

| NA2 file / preserved site | Verified source behavior | Donor evidence and unresolved decision |
| --- | --- | --- |
| BTL `0x66A9C` / `D 0x0071A95C`; `0x66AAC` / `D 0x0071A96C` | Top-panel initializer stores root X 6/506 by internal side and Y 10 at parent `+0x30/+0x34`. Child drawing recomputes base plus presentation offset. | Donor -31/536 changes a group anchor. Final top-panel margins remain a layout choice; this is not a width replacement for every child sprite. |
| BTL `0x68C24` / `D 0x0071CAE4`; `0x68C88` / `D 0x0071CB48` | The lower support-block draw loads X 120/392, mirrors horizontal scale for the second side, and reuses the selected base for its sprites, text and icon. Its ownership is established in [Substitution](../../knowledge/gameplay/battle_hud.md#support-gauge). | Donor 30/480 separates the two groups. The reference's left NA2 site is corrected below; exact donor placement is not accepted by structural similarity. |
| BTL `0x5B870` / `D 0x0070F730`; `0x5B880` / `D 0x0070F740` | The [lower item-panel constructor](../../knowledge/gameplay/battle_item_inventory.md#na2-panel-layout) initializes root X 66/446 and common Y 340. | Donor -16.5/528 moves a whole item-panel root, separately from support-block anchors. Suitable margins remain undecided. |
| BTL `0x32C4` / `D 0x006B7184`; `0x32EC` / `D 0x006B71AC` | The [combo-number presentation owner](../../knowledge/gameplay/battle_lifecycle.md#root-component-forest) uses animated offset plus 96, or plus 416 followed by subtraction of 30, for sprite/text drawing. Its conditional 3D-object path calls `FUN_0010E320` at `D 0x006B73F8` with depth 500. | Donor 6/464 changes this mixed owner. Anchor placement and forward/reverse projection agreement are linked; treating it as an isolated 2D constant pair would miss the 3D attachment. |

**Contradiction, resolved by current bytes:** the donor reference lists the
left 120.0 NA2 gauge load at file `0x68C30`, `D 0x0071CAF0`.
MCP bytes there are `00 00 00 00` (NOP). The actual instruction is
`lui v0,0x42F0` at file `0x68C24`, `D 0x0071CAE4`, followed by
`mtc1 v0,f21` at `D 0x0071CAE8`. The complete retail prologue begins
at `D 0x0071CAB0`; the imported `FUN_0071CAF0` begins inside this body.
The right load at `D 0x0071CB48` remains `lui v0,0x43C4` (392.0).
The donor document is retained as read-only comparative evidence; the corrected
NA2 source site above is the applicability result of this pass.

The HUD's central clock uses bounded 38-by-62 digit rectangles centered at
logical X 256 for one digit, or 271/241 for two; unlimited mode uses a
78-by-62 rectangle. Those are retail resource dimensions and group anchors,
not full-frame widths. The parent and child scales, inherited contexts, and
rotating gauge elements remain separate from root-anchor placement. Generic
sprite `FUN_001CC3A0` has both axis-aligned and enabled-rotation paths, and
both consume the renderer's 2D matrix through `FUN_0010EFA0`. A candidate
must preserve those paths' proportions without assuming every caller rotates.

## Remaining proper-widescreen decisions

The draft's Hor+ requirement fixes the aspect conversion ratio
`(4/3)/(16/9)=0.75` when vertical composition is retained. It does not
choose a renderer owner, a 2D coordinate policy or a margin for each HUD
group. The mapped constants and paths above make those choices separate and
reviewable:

| Decision | What the evidence now establishes | Still undecided |
| --- | --- | --- |
| Primary 3D scope | The default renderer is shared by battle camera output, rectangle contexts and named shadows; scene-camera drawing temporarily clones and binds renderer state. Display refresh replays registered states separately from camera-matrix refresh. | Selection across all screens and nonprimary resource-linked/embedded owners; how scoped copies inherit the chosen primary policy. |
| Logical reference projection | `+0x100` is consumed by screen projection; the 688 numerator changes both reference axes. `FUN_0010E320` is not a general inverse of the scaled/offset forward path. | Whether reference-space or screen-attached effects need a separate correction; no basis is established for copying every donor coefficient. |
| Base 2D and framebuffer effects | `+0x1C0` is independent of 3D scale. A 0.75 base transform, exact edge compensation and local counter-scaling have distinct algebra; the common local initializer includes framebuffer blur. Sampling has a separate 512 render-width gate. | Which draw environments use the proposed base squeeze and which effect records need full-frame compensation; final exact versus overscan bounds and applicability of render-dimension changes. |
| Full-frame fills | The bounded signature population and direct callees are verified, with named fade and Practice backdrop candidates; normal lists impose their selected renderer's viewport scissor. | Caller semantics for anonymous/weak mappings and the twelve unchanged ETC draws; selection beyond the repeated signature population and viewport/clipping agreement. |
| Bounded layout | Top panels, lower item roots, lower support blocks and the central clock are different owners; combo presentation also creates a 3D attachment. | Per-group margins and final placement values; a donor anchor is comparative evidence rather than an accepted NA2 value. |
| Visibility | The ordinary inspected model gate and bounded background cohort consume scaled `+0x40`, not independent `+0xC0`. Entry `0x1F` evaluates eight corners against viewport/depth planes and distinguishes rejection from two retained classes. | Off-screen entry 0's additional-vector lifetime, remaining rejection paths and the independent matrix's consumers. A blanket culling expansion is not established as necessary. |
| Shadows | Geometry, target remap and composite depend on the borrowed renderer while target resolution remains separate. Scoped ordinary-camera rebinding leaves the controller binding unchanged. | Whether any projection/composite correction is needed; how primary/scoped inheritance applies to the controller. Target-size expansion is not justified by the inspected ownership alone. |
| Output and media | The draft treats output presentation and video fit as distinct policies from game-memory projection. | Final output integration and video fit policy; no new media investigation was performed in this pass. |

The [visibility caller inventory](../../knowledge/runtime/visibility.md#bounded-resident-caller-inventory)
also records background owners whose retained classification gates angle,
UV, countdown or random-state advancement. A wider retained region can
therefore affect their presentation state as well as submission. That is a
source-derived dependency for future widescreen decisions, not an observed
fault or authorization to alter those owners.

This completes the bounded static integration pass described in Research
coverage. It leaves the listed design choices and evidence limits explicit;
the existing basic patch remains the only implementation described here.

## Validation

Run with PCSX2's 16:9 presentation enabled and emulator widescreen cheats
disabled. Trace the primary renderer's scale and 2D matrices across boot,
menus, overlays, battle, cutscenes, and return transitions. Test each candidate
coefficient and draw cohort independently.

Compare matched 4:3 and 16:9 captures across boot, menus, selection screens,
battle and Practice, ADV, Collection, effects, transitions, and every FMV
class. Accept a site only when it adds intended horizontal coverage, preserves
vertical composition and bounded-element proportions, fills required edges,
and introduces no newly visible garbage or premature culling.
