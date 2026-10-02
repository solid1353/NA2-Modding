# UI animation and easing

This document records presentation-value animation in retail NA2
(`SLPS-25837`). Screen navigation and layout remain with their own documents.
Binary identities and address conversion follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Reusable UI animation helpers and controllers: fades,
  slides, pulses, recursive easing, delays, reverse cursors, completion, and
  pause/update/reset/lifetime ownership.
- **Exploration depth:** the complete instruction bodies of the scalar
  approach, RGBA pool updater, panel transition, scrolling updater,
  squash/stretch sampler, and Character Select common scalar tail were read.
  Constructors, reset/rearm operations, callback-table initialization, and
  representative Mode Select, Options, Character Select and Collection
  producers/consumers were traced. The five direct scalar call sites are
  accounted for; other controller caller sets were sampled rather than exhausted.
- **Confirmed coverage:** Arithmetic and endpoint order; call-based timing;
  separate update/draw ownership where present; drawing that also advances
  counters; allocation, slot reuse, text gates, delay gates and local resets.
  The selector's recursive formula and request-driven pulse are established,
  with their distinct completion behavior.
- **Unresolved or untested:** The fade pool gate's writer, the `0x08` phase's
  arming producer, the selector-relative `+0xBC` rendering consumer, Collection
  pulse-counter initialization, and all unexamined controller callers remain
  unresolved. No exhaustive inventory of every UI animation is claimed.
- **Deliberate exclusions and overlap:** [Mode flow](../game/mode_flow.md)
  owns screen state machines; [Character Select](../game/character_select.md)
  owns selector navigation; [Animation runtime](animation_runtime.md) owns
  resource-driven playback; [Timer primitives](timer_primitives.md) owns
  general timers; [Battle HUD](../gameplay/session/battle_hud.md) owns HUD-specific gauges
  and clock effects. This document owns reusable UI presentation controllers
  and caller timing contracts. Screen layout and localization are excluded.
- **Evidence limitations:** Static evidence establishes
  arithmetic and local instruction order. It does not establish wall-clock
  duration or calls per displayed frame. Recovered direct xrefs and encoding
  scans are bounded because the preserved imports have incomplete analysis;
  indirect calls and pointer aliases may be absent. Raw instructions/bytes
  resolve floating-point ABI, unrecognized initializer code, and the inspected
  overlay call targets. Formula-derived conclusions are identified as such.

## Fixed-step scalar approach

Resident `FUN_00387400`, instruction range `0x00387400..0x00387458`, receives
target in `f12`, step in `f13`, and `float *value` in `a0`. For a positive
step it subtracts the step above the target, adds it below the target, and
clamps an overshoot to the target. Equality leaves the value unchanged. It
has no timer, completion return, reset, allocation or pause check: the caller
owns the float and decides when to invoke it. The helper itself does not
validate a positive step.

The direct-xref set consists of `0x003858D4`, `0x00389C54`,
`0x00389C84`, `0x00389CDC` and `0x00389D0C`. These are a recovered caller
set, not a whole-program absence proof. An independent direct-JAL encoding
search recovered the same five sites in the resident image, plus their
mapped aliases; it found no matching direct instruction in `BTL.BIN` or
`ETC.BIN`. This does not cover indirect dispatch.

Mode Select update `FUN_003854F0` passes target `0.0`, step `0.1`
(`0x3DCCCCCD`) and controller float `+0x28`. The common update tail performs
one approach call; its terminal-state early return skips that tail. After
the approach, the selected menu resource advances only when
`abs(controller.+0x28) <= 0.01`; other entries use a different resource
operation. Thus reaching the neighborhood of zero gates another animation,
but the helper's own clamp reaches exact zero. The units are value units per
call, with no elapsed-time multiplier. Menu selection and resource playback
remain with their owning documents.

### Options weights and arrow phase

The other four sites belong to Options subcontroller `FUN_00389550`.
Its common tail approaches four floats by `0.3` (`0x3E99999A`) per call:
`+0x74/+0x78` target 1 only for the selected choice `+0x28` while selected
row `+0x24 == 1`, otherwise 0; `+0x7C/+0x80` target 1 for the selected
row, otherwise 0. Constructor `FUN_003890F0` initializes all four to zero.
There is no completion latch in these loops; the scalar helper supplies
their endpoint clamps. Accept/cancel returns before the common tail.

