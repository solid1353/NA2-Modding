# Character action callbacks

This document investigates character-specific action algorithms in retail
NA2 (`SLPS-25837`).

## Research coverage

- **Assigned scope:** Character callback and fighter virtual-method action algorithms, held loops, rate overrides, writable phase-row changes and exit paths beyond common combat execution.
- **Exploration depth:** All seven slots in 78 definition callback tables and nine slots in 74 concrete fighter vtables were inventoried. All 491 distinct roots were screened: 420 decompiler bodies and 71 bounded instruction-byte bodies. Selected held, rate, row and exit families were followed into their relevant helpers and retail rows, including Kidomaru's channel-1 release dispatcher and channel-5 phase-cycle producer. Lee/Guy's channel-7 publications were followed through selected constructors, parameter writers, drawing-context aliases and cleanup; this was not a complete transitive call-graph investigation.
- **Confirmed coverage:** Code-authored event helpers and callback-produced continuation permission in selected families; shared wrap-counter production/reset; eleven wrap-controlled held branches; input-ratio, per-update, event-count and wrap-indexed rate families; all six authored relative cycles with explicit callback/helper destinations; Lee/Guy effect-mode producers, category/radius mutation and channel-7 render-owner publication; Kiba's response-count exit; and Kidomaru's three secondary-timer holds, release continuations and charge-derived phase-cycle limit.
- **Unresolved or untested:** Equivalent writers or consumers hidden through other aliases or unvisited descendants; lifetime of every copied drawing descriptor; complete player-facing identity/reachability of local actions; and Kidomaru's admission under interruptions and unusual command/phase scheduling. Static inspection does not establish elapsed duration, appearance or contact results.
- **Deliberate exclusions and overlap:** [Combat action execution](../combat/combat_action_execution.md) owns common action/phase dispatch and the complete authored-array census; [Character assets](../../game/character_assets.md#per-character-code) owns definition-table shape and provider selection; [Battle entities](../session/battle_entities.md#complete-table-selected-concrete-lifetime-paths) owns concrete class construction/lifetime. [Puppet control](puppet_control.md), [Projectiles](../projectiles_and_items/projectiles.md), [Awakening](awakening.md) and [Ultimate Jutsu](ultimate_jutsu.md) own their specialized effects.
- **Evidence limitations:** Static analysis establishes instructions and data, not player-visible behavior or ordinary-play reachability. Function boundaries and inferred signatures can be incomplete.

## Evidence convention and ownership

Binary identities and address conventions belong to
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
`FUN_` names are analysis labels. Numeric action IDs below are callback-local
IDs; [Combat action execution](../combat/combat_action_execution.md#character-execution-callbacks)
explains configured-provider remapping.

The dispatcher contract of `FUN_00217670` (channels 1, 2, 3, 5, 6 and 7 read
definition slots 0, 1, 2, 4, 5 and 6; slot 3 has no channel) and
provider-table selection are owned by
[Character assets](../../game/character_assets.md#per-character-code). This
file investigates the selected bodies. Definition slot 3 is the
source-fighter response callback at vector `+0x0C`, selected from fighter
`+0xA8` by the accepted-hit initializer. Its caller contract and complete
response inventory belong to [Hit response](../combat/hit_response.md#character-response-callbacks).

## Complete bounded class/slot census

All 94 rows of the resident `0x005A2900..0x005A2BF0` table, all seven
callback words at definition `+0x1C` of the 78 distinct nonzero definition
pointers, and all nine words at vtable `+0x0C..+0x2C` of the 74 concrete
class vtables identified by the construction inventory in Battle entities
were read. This is a complete census of these roots, including the four
jutsu-only definitions; it does not include independently constructed
classes or virtual slots beyond `+0x2C`. The per-slot definition populations
are in [Character assets](../../game/character_assets.md#per-character-code);
within every definition slot, each nonzero pointer is a distinct target.
The vtable slots are:

| Root slot | Nonzero classes | Distinct targets |
| --- | ---: | ---: |
| Vtable `+0x0C` | 74 | 1 (`0x0024D830`) |
| Vtable `+0x10` | 74 | 1 (`0x0024DA50`) |
| Vtable `+0x14` | 74 | 1 (`0x0024DD70`) |
| Vtable `+0x18` | 74 | 1 (`0x0024DE40`) |
| Vtable `+0x1C` | 74 | 74 |
| Vtable `+0x20` | 74 | 22 |
| Vtable `+0x24` | 74 | 19 |
| Vtable `+0x28` | 74 | 37 |
| Vtable `+0x2C` | 74 | 14 |

The census has 491 distinct resident targets (321 definition callbacks and
170 virtual targets, without overlap). Seventy-one of them have no analyzed
function and were reviewed from instruction bytes, as described below; the
other 420 decompiler bodies were screened for direct phase-set/increment
calls, explicit secondary-timer resets, logical held-bit `0x8000` checks, playback-rate field
`+0xB90`, and row/payload accesses. The algorithm sections below inspect
selected matches in context. A nonzero target or successful decompilation is
not proof of a nontrivial or complete body. This screen does not establish
absence of equivalent operations through aliases, indirect calls, unparsed
instructions, or transitive helpers.

Direct playback-rate writes appeared in twelve callback roots, for definition
IDs 40, 62, 63, 65, 66, 67, 76, 77, 80, 87 (two roots) and 93. ID 92's
slot-3 callback instead reads the rate product. No direct `+0xB90` writer
appeared in the bounded virtual-root text. These are text-screen bounds,
not a whole-program writer census.

### Entries without an analyzed function

The 71 missing entries were reviewed from instruction bytes through their
reachable return and delay slot. Fifty are immediate returns, including
literal `-1` response returns. Seventeen more contain only an ID gate or
flag reads, with no stores or calls. The remaining four are Lee and Guy's
channel-1 and channel-7 callbacks, whose complete bounded bodies are:

| Definition / channel | Resident byte interval, inclusive | Confirmed effects |
| --- | --- | --- |
| 67 / 1 | `0x002BD970..0x002BDAF0` | Action categories and six phase-row radii, detailed below. |
| 67 / 7 | `0x002BDB00..0x002BDB48` | Actual-ID gate `0x43`; publish fighter `+0x6874` to GP-relative word `-0x7DE8`; if byte `+0x6824` is nonzero, also publish `+0x6820` to word `-0x35FC`. |
| 69 / 1 | `0x002C3DF0..0x002C3FC4` | Action categories, detailed below. |
| 69 / 7 | `0x002C3FD0..0x002C4004` | Actual-ID gate `0x45`; publish fighter `+0x69B4` to GP-relative word `-0x7DE8`. |

These four bodies have no calls or branches outside their byte intervals.
The channel-7 stores establish pointer publication; their selected consumers
and lifetimes are traced below.

## Code-authored events and continuation permission

Some callbacks author events in code rather than in phase rows, and one
produces continuation permission instead of relying on fixed row bytes.
Character names follow the project's numeric character reference; these
static paths do not establish roster reachability.

| Definition ID / callback | Confirmed execution behavior |
| --- | --- |
| 1, Classic Naruto / `FUN_002539E0 -> FUN_00252A10 -> FUN_00252C40` | Channels 2/3 target no-ops at `0x00252C20/0x00252C30`; channel 5 reaches timed event code after its active/pass-bit gates. Action `0x23` phase 0 event 5 and phase 1 event 7 call different helpers `FUN_0020B960/FUN_0020BA50`. |
| 2, Classic Sasuke / `FUN_00253DB0` | Action `0x2B` phase 0 secondary event 2 calls `FUN_00204220`; phase 1 zero event calls `FUN_0020ABC0/FUN_0024C370`. |
| 4, Classic Gaara / `FUN_002574B0` | Action `0x22` phase 0 triggers `FUN_00204450` at secondary events 7,8,9,11; other actions use different event sequences. |
| 69, Might Guy / `FUN_002C4710` | Action `0x30` enables or clears payload bit `0x20` in both banks of phase 1 according to current outcome byte `+0xA40 == 1`. |

Payload bit `0x20` is the continuation gate consumed by
[Combat action execution](../combat/combat_action_execution.md#continuation-and-common-exit-decisions),
so Guy's action `0x30` continuation window is produced by its callback.

## Held phases controlled by animation wraps

**Observation:** Resident `FUN_0024D1C0` saves the scene's frame in fighter
`+0xB92`, advances it, then compares the new unsigned frame with that saved
unsigned halfword. On a decrease, it increments byte `+0xB97` unless it is
already `0xFF`, and sets notification byte `+0xB98`. Disassembly at
`0x0024D360..0x0024D394` confirms the unsigned comparison, byte load/store,
and saturation sentinel. `FUN_00218060` clears both bytes when it installs a
nonnull animation object. This is a wrap counter, not a counter of hits or
callback invocations. It can remain nonzero throughout later updates of the
same installed animation.

The following complete held-control branches call live BTL `0x0071EF70`
(imported `0x0071EF30`) to increment the current phase. The common setter's
timer reset and payload refresh remain owned by Combat action execution.
Logical held bit `0x8000` is read from fighter `+0x338`; the table does not
assign a physical button name.

| Definition ID / resident channel-3 callback | Local action / phase | Admission and exit comparison |
| --- | --- | --- |
| 6 / `0x002590B0` | `0x1C / 1` | Require wrap count nonzero; advance on release or count greater than 2. |
| 14 / `0x0025F410` | `0x28 / 1` | Require count nonzero; advance on release or count greater than 15. |
| 16 / `0x00262350` | `0x1C / 1` | Require count nonzero; advance on release or count greater than 2. |
| 38 / `0x00275600` | `0x1C / 1` | Require count nonzero; advance on release or count greater than 3. |
| 49 / `0x00283A70` | `0x20 / 1` | Also require secondary event zero; advance on release or count greater than 7. |
| 65 / `0x002B7D10` | `0x18 / 1` | Require count nonzero; advance on release or count at least 6, raised to at least 7 when fighter delta `+0x1AC` is greater than 1. |
| 75 / `0x002D3670` | `0x1F / 1` | Require count greater than 1; advance on release or count greater than 9. |
| 80 / `0x002E75B0` | `0x33 / 1` | Require count nonzero; advance on release or count greater than 2. |
| 86 / `0x002F1270` | `0x17 / 0` | Require count nonzero and release; this branch has no count ceiling. |
| 93 / `0x00301F50` | `0x1D / 1` | Require count greater than 1; advance on release or count greater than 4. |
| 93 / `0x00301F50` | `0x19 / 1` | Require count nonzero; advance on release or count greater than 2. |

These branches often continue other work after incrementing phase; calling the
helper is not a return. Many also compare scene-frame wrap directly, clear
outcome byte `+0xA44 == 1`, or call `FUN_00222BB0` with the opponent and
current action. The accepted-hit meaning of that helper belongs to
[Hit response](../combat/hit_response.md). The table establishes each callback's held
exit branch, not the action's only possible interruption or elapsed duration.

### Writable motion in two held variants

ID 14 action `0x28` writes planar motion in phase-1 row `+0x0C` (action's
row-array base `+0x58`) to `+6.0` or `-6.0` from logical direction bits
`1/2` and facing `+0x990`. Action event zero in phase 0 initializes it to
`+6.0`. Thus its repeated phase also permits direction-dependent row mutation.

ID 75 action `0x1F` stops vertical speed when the non-sentinel ground-distance
field `+0xBA4` is at most 165. In phase 1, zero vertical speed writes local
attack offset `-60.0` to row-1 `+0x30` (base `+0x7C`) and radius `70 + 2 * wrap_count`
to row-1 `+0x3C` (base `+0x88`); nonzero vertical speed instead writes
`+60.0` and zero radius. These offsets follow the shared 0x4C-byte row layout;
they do not establish visible geometry or contact results.

### Kiba's response-count exit

ID 78 channel 3 `FUN_002E1D90`, actual-ID gate `0x4E`, has a different
held branch for action `0x2F` phase 2. It compares the signed halfword at
the child pointer `fighter+0x6258` with live action record `+0x2E`.
At or above that limit it increments phase; below it, release of logical
`0x8000` increments phase. The extra unsigned-wrap nonnegative check in
`0x002E2108..0x002E2110` imposes no positive-wrap requirement.
Instructions `0x002E20DC..0x002E212C` confirm both paths.

The counter is reset to zero by this channel-3 body on phase-0 secondary
event zero (`0x002E2310..0x002E2338`). Source response callback
`FUN_002E2360` passes the child and increment 1 to live BTL `0x00722D90`
before its action-specific response work. Imported bytes
`0x00722D50..0x00722D78` show that helper compares child word `+4` with
word `+0x194` of the object at resident GP-relative pointer `-0x35F4`.
Only a changed value stores the new stamp and adds the increment to signed
halfword `+0`. Thus repeated response callbacks at the same stamp add at
most once; this is not the animation-wrap counter. The source-response
dispatch belongs to Hit response, and child lifetime belongs to Battle
entities. No wider meaning is assigned to the stamp here.

## Rate overrides and their record side effects

**Observation:** These are direct writes to unsigned playback rate `+0xB90`.
The consumer divides this value by 256 for the phase timeline, while scene
playback also multiplies by fighter delta `+0x1AC`. That consumer contract
belongs to Combat action execution; no rate below is an elapsed-time measurement.

### Neji's per-update rate ramp

ID 65 channel 3 `FUN_002B7D10`, action `0x18`, clamps an initial rate above
`0x100` to `0x100` at primary event zero. In phase 1 it adds 8 on every
callback invocation admitted to that branch, then caps at `0x200`. The
resident constant block `0x00603840..0x00603857` supplies step 8,
intermediate threshold `0x160`, cap `0x200`, and three pairs for the live
action record's `+0x30/+0x32`:

| Resulting playback rate | Action `+0x30` | Action `+0x32` |
| --- | ---: | ---: |
| Below `0x160` | 2 | 2 |
| `0x160..0x1FF` | 1 | 1 |
| At cap `0x200` | 0 | 1 |

Disassembly `0x002B8204..0x002B82C0` confirms GP-relative loads,
halfword addition/store and both thresholds. The address uses resident
`gp = 0x0060A9F0`, whose ownership is documented in
[Overlay ABI](../../runtime/overlay_abi.md#overlay-to-resident).
These action-record fields feed accepted-hit pause/rejection handling in
Hit response. The held-exit check precedes the ramp and does not return;
an invocation that advances out of phase 1 can still perform this write.

### Rock Lee's count-dependent rate and additional exits

ID 67 channel 3 `FUN_002BDF80`, action `0x18`, resets signed counter
`+0x67F8` and presentation countdown `+0x67F9` at primary event zero.
In phase 1 it derives the counter in two ways: when animation header
`scene[+0x90][+0x28] & 2` is clear, a secondary event at
`counter * animation_frame_count` increments it; with that flag set, it
assigns `wrap_count + 1`. It then stores `0x100 + 24 * counter` to `+0xB90`.
Instructions `0x002BE3A8..0x002BE43C` confirm these distinct sources.

With a positive counter it increments phase on logical release, counter at
least 8, or character byte `+0x6818 == 0`. It also exits when current outcome
`+0xA40` is either -1 or 1 and `FUN_00231BF0(fighter, opponent) == 1`.
The complete comparison sequence is `0x002BE440..0x002BE4D4`.
The helper resolves the current action's accepted-hit repetition count;
the authoritative contract remains in Hit response. This held action has
outcome and character-state exits beyond its count ceiling.

The class's virtual method `+0x1C`, `FUN_002BD1D0`, supplies that character
state: effect `0x44` or `0x45` present sets byte `+0x6818` to 1; neither
present sets it to zero. This is a traced producer of the extra exit predicate.
The same byte selects the category/radius mutations below; specialized effect
behavior remains owned by Awakening.

### Hinata and Sasuke's wrap-indexed rate/response pairs

ID 80 channel 3 `FUN_002E75B0`, action `0x33` phase 1, stores rates
`0x130`, `0x150`, `0x180` for wrap counters 0, 1, 2 respectively. It does
not assign a rate in this branch for other counts. In that action it also
chooses live action `+0x30/+0x32` from the product `rate * fighter_delta`.
The constant block `0x00603D20..0x00603D37` gives thresholds `0x80` and
`0x120` and pairs `3/13`, `2/5`, `1/3` for below the lower threshold,
the middle interval, and at/above the upper threshold.

ID 93 channel 3 `FUN_00301F50`, action `0x19` phase 1, stores
`0x100`, `0x110`, `0x120`, `0x130` for wrap counters 0, 1, 2, 3.
Its corresponding product thresholds are also `0x80/0x120`, with pairs
`2/7`, `1/4`, `0/2` at resident `0x00604148..0x0060415F`.
Action `0x1D` phase 1 instead uses rate `0x100` and planar speed 50 while
count is below 2, then rate `0x200` and speed 100. The pointer is the
action's first row `+0x0C`, derived from record `+0x50`, rather than the
current phase's row. Phase-0 secondary event zero restores rate `0x100`
and that row's planar speed to zero.

### Other direct rate-writer families

| Definition ID / callback | Confirmed rate branch |
| --- | --- |
| 40 / channel 3 `0x00279EB0` | Action `0x18`, phase 1: truncate `16 + 752 * FUN_00247E90(fighter)` to a halfword. |
| 63 / channel 3 `0x002B2C30` | Action `0x20`, phase 0, secondary cursor `+0x1E8 > 11`: write `0x100`. Specialized control remains in Puppet control. |
| 76 / channel 2 `0x002D4AB0` | Require actual fighter ID `0x4C`; major 0 substate 3 writes `0xD0`. |
| 77 / channel 3 `0x002D9AA0` | Action `0x1C`, phase 1: truncate `16 + 496 * FUN_00247E90(fighter)` to a halfword. |
| 87 / channel 2 `0x002F2D70` | Require actual fighter ID `0x57`; major 0 substate 3 phase 1 writes `0xB0`. |
| 87 / channel 3 `0x002F2EF0` | Action `0x23`, phase 0 secondary event 1 writes `0x120` only when effect `0x5B` or `0x5C` is present. Effect ownership remains in Awakening. |

The complete `FUN_00247E90` returns signed progress/latch `+0xB4C`
(falling back to `+0xB48` when zero) divided by nonzero signed cap
`+0xB4A`, or zero for cap zero. The producer, release latch and constructor
caps belong to [Action commands](../combat/action_commands.md#resident-post-translation-synthesis).
The rate callbacks perform no independent clamp on that returned ratio.
Tenten and Chiyo's remaining rate writers are coupled to phase loops below.

## Phase-entry loops and explicit destinations

The following findings combine callback control with the selected retail rows
for the local action IDs below; the complete authored-array census belongs to
Combat action execution. Relative jumps are evaluated on animation end by the
shared phase updater.

| Definition / action | Authored cycle | Callback exit |
| --- | --- | --- |
| 51 / `0x2C` | Phase 3 at `0x004BB39C` has condition -3, returning to phase 0. | `FUN_002872A0` resets float `+0xA60` at primary event zero; subsequent phase-0 zero events increment it. At count at least 1, release or count at least 8 sets phase 4. It also manages current/prior hit-outcome bytes between repeats. |
| 62 / `0x1C` | Phase 7 at `0x004F4C30` has condition -5, returning to phase 2. | `FUN_002ADE20` resets `+0xA60/+0xA64/+0xA68` at primary event zero; phase-2 zero events increment `+0xA60`. Above phase 1 and below phase 8, count at least 4 sets phase 8; otherwise release sets phase 9. |
| 66 / `0x23` | Phase 2 at `0x0050B7C4` has condition -2, returning to phase 0. | `FUN_002B9660` latches a release/count decision in the current phase, then sets phase 3 only after the phase differs from the latch. |
| 77 / `0x1B` | Phase 3 at `0x00543B84` has condition -3, returning to phase 0. | `FUN_002D9AA0` resets float `+0xA88` at primary event zero; later phase-0 zero events increment it. Above phase 1 and below phase 4, release or count at least 3 sets phase 4. |

For IDs 51, 62 and 77, the primary-zero branch clears the float counters
instead of counting that entry. These float counters are separate from the
shared wrap byte. Tenten's byte counter has different initialization order,
described below.
Super Choji's callback first runs a ground query and landing transition helper,
then rechecks that action `0x2C` is still current before continuing its loop
work. A landing-driven change can bypass the later held decision.

### Chiyo's growing increment

For ID 62 action `0x1C`, each admitted secondary event 1 increases float
`+0xA68` by one, truncates it to a signed halfword, and adds that halfword
times signed step 37 to current rate `+0xB90`, capped unsigned at `0x300`.
The step/cap are the halfwords at resident `0x00603768`; instructions
`0x002ADE78..0x002ADE7C` and `0x002AE4B8..0x002AE4D8` confirm the loads
and unsigned cap comparison. This is not a fixed increment per update: the
event crossing and accumulated `+0xA68` govern each addition. The base row
rate may be reinstalled on intervening phase-animation selection.

### Tenten's latch and phase-3 row rewrite

ID 66 action `0x23` uses character block `fighter+0x5BB0`: signed byte
`+4` is the latched phase, byte `+5` the entry count, byte `+6` another
cleared working byte. Primary event zero sets them to `-1/0/0`. Secondary
zero events in phases 0, 1 or 2 increment the signed count; those phases
assign rate `0xF4 + 12 * count` each invocation. The secondary-zero check
follows initialization independently, so it can count that same invocation.

While the latch is -1, positive count plus release or count greater than 4
records the current phase. That invocation still selects the eventual phase-3
animation as `0x80/0x82/0x84` for current phase 0/1/2. A later invocation
with a different phase sets phase 3. This defers the exit to a phase boundary
rather than leaving immediately on release.

The writable phase-3 row begins at current action row-base `+0xE4`
(retail row at `0x0050B810`). On that exit, count exactly 6 replaces its
animation with `0x85`, motion-event time with 2, planar speed with -30,
vertical speed with zero, decay with 0.1 and multiplier with 1. Other counts
disable its motion event with `0x7FFF`, set both speeds to zero, decay to
0.2 and multiplier to 1. Instructions `0x002BA934..0x002BAABC` corroborate
the count, latch, phase setter and row offsets despite decompiler warnings in
other portions of this large body.

### Might Guy's two delegated loops

ID 69 channel 3 `FUN_002C4710` first calls `FUN_002C5BC0`. A nonzero
return suppresses the rest of that callback's ordinary action-specific body.
The helper handles actions `0x1C` and `0x1D`, which the root-only text screen
therefore does not expose as direct rate writers.

Action `0x1C` resets signed entry count `+0x69A8` at primary event zero and
increments it on phase-1 secondary event zero. In phases 1/2 it stores
`0x100 + 36 * count`. For positive count it sets phase 3 on release,
count greater than 3, or outcome -1/1 combined with record-sensitive repeat
helper `FUN_00231BF0(fighter, opponent) == 1`. Retail phase 2's condition
-1 at `0x0051D1C4` returns to phase 1, connecting that authored cycle to
the callback's explicit phase-3 destination.

Action `0x1D` phase 2 stores `0x100 + 24 * wrap_count` and increments
phase on release, wrap count at least 8, the same outcome/repeat comparison,
or character mode byte `+0x69B1 == 0`. Its unsigned wrap count has no
positive-count requirement, so release can be admitted before the first wrap.
Instructions `0x002C6100..0x002C6248` confirm the rate, unsigned counter,
held/outcome predicates and phase-increment call. Both branches can continue
presentation and outcome bookkeeping after changing phase.

Virtual method `+0x1C`, `FUN_002C1ED0`, produces the mode byte: effect
`0x47` present selects 1; otherwise effect `0x48` present selects 2;
neither selects zero. Effect `0x47` therefore takes precedence if both are
present. The mode also selects the writable action categories below.

## Effect-dependent action and row mutation

Both channel-1 bodies below require their actual fighter ID. They use fighter
`+0xBC`, the alternate action-array pointer copied and selected by common
loader `FUN_002151E0`. Action records have stride `0x54`; each category
write is at `array + action_id * 0x54 + 0x10`. Their row accesses dereference
that record's `+0x50`. The setup/selection contract belongs to
[Action commands](../combat/action_commands.md#action-table-source-and-setup); the row
layout belongs to Combat action execution. These mutations show why shipped
categories and rows alone cannot describe the live action configuration.

### Rock Lee

`0x002BD970` requires actual ID `0x43` and selects from mode `+0x6818`.
The complete category-write groups are:

| Local actions | Mode zero | Mode nonzero |
| --- | ---: | ---: |
| `0x18` | 0 | 4 |
| `0x1D, 0x1E, 0x27, 0x28, 0x29` | 0 | 1 |
| `0x1C, 0x23, 0x24, 0x25, 0x26` | 1 | 0 |

The same body changes action `0x2E` row radii at row-array offsets
`+0x70/+0xBC/+0xD4/+0x108/+0x154/+0x16C`: phase 1 bank 1, phase 2
banks 1/2, phase 3 bank 1, phase 4 banks 1/2. Mode zero assigns 70 to
all six. Nonzero mode assigns 100 to the first four and 110 to the last
two. These are the shared radius fields at row `+0x24/+0x3C`; the body
does not change their centers or establish a contact result.

### Might Guy

`0x002C3DF0` requires actual ID `0x45` and selects from mode `+0x69B1`.
Its complete write groups are:

| Local actions | Mode 0 or other | Mode 1 | Mode 2 |
| --- | ---: | ---: | ---: |
| `0x1C` | 4 | 0 | 0 |
| `0x1D` | 0 | 4 | 4 |
| `0x1E, 0x1F` | 0 | 1 | 1 |
| `0x20, 0x21` | 1 | 0 | 0 |
| `0x22, 0x23, 0x26, 0x27, 0x28` | 1 | 1 | 0 |
| `0x24, 0x25` | 0 | 0 | 1 |
| `0x29` | 0 | 0 | `0x100` |
| `0x2A` | 0 | 0 | `0x200` |

These are assignments of the whole category word, not bitwise additions.
They do not by themselves select or begin an action. The preceding producer
establishes modes 0/1/2; the byte branch also routes every other value to the
mode-0 assignments.

## Lee/Guy's channel-7 render-owner publications

**Observation:** With resident `gp = 0x0060A9F0`, the two published words
are `0x00602C08` (`gp-0x7DE8`) and `0x006073F4` (`gp-0x35FC`).
Common virtual `+0x14`, `FUN_0024DD70`, requires node flag `+0 & 4`,
dispatches channel 7, traverses the primary scene at fighter `+0xE70`
through `FUN_001BB790`, and later invokes the concrete virtual `+0x28`.
The intervening `FUN_00308FD0/FUN_00308FE0` bodies are immediate returns.
This ordering places the publications around selected drawing work.

### Fighter-owned optional-pass parameters

Lee's constructor `FUN_002BCCB0` and Guy's `FUN_002C1BF0` each allocate a
`0x34`-byte block, initialize it through `FUN_001C4470`, store it at
`+0x6874/+0x69B4` respectively, and initially write `0x80` at block `+0x0C`.
The shared initializer sets enable halfword `+0x1C` to 1 and scalar
`+0x10` to 1.0. These are concrete fighter-owned allocations, separately
published into the shared drawing state; the complete class factory/vtable
inventory remains in [Battle entities](../session/battle_entities.md#complete-table-selected-concrete-lifetime-paths).

The already traced virtual-`+0x1C` effect predicates also write these blocks:

| Producer | Established mode | Block `+0x0C` | Block float `+0x10` |
| --- | --- | --- | --- |
| Lee `FUN_002BD1D0` | Neither effect `0x44/0x45` | `0x80000000` | 1.0 |
| Lee `FUN_002BD1D0` | Either effect present | `0x00000080` | 1.25 |
| Guy `FUN_002C1ED0` | Mode 0 | `0x80000000` | 1.0 |
| Guy `FUN_002C1ED0` | Mode 1 or 2 | `0x00000080` | 1.25 |

`FUN_001982B0` and `FUN_00198340` snapshot global `0x00602C08` into
model-working context `+0x248`. The primary-scene branch
`FUN_001BB790 -> FUN_00190F40 -> FUN_001982B0 -> FUN_001910E0`
therefore connects channel-7 publication to that alias. The latter dispatcher
admits optional pass bit 1 only with model flag `0x80`, a nonnull alias and
nonzero block halfword `+0x1C`. Ordinary drawing passes the alias to
`FUN_001C3DA0`; packed drawing passes it through `FUN_001C3750` to
`FUN_001C3A20`. Both producers supply the block and working context to
`FUN_001C4290`. Instructions `0x00191504..0x00191524`,
`0x00191868..0x00191878`, `0x00190A70..0x00190A7C`,
`0x001C3E2C..0x001C3E40` and `0x001C3A9C..0x001C3AB0`
confirm the alias loads and forwarded arguments despite incomplete
decompiler call signatures. Color fallback, width/alpha calculation, packet
state and geometry remain in [Material draw modes](../../runtime/rendering/material_render_modes.md#extra-model-owned-blend-state-and-frame-restoration)
and its linked VU investigation. These callbacks change pass parameters;
the static trace does not measure the resulting visible appearance.

Lee's concrete `+0x28`, `FUN_002BD2D0`, resets global `0x00602C08` to
default block `0x0061FD50` after any auxiliary-scene traversal. Guy's
`FUN_002C2020` resets it before its additional drawing work. Their deleting
destructors `FUN_002BD0B0/FUN_002C1E00` call `FUN_001C4410(block,1)` and
clear the fighter field. That block destructor also resets the global to
`0x0061FD50` if it still points to the freed block. It does not search or
clear already copied working-context aliases. The block remains owned by
the fighter throughout these temporary publications.

### Lee's separate draw/list environment

Lee's constructor additionally allocates `0x40` bytes at fighter `+0x6820`
and initializes it through `FUN_0010A1D0` with selector `0x100` and renderer
pointer from global `0x0060919C`. The helper stores that supplied pointer at
block `+0x3C` and clears ownership byte `+7`, so this block borrows it.
Byte `+0x6824` starts at zero. Channel-2 callback `FUN_002BDB50`, gated to
actual ID `0x43`, sets that byte on local action 6's primary event 5 and
clears it on event 13; instructions `0x002BDC90..0x002BDCD0` confirm both.
These are selected writers, not proof that every interruption clears it.
Channel 7 publishes the block to `0x006073F4` whenever that byte is nonzero.

The same two model-working initializers snapshot this global at `+0x1FC`
and its block `+0x3C` renderer pointer at `+0x1F8`. The optional-pass packet
producers read `context[+0x1FC]+8` to choose their allocation/list path.
`FUN_001BB790` also saves and restores block `+0x3C` through
`FUN_001BBC90/FUN_001BB9C0` around a scene-specific renderer substitution.
Thus the second publication selects a draw/list environment distinct from
the `0x34`-byte optional-pass parameter block. Generic list/buffer lifetime
belongs to [Render submission](../../runtime/rendering/render_submission.md), and renderer
coordinates remain with that document's linked coordinate owner.

Lee's `+0x28` captures the then-current `0x006073F4`. When scene `+0x682C`
exists and byte `+0x6870` is nonzero, it prepares `+0x6820`, optionally
substitutes it unless current local action is `0x33`, and traverses that
auxiliary scene. It then restores the captured global. That capture occurs
after channel 7, so it can preserve channel 7's selected environment; it is
not necessarily the value from before the callback. The destructor releases
`+0x6820` through `FUN_0010A0F0(block,1)` and clears the field. That helper
selects default environment `0x00609160` through `FUN_00106230` if the global
still equals the destroyed block, and frees block `+0x3C` only when ownership
byte `+7` is nonzero. Guy's separate mode-2 auxiliary substitutions save and
restore this environment inside `FUN_002C2020`; his channel-7 body itself
only publishes the optional-pass parameter block.

### Bounded alias coverage

Direct-reference metadata omits some GP-relative instructions, including the
two channel-7 stores. Selected GP-load/store byte searches and instruction
review therefore supplemented xrefs. A bounded search of `lw` encodings
with displacement `0x248` followed the model-working aliases above;
unaligned matches and repeated memory mirrors were not counted as consumers.
Other aligned matches in `FUN_00320EA0/FUN_00321610` compare a different
object's `+0x248` with another object's `+0x10`; they do not read the
model-working context. Equal field offsets alone do not establish an alias.

An additional body, `FUN_0035DD10`, reads a supplied context's `+0x248`,
copies its `0x34` bytes to supplied storage and repoints that context
to the copy. Instructions `0x0035DD5C..0x0035DD74` and
`0x0035DF18..0x0035DF28` establish the copy and publication. No incoming
xref was returned for this body, so this read does not establish its
reachability from Lee/Guy's selected traversal or the copy's full lifetime.
The distinct scoped global substitution at `FUN_0035C110` is already owned
by [Material draw modes](../../runtime/rendering/material_render_modes.md#scoped-cpu-state-and-restoration-boundaries).
These selected paths resolve the two channel-7 pointers' roles and concrete
owners, without claiming a complete whole-program alias-consumer census.

## Kidomaru's secondary holds and delegated relative-cycle exit

ID 53 channel 3 `FUN_00288FD0` has three complete timer-reset branches:
action `0x16` phase 1 resets secondary block `+0x1DC` to zero when cursor
`+0x1E8 > 0`; action `0x1F` does so above 2; action `0x22` above 1.
Their retail phase-1 rows at `0x004C3EFC`, `0x004C4700`, `0x004C49AC`
all have progression condition zero, with rates `0x20/0x100/0x80` and
start frames `10/9/9` respectively. The reset calls preserve phase and
therefore do not by themselves reach the terminal row. Their channel-2
entry is an instruction-confirmed no-op at `0x00288FC0`.

These branches also call charge-presentation helper `FUN_0020A210`, which
reads the input progress ratio and emits timed presentation work; its complete
body has no phase setter or state transition. The exit producer is a different
channel, rather than that presentation helper or the channel-2 no-op.

### Channel-1 release dispatch

**Observation:** Definition callback table `0x004C1850` selects channel 1
`FUN_00288F20`. Its complete body calls `FUN_00248020(fighter, action, 1, 1, 0)`
for local actions `0x16`, `0x1F`, and `0x22`, in that order. It ORs their
return values and calls `FUN_00247F50` only when all three return zero.
Instructions `0x00288F38..0x00288FA4` establish the arguments and ordering.
The latter helper clears the working charge counters only while release
latch `+0xB4C` is zero, preserving an already latched amount.

The release branch in `FUN_00248020` requires an input object, no pending
continuation (`s16 +0xA3E == -1`), a current callback-local action equal to
the supplied ID, phase 1, and neither logical `0x2000` nor `0x4000` in
input-object word `+0xAC`. It latches progress `+0xB48` into `+0xB4C`
(substituting 1 for zero), clears progress/overflow, then scans the live
action array in increasing index order for the first signed continuation
byte `record+0x18` equal to the hold action. It dispatches that record through
`FUN_0023A9A0(fighter,index,0)`; this changes action, not merely phase.
Instructions `0x00248404..0x002484F8` confirm the gates, widths, first-match
scan and call. The helper's earlier context/direction predicates determine
its return value and input rewriting; they are not extra guards around this
final release branch. Dispatch still has its own record eligibility gate.

All 39 records in this definition's shipped array at `0x004C5080` were read
to establish the first matching continuation, rather than assuming adjacency:

| Hold / shipped record | Hold signature | First release continuation / shipped record | Release signature |
| --- | --- | --- | --- |
| `0x16 / 0x004C57B8` | `0x00400212` | `0x17 / 0x004C580C`, continuation byte `0x16` | `0x00800112` |
| `0x1F / 0x004C5AAC` | `0x00400214` | `0x20 / 0x004C5B00`, continuation byte `0x1F` | `0x00800114` |
| `0x22 / 0x004C5BA8` | `0x00400414` | `0x23 / 0x004C5BFC`, continuation byte `0x22` | `0x00800114` |

Hold category words are `8`; their release records use `0x10`. Their
behavior words are `0x00070009` for the first pair and `0x0007000A` for
the other pairs. Shipped `record+0x50` values are row indices, converted
to live pointers during [Action-table setup](../combat/action_commands.md#action-table-source-and-setup).
The row starts are indices `100/103`, `127/130`, and `136/139` for the
hold/release pairs. Each hold has phase 0, condition-zero phase 1, and a
terminal phase 2. Release dispatch therefore bypasses the hold's otherwise
unreached terminal row.

The constructor supplies hold threshold 12 and progress cap 36. The common
sequencer publishes `0x2000` while charging, and `0x4000` on release while
latching progress; channel 1 can also dispatch when both bits disappear.
`FUN_0024FD80` invokes charge synthesis in `FUN_0024C440` before its
channel-1 pass, and copies the resulting input into fighter `+0x338`
later. This distinguishes helper-driven dispatch from the ordinary
signature-matching/pending route. The shared synthesis and selector contracts
remain in [Action commands](../combat/action_commands.md#resident-post-translation-synthesis).
These static paths establish the three release destinations, without claiming
every interrupted or delayed input sequence reaches them.

### Channel-5 count and phase-3 destination

**Observation:** The relative cycle of release action `0x23` is controlled
by `FUN_0028A890`, reached through channel-5 root `FUN_0028BE00` when node
flag `u8 +0 & 2` and fighter flag `u8 +0x61 & 0x20` are set.
`FUN_00250230` dispatches channel 5 after its virtual-slot-`+0x20` pass.
This class's `+0x20` entry `0x002504A0` is an instruction-confirmed immediate
return. Thus the producer lies in a descendant of the channel-5 root and
was not exposed by the direct channel-3 phase-call screen.

On primary event zero, the helper clears 25 words `+0xA60..+0xAC0`,
including float entry count `+0xAB8`. On phase-0 secondary event zero it
sets float limit `+0xABC = 2 + 8 * FUN_00247E90(fighter)` and saves that
ratio at `+0xAC0`. Phase-1 secondary event zero increments `+0xAB8` by
1. Phase-2 secondary event zero compares the count with the saved limit;
**strictly greater** increments phase to 3. Instructions
`0x0028B5CC..0x0028B694` establish the formula, float
stores, `c.le.S` bypass and phase-increment call. The count is phase-entry
count, not animation-wrap count or successful projectile count.

Phase 2 also checks secondary event 2 independently. When crossed, it sets
the current phase minus 1 and sets fighter `+0x63` bit 0, confirmed at
`0x0028B698..0x0028B6E0`. This is an explicit return to phase 1 in addition
to the authored animation-end relative jump. The event check follows the
phase-3 increment; the common phase setter resets the secondary timeline,
so the later check observes that reset rather than the old phase-2 cursor.
The shared reset/event contracts belong to Combat action execution and
[Timer primitives](../../runtime/timer_primitives.md).

The complete shipped row sequence at `0x004C4A44` is:

| Phase / resident row | Animation / condition / start frame / rate |
| --- | --- |
| `0 / 0x004C4A44` | `107 / 1 / 0 / 0x200` |
| `1 / 0x004C4A90` | `106 / 4 / 1 / 0x200` |
| `2 / 0x004C4ADC` | `107 / -1 / 0 / 0x200` |
| `3 / 0x004C4B28` | `107 / -16 / 0 / 0x180` |
| `4 / 0x004C4B74` | Terminal animation `-1` |

This closes the sixth authored relative-cycle destination: entry count above
the charge-derived limit reaches phase 3, whose animation-end condition
reaches terminal phase 4. The channel-3 body still only schedules sound and
presentation for this action. The channel-5 helper requests emission on
phase-0 and phase-2 zero events independently of the exit decision, including
the invocation that increments to phase 3. Emission helper `FUN_00289AC0`
returns failure on a null spawn and does not write this entry count; no
successful-spawn gate surrounds the phase exit. Its projectile construction
and later behavior belong to [Projectiles](../projectiles_and_items/projectiles.md), not this count.
The three hold exits and the relative-cycle destination are statically
resolved; ordinary-play cadence, exact emitted totals and all interruptions
remain outside this result.
