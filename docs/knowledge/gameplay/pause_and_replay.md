# Pause, start-menu, and battle-restart control

This document records the established resident/BTL control paths related to
battle pause suppression, the battle start menu, and battle reconstruction.

The result is primarily static reverse engineering. No runtime pause or replay
experiment was performed for this investigation. Numeric states and command
IDs remain numeric unless their effect is directly established; names below
are descriptive working identities, not recovered original symbols.

## Research coverage

- **Assigned scope:** resident/BTL battle pause and replay control: pause
controller ownership and states, the simulation/update paths affected by its
masks, start-menu/result routing, and any provable battle replay, restart, or
reconstruction lifecycle. The investigation stayed within the exact resident
and BTL binaries identified below and their maintained read-only exports.

- **Exploration depth:** coverage was deep but bounded rather than exhaustive across the game:

- The resident running-session chain was traced from `FUN_001EF8F0` through
  mask construction `FUN_001F0290`, the complete explicit bit-dispatch table in
  `FUN_001F03E0`, countdown/update calls `FUN_001F10F0` and `FUN_001F0B10`,
  owner construction/destruction, and the relevant controller states `11..25`.
  This included the route-`6`, route-`7`, and route-`8` teardown or
  reconstruction paths and the direct producers that reach them.
- The BTL pause-controller lifecycle and selected child branches were followed
  through encoded live constructor/update/destructor targets, selectors `0`,
  `1`, and `13`, their resource identities, and the direct parent-mask writes
  made by selectors `1` and `13`. The auxiliary object at `0x00607844` was
  followed through allocation, destruction, and the cut-in-related `+0xA50`
  writer/reset range from live `0x0086F2E0` through `0x00870B38`.
- The primary scheduler array built at live `0x007092E0` was resolved through
  constructors, vtables, RTTI, and callback slots. Every explicit bit test and
  direct call in `FUN_001F03E0` was tabulated; targeted RTTI/resource work
  identified bits `0..4` and the countdown-presentation half of bit `9`.
  Semantics for the remaining fixed consumers were sampled only far enough to
  avoid unsupported names.
- The start-menu chain was traced from resident `FUN_001EBD90` through BTL live
  construction/update/result range `0x0087B0D0..0x0087D940`, its command-list
  tables, command factory, child-result propagation, and exact Shift-JIS prompt
  fragments for commands `0xA`, `0xB`, and `0xE`.
- Complete direct-pattern scans within the two exact binaries covered immediate
  route-`8` stores, direct constant-offset stores to auxiliary `+0xA50`, and
  direct stores to controller `+0x694`. These exhaustive claims apply only to
  those direct instruction patterns in these binaries; indirect writes,
  dynamically selected calls, and other overlays remain outside them.
- Replay coverage was a bounded search of resident/BTL literals, exports, and
  the traced teardown/reconstruction call paths. It found no proven capture
  buffer, recorded-input playback, serialized battle snapshot, or explicit
  random-state restore. This is a useful negative, not exhaustive proof of
  absence.

- **Confirmed coverage:** resident ownership of the pause
controller, persistence and direct producers of its two suppression words, the
selective three-phase scheduler and its exceptions, the separate aggregate
countdown gate, start-menu command/result-to-route flow, owner destruction and
recreation during restart-like paths, the two bounded route-`8` reconstruction
producers, and the lack of a proven replay mechanism in the inspected paths.

- **Unresolved or untested:** indirect or other-overlay suppression writers; exact
visible phase names for several selector branches and the cut-in flag; semantic
identities for the remaining fixed scheduler consumers; remaining menu labels
and input-to-result mapping; the user-facing events behind route-`8` modes `1`
and `2`; and replay mechanisms outside the bounded paths.
- **Deliberate exclusions and overlap:** controller-input polling, frame-rate patch design, practice configuration,
match-result interpretation, non-gameplay media, and all story-mode logic.
Those neighboring areas were neither used to fill gaps nor documented as
evidence.

- **Evidence limitations:** validation is static except for the clean-savestate/loader proof of the BTL
`MWo3` header convention. No runtime pause, menu-selection, reconstruction, or
replay experiment was run, so visible timing, exact input mapping, and dynamic
reachability remain unverified. Raw-file disassembly was used to audit encoded
targets and the `+0x40` overlay-address correction; the maintained disassembly
itself was not modified.

## Evidence identity and address conventions

The clean resident and BTL inputs and their address conversions are defined in
[Standard game file identities](../game/files/file_identities.md).

Encoded absolute pointers and `j`/`jal` targets in the raw overlay already use
live addresses. They must not receive another `+0x40`; instead, their physical
target bytes appear at `encoded live target - 0x40` in the preserved export.
This explains several misleading intra-overlay callee labels in the export.
The retained-header rule is runtime/loader evidence from a clean savestate;
unless a passage below says otherwise, the controller and state-machine facts
are direct static facts from the two identified binaries. Interpretive labels
are explicitly described as inferences.

## Resident pause-controller consumption

The resident battle-session update is rooted at `FUN_001EF8F0` (resident/live
`0x001EF8F0`, ELF file `0x0EF9F0`). When its preceding state dispatcher returns
zero, it calls, in order:

1. `FUN_001F0290` to construct two allowed-update masks;
2. `FUN_001F03E0` to dispatch masked battle-system update phases;
3. `FUN_001F10F0`;
4. `FUN_001F0B10`.

### Controller fields and mask construction