The same tail advances float phase `+0x3C` by `0.05` and subtracts 1 only
when the new phase is greater than 1. Reset `FUN_003894C0` sets phase zero.
Draw consumer `FUN_00389FC0` maps the choice weights to vertical displacement
`(1-weight)*10`; it also uses `3*sin(pi*phase)` for the selected choice's
arrow. `FUN_00389D50` uses the same phase for mirrored arrows with
displacement `50 + 3*sin(pi*phase)`. Neither draw consumer increments this
phase. Main draw `FUN_0038A1F0`, instructions `0x0038A28C..0x0038A314`,
reads the row weights as floats and maps them to horizontal displacement
`(1-weight)*20`. It also uses `40 + 6*sin(pi*phase)` for the vertical
arrow pair. Thus the phase and both weight pairs have identified draw consumers.

## Four-slot RGBA transition pool

Resident `FUN_00185F50` allocates two `0x98`-byte pools and constructs each
through `FUN_001834B0`; their handles are `uGpffffca70` and `uGpffffca74`.
The constructor clears pool `+0x00`, each slot's flags, and pool `+0x94`.
It also establishes a shared default rendering context. There are four slots,
each `0x24` bytes, beginning at pool `+0x04`.

Slots are embedded in their pool; clearing one does not release the pool.
Destructor `FUN_001835C0` releases a non-null pool only when its second
argument, interpreted as a signed halfword, is positive. The release path
is `FUN_00117000` to allocator release `FUN_00117C40`; the destructor has
no separate per-slot allocation to free.

| Slot-relative offset | Type | Established use |
| --- | --- | --- |
| `+0x00` | halfword flags | Mask `0x01` means active; completion behavior uses masks `0x02`, `0x04`, `0x08`. |
| `+0x02` | signed halfword | Current transition cursor. |
| `+0x04` | signed halfword | Current phase duration. |
| `+0x06` | signed halfword | Second-phase duration set by `FUN_00183E80`. |
| `+0x08` | signed halfword | Intermediate-phase duration read by the `0x08` transition. Its arming producer is not established. |
| `+0x0C/+0x10` | floats | Rectangle origin. |
| `+0x14/+0x18` | floats | Rectangle extent. |
| `+0x1C/+0x20` | packed words | Start/end color, four separately interpolated bytes. |

Pool `+0x00 != 0` makes `FUN_00183650` return before both drawing and
advancement. Pool `+0x94` selects a rendering context; zero uses the shared
default. Slots are traversed in ascending index order. Coordinate conversion
and render-packet ownership belong to [2D draw ownership](rendering/draw_2d_owners.md).

Wrapper `FUN_00186000` supplies the current rendering context to the first
global pool, supplies `uGpffffca84` to the second, and invokes
`FUN_00183650` on each. Resident draw owner `FUN_00108490` calls this
wrapper outside its local `(engine.+0x192 & 7) == 0` scene-draw checks.
That establishes local scheduling order, not a universal pause exemption;
the pool's own gate still applies. Task scheduling belongs to
[Task system](task_system.md). The inspected constructor and reset do not
identify the caller that writes the pool gate.

### Arming, completion, and reuse

Each allocator searches indices `0..3` for flags exactly zero and returns
`-1` when none is available. It writes the rectangle and starts cursor zero.
The float rectangle ABI uses `f12..f15`; the pool and duration are integer
arguments. Function names below are resident addresses.

| Function | Initial flags | Color and phase contract |
| --- | --- | --- |
| `FUN_00183DF0` | `3` | Start = supplied packed color; end = its low 24 bits, making the high byte zero. Clears the slot after this phase. |
| `FUN_00183E80` | `5` | Start = supplied color with high byte zero; end = supplied color. Stores two durations; completion rearms the reverse color phase and then clears. |
| `FUN_00183F10` | `1` | Explicit start/end colors and one duration. Holds the endpoint after completion; the slot remains occupied. |
| `FUN_00183F90` | `1` | Rearms an existing index, cursor zero, supplied duration, start = previous stored endpoint, end = supplied color. Preserves rectangle. |
| `FUN_00183610` | `0` | Clears all four flags only. It does not clear cursors, colors or pool pause/context fields. |
| `FUN_00184000` | `0` | Clears one supplied slot index's flags only. |
| `FUN_00183FD0` | unchanged | Returns signed `cursor < duration`, without checking activity or validating the index. |

