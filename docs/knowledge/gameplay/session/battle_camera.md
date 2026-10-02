# Battle camera control

This note records how the retail NA2 (`SLPS-25837`) battle camera is built,
updated, and switched: the camera classes in the `ccCameraCtrl` registry, the
main gameplay camera that tracks both fighters and frames the stage from a
per-stage record, and the camera controller that switches to scripted
presentation cameras on requests and events. It does not cover Adventure,
cutscene cameras, rendering projection internals, or player-visible camera
policy that has not been observed at runtime.

All BTL addresses below are live addresses; preserved import addresses and
complete-file offsets follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Because the header-skipped import attaches some direct-call targets to a false
symbol `0x40` after the physical callee, the findings rely on instruction
bytes and field behavior rather than those call labels.

## Research coverage

- **Assigned scope:** the retail BTL battle camera: camera classes and
  activation, the common camera update and output, the main camera's tracking,
  distance, framing, and smoothing, its per-stage record, the camera
  controller's publication, slots, request/event-to-mode mapping, ownership
  switching, preset selection, stage-edge correction, and stage- or
  event-driven inputs.
- **Exploration depth:**
  - Registry and camera vtables resolved through RTTI; the common update,
    output helper, active-camera switch helpers, main-camera initializer,
    tracking, placement, both smoothing routines and its section-transfer
    branch read completely.
  - Every direct read of the per-stage record pointer, and every stage-slot,
    stage-controller, and `ccField` access in camera range
    `0x006D5640..0x006DE400`, enumerated.
  - Controller construction/destruction, publisher, update order, event-edge
    gate, slot loops, event jump table, numeric mode dispatch `0..18`, every
    mode handler, preset families, ownership switch, effect-record adaptation,
    all 55 contiguous effect-camera records, and the mode-18 correction
    helper traced.
  - Direct event-writer and reset calls enumerated in the resident and BTL
    programs.
- **Confirmed coverage:** class identities and activation; which vector is
  the eye and which the look-at target; the main camera's tracking modes,
  section-transfer position selection, distance limits, lateral framing,
  height limits, and smoothing bands; the per-stage record table and which
  fields are read; controller cadence; request mapping and commit order;
  ownership states `0`, `1`, and `-1`; preset families; the stage inputs
  traced below; and the request/variant gates and record sources below.
- **Unresolved or untested:** player-facing names for numeric requests/modes
  and individual effect/move labels; the sign convention of the vertical axis;
  per-stage record fields `+0x10`, `+0x18`, `+0x44`, `+0x58`, and `+0x5C`,
  which have no direct reader in the camera code; whether mode 1's exit has
  an ownership-0 alternative after its request-3 comparison; the visible
  contribution of the mode-18 angle derived from the jutsu-clash side
  counters; and visible behavior.