`FUN_001F0290` (resident/live `0x001F0290`, ELF file `0x0F0390`) reads the
object pointer at resident global `0x00607834`. When it is non-null, the
function begins with its `u16` fields `+0x12` and `+0x14`, passes pointers to
both temporary values to encoded live BTL target `0x007729E0`, applies
session-local overrides, and stores the bitwise complements at session fields
`+0x02` and `+0x04`.

Raw disassembly narrows the BTL target's effect. It ignores the second pointer,
reads another object pointer from resident global `0x00607844`, and tests byte
`object+0xA50`. Only when that byte equals `1` does it force the first
temporary suppression value to `0xFFFF`; otherwise it changes neither value.
The target's physical bytes are at preserved export `0x007729A0`, raw file
`0x000BEAE0`. The object's ownership and direct `+0xA50` writers are established
below, but its semantic class identity is not.

The direct static facts are therefore:

- controller `+0x12` contributes to the first/third-phase mask;
- controller `+0x14` contributes to the second-phase mask;
- session `+0x02/+0x04` are the final allowed-update masks;
- any nonzero pre-complement value also sets bit 0 of resident byte
  `0x006B28D0`.

Calling `+0x12/+0x14` **suppression bitsets** is a high-confidence inference
from that final complement, not a recovered type name. The BTL target's
one-sided write also proves it cannot directly contribute any bits to the
second suppression word.

The manager pointer at `0x00607600` supplies another numeric gate.
`FUN_001F4790` (resident/live `0x001F4790`, ELF file `0x0F4890`) is exactly
`manager->field_14 == requested_value`. When that field equals `1`,
`FUN_001F0290` forces the first suppression word to `0xFFFF`, rather than
deriving it solely from the controller.

### Auxiliary BTL global and the `+0xA50` override

The object at `0x00607844` is a separately BTL-owned `0x3330`-byte global
system, although its semantic class name is not recovered. During resident
session setup, `FUN_001EF330` calls `FUN_00309090(1)`, which reaches live BTL
allocator/publisher `0x00776AD0`. That function allocates `0x3330` bytes, calls
live constructor `0x00777130`, and publishes the result at `0x00607844`.
Resident teardown `FUN_001EEFD0` calls `FUN_00309110`, which reaches live BTL
destructor wrapper `0x00776B20` and clears the global.

| Operation | Raw file | Preserved export | Live |
| --- | ---: | ---: | ---: |
| Allocate/publish global | `0x000C2BD0` | `0x00776A90` | `0x00776AD0` |
| Construct object | `0x000C3230` | `0x007770F0` | `0x00777130` |
| Destroy/clear global | `0x000C2C20` | `0x00776AE0` | `0x00776B20` |

Its byte `+0xA50` has exact direct producers in BTL. Live setup function
`0x0077E460` clears it. Live store `0x0086FE6C` sets it to `1`; live stores
`0x0086FFE4`, `0x00870644`, and `0x00870B38` clear it again. No other direct
constant-offset byte store to `+0xA50` was found in a complete raw BTL
disassembly scan.

The writer chain ties this transient state to a cut-in presentation
subcontroller. Unconditional auxiliary-object update `0x00778D90` iterates two
side records; after its predicate succeeds, it calls live `0x0086FCD0`
(preserved export `0x0086FC90`, raw file `0x001BBDD0`) on the subobject at
auxiliary-object `+0x210`. That routine validates the supplied three-word
record against one of the auxiliary object's two records, stages it in the
corresponding side slot, ensures a presentation-effect object exists, and then
sets `+0xA50 = 1` at live `0x0086FE6C`.

The subobject initializer at encoded live `0x0086F2E0` directly references
the BTL data literals `1%scutin.ccs` (raw `0x001FA588`, preserved export
`0x008AE448`, live `0x008AE488`) and `ANM_1%s_cutin` (raw `0x002074F8`,
preserved export `0x008BB3B8`, live `0x008BB3F8`), as well as
`battlegauge.ccs`. Reset entry `0x0086FEA0` clears the byte at `0x0086FFE4`;
the other two clears occur when the paired side-state machine advances to its
next overall state (`0x00870644`) and when both side slots are inactive
(`0x00870B38`). Calling the byte a **cut-in presentation active/staged flag** is
therefore a high-confidence functional inference from direct resource and
state-machine evidence, not a recovered field name. The exact visible phase it
covers, and whether every cut-in uses it, remain unproven.

When the byte is `1`, it independently forces the first allowed mask to zero,
enables primary-array pointer `1`'s first callback despite cleared bit `1`, and
skips the two live `0x00870230` calls. These effects are direct; describing the
byte itself as a secondary pause flag would be an inference.

### Proven BTL suppression writers

Two controller-child branches directly write the parent controller's
`+0x12/+0x14` fields:

| Selector at controller `+0x0D` | Live child update | Proven parent-field writes |
| ---: | ---: | --- |
| `1` | `0x0076CC00` | `0x0076CDB4/0x0076CDB8` and `0x0076D7B4/0x0076D7B8` each store `0xFFFF/0xFFFF` |
| `13` | `0x00769790` | `0x00769E7C/0x00769E80` store `0x0110/0x0110`; `0x0076A338..0x0076A364` forces the first word to `0xFBFF` and applies `(old \| 0x0200) & 0xFBFF` to the second; `0x0076A440..0x0076A460` stores `0xFBFF/0xFBFF` |

For selector `13`, the middle operation yields `0xFBFF/0x0310` along the
traced path that previously stored `0x0110/0x0110`. The operations themselves,
rather than that prior-value-dependent result, are the general static fact.
The selector-`1` function's physical bytes begin at preserved export
`0x0076CBC0`, raw file `0x000B8D00`; selector `13` begins at preserved export
`0x00769750`, raw file `0x000B5890`.