Rearming uses the old **stored endpoint**, not the currently interpolated
color. Clearing activity is therefore distinct from clearing timing storage,
and a held complete transition still occupies an allocator slot.

Resident wrappers `FUN_001EB600`, `FUN_001EB670` and `FUN_001EB700`
clear the second global pool before allocating a held full-screen rectangle
`(0,0,512,384)`. The first uses duration 1 and identical color endpoints;
the other two use caller-supplied duration and opposite endpoint ordering
from the same two-word color record. These callers own pool reset and
presentation direction; the pool does not choose them from screen state.

### Draw-before-advance order

The complete `FUN_00183650` body is `0x00183650..0x00183DE8`.
For each active slot, its packet path samples the current cursor and computes
each byte as `start + trunc((end - start) * cursor / duration)`, then masks
the result to eight bits. The signed division helper is `FUN_0016F568`.
The caller supplies a signed-halfword duration and performs no zero-duration
guard before division.

Only after packet values are written does `0x00183B78..0x00183B94` increment
the cursor by one and compare its signed-halfword result with duration. The
increment still executes when packet storage is unavailable: branch
`0x001837CC` skips to `0x00183B78`, not past the counter. Thus this pool
counts eligible **draw-function invocations**, not elapsed seconds or
successful submissions.

Completion chooses the first matching behavior, in this order:

1. Flags `& 0x02`: clear flags, freeing the slot.
2. Flags `& 0x04`: replace mask `0x04` with `0x02`, reset cursor, load the second
   duration, copy endpoint to start, and clear the endpoint's high byte.
3. Flags `& 0x08`: replace mask `0x08` with `0x04`, reset cursor, load the intermediate
   duration, and copy endpoint to start without changing endpoint.
4. Otherwise clamp cursor to duration and keep the active flag.

Consequently a one-phase held transition first samples cursors `0..D-1`,
becomes complete after invocation `D`, and samples exact endpoint `D` on the
next eligible call. A clearing or phase-switching transition changes state
after sampling `D-1`; it does not first emit an extra sample at `D` for that
phase. The `0x08` branch supports an intermediate constant-color phase, but
its in-scope arming caller remains unresolved. These statements assume a
positive duration that does not overflow the signed-halfword cursor.

## Shared panel open/close controller

The `0x80`-byte panel family begins with constructor `FUN_0037FFC0`.
`FUN_00380420` sets the style and rectangle and saves their resting values;
`FUN_003805F0` accepts a five-halfword record `(style, x, y, width, height)`.
This is a reusable animation controller, with recovered opening callers in
Mode Select, Options, Save/Load, Character Select and other resident dialogs.
Their navigation and text content are outside this document.

| Panel field | Established animation contract |
| --- | --- |
| `+0x00`, `+0x04..+0x10` | Current style and float rectangle. |
| `+0x14`, `+0x18..+0x24` | Saved resting style and rectangle. |
| `+0x40` | Signed-halfword state: `0` open/resting, `1` opening, `2` closing, `3` closed. |
| `+0x46` | Signed-halfword reverse cursor. |
| `+0x48` | Signed-halfword duration `D`. |
| `+0x58` | Float transition fraction consumed by panel rendering. |
| `+0x62/+0x63` | Text-enable byte and transition text-hiding policy byte. |
| `+0x64` | Opening sound-enable byte. |

`FUN_00381900(panel,D)` arms opening; `FUN_00381930(panel,D)` arms closing.
Both write `cursor = D` and store `D`. `FUN_00381950` restores the resting
rectangle, open state, fraction 1, cursor 0 and text-enable byte 1.
`FUN_00381A40` forces closed state, zero current rectangle/fraction and
cursor 0, without erasing the saved resting rectangle. Predicates
`FUN_00381FA0`, `FUN_00381FC0`, `FUN_00381FE0` mean respectively open,
closed, and either resting endpoint.

