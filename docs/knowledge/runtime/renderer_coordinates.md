# Renderer and coordinate systems

This document owns the transform state and coordinate conversions of the
retail NA2 (`SLPS-25837`) renderer. Unless stated otherwise, addresses below are
resident `SLPS_258.37` EE addresses; see
[address conventions](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Retail renderer construction, refresh, matrices, viewport and world/view/projection/screen/2D coordinate transforms.
- **Exploration depth:** The shared constructor and its three direct resident callers, complete camera/projection refresh, viewport updater, scale setter, renderer list, copy routine, coordinate utilities, both local 2D composition branches, three camera builders and ordinary model composition were traced through decompilation and relevant instructions. Primary/display environment creation, scoped scene copies and shadow projection inputs were traced at their shared transform boundaries. All six direct calls to the draw-environment selector, the streamed scene's environment-selection helper family, all three BTL direct callers of lazy camera publication and both shared particle-manager draw loops were inspected. Literal `+0xC0` candidates and base/battle generator environment binding were followed through bounded aliases; other inline global stores remain unclassified.
- **Confirmed coverage:** Column-vector composition, distinct configured-width and fixed-512 projection paths, viewport conversion from logical 512 by 384 units, device-center bias, reverse depth mapping, independent 2D transforms, persistent renderer lifetime and draw scratch lifetime are established below. Direct draw-environment selection, streamed group selection/restoration and the three BTL callers of the lazy camera publication helper are separated from renderer-pointer substitution. The persistent `+0x0C0` copy and refresh-scratch `+0x0C0` are distinct data paths.
- **Unresolved or untested:** A computational consumer of persistent matrix `+0x0C0` is not established; its full-state data copy is established. The inspected paths do not enumerate every inline environment store, renderer attachment, screen or model caller. Extreme/nonfinite conversion inputs and degenerate camera bases are not established.
- **Deliberate exclusions and overlap:** Visibility decisions belong to [Visibility bounds and culling](visibility.md), scene/model hierarchy to [Model runtime](model_runtime.md), named 2D callers to [2D draw ownership](draw_2d_owners.md), packets to [Render submission](render_submission.md), material state to [Texture and material runtime](texture_material_runtime.md), off-screen targets to [Shadow rendering](shadow_rendering.md), downstream VU execution to [Model VU programs](model_vu_programs.md) and [Shadow VU program](shadow_vu_program.md), particle scheduling to [Particle runtime](particle_runtime.md), and battle camera requests to [Battle camera](../gameplay/battle_camera.md). This document owns their shared transform contract and environment selection at those boundaries.
- **Evidence limitations:** Findings are static retail-code observations. Preserved function boundaries and decompiler argument recovery can be wrong; instruction operands take precedence. No whole-program absence claim follows from a missing xref.

## Persistent transform state

`FUN_0010f2e0` initializes a caller-supplied render-state object. It clears the
vectors at `+0x200`, `+0x210`, `+0x220`, and `+0x230`, sets both components of
the upper-limit vectors to `4095.0`, installs depth defaults through
`FUN_0010e410` and `FUN_0010f480`, stores `45.0` at `+0x29C`, refreshes with an
identity camera matrix through `FUN_0010daf0`, then supplies a logical viewport
`(0, 0, 512, 384)` with both projection scales `1.0` through `FUN_0010f430`.
The constructor's exact order matters: the initial camera refresh precedes the
viewport/scale initialization; a later camera refresh supplies matrices derived
from the initialized viewport. The constructor itself does not perform that
second camera refresh.

| Owner path | Allocation/attachment contract | Lifetime evidence |
| --- | --- | --- |
| `FUN_0010a1d0(base, order, suppliedRenderer)` | Zero supplied pointer allocates `0x2B0` bytes with `FUN_00117150`, initializes through `FUN_0010f2e0`, stores the pointer at base `+0x3C`, and sets ownership byte `+7` to one. Nonzero pointer is borrowed and sets `+7` to zero. | `FUN_0010a040` frees an owned previous renderer through `FUN_0010f280(renderer,1)` before installing a borrowed replacement. |
| `FUN_00329740(owner)` | Renderer is embedded at owner `+0x1C0`; `FUN_0010f2e0` receives that address. | `FUN_00329850` unlinks it through `FUN_0010f280(owner+0x1C0,-1)` before destroying the owner's draw bases at `+0x180/+0x140`; it does not separately free the embedded renderer. |
| `FUN_00376a80` | Lazily creates an eight-byte holder, separately allocates `0x2B0` renderer, stores it in holder `+0`, creates a resource-linked object in holder `+4`, and refreshes from that object's camera at `+0x10C`. | Holder global is `gp-0x326C`; `FUN_00376b40` destroys/frees both children and holder, then zeroes the global. |

`FUN_00105fc0` uses the allocation path for the primary environment at
`0x00609160` and display environment at display `+0x110`. It then creates
display environment `+0x150` with the pointer from display `+0x14C`, which
is the preceding environment's renderer slot. These two display environments
therefore share one renderer, while the primary environment has its own.

The embedded construction above does not imply that every draw base in that
owner uses the embedded state. `FUN_00329930` initializes base `+0x180` with
an externally supplied renderer and base `+0x140` with a separately allocated
one, then sets both viewports. Its constructor's renderer at `+0x1C0` is a
distinct storage location.

`FUN_0010f1e0` prepends every initialized state to the list at `gp-0x3624`,
using renderer `+0x268` as next pointer. `FUN_0010f140` removes a matching
state; `FUN_0010f280` always requests that removal for a nonzero state and
frees its allocation only when its signed second argument is positive.

`FUN_001bb9d0(destination, source)` is another proven writer. Its bounded
field copy transfers the eight matrices, four limit vectors, vector `+0x240`,
viewport bounds, packed bounds, list pointer, scales, rectangle, depth, field
of view and focal coefficient, continuing through `+0x2A8`. Thus the shared
two-field scale setter is not the only mechanism that can publish scale values
into a renderer. The copy's scoped scene-draw use is described below.

The following are direct writes in the shared core, not inferred C++ names.

| Object range | Established role | Proven writer |
| --- | --- | --- |
| `+0x000..+0x03F` | `C^-1 * Rx(-pi)` using the rigid inverse; translation column is then reset to `(0,0,0,1)` | `FUN_0010daf0`, `0x0010db64..0x0010dbe0` |
| `+0x040..+0x07F` | Configured-display projection composed with supplied camera transform | `FUN_0010daf0`, `0x0010de4c..0x0010de60` |
| `+0x080..+0x0BF` | Supplied camera transform, or the composed pair when a third matrix is supplied | `FUN_0010daf0`, `0x0010db18..0x0010db60` |
| `+0x0C0..+0x0FF` | Symmetric near/far projection composed with the same camera transform | `FUN_0010daf0`, `0x0010e00c..0x0010e0e8` |
| `+0x100..+0x13F` | Fixed-512-reference projection composed with the camera transform | `FUN_0010daf0`, `0x0010de78..0x0010df3c` |
| `+0x140..+0x17F` | Configured-display projection before camera composition | `FUN_0010daf0`, `0x0010de64..0x0010de74` |
| `+0x180..+0x1BF` | Separate affine device mapping with width/height half-extents and depth midpoint | `FUN_0010daf0`, `0x0010e0ec..0x0010e1bc` |
| `+0x1C0..+0x1FF` | Logical 2D transform composed with 16-unit-per-pixel device mapping | `FUN_0010ecd0` |
| `+0x200..+0x23F` | Two lower/upper limit-vector pairs: `+0x200/+0x210` XY are device viewport endpoints; `+0x220/+0x230` XY initialize to `0/4095`. Both pairs store near/far in W. | Constructor, `FUN_0010e410`, viewport updater; full-copy writer also transfers them |
| `+0x240..+0x24F` | Rigid inverse camera matrix applied to `(0,0,-1,1)` at `0x005BED60` | `FUN_0010daf0`, `0x0010dbe4..0x0010dbfc`; vector bytes `00000000 00000000 000080BF 0000803F` |
| `+0x250..+0x25F` | Viewport left, top, right and bottom in configured display pixels | `FUN_0010e460` |
| `+0x260..+0x267` | Packed clamped integer viewport bounds | `FUN_0010e460` |
| `+0x26C/+0x270` | Device-centered projection translation | `FUN_0010e460` |
| `+0x274/+0x278` | Horizontal/vertical projection scales | Four-instruction `FUN_0010ecc0` |
| `+0x27C/+0x280` | Caller-provided projection-center offsets in logical units | `FUN_0010e460` |
| `+0x284/+0x288/+0x28C/+0x290` | Logical viewport left, top, width and height | `FUN_0010e460` |
| `+0x294/+0x298` | Depth-map endpoints, used independently of near/far planes | Four-instruction `FUN_0010f480` |
| `+0x29C` | Field of view in degrees, converted using `0.017453292` and halved before tangent evaluation | Constructor and camera wrapper `FUN_0010e220` |
| `+0x2A0` | Configured-width focal coefficient | `FUN_0010daf0`, `0x0010dcb4..0x0010dcbc` |

All fields in this table are also transferred by the full-copy writer above.
`FUN_0010e410` sets near `+0x20C/+0x22C` and far `+0x21C/+0x23C` without
refreshing matrices. Defaults are near `8.0`, far `1048576.0`, depth endpoint
`+0x294 = 0`, and `+0x298 = 1048575.0`. `FUN_0010e220` obtains field of view
from camera record `+0x0C` and supplies camera matrix `+0x10` plus optional
third matrix to the complete refresh.

## Matrix storage and multiplication

Each matrix occupies four consecutive vec4 columns. `FUN_00151ff0`
(`0x00151FF0..0x0015201B`, exposed by wrapper `FUN_0010ba40`) explicitly
computes `col0*x + col1*y + col2*z + col3*w`; translation is the fourth
column at `+0x30`. `FUN_00152020` (`0x00152020..0x00152063`, wrapper
`FUN_0010ba60`) does that operation for every column of its second input.
Thus `multiply(out,A,B)` produces `A*B`, applying `B` first.

`FUN_00152138` (`0x00152138..0x001521A3`) transposes the upper 3 by 3
matrix and replaces translation with its negated product against the original
translation. This is a rigid-transform inverse, rather than a general inverse
for arbitrary scale/shear. The refresh routine uses it for its camera input.
With optional third matrix `T`, refresh first forms `C = T*cameraMatrix`;
otherwise `C` is copied directly. It stores `C` at `+0x80` and forms its
derived projection matrices as `projection*C`. The fixed rotation comes from
`FUN_0010e200 -> FUN_00152460`, whose basis preserves X and rotates Y/Z.

## Camera matrix builders

The renderer receives a world-to-view matrix in camera record `+0x10`.
Three shared resident builders establish its direction and composition order;
camera selection and movement remain with the camera's owner.

| Builder | Observed input-to-matrix contract |
| --- | --- |
| `FUN_0019c290(camera, eye, target)` | Forms `forward = target-eye`. Reference axis is `(0,0,-1,0)`, changed to `(1,0,0,0)` when forward X and Y are both zero. Calls `FUN_00152628` to write camera `+0x10`. |
| `FUN_00152628`, `0x00152628..0x001526D7` | Constructs column basis `right = normalize(referenceAxis cross forward)`, `forward = normalize(forward)`, `up = forward cross right`, adds eye translation, then applies the rigid inverse. The stored matrix therefore transforms world points into that camera basis. Cross product and XYZ normalization are `FUN_00152068` and `FUN_001520b0`; both produce vector W zero. |
| `FUN_0019c340`, `0x0019C340..0x0019C407` | Forms `sourceTransform * Rx(pi)`, rigid-inverts it, and copies the result to camera `+0x10`. It temporarily advances display scratch by `0x50`, then restores the cursor. |
| `FUN_0019c410`, `0x0019C410..0x0019C533` | Builds orientation `Rz(az)*Ry(ay)*Rx(ax)*Rx(pi)` from the three caller angles, adds the caller position to translation, rigid-inverts, and stores camera `+0x10`. It uses and returns `0x50` scratch bytes. |

The rotation helpers left-multiply the source matrix by their rotation:
X `FUN_00152460`, Y `FUN_00152508`, Z `FUN_001523b8`. This is established
by their four-column vector loops, not by call order alone. Their angle input
is radians; the camera builders' fixed X rotation uses float bits
`0x40490FDB` for pi. The degree-to-radian conversion belongs to the renderer's
separate field-of-view calculation.

## Projection refresh

The full instruction range of `FUN_0010daf0` is
`0x0010DAF0..0x0010E1DF`. It obtains `0x1C0` bytes through `FUN_0010bae0`,
uses that area for temporary matrices, and returns it through `FUN_0010b9f0`
before returning. This is a separate scratch lifetime from the caller's
render-state object.

Let `W/H` be the display halfwords at the display object `+8/+0xA`, `gY` its
float at `+0x10`, `theta` renderer `+0x29C`, `sx/sy` renderer
`+0x274/+0x278`, and `cx/cy` renderer `+0x26C/+0x270`. The code computes
`d = 2*tan(theta*pi/360)`, `F = W/d` and `F512 = 512/d`. It stores `F` at
`+0x2A0`. Thus the two focal coefficients coincide only when `W = 512`.

Before camera composition, the configured-display projection has diagonal
coefficients `F*sx` and `F*sy*gY`, homogeneous output `w' = z`, and center
contributions `cx*z`, `cy*z`. With near/far values `n/f` from
`FUN_0010e1f0`/`FUN_0010e1e0` and depth endpoints `z0/z1` from
`+0x294/+0x298`, its depth numerator is `B*z + A`, where
`A = n*f*(z1-z0)/(f-n)` and `B = (z0*f-z1*n)/(f-n)`.
After homogeneous division, `depth = B + A/z`, which maps near `n` to `z1`
and far `f` to `z0`. This reverse ordering is derived directly from the matrix
product; it agrees with the separate affine depth mapping below.

The fixed-reference projection uses `F512*sx`, `F512*sy`, and half the logical
viewport width/height (`+0x28C/2`, `+0x290/2`) as center contributions. It
reuses the depth terms of the temporary matrix. Unlike the configured-display
projection, it does not multiply the vertical scale by `gY`.

The symmetric projection at `+0x0C0` uses horizontal/vertical coefficients
`F/(W/2)` and `F/(H/2)`, depth coefficients `(f+n)/(f-n)` and
`-2*f*n/(f-n)`, and homogeneous output `w' = z`. The separate affine mapping
at `+0x180` contains `(W/2)*sx`, `(H/2)*sy*gY`, depth scale `(z0-z1)/2`,
depth translation `(z0+z1)/2`, and center translations `cx/cy`.

**Inference, high confidence:** The recorded coefficients give
`deviceAffine*symmetricProjection = configuredProjection`. Since stored
`+0x0C0` already includes `C`, the corresponding stored-matrix product is
`renderer[+0x180]*renderer[+0x0C0] = renderer[+0x40]`, apart from floating
arithmetic rounding. This algebraic equivalence does not establish a consumer
of `+0x0C0` or prove that a draw path multiplies those stored matrices.

### Persistent `+0x0C0` and bounded alias tracing

**Observation:** the complete refresh has two different bases with a `+0xC0`
address. Its `s0` is the allocated `0x1C0`-byte scratch block; the renderer
argument is retained on the stack. Instructions `0x0010DE78..0x0010DF3C`
initialize and multiply **scratch** `+0xC0`, then use it as an input to the
write of renderer `+0x100`. The write of persistent renderer `+0xC0` at
`0x0010E0D4..0x0010E0E8` instead reloads the renderer argument, sets the
destination to that base plus `0xC0`, and supplies scratch `+0x100` and
scratch `+0x40` as the multiplication inputs. A literal `0xC0` in this
function therefore cannot by itself establish a read of persistent `+0xC0`.

The full-state copy's specific alias chain is
`sourceRenderer+0xC0 -> t0 -> lw +0/+4 -> destinationRenderer+0xC0` at
`0x001BBA54..0x001BBA7C`. Eight iterations advance both pointers by eight
bytes, transferring exactly 64 bytes. Its only resident xref caller is
`FUN_001BB790`; direct-call word `0x0C06EE74` likewise has only that resident
site after alias deduplication and no matches in imported BTL or ETC. In that caller the sequence is copy at `0x001BB7F0`, bind
at `0x001BB7FC`, and camera refresh at `0x001BB808`, before model/effect,
composition or attached-manager submission. There is no intervening
computational use of the copied `+0xC0` in this caller; the refresh replaces
that matrix from the scene camera before those submissions.

A bounded byte search of the resident executable for aligned `addiu`, `lq`
and `lqc2` instructions with a literal `0xC0` offset found the following
renderer-adjacent candidate families; each was followed through its complete
available function body:

| Candidate family | Established base of the apparent `+0xC0` access |
| --- | --- |
| `FUN_0010CB50`, `FUN_0010D8E0` | Render/light environment storage, including an embedded light-list head; distinct from the `0x2B0` transform state. |
| `FUN_0018D740`, `FUN_0018E240`, `FUN_0018E530` | A separately allocated `0x140`-byte geometry-processing workspace; `+0xB0/+0xC0/+0xD0` hold decoded triangle vectors. |
| `FUN_00193A70`, `FUN_00193B50` | A `0xC0` stride advancing source payload addresses between packet batches. Their three resident xref caller classes (`FUN_001939E0`, `FUN_00192FB0`, `FUN_001B0790`) supply geometry descriptor `+0x1C/+0x20` or draw-context `+0x238/+0x23C` payload pointers. |
| `FUN_001822B0` | A draw workspace's color product vector at `+0xC0`; its projection inputs separately use the bound renderer's `+0x1C0` or `+0x40`. |
| `FUN_0019AEB0` | A scene-node-derived object's vector at `+0xC0`, scaled by object `+0xB0`; the base is the supplied object, not a renderer obtained from environment `+0x3C`. |
| `FUN_001A2BB0`, `FUN_001A2E70` | Local object orientation matrices/vectors used by interpolation; their objects also carry position at `+0x100` and scale at `+0x80/+0x94/+0xA8`. |

These are bounded candidate classifications. The search does not cover every
scalar access in `+0xC0..+0xFC`, computed indexing, an alias formed by multiple
smaller additions, indirect calls or arbitrary external bulk copies. Other
literal candidates remain unclassified. The established copy and these
classified false leads neither prove that persistent `+0xC0` is unused nor
establish a visible fault.

## Logical viewport and 2D device coordinates

`FUN_0010e460` first retains the caller's logical rectangle, then converts X
values by `W/512` and Y values by `H/384`. It stores floating bounds
`(left, top, left+width, top+height)` at `+0x250..+0x25C`. The packed bounds
use conversion helper `FUN_001711c0` after adding `0.5` to left/top and
subtracting `0.5` from right/bottom, then clamp each coordinate to
`0..W-1` or `0..H-1`. For finite viewport-sized inputs, the helper truncates
toward zero: `FUN_001711c0` converts the absolute value through
`FUN_00171098` and restores its sign; its final unsigned conversion
`FUN_00171f58` shifts the significand without a rounding increment.
This bounded result does not cover extreme or nonfinite values.

Device-centered origin is logical viewport origin in display pixels plus
`2048-W/2`, `2048-H/2` (the half-dimensions use integer shifts). Projection
center adds the caller's center offsets scaled by `W/512`, `H/384` to that
origin. Separately, the routine adds `0.5` to the device-centered endpoints,
converts through scalar `cvt.w.S`, then converts the integers back to float
at `+0x200/+0x204` and `+0x210/+0x214`. This endpoint path is distinct from
the packed-bound helper. It calls the shared projection-scale writer at
`0x0010EC30 -> 0x0010ECC0`, then resets the logical 2D transform through
`FUN_0010ec90` with scales `1.0/1.0`, rotation `0`, and pivot `(256,192)`.

`FUN_0010ecd0` constructs a pivot-based logical transform by first translating
by the negative pivot, installing horizontal/vertical scales, optionally
rotating, and translating by pivot plus caller offset. It composes this with
an affine device mapping whose diagonals are `16*W/512`, `16*H/384` and whose
translations are `32768-8*W + viewportLeft*16*W/512` and
`32768-8*H + viewportTop*16*H/384`. The result is written to `+0x1C0`.
With `W/H = 512/384`, identity local transform and zero viewport origin,
logical `(256,192)` maps to device `(32768,32768)`, and one logical unit maps
to 16 device units. This center calculation follows the recorded coefficients;
the packet-level meaning belongs to render-submission research.

## Coordinate utility consumers

The following consumer contracts are established by instructions, including
conversion masks that the decompiler does not recover correctly.

| Function and bounds | Transform and output contract |
| --- | --- |
| `FUN_0010e270`, `0x0010E270..0x0010E2FB` | Applies renderer `+0x100` through `FUN_00152af0` to a homogeneous input vector, divides XYZ by resulting W, converts X/Y back from four-fraction-bit integers using `FUN_0010e300`, converts integer Z to float, and writes output W as zero. This returns logical projected X/Y plus mapped integer depth. |
| `FUN_00152af0`, `0x00152AF0..0x00152B33` | Calculates a matrix-vector product and `Q=1/w`, multiplies **XYZ** by Q, then executes `vftoi4.xyzw`. When fourth argument is nonzero, only **ZW** are overwritten by `vftoi0.zw`; X/Y retain four fractional bits. The decompiler's apparent whole-vector `vftoi0` is incorrect. |
| `FUN_0010e320`, `0x0010E320..0x0010E407` | Forms camera-space point `(depth*(screenX-256)/F, depth*(screenY-192)/F, depth, 1)` using `F=renderer[+0x2A0]`, rigid-inverts renderer `+0x80`, and transforms the point into world space. |
| `FUN_0010efa0`, `0x0010EFA0..0x0010EFD7` | Applies renderer `+0x1C0` and converts all components with `vftoi0`; output X/Y already represent 16 units per display pixel because that factor is in the matrix. No homogeneous divide is performed. |
| `FUN_0010f020`, `0x0010F020..0x0010F077` | Copies floating device rectangle endpoints `+0x200/+0x204/+0x210/+0x214`; it does not project an input point. |
| `FUN_0010efe0`, `0x0010EFE0..0x0010F01F` | Obtains those four endpoint floats through `FUN_0010f020` and converts using `FUN_0010ba00`'s `vftoi4`. |
| `FUN_0010f080` / `FUN_0010f0c0` | Copies floating pixel viewport bounds at `+0x250`, or converts all four to four-fraction-bit integers respectively. |
| `FUN_0010f100` | Copies the inverse-camera-derived vector at `+0x240`. |

**Inference, high confidence:** `FUN_0010e320` is a depth-specified
screen-to-world utility, but its formula is not a general inverse of the
renderer projection. It uses fixed center `(256,192)` and configured-width
`F`, without consulting viewport center, logical rectangle or either scale
field. Calling it an unconditional inverse of `FUN_0010e270` would therefore
overstate the evidence. Their formulas coincide in X/Y for the default
512-unit identity-scale case with matching camera-space depth, subject to the
forward utility's quantization. The inverse utility requires that camera-space
depth, whereas the forward utility returns mapped depth `B + A/z`.

The direct resident consumers of `FUN_0010efa0` (`FUN_001cc3a0`,
`FUN_00183650`, `FUN_00309800`) transform a rectangle's anchor through the
complete `+0x1C0` matrix but scale its extents only by diagonal fields
`+0x1C0/+0x1D4`; the callers and their clipping belong to
[2D draw ownership](draw_2d_owners.md#clipping-and-coordinate-ownership).

## Per-draw 2D transform records

`FUN_0010bb10` initializes a separate draw record, not the persistent renderer.
Its proven transform fields are rotation `+0x0C`, horizontal/vertical scale
`+0x10/+0x14`, pivot `+0x20/+0x24`, and local translation `+0x28/+0x2C`.
The two scale fields receive the same caller float; pivot defaults to
`(256,192)` and translation to `(0,0)`. `FUN_0010bc00` supplies the same
transform defaults with unit scale and zero rotation. Color, draw mode and
other packet controls have separate ownership.

Both branches in `FUN_0010a520` read renderer from draw environment `+0x3C`.
For a viewport of logical size `(rw,rh)` and pivot `(px,py)`, they construct
four corners `(-px,-py)`, `(rw-px,-py)`, `(-px,rh-py)`,
`(rw-px,rh-py)`. The local matrix is `T(pivot)*T(offset)*Rz(rotation)*S`,
then the code forms `renderer[+0x1C0]*local` and transforms all four corners.
The first branch's relevant construction/composition is
`0x0010A980..0x0010AB7F`; the second's is `0x0010B3B0..0x0010B593`.
The branch selector is draw-record byte `+0x31` at `0x0010A564`, and both
paths share this transform contract despite different packet operations.

This separates three lifetimes: persistent renderer state, caller-supplied
local draw-record fields, and temporary composed matrices obtained from the
display scratch cursor. `FUN_0010bae0` rounds scratch requests up to sixteen
bytes and advances display `+0x1C0`; `FUN_0010b9f0` restores the old cursor.
The scratch allocator does not construct or register a persistent renderer.

## Refresh and binding order

`FUN_0010f430` derives center offsets from half the caller's rectangle width
and height and forwards to `FUN_0010e460`. `FUN_0010f210` walks the renderer
list and replays each object's stored rectangle, center offsets and scales
through that updater. Its direct caller is display reconfiguration
`FUN_001065a0`, after that routine updates configured dimensions and vertical
factor `gY = H*(4/3)/W`. The list refresh resets `+0x1C0` to its default
local transform and republishes viewport/scales; it does not call the camera
projection refresh `FUN_0010daf0`. The scale setter, near/far setter,
depth-endpoint setter, viewport updater and camera refresh are therefore
distinct state-changing operations.

`FUN_00106230` selects the active draw environment at `gp-0x35FC`, rather than
storing a renderer pointer. Its renderer is environment `+0x3C`.
`FUN_0010a040` is the ownership-aware replacement described above, while
`FUN_001bb9c0` directly swaps that pointer without touching ownership byte
`+7`; `FUN_001bbc90` retrieves it. The main resident environment at
`0x00609160` has renderer pointer word `0x0060919C`; battle camera publication
through that environment is owned by
[Battle camera](../gameplay/battle_camera.md#common-camera-update-and-output).

`FUN_001bb790` (`0x001BB790..0x001BB987`) supplies a scoped camera context.
When scene-play object `+0x10C` is nonzero, it saves the active environment's
renderer, lazily allocates `0x2B0` bytes into scene `+0x110`, copies the saved
renderer through `FUN_001bb9d0`, binds that copy, and refreshes it from the
scene camera through `FUN_001bb990 -> FUN_0010e220`. After the scene's draw
work it restores the saved renderer pointer at `0x001BB930..0x001BB938`.
This path calls no renderer constructor/list registration. The copied next
pointer is data in the clone; it does not by itself insert that clone into the
registered renderer list. The scene destructor `FUN_001b7570`, at
`0x001B75B8..0x001B75CC`, frees the clone through `FUN_00105650` and clears
scene `+0x110`. Other scene-play allocation/release and callers belong to
[Scene playback owners](scene_playback_owners.md).

### Draw-environment selection and streamed exceptions

The selector is exactly `sw a0,-0x35FC(gp); jr ra; nop` at
`0x00106230..0x00106238`. Its global is `0x006073F4`; the independently
selected render/light environment is `0x006073D4` (`gp-0x361C`). A byte search
for direct-call word `0x0C04188C` found six resident instruction sites in
five functions and no matches in BTL or ETC; xrefs identify the same five
callers, whose selector arguments establish this direct-call inventory:

| Caller / selector site | Selected draw environment and condition |
| --- | --- |
| `FUN_00105FC0` / `0x001060E4` | Selects primary environment `0x00609160` after its construction. |
| `FUN_001081B0` / `0x0010833C` | Selects display `+0x150` after the optional display `+0x520` callback, when display `+0x192 & 7` is zero and that callback exists. |
| `FUN_001081B0` / `0x00108374` | Selects primary environment unconditionally before normal return. |
| `FUN_00108490` / `0x00108550` | Selects display `+0x150` before its draw/drain work; the selection itself is outside the `+0x192 & 7` gate. |
| `FUN_001086C0` / `0x00108934` | Selects display `+0x150` immediately before calling display `+0x500`, when the callback exists and display `+0x504` is nonzero. |
| `FUN_0010A0F0` / `0x0010A130` | When the destroyed environment equals the current global, selects the primary environment before releasing owned transform state. |

This is a complete inventory of that direct opcode in those three imports,
not a complete inventory of environment selection. Inline writes bypass the
selector. In particular, the streamed helper `FUN_001A0A40`
(`0x001A0A40..0x001A0B77`) saves both globals, selects scene `+0x110` as the
render/light environment and scene `+0xF4` as draw environment, constructs the
scene camera at `+0xF0`, then refreshes the renderer at `scene[+0xF4]+0x3C`.
Here scene is the object reached through container `+0x78`; it is distinct
from the object-animation player used by `FUN_001BB790` above.

The streamed wrapper next calls `FUN_001A2000` for its environment-group list
at scene `+4`. That helper selects each group's environment from group `+4`
through `sw v1,-0x35FC(gp)` at `0x001A2044`, then dispatches that group's
`0x0100` model and `0x0E00` textured-effect nodes. It leaves the selected
environment in the global. The analogous binding helper `FUN_001A1F40`
selects each group at `0x001A1F58` and likewise has no local restoration.
Their argument recovery is imperfect: instructions for the latter load the
list head through `a0`, whereas its decompilation associates that load with
the second displayed parameter. The group/environment field relationship is
established by the instructions independently of that prototype.

After group submission and the optional callback, `FUN_001A0A40` selects the
auxiliary 2D environment at scene `+0x10C` only when it is nonzero, draws
scene `+0x108` list entries through `FUN_0010A520`, then restores the saved
draw and render/light globals at `0x001A0B4C..0x001A0B50`. Instructions
`0x001A0B00..0x001A0B10` branch around the global store when `+0x10C` is zero;
the decompiler's apparent unconditional zero assignment is not the instruction
behavior. There is no constructor, full-renderer copy or renderer-pointer
swap in this wrapper: it selects existing environments and refreshes the
scene environment's existing renderer. Streamed scheduling and resource
ownership remain in [Scene playback owners](scene_playback_owners.md).

### Lazy camera publication into existing environments

`FUN_00376BF0` (`0x00376BF0..0x00376C2B`) checks holder global `gp-0x326C`
and, when present, calls `FUN_0010E220(environment[+0x3C],
holder[+4][+0x10C],0)`. Its first argument is a draw environment. It does
not fetch holder `+0`, which is the holder's own separately allocated
renderer initialized by `FUN_00376A80`. This distinction separates using the
holder's camera from selecting or copying the holder's renderer.

The exact direct-call word `0x0C0DDAFC` has three matches in BTL and none in
the resident executable or ETC; resident xrefs do not include these
cross-import calls. All three caller bodies and call argument instructions were
inspected:

| BTL preserved caller / call site | Environment choice and restoration |
| --- | --- |
| `FUN_006B4CC0` / `0x006B4CF4` | When owner `+0` contains a player, saves the current environment, selects the environment at shared owner `gp-0x33F0 -> +0xDD4`, publishes the holder camera into its renderer, advances the player when player `+0xFC` is nonzero, draws it through `FUN_001BB790`, then restores the global at `0x006B4D38`. |
| `FUN_006B4D60` / `0x006B4D88` | Uses the same shared environment for the player at owner `+4`, with the same camera/advance/draw sequence; restores at `0x006B4DCC`. |
| `FUN_0087F290` / `0x0087F2E8` | Its owner-byte `+1 == 0` branch saves and selects owner `+8`, publishes the camera, optionally advances player `+0xC`, submits that player, and restores at `0x0087F370`. The nonzero-byte branch decrements the byte and bypasses environment selection. |

These are preserved import addresses, whose live instruction addresses are
`+0x40`; their encoded resident call target remains `0x00376BF0`. The third
body is split in Ghidra: raw instruction word `0x10000029` at preserved
`0x0087F2D0` branches to the common epilogue at `0x0087F378`, and bytes
`0x0087F378..0x0087F397` restore the registers/stack and return. This
corroborates the nonzero-byte bypass and the zero-byte restoration without
inventing a missing fallthrough from the truncated disassembly.

Restoring the selected environment global is not a rollback of the camera
refresh into its renderer. The scoped player-camera path can subsequently
bind and refresh its own copy as described above. The three callers establish
this sequence, not a player-facing identity, a character-specific difference
or reachability from every battle state.

### Particle environment overrides and nested scene cameras

The manager loops `FUN_0034FFD0` and `FUN_003530A0` save the current draw
environment **after** calling emitter virtual slot `+0x18`. They select
nonzero emitter `+0x1D8` for the particle loop and restore the saved global
before calling emitter slot `+0x1C`. Selection/restoration instruction sites
are `0x00350020/0x003500A4` and `0x00353104/0x00353184`. Both restorations
require the emitter override and the saved environment to be nonzero
(`0x00350090..0x003500A4`, `0x00353170..0x00353184`). Thus these bodies do
not implement an unconditional save/restore when the saved global is zero.
No occurrence or visible consequence of that case is established.

Emitter `+0x1D8` is a draw-environment pointer, not a matrix or
transform-state pointer, and the draw loop reads it live at each selection.
How the base and battle generator classes publish it, including the scene
action wrapper `FUN_001ABD60`, is owned by
[Particle runtime](particle_runtime.md#battle-particle-generator-extension).

**Inference, high confidence within these paths:** an environment reference
retained in an emitter refers to that environment's current
`+0x3C` renderer slot; it does not snapshot the renderer. When
`FUN_001ABD60` is called within `FUN_001BB790`, the scene-copy binding remains active until
after the manager returns. A particle whose visual dispatch reaches another
`FUN_001BB790` can perform another scoped renderer substitution on its
selected environment. The proven normal-return restoration is of each saved
renderer pointer; there is no copy-back of the inner renderer into the saved
one. Particle dispatch/history contracts remain in
[Particle runtime](particle_runtime.md#concrete-visual-update-and-draw).

## Model-to-device composition and draw scratch

`FUN_00190f40` obtains a `0x280`-byte block from the display scratch cursor
when model submission work is needed. `FUN_001982b0` fills that draw context:
`+0x110` points to the scene node's accumulated world matrix, `+0x1FC`
captures the active draw environment from `0x006073F4`, and `+0x1F8`
captures its renderer from environment `+0x3C`. Field `+0x1F4` separately
captures render/light environment `0x006073D4`, selected by `FUN_00106210`.
The draw context is not another persistent renderer. The caller dispatches
ordinary and shadow work as applicable, then restores the scratch cursor.
Scene-node matrix construction and hierarchy belong to
[Model runtime](model_runtime.md#composition-hierarchy-and-matrix-lifetime).

The common composition in `FUN_001910e0`, at
`0x00191234..0x00191240`, is
`drawContext[+0x80] = renderer[+0x40] * worldMatrix`.
Before that, a branch selected by draw-context flags `+0x20C & 0x100000`
uses the lengths of the world matrix's XYZ basis columns as diagonal scales,
multiplies them by renderer `+0x000`, restores world translation and points
draw-context `+0x110` to that replacement matrix. Both branches subsequently
use renderer `+0x40`. The ordinary visibility path receives this composed
draw matrix; its decisions are owned by [Visibility](visibility.md).

The packet producer `FUN_0018ffb0` normally copies that draw-context matrix.
Its part-depth branch at `0x00190354..0x001903F8`, selected when part
`+0x28` is nonzero, copies projection-only renderer `+0x140` into draw
scratch, changes its depth coefficient, then composes it with renderer
`+0x80` and the current world matrix. The replacement coefficient is
`B - A*delta/(z*(z+delta))`, with `delta = part[+0x28]` and
`z = drawContext[+0x10C]`; `A/B` are the near/far depth terms above.
This modifies the draw matrix in scratch, leaving the persistent renderer's
projection matrices intact. Upload layouts and downstream execution belong to
[Render submission](render_submission.md).

The shadow geometry path `FUN_0018cf70` also starts from configured-display
projection: controller renderer `+0x40` times the current world matrix. It
then applies local shape scale and a target remap derived from the renderer's
device rectangle returned by `FUN_0010f020`. Projection-only `+0x140` is
used separately for its near-plane input. These are scratch compositions;
the target size does not itself demonstrate another persistent renderer.
The renderer is read from controller `+0x4C`, rather than draw-context
`+0x1F8`. The scoped scene swap through `FUN_001bb9c0` writes only the active
environment's `+0x3C` slot and leaves that controller slot unchanged.
Controller attachments, remap coefficients and target lifetime are owned by
[Shadow rendering](shadow_rendering.md#geometry-inputs-and-renderer-ownership).