These parent-controller fields persist across frames; `FUN_001F0290` copies
them but does not clear them. Selector `1` therefore reasserts full suppression
at two transitions, while selector `13` progresses through the three patterns
shown above. The common controller cleanup is the proven eventual clear of
both words. A bounded review of the selector-`0` child branch found nearby
child-local halfword writes but no write through the saved parent pointer to
`+0x12/+0x14`. That is a useful negative for this branch, not proof that no
indirect producer can affect it elsewhere.

Before the resident session-local overrides and the separate `+0xA50`/manager
force-to-`0xFFFF` cases, the bitwise complement gives these controller-only
allowed-mask contributions:

| Controller suppression `+0x12/+0x14` | Allowed first/third and second masks |
| --- | --- |
| `0xFFFF/0xFFFF` | `0x0000/0x0000` |
| `0x0110/0x0110` | `0xFEEF/0xFEEF` |
| `0xFBFF/0x0310` | `0x0400/0xFCEF` |
| `0xFBFF/0xFBFF` | `0x0400/0x0400` |

The resident overrides OR additional suppression bits before complementing,
so they can only narrow these allowed masks. During an active start menu,
manager `+0x14 == 1` forces the first/third allowed mask to exactly `0x0000`
regardless of the controller value; it does not itself force the second mask.

### Selective update gating

`FUN_001F03E0` (resident/live `0x001F03E0`, ELF file `0x0F04E0`) consumes the
allowed masks in three phases:

| Phase | Mask | Dispatch |
| --- | --- | --- |
| First | session `+0x02` | object virtual slot `+0x0C` and fixed subsystem updates |
| Second | session `+0x04` | object virtual slot `+0x10` and fixed subsystem updates |
| Third | session `+0x02` | object virtual slot `+0x14` and fixed subsystem updates |

The four primary pointers are reached through the array at session `+0x18`.
Each object's callback table is at object `+0x0C`; the three phases invoke
table slots `+0x0C`, `+0x10`, and `+0x14`. Their construction and RTTI make
their identities concrete:

| Array index / bit | Allocation and constructor | Vtable | RTTI identity | Live callback targets `+0x0C/+0x10/+0x14` |
| --- | --- | ---: | --- | --- |
| `0` / bit `0` | `0x18` bytes, live BTL `0x006D5640` | `0x005DDB40` | `ccCameraCtrl` | `0x006D59D0 / 0x006D67A0 / 0x006D67C0` |
| `1` / bit `1` | `0x10` bytes, live BTL `0x006F0F90` | `0x005DDD10` | `ccCommandCtrl` | `0x006D67E0 / 0x006D67A0 / 0x006D67C0` |
| `2` / bit `2` | `0x34` bytes, resident `0x0024E0B0` | `0x005D9FC0` | `ccPlayerCtrl` | `0x002504B0 / 0x00250690 / 0x00250800` |
| `3` / bit `4` | `0x10` bytes, live BTL `0x00709150` | `0x005DDD60` | `ccFieldCtrl` | `0x006D67E0 / 0x006D67A0 / 0x006D67C0` |

Live BTL builder `0x007092E0`, called by the `0x10`-byte array owner created
at live `0x00709240`, constructs those four roots in that order. The vtable
type-descriptor chains point respectively to exact strings `ccCameraCtrl`,
`ccCommandCtrl`, `ccPlayerCtrl`, and `ccFieldCtrl`; these are recovered binary
identities rather than descriptive names. Encoded vtable pointers are already
live addresses. For the BTL constructors and callbacks above, physical
preserved-export bytes are `0x40` lower.

The exact allowed-bit consumers are:

| Bit | First phase, mask `+0x02` | Second phase, mask `+0x04` | Third phase, mask `+0x02` |
| ---: | --- | --- | --- |
| `0` (`0x001`) | `ccCameraCtrl` slot `+0x0C` | `ccCameraCtrl` slot `+0x10` | `ccCameraCtrl` slot `+0x14` |
| `1` (`0x002`) | `ccCommandCtrl` slot `+0x0C` | `ccCommandCtrl` slot `+0x10` | `ccCommandCtrl` slot `+0x14` |
| `2` (`0x004`) | `ccPlayerCtrl` slot `+0x0C` | `ccPlayerCtrl` slot `+0x10` | `ccPlayerCtrl` slot `+0x14` |
| `3` (`0x008`) | `ccBuddyAtkCtrl` wrapper, live BTL `0x00885400` | same singleton, live BTL `0x00885430` | same singleton, live BTL `0x00885460` |
| `4` (`0x010`) | `ccFieldCtrl` slot `+0x0C` | `ccFieldCtrl` slot `+0x10` | `ccFieldCtrl` slot `+0x14` |
| `5` (`0x020`) | live BTL `0x00734BA0` if global `0x00607820` is non-null | live BTL `0x00734D30` under the same condition | none |
| `6` (`0x040`) | live BTL `0x0077CE40` if global `0x00607844` is non-null | live BTL `0x00779020` under the same condition | live BTL `0x00779050` under the same condition |
| `7` (`0x080`) | set resident `0x0061AFD1 = 1`, call `FUN_00309190`; otherwise clear the byte | set resident `0x0061AFD2 = 1`, call `FUN_003091E0`; otherwise clear the byte | `FUN_00309270` |
| `8` (`0x100`) | `FUN_003747C0(session+0x20 object)` | `FUN_00374D90(session+0x20 object)` | none |
| `9` (`0x200`) | live BTL `0x0087EB40(session+0x2C countdown-presentation object)` and `0x006B48E0(session+0x30 object)` | live BTL `0x0087EDD0(session+0x2C countdown-presentation object)` and `0x006B4A10(session+0x30 object)` | none |
| `10` (`0x400`) | `FUN_0036BF10(0)` when `FUN_0036B6C0` succeeds | `FUN_0036BFF0(0)` under the same condition | none |

