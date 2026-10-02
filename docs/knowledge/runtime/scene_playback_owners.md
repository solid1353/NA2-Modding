# Scene playback callers and owners

This document records scene-playback ownership and scheduling in retail NA2
(`SLPS-25837`): the playback families, the streamed play worker, the
direct-call census, and the resident and ETC owners of explicit seeks. BTL
owners are catalogued in [BTL scene playback owners](scene_playback_owners_btl.md).
Function names are the preserved analysis names; semantic labels describe the
inspected behavior. File identities and overlay address conversion follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** direct calls to the scene advance, seek, stream-step and
  restart APIs, classified by owning object and scheduling phase across the
  retail resident ELF, `BTL.BIN` and `ETC.BIN`.
- **Exploration depth:** an exact-JAL byte census of advance, seek, stream
  step and restart across all three programs. All 35 resident and all 3 ETC
  direct seek sites are classified here; 189 of the 214 BTL seek sites are
  classified in [BTL scene playback owners](scene_playback_owners_btl.md).
  Worker scheduling, fighter and auxiliary gates, rate producers, reuse,
  owner cleanup and seek-before-submission paths were inspected, with
  instruction bytes recovering truncated overlay bodies and caller/vtable
  connections.
- **Confirmed coverage:** task-driven streamed playback differs from
  object-owned animation. Stream pause gates cursor increments but leaves
  manager, callback and submission work active. Owners separately omit
  advance, supply zero steps, repeat by explicit seek, choose initial frames,
  restore cursors for submission, or retire players. Active-blend cancellation
  qualifies the usual absolute-seek contract; streamed manager counts use raw
  rate values, while object manager counts use crossed whole frames.
- **Unresolved or untested:** the complete owner matrix for 178 resident, 254
  BTL and 106 ETC advance candidates; the 25 unclassified BTL seek leads;
  indirect callers; the entry and screen identity of the ETC owners; the
  scheduled owner of the resident compact cursor wrappers; producers and
  meaning of the scene multiplier at `scene+8`; and complete pause and cleanup
  relationships for unclassified owners. No wall-clock cadence or observed
  instance behavior is established.
- **Deliberate exclusions and overlap:** BTL owners belong to
  [BTL scene playback owners](scene_playback_owners_btl.md);
  [Animation runtime](animation_runtime.md) owns evaluation algorithms;
  [CCS runtime](../game/files/ccs_runtime.md) owns parsing and resource
  lifetime; [Resident task system](task_system.md) owns thread and wait
  mechanics; [Effect generator commands](effect_generator_commands.md) owns the
  action-manager count contracts. This document owns callers and scheduling.
  Excluded game modes were not investigated.
- **Evidence limitations:** static evidence does not establish wall-clock
  cadence or indirect-call completeness. False no-return boundaries and
  incomplete analyzed xrefs require instruction-byte corroboration.

## Playback families

| Family | Operation | Owner and caller contract |
| --- | --- | --- |
| Object animation | `FUN_001BB210(player, delta, alternate_output)` | Mutable player, distinct from the shared `0x0700` animation descriptor; delta is in 1/256-frame units. Calling this function does not itself submit the player for drawing. |
| Object animation | `FUN_001BB5C0(player, target, flags)` | Seek API in 1/256-frame units. With no active blend it derives a forward delta or resets evaluator/reader state before advancing from zero. Active-blend cancellation has the exception described below. Bit 0 of `flags` controls preservation of the command callback during this operation. |
| Streamed container | `FUN_001B4C60(container)` | Uses container rate/control fields and checkpoint state; invoked by the primary play task. |
| Streamed container | `FUN_0019FFC0(container)` | Restart requested by the play loop or a streamed `-2` marker; requires a nonzero checkpoint table. |