- **Deliberate exclusions and overlap:** Adventure, cutscene cameras,
  projection/render internals, and unproved player-visible policy were
  excluded. Session and graph ownership are owned by
  [Battle lifecycle](battle_lifecycle.md); stage archives, `ccBgControl`, and
  line nodes by [Stages](../stages/stages.md); pause gating of the camera update by
  [Pause and replay](pause_and_replay.md); the fighter section-transfer fields
  by [Section transfers](../stages/section_transfers.md); the side-indexed pending
  contribution word by
  [Combo accounting](../combat/combo_accounting.md#per-side-accumulated-contribution-route);
  and the jutsu-clash side counters by
  [Match outcomes](battle_statistics.md#jutsu-clash-outcome-selection-and-callback-lifetime).
- **Evidence limitations:** no live camera capture, frame stepping, or request
  injection was performed. Axis roles come from code structure, not from
  observed motion. The direct-call scan does not exclude indirect producers,
  and physical record intervals do not prove script selectability. Some
  enclosing BTL function boundaries remain incomplete.

## Camera classes and activation

Graph field `+0x00` is the `ccCameraCtrl` registry (vtable `0x005DDB40`). Its
nodes are cameras sharing the `ccCamera` base (vtable `0x005DDB10`, base
constructor `0x006D59F0`):

| Class | Vtable | Instances | Class compute (slot `+0x2C`) |
| --- | ---: | --- | ---: |
| `ccCamera01` | `0x005DDBE0` | one `0x1D0`-byte main camera from graph build | `0x006D6AD0` |
| `ccDummyCamera` | `0x005DDB80` | controller slot 0, `0x160` bytes | `0x006DBEA0` |
| `ccPMCCamera` | `0x005DDBB0` | controller slots 1 to 3, `0x250` bytes | `0x006D9290` |

Each camera's `+0x14` points to a Shift-JIS debug name. The main camera is
`基本カメラ` (basic camera); the controller slots are `ダミーカメラ＃０`
(dummy camera #0), `演出カメラ「子」`, `演出カメラ「丑」`, and `演出カメラ「寅」`
(presentation camera Rat, Ox, and Tiger). The session keeps the main camera
at `+0x14`; it is what resident code reaches as the default camera.

Each camera owns a `0x50`-byte engine camera at `+0xA4`, created by
`0x006D5A50(camera, 0x00609160)`, which also stores that resident output
object at `+0xA8` and sets node flag bit 1. Every battle camera uses the same
output object. Byte `+0x60` is the active flag. The registry keeps the current
camera at `+0x10` and the previous one at `+0x14`:

| Helper | Effect |
| --- | --- |
| `0x006D57A0(ctrl, camera)` | Deactivates any member with the same `+0xA8` output object, appends the camera, makes it current, and activates it. Graph build registers `ccCamera01` this way. |
| `0x006D5830(ctrl, camera, keep)` | Makes the camera current and active; deactivates the old current camera unless `keep`. |
| `0x006D5880(ctrl, camera, keep)` | Same, but first copies the old current camera's eye `+0x30`, angles `+0x40`, target `+0x80`, and distance `+0xA0` into the new camera. |

The controller appends its four slot cameras with the plain list append
`0x00709E60`, so they start inactive.

## Common camera update and output

Every camera's phase-1 update is `0x006D5B50`. It calls the class compute
slot `+0x2C`, then `0x006D5C90`, which stores the eye-to-target distance at
`+0xA0` and two wrapped angles at `+0x40/+0x48`. A nonzero compute result
makes the update return 1, so the phase-1 walker removes and destroys that
camera. Otherwise, when the camera is active and has its engine camera and
output object, it calls resident `FUN_0019C290(engine, eye, target)` with
eye = `+0x30` plus the offset vector at `+0x90`, and target = `+0x80`, calls
`FUN_0010E220(output+0x3C word, engine, 0)`, and stores the output object at
resident `0x006073F4`. `FUN_0019C290` forms the
view from `target - eye` and a fixed axis `(0, 0, -1)`, falling back to
`(1, 0, 0)` when the view direction has no component 0 or 1. Thus `+0x30` is the eye, `+0x80` is the look-at
target, and component 2 is the vertical axis; the sign of "up" is not assigned
here.

Only the active camera reaches the output call, so switching the active flag
switches the rendered view. The stage's draw pass temporarily replaces
`0x006073F4` with each background selector group's own view object and
restores `0x00609160` afterward; see
[Battle lifecycle](battle_lifecycle.md#per-update-stage-work). The camera registry runs in phase 1 before the
fighter registry; see [Battle lifecycle](battle_lifecycle.md#per-update-dispatch).

## Main camera

`ccCamera01` is created by graph build (`0x006DDE10` allocation, `0x006D6800`
initialization). The initializer seeds the eye to `(0, -5000, 1500)`, sets
per-update step limits `+0x70/+0x74 = 300`, snap byte `+0x62 = 1`, and binds
its per-stage record through `0x006D69D0(camera, manager+0x98)`: the old
pointer at `+0x194` is saved to `+0x198` and `+0x194` becomes
`*(0x00891E10 + slot * 4)`. Without a manager it uses slot 0. These two
initializer calls are the only callers, so the record is bound once per
session. Byte `+0x61 == 1` or manager `+0x14 == 1` makes the compute return
before tracking, so the camera holds its position.

Each update the compute allocates a working frame, stores both fighters from
camera `+0x20/+0x24`, and copies `ccBgControl` vector `+0x50` into the frame
through `ccField` (`0x00708B60`). No reader of that copied vector was found in
the main camera's routines.

### Tracking target

`0x006D7570` chooses the look-at target by mode `+0x64`:

- mode 0: the midpoint of both fighters' positions; frame `+0xB8` becomes the
  component-1 distance from the midpoint to the fighter with the smaller
  component 1, half their spread;
- mode 1 or 2: the first or second fighter's position, with frame `+0xB8`
  cleared; in these modes sub-mode `+0x164` of 1 or 2 adds `+100` to
  component 0 and `-50` or `-100` to component 2;
- in every mode, byte `+0x162 == 1` averages the target with a third point
  in the frame.

When `+0x164 == 0`, component 0 of the target is clamped to the record's
`+0x34..+0x30` range; a zero bound disables that side. Vtable slot `+0x24`
(`0x006D6A00`) sets `+0x164` from a fighter's state and slot `+0x28` sets
`+0x16C/+0x16E`.

**Section-transfer branch.** Before its ordinary fighter-position reads, the
main compute has an explicit branch for each fighter whose section-transfer
delta `+0x9F0` is nonzero. It uses physical position `+0x30` when physical
component `+4` equals destination component `+0xA24`, and otherwise origin
snapshot `+0xA10`. It stores that position in its frame at `+0x40/+0x50`,
updates saved tracking position `camera+0x1A0/+0x1B0`, clears the
corresponding short `+0x16C/+0x16E`, and adds `0.75` of the scaled fighter
height to the frame's vertical component. The shared resident position
service `FUN_00216320` returns the fighter's eased auxiliary vec4 `+0x2C0`
during a transfer; that easing does not establish that the main camera
follows the eased point. Instruction
bytes at `0x006D6F68..0x006D70F7` and `0x006D7104..0x006D7283` hold both
symmetric branches; `c.eq.s f1,f0` and `bc1f` at `0x006D704C/0x006D7050` and
`0x006D71E8/0x006D71EC` establish exact component equality rather than a
less-than comparison. Neither transfer direction calls the controller's event
or ownership-switch path. The transfer fields are documented in
[Section transfers](../stages/section_transfers.md#request-admission-and-retained-destination).

### Distance, elevation, and framing

`0x006D78C0` sets the engine camera's field of view, from code constants
while byte `+0x160` is clear, and computes a fit distance from the fighters'
positions and that field of view. Frame `+0xB4` receives the larger of the fit
distance and half the frame span `+0x94` divided by the half-angle tangent.
Record `+0x54 == 1.0` zeroes the spread term `+0xB8`.

`0x006D8120` places the eye:

1. When `+0x164 == 0`, it projects both lateral view edges (target component 0
   plus and minus the fit distance times the half-angle tangent) against
   record `+0x38` (upper) and `+0x3C` (lower). When an edge passes its limit,
   the target's component 0 moves a quarter of the overshoot back toward
   zero, never crossing zero. Target component 2 is then capped at `2500`.
2. The distance is `+0xB4 + +0xB8`, clamped to record `+0x28..+0x2C`. Vtable
   slots `+0x1C/+0x20` return these two limits.
3. The eye offset is `-distance` times two trigonometric functions of the
   smoothed elevation angle `+0x174`, on components 1 and 2.
4. With both fighters' `+0x9F6` clear and mode 0, target component 2 rises by
   `(distance - min) * 425 / (max - min) - 0.5 * frame[+0x90] + 8`.
5. The eye becomes target plus offset; when `+0x164 == 0` its component 0 is
   scaled by record `+0x48`. The eye is then placed at the chosen distance
   along the resulting direction, and eye component 2 is capped at record
   `+0x40`.

The target elevation `+0x170` starts each update at zero. In mode 0 it is
reduced by record `+0x4C` when the fighters' `+0x9F6` values differ, or by
`+0x50` when they are equal and nonzero. [Stages](../stages/stages.md) describes
fighter `+0x9F6` as the fighter's stage section, which makes this a
multi-section stage adjustment; the camera code itself only compares the
values. If it is still zero it is derived
from the current eye-target separation divided by the record's distance range
with the constant `-5.0`. Sub-mode `+0x164` forces `-20`. `+0x174` then moves
one eighth of the way toward `+0x170`, or snaps when `+0x62 == 1`.

### Smoothing

`0x006D8820` moves the eye `+0x30` and `0x006D8B30` moves the target `+0x80`
toward the placed values. Each component moves by the difference, clamped to
`±300` (`+0x70` or `+0x74`), times a coefficient (`+0x178` for the eye,
`+0x17C` for the target). Each coefficient normally relaxes one eighth of the
way per update toward a record value chosen by the move; the eye's special
cases assign their value directly:

| Vector | Condition | Record field |
| --- | --- | --- |
| eye | component 1 decreasing | `+0x00`; set to `1.5 * +0x00` when a fighter with `+0x9F0` set has `+0xA24` below the eye's component 1 |
| eye | component 1 increasing, change `≥ 1500` / `≥ 100` / `< 100` | `+0x04` / `+0x08` / `+0x0C`; set to half of `+0x08` when a fighter has `+0x9F0` set |
| target | fighters' `+0x9F6` equal and both `+0x9F0` clear | `+0x14` |
| target | component 1 not increasing, distance `≥ 100` / `≥ 50` / `< 50` | `+0x1C` / `+0x20` / `+0x24` |
| target | component 1 increasing, both `+0x9F0` clear, distance `≥ 1000` / `≥ 50` / `< 50` | `+0x1C` / `+0x20` / `+0x24`; otherwise `+0x14` |

Nonzero floats at camera `+0x68` and `+0x6C` override the eye and target
coefficients. Snap byte `+0x62 == 1` copies the placed values directly.

### Fighter section-transition inputs

The smoothing predicates test fighter section-transfer delta `+0x9F0`, which
is nonzero only during an active transfer, and component 1 `+0xA24` of its
resolved destination vector `+0xA20`; both are documented in
[Section transfers](../stages/section_transfers.md#request-admission-and-retained-destination).
Initialization, cleanup, and interruption clear the delta as described in
[Section transfers](../stages/section_transfers.md#interruption-and-cleanup), which ends
these transfer-specific checks.

## Per-stage camera record

The main camera's per-stage parameters are a `0x60`-byte float record per
raw stage slot. Pointer table `0x00891E10` holds 24 entries; the records are
contiguous at `0x00891510 + slot * 0x60`. Established fields:

| Offset | Use |
| ---: | --- |
| `+0x00..+0x0C` | eye smoothing coefficients |
| `+0x14`, `+0x1C..+0x24` | target smoothing coefficients |
| `+0x28` / `+0x2C` | minimum / maximum camera distance |
| `+0x30` / `+0x34` | upper / lower clamp on target component 0 |
| `+0x38` / `+0x3C` | upper / lower limit for the lateral view edges |
| `+0x40` | upper bound on eye component 2 |
| `+0x48` | factor on eye component 0 |
| `+0x4C` / `+0x50` | elevation reductions for the two fighter-state cases |
| `+0x54` | `1.0` disables the fighters' spread term in the distance |

Fields `+0x10`, `+0x18`, `+0x44`, `+0x58`, and `+0x5C` have no direct reader
in the camera code. Retail values:

| Archives | `+0x00..+0x24` | Distance | Target clamp | Edge limits | Eye cap | `+0x48` | `+0x4C/+0x50` | `+0x54` |
| --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |
| `S01`, `S02`, `S19..S22` | A | 600..4000 | ±1000 | ±1200 | 1500 | 0.8 | 2.5 / 5 | 1.2 |
| `S05` | A | 600..3800 | ±1000 | ±1200 | 1500 | 0.8 | 2.5 / 5 | 1.2 |
| `S06`, `S07` | A | 600..3600 | ±1000 | ±1200 | 1500 | 0.8 | 2.5 / 5 | 1.2 |
| `S08` | A | 600..4000 | ±1000 | ±1000 | 1500 | 0.9 | 2.5 / 5 | 1.2 |
| `S11` | A | 600..4000 | ±1000 | ±1200 | 1500 | 0.8 | 5 / 5 | 1.2 |
| `S12`, `S17`, `S18` | A | 600..3300 | ±1000 | ±1200 | 1500 | 0.8 | 2.5 / 5 | 1.2 |
| `S13` | A | 600..4100 | ±1000 | ±1200 | 1500 | 0.4 | 2.5 / 5 | 1.2 |
| `S03` | B | 600..4000 | ±1200 | ±1300 | 1200 | 1.0 | 10 / 10 | 1.1 |
| `S04` | B | 600..4000 | ±1800 | ±1500 | 2000 | 0.5 | 15 / 10 | 2.0 |
| `S09` | B | 600..4000 | ±1100 | ±1300 | 1200 | 0.6 | 10 / 10 | 1.2 |
| `S10` | B | 800..6000 | ±1300 | ±1600 | 2000 | 0.2 | 5 / 5 | 1.4 |
| `S14` | B | 600..3400 | ±1000 | ±1300 | 1200 | 1.0 | 10 / 10 | 1.2 |
| `S15` | B | 600..4000 | ±1500 | ±1500 | 2000 | 0.8 | 10 / 15 | 1.5 |
| `S16` | B | 600..3600 | ±1100 | ±1300 | 1200 | 0.8 | 10 / 10 | 1.2 |
| `S23` | B | 600..3600 | ±1200 | ±1300 | 1200 | 1.0 | 10 / 10 | 1.0 |
| `S24` | B | 600..4000 | ±1800 | ±1500 | 2000 | 0.5 | 2.5 / 15 | 2.0 |

Coefficient set A is `0.65, 0.3, 0.15, 0.05, 0.03, 0.65, 0.65, 0.15, 0.175,
0.03`; set B is `0.8, 0.4, 0.2, 0.1, 0.05, 0.8, 0.4, 0.2, 0.1, 0.05`. Field
`+0x44` is `200` except `-500` for `S10` and `-200` for `S15`. Record `n` serves
raw load slot `n`, whose archive is `S(n+1)`; see
[Stages](../stages/stages.md#stage-identity-and-resource-mapping).

## Shared controller entry points

The camera controller is a separate `0x68`-byte object that drives the
presentation cameras. BTL accesses it through resident global `0x006077E8`
(`$gp - 0x3208`). Live `0x006DBD60` is an exact publisher:

```text
sw a0,-0x3208(gp)
jr ra
nop
```

An exhaustive aligned-word scan found this as the only BTL store to that GP
offset. Four adjacent entry points establish the public control surface:

| Live address | File offset | Behavior |
| --- | --- | --- |
| `0x006DBD70` | `0x27E70` | Returns true only when a controller exists and ownership state `+0x30` is 1. |
| `0x006DBDA0` | `0x27EA0` | Requests reset through `0x006DC9C0(controller, 1)`. |
| `0x006DBDD0` | `0x27ED0` | Writes the pending controller event at `+0x1C`. |
| `0x006DBDF0` | `0x27EF0` | Writes the side selector at `+0x00` and discriminator at `+0x24`. |

Resident `FUN_001EF330` allocates `0x68` bytes, passes the allocation and the
`ccCameraCtrl` registry to `0x006DBEB0`, stores the returned controller at
session `+0x1C`, and publishes it through `0x006DBD60`. The wrapper runs
`0x006DBF70` followed by `0x006DBFF0`. During `FUN_001EEFD0`, the resident
calls `0x006DBF00(controller, 1)`, clears session `+0x1C`, and then calls
`0x006DBD60(0)`. The two resident calls at `0x001EF47C` and `0x001EF0FC` are
the only direct `jal` sites to the publisher in the retail resident and BTL
files.

The controller update `0x006DC3B0` has one direct caller, resident
`0x001F0484` in `FUN_001F03E0`, which passes session `+0x1C` and skips the
call while manager `+0x14 == 1`. It therefore runs at most once per battle
service update, before any registry callback.

## Address map

| Live address | File offset | Established role |
| --- | --- | --- |
| `0x006D57A0` | `0x218A0` | register and activate a camera |
| `0x006D5830` | `0x21930` | make a camera current |
| `0x006D5880` | `0x21980` | make a camera current, copying the old view |
| `0x006D5B50` | `0x21C50` | common camera phase-1 update and output |
| `0x006D6800` | `0x22900` | `ccCamera01` initializer |
| `0x006D69D0` | `0x22AD0` | bind per-stage record |
| `0x006D6AD0` | `0x22BD0` | `ccCamera01` compute |
| `0x006D7570` | `0x23670` | tracking target |
| `0x006D78C0` | `0x239C0` | field of view and fit distance |
| `0x006D8120` | `0x24220` | eye placement and framing |
| `0x006D8820` | `0x24920` | eye smoothing |
| `0x006D8B30` | `0x24C30` | target smoothing |
| `0x006D8EB0` | `0x24FB0` | clamped per-component step |
| `0x006DBD60` | `0x27E60` | publish/clear the shared controller pointer |
| `0x006DBEB0` | `0x27FB0` | controller construction wrapper |
| `0x006DBF00` | `0x28000` | deleting controller teardown wrapper |
| `0x006DBF70` | `0x28070` | controller state/slot initializer |
| `0x006DBFF0` | `0x280F0` | slot camera construction and registration |
| `0x006DC300` | `0x28400` | remove all non-null camera slots |
| `0x006DC3B0` | `0x284B0` | per-update dispatch and previous-state commit |
| `0x006DC450` | `0x28550` | request-to-mode derivation |
| `0x006DC5C0` | `0x286C0` | pending-event-to-request resolver |
| `0x006DC900` | `0x28A00` | numeric-mode handler dispatch |
| `0x006DC9C0` | `0x28AC0` | reset/return-to-main-camera request |
| `0x006DCA80` | `0x28B80` | active camera ownership switch |
| `0x006DCC40` | `0x28D40` | stage-boundary/segment-side probe |
| `0x006DCDD0` | `0x28ED0` | handlers for modes 4 through 6 |
| `0x006DD130` | `0x29230` | mode-1 preset handler |
| `0x006DD530` | `0x29630` | mode-2 preset handler |
| `0x006DD9E0` | `0x29AE0` | mode-3 preset handler |

## Controller layout

| Offset | Established role |
| --- | --- |
| `+0x00` | side selector; value 1 chooses the first fighter, other values the second |
| `+0x04` | derived camera-mode class |
| `+0x08` | previous derived class |
| `+0x0C` | active preset/variant index |
| `+0x10` | prior or exclusion preset index |
| `+0x14` | current camera request code |
| `+0x18` | previous request code |
| `+0x1C` | pending controller event/state |
| `+0x20` | previous pending event/state |
| `+0x24` | mode discriminator supplied as a skill/effect identifier by the traced producers; initialized to `-1` |
| `+0x28` | enables counter advancement while manager `+0x14 == 0` |
| `+0x2C` | eligible-update counter, otherwise cleared each update |
| `+0x30` | output ownership state: main camera versus presentation camera |
| `+0x34` | number of constructed camera slots |
| `+0x38` | selected camera-slot index |
| `+0x3C` | previous camera-slot index |
| `+0x40..+0x5F` | eight camera-object pointers |
| `+0x60` | the `ccCameraCtrl` registry used to register and remove slot cameras |

The cleanup loop removes every non-null slot through the `+0x60` registry and
then clears that pointer. `0x006DBFF0` constructs exactly four slot cameras:

| Slot | Class | Initialization established statically |
| ---: | --- | --- |
| 0 | `ccDummyCamera` | Eye `(0, 0, -10000)`, target `(0, 0, -11000)`. |
| 1 | `ccPMCCamera` | Anchors `+0x190/+0x194` = fighter 0 / fighter 1 position (fighter `+0x30`); offset vectors with component 2 of 140 and 120. |
| 2 | `ccPMCCamera` | Mirrors slot 1 with the anchors swapped. |
| 3 | `ccPMCCamera` | Configured through `0x006DC370(controller, 3, 0x00891E90, P1 position, P2 position)`, the setup path the mode handlers also use. |

Each construction increments `+0x34`, leaving it at four; slots 4 through 7
remain null. Allocation failure is not handled: the returned pointer is
dereferenced even when the allocator returned zero. In `ccPMCCamera`,
`+0x194` is a fighter-position anchor, unlike `ccCamera01`, where it is the
per-stage record.

## Request-to-mode mapping

When request `+0x14` changes from `+0x18`, the controller derives `+0x04`.
Three negative request codes have direct mappings:

| Request | Derived mode |
| ---: | ---: |
| `-5` | 4 |
| `-6` | 5 |
| `-7` | 6 |

Request 1 asks the selected fighter-side subsystem for a three-valued state:
return 0 maps to mode 2, return 1 maps to mode 1, and return 2 maps to mode 3.
All other requests pass through a discriminator mapper using `+0x24` and
`+0x14`; unrecognized values return `-1` and leave the prior class unchanged.
The numeric classes are established control values, not recovered camera
names.

| Discriminator | Derived mode |
| --- | ---: |
| `0x10` | 8 |
| `0x21` | 9 |
| `0x27` | 10 |
| `0x2C` | 11 |
| `0x89` | 12 |
| `0x34` | 13 |
| `0x39` | 14 |
| `0x2E` | 15 |
| `0x59`, `0x8F`, or `3` | 16 |
| `1`, `0x1C`, `0x6B`, `0x71`, `0x75`, `0x95`, or `0xAB` | 7 |
| other bounded skill/effect ID whose metadata byte `+0x04` is set | 17 |
| request `-4`, independent of discriminator | 18 |

The pending event at `+0x1C` is itself converted to a request by
`0x006DC5C0`. Stable literal mappings are event `2 -> 5`, `6 -> -1`,
`7 -> -4`, `8 -> -5`, `9 -> -6`, and `10 -> -7`. Events 3, 4, and 5 map to
requests 2, 3, and 4 only while at least one fighter-side `+0xB00` field is
nonzero. The eleven-entry jump table at live `0x008C23A0` and its complete
case bodies (`0x006DC610..0x006DC798`) confirm these mappings despite the
incomplete imported switch.

Event 1 first examines both fighters' Extra Hit roles at `+0xB00` (role
ownership is in [Extra Hit](../combat/extra_hit.md#exchange-state-at-fighter-0xb00)).
A nonzero low byte on the first fighter sets controller side to 1; otherwise
a nonzero low byte on the second sets it to 2. If the selected role contains
bit 0, the result is request 1. Otherwise it calls discriminator mapper live
`0x006D9DB0` (`0x006D9DB0..0x006D9F40`): the discriminator sets above return
requests `6..15`, while other signed IDs `0..0xC4` return `-3` and values
outside that bound return 0. This mapper does not name the IDs. Event 1 can
therefore initiate either the Extra Hit camera family or an effect-specific
presentation family.

### Update order, event edges, and automatic requests

The controller update `0x006DC3B0` first calls `0x006DC450`, which invokes the
pending-event resolver and overwrites request `+0x14` only when that resolver
returns nonzero. It then compares the possibly updated request with previous
request `+0x18`; only a change runs the request-to-mode mapping. Next,
`0x006DC900` dispatches the current numeric mode. Only after that handler
returns does the update copy current to previous fields (`+0x04 -> +0x08`,
`+0x0C -> +0x10`, `+0x14 -> +0x18`, `+0x1C -> +0x20`, slot `+0x38 -> +0x3C`)
and clear pending event `+0x1C`. A handler therefore sees the previous
snapshot from the preceding update.

The explicit-event path is edge-gated: pending event `+0x1C` must be nonzero
and differ from previous event `+0x20`. An identical event supplied on
consecutive controller updates is decoded only on the first update. Because an
update with no supplied event commits zero into `+0x20`, the same event code
can be decoded again after at least one zero-event update. That re-arming is a
static inference from the commit order; caller-side timing has not been traced.

When there is no new explicit event, the resolver has two automatic request
paths while ownership `+0x30` is nonzero and the derived mode is 1, 2, or 3:

- if both fighter-side fields at `+0xB00` are zero, it returns request `-1`;
- only in mode 1 with current request 3, it can return request 4 after
  comparing one side-selected fighter's coordinate at `+0x38` with the result
  of resident helper `0x001DC610` applied to that fighter's vector at `+0x30`.
  Controller side value 1 selects the second fighter; other values select the
  first. Fighter `+0x30` is the position vector, so `+0x38` is its component
  2.

Flag `+0x28` and resident predicate `FUN_001F4790(manager, 0)` cause counter
`+0x2C` to increment by exactly one; either condition failing clears it.
The predicate is precisely `manager[+0x14] == requested_value`, so this
counter counts enabled controller updates while manager `+0x14 == 0`.

The reconstructed case table and code establish the request-4 path.
Resident `FUN_001DC610(position, 0x20000000)` queries a component-2 segment
from `position + (0,0,5)` to `position - (0,0,1000)` and returns the hit's
component 2, or the original component 2 when no hit is found. Thus the
automatic request requires a different returned height and a signed height
difference below 300; it does not take the absolute difference.

## Camera ownership switching

`0x006DCA80` compares controller state `+0x30` with the main camera reached
through session `+0x14`:

- state 1: if the selected slot camera is inactive, the main camera is
  deactivated and the slot camera activated; if the slot index changed, the
  slot camera also becomes the registry's current camera through `0x006D5830`.
- state 0: if the main camera is inactive, it is reactivated at once, all
  eight slots are deactivated, and the controller's mode, preset, request, and
  slot fields are cleared.
- state `-1`: if the main camera is inactive, `0x006D5880` makes it current
  after copying the presentation camera's eye, angles, target, and distance
  into it; then the slots and fields are cleared as for state 0.

Only one camera is active at a time. **Inference:** state 0 cuts back to the
main camera's last view, while state `-1` makes the main camera start from
the presentation camera's view and ease back through its own smoothing.

## Preset orientation and non-repetition

Several mode handlers select a short preset ID from table families using the
resident 64-bit LCG wrapper `FUN_0017B798`. They first choose an orientation
from the fighters' relative coordinates or state, reduce the random result
modulo that orientation's candidate count, and add one before indexing. The
chosen short is stored at controller `+0x0C`. If it equals `+0x10`, the
previous preset is cleared to `-1`.

The four overlay-local tables are byte-exact. Each is laid out as two
signed-short candidate counts followed by interleaved candidates for the two
orientations:

| Live address | File offset | Signed-short contents |
| --- | --- | --- |
| `0x00895F40` | `0x1E2040` | `3, 3, 1, 2, 4, 5, 6, 7` |
| `0x00895F50` | `0x1E2050` | `2, 2, 10, 11, 12, 13, 0, 0` |
| `0x00895F60` | `0x1E2060` | `3, 3, 1, 2, 3, 4, 7, 8` |
| `0x00895F70` | `0x1E2070` | `3, 3, 0, 1, 2, 3, 4, 5` |

Pointer families at `0x00895F80`, `0x00895FA0`, and `0x00895FC0` select these
or equivalent resident constant tables according to modes 1 through 4.

### Mode handlers and preset records

Modes 1 through 3 select fixed-size `0xB0` records. Modes 4 through 6 use one
fixed record each:

| Mode | Handler | Record source |
| ---: | --- | --- |
| 1 | `0x006DD130` | `0x00891F40 + preset * 0xB0` |
| 2 | `0x006DD530` | `0x00892990 + preset * 0xB0` |
| 3 | `0x006DD9E0` | `0x008931D0 + preset * 0xB0` |
| 4 | `0x006DCDD0` | fixed `0x008936A0` |
| 5 | `0x006DCDD0` | fixed `0x00893750` |
| 6 | `0x006DCDD0` | fixed `0x00893800` |

`0x006D90A0` applies an `0xB0` record to a `ccPMCCamera`:

| Record offset | Established use |
| --- | --- |
| `+0x00/+0x01` | Enable the two anchor-pointer channels stored at object `+0x190/+0x194`. |
| `+0x02/+0x03` | Choose supplied versus inline initial vectors for the two channels. |
| `+0x04/+0x05` | Enable initial vectors copied to object `+0x170/+0x180`. |
| `+0x06/+0x07` | Enable optional vectors at record `+0x70/+0x80`, copied to object `+0x1A0/+0x1B0`. |
| `+0x08` | Copied to object control byte `+0x161`. |
| `+0x0C` | Copied to object flags `+0x164`. |
| `+0x10/+0x14` | Select which supplied anchor pointer is used when the corresponding channel is enabled. |
| `+0x18..+0x2C` | Six words copied to object `+0x228..+0x23C`. |
| `+0x50/+0x60` | Inline initial homogeneous vectors. |
| `+0x70/+0x80` | Optional homogeneous vectors gated by bytes `+0x06/+0x07`. |
| `+0x90/+0xA0` | Homogeneous vectors always copied to object `+0x1E0/+0x1F0`. |

Modes 7 through 18 have distinct handlers:

| Mode | Live handler | File offset |
| ---: | --- | --- |
| 7 | `0x006DA940` | `0x26A40` |
| 8 | `0x006DAB10` | `0x26C10` |
| 9 | `0x006DB030` | `0x27130` |
| 10 | `0x006DB410` | `0x27510` |
| 11 | `0x006DAC50` | `0x26D50` |
| 12 | `0x006DAED0` | `0x26FD0` |
| 13 | `0x006DB600` | `0x27700` |
| 14 | `0x006DBAF0` | `0x27BF0` |
| 15 | `0x006DB220` | `0x27320` |
| 16 | `0x006DB870` | `0x27970` |
| 17 | `0x006DA060` | `0x26160` |
| 18 | `0x006DA6B0` | `0x267B0` |

Modes 1 through 6 index their records by preset alone, so those records are
shared by every stage. Across the controller and all mode handlers
(`0x006D9F40..0x006DE400`), no code reads manager `+0x98` or the stage
controller global `0x006077E4`; the correction helper `0x006DA270` and the
edge probe reach the stage through `ccField`. Mode 18 also obtains the logical
stage ID indirectly through resident `FUN_00308080()`.

### Numeric request choreography

Modes 1 through 3 act on request changes. A mode change enables controller
counter `+0x28`; request 1 sets main-camera hold byte `+0x61` through live
`0x006DDE50`, and request 2 clears it through `0x006DDE60`, takes ownership
state 1, and resets counter `+0x2C`. Requests 2, 3, and 4 select a new preset
and apply it to the side's slot 1 or 2. Request 4 constructs an inline anchor
at the other fighter's position with component 2 replaced by the
`FUN_001DC610` result. Mode 1 uses this anchor for both channels; mode 2 also
forces slot 2; mode 3 supplies the same other-fighter anchor to both channels
for all three requests. These are distinct request stages, rather than one
camera preset replayed throughout an exchange.

Request `-1` disables the counter and clears main-camera hold. Mode 2 chooses
ownership `-1` only after preset 22 or 23, otherwise 0; mode 3 chooses `-1`.
Mode 1's exit (`0x006DD4A8..0x006DD4F8`) rereads current request `+0x14`
and compares it to 3 after entering the `-1` branch, which assigns ownership
`-1`. This compares the current request, not the previous one; whether the
comparison leads to an ownership-0 alternative is unresolved.

Mode 2 has a paired preset transition: requests 2/3, with previous slot
invalidated, turn previous preset 1 into 9 (`0x00892FC0`) or previous preset
2 into 10 (`0x00893070`) before the ordinary randomized choice. Mode 1's
request 2 forces preset 1/2 for selected fighter native ID 4. These exceptions
are bounded numeric results; their player-facing move names are not assigned.

Modes 4 through 6 choose slot 1. Mode 4 takes ownership on its request edge
and refreshes both inline camera anchors every update from resident
`FUN_00209070/FUN_00209110(fighter[+0xB30])`. Modes 5 and 6 apply their fixed
records only on a request edge: mode 5 anchors to both fighters' `+0xB20`
vectors and writes orientation-dependent endpoint offsets; mode 6 orders the
fighters by byte `+0xB17` and writes eye/target offsets. Those fields belong
to the separate resident `+0xB10` sequence, not the Extra Hit `+0xB00` roles.

The effect-specific handlers have the following complete request/record
partition. `variant` means the active effect object's integer `+0x594`, read
by live `0x007765C0`; it is not a camera frame counter.

| Mode | Entry request | Record base | Continued update |
| ---: | ---: | --- | --- |
| 7 | 6 | `0x00893960` | Apply variant 0 on the request edge. |
| 8 | 7 | `0x008938B0` | Apply variant 0, both anchors at the other fighter's position. |
| 9 | 8 | `0x00893D80` | Reapply when the effect variant changes. |
| 10 | 9 | `0x00894460` | Reapply when the effect variant changes. |
| 11 | 10 | `0x00893B70` | Entry reads the current effect variant; the unchanged-request branch checks request 11 before refreshing a changed variant. |
| 12 | 11 | `0x00893AC0` | Apply variant 0, both anchors from effect anchor channel 1. |
| 13 | 12 | `0x00894720` | Reapply when the effect variant changes. |
| 14 | 13 | `0x008957A0` | Reapply when the effect variant changes. |
| 15 | 14 | `0x008941A0` | Reapply when the effect variant changes. |
| 16 | 15 | `0x00894CA0` | Reapply when the effect variant changes; forces record selectors `+0x10/+0x14` to 1. |
| 17 | `-3` | Effect-supplied pointer | Fetch and apply the effect's camera record on every eligible handler update. |
| 18 | `-4` | `0x00893CD0` | Uses the controller counter and the correction helper after the record's timed threshold. |

The contiguous record block live `0x008938B0..0x00895E80` contains 55
complete `0xB0` records, ending before the camera debug-name strings. The
record bytes establish these physical family intervals and enabled timing
values; they do not by themselves prove every index can be selected by a
shipped effect script. Both channel delays/durations are equal in these records.

| Mode | Physical record indices | Last record | Enabled delay / duration |
| ---: | --- | --- | --- |
| 7 | `0..1` | `0x00893A10` | None. |
| 8 | `0` | `0x008938B0` | None. |
| 9 | `0..5` | `0x008940F0` | `0 / 93` on indices 0/1; other rows have timed bits clear. |
| 10 | `0..3` | `0x00894670` | `0 / 66` on indices 0/1; other rows retain duration 66 with timed bits clear. |
| 11 | `0..1` | `0x00893C20` | None. |
| 12 | `0` | `0x00893AC0` | `0 / 30`. |
| 13 | `0..7` | `0x00894BF0` | `0 / 100` on 0/1; `0 / 10` on 2..7. |
| 14 | `0..9` | `0x00895DD0` | None. |
| 15 | `0..3` | `0x008943B0` | `19 / 7` on 0/1; other rows have timed bits clear. |
| 16 | `0..15` | `0x008956F0` | `10 / 15` on every row. |
| 18 | `0` | `0x00893CD0` | `0 / 20`. |

Modes 7 through 17 select slot 1/2 by controller side. Their matching entry
request resets counter `+0x2C`, takes ownership 1, initializes the preset
index, and clears a matching previous preset to `-1`. Request `-1` disables
the counter, sets ownership to `-1`, and clears discriminator `+0x24`.
Mode 18 always uses slot 1 and invalidates previous slot `+0x3C`.

Mode 17's record accessor live `0x00777710` returns active effect `+0x108`
only while its byte `+0x105` is zero. A null record leaves the existing camera
unchanged. Mode 18 uses system vectors `+0xA80/+0xA90` as its anchors; after
controller counter `+0x2C >= record[+0x18] + record[+0x24]` (20 for its retail
record), it calls live correction helper `0x006DA270`. That helper is the only
direct call target of this name in BTL, at mode-18 call site `0x006DA8D8`.
It derives a signed angle from the difference between two side values read
through `0x007728D0`. That accessor compares the signed shorts at
system `+0xA7A + 2 * side` and `+0xA7A + 2 * (side ^ 1)`, clamps their
difference to `-15..15`, and returns a float bounded to `0..1`
(`0x007728D0..0x007729AC`). Those halfwords are the jutsu-clash side counters
`+0xA7A/+0xA7C` that the clash driver increments, documented in
[Match outcomes](battle_statistics.md#jutsu-clash-outcome-selection-and-callback-lifetime).
The correction moves controller float `+0x64` toward its angle through
`FUN_001808F0(..., 0x40)`, and suppresses a negative angle for active effect
IDs `0x30/0x69`. The complete continuation establishes that the helper resolves
a point within the selected fighter's current stage section, uses the resolved
component 1 for a segment test, and either rotates the record eye endpoint or
uses it without rotation when blocked. It publishes the angle back to
controller `+0x64` and the corrected offset to camera `+0x1A0`.

The mode-18 caller then restores its local copy of record `+0x90` to camera
`+0x1A0`, adding 80 to component 2 only when resident `FUN_00308080()` returns
logical stage ID 5 (`0x006DA898..0x006DA91C`). That resident accessor calls the
raw-slot mapper live `0x006C14E0` on manager `+0x98`; ID 5 corresponds to load
slot 4, as recorded in [Stages](../stages/stages.md#stage-identity-and-resource-mapping).
Thus the helper's camera-offset store is overwritten in this caller, while
its controller-angle store persists. The angle's visible contribution cannot
be inferred from its internal store alone.

Live adapter `0x006DC370` applies a record to the chosen slot via
`0x006D90A0`. Modes 7, 10, 11, 13, 14, 15, and 16 first pass their base and
variant to `0x00776610`: it can substitute another `0xB0` record after
querying effect virtual slots `+0x34/+0x38` (anchors), `+0x3C/+0x40`
(orientation/variant), and `+0x44/+0x48` (substitution tables), then testing a
stage segment from an anchor raised by 75 along component 2 toward the
record's component-0 offset. Modes 7, 11, 13, and 14 also choose their two
supplied anchors from effect channels according to record `+0x10/+0x14`.
This is a record-adaptation path before camera initialization, not a direct
per-stage camera-record lookup.

### Stage-edge correction

The boundary probe `0x006DCC40` reads the stage bounds from `ccBgControl`
`+0x20/+0x30` through `ccField` (`0x00708F60`). Those vectors are derived from
the archive's `DMY_linemin01/02` and `DMY_linemax01/02` nodes; see
[Stages](../stages/stages.md#line-construction). The probe tests the proposed side
against component 0 of those bounds and, when still ambiguous, performs two
resident segment queries (`FUN_001BF100`) from a point 75 units along
component 2 from the subject. It returns side code 1 or 2 when one direction
is blocked. Camera handlers then force candidate 1 on the corresponding side
instead of using the random result. Screen-left/right labels depend on stage
orientation and are not assigned here.

### Presentation-camera smoothing

The two anchor channels have independent integer counters: eye `+0x240` and
target `+0x244`. Record `+0x18/+0x1C` becomes their delay at object
`+0x228/+0x22C`; record `+0x24/+0x28` becomes duration at
`+0x234/+0x238`. Flag bits `0x08/0x10` enable their timed offset movers.
Initialization live `0x006D9360` clears the corresponding counter and
computes a displacement from initial offset `+0x1A0/+0x1B0` to endpoint
`+0x1E0/+0x1F0`, divided by `max(duration - 4, 1)`.

The complete raw offset bodies live `0x006D9510..0x006D9610` (eye) and
`0x006D9610..0x006D9710` (target) move only when
`delay < counter < delay + duration`. With `remaining = delay + duration -
counter`, their displacement multiplier is `0.25` when `remaining < 2` or
`remaining >= duration - 1`, `0.5` when `remaining == 2` or
`remaining == duration - 2`, and 1 otherwise. Exactly at `counter == delay +
duration` they copy the endpoint. Every invocation then increments its
counter by one, including delayed and already-completed invocations. These
are update counts, with no conversion to elapsed seconds in the scoped code.

Eye/target goal builders `0x006D9710/0x006D97B0` retain an initial anchor
snapshot while a nonzero delay has not expired (`counter <= delay`), then
read the live anchor each update; delay 0 reads it immediately. Inline
initial anchors and their one-shot snapshot bytes have the same channel
ownership. Goal construction invokes the enabled offset mover before final
eye/target smoothing. The movement gate below therefore gates both channel
counters as well as the smoothed vectors.

`ccPMCCamera` compute `0x006D9290` uses eye mover `0x006D9850`
(`0x006D9850..0x006D9A00`) and target mover `0x006D9A00`
(`0x006D9A00..0x006D9BB0`). The eye goal adds object offset `+0x1A0` to
working vector `+0x00`; the target goal adds `+0x1B0` to working vector
`+0x10`. Byte `+0x161 == 1` copies both goals directly. Otherwise each
component advances by `clamp(goal - current, -300, 300) * coefficient`,
where the eye coefficient is `0.125` and target coefficient is `0.25`.
Consequently the maximum component displacement is `37.5` for the eye and
`75` for the target per eligible update; `300` bounds the difference before
scaling.

The raw compute instructions (`0x006D9290..0x006D935C`) establish the order:
if byte `+0x160` is nonzero, run the initialization helper `0x006D9360` first;
then call resident `FUN_001F4790(owner, 1)`. Return value 1 skips the working
vector construction, both movers, and clearing of `+0x160`. Otherwise the
compute builds the two goals through `0x006D97B0` and `0x006D9710`, moves eye
then target, restores its `0x20`-byte working-frame allocation, and clears
`+0x160`. Initialization therefore precedes this movement gate and can be
repeated while the gate remains set. This predicate is distinct from the
controller counter's call with argument 0: it tests manager `+0x14 == 1`,
whereas the counter requires `+0x14 == 0`. Registry scheduling gates remain
with [Pause and replay](pause_and_replay.md).

Record application sets byte `+0x160 = 1` at live `0x006D9278`, requesting
initialization on the next compute. Thus a non-null record repeatedly applied
by mode 17 restarts enabled channel counters before each eligible movement
update. This is a static consequence of the handler and compute order; it
does not establish which timed records retail effects supply through that path.

## Stage- and event-driven inputs

The camera consumes these inputs:

- **Per-stage:** the main camera's record, selected once per session by the
  raw slot at manager `+0x98`; the `ccBgControl` bounds `+0x20/+0x30` read by
  the presentation-camera edge probe; the stage-section point resolver used
  by mode-18 correction helper `0x006DA270`; segment tests used by that helper,
  automatic request 4, and effect-record adaptation; and mode 18's 80-unit
  height bias for logical stage ID 5. [Collision](../combat/collision.md) owns the
  query contracts; [Stages](../stages/stages.md) owns the archive bounds and line data.
- **Events and requests:** the controller's pending event `0x006DBDD0` has
  26 aligned direct call sites in the retail resident and BTL programs (11
  resident, 15 BTL). The producer families and gates are recorded below.
- **Consumers of camera state:** `0x006DBD70` is queried by resident
  `FUN_003AE660`. When that predicate (which also tests other battle states)
  is true, `ccBgControl`'s phase-1 update turns off background scene selectors
  2 and `0x30` once and restores them when it becomes false. Other callers are
  `0x006BA614`, `0x0024A09C`, `0x0024D77C`, `0x00305B24`, and `0x00376A68`.
  The on/off reading of the scene routine `FUN_003ACF20`'s last argument
  (0 on entry, 1 on exit) is an inference.

### Action and effect producers

The table covers every direct `jal 0x006DBDD0` caller family, counting
resident mirrored address aliases once. The skill vtables that hold the BTL
callbacks reside in the resident ELF. Native class names identify retail code
families; they are not translated move names.

| Producer | Live call sites | Event and local gate |
| --- | --- | --- |
| Resident Extra Hit phase helper `FUN_00242B30`, called by `FUN_00243040` and the continuation containing `0x002439AC` | `0x00242BCC`, `0x00242C0C`, `0x00242C40`, `0x00242CE8`, `0x00242E24`, `0x00242E90`, `0x00242F18`, `0x00243024` | Phase `+0x194`: 0 emits 1; 1 emits 2; 2 emits 3; 6 emits 4. Phase counter `+0x196` is 0 except event 3's exchange-count-scaled branch. |
| Resident sequence `FUN_00247090` | `0x00247288` | Event 8 when incremented signed counter `+0xB12 == 0` and fighter side bit is clear. |
| Resident sequence `FUN_002466D0` | `0x00246788` | Event 9 on entry, with side bit clear; `FUN_00247090` reaches this entry when `+0xB12 == 0x4C`. |
| Resident sequence `FUN_00247490` | `0x00247840` | Event 10 while `+0xB10 == 5`, fighter `+0x192 != 5`, and incremented `+0xB14 > 3`; this can repeat on successive updates. |
| BTL shared skill callbacks `0x00794B00/0x00794BC0` | `0x00794B3C`, `0x00794C08`, `0x00794C2C` | Entry emits 1; exit emits 6 unless metadata byte `+1 == 1`, which requests reset instead. |
| `ccSkillHAK000`, vtable `0x005F9800`, callbacks `0x007A9D10/0x007A9DD0` | `0x007A9D4C`, `0x007A9E18`, `0x007A9E3C` | Same entry/exit contract as the shared callbacks. |
| `ccSkillFIR000`, vtable `0x005F2C20` | `0x007D7C88`, `0x007D810C` | Entry emits 1 with discriminator 1 when its scene predicate succeeds; exit emits 6 after the side-indexed pending contribution word `+0x3268` ([Combo accounting](../combat/combo_accounting.md#per-side-accumulated-contribution-route)) is `<= 0`, byte `+0x389 == 0`, and byte `+0x539 == 0`. |
| Five overridden skill exit callbacks, classes below | `0x007FCF40`, `0x007FF500`, `0x00802110`, `0x00806660`, `0x0080F3D0` | When object `+0x590` is nonzero, reset first, then emit 6. |
| BTL system presentation setup/exit paths | `0x0077AA34`, `0x0077BA64` | Setup emits 7 after publishing its `+0xA80` anchor; exit emits 6 after any conditional child callback. The enclosing imported function boundaries are incomplete. |

In `FUN_00242B30`, exchange count `+0xB08 == 1` emits event 3 at phase-2
counter 0. Other counts use `scale = max(0.01, 1 - (count - 1) * 0.25)` and
emit it when the phase counter equals integer conversion of `scale * 5`.
The phase updater calls this producer before advancing/resetting its counter,
so the entry gates read the current phase snapshot. Extra Hit role and action
ownership remain in [Hit response](../combat/hit_response.md).

The shared entry callback has 163 literal vtable references in resident
`0x005E0B18..0x005FB6E8`; for example `ccSkillKBW001` vtable `0x005E0900`
stores entry/exit at `+0x218/+0x21C`. Entry writes side
`object[+0x350] == 0 ? 1 : 2` and discriminator `object[+0x56C]` through
`0x006DBDF0`, emits event 1, then sets byte `+0x590` to 1. Exit checks and
clears that byte before consulting the metadata record, preventing a second
exit from emitting another event through this shared callback. The HAK
override follows the same order. FIR's selector call at `0x007D7C7C` instead
supplies side `object[+0x350] + 1` and literal discriminator 1. These establish
the discriminator as a skill/effect identifier in these producer paths.

The five reset-and-event-6 exit overrides resolve through their resident
vtable `+0x21C` and BTL RTTI as follows:

| Class | Vtable | Exit callback |
| --- | --- | --- |
| `ccSkillKBT001` | `0x005EC1D0` | `0x007FCF20` |
| `ccSkillSIN000` | `0x005EBF80` | `0x007FF4E0` |
| `ccSkillTND001` | `0x005EBD30` | `0x008020F0` |
| `ccSkillFOR000` | `0x005EB890` | `0x00806640` |
| `ccSkillANB000` | `0x005EB610` | `0x0080F3B0` |

Reset helper `0x006DBDA0` has twelve direct sites: four resident sites
`0x0024408C`, `0x00246E34`, `0x00246EB0`, `0x00247CA8`, and eight BTL sites
`0x00794C18`, `0x007A9E28`, `0x007DDB8C`, `0x007FCF34`, `0x007FF4F4`,
`0x00802104`, `0x00806654`, `0x0080F3C4`. The resident sites accompany Extra
Hit teardown or the `+0xB10` sequence's termination; the separate BTL routine
`0x007DDB50` clears object `+0x590` before requesting reset. These reset calls
do not identify additional event producers.

This is a complete inventory of the scoped aligned direct-call encodings and
their local gates, not proof that every authored action reaches one of them.
The 163 inherited callbacks still require action/asset ownership to assign
individual player-facing labels, and indirect calls are not excluded by this
scan. Effect and action execution are owned by
[Combat action execution](../combat/combat_action_execution.md) and
[Effect-generator commands](../../runtime/effect_generator_commands.md).

### Camera-named resources

The camera-named resources in BTL are not camera-controller inputs.
`ANM_bg_camera`, `CAM_%s_camera1`, and `CAM_%s_camera2` are read through GP
slots only by the cut-in initializer at `0x0086F460..0x0086F5A8`, alongside
`battlegauge.ccs`; `CAM_camera01` is referenced only by the battle-sequence
child at `0x0076D0E8/0x0076D4E8`. The formatted per-character names
`ANM_%c%c%c_camera`, `%d_camera`, `OBJ_%c%c%c%d_camera`, and
`OBJ_%c%c%c_camera` are built by BTL code at `0x00796F0C..0x007971BC`. The
fixed `OBJ_camera*` names are referenced only from resident data tables at
`0x00604F2C..0x00605460`.