For each non-null object at session `+0x24/+0x28`, either bit `9` or bit `10`
(`mask & 0x600`) also enables live BTL `0x0071AF30` in the first phase and
`0x0071B2E0` in the second. The exact masks therefore suppress selected
consumers; they are not one global `if (paused) skip frame` switch. Live BTL
addresses in this table follow the `+0x40` convention above.

Bit `3`'s identity is direct RTTI evidence. Live BTL publisher `0x00885210`
allocates `0x24` bytes, calls live constructor `0x00886CB0`, and stores the
object at resident global `0x00607888`. Its vtable type descriptor resolves to
the exact string `ccBuddyAtkCtrl`; the three bit-`3` wrappers call that
singleton's first, second, and third update functions. This name is recovered
from the binary, not inferred from behavior.

Manager field `+0x14 == 1` is exceptional: `ccCameraCtrl` first and third
phases still run even if allowed-mask bit 0 is clear. Its second phase receives
no equivalent exception. `ccCommandCtrl` has a different first-only exception:
byte `+0xA50 == 1` on the object at `0x00607844` enables its first callback even
if bit 1 is clear.

Several operations remain outside the masks. Among them are encoded live BTL
targets `0x00706420`, `0x00706450`, and `0x00706480`, controller pre/post work,
and resident `FUN_001DE1C0`. When manager field `+0x14 != 1`, the dispatcher
calls controller pre-work at encoded live BTL `0x0076EF90`; after first-phase
dispatch it calls controller post-work at encoded live BTL `0x0076F020`
whenever `0x00607834` is non-null. Their physical preserved-export addresses
are respectively `0x0076EF50` and `0x0076EFE0`.

Other unconditional or separately conditioned work around the masks is also
explicit: live BTL `0x006DC3B0` runs only when session `+0x1C` is non-null and
manager `+0x14 != 1`; live `0x00778D90` runs whenever `0x00607844` is non-null;
live `0x00778FF0` additionally requires manager `+0x14 != 1`; and live
`0x00870230` runs twice when that object's byte `+0xA50 == 0`. These are not
controlled by an allowed-mask bit.

Consequently, an active start menu does not stop all work: its zero
first/third mask still leaves the primary first/third callbacks enabled by the
manager exception, may leave pointer `1`'s first callback enabled by its own
exception, leaves the independently constructed second phase in force, and
continues all unconditional work listed above. The two later resident calls
`FUN_001F10F0` and `FUN_001F0B10` also occur after the mask dispatcher whenever
the enclosing session path remains in its running state; they are not direct
consumers of either allowed mask. The countdown update reached by the first
call nevertheless shares an aggregate pause flag produced during mask
construction, as detailed next.

This proves a selective pause-aware scheduler. It does **not** prove the
gameplay role of every gated subsystem or exclude additional indirect
suppression producers.

### Battle-countdown gate and presentation

The timer-shaped resident structure beginning at `0x006B28D0` supplies a second
kind of pause gate outside the per-bit scheduler. `FUN_001F0290` sets bit `0` of
its flags byte when either pre-complement suppression word is nonzero and clears
the bit only when both are zero. Later in the same session update,
`FUN_001F10F0` (resident/live `0x001F10F0`, ELF file `0x0F11F0`) conditionally
calls `FUN_001EBA80` (resident/live `0x001EBA80`, ELF file `0x0EBB80`) on that
structure. The latter routine does not decrement while flags bit `0` is set.
When bit `0` is clear and its separate non-decrement flag is also clear, it
subtracts structure `+0x1C` from the fixed-point value at `+0x04`, adds the same
amount to `+0x08`, and clamps expiration while setting flags bit `2`.

Initialization in `FUN_001EEE30` (resident/live `0x001EEE30`, ELF file
`0x0EEF30`) loads `+0x04` from manager query selector `6`, shifted left by 24;
the shared reset initializes the step at `+0x1C` to `0x00044444`. Together with
the decimal presentation evidence below, calling this the **battle countdown**
is a high-confidence functional identification, not a recovered type name. The
additional combat-state predicates in `FUN_001F10F0` can also prevent its
update independently of pause suppression.

The `0x44`-byte object at session `+0x2C` presents that countdown. Its encoded
live constructor is `0x0087E880`; its bit-`9` first-phase update at live
`0x0087EB40` obtains
`(value_at_0x006B28D4 + 0x00FFFFFF) >> 24`, splits it into two decimal digits,
and triggers sound `0x102D` when a changed positive value is below `6`. Its
second-phase update at live `0x0087EDD0` draws the digit textures. The object
loads `battlegauge.ccs` at raw BTL offset `0x00209C30`, preserved export
`0x008BDAF0`, live `0x008BDB30`. This establishes the functional label
**two-digit countdown presentation**; no RTTI class name was recovered. The
other bit-`9` object at session `+0x30` remains semantically anonymous.

### Shared ownership and controller lifecycle

Resident `FUN_001EF330` (resident/live `0x001EF330`, ELF file `0x0EF430`)
owns allocation and publication of the controller. If global `0x00607834` is
null, it allocates `0x6C0` bytes, initializes resident-side members, stores the
new pointer at `0x00607834`, and calls encoded live BTL constructor
`0x0076E9D0`. That constructor's physical bytes begin at preserved export
`0x0076E990`, raw file `0x000BAAD0`. The resident wrapper then supplies mode
bytes and calls encoded live BTL target `0x0076EC10`.