The transition engine `FUN_00381AB0`, complete instruction range
`0x00381AB0..0x00381EB8`, runs first in `FUN_00380B60`, before that
function draws the panel. It returns immediately for states other than 1/2.
For resting rectangle `(X,Y,W,H)`, cursor `q`, and positive duration `D`,
its arithmetic is:

| Value | Opening, state 1 | Closing, state 2 |
| --- | --- | --- |
| x | `X + (W/2 - 32)*q/D - D` | `X + (W/2 - 32)*(D-q)/D` |
| y | `Y + (H/2 - 32)*q/D - D` | `Y + (H/2 - 32)*(D-q)/D` |
| width | `64 + (W-64)*(D-q)/D + 2*D` | `64 + (W-64)*q/D` |
| height | `64 + (H-64)*(D-q)/D + 2*D` | `64 + (H-64)*q/D` |
| fraction | `(D-q)/D` | `q/D` |

The opening's `-D` position and `+2*D` size terms are literal code behavior;
duration participates in geometry as well as timing. Arithmetic samples the
old cursor **before** checking whether it is negative. For nonnegative `q`,
the function decrements it by one. It commits the resting endpoint only on
a call that begins with `q < 0`, overwriting that call's provisional arithmetic.
Thus arming with positive `D` requires `D+2` invocations to change state to
open/closed: `D+1` samples at `D..0`, then endpoint commit at `-1`.
It has no elapsed-time input or positive-duration guard.

When enabled, the opening sound is issued on the first sample `q == D`.
The transition policy can clear the text-enable byte. Text consumers
`FUN_00382470` and `FUN_00382610` check it; border/background paths
`FUN_00381510` and `FUN_00380C40` remain eligible while panel state is less
than 3. `FUN_00380B60` invokes the transition engine before those paths.
Suppressing this outer call stops cursor advancement; hiding text does not.
There is no independent pause flag in the inspected transition engine.
Destructor `FUN_003801C0` releases the text object, child render objects,
and attached content; the transition scalars live in the owning panel.

## Counter-driven squash/stretch pulse

Resident `FUN_0037E7C0`, complete instruction range
`0x0037E7C0..0x0037E944`, fills four floats `(110, 36, sx, sy)` and
mutates a caller-owned signed-halfword counter. It increments the counter
**before** choosing its sample. For the incremented value `t`:

| Counter range | Horizontal scale `sx` | Vertical scale `sy` |
| --- | --- | --- |
| `t < 10` | `1 - 0.05*t` | `1 + 0.03*t` |
| `10 <= t < 15` | `0.5 + 0.1*(t-10)` | `1.3 - 0.06*(t-10)` |
| `15 <= t < 20`, odd | `0.95` | `1.05` |
| `15 <= t < 20`, even | `1.05` | `0.95` |
| `t >= 20` | `1` | `1` |

At `t >= 101` it resets the counter to zero while still emitting the
resting sample. Starting at zero therefore gives a 101-invocation cycle;
there is no completion return or independent pause flag. Negative initial
values and signed-halfword overflow are not guarded.

Three recovered direct callers are drawing wrappers `FUN_0037E950`,
`FUN_0037EA80`, and `FUN_0037EBD0`. The first applies caller translation
and a uniform scale to the pulse. The second also swaps its scale axes,
draws with angle `pi/2`, then resets that sprite angle to zero. The third
accepts separate translation and axis-scale values. All three invoke the
helper once and center the scaled sprite. Sharing one counter among several
wrapper invocations would advance it several times; a render-only entrypoint
therefore need not leave presentation state unchanged.

Mode Select draw `FUN_00385C00` invokes `FUN_0037E950` with controller
`+0x50`; initialization `FUN_003839E0` sets that counter zero. Terminal
state 6 skips the draw body and this increment. Collection drawing in
`ETC.BIN` also invokes the resident wrapper with GP-owned counter
`gp-0x3034`, except in local states 6 and 9. Its caller is imported
`FUN_006C8250`, live `0x006C8290`; the collection entry wrapper's raw JAL
at imported `0x006C8930` establishes that address conversion. Raw JAL at
imported `0x006C8358` confirms the resident pulse-wrapper target.
Collection counter initialization and other wrapper callers are not traced.