These families share downstream command/evaluation machinery, but their owner
fields and increment producers differ. The algorithms and exact cursor layout
are documented in [Animation runtime](animation_runtime.md); streamed parsing
and retention are documented in [CCS runtime](../game/files/ccs_runtime.md#streamed-playback-sp-skill-play).

An active blend changes the seek contract. Complete disassembly
`0x001BB5C0..0x001BB6E4` confirms that cancelling player `+0x114` sets the
comparison origin to zero without zeroing the stored cursor `+0xEC`. Target
zero consequently returns without reconstructing pose/cursor, while a
positive target reaches advance as a delta added to that retained cursor.
The precise algorithm belongs to [Animation runtime](animation_runtime.md#absolute-seeks-and-evaluator-reset).
The caller tables classify the purpose and argument of each call; they do
not establish a full rewind solely because a caller supplies target zero.

## Streamed worker scheduling

**Observation:** resident `FUN_001A0120` is a task body called through
`FUN_001A0980`. Its loop orders stream step, action-manager update, per-frame
callback, per-object callback, scene update/submission, then
`FUN_001D0000(task, 1)`. The per-frame callback receives the request index
from flags bits 16..22. The task's `+0x40` is 1 during the update/submission
region and 0 before its wait; this is separate from container `+0x40`, which
holds the task handle.

The stream increment producer is container signed-halfword rate `+0x9C`.
`FUN_001B4C60` consumes it only when container control `+0xA4` bit 0 is clear
or bit 2 requests a single step. It clears the single-step request after
consuming it. The play loop still calls the action manager with nonzero rate,
the callbacks and scene submission while that cursor gate is closed. Stream
pause therefore does not establish a pause of every object owned by the play
context. The normal skill-play request flags do not enable the optional
controller-driven rate/pause controls; their source is owned by the linked
CCS request-list research.

**Observation:** control bit `0x20` has two consumers in different phases.
When present on entry to `FUN_001B4C60`, it is consumed as checkpoint-zero
restart parsing. When observed by `FUN_001A0120` after its wait, it is cleared
and passed to `FUN_0019FFC0` for restart preparation. An end marker can also
trigger restart automatically when play flags bit 0 is set; play flags bit 2
instead permit the loop to keep presenting the ended stream until a stop.
The streamed `-2` result invokes restart inside the step routine itself.

The streamed caller passes raw rate `+0x9C` as the action-manager iteration
count, whereas object advance supplies the number of whole frame boundaries
crossed. Both count contracts belong to
[Effect generator commands](effect_generator_commands.md#scheduling-and-owner-gates).

**Observation:** a stop request is processed after the ordinary one-wait
boundary. The loop clears control `0x10`, closes the reader, releases the
optional ring manager, waits twice, removes its temporary controller state,
calls the end callback, and tears down the play state. It then writes task
`+0x40 = 2` and container runtime `+0xA6 |= 0x20`. Container retention and
destruction belong to `PlayDecode`, not this loop. The `PlayLock` companion
observes the task state; it does not advance scenes.

**Evidence:** decompilation of resident `FUN_001A0120`,
`FUN_001B4C60`, `FUN_0019FFC0`, `FUN_001BB210` and `FUN_001BB5C0`.
Task publication and the `PlayLock` companion belong to
[Resident task system](task_system.md#playback-companion-and-sound-descendants).

## Direct-call census and analysis limits

The following bounded census searches the exact little-endian MIPS JAL words
for advance (`84 EC 06 0C`) and seek (`70 ED 06 0C`) in the three exposed
in-scope programs. These are instruction candidates until their surrounding
code is classified; a byte match alone does not identify the owner or phase.

| Program | Advance byte sites / analyzed xrefs | Seek byte sites / analyzed xrefs |
| --- | ---: | ---: |
| Resident `SLPS_258.37`, low-address mapping | 178 / 178 | 35 / 35 |
| `BTL.BIN`, preserved mapping | 254 / 187 | 214 / 94 |
| `ETC.BIN`, preserved mapping | 106 / 60 | 3 / 3 |

Resident searches return three mapped copies of each site; only the
low-address copy is counted. The overlay discrepancies are material: an
analyzed-xref list misses 67 BTL and 46 ETC advance candidates, and 120 BTL
seek candidates. For example, BTL preserved `0x006C6590` contains the seek JAL
and `0x006C65B0` the advance JAL, although neither is in the respective xref
list. Read-only bytes `0x006C6500..0x006C65FF` confirm allocation/binding,
`player+0xFC` guards, seek to a selected frame shifted by 8, then advance using
`lhu player+0x94`. The preserved parser function ends at `0x006C6494`; that
boundary is not the end of the retail routine.

The two streamed operations have a much smaller direct-call census. Exact
JAL searches for `18 D3 06 0C` (step) and `F0 7F 06 0C` (restart) found one
resident step at `0x001A05C8`, two play-loop restarts at `0x001A0750` and
`0x001A077C`, and one marker-driven restart at `0x001B4E94`, after removing
resident aliases. Neither encoding appeared in BTL or ETC. This supports the
worker/marker ownership recorded above; it does not exclude indirect calls
or callers that start a worker through a higher-level request API.

[BTL scene playback owners](scene_playback_owners_btl.md#summary) classifies
189 of the 214 BTL seek sites by owner and policy. The 25 remaining sites
are unresolved leads at preserved
`0x00828020/0x008280DC`, `0x0082A830/0x0082A870`,
`0x0082C1F0/0x0082C258/0x0082C3DC/0x0082C44C/0x0082C80C/0x0082CA60`,
`0x00844E4C`, `0x008456E8`, `0x00848224`,
`0x00860DF8/0x00860E88/0x0086129C/0x008613E0/0x00861954/0x00862F5C`,
`0x0086582C`, `0x00869F38`, `0x0086B9F4`, `0x0087264C`,
`0x008742AC` and `0x0087C554`. They have no owner classification; their
surrounding gates, function boundaries and lifetimes are not recovered.

## Owner-stored cursor restoration wrappers

**Observation:** resident `FUN_0037E6B0` operates on a compact owner record
`{player at +0, completion at +4, integer cursor at +8}`. Each update first
seeks the player to `owner+8 << 8` with callback flag 0, advances by unsigned
halfword `player+0x94`, runs the composition helper `FUN_001BB6F0`, stores
the result at owner `+4`, and saves `player+0xEC >> 8` at owner `+8`.
`FUN_0037E760` seeks to that saved whole frame again, then calls submission
`FUN_001BB790` without a further advance.

This record owns a logical whole-frame cursor even though the pointed-to
player contains a fractional cursor. Seek here restores the owner's pose for
both update and submission; it is not necessarily an interactive timeline
command or restart. The wrapper itself supplies no pause predicate.
Whether multiple records share one player is determined by its constructors
and callers, not by the seek API alone. Resident analyzed xrefs, exact direct
JAL searches, and literal-pointer searches found no callers of either wrapper.
Their local update/submission contracts are established; their use by a
scheduled retail owner is unresolved. This is not an indirect-call absence
proof.

**Evidence:** complete disassembly `0x0037E6B0..0x0037E75C` and
`0x0037E760..0x0037E7B0`; seek calls at `0x0037E6E4` and `0x0037E78C`,
advance at `0x0037E714`, submission at `0x0037E798`.

## Fighter animation ownership

**Observation:** resident `FUN_0024D1C0` advances fighter-owned player
`fighter+0xE70`. It selects/binds a changed animation through `FUN_00218060`,
derives the step from fighter unsigned-halfword rate `+0xB90` multiplied by
float `+0x1AC`, and writes its truncated low halfword to player `+0x94`.
State `fighter+0x18E == 7` substitutes an overlay-provided rate before that
multiply. A latched end result `fighter+0xB88 != 0` forces the step to zero.
The caller still invokes advance with that zero step and dispatches the
event list through `FUN_001BB190(player, fighter)` afterward.

The upstream `FUN_0024DA50` gates the main fighter animation pass on fighter
byte-0 bit 1 and signed `fighter+0x20C < 1`. Inside the active-object branch,
an auxiliary player at `fighter+0xB30` has its own predicates (nonzero
`+0xB10` and auxiliary completion word `+0x14 == 0`) and is advanced later,
outside that main-player hold gate. A main fighter animation hold therefore
does not establish a hold of every animation attached to the fighter.

`FUN_00218060` is explicit animation setup, not a periodic increment producer.
It binds a selected descriptor with blend duration zero, optionally seeks to
fighter start frame `+0xB94 << 8`, and uses seek flag 0 or 1 according to byte
`+0xB96`. With a nonzero callback-enabled start it installs `FUN_002145B0`
and dispatches through `FUN_001BB190`. A rate below `0x100` with configured
start zero instead seeks to `0x100` with flag 1. It clears the owner's two
loop-observation bytes at `+0xB97/+0xB98`; the advance pass detects an integer
cursor decrease and updates them. Phase ordering and hit-response ownership
remain in [Hit response](../gameplay/combat/hit_response.md).

**Evidence:** decompilation of `FUN_00218060`, `FUN_0024D1C0`, and
`FUN_0024DA50`; direct advance sites `0x0024D32C` and `0x0024DC74`, setup
seek sites `0x002180E0`, `0x00218108` and `0x00218164`.

## Generator child ownership

**Observation:** resident `FUN_0034AB30` distinguishes a child resource kind
at owner `+4` and playback mode byte `+0x70`. For animation kind 2, mode 0
skips advance, mode 1 advances only before the last integer frame, and mode 2
advances then explicitly seeks to zero and advances again when the cursor
reaches at least `F-2`. Each advance uses child player `+0x94` and is followed
by `FUN_001BB6F0`. This owner-level repetition differs from the descriptor's
automatic loop policy.

Child reuse in `FUN_0034CF70` seeks the existing player to zero when the
incoming animation descriptor matches; a changed descriptor instead calls
`FUN_001B99B0`. Resource-kind changes destroy the old child before allocating
the replacement. These are spawn/reuse/reset operations, not periodic steps.
The generator algorithms and broader child lifetime belong to
[Particle and emitter runtime](rendering/particle_runtime.md).

**Evidence:** decompilation of `FUN_0034AB30` and `FUN_0034CF70`; advance
sites `0x0034AC90`, `0x0034ACC4`, `0x0034AD34`, seek sites `0x0034AD10`
and `0x0034D5D8`.

## Additional resident increment producers

| Owner path | Periodic operation and local gate | Setup/reset relationship |
| --- | --- | --- |
| Alternate-output owner, `FUN_001C7700`, player at owner `+0x90` | Requires nonnull player and nonzero player `+0xFC`; advances by unsigned player `+0x94`, passes the owner as the third argument, then composes. | `FUN_001C67E0` allocates/binds that player and performs the same advance/composition once after constructing its output controllers. These advances target owner output rather than the ordinary third-argument-zero path. |
| Lifetime-limited owner, `FUN_00212740`, player at `+0xB0` | Lifetime `+0x6C == 0` returns without advancing; positive values decrement. Completion `+0xB4 != 0` writes step zero, but advance/composition still run for a valid player. | Each active invocation updates owner state through `FUN_002120F0`, records completion, and increments owner counter `+0x68`. A zero step and an omitted invocation are different owner policies. |
| Scene-linked resident owner, `FUN_00396220`, player at `+0x28` | Computes `owner.float(+0x2C) * owner.float(+0x30) * scene.float(+8)` and stores the truncated low halfword at player `+0x94`; valid players then advance/compose. | The formula is an increment producer. This routine has no separate local pause predicate; a zero multiplier supplies a zero increment. The meaning and producers of the scene multiplier are not established here. |

**Evidence:** complete decompilation of `FUN_001C67E0`,
`FUN_001C7700`, `FUN_00212740` and `FUN_00396220`. The unsigned-halfword
load is significant: a stored negative halfword is not a signed reverse step
at the ordinary advance call.

Cleanup of the alternate-output owner is separately confirmed in
`FUN_001C6BB0`: it destroys player `+0x90` through `FUN_001B7570(...,1)` and
clears that pointer, releases/clears output controllers `+0x94/+0x98/+0x9C`
and `+0xA0`, and optionally frees the owner according to its destruction
argument. This retires ownership; seeking, setting the step to zero, or
clearing an end latch does not perform that teardown. Player internals remain
owned by the linked animation/CCS documents.

## Resident explicit-seek classification

All 35 resident direct seek sites belong to the inspected functions below.
This is complete classification of that direct-call census, not complete
classification of resident advance callers or indirect scheduling. `F`
denotes the descriptor frame count. Seeks at or beyond `(F-1)<<8` still use
the descriptor's end/loop policy; the requested endpoint alone does not prove
a held last pose. Flag 0 suppresses the command callback for seek evaluation,
not every effect-manager update; [Animation runtime](animation_runtime.md)
owns those internals.

| Owner / functions | Phase and seek purpose | Resident seek sites |
| --- | --- | --- |
| Two-descriptor controller, `FUN_001DEB50`, player `+0x1C` | Explicit selector 3 binds descriptor `+0x24`, requests `F<<8`, then stores selector state 4. Selectors 1/2 instead bind and advance/compose once. | `0x001DECDC` |
| Fighter animation setup, `FUN_00218060` | [Start-frame/callback selection](#fighter-animation-ownership). | `0x002180E0`, `0x00218108`, `0x00218164` |
| Fighter-associated presentation, `FUN_002455B0`, `FUN_002466D0` | State-transition reset: rebinds paired players in a shared presentation record and seeks its third players at `+8/+0x78` to frame 1. `002455B0` also resets outer player `+8`. These operations reset presentation state, not the primary fighter player `+0xE70`. | `0x0024584C`, `0x002458A4`, `0x002458FC`; `0x00246848`, `0x002468A0` |
| Fighter auxiliary, `FUN_00245C60`, `FUN_00247860` | Action setup binds the player in the auxiliary record at fighter `+0xB30`, clears its completion word `+0x14`, and starts at `0x900` (frame 9). The periodic auxiliary gate is described above. | `0x00245D08`, `0x00247AC8` |
| Fighter-attached secondary, `FUN_0027EB80`, player `+0x582C` | On update, follows the primary descriptor, copies its step, and advances/composes. When the descriptor agrees and the recovered unsigned integer-cursor difference meets the `>=2.0` comparison, seeks to primary integer cursor `<<8`. This is synchronization correction after advance. | `0x0027EC88` |
| Companion animation record, `FUN_002AD430`, player `+0x78` | Explicit descriptor selection and optional seek to fighter start halfword `+0xB94<<8`; then resets the companion's local timer through `FUN_002117A0`. | `0x002AD508` |
| Resource owner, `FUN_0030ED40`, player `+0x1A0` | Explicit frame selection for resource kinds 1/4. Masks request to 16 bits, replaces out-of-range values through the random/modulo path, changes selected zero to one, then seeks. Kind 3 stores an index instead of seeking. | `0x0030EE54` |
| Same resource owner, `FUN_003108A0` | Update requires player nonnull, resource kind 1/4 and byte `+0x1EC == 0`. Advances until completion byte `+0x1AF` is set; repeat byte `+0x1AC` then seeks to frame 1. Without repeat, byte `+0x1AD` can invoke virtual slot `+0x18`. | `0x00310994` |
| Pool reuse, `FUN_003337D0` | Selects an inactive `0x210`-byte record, resets/relinks it, then seeks its player `+0x1A0` to zero. Newly allocated records follow the separate construction path. | `0x003338F8` |
| Generator child, `FUN_0034AB30`, `FUN_0034CF70` | [Owner repetition and spawn/reuse reset](#generator-child-ownership). | `0x0034AD10`, `0x0034D5D8` |
| Compact cursor record, `FUN_0037E6B0`, `FUN_0037E760` | [Restore stored whole frame before advance and submission](#owner-stored-cursor-restoration-wrappers). | `0x0037E6E4`, `0x0037E78C` |
| Mode Select, `FUN_003849C0`, `FUN_003854F0` | Directional input arms arrow bytes `+0x88/+0x89` and seeks their players `+0x8C/+0x90` to zero. Update advances an armed arrow until completion, then clears its byte. Seven item players at `+0x98` advance only for the selected item with settled offset `abs(+0x28)<=0.01`; other items are sought to zero. | `0x00384A90`, `0x00384B20`, `0x00385978` |
| Sound Settings, `FUN_00389550` | Directional row change restarts player `+0x60` at frame 1. Accept/cancel return before the common decoration-advance tail. The reset-settings branch enters that tail without this seek. | `0x003899D4` |
| Scene-linked setup, `FUN_00396320`, `FUN_0039ABB0`, `FUN_0039B260`, `FUN_003A55F0` | Initial allocation/binding, one default-step advance/composition, caching the original unsigned step as a float, then configured-frame or `FUN_00180210(F-1)` seek. Players are at owner `+0x28`, except `0039ABB0` at `+0x2C`. These are setup positions, not periodic seeks. | `0x003965C0`, `0x003965E8`; `0x0039AE94`, `0x0039AEBC`; `0x0039B638`, `0x0039B660`; `0x003A5900`, `0x003A5928` |
| Moving-owner setup, `FUN_003AF5B0`, player `+0x34` | Resolves three descriptors, binds the first, establishes its transform, and seeks using `FUN_00180210(F-1)<<8`. | `0x003AF710` |
| Character Select finalized-state handler, `FUN_003B7FA0` | With owner `+0x90 != 0`, repeatedly requests frame 1 for players `+0x80/+0x84`; inspects a different player's `+0x94` cursor for an event. | `0x003B7FF8`, `0x003B8018` |

Every row is supported by decompilation of its listed
functions; the direct sites are from the deduplicated byte/xref census.
Screen identities are cross-linked to [Running help](../localization/ui/running_help.md),
[menu input mapping](menu_input/function_map.tsv), and
[Character Select](../game/character_select.md). UI geometry and transition
algorithms remain in [UI animation](ui_animation.md).

One setup family has an additional visibility gate: `FUN_003A5380`, the update
paired with `FUN_003A55F0`, skips playback for owner `+0x38 != 0` or an absent
player. With the player more than 6000 units from the inspected camera
position, fade `+0x40` decreases by `0.1`; once it would be negative, the
routine clamps it to zero and returns before producing/consuming the step.
Otherwise it uses the `+0x2C * +0x30 * scene+8` increment formula. This is a
local distance/fade gate; it does not establish a global pause policy.

## ETC explicit-seek owners

All three ETC seek JAL candidates have inspected surrounding code. The first
two belong to the same table-selected owner; the last belongs to a separate
five-slot selector. Their exact screen identities remain unresolved.

| Preserved function / live entry | Owner and phase | Seek policy |
| --- | --- | --- |
| `FUN_006BF820` / `0x006BF860` | Explicit descriptor selection for player `owner+0x1D4+index*4`, using container `owner+0x408` and a table row selected by `index%3`. | Selector argument zero binds the default descriptor and requests `F<<8` with flag 0. Other selector values bind then advance/compose once using player `+0x94`. The endpoint uses the descriptor's end/loop policy. |
| `FUN_006C0950` / `0x006C0990` | Update advances the selected `+0x1D4` player and secondary `+0x1B8` player independently, storing their end results at `+0x200` and `+0x1BD`. | When the secondary ends, the routine changes owner state `+0xC` to 1, rebinds the selected player to its default table descriptor, seeks to `F<<8` with flag 0, and clears the selected completion byte. This is an end-driven pose transition. |
| Preserved body fragment `FUN_006CE720` | Bounded loop over five nonnull player slots at owner `+0x40..+0x50`; selected slot comes from the owner's index/list fields. | The selected player advances/composes using its `+0x94` step. Every other valid player is repeatedly sought to `0x100` with flag 0. These are frame-1 requests for inactive slots. The fragment does not establish the enclosing method's entry or upstream scheduling gate. |

The ETC advance/seek paths above use third argument zero and check player
`+0xFC` before calling. **Evidence:** decompilation of the three preserved
functions and bytes `0x006CE720..0x006CE8AF`, which corroborate the
five-slot loop, unsigned step load, advance/composition pair, inactive seek,
and loop bound. Seek call addresses are preserved `0x006BF8BC`,
`0x006C0A80`, `0x006CE890` (live `0x006BF8FC`, `0x006C0AC0`,
`0x006CE8D0`). This exhausts the direct ETC seek candidates, not its advance
owners or indirect calls.