Resident `FUN_001EEFD0` (resident/live `0x001EEFD0`, ELF file `0x0EF0D0`)
performs the inverse path. It calls encoded live BTL destructor `0x0076ECF0`
(preserved export `0x0076ECB0`, raw file `0x000BADF0`), releases the remaining
resident-side members, frees the `0x6C0`-byte object, and clears global
`0x00607834`. Allocation/free and publication are therefore resident-owned;
BTL owns constructor, behavior, and destructor work inside the same object.

The outer lifetime is also bounded. State `14` calls resident
`FUN_001EC3B0`; when the session-owner global at `0x00607604` is null, that
function allocates a `0x38`-byte owner, publishes it, and invokes
`FUN_001EF330`. Resident `FUN_001EECD0` destroys that owner through
`FUN_001EEFD0` and clears `0x00607604`; this also destroys the pause controller
at `0x00607834` and the auxiliary BTL object at `0x00607844`. State `16`
(`FUN_001EDD10`) takes that path for every battle route other than `8`, including
start-menu routes `6` and `7`. Route `8` instead selects state `23` or `24`, and
each of those states performs the same owner destruction itself. Outer teardown
`FUN_001EC540` is another proven caller. Consequently, these objects do not
persist across a completed battle teardown: a continuing initialization route
allocates a new owner and new objects when it next reaches state `14`.

The BTL constructor initializes byte `+0x10` to `0`, halfwords `+0x12/+0x14`
to `0`, byte `+0x0D` to `0xFF`, and child pointer `+0x1C` to null. Encoded live
BTL target `0x0076F130` starts a controller branch by setting `+0x10 = 1` and
recording numeric selectors at `+0x0C/+0x0D`. The pre-update dispatcher at
live `0x0076EF90` selects one of three proven branches by `+0x0D`:

| `+0x0D` | Pre-update | Post-update | Cleanup | Constructed child size |
| ---: | ---: | ---: | ---: | ---: |
| `0` | `0x0076F6E0` | `0x0076F7C0` | `0x0076F610` | `0x20` bytes behind a `0x14`-byte wrapper |
| `1` | `0x0076F9F0` | `0x0076FB10` | `0x0076F840` | `0x440` bytes |
| `13` | `0x0076FC30` | `0x0076FD30` | `0x0076FB40` | `0x4C` bytes behind a `0x14`-byte wrapper |

All addresses in that table are encoded live targets. The corresponding
preserved-export bytes are `0x40` lower; raw file offsets are each live address
minus BTL base `0x006B3F00`.

Direct resource references establish functional presentation identities for
the three branches:

- selector `0` constructs its inner child at live `0x0076AD20`; that
  constructor directly loads the `battlegauge` resource literal at raw
  `0x001F1BE8`, preserved export `0x008A5AA8`, live `0x008A5AE8`;
- selector `1`'s `0x440`-byte child uses `3eye/enddemo.ccs` at raw
  `0x001F21D0`, preserved export `0x008A6090`, live `0x008A60D0`, together
  with `ANM_enddemo_ca` and other `ANM_end_*` resources;
- selector `13`'s child update directly loads `ougi.ccs` at raw `0x001F1AD0`,
  preserved export `0x008A5990`, live `0x008A59D0`, plus the
  `TEX_ougi_text_*`/`OBJ_ougi_text_*` resource family.

Accordingly, **battle-gauge presentation**, **end-demo presentation**, and
**ougi presentation** are high-confidence functional labels for selectors
`0`, `1`, and `13`. They are not recovered enum names, translations, or proof
of the exact visible phase covered by each branch.

Each branch constructs its child when `+0x10 == 1`, stores it at `+0x1C`, and
then writes `+0x10 = 2`. Subsequent pre/post calls update and draw the child.
Completion invokes branch cleanup; the common cleanup clears `+0x1C`,
`+0x12/+0x14`, and `+0x10`. The numeric lifecycle established statically is
therefore `0` inactive, `1` construction pending, and `2` child active. These
are descriptive lifecycle labels, not recovered user-facing state names.

Encoded live BTL entry `0x0076EE80` normalizes requested selector values
`13..15` to `13`, ignores selector `-1`, and starts a branch through
`0x0076F130` only when its numeric filters allow it. Controller byte `+0x694`
value `1` blocks every request; value `2` blocks selectors `0` and `1`. If an earlier
branch is active, `0x0076F130` first calls common cleanup `0x0076F1A0`, then
records the new `+0x0C/+0x0D` values and returns to construction-pending state
`1`.

A complete direct-store scan of the exact resident and BTL disassemblies found
only one constant-offset byte store to controller `+0x694`: live constructor
`0x0076E9D0` clears it to `0`. The implemented filter values `1` and `2` have
no direct producer in these two modules. Indirect writes or another overlay
remain possible, so this is a bounded negative rather than proof that those
values are unreachable.

The resident call origins establish the numeric selectors without establishing
their user-facing labels:

- session substate `1` in `FUN_001EF9C0` calls the wrapper at encoded live
  `0x0076EF60` with selector `0` and controller `+0x0C = 0`;
- session substate `8`, only for battle-route value `1` or `2`, calls it with
  selector `1` and controller `+0x0C = route - 1`;
- `FUN_00216EA0` passes requested selectors `13..15` and a one-bit object value
  for controller `+0x0C`; the BTL normalizer collapses all three selectors to
  `13`.

