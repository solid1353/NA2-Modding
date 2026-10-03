# Battle HUD

This document records the ordinary battle HUD's object ownership, data bindings,
update/draw order, visibility and teardown in unmodified retail NA2
(`SLPS-25837`). Complete-file identities and the overlay address conversion
belong to [Retail game file identities](../../game/files/file_identities.md).
Resident addresses are ELF virtual addresses. BTL addresses below are live
unless prefixed `D`; a preserved Ghidra address `D` is live minus `0x40`.

## Research coverage

- **Assigned scope:** the complete ordinary battle HUD object graph:
  construction, callback/update/draw order, gameplay-data bindings,
  visibility, top panels, support gauge, clock, root presentation forest
  (combo digits, prompts, glyphs, markers, popups, notices), meter
  storage/display patterns, and teardown.
- **Exploration depth:** the resident session constructor, service, and
  destructor; all four top children; the HP damage trail; top and clock
  hide/show state machines; shake request and consumer; lower-panel
  update/draw and support sampling; the support-gauge draw, palette, and
  rectangles; render-context ownership; the root's two presentation
  callbacks, its eight children's bindings, the combo digit object, and the
  prompt placement/activation helpers; the 94 character-cell rows, nine cell
  rectangles, 11 clock rectangles, dynamic chakra constants, and direct
  hide/show/shake call sites in resident code and BTL.
- **Confirmed coverage:** the bounded ordinary HUD graph, owned versus
  borrowed render resources, per-side fighter bindings, independent lower,
  top, central and root gates; update/draw order; presentation-only meter
  storage and the HP trail; support-gauge geometry, tint, and glyph binding;
  clock digits and feedback; combo-digit fade, shake, and color rows; prompt
  placement modes and activation ramps; slide and shake transitions; direct
  visibility requests; and subordinate destruction order.
- **Unresolved or untested:** original class names; semantic names of the
  character-keyed decorative atlas cells, the two generic chakra helper
  vectors, and the command-prompt subtypes; exact artwork appearance; indirect
  or unindexed producers of the visibility/scale/feedback-enable fields; and
  whether cut-in or special-scene HUD variants share this graph. No
  whole-program absence claim or measured elapsed-time claim is made.
- **Deliberate exclusions and overlap:**
  - [Battle lifecycle](battle_lifecycle.md) owns session, graph, and root
    allocation lifecycle; [Battle item inventory](../projectiles_and_items/battle_item_inventory.md)
    owns wheel storage and formulas.
  - [Support mechanics](../characters/support_mechanics.md) owns the support resource the
    gauge displays; [Combo accounting](../combat/combo_accounting.md) owns the combo
    count publication.
  - [Ultimate Jutsu](../characters/ultimate_jutsu.md) owns the presentation that hides and
    shows the HUD.
  - Localized name anchors belong to
    [Battle HUD character-name renderer](../../localization/ui/battle/character_names.md).
- **Evidence limitations:** conclusions are static. The preserved BTL import
  has split functions and incomplete xrefs, so absence of an xref is not proof
  of an absent caller.

## Battle-session ownership and order

Resident `FUN_001EF330` creates the ordinary presentation objects after
publishing both fighters in the battle manager. The `0x38`-byte session owns:

| Session field | Object | Construction |
| ---: | --- | --- |
| `+0x20` | `0xC8`-byte item manager, including both lower item/support panels | Resident `0x00373A20`; panel ownership is detailed in [Battle item inventory](../projectiles_and_items/battle_item_inventory.md#na2-ownership) |
| `+0x24` | `0x68`-byte side-0 top panel | BTL `0x0071A840(object, 1, manager[+0x4C])` |
| `+0x28` | `0x68`-byte side-1 top panel | Same constructor with side argument `2`, manager `+0x74` |
| `+0x2C` | `0x44`-byte central display owner | BTL `0x0087E880` |

Resident `FUN_001F03E0` reaches these after the battle graph's three phase
walks and auxiliary presentation work. It first updates the item manager
through `0x003747C0` when session update mask `+2 & 0x100` is nonzero, then
draws it through `0x00374D90` when draw mask `+4 & 0x100` is nonzero. It then
walks top panels in side order `0,1`, updating each through `0x0071AF30` when
`updateMask & 0x600` is nonzero and drawing it through `0x0071B2E0` when
`drawMask & 0x600` is nonzero. Each side's update precedes that same side's
draw. Central-owner update/draw (`0x0087EB40/0x0087EDD0`) follows, gated by
`0x200`, followed by root presentation work. Mask construction is owned by
[Pause and replay](pause_and_replay.md#controller-fields-and-mask-construction).

The top-panel entrypoints are direct session calls. They are not virtual node
callbacks in a fighter registry. The item manager has additional battle-state
and own-flag gates: `FUN_003747C0` updates both lower panels through
`0x00712380` when manager `+0xB8 & 2` is clear and battle-state result from
`0x00250820` is `0`, `3` or `4`. Its unrelated list work has separate gates.

## Top-panel construction

The outer constructor at live `0x0071A840` calls initializer
`0x0071A8D0`; its full body is preserved at `D 0x0071A890..0x0071AB60`
(BTL complete-file `0x669D0..0x66CA0`). It translates constructor side `1/2`
to internal side byte `0/1`, and binds the corresponding fighter from manager
`+0xDE4/+0xDE8`. Two `0x40`-byte sprite/render objects are initialized through
resident `0x00110340` and `0x0010A1D0`: primary ID `0x80` with the resident
renderer value at `0x0060919C`, and secondary ID `0x83` with zero as the third
argument. Resident `FUN_0010A1D0` establishes that the primary context borrows
that renderer, while each secondary context allocates and owns its own
`0x2B0`-byte renderer at context `+0x3C`. Context byte `+7` records that
ownership; `FUN_0010A0F0` deletes only an owned renderer. This distinguishes
the two render contexts from their sprites and borrowed textures. Child
allocation and initialization then proceed in this order:

| Parent field | Allocated bytes | Child initialization/binding | Observed role |
| ---: | ---: | --- | --- |
| `+0x18` | `0x40` | Primary render object | Shared by all four top children |
| `+0x1C` | `0x40` | Secondary render object | Additionally bound to child `+0x28` |
| `+0x20` | `0x1C` | `0x0071B3A0`, then `0x0071B420(child,parent)`; sprite binding `0x0071B580` | Decorative discs, panel frame and character-keyed atlas cell |
| `+0x2C` | `0x0C` | `0x0071BB70`, then `0x0071BBD0(child,parent)`; binding `0x0071BCB0` | Character name |
| `+0x24` | `0x28` | `0x0071BF00`, then `0x0071BF60(child,parent)`; binding `0x0071C030` | HP current/trailing display |
| `+0x28` | `0x6C` | `0x0071D2C0`, then `0x0071D3E0(child,parent)`; bindings `0x0071D6B0/0x0071D6F0` | Chakra fill, reserved-chakra segment, thresholds and animated feedback |

The constructor finally calls `0x0071ABB0` to reset presentation state.

| Top-parent field | Established content |
| ---: | --- |
| `+0x00/+0x04` | Effective draw X/Y, recomputed by draw |
| `+0x08` | Scale, initialized `1.0` |
| `+0x0C` | Internal side byte `0/1` |
| `+0x10` | Constructor's third argument (selected character ID at session callsite) |
| `+0x14` | Bound fighter pointer |
| `+0x18/+0x1C` | Owned primary/secondary render objects |
| `+0x20/+0x24/+0x28/+0x2C` | Four owned top children |
| `+0x30/+0x34` | Base X/Y: `(6,10)` for side 0, `(506,10)` for side 1 |
| `+0x38/+0x3C` | Additive X/Y presentation offset |
| `+0x40/+0x44` | Transition values; `+0x44` is Y-slide velocity |
| `+0x48` | Transition selector, initialized `3` |
| `+0x4C/+0x50` | Hide/show substates, reset to zero |
| `+0x54` | Child-draw visibility byte, initialized zero |
| `+0x58/+0x5C/+0x5E/+0x5F/+0x60/+0x64` | Shake substate, update count, sample duration, sample count, amplitude and initial table index; initialized by the shake request rather than parent reset |

## Child update and draw boundaries

Top update `0x0071AF30` visits non-null children at `+0x20`, `+0x24`,
`+0x28`, `+0x2C`, in that order, before the parent transition. It does not
gate those calls with parent visibility. Draw `0x0071B2E0` skips every child
when `+0x54 == 1`; otherwise it recomputes effective X/Y as base plus offset,
then visits the same four pointers in the same order. It restores the resident
render-context global after the calls.

HP display state is separate from fighter health and is updated while hidden.
Its sampling, delay and trailing segment are documented in
[HP and name bindings](#hp-and-name-bindings).
The support gauge belongs to the lower item panel's `+0x1C`, and its draw
wrapper samples its state before its visibility check. This means the
top panel's four-child sequence does not update the support gauge; its owner
is the item-panel root described in [NA2 HUD wheel](../projectiles_and_items/battle_item_inventory.md#na2-hud-wheel).

The lower-panel update additionally calls support pulse updater `0x0071CA00`
after the selected-item and list updates, before clearing the panel's event
bytes. That updater first calls sampler `0x0071C810`, then advances the pulse
state. The panel's draw wrapper `0x0071D270` calls that same sampler again,
then draws through `0x0071CAF0` only when support byte `+0x0A` is nonzero.
Thus ordinary update-and-draw samples support twice but advances its pulse
once; an update/draw mask can separate those operations. The tail call is at
`D 0x00712734` and the wrapper at `D 0x0071D230..0x0071D26C`. Gauge geometry
and colors are described in [Support gauge](#support-gauge).

| Child | Update entry | Draw entry | Data/render pattern |
| --- | ---: | ---: | --- |
| Frame/discs `+0x20` | `0x0071B5B0` | `0x0071B720` | Parent/fighter status controls disc speed; three phases live at child `+0x10..+0x18`. The shared panel anchor, scale and side determine placement. |
| HP `+0x24` | `0x0071C000` | `0x0071C0E0` | Samples fighter `+0x6C`; normalized current/trailing display fields and a delay remain child-owned. Draw also stores its current/max ratio at child `+0x20` and selects a color category at `+0x24`. |
| Chakra `+0x28` | `0x0071E070` | `0x0071EE70` | Samples current and reserved chakra, then advances display/feedback state. Draw submits fill/threshold sprites, optional animated feedback and a rotating icon. |
| Name `+0x2C` | `0x0071BCC0` | `0x0071BE20` | Character-keyed resident rectangle table, plus a conditional fighter-state name substitution. It consumes the parent anchor/scale/side. |

### Frame and character-keyed cell

The `0x1C`-byte child stores parent at `+0`, two owned sprites at `+4/+8`,
disc-speed scalar at `+0x0C`, and three float phases at `+0x10..+0x18`.
Initializer `0x0071B420` obtains `battlegauge`, creates the two sprites through
resident `0x0037B670`, and selects an atlas cell using all 94 four-byte records
at live `0x008C4160..0x008C42D7`: `{s16 characterId, u8 cell, padding}`.
The keys are `1..93` followed by `0`; cell values are `0..7`. An unmatched key
uses cell `8`. Nine eight-byte `(u,v,w,h)` records at `0x008C4110..0x008C4157`
provide eight 30-by-30 cells in the grid `(1/33/65,1/33/65)` and default
`(17,17,30,30)`. Static selection alone does not identify the depicted symbol.

Update `0x0071B5B0` selects speed target `8.0`, step `0.4`, when the bound
fighter exists and byte `+0x63 & 0x20` is set; otherwise target `1.0`, step
`0.1`. It advances and wraps all three phases. Draw `0x0071B720` submits those
three discs first, mirrors their X displacement and rotation for side 1, then
draws the panel/frame pieces and the chosen cell. Initialization, sprite
ownership and the full character loop are at `D 0x0071B360..0x0071B56F`.

### HP and name bindings

The HP child owns one sprite and borrows its parent. Its maximum at `+0x1C`
is initialized to `1.0`; current HP at `+8`, trailing HP at `+0x0C`, and
delay at `+0x10` are separate display fields. Draw `0x0071C0E0` stores
`current/max` at `+0x20` and selects tint category `0` above `0.5`, `1` above
`0.1` through `0.5`, and `2` at `0.1` or lower. Its geometry helper
`0x0071C530` returns the filled segment's endpoint, Y, width and height using
that draw-computed ratio and the parent effective position. The top-parent
wrapper `0x0071AD10` delegates to it when child `+0x24` exists, otherwise
writes a zero vector. A call to the geometry helper alone does not refresh
HP or that ratio; hidden parent drawing skips the ratio-producing call.

The HP child's constructor at Ghidra `0x0071BF20` initializes trailing HP
from fighter `+0x6C` and clears the delay. Each update (live `0x0071C000`,
Ghidra `0x0071BFC0`, called from file `0x67060`) samples that fighter field
into current HP. When current and trailing HP are equal, it sets the delay to
`100`; otherwise it decrements a positive delay. Once the delay reaches zero,
trailing HP moves toward current HP by `0.01` per update, clamped at current
HP. The renderer draws a separate segment only when trailing HP exceeds
current HP; the segment covers their difference and uses RGB
`(0x4A, 0x04, 0x09)`. Current HP and the trail are display fields; their
updates do not write fighter health.

The name child stores parent, sprite and displayed character key at
`+0/+4/+8`. Initialization selects an eight-byte rectangle from resident
`0x005B13A0`, keyed by `characterId-1`; invalid indexes use the final record
under the count at `0x005D46E8` (retail count `96`). Update `0x0071BCC0` only
performs a dynamic key substitution when parent selected key is `0x25` and a
fighter exists. Major action state `+0x18E == 0` and action index `+0x190 == 3`
select key `0x5E`; leaving that condition restores `0x25`. The bounded update
does not generalize this substitution to every character. These fields and
the complete conditional are at `D 0x0071BB30..0x0071BDD3`. Character-name atlas
positioning remains owned by the linked localization document.

### Chakra storage and display

The `0x6C`-byte chakra child has this layout, established by its initializer,
update chain, all three draw helpers and destructor:

| Offset | Established role |
| ---: | --- |
| `+0x00/+0x04/+0x08` | Parent, borrowed `battlegauge` resource, refreshed fighter pointer |
| `+0x0C/+0x10/+0x14` | Owned fill, overlay/threshold and animated marker sprites |
| `+0x18/+0x1C` | Marker-cell update counter and marker scale |
| `+0x20` | Fill category `0..4` |
| `+0x24/+0x28` | Current and previous chakra samples |
| `+0x2C/+0x30` | Requested and displayed reserved-chakra amount |
| `+0x34` | Display total, current plus requested reservation, upper-clamped to the bar maximum |
| `+0x38/+0x3C` | Eased animation-rate scalar and pulse phase |
| `+0x40/+0x41` | Reserved-segment blink selector and two-update counter |
| `+0x44/+0x48/+0x4C` | Three owned `ANM_ef_gau02a/01a/00a` animation objects |
| `+0x50/+0x51/+0x52` | Three feedback-active bytes |
| `+0x54/+0x58` | First/third feedback fade values |
| `+0x5C` | Borrowed secondary render object from top parent `+0x1C` |
| `+0x60` | Owned `0x50`-byte helper initialized by resident `0x0019C690/0x0019C410` |
| `+0x64/+0x68` | Optional feedback-draw enable byte, initialized `1`; rotating-icon phase |

Initializer `0x0071D3E0` calls `0x0071D500` to bind the parent fighter and
initialize both chakra samples from fighter `+0x70`, and both reservation
samples from fighter `+0x7C`. It creates fill sprites from `TEX_xgauge` and
the marker from `TEX_xgauge3`. Resource/animation names and pointers are at
`D 0x00899DC0..0x00899E2B`; initializer and cleanup instructions at
`D 0x0071D280..0x0071D6BB` establish the ownership.
Gameplay meaning and mutations of fighter `+0x70/+0x7C` belong to
[Chakra and guard](../combat/chakra_and_guard.md#fighter-and-action-record-fields).

Update `0x0071E070` calls `0x0071D700`, `0x0071D880`, and `0x0071D9F0`
in order, then advances rotating-icon phase by `rate / 90`, subtracting `1`
when it exceeds `1`. The first helper refreshes the fighter, copies the prior
current sample, reads fighter `+0x70/+0x7C`, computes the total, and clips it
at `15.0`; clipping reduces only the child's displayed current sample. It
does not write fighter chakra. Positive totals select categories `1..4` at
the `5/10/15` thresholds; nonpositive total selects `0`.
The animation-rate scalar moves 10% of the distance toward category targets
`0.1,0.4,0.8,1.2,1.8`; feedback byte `+0x52` overrides the target to `3.0`.
Those five targets are live `0x00899E70..0x00899E83`, checked at
`D 0x00899E30..0x00899E43`.

The displayed reservation at `+0x30` moves upward toward requested reservation
`+0x2C` by `0.5` per child update and is clamped at that request; a decrease
is copied immediately. The fill draw at `0x0071E100` uses
`total - displayedReservation` for the first segment and the displayed
reservation for a second segment, so an unchanged gameplay total can produce
changing segment widths. Both segments use the same `15.0` denominator.
Positive displayed reservation toggles the second segment's palette every
two updates; zero clears the blink. Three threshold markers follow the
segments. The marker-cell counter wraps after 12 cells, advancing once per
child update. These are update-counted presentation values, not another
gameplay resource.

The bar's float geometry and maximum are initialized automatically when BTL
loads. Live initializer `0x008D5F40` converts the chakra rectangle's signed
width/height at `0x008C433C/3E` (`108,8`) into floats at `0x008C4348/4C`,
derives three threshold X positions, and copies the final `15.0` threshold
from `0x008C43B0` to maximum `0x008C43B8` (`D 0x008D5F00..0x008D5FAF`); these output fields are zero in
the file before initialization. The constructor interval itself is owned by
[Overlay ABI](../../runtime/overlay_abi.md#constructor-interval).

The third update helper scans active command records `4..9` of the bound
fighter's `+0xA54` action array, stride `0x54`, testing record `+0x10` and taking
the first active record's float `+0x20`. A nonnegative requirement no greater
than the child's total enables its threshold feedback. It also handles a
separate feedback condition `fighter.s16[+0x18E] == 0 &&
fighter.s16[+0x190] == 4`. Animation advancement, active flags and fades
remain in the child. The first feedback fade decreases by `0.1` per update
after the requirement ceases to hold; the third decreases by `1/30` after
the separate action-state condition ceases. The fields are action category,
action cost, major action state and action index under the existing
[Action commands](../combat/action_commands.md#working-action-arrays) contract.
This HUD consumer does not establish whether the action will execute.

Draw wrapper `0x0071EE70` calls the fill/threshold helper `0x0071E100`,
optional animated-feedback helper `0x0071E960` when child `+0x64` is nonzero,
then rotating-icon helper `0x0071EC60`, and resets all three sprites through
resident `0x001CC070`. Feedback uses the secondary render context, draws only
the animations whose active bytes are set, and restores the prior context.
The rotating-icon helper uses child `+0x68` for its angle and clears the
rotation afterward. The helper entries are at `D 0x0071E0C0..0x0071E11F`,
`D 0x0071E920..0x0071E96F` and `D 0x0071EC20..0x0071EC6F`.

## Support gauge

The per-side support-gauge wrapper first calls its native update, tests byte
`+0x0A`, and calls `TEX_xgauge` only when that byte is nonzero. The
complete-file update and draw calls are BTL `0x69380/0x69398`; live
addresses are `0x0071D240/0x0071D258`.

| Controller field | Native role |
| ---: | --- |
| `+0x00` | side index |
| `+0x04` | fighter pointer |
| `+0x0A` | visibility state |
| `+0x0B` | fill/animation state |
| `+0x0C` | normalized support fill |
| `+0x10` | prior fill |
| `+0x18` | primary support-gauge render object, also used for the icon |
| `+0x1C` | support-button glyph render object |
| `+0x20` | support-button frame render object |
| `+0x24` | icon pulse scale added to `1.0` |
| `+0x28` | icon pulse alpha |

The native update copies fighter support value `+0x74` into controller
`+0x0C`. The draw scales a 64-unit foreground by that value. Its side bases are
`120.0/392.0` with shared Y `340.0`. The red marker is fixed at half bar: the
fill begins at `20.0`, spans `64.0`, and the marker uses `52.0`.

The draw, Ghidra `FUN_0071CAB0`, places the whole support block from that one
anchor. Side 1 uses negative widths. The Y base adds the slide offset that
`0x0070FE60` returns for the side's item panel (panel `+0x44`), found through
`0x00376610(controller)` and `0x00375A60(hud, side)`. The controller is that
panel's owned `+0x1C` object, and the panel's root draw ends with this draw;
see [Battle item inventory](../projectiles_and_items/battle_item_inventory.md#na2-hud-wheel). In draw
order it commits, through `0x001CC350`:

- the bar frame's left cap, a single stretched texel column after it, and the
  X-flipped cap;
- the fill column twice, first in `0x7F7F7F`, then in fill-palette entry
  `+0x0B`, or entry `3` when `+0x0A` is `2`;
- the marker.

It then draws, with resident `0x0037BD00`, the button frame with object `+0x20`
at Y `+20`, the button glyph with object `+0x1C` at the same point, and the
icon with object `+0x18` at Y `-2`. While `+0x0B` is `1` or `2`, the icon is
drawn again at alpha `[+0x28]` and scale `1 + [+0x24]`, times `1.1` in state
`2`. The glyph is the side's binding array `0x001F3F10(side + 1)` halfword
`+0x0A`, the Linked Attack binding, resolved through BTL `0x006B4110`,
`0x006B4E60`, `0x006B4EF0`, resident `0x001CD7F0`, and BTL `0x006B4F50`. Its
alpha is `0.8` in state `0`.

The pieces are resident gp-relative rectangles in `TEX_xgauge` texel units
(X, V from the top, W, H):

| Address | Piece |
| ---: | --- |
| `0x00604D18` | Bar frame left cap `(89,108,22,20)`; the stretched column is X `111` |
| `0x00604D20` | Marker `(89,89,7,18)` |
| `0x00604D28` | Icon `(125,101,26,26)` |
| `0x00604D30` | Fill column `(4,91,0,10)` |
| `0x00604D38` | Button frame `(21,33,36,24)` |

`TEX_xgauge` in `battlegauge.ccs` is a 256-by-128 PSMT8 texture whose rows are
stored bottom-up. `0x001CC350` supports X and Y flips through sprite flags
`0x20` and `0x40`, but not rotation.

At Ghidra `0x0071CF5C..0x0071CF60`, `lui v0,0x40` followed by
`ld a0,-0x4038(v0)` reads resident `0x003FBFC8`: the load displacement is
signed, so the effective address is `0x00400000 - 0x4038`. Clean ELF bytes
there are `80 80 80 80 00 00 00 00`. The packing sequence through Ghidra
`0x0071CF9C` uses only the first three bytes as RGB `(0x80,0x80,0x80)` and
preserves the sprite's Q field; it does not copy the fourth byte to alpha.
This neutral tint preserves the marker texture's own color.

The marker calls resident rectangle helper `0x0037BC40`. Its scaled counterpart
`0x0037BD00` changes destination dimensions and centering using the supplied
scales. Both set the same source rectangle/mode, preserve RGB and alpha, and
submit through `0x001CC350`; neither supplies a different marker tint or
texture.

The fill tint is selected independently from the marker. In normal controller
state (`+0x0A == 1`), the update assigns color index `+0x0B` from the half-gauge
eligibility result and the full-gauge comparison:

| Fill condition | Index | Native RGB tint |
| --- | ---: | --- |
| Below `0.5` | `0` | `(0x1E, 0x64, 0x78)` |
| At least `0.5`, below `1.0` | `1` | `(0x7F, 0x50, 0x32)` |
| At least `1.0` | `2` | `(0x7F, 0x78, 0x32)` |

Controller state `+0x0A == 2` overrides the indexed tint with
`(0x7F, 0x00, 0x00)`. The four packed colors are at live BTL `0x00899DD0`,
Ghidra `0x00899D90`, complete-file `0x1E5ED0`:
`1E 64 78 FF 7F 50 32 FF 7F 78 32 FF 7F 00 00 FF`.
The draw loads this palette at Ghidra `0x0071CD5C..0x0071CD88`, selects by
`+0x0B` at `0x0071CE44..0x0071CE94`, and applies the state-2 override at
`0x0071CE98..0x0071CEDC` before committing the fill sprite.
Before the foreground, Ghidra `0x0071CD90..0x0071CE40` draws the full-width
inner background with RGB `(0x7F,0x7F,0x7F)`. Palette packing changes only RGB;
the sprite retains its existing alpha and Q.

The update's threshold helper is live BTL `0x0071C970`, Ghidra `0x0071C930`.
It calls resident `0x002381E0`, which returns whether fighter `+0x74` is at
least `0.5`; the update then compares controller `+0x0C` with `1.0` to choose
index `1` or `2`. The resident helper has no defined Ghidra function; its
comparison is established from the bytes at `0x002381E0..0x00238208`.

## Central battle-clock display

The central `0x44`-byte owner is the battle-clock display. Constructor
`0x0087E880` initializes through `0x0087E8B0`, obtains `battlegauge` and
`TEX_xgauge5`, samples resident clock reader `0x001EBBF0`, and creates an
owned `0x40`-byte render object with ID `0x86` plus an owned `0xF8`-byte sprite.
The sprite borrows the render object via its `+0xD0`. The complete constructor
and destructor were checked at `D 0x0087E870..0x0087EAEC`.

| Clock-owner field | Established content |
| ---: | --- |
| `+0/+8` | Units/tens digit bytes |
| `+4/+0x0C` | Per-digit display scale, initialized `0.8` |
| `+0x10/+0x14/+0x18` | Owned sprite, owned render object, borrowed texture |
| `+0x1C/+0x20/+0x24` | Current integer clock sample, previous sample, change counter |
| `+0x28/+0x2C/+0x30` | Y offset, show velocity, hide velocity |
| `+0x34/+0x38/+0x3C/+0x40` | Visibility byte, hide substate, show substate, transition selector |

Update `0x0087EB40` skips digit sampling/clock-change feedback when resident
`0x001EBBD0` reports `1` (unlimited clock). Otherwise it refreshes the
integer and decimal digits. At zero it sets both scales to `1.1`; below ten
it increases the scale by `0.015` up to `1.1`. A changed sample then overrides
both scales to `0.8`, increments the change counter and plays sound
`0x102D` through resident `0x001D8050` only for values `1..5`. It copies the
sample to previous, updates hide/show state, and finally sets sprite RGB to
`(FF,52,02)` below ten or `(FF,D2,05)` otherwise. This is a clock consumer;
timer units and production belong to
[Shared timer primitives](../../runtime/timer_primitives.md).

Draw `0x0087EDD0` returns when owner visibility `+0x34 == 1`. Unlimited
clock draws the eleventh rectangle at live `0x008D1840`; otherwise it suppresses
a leading zero while always drawing at least one digit. The ten digit records
at `0x008D17F0..0x008D183F` are eight-byte `(u,v,w,h)` rectangles, `38x62`;
the unlimited record is `78x62`. A single digit is centered at logical X `256`;
two are centered at `271` and `241`. Y is integer-converted from `offset+33`.
All draw through resident `0x0037BEC0`, then the sprite is reset with
`0x001CC070`. The digit path is at `D 0x0087EB00/0x0087ED90`, with rectangle
bytes at `D 0x008D17B0..0x008D1807`.

## Destruction and resource lifetime

Resident `FUN_001EEFD0` destroys the item manager first, then both top parents
in side order via `0x0071A870(parent,1)`, then the clock via
`0x0087EA70(clock,1)`. The root presentation forest is destroyed afterward.
The surrounding session, fighter and archive lifetime is documented in
[Battle lifecycle](battle_lifecycle.md#teardown-order).

Top destructor `0x0071A870` invokes cleanup `0x0071ABE0` and frees the parent
when its signed 16-bit delete flag is positive. Cleanup destroys and frees
children in pointer order `+0x2C,+0x28,+0x24,+0x20`, clears every pointer,
then deletes secondary and primary render objects `+0x1C,+0x18`; cleanup continues after each free
(`D 0x0071ABA0..0x0071ACC3`).

The frame child deletes both sprites through resident `0x001CBDF0`; name and
HP each delete their one sprite. Chakra deletes its three sprites, three
animation objects through `0x001B7570`, and its `+0x60` helper through
`0x00117000`, clearing the owned pointers. Borrowed parent, fighter, resource
and render-context pointers are not freed by those children. Clock cleanup
deletes its render object and sprite, clears both, and restores the shared
slide publication to `-2.0`. There is no per-meter independently scheduled
task established in these constructor and cleanup paths.

## Visibility and shared transforms

Resident hide/show requests `0x001F1820(mask)` and `0x001F1A20(mask)` select
independent owners. They also clear/set the corresponding visibility-intent
bits in the session's first byte; those intent bits are separate from a
child's completed slide/visibility state.

| Request mask bit | Selected HUD owner | Concrete request |
| ---: | --- | --- |
| `1` | Clock | `0x0087F020/0x0087F030` sets clock transition `+0x40` to `0/1` |
| `2` | Side-0 top panel | Parent `+0x48 = 0/1` |
| `4` | Side-1 top panel | Parent `+0x48 = 0/1` |
| `8` | Side-0 lower panel | Resident `0x00376230/0x00376290`, then `0x00711A30/0x00711A60` |
| `0x10` | Side-1 lower panel | Same lower-panel request path |

`-1` selects all five. `-7` is `0xFFFFFFF9`, selecting clock and both lower
panels while leaving both top-panel request bits clear. In particular, the
Ultimate-Jutsu staging hide at live `0x00769F78` does not itself hide the two
HP/name/chakra top parents. Its enclosing sequence is documented in
[Ultimate Jutsu](../characters/ultimate_jutsu.md#presentation-state-machine). Because the
top show transition clears visibility while still sliding, visibility alone
does not establish that a top panel has finished returning onscreen.

Top hide `0x0071AD80` uses substate `+0x4C`: initialize Y velocity to `-5`,
then add it to offset and reduce it by `0.7` per update. After the offset
crosses `-120`, clamp there and enter terminal substate `2`; the next call
sets visibility `+0x54 = 1` and selector `+0x48 = 3`. Top show `0x0071AE50`
initializes velocity `20`, then adds it to offset and increases it by `0.1`
with minimum `10`, clearing visibility while moving. It clamps at offset
`-2`, enters show substate `2`, and retains selector `1`; that terminal
substate keeps the offset at `-2`. Reset `0x0071ABB0` initializes offset
`-2`, selector `3`, and visibility zero. The paths are
`D 0x0071AB70..0x0071AB9F` and `D 0x0071AD40..0x0071AEEC`.

The clock has separate substates and velocities. Hide `0x0087E6C0`
subtracts velocity starting at `5`, increasing by `0.7`; after crossing
`-120` its terminal substate sets visibility and selector `3`. Show
`0x0087E790` adds velocity starting at `20`, decreasing by `0.1` with minimum
`10`; it clears visibility while moving, clamps offset at `-2`, then its
terminal substate sets selector `3`. Constructor state uses offset zero and
visibility zero. These complete paths are at
`D 0x0087E610..0x0087E833`.

Lower visibility is positional. Hide moves state byte `+0x60` from `0` or
`3` to `1`; show moves it from `1` or `2` to `3`. Update `0x00711B40` moves
Y offset `+0x44` 30% of the remaining distance toward `200` when hiding, or
zero when showing, snapping within one unit and ending at state `2` or `0`.
The lower root draw still executes: its wheel origin includes that offset,
and the support draw reads the same panel offset through `0x0070FE60`.
This differs from top and clock terminal states, which skip their draws.
The request/update instructions were checked at
`D 0x007119F0..0x00711A4F` and `D 0x00711B00..0x00711BE7`.

### Top-panel shake and attachment consumers

Request `0x0071B1B0(parent, signedByteLevel)` accepts only levels `0..4`.
It selects parent transition `2`, sample duration `1`, sample counts
`3,3,5,7,7`, and amplitudes `0.5,1,1.75,2.5,4`. A changed amplitude restarts
shake substate zero; an in-progress equal amplitude is preserved.
Update `0x0071B020` initializes offsets `(0,-2)`, chooses a starting index
through resident `0x00180210(7)`, then consumes eight `(x,y)` rows at live
`0x008C42E0..0x008C431F`. It multiplies each by amplitude, adds resting Y
`-2`, clamps parent base-X plus offset to `0..512`, and increments its
update count. At termination it restores offsets `(0,-2)` and selector `3`.
The complete request and consumer were checked at
`D 0x0071AFE0..0x0071B297`, and the eight rows at
`D 0x008C42A0..0x008C42DF`.

The only decoded direct call to this shake entry in resident executable code
and BTL is resident `0x0035BAEC`, inside cinematic hit callback
`FUN_0035B740`. It selects the opposing side's parent through
`0x001F1C40(1/2)`, and passes hit-record signed byte `+2` when it is not `-1`.
This bounds the established shake producer; indirect calls are not excluded.

Fresh anchor getter `0x0071AD50` computes parent base plus offsets directly.
The root-owned status glyph's anchor update at live `0x006B8EE0` gets the
side's top parent through resident `0x001F1C40`, calls that getter, adds its
own signed-halfword offset, and stores destination X/Y. Thus top slide/shake
also moves this root-owned attachment even though it is not one of the top
parent's four children. This getter is distinct from `0x0071AD10`, which
returns HP-fill geometry. Their bodies and the glyph call were checked at
`D 0x0071ACD0..0x0071AD33` and `D 0x006B8EA0..0x006B8F0B`.

Top update publishes its Y offset to resident `0x00604D08` (`gp-0x5CE8`)
after the child/transition calls. Since session service walks side 0 then 1,
side 1 is the last top writer in that pass. Clock cleanup resets it to `-2`.
This is a shared presentation publication, not a replacement for per-parent
offset storage; additional consumers are not exhaustively assigned here.

### Direct visibility request coverage

Byte searches for encoded `jal` operands across the resident executable and
BTL, followed by instruction inspection at every executable match, found:

| Request | Resident call sites | Live BTL call sites | Mask |
| --- | --- | --- | --- |
| Hide | `0x00242BD8`, `0x00245994` | `0x0076CCBC`, `0x0077A948`, `0x00793770` | `-1` at every listed site |
| Hide | — | `0x00769F78` | `-7` |
| Show | `0x00244098`, `0x00246D3C` | `0x0076A63C`, `0x0077B530`, `0x00793894` | `-1` at every listed site |

The functions surrounding the last two BTL hide/show pairs have their own
state gates; their class names and complete presentation semantics are not
established by a HUD request. Their preserved Ghidra addresses are the
listed live addresses minus `0x40`. Mirrored ELF program-memory matches are
the same physical resident instructions, not additional callers. This is a
bounded direct-call census, not an exhaustive indirect-call claim.

## Remaining ordinary presentation forest

Session `+0x30` owns the separate root forest for combo digits, command
prompts, selectable command strips, status glyphs, projected player markers,
numeric popups/history, shared icon resources and success/failure notices.
Its eight root fields, paired arrays, phase gate, construction and deletion
are recorded in
[Battle lifecycle's root component forest](battle_lifecycle.md#root-component-forest).
Those root children are not owned by either top panel or the item manager.
The session reaches this root only after lower panels, both top panels and
clock, under mask `0x200`. Child active/fade gates remain separate from the
root gate.

None of the root element constructors installs a vtable, so RTTI supplies no
original class names. Their resource bindings and callbacks establish the
following functional roles. All BTL addresses in this table are live;
the last row uses resident functions.

| Root field | Established presentation role | Side/resource binding | First callback | Second callback |
| ---: | --- | ---: | ---: | ---: |
| `+0x00` | Combo-number display: `TEX_xcombo` digits and `ANM_xcombo_ht` animation | `0x006B6AE0` | `0x006B6D10` | `0x006B7100` |
| `+0x04` | Button/command prompts using `TEX_xcommand` and `TEX_xcommand02` | `0x006B5020` | `0x006B53F0` | `0x006B56E0` |
| `+0x08` | Selectable command strip: `TEX_j_waku` frame, command glyphs, and `TEX_xosubotan` button texture | `0x006B7650` | `0x006B7840` | `0x006B79B0` |
| `+0x14` | Shared icon/menu render bundle: `TEX_xicon_b`, `TEX_xicon`, `TEX_xmenu`, and `ANM_xicon02` | `0x006B83A0` | `0x006B8570` | `0x006B8620` |
| `+0x10` | Per-side gameplay-node icon display with 26 owned glyph slots | `0x006B9A50` | `0x006B9CC0` | `0x006BA120` |
| `+0x18` | Per-side numeric popup/history display, using `TEX_xcombo` digits | `0x006BB2B0` | `0x006BB3A0` | `0x006BB590` |
| `+0x0C` | Per-side markers positioned from the fighter's projected world position | `0x006BA3A0` | `0x006BA3D0` | `0x006BA870` |
| `+0x1C` | Success/failure notice using `TEX_xsuccess` and `TEX_xfails` | `FUN_001F8F00` | `FUN_001F91A0` | `FUN_001F9320` |

These are descriptions of observed consumers, not recovered class names.
For example, live `0x006B7100` divides the combo value at object `+0x0C`
into decimal digits and submits its digit texture and hit animation. The
command-strip draw at live `0x006B79B0` reads at most five sequence bytes
through `+0x2F8`, stops at sentinel `0x1E`, and sends them to the command
glyph renderer. The separate root `+0x04` prompt has the placement and
activation interfaces described below; exact gameplay subtype names are
not established.

The icon parent allocates 26 `0x38`-byte children. Its first callback calls
live `0x006B9D30`, which obtains the side's fighter and checks IDs
`0..0x89` through resident `FUN_00306420`; that predicate searches the
fighter's gameplay-node list. Present IDs not already displayed are assigned
to glyph slots, with IDs `0x79/0x7A` excluded by this consumer. The second
callback traverses those glyph children in reverse order and reaches the
shared icon-rendering path. Node identity and gameplay effects belong to
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#per-fighter-storage).
This presentation enumeration does not establish another gameplay update.

The marker's first callback copies the fighter's `+0x30` position and projects
it through resident `FUN_00376930`. Its second uses icon descriptor groups
`117..119` and `120..122`, with screen-edge clamps, and borrows textures
from root `+0x14`. The numeric-history parent maintains a linked popup list
and a saturated aggregate/peak pair; its second callback submits the active
entries. The triggering gameplay meanings of these displays are not
established.

The full shared-icon binding (live `0x006B83A0..0x006B856C`, file
`0x44A0..0x466C`) stores five sprite-wrapper pointers at `+0x00..+0x10`, an
animation at `+0x18`, and two render layers at `+0x14/+0x1C`. The icon
parent's side binding and enumeration are at live `0x006B9A50..0x006B9BF4`
and `0x006B9D30..0x006BA11C`.

### Combo digit presentation

Each side's combo digit object is a `0x44`-byte element of root `+0x00`.
[Combo accounting](../combat/combo_accounting.md#separate-presentation-count) owns its
count increment (`0x006B6C30`) and running-count reset (`0x006B6BF0`), which
write running word `+0x08`, latched word `+0x0C`, active byte `+0x01` and
shake countdown `+0x20`.

The side lookup at live `0x006B3FB0` (`D 0x006B3F70..0x006B3FBB`) resolves
session global
`0x00607604`, read session `+0x30`, then return root `+0x00` array plus
`side*0x44`, or zero when the session/root is absent. This is the combo
manager's `+0x04` binding.

Initialization at `D 0x006B69D0..0x006B6A17` zeros both count words, side/resource fields, active/fade
flags and shake/appearance values. Resource binding `D 0x006B6AA0` / live
`0x006B6AE0` calls that initializer, stores the side at `+0x04`, and binds
digit sprite `+0x38` plus animation `+0x40`.

Update `D 0x006B6CD0` / live `0x006B6D10` returns while byte `+0x00` is
nonzero or active byte `+0x01` is zero (`D 0x006B6CF8..0x006B6D27`).

| Presentation field | Eligible update operation |
| --- | --- |
| `+0x10` | Increment until `30`; only later calls subtract from opacity `+0x14`. |
| `+0x14` | Subtract float `0.05`; clear active byte when result is nonpositive. |
| `+0x24/+0x28/+0x2C` | Appearance overlay: add `0.1` to overlay opacity until `>=0.4`, then clear overlay flag; add `0.15` to extra scale while the flag was active on entry. |
| `+0x3C/+0x40` | Advance the associated animation. Its flag clears only when animation reports completion and main opacity is nonpositive. |
| `+0x20/+0x18/+0x1C` | Ten-call shake countdown after a count publication; while positive, decrement and obtain two signed offsets using resident random helper with magnitude `min(running_count*0.65,7)`. When nonpositive on entry, zero both offsets. |

These are update-call counts and float constants, not durations in seconds.
The fade does not inspect the combo manager's current count or its 90-unit
timer. It starts on each qualifying display increment and can run while the
live combo is still retained. Once the active byte is zero, the update skips
its animation work as well.

Draw `D 0x006B70C0` / live `0x006B7100` requires active byte `+0x01` and
uses latched word `+0x0C`, not running word `+0x08`. It selects one of five
12-byte color/scale rows through live bases `0x008BFED8/0x008BFEDC/0x008BFEE0`
(`D 0x008BFE98/0x008BFE9C/0x008BFEA0`). The loop begins at index `1`,
advances while `index < 5` and that row's threshold is `<=count`, and then
reads the selected row's color/scale. It never selects index `0`. Bytes
`D 0x008BFE98..0x008BFEDF` establish:

| Latched count | Selected row | Color word | Float digit scale |
| --- | ---: | --- | ---: |
| `<5` | `1` | `0xFF00A0A0` | `1.0` |
| `5..9` | `2` | `0xFF00A0A0` | `1.0` |
| `10..19` | `3` | `0xFF0060A0` | `1.1` |
| `20..29` | `4` | `0xFF0040A0` | `1.2` |
| `>=30` | `5` | `0xFF0000A0` | `1.3` |

The words describe numeric packed color data without assigning an unverified
color-channel convention. The digit renderer, entry `D 0x006B6F00` / live
`0x006B6F40`, extracts decimal digits, uses `32x40` atlas cells, and submits
digits with spacing `24*scale`. The clamped publication supplies at most three digits.

The draw's base position is `x=96` for side other than `1`, or `x=386` for
side `1`, and `y=140`, plus shake offsets. It first submits the main digits
with main opacity, optionally submits the appearance overlay with its
extra scale, then submits the hit animation while `+0x3C` remains set.
Resetting only running word `+0x08` does not erase the already latched result.

### Prompt placement and activation interfaces


The two `0x580`-byte root `+0x04` objects have side halfword `+0x28`,
active byte `+0x20`, placement selector byte `+0x10`, label selector
`+0x2F`, and command bytes beginning at `+0x30`. Their draw callback live
`0x006B56E0` distinguishes these numeric placement modes:

| Selector | Established placement |
| ---: | --- |
| `0` | Stored side coordinates `(100, 160)` or `(412, 160)` |
| `1` | Fighter `+0x30` position plus the height returned by resident `FUN_002163A0`, projected through `FUN_003537C0`; screen Y is reduced by `70`, and X is clamped to `70..442` |
| `2` | Stored coordinates `(256, 260)` for either side |
| `3` | Stored coordinates `(100, 260)` or `(412, 260)` chosen using the fighters' relative X ordering; draw scale is forced to `0.6` in the ordinary presentation path |

Live `0x006B5EC0` stores the selector and side coordinates from table
live `0x0088F780`, using `8` bytes per selector and `4` per side. Mode
`3` selects the placement side from the two fighters' X values; modes
`0/2` use the object's side. The table's
zero coordinates for mode `1` are superseded by the draw-time projection.
These numeric modes establish placement, not original names or the full set
of gameplay callers.

Live `0x006B5D10` activates the prompt only when resident
`FUN_001F6DB0(manager)` succeeds or the supplied force byte is nonzero.
It writes duration halfword `+0x2A`, active byte `+0x20 = 1`, alpha
`+0x14 = 1.0`, ordinary-path byte `+0x57C = 1`, the placement, and
force byte `+1`. The other activation helper, live `0x006B5DC0`, uses
the manager gate for activation; a positive ramp argument separately sets
`+0x57C = 0`, fraction `+0x574 = 0`, denominator `+0x578`, and
counter `+0x57A = 0`. That ramp-field write and final placement call
remain outside the manager-gated block, so the helper's invocation alone
does not prove that the prompt became active.

The first callback advances this ramp once per eligible invocation and
switches to the ordinary path when counter reaches denominator. During
the ramp, the second callback submits two copies displaced horizontally
by `±70 * (1 - fraction)`, each with alpha `alpha * fraction * 0.5`.
In the ordinary path, a positive duration decrements; zero duration reduces
alpha by `0.15` per eligible invocation until active byte `+0x20` clears.
Negative duration does not decrement there. Explicit hide helper live
`0x006B5E80` zeroes duration and can clear active state immediately,
depending on its argument and `+0x57C`. Byte `+0 == 1` or inactive
`+0x20` suppresses both callbacks; an unforced prompt also remains subject
to their manager/fighter gates. These are invocation-counted controls,
not measured durations or evidence that every selector/caller combination
is reachable. The root's original non-polymorphic class names and full
label/glyph-to-gameplay identity remain unresolved.

Player-marker rectangles and conditional labels belong to
[Battle UI selectors and prompts](../../localization/ui/battle/selectors_and_prompts.md#player-markers).
Item/status label composition belongs to
[Battle item/status presentation](../../localization/ui/battle/item_status.md).
Gameplay-list identity remains in
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#per-fighter-storage).
These links retain their texture/layout and gameplay ownership rather than
turning HUD display values into additional gameplay state.

The resident service finishes with `FUN_001DE1C0` after HUD/root work; its
direct call is at `0x001F0A68`. Therefore this HUD samples the fighter state
available before that service's final overlap-query publication. This ordering
does not establish a universal elapsed time or same-update contact result;
fighter processing and collision ownership remain in the gameplay documents.

## Confidence and remaining limits

**Observations, high confidence:** The constructor fields, owned-pointer
cleanup, direct callback order, scalar reads/stores, atlas bounds, selector
branches and physical request instructions are established from instruction
bytes. Neighboring documents supply the linked wheel, support-resource, and
root-allocation contracts.

**Inferences:** Names such as top panel, frame/discs, clock owner and feedback
describe their observed consumers and textures; they are not recovered class
names. Display rates/counts describe eligible native callback invocations.
They are not conversions to wall-clock seconds.

**Unresolved:** No depicted symbol is assigned to every
character-keyed decorative cell, the generic chakra helper vectors' original
type, or every indirect producer of scalar/enable fields. The document establishes
the ordinary graph and reviewed branches, without claiming all cut-in or
special-scene HUD variants share that graph.
