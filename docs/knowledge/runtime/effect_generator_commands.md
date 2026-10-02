# Effect-generator commands

This document investigates how retail NA2 (`SLPS-25837`) executes authored
effect-generator action packets: runner construction, command bytes, scene and
bone anchors, update scheduling, and removal/reset lifetime. Addresses are
resident `SLPS_258.37` EE addresses unless an overlay is named; see
[address conventions](../game/files/file_identities.md#address-conventions).
Composition-child attachment chains are a separate system documented in
[Composition attachment dynamics](composition_attachment_dynamics.md).

## Research coverage

- **Assigned scope:** Downstream execution of authored effect-generator actions, including command fields, event/frame conditions, scene/bone anchoring, spawn/remove and reset/lifetime.
- **Exploration depth:** The resident action constructor, complete command-update loop, both recovered resident update callers, and the reset and removal families were traced statically; broader scene-wrapper scheduling was not traced.
- **Confirmed coverage:** Generator creation precedes command execution; byte commands select an emission gate and saturating cursor. Primary/secondary anchors retain current/previous positions. Animation and streamed owners supply different iteration-count units. Immediate removal, deferred owner requests and cursor rewind are distinct operations.
- **Unresolved or untested:** The action-entry preserved dword, authored corpus distributions of command values, packet lengths and anchor combinations, every outer scheduler, and visible consequences of the different count units of the two callers remain unresolved.
- **Deliberate exclusions and overlap:** [CCS object types](../game/files/ccs_object_types.md) owns the `0x0D80` and `0x0D90` parser/type evidence; [CCS runtime](../game/files/ccs_runtime.md) owns container lists and stream playback; [Particle runtime](particle_runtime.md) owns emitter simulation and particle survival after removal requests; [Model runtime](model_runtime.md) owns skeleton matrices; [Composition attachment dynamics](composition_attachment_dynamics.md) owns `0x2300` composition-child chains; [Scene playback owners](scene_playback_owners.md) and [Timer primitives](timer_primitives.md) own broader caller timing.
- **Evidence limitations:** Static retail `SLPS_258.37`, with direct-call searches of `BTL.BIN` and `ETC.BIN`. Preserved analysis has incomplete function definitions, xrefs and argument recovery; instructions and resident bytes corroborate the relevant code. Direct-call negatives do not exclude indirect paths. No live instance state has been observed.

## Generator-action runners

**Observation, high confidence.** `FUN_001ABBE0` walks the action-packet list
through packet `+0x04`, creates a `0x10`-byte runner per packet with
`FUN_001AB0B0`, and links the runners through runner `+0x00`. The manager's
`+0x00` selects the generator owner; zero selects resident default `0x0061AF80`.
The runner retains its source packet at `+0x04`, stores the entry count at
`+0x08`, and allocates `0x14` bytes of state per entry at runner `+0x0C`.

For entry `i`, the source descriptor is `packet + 0x10 + 0x18*i`. The following
fields are named by their consumers rather than by adjacent resource names.

| Descriptor-relative field | Consumer-established role |
| ---: | --- |
| `+0x00` | Generator record supplied to `FUN_001AACF0`. |
| `+0x04` | Optional primary anchor record. Construction reads record `+0x34`, then its first word, into state `+0x04`. |
| `+0x08` | Optional secondary anchor record, resolved the same way into state `+0x08`. |
| `+0x0C` | Preserved dword not read by the inspected constructor/update loop; meaning remains unresolved. |
| `+0x10` | Unsigned halfword command-byte count. |
| `+0x14` | Pointer to command bytes; copied into state `+0x00` as the current cursor. |

| Entry-state offset | Role |
| ---: | --- |
| `+0x00` | Command-byte cursor. |
| `+0x04`, `+0x08` | Primary and secondary scene-object pointers. |
| `+0x0C` | Materialized generator pointer. |
| `+0x10` | Owner handle, initialized to `-1`. |

Ghidra defines no function at constructor callback `0x001AB260`; its bytes
`0x001AB260..0x001AB274` independently show stores of zero to state `+0x0C`
and `-1` to `+0x10`, followed by return. `FUN_001AACF0` creates a generator only
when the handle is `-1` and the generator record's `+0x2C` descriptor is nonzero.
It calls `FUN_00352A10`, stores the handle, obtains the pointer with
`FUN_00352C40`, copies seven descriptor floats through
`FUN_001AB040..FUN_001AB0A0`, and calls `FUN_0034C400(generator,0)`.
Thus generator allocation occurs during runner construction, before an enable
command; enable/disable bytes are not themselves allocation/removal commands.

Those setters are direct `swc1 f12` stores. Descriptor-to-generator offsets are
`+0x20 -> +0x16C`, `+0x24 -> +0x184`, `+0x1C -> +0x180`,
`+0x0C -> +0x190`, `+0x10 -> +0x188`, `+0x14 -> +0x194`, and
`+0x18 -> +0x18C`, in initialization order. Their emitter meanings belong to
[Particle runtime](particle_runtime.md); they are numeric values.

### Commands and iteration ordering

**Observation, high confidence.** The complete `FUN_001AB280`
`0x001AB280..0x001AB428` loop executes these steps for each entry, in order:

1. Read the unsigned byte at the current cursor. Byte `1` calls
   `FUN_0034C400(generator,1)`; byte `2` calls it with zero. Every other byte
   makes no gate call.
2. Increment the cursor by one when it is below
   `command_start + command_count - 1`. The final byte is reread on every
   subsequent iteration; there is no wrap or automatic runner removal here.
3. If the generator pointer is nonzero, refresh each available anchor and
   publish its data to the generator.

`FUN_0034C400` at `0x0034C400..0x0034C418` writes the supplied byte to generator
`+0x34`; a nonzero value also clears generator byte `+0x35`. This is the direct
gate contract. What emitter updates subsequently do with those bytes is owned
by the particle-runtime investigation.

`FUN_001ABC70(manager,count)` repeats the whole runner-list update exactly
`count` times; count zero performs no runner update. After each list traversal,
it calls `FUN_0034FEA0` only when manager `+0x00` is nonzero. The direct command
loop therefore uses discrete byte-index steps, with gate update before anchor
publication. A command list ending in byte `1` repeatedly clears `+0x35`; an
ending byte `2` repeatedly writes a disabled gate. Neither effect is inferred
from a resource's name.

The update loop does not check command count zero before dereferencing the
cursor and does not check the generator pointer before calling the gate setter
for bytes `1`/`2`. Safe input and successful construction are preconditions for
those branches; this is a code observation, not evidence of a retail failure.

### Scene and bone anchors

**Observation, high confidence.** For the primary anchor,
`FUN_001AB470` refreshes the scene object's transform: a zero `+0x80` copies
its `+0x40..+0x7F` transform to `+0x00..+0x3F` and clears byte `+0x8D`;
otherwise it calls `FUN_0019C7C0`. `FUN_001AB460` returns object `+0x30`.
The update passes that address to `FUN_0034CA20(generator,position,0)`, extracts
a transform with `FUN_0010BF20`, zeros three translation components in the
extracted transform, and copies its `0x40` bytes into generator `+0x70..+0xAF`
through `FUN_001AB430`. The primary object therefore supplies both position
and a transform basis.

The primary setter `FUN_0034CA20` copies the supplied four-component position
to generator `+0xB0..+0xBF`, keeps a previous-position vector at
`+0xC0..+0xCF`, and sets byte `+0x1E5` to one. With the supplied third argument
zero, an already nonzero previous position is replaced with the old current
position; first-use handling chooses the new position when both stored vectors
have zero XYZ length. The secondary setter `FUN_0034CAF0` always copies old
`+0xF0..+0xFF` to `+0x100..+0x10F` before storing the supplied position at
`+0xF0..+0xFF`.

An anchor may be a scene child representing a bone, but the command
consumer itself reads a scene-object pointer; it performs no numeric bone-index
lookup. Object creation and hierarchy evaluation belong to
[Model runtime](model_runtime.md).

### Scheduling and owner gates

**Observation, high confidence.** There are two recovered resident update
callers of `FUN_001ABC70`, with different count contracts:

| Owner / call | Count and conditions |
| --- | --- |
| Animation scene, `FUN_001BB210`, call `0x001BB328` | Manager at scene `+0xF8`. After transform advancement through `FUN_001B8410`, passes `(new_time >> 8) - (old_time >> 8)` from unsigned 8.8 scene time `+0xEC`. Scene byte `+0xF7` bit `0x04` suppresses the call. Interpolation-transition early return also skips it. End-time clamping limits the count to frames actually reached. |
| Stream playback, `FUN_001A0120`, call `0x001A05F0` | Manager at play-context `+0x114`. After `FUN_001B4C60`, passes signed container halfword `+0x9C` directly when nonzero. Instructions `0x001A05D0..0x001A05F4` perform sign extension, not an 8-bit fixed-point shift. |

`FUN_001ABC70` instructions `0x001ABC88..0x001ABCEC` retain the argument and
compare an integer iteration counter with it using `sltu`; they perform no
fixed-point conversion. Consequently the streamed path's rate value `0x100`
means 256 manager iterations, whereas an animation advance of `0x100` normally
crosses one scene-frame boundary and requests one iteration. A negative streamed
rate is sign-extended into the unsigned comparison and requests a large unsigned
iteration count. These are static instruction contracts; no claim is made about
which authored action packets use that streamed path or its visible consequences.
The recovered call count is bounded resident-xref coverage, not a whole-program
absence proof. A direct-call byte search found no calls to `FUN_001ABBE0`,
`FUN_001ABC70`, `FUN_001ABD10` or `FUN_001BC680` in `BTL.BIN` or `ETC.BIN`;
indirect calls and other encodings are not excluded.

Animation stream event blocks are parsed later in `FUN_001BB210`, after the
action update. Its loop branch at `0x001BB454` calls `FUN_001ABD10`, which
disables each generator and resets each cursor to its command start through
`FUN_001AB680`; it does not recreate the generator. Backward seek
`FUN_001BB5C0` performs the same action reset before advancing from time zero.
Neither routine is itself proof of a wall-clock frequency.

### Removal and reset lifetime

**Observation, high confidence.** Animation binding `FUN_001B99B0` publishes
temporary scene lookup rows at each source record's `+0x34` while it constructs
objects and resolves anchors. At its `0x001BA6AC..0x001BA70C` action-manager
branch, scene byte `+0xF7` bit `0x04` suppresses action rebinding. Otherwise it
releases old runners with `FUN_001AB9F0`, obtains the action list from animation
descriptor `+0x04`, creates a `0x0C`-byte manager when needed, optionally replaces
its generator owner through `FUN_001ABA80` unless bit `0x08` is set, and creates
new runners through `FUN_001ABBE0`. Temporary record `+0x34` rows are cleared
at the end; the runner keeps the resolved scene pointers, not those temporary rows.

| Lifecycle operation | Direct effect |
| --- | --- |
| `FUN_001ABD10` / `FUN_001AB680` | Gate zero and cursor rewind; retain generator pointers and handles. |
| `FUN_001AB8E0` / `FUN_001AB4D0` / `FUN_001AB550` | For each live handle, call `FUN_00352C90`, clear state pointer/handle, free entry state and runner, and clear manager list. `FUN_00352C90` unlinks the generator from its owner and calls destructor `FUN_0034B780`. |
| `FUN_001AB9F0` / `FUN_001AB5A0` / `FUN_001AB620` | Call `FUN_00352DF0(owner,handle,2)`, clear runner pointer/handle, free entry state and runner, and clear manager list. The generator stays on the owner's list: the callee sets generator byte `+0x08` to `2`, `+0x35` to `1`, `+0x36` to zero, and `+0x198` to `3`. This is a deferred owner-state request, not immediate destruction. |
| `FUN_001AB740` | First uses the deferred runner-release path. Then destroys its private generator owner through virtual slot `+0x08`, or links that owner into the receiver returned by `FUN_00353330` when manager byte `+0x08` requests transfer and the receiver exists. Finally frees the manager when the destructor argument is positive. |

The explicit immediate-release scene wrapper is `FUN_001BC680`; normal binding
replacement uses the deferred path. Stream teardown `FUN_001A2280` destroys
play-context manager `+0x114` through `FUN_001AB740`. Stream restart
`FUN_0019FFC0` creates runners again from container `+0x58` but makes no preceding
runner-release call in its inspected body; `FUN_001ABBE0` starts writing at manager
`+0x04`. Therefore the restart's direct body must not be described as the
animation cursor-rewind operation. A full attribution of any older generator's
remaining owner lifetime is not established.

## Remaining boundaries

- The action-entry preserved dword `+0x0C` is not consumed by the inspected
  construction, command-update, anchor, reset, or runner-release family. It
  retains no established command meaning here.
- The runner command cases are fully bounded. The complete authored CCS corpus
  has not been walked to count command values, packet lengths or anchor
  combinations.
- Not every outer scheduling owner is established.
  [Scene playback owners](scene_playback_owners.md) and
  [Timer primitives](timer_primitives.md) own broader caller timing. No seconds,
  displayed-frame frequency, or universal pause contract is assigned here.
- Particle survival after the deferred removal request and the generator's
  internal use of anchor history remain owned by
  [Particle runtime](particle_runtime.md). Skeleton matrix evaluation remains
  owned by [Model runtime](model_runtime.md).