The wrapper at `0x0076EF60` discards its original second argument and forwards
the original third and fourth arguments as controller `+0x0C` and selector
`+0x0D`. This argument reshuffle matters when reading its resident call sites.

### Additional hold consumer

`FUN_0024ED40` (resident/live `0x0024ED40`, ELF file `0x14EE40`) is another
direct consumer. It requires the controller pointer and, while signed byte
`controller+0x10` is nonzero in its local state 0, repeatedly reasserts fields
and positions on a paired-object sequence and returns. Only a zero byte lets
the sequence advance to its next state. This proves a pause-aware hold, but
the higher-level sequence's semantic name was not established.

## BTL start-menu construction and UI states

### Resident ownership and top-level result routing

Resident `FUN_001EBD90` (resident/live `0x001EBD90`, ELF file `0x0EBE90`)
owns the top-level start-menu lifecycle. Its menu-local state, selected-side,
and object-pointer globals are respectively `0x00607660`, `0x00607664`, and
`0x00607668`. These are distinct from the battle-route global `0x00607670`
and the pause controller pointer at `0x00607834`.

When the manager at `0x00607600` has field `+0x14 == 0`, the relevant blockers
are clear, and resident `FUN_001EBC50` returns a nonzero side (`1` or `2`), the
owner stores that side, changes manager `+0x14` to `1`, and changes menu-local
state to `1`. While that state is active it allocates a `0xCC`-byte object if
needed, initializes resident member `object+0x8C`, calls encoded live BTL
targets `0x0087B0D0` and `0x0087B360`, publishes the object at `0x00607668`,
and calls encoded live BTL updater `0x0087D940` each pass.

A nonzero updater result closes the menu, restores manager `+0x14` to `0`,
destroys the object through encoded live BTL target `0x0087B160`, releases its
resident member, frees the object, and clears the menu globals. The resident
then routes the exact result as follows:

| BTL updater result | Resident effect |
| ---: | --- |
| `1` | Call `FUN_00216460` on both manager objects at `+0xDE4/+0xDE8` |
| `2` | Write battle-route value `7` at `0x00607670` |
| `3` | Write battle-route value `6` at `0x00607670` |

Because every nonzero result has already closed and freed the menu at this
point, result `1` is structurally the local continuation path: it refreshes
fields on the two manager objects but leaves the battle-route global unchanged.
Results `2` and `3`, by contrast, write nonzero routes consumed by the running
session and enter the teardown paths below. This establishes control flow, not
the on-screen wording of any choice.

This allocation chain proves that the `0xCC`-byte start-menu object and the
`0x6C0`-byte pause controller are separately resident-owned objects. They are
still coupled through manager `+0x14`: the active-menu value `1` forces the
first allowed-update mask to zero, supplies the primary-object exception in
the selective scheduler, and prevents the controller pre-work call described
above.

BTL contains adjacent class-identity strings for `ccStartMenuBase`,
`ccStartMenuPrivateCmd`, `ccStartMenuBasicCmd`, `ccStartMenuYesNo`,
`ccStartMenuSimpleDisp`, `ccStartMenuMission`, `ccStartMenuItemStock`,
and `ccStartMenuKeyconfig`. The first string is at
preserved export `0x008BD9E0`, raw file `0x00209B20`, live `0x008BDA20`.
These literals establish a start-menu class family, but not the semantics of
every numeric command.

The initializer at preserved export `FUN_0087B370` (raw file `0x001C74B0`,
live bytes `0x0087B3B0`) clears object field `+0x18`, then builds a command-ID
list beginning at `+0x1C`. Its numeric mode comes from resident
`FUN_001EC240`: field `+0x14` of the object at global `0x00607620`, or `0` if
that object is null. It separately reads manager `+0x1C`; for mode `2`, it
replaces that secondary value with `1` or `2` according to whether manager
`+0x18` is zero. The established lists are:

| Returned mode | Command IDs, in order |
| ---: | --- |
| `4` or `5` | `0, 4, 1, 6, 0xE` |
| `1` | `0, 4,` optional `4, 1, 6, 0xA, 0xB` |
| `3` | `0, 4, 1, 6, 9,` optional `7, 0xE` |
| `2` | `0, 4, 1, 6, 5, 0xA, 0xB` |

In mode `1`, the second ID `4` is included when manager `+0x1C` is `0` or `3`.
In mode `3`, ID `7` is included when encoded live BTL predicate `0x006EE550`
returns zero. Object fields `+0x04/+0x08` become `1/1` for final secondary
values `5` or `2`, `0/0` for values `4` or `1`, and `2/0` for value `0`.
This is proven mode-dependent menu routing. The labels of those mode values,
fields, and command IDs are not yet proven.

For the command IDs within this investigation's scope, the live factory at
`0x0087BB10` installs child implementations corresponding to the adjacent
class identities as follows:

| Command ID | Child identity |
| ---: | --- |
| `0` | `ccStartMenuKeyconfig` |
| `1` | `ccStartMenuBasicCmd` |
| `2`, `3` | `ccStartMenuPrivateCmd` |
| `6` | `ccStartMenuSimpleDisp` |
| `7` | `ccStartMenuItemStock` |
| `8`, `9` | `ccStartMenuMission` |
| `0xA..0xE` | `ccStartMenuYesNo` |

Command ID `4` has no child-construction block: its jump-table entry reaches a
deliberate null store if dispatched directly. Valid menu flow must therefore
filter it before the factory. Treating it as a nonselectable list marker is a
strong structural inference; its exact presentation role is not recovered.

