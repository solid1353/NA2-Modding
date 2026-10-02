# Pause, start-menu, and battle-restart control

This document records the resident and BTL control paths for battle pause
suppression, the battle start menu, and battle reconstruction in retail NA2
(`SLPS-25837`). Numeric states and command IDs remain numeric unless their
effect is directly established; descriptive working identities are
distinguished from recovered RTTI names.

## Research coverage

- **Assigned scope:** battle pause and replay control: pause-controller
  ownership and states, the update paths affected by its masks, start-menu and
  result routing, and any provable battle replay, restart, or reconstruction
  lifecycle.
- **Exploration depth:** deep but bounded:
  - The resident running-session chain from `FUN_001EF8F0` through mask
    construction `FUN_001F0290`, the complete explicit bit-dispatch table in
    `FUN_001F03E0`, countdown/update calls `FUN_001F10F0` and `FUN_001F0B10`,
    owner construction/destruction, and controller states `11..25`, including
    the route-`6`, route-`7`, and route-`8` paths and their direct producers.
  - The BTL pause-controller lifecycle through its constructor, update, and
    destructor targets; selectors `0`, `1`, and `13`, their resources, and
    their direct parent-mask writes; the complete common cleanup and the three
    branch release bodies.
  - The auxiliary object at `0x00607844` through allocation, destruction, and
    the cut-in `+0xA50` writer/reset range live `0x0086F2E0..0x00870B38`.
  - The primary scheduler array built at live `0x007092E0` through
    constructors, vtables, RTTI, and callback slots.
  - The start-menu chain from resident `FUN_001EBD90` through BTL live
    `0x0087B0D0..0x0087D940`, its command lists, command factory, child-result
    propagation, and the Shift-JIS prompts for commands `0xA`, `0xB`, and
    `0xE`; the Simple Display child's selection and completion path.
  - Direct-pattern scans of the two binaries for immediate route-`8` stores,
    constant-offset stores to auxiliary `+0xA50` and controller `+0x694`,
    direct calls to the session override writer (BTL, resident, and ETC), and
    `gp`-relative loads of `0x00607834` (six BTL and 31 resident sites).
  - A bounded replay search of resident/BTL literals, exports, and the
    teardown/reconstruction call paths.
- **Confirmed coverage:** resident ownership of the pause controller,
  persistence and direct producers of its two suppression words, the selective
  three-phase scheduler and its exceptions, the separate aggregate countdown
  gate, start-menu command/result-to-route flow, the Free Battle and Practice
  command lists with their placeholder replacement and joins to the observed
  labels, owner destruction and
  recreation during restart-like paths, the two route-`8` reconstruction
  producers, the second-phase override's copied-mask semantics, distinct reset
  and participant lifetimes, and the lack of a proven replay mechanism in the
  inspected paths.
- **Unresolved or untested:**
  - Indirect or other-overlay suppression writers, cached controller aliases,
    and whether all interruption paths restore the copied second-phase
    override.
  - Exact visible phases and labels for the battle-gauge, end-demo, and ougi
    branches and for the cut-in flag; semantic identities of the fixed
    scheduler consumers on bits `5..10`.
  - Labels of the mode-`3`, `4`, and `5` start-menu entries, producers of
    modes `4` and `5`, and the input path that produces result `1`.
  - The user-facing events behind route-`8` modes `1` and `2`.
  - Replay mechanisms outside the bounded paths.
- **Deliberate exclusions and overlap:**
  - Controller-input polling belongs to
    [Controller input](../../runtime/controller_input.md); Practice configuration
    to [Practice mode](../modes/practice_mode.md); result interpretation to
    [Match outcomes](match_outcomes.md); visible menu labels to
    [Modes and navigation](../../game/modes_and_navigation.md).
  - Session construction, teardown order, and continuation rebuilds belong to
    [Battle lifecycle](battle_lifecycle.md); reusable timer arithmetic to
    [Timer primitives](../../runtime/timer_primitives.md); participant admission
    and release to [Target selection](../combat/target_selection.md); graph ownership to
    [Battle entities](battle_entities.md).
  - Story-mode logic and non-gameplay media are excluded.
