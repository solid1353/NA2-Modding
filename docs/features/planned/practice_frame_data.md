# Practice frame-data display

This document owns provisional research for a Practice frame-data display.
No display or instrumentation is implemented. The useful boundary is an
observed action/event timeline; authored animation length alone cannot establish
startup, recovery, or advantage.

## Research coverage

- **Assigned scope:** Research a useful Practice frame-data display: source states and event boundaries for startup, active/recovery phases, hit/guard advantage, hitstop and actionable state, with animation-rate/physics/60FPS implications and limitations.
- **Exploration depth:** Direct read-only MCP inspection of the common action, phase, timer, animation, volume-publication, pair-outcome and accepted-response paths; complete Naruto definition-57 census of 49 action records and 193 phase rows. Character-specific coverage is bounded to the common dispatch interfaces, not every override.
- **Confirmed coverage:** Distinct engine, fighter and animation clocks; action/phase resets; two-slot volume activity with inclusive/rate-dependent ranges; ordinary query publication followed by next-pass consumption; separate outcome and response-entry boundaries; state-entry, guard and candidate gates differ; fixed-rate pause and scaled action-lock maintenance.
- **Unresolved or untested:** Exact move frame values, complete per-action candidate readiness, collision timing outside the bounded ordinary list path, projectile/auxiliary activity attribution, every character override, and display placement remain incomplete.
- **Deliberate exclusions and overlap:** Implemented Practice behavior remains owned by [Practice](../practice.md). Retail architecture remains owned by [Practice-mode knowledge](../../knowledge/gameplay/practice_mode.md). Retail contracts belong to [Combat action execution](../../knowledge/gameplay/combat_action_execution.md), [Hit response](../../knowledge/gameplay/hit_response.md), [Shared timers](../../knowledge/runtime/timer_primitives.md), [Animation runtime](../../knowledge/runtime/animation_runtime.md), [Input interpretation](../../knowledge/gameplay/action_commands.md), and [Battle HUD](../../knowledge/gameplay/battle_hud.md); this document records their implications for the proposed display.
- **Evidence limitations:** Static retail inspection only. No move frame values, executable instrumentation, or observed display result are claimed. Linked campaign documents have their own evolving coverage; conclusions here use the stated MCP evidence and established retail contracts, never uninvestigated wording.

## Evidence coordinates

The target is clean NA2 `SLPS_258.37` and `PRG/BTL.BIN`, identified in
[Retail game file identities](../../knowledge/game/files/file_identities.md).
Resident addresses below are live EE addresses. An overlay MCP address is
`live - 0x40`; complete BTL file offsets are `live - 0x006B3F00`.

## Action identity and clocks

The proposed observation identity needs fighter identity, major state, action
index, phase, current action record, and entry occurrence. Resident
`FUN_00217E40` (`0x00217E40..0x00218050`) stores major `+0x18E` and index
`+0x190`, resets the primary block at `+0x1B8` on a changed major/index, and
calls live BTL `0x0071EEF0` to reset the phase. A forced re-entry can reset
the same major/index. Comparing only the index would miss that occurrence.
Major `8` obtains the current descriptor from fighter `+0xA4C`.
Cleanup and new-state initialization run before the setter's same-state early
return; a no-change return does not imply no side effects. Entry accounting
must distinguish a requested state from an entry that actually resets cursors.

Direct disassembly of `FUN_0024D5E0` (`0x0024D5E0..0x0024D820`) shows that
positive pause count `+0x20C` prevents both timeline advances. Otherwise the
primary integer cursor `+0x1C4` advances by fighter scalar `+0x1AC`, while
the secondary cursor `+0x1E8` advances by `+0x1AC * (+0xB90 / 256)`.
The latter can reset independently when `+0xB98` requests it. Neither cursor
is a universal elapsed-frame counter.

The common phase updater, live BTL `0x0071F160` (MCP
`FUN_0071f120`), uses major-8 records of `0x4C` bytes through action
`+0x50`, versus `8`-byte records for other majors. It advances phases on
positive secondary-cursor thresholds, animation completion (`+0xB88`),
ground contact, or vertical velocity, according to the signed gate at row
`+2`. Each transition resets the secondary timer and updates `+0xA50` to
the major-8 row's event portion at `+0x1C`. It reports completion when the
new row's first halfword is `-1`. This is phase completion, not proof that
all action candidates are available.