The start-menu UI updater at preserved export `FUN_0087C6E0` (raw file
`0x001C8820`, live bytes `0x0087C720`) treats object `+0x00` as a numeric state:

- state `1` waits for resident target `0x00381FA0(object+0x44)`, then enters
  state `3`;
- state `2` waits for resident target `0x00381FC0(object+0x44)`, then enters
  state `6`;
- state `3` calls encoded live BTL target `0x0087C3F0`, whose physical bytes
  begin at preserved export `0x0087C3B0`, raw file `0x001C84F0`;
- state `4` advances opening/closing animation fields `+0x64`, `+0x6C`, and
  `+0x70`.

The child-result poller at preserved export `FUN_0087CAE0` (raw file
`0x001C8C20`, live bytes `0x0087CB20`) invokes a virtual method on the child at
`+0x38`. Child result `1` routes the parent to state `1`; result `2` routes it
to state `7`; result `3` routes it to state `8`.

The command-child factory at live `0x0087BB10` (preserved export
`0x0087BAD0`, raw file `0x001C7C10`) establishes the producers of those
results. Command ID `0xA` constructs a `ccStartMenuYesNo` child with field
`+0x0C = 2`; IDs `0xB..0xE` construct the same child class with `+0x0C = 3`.
The child's live updater `0x00877DD0` (preserved export `0x00877D90`, raw file
`0x001C3ED0`) returns `1` on one completion path and returns its `+0x0C` value
on the other. Consequently, command `0xA` can produce parent result `2`, while
commands `0xB..0xE` can produce parent result `3`. The user-facing labels of
these choices are not established by the updater alone.

The factory's exact Shift-JIS message fragments establish three prompts used by
the command lists above. In the battle-base branch, command `0xA` composes
`<r対戦|たいせん>`, `を<r終了|しゅうりょう>して`,
`ゲームモード<r選択|せんたく>`, and a final
`に<r戻|もど>りますが、...よろしいですか？` confirmation: conservatively,
“end the battle and return to game-mode selection?” Command `0xB` substitutes
`キャラクター<r選択|せんたく>`, giving “end the battle and return to
character selection?” Command `0xE` composes the fixed battle label with
`を<r終了|しゅうりょう>しますが、よろしいですか？`, or “end the battle?”
All three messages also contain `<iconCANCEL>キャンセル`.

Those fragments begin at live BTL addresses `0x008BCBF0`, `0x008BCC30`,
`0x008BCC80`, `0x008BCCA0`, `0x008BCCC0`, and `0x008BCCF0`; their raw offsets
are respectively `0x00208CF0`, `0x00208D30`, `0x00208D80`, `0x00208DA0`,
`0x00208DC0`, and `0x00208DF0`, and their preserved-export addresses are live
minus `0x40`. Command `0xA`'s non-`1` completion therefore becomes result `2`
and route `7`; command `0xB`'s becomes result `3` and route `6`. Command `0xE`
also produces result `3`/route `6`, but its prompt names no destination. This
is exact message composition plus established result flow; which physical
input selects each completion path was not inspected.

The parent result dispatcher at live `0x0087D330` (preserved export
`0x0087D2F0`, raw file `0x001C9430`) makes the parent states concrete:

| Parent state | Established dispatch/result |
| ---: | --- |
| `1..4` | Call live UI updater `0x0087C720`, return `0` |
| `5` | Call child-result poller `0x0087CB20`, return `0` |
| `6` | Return `1` |
| `7` | Wait on the effect at `+0xC0`, then return `2` |
| `8` | Wait on the effect at `+0xC0`, then return `3` |
| `9` | Complete the asynchronous object at `+0xC8`, then return field `+0xC4` |

Live wrapper `0x0087D940` calls that dispatcher, calls live draw/update target
`0x0087D460`, and preserves the dispatch result for the resident owner. This
closes the result chain without assigning speculative menu labels.

## Battle teardown and reconstruction

The resident battle controller dispatches its numeric states through one
switch. The established construction sequence is:

| State | Resident function | Established role |
| ---: | --- | --- |
| `11` | `FUN_001ED980` | Wait for the current resource fence, then start the next loaders and enter `12` |
| `12` | `FUN_001ED9E0` | Wait for readiness gates, start the next fence, and enter `13` |
| `13` | `FUN_001EDA50` | Adopt loaded fighter/stage resources, construct fighters, and enter `14` |
| `14` | `FUN_001EDB00` | Wait for readiness, construct the main battle graph, and enter `15` |
| `15` | `FUN_001EDB70` | Run the battle session; a completed session enters teardown state `16` |
| `16` | `FUN_001EDD10` | Countdown and release the main graph; destroy the session owner for non-`8` routes, then enter `17` |
| `17` | `FUN_001EDEE0` | Release shared graph resources, fighter resources, and the active stage archive |

All listed functions are resident/live addresses; their ELF file offsets are
their addresses minus `0x000FFF00`.

`FUN_001EE500` (resident/live `0x001EE500`, ELF file `0x0EE600`) handles the
reconstruction route dispatched as state `24`. It selects one side from
manager field `+0x50`, partially tears down the prior battle graph, destroys
the session owner (and therefore the pause controller and auxiliary BTL
object), and replaces the affected side data when required. It compares active
stage byte `manager+0x98` with pending stage byte `manager+0x9A`; when they
differ, it releases the current BTL stage archive and resident CCS resource,
and, unless the pending byte is `-1`, enqueues their replacements. It then
copies the pending identifiers, starts a resource fence, and writes controller
state `13`, re-entering fighter/stage construction. State `23`
(`FUN_001EE1C0`) is the other route-`8` reconstruction branch and likewise
destroys the session owner before returning to state `13`.