- **Evidence limitations:** conclusions are static. No pause, menu-selection,
  reconstruction, or replay behavior was observed at runtime, so visible
  timing, exact input mapping, and dynamic reachability remain unverified.
  Direct-pattern scans do not exclude indirect writes, dynamically selected
  calls, or other overlays.

## Evidence identity and address conventions

Address conventions follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Encoded absolute pointers and `j`/`jal` targets in the raw overlay already use
live addresses; their physical target bytes appear at `encoded live target -
0x40` in the preserved export, which explains several misleading intra-overlay
callee labels there. Interpretive labels are explicitly described as
inferences.

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

### Session-local override writer

Resident entry `0x001EC620..0x001EC658` (file `0x0EC720..0x0EC758`) writes
the second-phase override without writing the pause controller. With a non-null
session at `0x00607604`, it reads computed allowed mask `session+0x04`, sets
bit `0x10` for nonzero argument or clears it for zero argument, and stores the
result at `session+0x08`. The read is **`+0x04`, not `+0x08`**: restoration
therefore copies the current computed mask with bit `4` enabled, rather than
recovering a saved override: `lhu v1,4(a1)` at `0x001EC62C` and
`sh v1,8(a1)` at `0x001EC650`.

The mask builder ORs the complement of this override into the second
suppression temporary. **Inference from the exact operations:** argument zero
requests suppression of second-phase bit `4` on the next mask construction;
nonzero removes that bit from this override's suppression contribution.
Other disabled bits in the sampled computed mask can remain disabled in the
copied override, and controller suppression can independently keep bit `4`
disabled. This is neither a write to controller `+0x12/+0x14` nor an
unconditional enable of the next final mask. Bit `4` dispatches
`ccFieldCtrl`'s second callback, as tabulated below.

The twelve direct calls below (`jal` bytes `88 B1 07 0C`) are all in BTL; the
resident executable and ETC have none. These are callsites, not inferred
original function names; numeric animation fields remain numeric.

| BTL callsite, live (Ghidra = live minus `0x40`) | Argument and bounded caller condition |
| --- | --- |
| `0x00793A3C / 0x00793CE0` | Common paired-object path: zero when request flags bit `0` is set; restoration uses `1` while object byte `+0x70` is nonzero, after restoring saved camera vectors. |
| `0x0079BFE0 / 0x0079C02C` | `1` during cleanup when object byte `+0x10BA` is nonzero; `0` while counter `+0x1108 > 0` and the battle manager exists, before camera request `FUN_001F1740(1,2,10,2)`. |
| `0x007CE8EC` | `0` when the animation object at owner `+0x320` has word `+0x98 == 0x6A`; no paired `1` call in this native body. |
| `0x007D86C8 / 0x007D873C` | `0` for owner word `+0x1DC == 0x21`, `1` for `0x57`. |
| `0x007E01D8 / 0x007E0228` | Separate small entry/exit bodies pass `0/1` after their optional resident effect-service calls. |
| `0x007EEEC0 / 0x007EEF98 / 0x007EEFE0` | Destructor-shaped body passes `1` for nonnull owner; update passes `0/1` when owner `+0x2C8 > 0` and its animation word `+0x98` is `0x4E/0x64`. |

The last update's `0` call is at Ghidra `0x007EEF58`
(`0x007EEED0..0x007EEFA4` holds both requests). Other
listed paired paths corroborate disable/restoration behavior across several
native bodies, without establishing that every character variant restores an
override after every possible interruption. Shared resource-driven or indirect
calls, other overlays and writes through arbitrary aliases remain outside this
direct-JAL boundary.

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

### Bounded pointer-based writer review

The `lw ..., -0x31BC(gp)` load of global `0x00607834` (bytes `44 CE ?? 8F`)
occurs at six aligned BTL sites and 31 resident sites in the real ELF mapping,
repeated in two ELF alias mappings. The containing object-specific paths were
followed.

