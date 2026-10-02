# Particle and emitter runtime

This document investigates the particle and emitter runtime of retail NA2
(`SLPS-25837`): emitter construction, spawn and update algorithms, movement,
lifetime, force fields, drawing and destruction.

## Research coverage

- **Assigned scope:** Runtime emitter construction, spawn/update algorithms, movement, lifetime, particle parameters, draw behavior and destruction, including time sources and pause conditions.
- **Exploration depth:** Decompilation covers resident base/battle emitter construction and destruction, pool/resource reuse, spawn and velocity switches, fade states, all 34 force-field dispatch keys, transform/history composition, concrete visual update/draw routes, and recovered default/battle/scene manager callers. Instruction-level tracing covers the repeat loop's incoming register, preceding slot states and selected repeat-byte writers, and key 9's incoming scalar, field publication and selected resident descriptors. Disassembly or raw bytes corroborate consequential decompiler omissions.
- **Confirmed coverage:** A 0x220-byte base emitter owns a capacity-bounded array of 0xA0-byte particle elements and creates/reuses visuals at a circular cursor. Age, motion, fades and force fields use call counts; manager update and draw have separate gates. History publication also calls underlying sprite/scene playback under its own mode gates. The 0x280-byte battle extension shares these algorithms and supplies draw-environment, field and deferred-stop hooks. The repeat write uses a retained pointer whose initial value is manager scale on the recovered caller path; the selected constructors leave its gate disabled. Admitted key-9 nonzero mode consumes the current center-minus-visual X delta, while selected authored key-9 descriptors supply zero mode.
- **Unresolved or untested:** A positive repeat-byte producer and a reachable reactivation through the retained pointer, direct-mode publication for key 9, a selected nonzero authored mode, exact axis conventions in complex velocity branches, retail reachability of numeric selector combinations, and subtype-specific callers outside the recovered resident paths remain unresolved. Arbitrary pool combinations have not been shown reachable. No universal wall-clock rate or exhaustive game-wide particle-family inventory is established.
- **Deliberate exclusions and overlap:** Authored action packets and their anchors belong to [Effect-generator commands](../effect_generator_commands.md); resource parsing belongs to [CCS object types](../../game/files/ccs_object_types.md); draw-environment selection belongs to [Renderer and coordinate systems](renderer_coordinates.md#draw-environment-selection-and-streamed-exceptions); GS/VU submission belongs to [Render submission and buffers](render_submission.md). Complete-file evidence identities remain in [Retail game file identities](../../game/files/file_identities.md). [Puppet control](../../gameplay/characters/puppet_control.md) owns Sasori's caller relationships. This document owns shared runtime particle/emitter services and the selected field values needed to assess them, not authored packet interpretation or character-specific caller relationships.
- **Evidence limitations:** This is static evidence from retail `SLPS_258.37`, with a bounded `BTL.BIN` repeat-store search. Ghidra omits several leaf functions and misrepresents some R5900 vector/scalar arguments; raw bytes corroborate missing stubs. Immediate-offset store negatives do not exclude computed-address or bulk writes. Per-call age does not by itself establish wall-clock frequency.

## Evidence and address conventions

All addresses below are resident EE virtual addresses in retail
`SLPS_258.37`; see
[address conventions](../../game/files/file_identities.md#address-conventions).
`FUN_...` identifiers are preserved Ghidra labels, not recovered source names.
Field names here describe demonstrated reads/writes; unknown flag meanings
remain numeric.

## Construction and ownership

**Observation, high confidence.** `FUN_0034B720` allocates 0x220 bytes,
installs vtable `0x005DCA80`, initializes the embedded object at `+0x54` through
`FUN_0034A230`, and resets emitter fields through `FUN_0034A070`. The vtable's
RTTI pointer `0x005C8C88` names `ccGenerator2` at `0x005A6608`. Its force-field
vtable `0x005DCA50` resolves through `0x005C8CA8` to `ccForceField2`
at `0x005A6618`; the neighboring base descriptor names
`ccHigeParticleForceField` at `0x005A6630`.

`FUN_00352A10` packages four force-field descriptor pointers and delegates to
`FUN_00352A50`. That manager-side producer checks manager `+0x64 < +0x54`,
constructs an emitter, configures it through `FUN_0034BBB0`, adds the returned
particle capacity to manager `+0x64`, and registers it through `FUN_00352B10`.
The check precedes adding capacity; it does not clamp the new emitter to the
remaining manager budget.

`FUN_00352B10` appends an emitter to manager list head `+0x5C`; emitter
`+0x4C/+0x50` are previous/next links. It assigns emitter `+0x48` from manager
`+0x60`, advances that identifier source, and increments manager `+0x58`.
An already-registered emitter (`+0x48 != -1`) is returned without reinsertion.

### Emitter fields demonstrated by construction and update

| Emitter offset | Contract | Evidence |
| --- | --- | --- |
| `+0x04` | Integer update-entry age; reset to zero, incremented before emission. | `FUN_0034A070`, `FUN_0034C610` |
| `+0x08` | Lifecycle state: 0 running, 1 returns false immediately after particle processing, 2/3 return false when counted live visuals reach zero. | `FUN_0034C610` |
| `+0x0C`, `+0x64` | Head and count of linked force-field objects; their `+0x80/+0x84` are next/previous and `+0x88` is slot index. | `FUN_0034C1F0`, `FUN_0034C380` |
| `+0x10`, `+0x14` | Particle array pointer and allocated capacity. | `FUN_0034BBB0` |
| `+0x18`, `+0x1C` | Constructed-element count and circular spawn cursor. | `FUN_0034CF70` |
| `+0x20` | Count of live visuals with visual active byte `+0x80` set and alpha product above the function's positive threshold. | `FUN_0034C610` |
| `+0x34/+0x35` | Emission enabled/stopped bytes. Enabling `+0x34` clears `+0x35`; update emits only when enabled and not stopped. | `FUN_0034C400`, `FUN_0034C610` |
| `+0x37` | Enables distance-based suppression/fade processing relative to the supplied vector. | `FUN_0034C610` |
| `+0x38/+0x3C` | Linked resource-choice head and count, selected during each spawn. | `FUN_0034CF70` |
| `+0x48/+0x4C/+0x50` | Manager identifier, previous link, next link. | `FUN_00352B10` |
| `+0x150/+0x160` | Emitter scale/color vectors, multiplied by manager scale/color into `+0x1B0/+0x1C0`. Color alpha is the float at `+0x16C`. | `FUN_0034C610`, `FUN_0034F940` |
| `+0x180/+0x184` | Visual alpha-scale float and optional random-alpha bound; spawn copies the first to visual `+0x74` and samples the second into visual `+0x5C`. | `FUN_0034CF70` |
| `+0x188/+0x18C/+0x190/+0x194` | Distance suppression bounds and inner/outer alpha breakpoints; see the exact formulas below. | `FUN_0034A070`, `FUN_0034C610` |
| `+0x1D4` | Optional custom spawn operator, called virtually at slot `+0x08` for selector family 6. | `FUN_0034CF70` |
| `+0x1D8` | Optional draw-environment pointer selected for the particle draw loop. | `FUN_003530A0`, `FUN_0034A3B0`, binding slot `+0x20` |
| `+0x1DC..+0x1E4` | Optional per-particle 0x40-byte history-array configuration; allocated lazily at particle `+0x84`. | `FUN_0034CF70` |
| `+0x1E8..+0x21F` | Copy of 0x38-byte generator parameters, or resident defaults at `0x005C8CD0`. | `FUN_0034BBB0` |

### Pool sizing and lazy visual resources

`FUN_0034BBB0` copies the parameter descriptor, constructs each nonzero one
of four force-field descriptors as a 0x90-byte object, and replaces any old
particle array. Capacity argument `-1` requests an estimate from particle
lifetime `+0x1F4`, emission value `+0x200 / 30.0`, variation `+0x208`, and
fade increments derived from signed halfwords `+0x214/+0x216 / 2048.0`.
It clamps the estimate to at least one and rounds `(estimate + 15) & 0xFFF0`.
An explicit capacity skips this estimate. Capacity above 2000 reaches a
write to address zero in the inspected code, rather than a graceful clamp.

The allocation is `capacity * 0xA0 + 0x10`, initialized through
`FUN_00119380` with element constructor address `0x0034C070` and destructor
`0x0034B930`. Each slot initially has no visual at `+0x04` and no history
array at `+0x84`.

`FUN_0034CF70` operates on `array + cursor * 0xA0`, selects a linked resource
entry, and lazily creates a separate 0xA0-byte `ccParticle2` visual object
(vtable `0x005DCAC0`, RTTI `0x005C8E18`, name `0x005A6780`). That visual's
`+0x04` resource-kind selector chooses these underlying allocations:

| Runtime selector | Underlying allocation/construction | Reuse behavior |
| --- | --- | --- |
| 0 | 0x60 bytes, `FUN_001963F0` | Rebuilds when resource pointer changes. |
| 1 | 0xA0 bytes, `FUN_0019CD80` then `FUN_001952F0` | Rebuilds when resource pointer changes. |
| 2 | 0x120 bytes, `FUN_0019CD80`, embedded `FUN_001AA940`, then `FUN_001B7520`/`FUN_001B99B0` | Rebinds an existing object or restarts its playback state. |
| `0x12` | 0xB0 bytes, `FUN_0019CD80` then `FUN_00196B40` | Rebuilds when resource pointer changes. |

A differing selector destroys the old visual and history array before
construction. The same selector reuses its visual wrapper and resets the
particle element. Spawn increments and wraps cursor `+0x1C`; constructed
count `+0x18` is capped at capacity `+0x14`. Thus pool reuse is circular,
not a search for a free particle.

**Reset precision.** Pool setup writes element fade state `0xFF` and hold
zero explicitly at `0x0034BF74/0x0034BF78`; the callback at `0x0034C070`
only installs the element vtable and returns, as corroborated by resident
bytes; Ghidra defines no function there. On a selector change, spawn again
initializes those fields before constructing the replacement visual. On
same-selector reuse, `FUN_0034B220(element,1)` resets transforms, colors,
angular/history state and the one-draw skip, but does not write element
`+0x7E/+0x80`. Spawn separately replaces the hold at `0x0034D6B8` and
activates the selected visual at `0x0034D6C0`; nonzero fade parameters then
write state 1 or 3. With both fade parameters zero, this inspected reuse
continuation does not restore `0xFF`. A new visual's `+0x80/+0x81` and ages
start at zero in `0x0034C090`, another omitted function corroborated by bytes.

`FUN_0034CC80` allocates/appends 0x28-byte resource-choice nodes, assigning
their `+0x24` index from emitter `+0x3C`. The selector producers are
`FUN_0034C420` (0), `FUN_0034C4A0` (1), `FUN_0034C570` (2), and
`FUN_0034C500` (`0x12`). Node `+0x00` supplies the underlying resource,
`+0x04/+0x08` and `+0x0C/+0x10` carry two auxiliary resource pairs,
`+0x14` is the selector, `+0x18` carries playback configuration,
`+0x1C` is a byte option, and `+0x20` is next. `FUN_0034CF70` samples an
inclusive integer `0..count-1` through `FUN_00180210`, takes its integer
absolute value, and walks that many nodes. The RNG contract is owned by
[Resident randomness](../randomness.md).

### Battle particle generator extension

**Observation, high confidence.** `FUN_00349BA0` allocates 0x280 bytes and
constructs `ccHigeParticleGenerator` through `FUN_00349F60`: it first
initializes the `ccGenerator2` base, then installs vtable `0x005DCA20`
(RTTI `0x005C8CA0`, name `0x005A65F0`). It calls the same pool setup
`FUN_0034BBB0`, constructs supplied 0x90-byte fields with vtable
`0x005DCA60`, registers them, and initially disables emission.

`FUN_0034A530` constructs 0x14-byte resource descriptors at generator
`+0x220`, with count `+0x224`. `FUN_00349A80` enables/registers the generator
with the battle manager and either fills that resource array from the shared
resource catalog or converts an existing one through `FUN_0034A750` into
the same resource-choice nodes consumed above. The extension thus shares
pool, spawn, fade, integration and drawing algorithms.

Its pre-update slot `+0x10` is `FUN_0034A3B0`: it can refresh primary
position from `+0x270`, clears update byte `+0x264`, supplies a default draw
environment from the battle object `+0x2990` when generator `+0x230` is zero,
and publishes that environment at base `+0x1D8`
(`0x0034A408..0x0034A424`). Post-update `FUN_0034A440` refreshes
four cached field pointers at `+0x234`. `FUN_00349EA0` converts pending
extension word `+0x22C == 1` to stop state 2 and `== 2` to stop state 1,
clears the request, then invokes the ordinary manager update. Instructions
`0x00349ECC..0x00349F18` establish both state arguments: request 2 retains
`a2 = 1`, while request 1 explicitly loads `a2 = 2`.

Extension cleanup `FUN_0034A310` handles four externally held field slots
`+0x244/+0x254`, then destroys remaining fields through `FUN_0034C380`.
Destructor `FUN_0034A270` frees the extension resource array before freeing
the object. Particular effects' resource choices and caller semantics are not
covered here.

**Observation, high confidence.** The draw-environment binding slot `+0x20`
publishes differently in the two generator classes. Both vtables use empty
`+0x18/+0x1C` hooks at `0x0034A980/0x0034A990` (`jr ra; nop`).

| Generator vtable | Environment-binding publication |
| --- | --- |
| Base `ccGenerator2`, `0x005DCA80` | Slot `+0x20` points to `0x00352EE0`; bytes show `sw a1,0x1D8(a0); jr ra; nop`. Binding immediately changes the value used by the draw loop. |
| Battle `ccHigeParticleGenerator`, `0x005DCA20` | Slot `+0x20` points to `0x002A8DE0`; bytes show `sw a1,0x230(a0); jr ra; nop`. The pre-update method above later copies `+0x230` to `+0x1D8`, substituting battle-owner `+0x2990` when `+0x230` is zero. |

A virtual binding call alone therefore does not establish immediate `+0x1D8`
publication for the battle extension. The scene action wrapper `FUN_001ABD60`,
at `0x001ABD78..0x001ABD90`, obtains the current draw environment through
`FUN_0010DAE0`, passes it to each emitter's binding slot through
`FUN_00352E80`, then draws the manager.

## Stop and destruction

**Observation, high confidence.** `FUN_0034C610` increments emitter age,
emits, counts existing live visuals, advances particles through
`FUN_0034FAF0`/`FUN_0034FA60`, and then evaluates emitter lifetime. A finite
signed halfword at `+0x1EC` expires when `age > lifetime` (strict comparison);
`-1` disables that limit. Expiry writes state 2, stops emission at `+0x35`,
clears `+0x36`, and selects emitter fade state 3 at `+0x198`.
States 2 and 3 retain the emitter until its `+0x20` count is zero.
The count is computed before that call's particle advancement, so it is not
a post-update census.

`FUN_00352DF0` requests a state change by manager/emitter identifier. Every
nonzero requested state stops emission; state 2 also clears particle-repeat
byte `+0x36` and sets fade state 3. `FUN_00352C90` unlinks one emitter,
subtracts its capacity from manager `+0x64` (clamped at zero), destroys it,
and decrements emitter count `+0x58`. `FUN_00352D70` performs that capacity
accounting and destruction over the whole emitter list and clears its head/count.

`FUN_0034B780` resets/unlinks resources through `FUN_0034CDA0`, invokes
vtable slot `+0x0C` (`FUN_0034C380`) to destroy all force-field objects,
destroys each constructed particle visual through its virtual cleanup and
destructor, frees each history allocation, destroys/frees the particle array,
frees optional `+0x1D4`, and calls the emitter destructor at vtable `+0x08`.
`FUN_0034BA20` dispatches underlying visual destruction by selector 0/1/2/`0x12`.

The emitter vtable's slots `+0x10/+0x14` point to `0x0034FFC0/0x0034FFB0`.
Ghidra has no functions at those addresses; bytes show both are `jr ra`
with a zero delay-slot instruction. They are empty hooks, not the particle
update or draw implementation.

## Emission, particle lifetime and update ordering

**Observation, high confidence.** `FUN_0034CE00` emits only when there is a
resource choice (`+0x3C != 0`) and emission mode byte `+0x19A != 1`.
If integer delay `+0x2C` is nonzero, it increments `+0x30`, returns while
`counter <= delay`, then resets the counter. An eligible call adds
`rate(+0x200) / 30.0` to accumulator `+0x24` and spawns its truncated integer
part. The positive integer part is subtracted afterward, preserving the
fractional remainder. Low nibble 1 of parameter byte `+0x1E8` instead spawns
the truncated rate itself once and sets emission-stop byte `+0x35`.

These are call-count contracts. The `30.0` divisor is present in emission and
capacity estimation; it does not prove that every caller invokes the manager
30 times per second.

### Fade and hold states

`FUN_0034FAF0` visits every constructed pool element. Particle element
`+0x7E` is the fade state, `+0x5C` its alpha multiplier, and `+0x80` its
integer hold count. Generator halfwords `+0x214/+0x216` are signed fade-in
and fade-out increments divided by 2048.0.

| State | Operation in one call |
| --- | --- |
| 0 | Set alpha to zero and enter 1. |
| 1 | Add fade-in increment, clamp above 1, enter 2 at alpha >= 1. |
| 2 | Decrement hold count; below zero enter 3 when fade-out increment is nonzero, otherwise enter 4. |
| 3 | Subtract fade-out increment, clamp below zero, enter 4 at alpha <= 0. |
| 4 | Enter 5 and clear visual active byte `+0x80`. |
| 5 | Emitter repeat byte `+0x36` can restart state 0 and resample hold lifetime. The visual reactivation write uses retained register `s2`; see the limitation below. |
| `0xFF` | Clear the visual active byte when hold count is negative; this branch does not decrement that count. |

Spawn sets visual active and samples hold lifetime as
`L - integer_conversion(L * abs(FUN_001802B0(variation)))`, where `L` is
signed halfword `+0x1F4` and variation is float `+0x208`. The repeat path
uses the same expression. The absolute-value helper `FUN_0016E6F0` clears
the double sign bit after float-to-double conversion; variation is a
reduction for positive `L`, not a symmetric addition/subtraction. The RNG
itself is described in [Resident randomness](../randomness.md).

Spawn chooses state 1 with alpha 0 when fade-in is nonzero, otherwise state
3 with alpha 1 when fade-out is nonzero. With both zero, it leaves the
element's fade state unchanged: a newly initialized slot has `0xFF`, while
same-selector reuse retains its prior state as described above. Emitter
fade state `+0x198 == 3` promotes only particles still in `0xFF` to 3;
`+0x198 == 0` promotes `0xFF` to 1. It does not forcibly replace every
particle's existing fade state.

### Retained repeat pointer and its incoming owner

**Observation, high confidence.** The complete instruction listing for
`FUN_0034FAF0` initializes `s4` to the emitter and `s3` to pool index zero at
`0x0034FB10..0x0034FB18`; it saves incoming `s2` but does not initialize it.
The loop recomputes `s1 = emitter[+0x10] + index * 0xA0` and visits indices
in ascending order below constructed count `+0x18`. States 0/1/2/3 do not
write `s2`. State 4 changes the element to state 5 and loads its visual into
`s2` at `0x0034FD50`; negative-hold state `0xFF` loads its visual at
`0x0034FE00`. Both loads occur before their null checks. Thus even a null
visual replaces the retained pointer on those branches.

State 5 with repeat byte `+0x36 != 0` sets the current element to state 0,
resamples its hold count, and writes active byte 1 through retained `s2` at
`0x0034FDDC`, without reloading the current element's visual or checking the
retained pointer. The hold store at `0x0034FDE0` still targets the current
element. Register retention spans earlier slots within this invocation; the
callee restores incoming `s2` on return, so it does not retain the preceding
invocation's last visual. The `0xFF` branch only checks a negative hold and
disables its visual; only state 2 decrements the hold in this routine.

**Observation, high confidence for the recovered caller.**
`FUN_0034C610` sets its own `s2` from argument `a3` at `0x0034C63C`, reads
that pointer as a manager scale vector at `0x0034C698`, and calls
`FUN_0034FAF0` at `0x0034C938` without replacing it. Before the first state-4
or negative-`0xFF` load in a fade invocation, the repeat write therefore uses
this incoming scale-vector pointer on this caller path. The manager sets
`a3 = manager + 0x20` at `0x0034FF00`; if the repeat gate admits that first
write, its effective address is `manager + 0xA0`, beyond the recovered
0x70-byte manager allocation. After a disabling-slot load it
uses the most recently visited disabling slot's visual, which may differ
from the current repeating slot. The loop has no active-visual admission
check of its own.

### Repeat producers and the reachability boundary

**Observation, high confidence.** The identified emitter-byte producers are
all disabling writes. Reset `FUN_0034A070` stores zero to `+0x36` at
`0x0034A0B0`. Finite emitter expiry clears it at `0x0034C9E0`, after that
call's particle fade processing. Manager state request 2 clears it at
`0x00352E64`; other nonzero state requests stop emission without that clear.
The base construction route `FUN_00352A50 -> FUN_0034B720 -> FUN_0034BBB0`
and battle route `FUN_00349BA0 -> FUN_00349F60 -> FUN_0034BBB0` both include
the reset and do not enable repeat in their inspected continuations.
`FUN_0034C400` and battle registration `FUN_00349A80` enable emission and
clear its stop byte; they do not enable repeat. Copying the 0x38-byte
generator descriptor to emitter `+0x1E8` does not cover emitter `+0x36`.

Byte searches for all four high-byte forms of `sb register,0x36(base)`
in the resident program found only those three emitter writes after inspecting
the other physical-address matches; the other matches belong to unrelated
objects. The corresponding four `BTL.BIN` searches found no matches. Aliased
memory matches were not counted as separate writers. This is a bounded
immediate-offset byte-store result, not a census of every way to write the
byte.

**Inference, bounded to those construction paths.** Fresh emitters retain a
zero repeat gate until some additional writer changes it, so reaching state 5
alone does not reach the retained-pointer write. Within an admitted fade
invocation, a preceding state-4/negative-`0xFF` slot replaces the incoming
manager pointer; otherwise it remains the initial write base. Circular spawn
occurs before this fade pass and can reinitialize the visited slot's state,
so a pool ordering abstracted from the spawn schedule is insufficient to
prove either a wrong visual reactivation or an out-of-object write.

**Evidence limit.** No positive emitter-repeat producer
was established. Computed-address/bulk writes, other subtype callers, and an
actual ordered pool population before its next respawn remain unresolved.
The complete retained-register contract and the state-5 gate are confirmed;
neither a correct per-particle restart nor a reachable retail failure follows
without that producer and scheduling evidence. Bytes
`0x0034FD68..0x0034FE17` corroborate the repeat/negative-hold continuation,
and the jump table at `0x005C8DD0` corroborates all seven state targets.

### Manager gates and call sequence

`FUN_0034FEA0` returns without updating when manager byte `+0x51` is zero.
When enabled, each emitter receives this sequence:

1. Virtual pre-update slot `+0x10`.
2. `FUN_0034C610`: age, emission, live count, emitter-vector products,
   particle fades, force-field updates, emitter stop decision.
3. `FUN_003500F0`: force-field dispatch over eligible particles.
4. `FUN_0034F940`: compose particle transform/scale/color, advance visual.
5. Virtual post-update slot `+0x14`.
6. Remove the emitter through `FUN_00352C90` if step 2 returned false.

Manager `+0x50` tells step 2 whether the supplied manager vector has changed;
after visiting any emitter, the manager clears it. Base `ccGenerator2`
pre/post hooks are the empty stubs documented above. This function has no
elapsed-time/delta-time argument.

`FUN_0034F940` multiplies element scale vector `+0x30` and color vector
`+0x50` by emitter products `+0x1B0/+0x1C0`, calls `FUN_0034B310`, then calls
the active visual's slot `+0x0C`. `FUN_0034B310` composes accumulated
translation/rotation and color/scale through `FUN_0034AF00`. Its history
loop copies slot `i-1` to `i` for `i = used_count-1` down through 1, then
stores a 0x40-byte visual snapshot at the head and increments/clamps used
count to capacity. Thus the newly counted tail slot is not filled by that
call's shift while the count is still growing. History distance scalar `+0x90`
optionally caps each older position's distance from the head to
`distance * history_index`. The element accumulators are then cleared by
`FUN_0034B220(element, 0)`.

**Instruction corroboration.** `FUN_0034F940` at
`0x0034F9A4..0x0034F9B4` multiplies element color by the emitter product;
`FUN_0034B310` at `0x0034B34C..0x0034B35C` multiplies that argument by the
element color again. The final visual color is therefore
`element_color * element_color * emitter_product`, componentwise on this
path. In particular, element alpha is squared before the visual alpha-scale
`+0x74` is applied by `FUN_0034B070`. The live-count comparison earlier in
`FUN_0034C610` uses the unsquared element/visual alpha product.

### Caller scheduling and suppression

The resident manager constructor `FUN_001ABB60` initializes a 0x70-byte
manager with capacity budget 2000, no emitters, update/draw bytes both 1,
zero manager position/reference vectors, and unit scale/color vectors.
Its vtable `0x005D9F50` resolves through RTTI `0x005BF9F0` to name
`ccParticleManager` at `0x003FB850`.
Battle initializer `FUN_00353350` constructs that base and replaces its
vtable with `0x005DCAF8`, naming `ccHigeParticleManager` through RTTI
`0x005C8E30` and string `0x005A8EF0`. It also builds the battle resource
catalog used by `FUN_0034A530`. Catalog authorship belongs to
[Asset dependency graphs](../../game/files/asset_dependencies.md).

| Caller | Update/draw and scheduling contract |
| --- | --- |
| Render-phase routine `FUN_00108490`, instructions `0x001084A0..0x00108508` | When renderer byte `+0x192 & 7` is zero, steps resident manager `0x0061AF80`, steps a returned detached-manager list through `FUN_00352F60`, then draws the default manager and detached list. The same nonzero engine gate skips all four operations. |
| `FUN_00352F60` | For each detached manager, destroy it when its emitter count `+0x58 == 0`; otherwise call `FUN_0034FEA0`. Rendering the list separately uses `FUN_003530A0`. |
| Battle first phase `FUN_00309190` | If the battle manager at `gp-0x32E8` is nonzero, call extension manager update `FUN_00349EA0`. The phase dispatcher controls whether this wrapper is called. |
| Battle second phase `FUN_003091E0` | Publish the current view/reference vector at manager `+0x40`, then draw through `FUN_0034FFD0` when that battle manager exists. |
| Standalone owner `FUN_003AB220`, `FUN_003AB340`, `FUN_003AB370` | Allocate the same 0x70-byte battle manager at owner `+0x04`; separate owner callbacks invoke extension update and ordinary draw. |
| Scene action manager `FUN_001ABC70` | For each requested iteration, update authored action runners first, then call particle-manager update only when manager owner `+0x00` is nonzero. A zero owner uses the separately stepped resident default manager. |
| Scene action draw `FUN_001ABD60` | When manager owner `+0x00` is nonzero, propagate the draw environment through `FUN_00352E80`, then draw that particle manager. |

The scheduler places `FUN_00108490` after its cooperative task barrier;
[Task system](../task_system.md#manager-pass-and-ordering-boundary) owns that
ordering. This establishes one default-manager invocation per eligible
render-phase call, not a universal clock rate for every particle manager.

Battle phase mask bit 7 controls the first/second wrappers above and writes
default-manager bytes `0x0061AFD1/0x0061AFD2` (manager `+0x51/+0x52`). The
mask producer, pause-controller relationships and exceptions belong to
[Pause and replay](../../gameplay/session/pause_and_replay.md#selective-update-gating).
Thus update suppression and draw suppression are distinct; the emitter
itself contains no battle-pause query.

[Effect-generator scheduling](../effect_generator_commands.md#scheduling-and-owner-gates)
owns the two recovered scene-action callers and their different iteration-count
units; this document does not convert either into seconds.

### Distance suppression and alpha processing

When emitter byte `+0x37` is set, `FUN_0034C610` measures distance `d`
from each visual position to the manager reference vector `+0x40`.
Distances below emitter `+0x188` or above `+0x18C` set visual suppression
byte `+0x81`; inclusive bounds clear it. Within those bounds, element alpha
`+0x5C` is multiplied by these exact ratios:

| Condition | Multiplier |
| --- | --- |
| `d < emitter[0x190]` | `(emitter[0x188] - d) / (emitter[0x190] - d)` |
| Otherwise, `d > emitter[0x194]` | `(emitter[0x18C] - d) / (emitter[0x194] - d)` |
| Otherwise | 1 |

Reset defaults are 50, 5000, 400 and 4000 at those four offsets.
Instructions `0x0034C75C..0x0034C774` and `0x0034C790..0x0034C7A8`
corroborate the subtraction order: the default near/far intervals can yield
negative alpha multipliers. No clamp is inserted by this routine. The live
census follows this processing and compares visual-alpha times element-alpha
against the positive float threshold encoded as `0x01800000`; visual draw
suppression itself is checked later by `FUN_0034B5A0`.
The descriptor producers for these floats belong to
[Effect-generator commands](../effect_generator_commands.md).

## Drawing and history

**Observation, high confidence.** `FUN_003530A0` walks the manager list and
draws only managers with byte `+0x52 != 0`. Each emitter gets virtual slots
`+0x18/+0x1C` around its constructed particle loop. Emitter `+0x1D8` can
temporarily replace the selected draw environment `0x006073F4` for this loop;
the selection and restoration conditions are in
[renderer coordinates](renderer_coordinates.md#particle-environment-overrides-and-nested-scene-cameras).

A particle with element byte `+0x7D != 0` is skipped once and has that byte
cleared. Otherwise `FUN_0034B5A0` requires a nonzero visual, active visual
byte `+0x80`, and clear visual suppression byte `+0x81`. Without history it
calls visual slot `+0x10` once. With history it walks snapshots oldest to
newest, restores position, rotation, scale and color from each 0x40-byte
record, weights snapshot alpha by `1 - index / history_capacity`, updates
underlying color through `FUN_0034B070`, and calls the same draw slot for
each snapshot. This outer draw wrapper does not step its emitter age,
particle age or velocity.

The scale snapshot stores/restores visual base scale `+0x30`; the publication
routine reads composed scale `+0x40`. History drawing does not call
`FUN_0034AF00` to recompute that composed scale. Thus the restored base-scale
record alone does not establish a different submitted scale per snapshot.

The one-draw skip byte is set during full element reset
`FUN_0034B220(element, 1)` and also controls whether update composition uses
the emitter vector or the resident identity/default vector at `0x005C8D20`.
The concrete resource-family dispatch is recorded below; GS/VU submission
belongs to the renderer document.

### Concrete visual update and draw

The `ccParticle2` vtable `0x005DCAC0` assigns update slot `+0x0C` to
`FUN_0034AFF0`, draw slot `+0x10` to `FUN_0034B6F0`, and the resource-frame
hook `+0x18` to `FUN_0034B060`. The base vtable `0x005DCAE0` supplies
`FUN_0034AB30` and `FUN_0034AD60` for the latter resource operations.
`FUN_0034B6F0` checks the active byte before calling `FUN_0034AD60`.
Bytes at `0x0034B060` show `jr ra`/zero delay slot: that overridden
resource-frame hook is empty.

`FUN_0034AFF0` increments visual `+0x84/+0x88` by one, adds velocity vector
`+0x90` to visual position `+0x10`, publishes color through
`FUN_0034B070`, and calls slot `+0x18`. No elapsed-time factor intervenes.
`FUN_0034AB30` handles selector-2 scene animation through
`FUN_001BB210`/`FUN_001BB6F0` according to byte `+0x70`. Mode 0 skips
advancement; mode 1 advances until the last scene frame; mode 2 can rewind
and advance again near the end. The scene's `+0xFC` presence and time gates
also apply. For selector-0 sprites, any nonzero mode increments and clamps
visual frame index `+0x0C` to `0..underlying_frame_count-1`. Mode 2 first
resets an already out-of-range index to -1; the ordinary final-frame value
does not by itself trigger that reset.

The resource-frame routine is a direct call inside `FUN_0034B070`, before
that routine publishes transforms, colors and alpha. Consequently every
history snapshot's draw-side publication also invokes that playback routine
under its mode gates. It does not increment the outer visual's age or move
it by velocity, but it can advance the underlying resource. An eligible
selector-2 scene step can also reach its own action/particle manager through
`FUN_001ABC70`, whose owner and iteration gates are recorded above.
For selector 0, the routine packs RGB as truncated component values times
128 into three bytes and supplies alpha as visual `+0x5C * +0x74`.
Selectors 1/2/`0x12` receive transforms and that alpha through their
underlying draw-object setters.

`FUN_0034AD60` sends selector 2 to scene draw `FUN_001BB790`, selector 0
to sprite draw `FUN_00195A90`, selector `0x12` to `FUN_00190F40`, and
selector 1 to `FUN_00194180`. Selector 0/`0x12` byte `+0x7C` enables
additional render-state setup before those calls. This establishes the
visual consumer families, not every GS/VU primitive produced beneath them;
[Render submission and buffers](render_submission.md) owns that lower layer.

## Spawn geometry and velocity

**Observation.** `FUN_0034CF70` dispatches the high nibble of generator byte
`+0x1E8` after constructing/rebinding its selected visual. The low nibble
also controls emission mode. Generator byte `+0x1E9` bit 4 is passed as the
extra manager-vector option to the geometric helper; its low nibble selects
the later velocity algorithm. Attachment origin resolution remains owned by
[Effect-generator commands](../effect_generator_commands.md).

| High nibble | Spawn route observed in `FUN_0034CF70` |
| --- | --- |
| 0, 7 | `FUN_0034EF80` with zero radius, planar option. |
| 1 | `FUN_0034EF80` with sampled radius, planar option. |
| 2, 3, `0xB` | `FUN_0034EF80` with sampled radius, spatial option. |
| 4 | `FUN_0034F570` with zero radius. |
| 5, `0xC` | `FUN_0034F570` with sampled radius and origin addition enabled. |
| 6 | Optional custom operator at emitter `+0x1D4`, virtual slot `+0x08`. |
| 8 | `FUN_0034EF80` with twice sampled radius, planar option. |
| 9, `0xA` | `FUN_0034EF80` with twice sampled radius, spatial option. |
| `0xD..0xF` | No geometric case in this inspected switch. |

`FUN_0034EF80` starts at the resolved primary origin, generates a random
angle and rotates the resident unit vector, scales it by the supplied radius,
and adds it to the origin. Its spatial option uses two angles; the planar
option uses one. It writes visual position and element angular state
`+0x70/+0x74/+0x78`. This is an angular sampling algorithm; a uniform
surface/volume distribution is not established.

`FUN_0034F570` uses the primary and secondary origins. Velocity selectors
3/10 place the point along their separation using `cursor / capacity`, with
the cursor already incremented/wrapped by this spawn. Other selectors use
`abs(FUN_001802B0(separation_length))` along the normalized separation and
can add a random planar radial offset. Instructions `0x0034F694..0x0034F798`
recover the missing scalar argument: length is computed in `f12`, remains
there until the RNG call, and its result passes through the absolute-value
helper before scaling the normalized vector. This establishes the sampling
operation without claiming a uniform continuous distribution.

`FUN_0034E3E0` constructs visual velocity `+0x90`. Angular base halfwords
`+0x1F8/+0x1FA` and spread halfwords `+0x210/+0x212` convert to radians
with `pi / 32768`. Speed comes from `+0x1FC`, with variation `+0x20C`.
It selects on low nibble `+0x1E9`:

| Selector | Demonstrated velocity family |
| --- | --- |
| 0, 5, `0xD..0xF` | Default angle-derived normalized direction transformed by emitter basis, scaled by sampled speed. |
| 1, 8 | Outward from primary origin to spawned visual, with basis handling and sampled-speed branch. |
| 2, 9 | Inward from spawned visual to primary origin, normalized/scaled. |
| 3, 10 | No vector-producing branch here; these selectors are used by the two-origin spawn helper. The stack-vector result is not safely named from this decompilation. |
| 4 | Random-angle path, then the selector-6 basis/direction path. |
| 6 | Angle/basis-derived direction, normalization and speed scaling. |
| 7, `0xC` | Two angle matrices composed with emitter basis, then scaled unit vector. |
| `0xB` | Two random angles composed with emitter basis, then scaled unit vector. |

**Evidence limitation.** R5900 vector pseudo-operations and missing scalar
arguments make the exact axis convention and distribution of the more
complex velocity branches incomplete. The writes, branch set and per-call
integration are established; descriptive names such as a particular authored
cone/sphere mode are not recovered source names.

## Force-field consumer table

**Observation, high confidence for dispatch and fields.** `FUN_003500F0`
visits enabled emitter force fields (field byte `+0x04 != 0`) in linked-list
order. It searches all 34 eight-byte entries at
`0x005A6650..0x005A675F` by field selector byte `+0x52`. Each entry contains
an integer selector and function pointer. Particle eligibility requires a
nonzero active visual and element fade state other than 4. The dispatcher
computes field center `+0x70 = +0x20 + +0x10`, compares visual distance
strictly below the field radius, and calls the selected handler with element,
field and emitter. A zero radius on field byte `+0x51 == 1` uses float max
as the bound; other mode values use float max directly.

The table has keys 0..`0x21`. The inspected consumer does not check whether
the search exhausted all 34 entries before reading the function pointer.
This is a bounded dispatch observation, not evidence that malformed selectors
occur in retail assets.

| Key(s) | Handler address | Consumer behavior |
| --- | --- | --- |
| 0 | `0x00350320` | Add displacement to element `+0x10`; flag bit 0 selects velocity-scaled form. |
| 1 | `0x00350410` | Add field vector to visual velocity, or use the velocity-direction variant and element correction `+0x40`. |
| 2 | `0x003505E0` | Orbit-like position correction using element angular state `+0x78`, center and field angular increment. |
| 3 | `0x00351140` | Increment/wrap visual Euler rotation `+0x20` for resource selector 1. |
| 4, `0x15` | `0x00351280` | Add distance-weighted field vector to element correction `+0x40`. |
| 5 | `0x00351340` | Age-based scalar scale and aspect adjustment into element `+0x30`. |
| 6 | `0x003514C0` | Age-based interpolation stored in element scale X `+0x30`; no Ghidra function; bytes `0x003514C0..0x0035154B`. |
| 7 | `0x00351550` | Parallel age-based interpolation stored in scale Y `+0x34`; no Ghidra function; bytes `0x00351550..0x003515DB`. |
| 8 | `0x00351840` | Replace/multiply element scale using field vector and visual scale/aspect. |
| 9 | `0x00351960` | Alternating linear scale cycle from visual age and a half-period when its mode converts to zero; nonzero mode skips scalar computation and uses incoming `f1`, as detailed below. |
| `0xA`, `0x1B` | `0x00351C10` | Add signed angular increment `field+0x54 * pi/32768` to element `+0x24`, wrapping near +/-pi. |
| `0xB`, `0x1C` | `0x00351CC0` | Set that element angle directly from the signed halfword. |
| `0xC`, `0x1D` | `0x00351D10` | On visual age zero, copy field vector `+0x60` to element rotation `+0x20`; no Ghidra function; bytes through `0x00351D2B`. |
| `0xD`, `0x1E` | `0x00351D30` | Add a position-derived correction to element `+0x10`; scalar uses signed angular halfword conversion. |
| `0xE` | `0x00351DD0` | Age-driven multi-phase alpha envelope into element `+0x5C`, with optional modulo period. |
| `0xF`, `0x20` | `0x00352220` | Rotate an element center-relative offset by the signed field angle and add the difference to displacement. |
| `0x10` | `0x00352580` | Constrain visual position inside/outside a radius from the emitter's resolved origin, selected by field scalar. |
| `0x11` | `0x003503F0` | Add field vector `+0x60` directly to element displacement `+0x10`; no Ghidra function; bytes through `0x00350407`. |
| `0x12` | `0x003505C0` | Add field vector directly to correction `+0x40`; no Ghidra function; bytes through `0x003505D7`. |
| `0x13` | `0x00350C20` | Three-dimensional orbit correction from stored offset/angular state; also rotates visual velocity. |
| `0x14` | `0x00351260` | Add field vector directly to element rotation `+0x20`; no Ghidra function; bytes through `0x00351277`. |
| `0x16` | `0x003515E0` | Apply the X/Y scale handlers and corresponding Z scale increment. |
| `0x17` | `0x003516E0` | Initialize/move X scale toward configured terminal value using visual age. |
| `0x18` | `0x00351790` | Parallel Y scale operation. |
| `0x19` | `0x00351950` | Copy field vector `+0x60` to element scale `+0x30`; no Ghidra function; bytes through `0x0035195F`. |
| `0x1A` | `0x00351AF0` | Alternate positive/negative scale steps between visual-scale thresholds; element byte `+0x7C` stores direction. |
| `0x1F` | `0x00352100` | Four-duration periodic alpha phases stored at element `+0x5C`; no Ghidra function; bytes through `0x0035221B`. |
| `0x21` | `0x003528E0` | Radial displacement inside field radius, weighted by `1 - distance/radius`. |

Field byte `+0x05` chooses between values at `+0x60..+0x6F`
and direct values beginning `+0x30`. Their construction sources are recorded
below. Several handlers use
visual age `+0x88`; angular increments use `pi/32768` and scale/alpha
increments are applied once per dispatch call. No handler inspected here
takes a delta-time argument. Exact authored meanings of field bytes belong
to the generator-command/resource owners, not this runtime table.

`FUN_0034FA60` updates enabled field objects through virtual slot `+0x0C`
and refreshes their manager-vector anchor when manager byte `+0x50` is set.
The base field's slot points to `0x0034A9A0`; bytes show an empty
`jr ra`/zero-delay-slot hook. Field handling above is separate from that hook.

### Force key 9 and the incoming scalar

**Observation, high confidence.** `FUN_00351960` converts direct mode
float `+0x3C` or derived mode float `+0x6C` through `cvt.w.S`.
Nonzero results branch from `0x00351984` or `0x00351A24` to
`0x00351AAC`, skipping every local assignment of `f1`; the common vector
construction at `0x00351ABC` consumes that incoming register. Zero mode
computes a triangular scale between floats `+0x30/+0x34` (or `+0x60/+0x64`)
using visual age divided by half of the converted period `+0x38` (or `+0x68`).

The recovered force dispatcher supplies a concrete incoming value. At
`0x0035021C..0x00350228` it subtracts visual position from field center
`+0x70` into its stack vector. `0x00350230` loads that vector's X component
into `f1`; the following `madda.S f1,f1` updates the scalar accumulator,
and the remaining distance/radius comparison changes `f0`, not `f1`.
There is no intervening call before `jalr` at `0x00350278`. Thus admitted
key-9 nonzero mode on this path scales the resident vector at `0x005C8D10`
by `field_center_x - visual_position_x`, then writes W explicitly as 1 and
stores it to element scale `+0x30`. Resident data at that vector confirms
`(1,1,1,0)`, so the stored result is `(delta_x,delta_x,delta_x,1)`.
It is not dependent on a preceding
field handler's leftover scalar because each admitted particle recomputes
and reloads its own delta. Direct byte `+0x05 != 0` and derived byte zero
select the two mode sources, but share this continuation.

The dispatcher admission still requires field `+0x04 != 0`, a nonzero active
visual, element state other than 4, and distance strictly below its selected
bound. It does not require a nonzero X delta or constrain the sign of that
delta. Bytes at table entry `0x005A6698` confirm key 9 and pointer
`0x00351960`. A resident search for the exact direct `jal` encoding found
no matches; this does not exclude other indirect routes.

### Selected key-9 field publication and authored values

**Observation, high confidence.** Base setup `FUN_0034BBB0` initializes field
byte `+0x05` to zero, clears direct vector `+0x30`, then copies a supplied
0x20-byte descriptor to field `+0x50` at `0x0034BCE8`. Battle field
construction `FUN_00349BA0` uses `FUN_00349E10` for the same initialization
and copies the descriptor at `0x00349CD4`. Both routes enable field `+0x04`
after publication. Thus descriptor byte `+0x02` becomes dispatch key
`+0x52`, and descriptor floats `+0x10/+0x14/+0x18/+0x1C` become the
zero-byte-`+0x05` consumer's start/end/period/mode at
`+0x60/+0x64/+0x68/+0x6C`. They are copied authored values at construction,
not necessarily a vector recomputed each update. Both base/battle field
update vtables point to the empty hook `0x0034A9A0`.

The nonzero-byte-`+0x05` path instead reads direct vector
`+0x30/+0x34/+0x38/+0x3C`. Its four values start at zero in these
constructors. Neither this copy nor emitter emission enable sets the direct
selection byte. A concrete key-9 direct-value writer and selection-byte
producer remain unresolved; writing a direct vector alone does not establish
that the handler selects it.

Selected resident descriptor bytes establish these numeric zero-mode inputs:

| Descriptor address | Key | Start / end / period / mode | Derived half-period |
| --- | --- | --- | --- |
| `0x004F0B80` | 9 | `1.5 / 3.0 / 20.0 / 0.0` | 10 |
| `0x004F0BE0` | 9 | `1.0 / 3.0 / 10.0 / 0.0` | 5 |
| `0x00580030` | 9 | `1.4 / 1.48 / 8.0 / 0.0` | 4 |
| `0x005800D0` | 9 | `1.5 / 1.8 / 8.0 / 0.0` | 4 |
| `0x005A7AD0` | 9 | `0.5 / 1.0 / 15.0 / 0.0` | 7 |
| `0x005A7B30` | 9 | `0.5 / 1.0 / 10.0 / 0.0` | 5 |
| `0x005A7B50` | 9 | `0.8 / 1.7 / 50.0 / 0.0` | 25 |
| `0x005A7BD0` | 9 | `1.0 / 2.0 / 30.0 / 0.0` | 15 |
| `0x005A7E10` | 9 | `0.01 / 1.0 / 16.0 / 0.0` | 8 |
| `0x005D5650` | 9 | `0.5 / 1.5 / 20.0 / 0.0` | 10 |

The displayed decimals describe the inspected single-precision values. All
ten mode dwords are exactly zero; these examples do not admit the nonzero
mode branch. For a nonnegative age and positive half-period `H`, the zero-mode
instructions use `q = age / H`, `r = age % H`, replacing `r` with `H-r`
when `q` is odd, then store uniform XYZ scale
`start + r * (end-start) / H`, with W 1. Half-period uses signed integer
division by two after converting the period float. Consequently the selected
15.0 period produces a 14-call arithmetic cycle, not a 15-call cycle; this
does not assign seconds to those calls.

**Observation with a selector boundary.** `FUN_00353790` returns
`0x005A7480 + signed_byte(index) * 0x38`. The source table's field-index
halfwords at row `+0x30` identify field 12 in preset 3
(`0x005A7528`, indices `11,12,-1,-1`), and field 16 in presets 6 and 11
(`0x005A75D0`, `16,27,-1,-1`; `0x005A76E8`, `16,-1,-1,-1`). The recovered
construction continuation `0x0031B380..0x0031B3E4` maps each nonnegative
field index to `0x005A7950 + index * 0x20` and supplies the resulting
pointers to `FUN_00349BA0`. Field indices 12 and 16 therefore identify the
key-9 descriptors at `0x005A7AD0` and `0x005A7B50` under that publication mechanism.
That particular inspected caller selects preset 1; it does not itself prove
selection of presets 3, 6 or 11. Their concrete caller/gate selection is
unresolved.

**Evidence limit.** Arithmetic and these publication sources are confirmed;
authored names for the modes, a selected nonzero mode descriptor, every
indirect caller, and a concrete live admission are not established. The
zero-mode half-period has no local zero-divisor guard. Broader descriptor
distributions and resource interpretation belong to the existing resource and
effect-command owners; the selected values here only bound this consumer.