The relevant audited BTL helpers are:

| Operation | Raw file | Preserved export | Live |
| --- | ---: | ---: | ---: |
| Release active stage archive | `0x0000F260` | `0x006C3120` | `0x006C3160` |
| Enqueue replacement archive | `0x0000F2D0` | `0x006C3190` | `0x006C31D0` |
| Adopt loaded archive in state `13` | `0x0000F310` | `0x006C31D0` | `0x006C3210` |

This is a proven teardown-and-reconstruction lifecycle, not state rewind or
recorded-input playback. State `16` selects state `24` specifically when the
battle-route global is `8` and resident mode global `0x0060767C` is `2`; mode
value `1` selects state `23`.

The exact resident binary contains two immediate-value producers for route
`8`:

- `FUN_001EC5E0` (resident/live `0x001EC5E0`, ELF file `0x0EC6E0`) writes
  `0x00607678 = 1`, mode `0x0060767C = 1`, and route `0x00607670 = 8`, then
  writes its supplied value to the selected manager-side slot. Its sole direct
  resident caller is `FUN_0035B3B0`, which reaches it only when a side-indexed
  query returns nonzero and `FUN_001FDB40(side, 7) != 1`;
- `FUN_001F2E70` (resident/live `0x001F2E70`, ELF file `0x0F2F70`) contains the
  other immediate store, at `0x001F3370`. Along its numeric state-`0x0F` path,
  when the local result is zero, the session owner exists with halfword
  `+0x0A == 8`, and its progression bound permits another step, it increments
  the local counter, writes `0x00607678 = 1`, mode `0x0060767C = 2`, and route
  `0x00607670 = 8`, then marks one manager-side slot.

A complete direct-store scan of the exact resident disassembly found no other
immediate route-`8` writer. The generic route setter `FUN_001EC270` has only
resident callers passing `6` or `7`, and the exact BTL binary contains no call
to that setter. This establishes the two resident producer paths without
classifying the underlying result or recovering their user-facing labels;
indirect calls from another overlay remain possible.

### Start-menu result paths through teardown

The two nonlocal start-menu results follow a different, fully traced route.
In resident `FUN_001EF9C0`, battle-route value `6` or `7` makes the running
session request numeric route `0x17` and report completion. The outer battle
controller then advances through teardown states `16`, `17`, and `18`.

For controller field `+0x14` values `1` or `2`, state `18` sends battle-route
`7` to state `25` and battle-route `6` to state `22`:

- state `22` (`FUN_001EEAC0`) waits for the resource fence, clears it, and
  writes state `3`. State `3` resets session timing/status globals and advances
  into the ordinary initialization chain, which eventually reconstructs the
  fighter/stage resources and main battle graph in states `11..15`;
- state `25` (`FUN_001EEB10`) waits for the resource fence, clears it, writes
  manager `+0x0C = 1`, prepares the next resident resources, and causes the
  controller dispatcher to return status `3` to its caller.

The state-`3` path is not a direct snapshot restore or guaranteed immediate
rebuild. It traverses states `4..10`; states `7` and `9` can wait on separately
allocated control objects before the loader/reconstruction states `11..15`.
Thus start-menu result `3` -> battle-route `6` proves re-entry through the full
resident battle initialization lifecycle. State `16` has already destroyed the
old owner, so state `14` allocates a new owner, pause controller, and auxiliary
BTL object. Start-menu result `2` -> battle-route `7` instead reports outward
through state `25` and does not select reconstruction state `24`. Command
`0xA`'s exact result-`2` prompt and the established result-`3` prompts are
documented above; because multiple commands can produce result `3`, that route
does not have one unique user-facing label.

## Replay result and useful negatives

No battle replay capture/playback system was proven. Bounded literal searches
of both exact binaries and their resident/BTL exports found no meaningful
`replay`, `record`, `playback`, or `rematch` identifier; decompiler “maximum
restarts” messages were analysis warnings, not game behavior. The traced
reconstruction and initialization-re-entry routes exposed resource/object
teardown, but no replay buffer, capture/playback mode, serialized battle
snapshot, or explicit random-seed/state restore.

This is a useful negative result, not proof that the game has no replay
facility. Search and call-graph coverage were not exhaustive, and no runtime
experiment was performed.

A separate resident field at `object+0x504`, returned by `FUN_00103BA0` and
advanced through numeric states `0..4` by `FUN_001086C0`, is an asynchronous
I/O retry/status machine used by sector reads. Its nonzero value causes sector
read wrappers to wait or retry. It is not evidence of gameplay pause ownership
and should not be conflated with the battle controller at `0x00607834`.

## Open questions

- What exact visible phase boundaries and localized labels correspond to the
  established battle-gauge, end-demo, and ougi selector branches?
- Which concrete subsystems correspond to the still-anonymous fixed consumers
  on bits `5..10`?
- Which exact visible phase of the cut-in presentation corresponds to byte
  `+0xA50 == 1`, and do all cut-in variants use this path?
- What user-facing labels belong to the remaining start-menu command IDs, and
  which exact input path produces common result `1`? Commands `0xA`, `0xB`, and
  `0xE` now have bounded battle-branch prompt evidence above.
- What user-facing events correspond to the two established route-`8`
  producers (mode `1` -> state `23`, mode `2` -> state `24`)?
- Does any battle replay mechanism exist outside the bounded paths inspected
  here? A runtime trace at pause entry, menu selection, and reconstruction
  would discriminate these remaining cases more directly than names alone.