The additional BTL paths set the controller's stage byte `+0x0E`, query
selector `+0x0D`, issue a selector-`-1` request through the normalizer, or read
side-indexed identity/appearance bytes `+0x04/+0x08`. The latter retains the
controller pointer on its stack in Ghidra `0x0076BA30..0x0076BFA0`; its three
indirect callbacks are fixed to live `0x0076E180/0x0076E7C0/0x0076E870` and
perform resource/identity queries, not controller-mask stores. The additional
resident paths read activity/side fields, issue the already traced branch
requests, or update side flags through live `0x0076ECC0`. No additional
controller suppression-word writer or nonzero request-filter `+0x694`
producer was identified in these bounded paths. This is not a proof about
other address-loading forms, cached aliases, arbitrary callback targets, bulk
writes, or unexamined overlays. The session override writer above has a
different destination and does not contradict this controller-specific result.

### Selective update gating

`FUN_001F03E0` (resident/live `0x001F03E0`, ELF file `0x0F04E0`) consumes the
allowed masks in three phases:

| Phase | Mask | Dispatch |
| --- | --- | --- |
| First | session `+0x02` | object virtual slot `+0x0C` and fixed subsystem updates |
| Second | session `+0x04` | object virtual slot `+0x10` and fixed subsystem updates |
| Third | session `+0x02` | object virtual slot `+0x14` and fixed subsystem updates |

At entry, instructions `0x001F0430/0x001F0434` cache both masks in registers
before controller pre-work at `0x001F0468`. Child mask writes or common cleanup
later in this dispatch do not replace those cached values. Together with the
outer order `FUN_001F0290 -> FUN_001F03E0`, this establishes that their new
suppression values feed the next eligible mask construction. It does not
establish a measured display-frame delay. The cut-in exceptions below read
the auxiliary byte separately during dispatch and are not the same cached
mask contract.

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

