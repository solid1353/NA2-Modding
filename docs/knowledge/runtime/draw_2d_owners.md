# Full-screen and bounded 2D draw ownership

This document owns caller-level classification of retail NA2 (`SLPS-25837`)
2D geometry. Resident addresses below refer to `SLPS_258.37`; see
[address conventions](../game/files/file_identities.md#address-conventions).
Overlay evidence names both the preserved Ghidra address and live address
because BTL/ETC imports omit the `0x40`-byte header.

## Research coverage

- **Assigned scope:** Classify in-scope retail 2D draw callers/resources by owning screen/object, purpose, coordinate space, bounds/clip state, transforms and layout ownership.
- **Exploration depth:** Static inspection covers the rectangle-slot producer/consumer, both immediate rectangle helpers and their direct-call cohorts in resident/BTL/ETC code, atlas helpers and sprite transforms, selected front-end/Practice/HUD consumers, font quad emission, and render-list scissor installation. Raw bytes were inspected where function boundaries truncate callers.
- **Confirmed coverage:** Full-frame colored covers, full-frame textured presentation, oversized vertical masks, bounded atlas/line/highlight/text geometry, and authored CCS scene geometry are distinct owners. Logical coordinates, local transforms and selected-list clipping are established below.
- **Unresolved or untested:** Some BTL menu-family identities and animation-derived rectangle dimensions remain unresolved. The inventory does not cover every indirect sprite/font/CCS caller, every fade-slot producer, or every authored animation frame. Visible artwork bounds within the splash textures are not established.
- **Deliberate exclusions and overlap:** Shared transform formulas belong to [Renderer and coordinate systems](renderer_coordinates.md), packet lifetime to [Render submission](render_submission.md), HUD bindings to [Battle HUD](../gameplay/battle_hud.md), and font metrics to [Font renderer metrics](../localization/font/renderer_metrics.md). This document classifies their geometry callers. Master Mode and Shop are excluded.
- **Evidence limitations:** These are static retail observations. Preserved boundaries, decompiler arguments and xrefs are incomplete; missing direct references do not prove whole-program absence. No rendered output has been observed.

## Colored-rectangle slots

**Observation, high confidence.** Resident `FUN_001834B0` initializes a
`0x98`-byte owner: disabled word `+0`, four `0x24`-byte slots beginning at
`+4`, and optional render-list pointer `+0x94`. On the first initialization it
allocates a shared `0x40`-byte render-list object and configures its renderer
through `FUN_0010E460` with `(0,0,512,384)`, center `(256,192)` and unit
projection scales. This default list is separate from each caller's slot owner.

Each `0x24`-byte slot carries a float logical origin and a float logical
width/height, not endpoint coordinates. The producers `FUN_00183DF0`,
`FUN_00183E80` and `FUN_00183F10` retain caller-supplied geometry.
[UI animation and easing](ui_animation.md#four-slot-rgba-transition-pool)
owns the slot layout, allocation, RGBA interpolation, durations, completion
and reuse.

The consumer `FUN_00183650` (`0x00183650..0x00183DE8`) skips the
owner when `+0 != 0`. It selects `+0x94` or the shared list, processes slots
in index order, transforms the origin through `FUN_0010EFA0`, and computes extents from width/height
times the renderer's 2D matrix diagonals at `+0x1C0/+0x1D4`. It emits four
corners. Extents do not pass through
the full rotation matrix here; this path is an axis-aligned rectangle path.

Resident `FUN_00186000` sets the first global pool's `+0x94` to its caller's
list and the second pool's `+0x94` to `uGpffffca84`, then draws the two pools
in that order. Therefore the constructor's default viewport is not proof of
the final list used by every global fade. Locally owned pools can likewise
select their own list.

## Immediate rectangles and bounded sprites

**Observation, high confidence.** `FUN_00353850` receives floating logical
`(x,y,width,height)` and packed RGBA; it computes four corners, starts primitive
mode `5` through `FUN_001830A0`, submits each corner with
`FUN_001822B0(0)`, then ends through `FUN_00182F50`. `FUN_00353F40` is the
integer counterpart, with signed-halfword width/height and endpoint sums.
Neither helper chooses full-screen dimensions. Both reset the shared local
transform with `FUN_0010D6A0`; the integer helper additionally calls
`FUN_0010CA10` before submission.

`FUN_001822B0(0)` composes the current local transform with the selected
list's logical 2D matrix at renderer `+0x1C0`. In contrast to the slot
consumer, every supplied corner goes through the transform. The alternate
argument-bit-1 path uses the 3D projection at `+0x40`; these immediate helpers
choose the 2D branch. Shared matrix formulas belong to
[Renderer and coordinate systems](renderer_coordinates.md).

The centered atlas helper `FUN_0037BC40` takes four signed halfwords
`(sourceX,sourceY,width,height)`. It retains source size at sprite `+0x60/+0x64`,
sets UV origin times 16 at `+0x68/+0x6C`, writes mode `1` at `+0x70`,
destination size at `+0x58/+0x5C`, caller position at `+0x50/+0x54`, and
local origin `(-width/2,-height/2)` at `+0x44/+0x48`. The scaled helper
`FUN_0037BD00` preserves source size but multiplies destination size and
centering by supplied X/Y scales. Both submit through `FUN_001CC350`;
neither replaces the sprite's texture, RGB or opacity. `FUN_001CC070`
later attaches accumulated sprite packets to the selected list and resets
the per-batch count and packet pointer.

The generic sprite consumer `FUN_001CC3A0` has distinct geometry branches:

| State | Transform and bounds contract |
| --- | --- |
| `object+4 & 2 == 0` | Transform origin plus local offset through `FUN_0010EFA0`; derive axis-aligned size from 2D diagonal coefficients. Reject outside device-coordinate rectangle X `0x7000..0x9000`, Y `0x7200..0x8E00` using extent overlap. |
| `object+4 & 2 != 0` | Load angle `+0x4C`, negate it and build a rotation through `FUN_001523B8` at `0x001CC5F0..0x001CC600`; rotate local offset and two extent vectors, add caller position, then transform all four corners through `FUN_0010EFA0` at `0x001CCE18`, `0x001CCEC0`, `0x001CCF68`, `0x001CD020`. Reject when all four corners fail the same device bounds. |
| Textured mode `object+4 & 1` | Source UV construction uses the atlas size and origin; bits `0x20/0x40` exchange X/Y UV corners. These are flips, separate from the geometry rotation bit. |

The bounds correspond to a 512 by 448 device region at 16 units per pixel,
centered on `0x8000`; they are broader vertically than the logical 384-line
viewport. They are coarse rejection bounds, not an object-specific scissor
or proof that pixels outside the logical viewport appear. Generic rotation
capability does not establish that an individual HUD caller enables it.

## Practice geometry cohort

**Observation, high confidence.** BTL preserved `0x00882210..0x008825E8`
(live `0x00882250..0x00882628`, file `0x1CE350..0x1CE728`) is the Practice
Settings draw body. The decompiler stops at its first font call; raw bytes
expose the continuation. At preserved `0x008822A8`, byte `child+0x48`
gates the immediate rectangle call at preserved `0x008822E0`, live
`0x00882320`. Its arguments are `(0,0,512,384)` and
`(s16(child+0x54)<<24)|0x86A8BE`. The owner selects child `+8` as its list
before this call. This is a full-frame colored backdrop, independently gated
from the later rows, authored backing and prompts.

At preserved `0x008824D8..0x008824F0`, child `+0x18` and live table
`0x008D1908` supply the separate scaled atlas-panel helper
`FUN_0037E950`. Bytes at preserved `0x008D18C8` decode its first
rectangle as `(1,1,126,30)`. This bounded resource does not become
full-screen because another child draws a backdrop. Later submission calls
for child `+0x18/+0x1C/+0x20/+0x24` are at preserved
`0x00882588..0x008825AC`.

The backing and title use authored CCS animation/model geometry, not these
rectangle slots. Their named resources, row window geometry and lifetime are
owned by [Practice Mode](../gameplay/practice_mode.md#native-practice-settings-presentation-geometry).

## Confirmed screen-sized callers

These calls specify origin `(0,0)` and extent `(512,384)` explicitly. Their
screen-sized classification follows retail geometry and fade state, not a
literal width match alone. The pool's selected list supplies clipping;
global pool list overrides are described above.

| Owner/path | Resident evidence | Geometry and state ownership |
| --- | --- | --- |
| Global fade wrapper | `FUN_00105600`, call `0x00105638` | Forwards duration and colors to the shared owner `gp-0x358C`; fixed full-frame rectangle. |
| Table-selected fill/fade wrappers | `FUN_001EB600`, `FUN_001EB670`, `FUN_001EB700` | Clear shared slots first. Read 8-byte color pairs at `0x005C0950`; use same/same, second/first, or first/second endpoint order. |
| Playback/transition controller | `FUN_001DBD60`, calls `0x001DBDE0`, `0x001DBF68`, `0x001DBFE8`, `0x001DC060` | Initial cover and later timed/skip transitions use white opaque/transparent endpoints. Owner waits on `FUN_00183FD0` and yields through `FUN_001D0340`. Exact presentation identity is not established. |
| Title transition | `FUN_001DF690`, state `2`, and states `4/6` | State `2` creates a 14-step white cover through `FUN_00183DF0`; the later states call black table fade `FUN_001EB700(0,20)`. The separate title scene draw is `FUN_001DFAB0`. |
| Mode Select entry and return | `FUN_00383DB0`; `FUN_003854F0` | Entry uses opaque-to-transparent white over 16 steps. Confirmed return-to-title uses transparent-to-opaque saved clear color over 30 steps; a resumed dialog uses `0x50000000` to transparent over four steps. The controller owns transition state, separately from its CCS background. |
| Character Select confirmation | `FUN_003BBBB0`, call `0x003BC2EC` | Accepted selection creates a transparent-to-opaque white 16-step cover. This rectangle is separate from portrait and prompt batches. |

The three directly decoded color pairs at `0x005C0950..0x005C0967` are
`(0x00000000,0xFF000000)`, `(0x00FFFFFF,0xFFFFFFFF)` and
`(0x00FFFFFF,0xFFFFFFFF)`. They describe black and white opacity transitions;
the calling wrapper chooses direction. Table index bounds are not proven.

Title and Mode Select identities, transitions and object fields are owned by
[Front-end mode flow](../game/mode_flow.md#mode-select-controller).
Character Select state and final handoff are owned by
[Character Select](../game/character_select.md#appearance-fixed-choices-and-final-handoff).

## Direct immediate-rectangle caller inventory

**Observation, high confidence for arguments; limited screen naming.** Raw
JAL-pattern searches and caller-byte inspection establish the following
bounded cohort. `FUN_00353850` has nine physical BTL call sites and no direct
sites in the resident or ETC images. `FUN_00353F40` has fourteen BTL sites,
three physical resident sites and no ETC sites. Resident mirror mappings
repeat the same three instructions and are counted once. This accounts for
direct calls to these two helpers in the inspected images, not inline quads,
function-pointer calls, or the rectangle-slot producers.

Overlay call addresses in this table are **preserved / live**. The logical
rectangle is `(x,y,width,height)`; dimensions alone do not identify the screen.

| Helper and owner | Call evidence | Logical geometry and draw state |
| --- | --- | --- |
| Float; BTL menu background cohort | `0x006DE7F4 / 0x006DE834`, `0x006DE918 / 0x006DE958`, `0x006DEA28 / 0x006DEA68`, `0x006DEB54 / 0x006DEB94`, `0x006EBB1C / 0x006EBB5C`, `0x006EDBAC / 0x006EDBEC` | `(0,0,512,384)`, RGBA `0x18000000`, before later menu scene geometry. Repeated coverage is established; exact identity of each menu state is unresolved. |
| Float; Start Menu row highlight | `0x0087D278 / 0x0087D2B8` | `(windowX+1,parent+0x84-22,windowWidth-2,44)`, RGBA `0x5FD45050`. Selects the child window's list through `FUN_00380A30`; window getters `FUN_00382060/003820C0` supply origin/extent. This is a bounded highlight, not a dimmer. |
| Float; Practice backing child | `0x00880830 / 0x00880870` | `(0,0,512,384)`, RGBA `(s16(child+0x54)<<24)\|0x86A8BE`; separately owned from the Settings draw body. |
| Float; Practice Settings | `0x008822E0 / 0x00882320` | Full-frame backdrop and byte `+0x48` gate detailed above. |
| Integer; BTL window dimmers | `0x006E31FC / 0x006E323C`, `0x006E5260 / 0x006E52A0`, `0x006E722C / 0x006E726C` | `(0,0,512,448)`, black with computed opacity. The first two inspected owners multiply their modal opacity by the parent opacity and `255*0.5`. These masks request 448 logical lines; they do not establish a 448-line viewport. |
| Integer; two repeated bounded boxes | `0x006E4E98 / 0x006E4ED8`, `0x006E4F18 / 0x006E4F58` in `FUN_006E4D40` | For `i=0,1`, outer `(110,16+36*i,123,25)` in gray `0x808080`; inner `(112,18+36*i,121,23)` in `0xF0F0F0`. Parent `+0x58` controls opacity. The same owner separately draws one of the 512-by-448 dimmers. |
| Integer; BTL modal cover cohort | `0x006EBCB8 / 0x006EBCF8`, `0x006ED08C / 0x006ED0CC`, `0x006ED2EC / 0x006ED32C`, `0x006EDD3C / 0x006EDD7C`, `0x006EDE00 / 0x006EDE40` | `(0,0,512,384)`, RGBA `0x88000000`, before later modal/menu children. Exact labels are unresolved. |
| Integer; Stage Select selected-stage fallback | `0x00715394 / 0x007153D4` in `FUN_007151D0`; caller `0x00715D70 / 0x00715DB0` | `(20,340,200,40)`, RGBA `0x7F000000`, in the branch where selected stage does not match the 24-row preview table. The matched branch instead emits a bounded atlas cell through `FUN_0037BD00`. |
| Integer; animation-derived BTL rectangle | `0x00876BBC / 0x00876BFC` | Four float fields supplied by the caller become signed-halfword geometry; RGBA is separately supplied. The examined body selects parent-window list `+0x74`. Full-frame coverage and exact screen identity are not established. |
| Integer; three BTL menu rules | `0x00877344 / 0x00877384` | Copies three 20-byte records from live `0x008BD850` (preserved `0x008BD810`): RGBA `0xFF404040` and rectangles `(200,14,1,296)`, `(284,14,1,296)`, `(8,42,348,2)`. These are bounded vertical/horizontal rules. |
| Integer; Start Menu host cover | `0x0087D4C8 / 0x0087D508` | Live constant record `0x008BD9F0` (preserved `0x008BD9B0`) supplies RGBA `0x88000000`, `(0,0,512,384)`. Host `+0x3C` selects the list before child dispatch. |
| Integer; resident running-help backing | `0x0037FA60` in `FUN_0037F900` | Uses object width/height at `+0/+4`, origin `(0,0)`, color `+0x20`, list `+0x0C`; the alternative uses its textured backing sprite. Size belongs to the help object. |
| Integer; resident Character Select modal covers | `0x003BC7D0` in `FUN_003BC780`; `0x003BC988` in `FUN_003BC950` | `(0,0,512,384)`, RGBA `0x88000000`, followed by window and bounded text/prompt children. Specific modal labels are unresolved. |

The Start Menu parent and its child/result boundaries are owned by
[Pause and replay](../gameplay/pause_and_replay.md#btl-start-menu-construction-and-ui-states).
Stage records and preview construction are owned by
[Stage Select UI](../localization/ui/stage_select.md#stage-records-and-preview-construction).

## Screen and resource ownership

The following consumers distinguish the frame they cover from the bounded
artwork, text or authored scene layered with it. **Observation, high
confidence for the inspected consumers.**

| Screen/object | Evidence and resource | Geometry/layout owner |
| --- | --- | --- |
| Startup splashes | `FUN_001E0390` constructs `TEX_logo_notice_pss`, `TEX_logo_bn_pss`, `TEX_logo_b_pss`, `TEX_logo_adx_pss`; strings at `0x00400DB0..0x00400DF0`. `FUN_001E00E0` draws texture `object+0x1C`. | Explicit type-5 textured quad `(0,0)..(512,384)`, reversed V coordinates, object opacity `+0x18`, suppressed in state `7`. This proves full-frame texture presentation, not the opaque/visible bounds of a logo inside the texture. |
| Title scene | `FUN_001DFAB0`, CCS animation `+0x1C` and item animations `+0x2C/+0x30` | Authored animation/model geometry; camera/list selected through `FUN_0010E220`. Draw phases gate scene and items. The separate transition rectangle above owns the cover. |
| Mode Select scene and footer | `FUN_00385C00`, background animation `+0x78`, further animations `+0x7C/+0x80`; lists `+0x68/+0x6C`, prompt batches `+0x70/+0x74` | Main scene uses authored CCS geometry. Footer uses bounded atlas helpers and separately owned windows/running help. Selecting a full-frame list does not turn each footer sprite into a full-frame object. |
| Character Select support carousel | `FUN_003B84D0`; `FUN_0037D470` selects an 8-byte atlas rectangle from resident `0x005D4B70`; sprite batch `parent+0xA8` | Iterates thirteen columns `-6..6`, centered at caller-derived X and Y `61`, through `FUN_0037BC40`. Decoded leading portrait cells are `38x46`; unavailable/selected overlays at `0x00604830/0x00604838` are also `38x46`. Selector motion changes the centers, independently of the screen cover. |
| Battle top panels | BTL HP draw preserved `0x0071C0A0`, live `0x0071C0E0`; parent/child batches documented by the HUD owner | Current/trailing HP derive bounded widths from the source rectangle and sampled ratios. Mirrored parent position/scale controls side placement. These are atlas bars, frames, names and icons, not screen-cover rectangles. |
| Running help | `FUN_0037F900` | Backing uses owner extent; linked text entries draw within the help object's list. The generic solid-backing branch is counted above. Width is a local layout input, independent of glyph dimensions. |
| Font glyphs | `FUN_00187CC0` | Emits individual type-5 textured quads through `FUN_001822B0(0)`. Normal geometry uses descriptor width for both destination axes, with right endpoint minus one; output height remains a source V extent. Orientation changes corners/UVs. Text placement belongs to the font context and caller. |

Resource loading and splash lifecycle are in
[Startup](../game/startup.md#splash-controller). Portrait identity and selector
motion are in [Character Select](../game/character_select.md#support-cursor-and-carousel).
HUD anchors, child resources, gauge proportions and central clock are in
[Battle HUD](../gameplay/battle_hud.md#top-panel-construction). Help queue
extent and visibility are in
[Running help](../localization/ui/running_help.md#how-the-extent-affects-visibility).
The glyph descriptor contract is in
[Font renderer metrics](../localization/font/renderer_metrics.md#glyph-geometry).

### Playback bars and captions

`FUN_001DC1A0` selects resident list `0x00607474`, resets local state through
`FUN_0010D6A0`, and emits two opaque black type-5 quads. These are separate
top/bottom bars, not a full-frame rectangle. Both use X endpoints from
`0x006075A0` and `0x00602CB8`. The inspected resident data at
`0x00602CB8..0x00602CC7` sets right X `512`, bottom Y `384`, upper-bar end
Y `20` and lower-bar start Y `314`. Left X is a mutable global whose producer
is not established. Every vertex uses `FUN_001822B0(0)`.
The same consumer separately emits centered caption text at X `256`, with
Y `338` or `328` depending on a newline search, and caption opacity from its
controller. Bar geometry and caption geometry therefore have different
owners even though they share the presentation list.

### Framebuffer-effect local 2D object

The retail call at `0x001A18EC` has bytes `C4 2E 04 0C`, targeting
`FUN_0010BB10`. The surrounding construction branch selects CCS type
`0x1D00`, allocates `0x48` bytes, writes descriptor `0x005D9EC0`, and
initializes the embedded object at `+8`. Type naming belongs to
[CCS object types](../game/files/ccs_object_types.md): `ccStreamFBSBlurParam`.
This initializer stores local pivot `(256,192)`, equal caller-supplied X/Y
scales, angle, color and material state. Its consumer `FUN_0010A520` derives
corners from the selected renderer's viewport width/height and composes local
scale/rotation/translation with that renderer's 2D matrix. This establishes
a framebuffer-effect coverage owner; it does not establish a common size
contract for atlas portraits, glyphs, or HUD bars.

## Clipping and coordinate ownership

**Observation, high confidence.** The viewport updater `FUN_0010E460`
([renderer coordinates](renderer_coordinates.md#logical-viewport-and-2d-device-coordinates))
packs the inclusive scissor endpoints at renderer `+0x260` as
`Xmin | Xmax<<16 | Ymin<<32 | Ymax<<48`.

Render-list finalization `FUN_00109D50` first resolves ordered work, then,
when list byte `+6 == 0`, allocates/prepends a `0x30`-byte state packet.
Instructions `0x00109DE8..0x00109E04` store GS register `0x40` with the
value read through list `+0x3C` to renderer `+0x260`. List byte `+6 != 0`
instead calls the inspected empty `FUN_00109D00`; this branch does not emit
the same scissor packet. Packet ordering/lifetime belongs to
[Render submission](render_submission.md#frame-chain-and-vif1-submission).

Consequently, caller geometry and local transformation are bounded by the
**selected list's** scissor on the normal list path. The shared default
512-by-384 rectangle list is one such owner; callers that replace the pool
list or select a window list inherit that renderer's viewport. A 512-by-448
mask or a glyph partly beyond its window does not prove visible coverage
outside that viewport.

`FUN_001830A0` also copies renderer clip vectors `+0x200/+0x210` and
`+0x220/+0x230` into the current primitive; `FUN_001822B0` uses them when
selecting vertex emission. The examined rectangle-slot packet setup
`FUN_00184020`, immediate primitive setup and generic sprite packet setup
`FUN_001CD5E0` do not install their own register-`0x40` scissor. The generic
sprite's coarse 512-by-448 rejection region described above is a separate
CPU-side decision. Neither mechanism replaces the list's clipping ownership.

The examined `FUN_00109A10(list,color)` constructs a viewport-sized fill
packet using `FUN_0010EFE0` endpoints; it does not install register `0x40`.
Calling it with zero in a screen draw body is not evidence of a new clipping
rectangle. Matrix construction, logical pivots and output-coordinate
conversion remain owned by
[Renderer and coordinate systems](renderer_coordinates.md).