Options main draw `FUN_0038A1F0` also invokes `FUN_0037E950`, with local
counter `+0x38` (`0x0038A458..0x0038A464`). `FUN_003894C0` resets that
counter to zero independently of the update-driven sine phase at `+0x3C`.
The same owner therefore has two presentation clocks with different call sites.

## Delayed scrolling strip

`FUN_0037ED00` initializes a reusable strip; `FUN_0037F460` applies a
`0x24`-byte configuration record, and `FUN_0037F420` selects a record at
resident `0x005B16E0 + index*0x24`. Four inspected adjacent records all
provide speed `2.0`. `FUN_0037F7F0` advances the strip;
`FUN_0037F900` draws its queued segments. The updater does not draw and the
renderer does not advance the scroll cursor.

| Strip field | Use |
| --- | --- |
| `+0x00/+0x04` | Horizontal/vertical viewport extent. |
| `+0x24` byte | Zero selects horizontal scrolling; nonzero selects vertical. |
| `+0x2C` pointer | Head of linked `0x10`-byte segments. |
| `+0x30` float | Scroll distance. |
| `+0x34` float | Distance added per eligible update. |
| `+0x38/+0x3A` | Signed-halfword delay and elapsed-delay counter. |
| `+0x3C` byte | Enqueue inhibition. |
| `+0x3D` byte | Minimum-first-segment extent policy. |

Each segment contains an ownership byte at `+0x00`, string pointer at
`+0x04`, float extent at `+0x08`, and next pointer at `+0x0C`.
`FUN_0037F590` enqueues only when the sum of existing segment extents is
no greater than scroll distance and enqueue inhibition is zero. A copied
string belongs to its segment; a borrowed string does not. When the first
segment is added and delay is nonzero, distance becomes `0.9*viewport_extent`
and elapsed delay becomes zero. The minimum-extent policy can enlarge that
first segment to `distance + 20`.

The instruction range `0x0037F7F0..0x0037F8FC` confirms all update branches.
An empty queue resets distance and elapsed delay. Otherwise, while
`elapsed < delay`, one is added to elapsed and the call returns without
scrolling. The first movement follows those delay invocations. Once eligible,
distance increases by speed; when it reaches `head.extent + viewport_extent`,
the updater subtracts the head extent and releases **one** head segment.
It does not loop through several expired segments in one call, even for a
large speed. The renderer places cumulative segments at
`viewport_extent - distance + accumulated_extent` on the selected axis.

`FUN_0037EEE0` clears and frees the whole queue and resets distance/delay
counter; `FUN_0037EE50` destroys child render objects and calls that clear.
These contracts establish lifetime and call-based units, without assuming
that a strip update equals one presented frame. Five recovered direct update
sites are `0x00385BCC`, `0x00388AA8`, `0x00389A4C`, `0x0038BE18` and
`0x0038C0CC`; the Mode Select common tail performs enqueue then update,
whereas the inspected Options subcontroller performs update then enqueue.
Options constructor `FUN_003890F0` selects configuration 3, sets delay 30,
and enables the minimum-first-segment extent policy. Delay thus counts 30
eligible updater calls in that owner. Enqueue inhibition is not an update
pause: `FUN_0037F7F0` does not inspect it. Suppressing the update call is the
only local pause mechanism established for this strip.

## Character Select presentation values

The selector's common updater `FUN_003B9480` is called for both player
objects from parent `FUN_003BCA90`. The parent's terminal-state early return
skips these updates. The selector update first dispatches its current
presentation-state callback, then advances resource-driven animations, then
executes the scalar/pulse tail. Resource playback itself belongs to
[Animation runtime](animation_runtime.md).

The 14 update callback records are copied from file-backed
`0x005B4328..0x005B4407` (source stride `0x10`) into runtime
`0x005D66B0..0x005D6757` (destination stride `0x0C`). Each inspected record
has adjustor 0, dispatch field `-1`, and a direct code pointer. Raw bytes
at `0x005D9A20..0x005D9CA8` establish these copies even though that
initializer range is not recognized as a function. `FUN_00119B10` consumes
the record; treating the initial zero-filled destination as the callback
table would miss all these consumers.