The battle countdown at resident `0x006B28D0` supplies a second kind of pause
gate outside the per-bit scheduler. `FUN_001F0290` sets bit `0` of its flags
byte when either pre-complement suppression word is nonzero and clears the bit
only when both are zero. Later in the same session update, `FUN_001F10F0`
conditionally calls accumulator `FUN_001EBA80`, which does not advance while
flags bit `0` is set. The accumulator and its other gates are described in
[Match outcomes](match_outcomes.md#timer-path); the configured session reset
(`FUN_001ED110`, outer state `3`) versus round initialization
(`FUN_001EEE30`) in
[Timer primitives](../../runtime/timer_primitives.md#clear-versus-configured-reset);
the arming of flag bit `1` at owner creation in
[Battle lifecycle](battle_lifecycle.md#session-construction); and its
two-digit presentation by the session `+0x2C` clock in
[Battle HUD](battle_hud.md#central-battle-clock-display). Route `8` re-enters
at state `13` without traversing state `3`, so it rebuilds the session and
rearms the countdown without the configured reset.

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

The controller has the session's lifetime: session destruction (state `16`
for routes other than `8`, states `23/24` for route `8`, or outer teardown
`FUN_001EC540`) destroys it together with the auxiliary BTL object at
`0x00607844`, and the next state `14` allocates new ones. The session
construction and teardown order belong to
[Battle lifecycle](battle_lifecycle.md#teardown-order).

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

The lifecycle byte has exactly these BTL stores: the constructor (live
`[0x0076E9D0,0x0076EC10)`) writes `0` at live `0x0076EAA4`; the request
routine `0x0076F130` first runs common cleanup when the byte is nonzero, then
writes `1` at live `0x0076F168`; the three branches write `2` after
constructing their child at live `0x0076F778` (selector `0`), `0x0076FAB4`
(selector `1`), and `0x0076FCE8` (selector `13`); and common cleanup writes `0`
at live `0x0076F230`. No `-1` store to this byte exists in the implementation;
the zero store at live `0x0076FCDC` belongs to a newly allocated child object.

The complete common cleanup is live `0x0076F1A0..0x0076F328`, Ghidra
`0x0076F160..0x0076F2E8`, file `0x0BB2A0..0x0BB428`. Beyond the fields above, it
clears controller `+0x220/+0x224`, owned
presentation handles `+0x5C0..+0x5CC`, and `+0x234`. After its final service
call, it writes byte `+0x0D = -1` and halfword `+0x18 = -1`. It does not
reset request-filter byte `+0x694`, mode byte `+0x0C`, or halfword `+0x1A`.
This is a branch-end reset on a retained object, distinct from destruction of
the object itself.

Each of the three pre-update bodies reaches common cleanup when its child
update returns zero: selector `0` calls it at live `0x0076F794`, selector `1`
at `0x0076FAD0`, and selector `13` at `0x0076FD04`. Selector `0` and `1`
then call resident `FUN_001E91E0`; selector `13` does not. The branch-specific
release bodies are complete at Ghidra `0x0076F5D0..0x0076F69C`,
`0x0076F800..0x0076F934`, and `0x0076FB00..0x0076FBE4`. The last also restores
both manager-published fighters' `+0x1B0` to float `1.0`. Their pointer tests
and releases concern the child graph; the two suppression-word clears occur
in common cleanup.

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

### Tone-shade destination block

The pause controller (the "sequence" object in
[Randomness](../../runtime/randomness.md#tone-shade-animator-timing-is-not-another-seed))
embeds a tone-shade destination block at `+0x650` and its eight-byte
`ccToneShadeAnimRandom` animator at `+0x68C`. The animator's LCG draws belong
to Randomness. "Displayed" addresses below are preserved Ghidra BTL addresses;
see [address conventions](../../game/files/file_identities.md#address-conventions).

**Observation, high confidence.** `FUN_001EF330` initializes destination
`controller + 0x650` before constructing the animator at `+0x68C`, then
publishes the controller at `0x00607834`. Resident `FUN_001EEFD0` calls live
BTL `0x0076ECF0` before destroying the embedded destination through
`FUN_0018F530(controller + 0x650, -1)` and freeing the controller. That
destination destructor redirects global `0x00602A64` to resident default
`0x00618F00` if it still points at the destroyed destination. Neither
inspected teardown body calls the animator's update slot or a separate
animator destructor.

The controller's post-work callback, displayed `0x0076EFE0` / live
`0x0076F020`, writes `controller + 0x650` to `gp-0x7F8C`, live global
`0x00602A64`, at displayed `0x0076F018/0x0076F01C`, unless signed byte
`controller + 0x694` equals one. It also publishes the adjacent render blocks.
Resident context constructors `FUN_001982B0` and `FUN_00198340` copy this
global into context `+0x250`. Resident dispatcher `FUN_001F03E0` replaces it
with the default at `0x001F06C8..0x001F06D0` after controller post-work.
These are destination publication paths; no animator receiver or invocation
follows from the publication alone.

A writer to the two destination words `+0x34/+0x38` does not use an RNG.
Displayed `0x0076F3B0` / live `0x0076F3F0` acts only when its second integer
argument is numeric ID `0x49`; it takes the controller in `a0` and a
coefficient in `f12`. Its instruction span `0x0076F3F0..0x0076F5A0`
includes the following stores:

| Displayed instructions | Controller-local effect |
| --- | --- |
| `0x0076F44C..0x0076F4B0` | Add binary32 `0.01f` to accumulator `+0x698`, add one when negative, subtract one when at least one. |
| `0x0076F4B4..0x0076F518` | Apply the same update to the independent accumulator `+0x69C`. |
| `0x0076F51C..0x0076F54C` | Bind a resource to destination `+0x650`, store the supplied coefficient at destination `+4`, and set its numeric parameters. |
| `0x0076F564..0x0076F570` | Copy accumulator `+0x698` to destination `+0x34` and accumulator `+0x69C` to destination `+0x38`. |

The controller initializer clears both accumulators at displayed
`0x0076EB7C/0x0076EB80`. In the inspected helper family this writer is called
from displayed `0x0076DCB0` / live `0x0076DCF0` only under its record flag
`+4 & 0x400`; the caller supplies coefficient `1.2f` when its numeric state is
below six and `1.0f` otherwise. This bounds an independent write path, not
measured cadence or feasibility of the ID/flag combination. It does not touch
animator counter `controller + 0x690` or period `+0x692`.

### Session resets and retained skill participants

Resident `FUN_001EED40` is the `0x38`-byte session-owner reset called by
`FUN_001EEC80` before round initialization and by `FUN_001EECD0` after graph
teardown. It writes both computed masks `+0x02/+0x04` and session-local
overrides `+0x06/+0x08` to `0xFFFF`, and zeros the owner pointer fields.
It does not reset the countdown structure or the separately allocated
controller in place. The owner allocation/reconstruction contract remains in
[Battle lifecycle](battle_lifecycle.md#session-construction).

The `ccPlayerCtrl` coordinator retains its skill participants independently
of the pause controller. Its constructor `FUN_0024E0B0` clears participant
pointers `+0x24/+0x28`, and state-setter callers `FUN_00216C60` and
`FUN_00216D00` install their supplied pair after setting a state. Common
pause-controller cleanup has no coordinator access, so ending the presentation
does not release the retained pair, and state-6 substate `0` can resume with
the same pair after controller `+0x10` becomes zero. The state setter,
input lock, and release belong to
[Target selection](../combat/target_selection.md#skill-participants-and-lock-release)
and [Battle entities](battle_entities.md#derived-fighter-registrycoordinator).

### Additional hold consumer

`FUN_0024ED40` (ELF file `0x14EE40`), the coordinator's Ultimate Jutsu
state-6 handler ([Target selection](../combat/target_selection.md#skill-participants-and-lock-release),
[Ultimate Jutsu](../characters/ultimate_jutsu.md#damage)), also consumes the controller. It
requires the controller pointer and, while signed byte `controller+0x10` is
nonzero in its local state 0, reasserts fields and positions on the paired
fighters and returns; only a zero byte lets it advance.

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

| Returned mode | Process requested by | Command IDs appended, in order |
| ---: | --- | --- |
| `4` or `5` | No producer established | `0, 4, 1, 6, 0xE` |
| `1` | Free Battle, `FUN_001EA8C0 -> FUN_001EC300(1)` | `0, 4,` optional `4, 1, 6, 0xA, 0xB` |
| `3` | `FUN_001EC300(3)` from `FUN_001FEA70`, `FUN_001FED10` and `FUN_001FEF50`; not Free Battle or Practice | `0, 4, 1, 6, 9,` optional `7, 0xE` |
| `2` | Practice, `FUN_001EA940 -> FUN_001EC300(2)` | `0, 4, 1, 6, 5, 0xA, 0xB` |

`FUN_001EC7A0` stores the `FUN_001EC300` argument at process `+0x14`
(`sw s1, 0x14(s0)` at `0x001EC7C4`); the manager-mode joins are owned by
[Mode flow](../../game/mode_flow.md#btl-handoff-and-return).
In mode `1`, the second ID `4` is included when manager `+0x1C` is `0` or `3`.
In mode `3`, ID `7` is included when encoded live BTL predicate `0x006EE550`
returns zero. The append helper at live `0x0087BAE0` (Ghidra `0x0087BAA0`)
stores into `+0x1C + 4*count` only while count `+0x18` is below `7`.

ID `4` is a placeholder, not a dispatched command. After the list is built,
the initializer calls live `0x0087C190` (Ghidra `0x0087C150..0x0087C19F`),
which replaces the first list entry equal to its second argument with its third
argument and stops. It first calls `(4, 2)` unless the final secondary value is
`5` or `2`, then always calls `(4, 3)`. Therefore:

- with secondary value `5` or `2`, the first `4` becomes `3`;
- otherwise the first `4` becomes `2`, and a second `4` (Free Battle with
  manager `+0x1C` equal to `0` or `3`) becomes `3`;
- in Practice, the single `4` becomes `2` when manager `+0x18` is zero and
  `3` otherwise.

Object fields `+0x04/+0x08` become `1/1` for final secondary
values `5` or `2`, `0/0` for values `4` or `1`, and `2/0` for value `0`.
The meaning of fields `+0x04/+0x08` is not established statically.

### Start-menu admission timeout-marker check

In `FUN_001EBD90`, resident `0x001F4790(manager,0)` first tests whether the
session manager's `+0x14` equals zero. Only that zero-state branch reads the
timeout marker through `FUN_001EC290` at `0x001EBE0C`. A set marker follows
`0x001EBE24..0x001EBE34` to the read-only getter `0x001F47B0(manager)` and
returns, skipping the later input/request admission path and its writes. The
nonzero manager-state branch at `0x001EBEE0` processes the existing child
without this check. A set timeout marker therefore blocks opening a start
menu; it does not by itself cancel or destroy an already active child. The
marker's producer and reset belong to
[Match outcomes](match_outcomes.md#terminal-detector-and-classifier).

### Command identities and observed labels

The live factory at `0x0087BB10` installs child implementations corresponding
to the adjacent class identities as follows:

| Command ID | Child identity |
| ---: | --- |
| `0` | `ccStartMenuKeyconfig` |
| `1` | `ccStartMenuBasicCmd` |
| `2`, `3` | `ccStartMenuPrivateCmd`; child `+0x0C` is the command ID minus `2` (`addiu v1, s1, -2` at Ghidra `0x0087BBC8`) |
| `5` | Practice settings wrapper; see [Practice mode](../modes/practice_mode.md#registered-standalone-practice-selection) |
| `6` | `ccStartMenuSimpleDisp` |
| `7` | `ccStartMenuItemStock` |
| `8`, `9` | `ccStartMenuMission` |
| `0xA..0xE` | `ccStartMenuYesNo` |

Command ID `4` has no child-construction block: its jump-table entry reaches a
null store if dispatched through this factory. It never reaches the factory
from the Free Battle or Practice lists, because the placeholder replacement
above rewrites every `4` there to `2` or `3`.

Runtime observation recorded in
[Modes and navigation](../../game/modes_and_navigation.md#free-battle-round-and-pause-menu)
shows the Free Battle entries Controls, 1P Commands (opens the character's
move list), Command Chart, Simple Display, Back to Game Mode Screen, and Back
to Character Select, with 2P Commands inserted after 1P Commands in a
joined-Player-2 round. These match the mode-`1` list in order: `0`, `2`
(optional `3`), `1`, `6`, `0xA`, `0xB`. The
[Practice menu](../../game/modes_and_navigation.md#practice-pause-menu) shows
Controls, 1P Commands, Command Chart, Simple Display, Practice, Back to Game
Mode Screen, and Back to Character Select, matching the mode-`2` list in order:
`0`, `2` or `3`, `1`, `6`, `5`, `0xA`, `0xB`. The move-list entries are
therefore `ccStartMenuPrivateCmd` children, the Practice entry is the command-`5`
Practice settings wrapper, and the two exits are the `0xA`/`0xB` Yes/No
children. Commands `7` and `9` (`ccStartMenuItemStock`, `ccStartMenuMission`)
and `0xE` appear only in the mode-`3` list, which neither Free Battle nor
Practice selects. The labels of the mode-`3` entries are not established.

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

### Simple Display selection

Command `6`'s `ccStartMenuSimpleDisp` initializer is live BTL `0x00877870`
(preserved address `0x00877830`, raw file `0x001C3970`). The child owns its
selection window at `+0x0C`; that window owns the list at `+0x7C`. Instruction
`sh zero, 0x10(v0)` at live `0x00877904` (preserved `0x008778C4`, raw
`0x001C3A04`, bytes `100040A4`) disables automatic completion. It does not
select a row. The preceding resident list initializer `FUN_00382a20` clears
the selected row, a 32-bit field at list `+0x18`, to `0`. The Simple Display
initializer does not read the current Simple Display setting.

Resident input handler `FUN_00383340` changes list `+0x18` for cursor movement.
Result getter `0x00383590` returns that field unless completion state `+0x12`
is `2`, in which case it returns `-1` for cancellation.

List `+0x10` is a 16-bit automatic-completion mode. `FUN_003834e0` recognizes
`1` as confirmation and `2` as cancellation. Once counter `+0x22` reaches
threshold `+0x20`, it copies the mode into completion state `+0x12` and sets
event bit `0x08` at `+0x28`. Both counter and threshold initialize to zero,
so enabling mode `1` without a delay immediately enters confirmation when
the window becomes ready. `FUN_00382ef0` then calls `FUN_00383240`, whose
confirmation animation advances the `+0x24/+0x26` counters, followed by
`FUN_003831c0` to close the window.

The completion updater is live `0x00877A10` (preserved `0x008779D0`). It
reads the selected row through resident `0x00383590`: row `0` passes enabled
to `FUN_001f6d80`, while row `1` passes disabled. The order is therefore
On, Off. `FUN_001f6d80` delegates to `FUN_001f59f0(manager, 0, value)`, which
writes bit `0x02` of the active settings pack.

The corresponding getter is `FUN_001f6db0`, delegating to
`FUN_001f6420(manager, 0)`. Its case at `0x001F6448` selects
`manager+0x9F4` in modes `2/3` and `manager+0xA00` otherwise, then returns
bit `0x02` as a Boolean. The menu's initial row and the active value are
independent: its fixed initial On selection does not establish that the
setting is On.

The complete initializer spans preserved `0x00877830..0x008779CF`.

## Battle teardown and reconstruction

Battle teardown and reconstruction are resident outer-controller states:
states `11..14` load resources and build the session, state `15` runs it,
state `16` (`FUN_001EDD10`) destroys the session for routes other than `8`,
and state `17` releases archives. Route `8` instead selects state `23`
(`FUN_001EE1C0`, mode `0x0060767C == 1`) or `24` (`FUN_001EE500`, mode `2`);
each destroys the session (and therefore the pause controller and auxiliary
BTL object) itself and re-enters at state `13`. The session teardown and
rebuild, including the stage-archive comparison of state `24`, belong to
[Battle lifecycle](battle_lifecycle.md#continuation-encounters-rebuild-the-session);
the two route-`8` producers (`FUN_001EC5E0` after an Ultimate Jutsu form
request, `FUN_001F2E70` in the higher-level sequence) to
[Match outcomes](match_outcomes.md#higher-level-sequence-counter-and-result-8-continuation)
and [Awakening](../characters/awakening.md#effect-to-form-mapping-and-resource-replacement).
A direct-store scan of the resident disassembly found no other immediate
route-`8` writer; generic route setter `FUN_001EC270` has only resident
callers passing `6` or `7`, and BTL does not call it. This is a
teardown-and-reconstruction lifecycle, not state rewind or recorded-input
playback.

### Start-menu result paths through teardown

Start-menu results `2` and `3` become battle-route codes `7` and `6`. Both
end the running session and pass through teardown states `16..18`; state `18`
sends route `6` to state `22`, which loops to state `3` and re-enters the full
initialization chain (states `4..10`, then `11..15`, with a new session and
pause controller allocated at state `14`), and route `7` to terminal state
`25`. The outer routing is described in
[Match outcomes](match_outcomes.md#outer-controller). Because multiple
commands can produce result `3`, that route has no single user-facing label.

## Replay result and useful negatives

No battle replay capture/playback system was proven. Bounded literal searches
of both exact binaries and their resident/BTL exports found no meaningful
`replay`, `record`, `playback`, or `rematch` identifier. The traced
reconstruction and initialization-re-entry routes exposed resource/object
teardown, but no replay buffer, capture/playback mode, serialized battle
snapshot, or explicit random-seed/state restore.

This is a useful negative result, not proof that the game has no replay
facility; search and call-graph coverage were not exhaustive.

The resident field at `object+0x504` (returned by `FUN_00103BA0`, states
`0..4` advanced by `FUN_001086C0`) is a sector-read retry/status machine owned
by the resident runtime (see [Overlay ABI](../../runtime/overlay_abi.md) and
[Resident task system](../../runtime/task_system.md)); it is unrelated to the
pause controller.