Gate `0` holds the phase. Negative gates outside `-0x10..-0x14`
perform a relative phase jump on animation completion, clamped at phase zero.
The updater makes at most one phase transition per call, so a phase table is
not necessarily a linear animation sequence.

**Display implication:** retain action elapsed updates separately from primary
and secondary cursor values, and keep an explicit action-entry occurrence.
Phase number should remain diagnostic metadata until its attack activity is
classified from consumers.

## Actionable is a qualified endpoint

Direct disassembly of resident `FUN_00239E50`
(`0x00239E50..0x0023A048`) confirms a state-entry predicate with selector
argument `a1`, rather than one unconditional actionable flag:

| Condition | Ordinary entry result |
| --- | --- |
| Action-lock count `+0x254 != 0` | rejected |
| Major `0` | allowed only for minor `0`, `3`, `4`, `5`, or `7` |
| Major `1` | allowed only for minor `0x0E..0x14` |
| Majors `2`, `3`, `4` | allowed after the lock check |
| Major `5` | minor `0x5B/0x5C` allowed; other minors require selector `2` |
| Major `6` | minor `0x5F` requires primary cursor `>= 8`; `0x60` requires `>= 3`; other minors rejected |
| Major `8` | rejected when current action type `+0x10 & 0x000C0000` is nonzero |
| Other major | rejected |