| State IDs | Callback | Presentation action relevant here |
| --- | --- | --- |
| 0 | `0x003B7AF0` | Raise `+0x3C` by `0.1` to 1, then lower `+0x2C` by `0.1` to 0; completion depends on both ordered ramps. |
| 4 | `0x003B7C60` | Raise `+0x2C` by `0.1` to 1, then lower `+0x3C` by `0.1` to 0; also wait for resource completion at `+0x90`. |
| 7 | `0x003B7DA0` | Raise `+0x3C` by `0.1`, clamp at 1, and wait for resource completion `+0x90`. |
| 8 | `0x003B7E70` | Poll the shared child panel's open predicate. |
| 10, 11 | `0x003B7EE0`, `0x003B7F40` | Poll the child panel's closed predicate. |
| 12 | `0x003B7FA0` | Inspect resource cursor/completion and select a resource sample. |
| 2, 3, 6 | `0x003B7BD0`, `0x003B7C30`, `0x003B7D70` | State routing without a scalar increment. |
| 1, 5, 9, 13 | `0x003B7BC0`, `0x003B7D60`, `0x003B7ED0`, `0x003B8040` | No-op `jr ra; nop`, corroborated through raw bytes because no function is defined. |

These are bounded presentation callbacks, not a description of the menu's
navigation state machine. Entry helpers `0x003B56B0..0x003B5BB0` initialize
the ramp endpoints and resource-completion latches. For example,
`FUN_003B56B0` starts `+0x2C` at 1, `FUN_003B5840` starts `+0x3C` at 1,
and `FUN_003B5910` starts `+0x3C` at 0. The shared panel is opened/closed
with duration 8 by `FUN_003B59D0`/`FUN_003B5AC0`.

### Linear motion, recursive easing and pulse request

The raw common tail `0x003B978C..0x003B99D8` establishes these contracts:

| Field | Formula/gate | Reset or consumption |
| --- | --- | --- |
| `+0x6C` float | Add `0.2` toward 1 when `+0x88` is neither 4 nor 3 and selector `+0x08` is neither 1, 3 nor 2; otherwise subtract `0.2` toward 0. Clamp both endpoints. | Constructor initializes zero; portrait renderer `FUN_003B83E0` maps it to a mirrored position with `30*x - 150`. |
| `+0x28/+0x38` floats | Outside `[-1,1]`, move by `0.2` toward the nearest endpoint. Inside that interval, leave unchanged. | Fighter/support selection setters reset their respective offsets; navigation adds/subtracts 1 per visited slot. Carousel consumers scale the offsets by 36. |
| `+0xBC` float | `x = x + (1-x)*0.02`, every common-tail call. | Fighter setter `FUN_003B4750` and successful navigation in `FUN_003B60A0` reset zero. No rendering consumer is established. |
| `+0x64` float | If phase or request `+0x68` is nonzero, add `0.03`. Only when new phase is **greater than** 1, subtract 1 if request is nonzero, otherwise reset phase zero. | Constructor initializes phase zero. Request `+0x68` is always cleared at the end of the update. `FUN_003B5C00` sets request to 1 on eligible input-processing updates, after its early-return gates. |

The recursive formula has no threshold, clamp or completion latch. In exact
arithmetic from zero its remaining distance is `0.98^n`; this is an inference
from the formula, not a measurement or a promised exact float endpoint.
Navigation wrap and eligibility belong to
[Character Select](../game/character_select.md). The inspected float-load
encoding scan found only the updater's selector-relative `+0xBC` load;
another `+0xBC` occurrence in the support renderer is stack-local. This does
not rule out an integer load, pointer alias or unexamined consumer.

`FUN_003B9160` reads pulse phase without advancing it. Its arrow displacement
is `5 * max(0, sin(pi*phase)-0.1) / 0.9`, applied to mirrored arrows. The
sine wrapper `FUN_0016F2E8` and polynomial kernel `FUN_0016DD28` were checked.
This is one half-sine pulse per normalized `0..1` traversal, with a dead zone
near both endpoints. A withdrawn request lets an already-started pulse finish;
it stops at zero on crossing rather than freezing immediately.