The major-8 check is the complete small helper `FUN_002440C0`.
The predicate does not check `+0x20C`. The pause/input ordering and reaction
exits remain owned by [Hit response](../../knowledge/gameplay/hit_response.md#fighter-update-pause-and-action-lock).
A true predicate during pause therefore cannot by itself mean an ordinary
action update will execute on that tick.

The ordinary selector `FUN_0023A390` also requires its input family, a
non-`-1` selector mode, `+0xB34 == -1`, and another state gate before
matching action data. It then validates a concrete record through
`FUN_00244190` (`0x00244190..0x002445C8`): action cost, category, ground/air
context, effects, and manager state can still refuse it. The validator has
side effects on failure (feedback and `+0x19C`), so invoking it just to draw
an availability indicator would alter retail behavior.

**Provisional metric:** expose the lock and state-entry gate as qualified
diagnostics. Any eventual advantage endpoint must name the allowed action
class and account for its scheduling gate. A generic green "actionable"
indicator or subtraction of `+0x254` values is not yet justified.

Guard is a different endpoint. Direct `FUN_00228320` inspection shows that
major `8` cannot initiate ordinary guard even when the state-entry predicate
allows action selection; majors `5..7` also reject guard initiation. Guard
requires zero lock, its own major/minor gates, additional `+0x9F0` and
`FUN_0022D5B0` gates, and grounded context for stance entry. Existing guarded
reactions `(0,6/7)` bypass that input-side path. Therefore attack-entry
advantage and guard-ready advantage must remain separately qualified values.

## Ordinary fighter activity source

Resident `FUN_0024DE40` establishes the common fighter-volume boundary.
While the fighter is enabled, its scheduling flags allow this late pass, and
pause count `+0x20C < 1`, it examines the current event pointer `+0xA50`.
Major `8`, event flags bit `0x2`, and clear exchange-role mask
`+0xB00 & 0xFF00` cause two calls to `FUN_0021FC70`, for slots `0` and `1`.
Each event slot is `0x18` bytes; the second follows the first. Otherwise both
nodes in the fighter's `+0xDF4` list are disabled through `FUN_001DCD10`.
The timelines advance only after this work. Thus a phase event can carry two
different activity intervals, and event flag `0x2` alone is insufficient.

The complete `FUN_0021FC70` consumer establishes these slot fields:

| Event-slot offset | Consumer meaning |
| ---: | --- |
| `+4`, `+6` | Signed start/end bounds; either `-0x7FFF` disables the slot. Negative bounds are resolved relative to phase/animation extent and start offset, then clamped at zero. |
| `+8` | Radius copied to the slot-specific volume field `+0xC98 + slot * 0x50`; the spherical record layout is established by the linked Collision contract. |
| `+0x0C` | Attachment-name pointer; a nonempty name must resolve through scene lookup before the node is enabled. Empty name uses the fighter transform. |
| `+0x10`, `+0x14` | Placement components used to form the published volume position. |

The range decision uses secondary timer `+0x1DC` through
`FUN_00211BA0` or its modulo sibling `FUN_00211C80`, depending on animation
flags. Both inspect old and current integer cursors and inclusive ranges,
including intermediate integers when a step skips more than one. The consumer
has additional handling for scene rates above and below `0x0100`: at slow
rates it replaces the timer decision with a scene-cursor range check after
incrementing finite bounds. A static `(start,end)` pair therefore cannot be
reported directly as an update count without replaying the proven consumer
semantics.

On success it enables the slot's list node through `FUN_001DCCC0` and writes
the current action pointer through `FUN_00222A30`. Failure disables the same
node through `FUN_00220210`. The enable/disable leaves manipulate list
membership and node word `+0`; they are not contact or damage events.

**Provisional metric:** a per-update activity strip based on the actual two
published fighter nodes, attributed to the action occurrence that enabled
them. Startup ends at the first such enable; activity is the union of both
slots' enabled intervals, preserving gaps and later reactivation. This would
measure common fighter-volume publication, not guaranteed hit detection or
projectile lifetime. During fighter pause this path does not rebuild the nodes;
unchanged enabled nodes need a separate pause marker rather than being counted
as new advancing attack frames.

## Contact outcome and recovery boundaries

Direct disassembly of battle service `FUN_001F03E0`
(`0x001F03E0..0x001F0AA0`) places query processor `FUN_001DE1C0` at
`0x001F0A68`, after all three graph passes and the HUD work. That processor
clears old list results, then publishes new directional overlap results.
The next ordinary fighter first pass, `FUN_0024FD80`, consumes those lists
through `FUN_0021E700` before input/action processing. Under uninterrupted
ordinary dispatch, the inferred sequence is publication and overlap query on
update `k`, followed by pair arbitration and response routing on `k+1`.
This is a bounded call-order conclusion, not a universal one-update latency
for every source or scheduling state. Volume startup and accepted-contact
startup therefore need separate event positions.

`FUN_0021E700` consumes collision result lists before the pair resolver.
`FUN_0021ED70` then edits both fighters' `+0xE3C` masks for clashes,
counter opportunities, rejection, and source validity. Raw hit-bit transitions
alone are therefore unsuitable as a successful-contact counter.
`FUN_0021F610` classifies the pair outcome, returning ordinary `1`, guarded
`-1`, rejected `0`, or the separate `-2` branch, and writes short-lived
outcome bytes through `FUN_002391D0` at fighter `+0xA40/+0xA42..+0xA44`.
These are useful outcome observations, not proof that response entry happened.

The response-entry seam is `FUN_002209A0`: after its rejection gates, it
selects `FUN_00232B80` or `FUN_00228760` from the final guard state
`+0x95A`. Router modes include ordinary paired fighter, auxiliary source,
and projectile source. Source object `+0xE58` and retained attack
`+0xE54` must accompany an outcome so that an independent projectile hit is
not attached to the fighter's newly selected action. The
[Hit-response contract](../../knowledge/gameplay/hit_response.md#accepted-hit-routing)
owns all routing details and the
[Collision contract](../../knowledge/gameplay/collision.md) owns candidate generation.

The major-8 exit dispatcher `FUN_0023B280` can dispatch a staged action
`+0xA3E` when current event flags contain `0x20`, before the ordinary
completion exit. Other branches use exchange state, paired state, landing,
or specialized action handlers. Its ordinary `FUN_0023BDC0` exit selects
neutral when grounded or airborne major `3` otherwise; mode `2` selects
landing state `(4,0x26)`. A cancelled action, a landed action, and an
uncancelled animation completion have different endpoints.

**Provisional interpretation:** recovery is the time after the final owned
activity interval until a specified ordinary action can enter, with a separate
cancel/landing marker. Hit or guard advantage is a paired measurement from
the same accepted-contact occurrence, `defender_ready_tick -
attacker_ready_tick`, so positive means the attacker becomes ready earlier.
Both endpoints must use the same clock and readiness definition. The contact
type must be taken from the branch actually entered, and the result remains
incomplete while either endpoint is unknown. Authored animation duration,
lock difference, and the latest retained outcome byte cannot supply that
measurement on their own.

## Bounded authored-data audit

Definition 57 (Naruto) at resident `0x004DAD80` identifies 49 action
records at `0x004D9D50..0x004DAD63` and 193 `0x4C`-byte phase rows at
`0x004D61F0..0x004D9B3B`. All bytes of both arrays were read through MCP;
each of the 49 authored entry indices reaches a terminal row within that
bounded array. Setup copies and adjusts this data through `FUN_00218FE0`,
including configured jutsu providers, so this is an authored-table audit,
not a claim about an arbitrary live fighter's final table.

Of the 193 rows, 52 are terminal and 141 nonterminal. Nonterminal phase gates
are animation end `-0x10` on 90 rows, ground contact `-0x11` on 19, hold
`0` on 16, and positive thresholds on 16. Rates range from `128` to `1024`
(nominal `/256` factors `0.5..4.0`); 115 nonterminal rows use `256`.
There is no single fixed phase count or rate applicable to this table.

Among nonterminal rows, 62 set payload bit `0x2`: 44 have one non-disabled
volume range, 13 have two, and five disable both. Those five are rows
`4`, `10`, `124`, `130`, and `166`. Of the 70 non-disabled slot ranges,
32 contain a negative endpoint; six two-slot rows use differing ranges.
These are authored range counts, not active-frame counts.

| Action slot / authored rows | Observation relevant to a display |
| --- | --- |
| `21`, rows `104..106` | First row has slot-0 bounds `4..5`, rate `256`; the second row has both slots disabled and flags `0x28`. The final row is terminal. Bounds are secondary-cursor data, not a measured startup value. |
| `24`, rows `113..115` | First row has slot-0 `8..-1` and slot-1 `8..8`; the next has slot-0 `0..1`. Activity spans separate phases and uses relative bounds. |
| `27`, rows `123..126` | First row uses `8..12` and `23..28`; the middle row sets bit `0x2` but disables both slots; the next uses two `0..8` ranges at rate `400`. A continuous active band would hide a real authored gap. |
| `28`, rows `127..129` | Slot bounds `-3..-1` and `-2..-2` require animation/phase extent resolution. |
| `29`, rows `130..133` | Its bit-`0x2` first row disables both ordinary slots; later rows hold or complete differently. No ordinary-volume startup value follows from this record alone. |
| `48`, rows `189..192` | Two initial rows have flags `0x10` and rate `320`, with positive then animation-end progression; the next has flags `0x2A`, rate `288`, and slot-0 `0..1`. A non-unit-rate startup is present even in this bounded ordinary category. |

This census establishes concrete reasons to derive activity from consumers.
It does not establish move names, final configured availability, projectile
spawn time, attachment success, or hit/guard advantage.

## Pause, scheduling and display units

The checked `FUN_00224510` pause initializer uses attack halfword `+0x30`,
pending flag `+0x202 & 4`, sentinel `0x7FFF`, and caller mode to choose
immediate versus staged activation. The maintenance order in
`FUN_0024C440` checks pause before decrementing action lock by `+0x1AC`,
then activates or decrements the pause by fixed `1.0`. Sampling only the
signed pause count can mistake a staged negative value for no forthcoming
freeze. Attacker, ordinary receiver and guarded receiver do not share one
activation edge; the full sequence and fallback arbitration are in
[Hit update order](../../knowledge/gameplay/hit_response.md#hit-update-order-and-elapsed-updates)
and [Guarded response](../../knowledge/gameplay/hit_response.md#guarded-hit-transitions).

**Provisional metric:** show each fighter's pause count, pending activation,
and accumulated updates in which the relevant action/animation passes were
suppressed. Keep the pause marker separate from advancing activity. Report
lock count as "action lock", not total hitstun; accepted-hit rejection
`+0x230` is a third channel with its own purpose.

The engine ordinal at system context `+0x194` increments in
`FUN_001081B0` before pad publication and before battle service. Direct
`FUN_001F03E0` inspection confirms separately masked first, second and third
passes; fighter-owner slot `2` uses mask bit `0x4`, with update and late update
from session `+2` and its middle pass from `+4`. The ordinal can advance
while fighter work is suppressed. The
[Selective update gates](../../knowledge/gameplay/pause_and_replay.md#selective-update-gating)
own the complete mask contract. An elapsed-action clock therefore needs
dispatched battle updates and scheduling markers; an engine-ordinal
subtraction alone includes unrelated pause/menu time.

Within dispatched fighter work, the checked order is maintenance and accepted
hit routing; phase/exit processing, input selection and action update;
movement and animation; late volume publication; then timeline advancement.
A proposed readiness sample belongs at the actual input-consumption boundary
after phase/exit processing. A sample during drawing sees later cursor and
animation state. Contact events must be retained when their routing branch
is reached rather than inferred later from a final state snapshot.

`FUN_0024D1C0` (`0x0024D1C0..0x0024D3B0`) multiplies unsigned rate
`+0xB90` by fighter scalar `+0x1AC`, converts with actual EE `cvt.w.s`,
stores the low 16 bits as scene `+0x94`, and calls `FUN_001BB210`. An
already completed animation sets that increment to zero. Fractional timer
advancement and this quantized animation step can consequently differ.
The scalar itself is the global rate or local override `+0x1B0`, multiplied
by `+0x1B4` when that differs from `1.0`, as checked in maintenance.

Retail's mode-loop call at `0x001E11C4` supplies step `2`; the setter
`FUN_00107560` writes context byte `+1`, and `FUN_001083A0` waits until
the VBlank count reaches it. At nominal retail pacing, one dispatched battle
update is the 30-Hz unit described by
[Battle update cadence](../../knowledge/gameplay/battle_lifecycle.md#battle-update-cadence).
The display should name that unit explicitly. Authored animation frames,
VBlanks, and dispatched updates are distinct.

For a future 60-FPS configuration, the
[60 FPS investigation](60_fps.md) owns
timing changes. This proposal would retain both simulation progress and
presentation/update ordinals, along with effective rate and schedule markers.
Doubling a displayed frame number or halving animation lengths cannot by
itself account for fixed-`1.0` pause, fractional lock, integer event crossings,
and quantized scene playback. Contact/landing-dependent phase gates also need
the actual movement outcome; the
[Movement contract](../../knowledge/gameplay/movement_and_physics.md) and
[Response gravity and airtime](../../knowledge/gameplay/hit_response.md#gravity-and-airtime)
own those facts. No universal 60-FPS conversion or landing recovery constant
is established here.

## Provisional display scope

A useful first display would retain an observation timeline and show derived
values only when their endpoints are established. The following are proposed
metrics; none has been implemented or measured in this investigation.

| Proposed value | Required observation | Current research limit |
| --- | --- | --- |
| First ordinary activity | Action entry occurrence to first owned slot publication | Use elapsed update offsets, with entry at offset zero. An action without ordinary slot publication has no value for this metric. |
| Activity strip | Separate slot-0/slot-1 publication intervals, their union, and pause markers | Preserve gaps and later reactivation; attachments and query eligibility still affect whether a published slot produces a candidate. |
| Accepted contact | Actual ordinary-hit or guarded-response branch, source object and retained attack | Distinguish query publication, pair outcome and accepted response; independent sources need their own action attribution. |
| Recovery and advantage | Final owned activity plus separately qualified readiness endpoints at input consumption | A lock-free state alone does not establish either endpoint. Candidate-dependent readiness remains incomplete. |
| Pause and rates | Pending/active pause, suppressed fighter passes, effective fighter scalar and animation rate | The counters use different units; show their identities rather than combining them into one duration. |

The timeline should keep dispatched battle-update offsets and advancing
action progress separate. This makes paused activity and elapsed advantage
assessable without silently changing the meaning of a frame when rates differ.
The active unit and readiness class should accompany any derived number;
unknown endpoints should remain unknown rather than being replaced with
animation length or a countdown.

The checked [HUD order](../../knowledge/gameplay/battle_hud.md#battle-session-ownership-and-order)
allows presentation after the fighter's update passes, but that snapshot
already follows phase changes and timeline advancement and precedes the
tail collision query. An eventual display would need retained events from
the earlier seams. Existing HUD ownership, hide/show transitions and resource
lifetime belong to that contract; this investigation has not established a
Practice-only placement, text budget or lifetime for additional display state.

The bounded pass establishes source seams and concrete authored-data hazards.
Turning them into complete frame values still requires tracing the selected
readiness classes through their remaining candidate gates and covering source
types and character callbacks outside the common fighter path. That work
cannot be replaced by a static scan of phase lengths.
