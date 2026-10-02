# Combat action execution

This document investigates combat action execution in retail NA2
(`SLPS-25837`).

## Research coverage

- **Assigned scope:** Execution after a selected action enters the fighter: ordinary action/phase dispatch, authored event/row consumers, attack activation, combo continuation, cancel/interruption rules and the boundary with character overrides.
- **Exploration depth:** Inspected common action entry/cleanup, phase progression and animation selection, motion/event consumers, transition/update dispatch, attack publication and all eleven recovered resident callers, and two input-interruption predicates. Read all 94 definition-table entries and every counted action/phase array of their 78 distinct nonzero definitions; checked row indices, forward terminal bounds, and all relative-jump records.
- **Confirmed coverage:** Major-8 entry ordering and field ownership, separate action/phase clocks, 0x4C-byte row layout, phase conditions and loops, common continuation/exit gates, two attack-bank activation windows, and character-specific scene/timer selection are established below.
- **Unresolved or untested:** Condition-zero phase lifetimes, full exit conditions of every authored loop, alternate indirect attack registrations, every payload flag's meaning, and player-facing durations remain unresolved. The census proves array bounds, not reachability of every record.
- **Deliberate exclusions and overlap:** [Action commands](action_commands.md) owns input matching, action-record selection, and setup; [Character action callbacks](character_action_callbacks.md) owns character callback algorithms; [Hit response](hit_response.md) owns accepted-hit reactions; [Extra Hit](extra_hit.md) owns the paired exchange; [Throws and captures](throws_and_captures.md) owns category-`0x100/0x200` capture coordination; [X-dash](xdash.md) owns the category-`2` state machine; [Ultimate Jutsu](ultimate_jutsu.md) owns that execution family. [Battle entities](battle_entities.md) owns allocation and fighter-class tables. Complete-file identities remain in [Retail game file identities](../game/files/file_identities.md).
- **Evidence limitations:** Static code and bytes establish control flow, not observed animation outcomes. Preserved BTL imports have incomplete function boundaries/xrefs; raw operands retain live addresses. Unexamined character paths remain unknown.

## Evidence convention

Address conventions follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).
BTL addresses below are live EE addresses unless explicitly labeled `D`
(Ghidra imported byte address). Function names are analysis labels, not
recovered source names.

## Action entry and state ownership

Resident `FUN_0023A9A0` finishes accepted-record dispatch with
`FUN_00217E40(fighter, 8, index, mode)` at `0x0023AE84`. The record is
`fighter[+0xA54] + index * 0x54`; record selection and validation belong to
Action commands. State setter `FUN_00217E40` calls old-state cleanup
`FUN_00217BD0`, then new-state initialization `FUN_00217D30`, **before** its
same-state early return. Therefore a zero return for an unchanged state is
not proof that cleanup and initialization did not run.

For major 8, initialization calls `FUN_00238A70`: it stores the selected
index at signed halfword `+0xA3C`, current record pointer at `+0xA4C`, clears
pending continuation `+0xA3E` to -1, and clears four outcome/auxiliary bytes
`+0xA40/+0xA42/+0xA43/+0xA44` through `FUN_002391B0`. It also clears
`+0xE50`, resets the opponent's retained `+0xE54` if it equals this action
record, and routes category masks `0x2`, `0x100`, and `0x200` to separate entry
helpers. These operations occur while the old major/substate is still stored.

The setter then writes signed major `+0x18E` and action index/substate
`+0x190`. A changed major or substate resets the primary timeline block
`+0x1B8` and calls live BTL `0x0071EEF0` (D `0x0071EEB0`) to set phase
`+0x192` to zero and reset the secondary block `+0x1DC`. A nonzero mode
forces the substate comparison to treat the prior value as -1. For major 8,
the setter publishes the current action record as descriptor `+0xA30`;
native substates below `0x66` instead use the 8-byte descriptor at live
`0x0089AEB0 + substate * 8`. It sets contact-history byte `+0xB9C` to 1
when grounded (`u8(+0x63) & 0x80`), otherwise 2.

### Confirmed execution fields

| Fighter field | Width | Contract established in the traced code |
| --- | --- | --- |
| `+0x18E/+0x190/+0x192` | signed 16 bits each | Major, substate/action index, phase |
| `+0x1AC` | float | Effective fighter update delta used by the two timelines |
| `+0x1C4` | signed 32 bits | Primary action cursor; reset on changed/forced action entry |
| `+0x1E8` | signed 32 bits | Secondary phase cursor; reset on phase change |
| `+0xA30` | pointer | Current descriptor; current 0x54-byte action record for major 8 |
| `+0xA3C/+0xA3E` | signed 16 bits each | Current selected index and pending continuation index (-1 when absent) |
| `+0xA4C` | pointer | Current action record |
| `+0xA50` | pointer | Current 0x4C-byte phase row's attack payload at row +0x1C |
| `+0xB84` | pointer | Animation-object pointer table |
| `+0xB88` | 32 bits | Animation-end result consumed by phase progression |
| `+0xB90/+0xB94` | 16 bits each | Phase animation/secondary rate and start frame |
| `+0xB98` | byte | Primary-animation wrap notification consumed by the timeline update |

## Shared phase progression

Live BTL `0x0071F160` (D `0x0071F120`) reads a phase row from
`descriptor[+0x50] + max(phase,0) * 0x4C` for major 8. Other majors read
`descriptor[+4] + max(phase,0) * 8`. The first eight bytes have the same
four-halfword contract in both forms:

| Row offset | Interpretation |
| --- | --- |
| `+0x00` | Signed animation slot; -1 marks terminal row |
| `+0x02` | Signed progression condition |
| `+0x04` | Signed animation start frame |
| `+0x06` | Animation and secondary-timeline rate, interpreted by consumers as /256 |

Conditions `-0x10..-0x14` mean animation end, grounded, descending or
grounded, animation end or grounded, and animation end and grounded,
respectively. Positive values advance when secondary cursor `+0x1E8`
reaches the value; zero holds. Every other negative value is a **relative
phase jump on animation end**, clamped to phase zero. The common updater
performs at most one change per call, resets `+0x1DC`, refreshes major-8
`+0xA50` to the new row +0x1C, then returns whether the resulting row's
animation slot is -1. The explicit setter at live `0x0071EEF0` and increment
helper at live `0x0071EF70` perform the same reset/publication without
evaluating a progression condition.

Live `0x0071F640` (D `0x0071F600`) selects phase animation only at the
secondary block's zero event and when its flag `0x0008` is clear. For a
nonterminal row it calls resident `FUN_00218190`, writes the start frame to
`+0xB94` (negative authored values add the animation's frame count), and
copies rate to `+0xB90`. Animation evaluation belongs to
[Animation runtime](../runtime/animation_runtime.md); response-specific phase
tables remain in Hit response.

### Action and phase clocks

The common late pass calls `FUN_0024D5E0` **after** ordinary attack
publication, fighter virtual slot `+0x2C`, and callback channel 6. With no
positive pause it advances primary block `+0x1B8` by fighter delta `+0x1AC`
and secondary block `+0x1DC` by `u16(+0xB90) / 256.0 * delta`. Rate
`0x100` takes the equivalent direct-delta branch. These are separate cursors:
an action-level event can continue across phase changes while a phase-level
event starts from zero again.

`FUN_0024D1C0` writes the truncated product
`u16(+0xB90) * delta` to primary scene rate `+0x94`, stores the previous
scene frame in fighter `+0xB92`, and publishes the animation-end result at
`+0xB88`. If the resulting frame wraps below the saved frame, it sets
`+0xB98`. On consuming that notification, `FUN_0024D5E0` skips one
secondary advance. For a condition-zero phase it additionally resets that
block's integer/fractional positions and assigns flags `(flags & ~0x4) | 0xB`;
mask `0x8` inhibits the ordinary phase-animation restart described above.

During positive pause, the late timeline update clears only event flag mask
`0x2` in the two blocks. It does not erase their positions or remainder.
Shared rounding/crossing contracts belong to
[Timer primitives](../runtime/timer_primitives.md), and pause ownership to
[Pause and replay](pause_and_replay.md). Static invocation counts and authored
rates do not by themselves establish elapsed seconds or visible duration.

## Ordinary dispatch order

The fighter-list pass `FUN_0024FD80` gates action processing on node flag
`u8(+0) & 2` and no positive pause `+0x20C`. After hit routing and the
fighter virtual slot `+0x1C`, it calls input copy `FUN_00217320`,
`FUN_002173D0`, phase/transition dispatcher `FUN_00248580`, input action
dispatcher `FUN_00248EC0`, then per-action dispatcher `FUN_00249640`.
Entity scheduling and the higher owner belong to Battle entities and
[Battle lifecycle](battle_lifecycle.md).

`FUN_00248580` skips when fighter `+0x63 & 1` is set, applies
`FUN_0023EF50`, runs common phase progression, then switches on major:
major 8 reaches `FUN_0023B280(fighter, terminal)`. Major 5/6 routes to the
response/recovery owners. The later `FUN_00249640` first calls
`FUN_00217670` for channels 2 and 3, then routes major 8 to
`FUN_0023BAC0`, and finally selects phase animation through live
`0x0071F640` and invokes the embedded animation object's slot +0x0C.
Thus a transition or newly selected action can receive its update in that
same list pass.

The major-8 update splits on exchange state `+0xB00`, paired state
`+0xB10`, category `action[+0x10]`, and behavior flags `action[+0x14]`.
The ordinary branch passes `action[+0x50] + phase * 0x4C + 8` to shared
row-motion consumer `FUN_0021ACB0`; category `2`, category `0xF00`,
category `0xC0000`, and behavior mask `0x2` select separate consumers.

## Authored motion events and phase payload

`FUN_00218FE0` copies the character definition's `+0x38` counted array of
0x4C-byte rows from definition `+0x3C` (fighter `+0xC8`) to fighter `+0xCC`.
It converts each action record's `+0x50` row index into a pointer in that
writable array. Configured jutsu can replace the first twelve rows; those
provider rules remain in Character assets and Action commands.

The first eight bytes control the phase. The next 0x14 bytes are the motion
event passed to `FUN_0021ACB0`; the remaining 0x30 bytes form the payload
published as `+0xA50`. The motion consumer establishes these row fields:

| Absolute row offset | Width | Observed use |
| --- | --- | --- |
| `+0x08` | u16 | Motion flags; zero suppresses this consumer |
| `+0x0A` | s16 | Event time; `0x7FFF` disables the event |
| `+0x0C/+0x10` | float each | Planar and vertical speed arguments |
| `+0x14` | float | Planar decay toward zero when no motion event is taken |
| `+0x18` | float | Copies to fighter `+0x9B4` whenever the motion block is nonzero and this value differs from 1 |
| `+0x1C` | u32 | Attack/phase flags; continuation gate includes `0x20` |

Motion mask `0x1` selects primary timeline `+0x1B8/+0x1C4`; mask `0x2`
selects secondary `+0x1DC/+0x1E8` and takes precedence when both are set.
`FUN_0021A6D0(fighter, motion, 1)` checks the floating crossing-event helper
`FUN_002118A0`. A negative event time derives a threshold from positive
phase duration, or animation frame count minus one, then subtracts phase
start frame and adds the negative offset, clamping at zero. For a secondary
event beyond the last animation update, the helper can make one final check
at the current secondary cursor. These are event thresholds, not unconditional
per-call impulses.

On an admitted motion event, flag group `0xFF00` determines the two speed
arguments before later scaling:

| Flag group | Planar argument | Vertical argument |
| --- | --- | --- |
| `0x0100` | Authored | Authored |
| `0x0200` | Current + authored | Current + authored |
| `0x0400` | Current + authored | Authored |
| `0x0800` | Authored | Current + authored |
| Other | Current | Current |

Flag `0x10` can invert the authored planar component
when direction halfwords `+0x98C/+0x990` differ. Subsequent scaling and
integration belong to [Movement and physics](movement_and_physics.md); this
document establishes how authored action rows reach those consumers.

## Continuation and common exit decisions

`FUN_0023B280` is the complete common major-8 transition body
`0x0023B280..0x0023BAB8`. It requires both the current record and phase
payload. Before its ordinary exit decisions it resolves the opponent's source
record, preferring retained `+0xE54`. If that pointer is absent it checks
source `+0xE58`, then `+0xC74`, through `FUN_002179F0` when the source's
`+0x0C` word is nonzero; if no record is found it uses the dummy record at
`0x00407C00`. Source-kind and lifetime distinctions belong to
[Target selection](target_selection.md).

When that resolved record equals the current record and outcome byte
`+0xA40 == 1`, it scans the whole action array upward for a record whose
signed continuation byte `+0x18` equals current index `+0xA3C` and whose
signature `+0x1C` contains `0x08000000`. After validation, result 3 dispatches
immediately. Otherwise current behavior bit `0x02000000` also dispatches
immediately after synchronizing direction to `+0x326`; without that bit it
stages the index at `+0xA3E`. Input-based continuation selection belongs to
Action commands.

The subsequent branch order is significant:

| First applicable condition | Transition owner |
| --- | --- |
| Current category `0xC0000` | Skip ordinary exits; retain the trailing opponent-lock maintenance |
| Exchange state `+0xB00 & 0xFF` | `FUN_002424E0` |
| Zero exchange state and category `0xF000` | `FUN_00243EF0`, then common exit |
| Paired state `+0xB10 != 0` | `FUN_00247860` |
| Current category mask `0x2` | `FUN_0023C230` |
| Pending candidate `+0xA3E != -1` | Evaluate continuation as below |
| Otherwise | Behavior flags and terminal/grounded conditions |

A pending ordinary continuation is dispatched only when exchange state is
zero and current payload `+0x00 & 0x20` is set. Special category `0x1000`
first delegates to Extra Hit eligibility `FUN_00241A50`; that path belongs
to [Extra Hit](extra_hit.md#eligibility-and-action-exit). A pending `0xF00000` category is additionally checked
against its low signature context and current groundedness. Presence of a
pending index is therefore not proof that it will execute.

For the ordinary behavior branch, action `+0x14` mask `0x2` delegates to
`FUN_0023F170`. With that mask clear and mask `0x1` clear, terminal phase
causes common exit. With mask `0x1` set, airborne execution can exit before
terminal: the branch also checks battle-coordinator state, zero exchange state,
record `+0x38 == 0`, and the bounded ground-distance comparison in
`+0xBA4`. A terminal phase exits via mode 2 when grounded on the first
consecutive grounded update (`+0xB9A == 1`), otherwise mode 0.

Common exit `FUN_0023BDC0` first clears specialized motion bookkeeping
through `FUN_0023EF30`, then enters `(0,0)` when grounded in mode 0,
or `(3,0x1E)` when airborne. Mode 2 enters `(4,0x26)` regardless of
groundedness; mode 1 enters that state when grounded and `(3,0x1E)` when
airborne. These state IDs are established transitions; their movement behavior
belongs to Movement and physics.

`FUN_0023F170` covers landing exits selected by behavior mask `0x2`.
Category `0x200` waits
for terminal, clears `+0xA46/+0xA47/+0xA48`, then returns to neutral or
air state. Other records inspect terminal, previous phase's ground conditions,
consecutive grounded count, behavior bit `0x08000000`, current/prior outcome
bytes, and payload masks `0x4/0x8`. They can exit on landing or hold an
authored ground-sensitive phase. This branch does not have a single fixed duration.

Cleanup `FUN_00238D00` is called from the state setter while the old major
8 record is still installed. Raw instructions at `0x00217D04` preserve the
requested next major/substate in argument registers despite the decompiler's
argument-less call. Cleanup clears current/pending indices, the `+0x26C`
countdown block, two attack registrations under `+0xDF4`, and `+0xE50`.
It preserves prior outcome at `+0xA41` only for an attack-to-attack change,
otherwise writes zero. Category-specific cleanup and paired-state teardown
precede those common clears. Damage interruption reaches this cleanup through
the same setter; accepted-hit decisions remain with Hit response.

## Ordinary attack registration

The common late fighter pass `FUN_0024DE40` publishes attack geometry only
for an active, unpaused fighter in major state 8 with a current phase payload,
payload mask `0x2`, and no `+0xB00 & 0xFF00` exchange state. It also requires
the pass-enable bit `+0x61 & 0x10`: when that bit was clear, it sets the bit
and returns. The pass calls `FUN_0021FC70` twice, with successive 0x18-byte
payload banks, the fighter's primary scene at `+0xE70`, animation-end word
`+0xB88`, and secondary timeline `+0x1DC`. Outside the admitted branch it
deactivates both registrations under `+0xDF4` only within the unpaused
processing block. During positive pause this common block neither publishes
nor deactivates those registrations.

The two banks occupy row `+0x1C..+0x4B`. The registration consumer establishes
the following fields; the second bank repeats them at row `+0x34`:

| First-bank row offset | Width | Observed use |
| --- | --- | --- |
| `+0x1C` | u32 | Phase/attack flags checked by the caller |
| `+0x20/+0x22` | s16 each | Inclusive activation start/end thresholds |
| `+0x24` | float | Radius copied to the corresponding fighter geometry bank |
| `+0x28` | pointer | Skeleton-node name; an empty name uses the fighter transform |
| `+0x2C/+0x30` | float each | Local position offsets |

`FUN_0021FC70` deactivates the selected bank when the phase, scene, timer,
or payload is missing, either bound is `-0x7FFF`, or a requested skeleton
node cannot be found. Negative bounds are derived from the phase's positive
duration, otherwise animation frame count minus one, less the phase start
frame, plus the signed offset; the result is clamped at zero. For ordinary
playback it uses the inclusive crossed-interval helper `FUN_00211BA0`.
An animation loop flag selects wrap-aware `FUN_00211C80` instead.
The interval includes positions crossed between updates; it is not simply
an equality test against the current cursor.

Playback rate also affects admission. Above `0x100`, the consumer can lower
a bound by one cursor position when the accumulated fractional step and
integer playback advance meet its `1.9` comparison. In that above-`0x100`
branch, animation end can also lower a still-unreached bound to the current
cursor. With a nonzero rate below `0x100`, it instead tests the scene's
integer animation frame against the
adjusted inclusive bounds. These distinct branches must be preserved when
interpreting an authored activation window.

On admission, it resolves the named node or fighter transform, applies the
authored offsets, updates the corresponding geometry under `+0xC98`, and
activates the selected registration through `FUN_001DCCC0`. It also calls
`FUN_00222A30`, which stores the current action-record pointer at `+0xE50`.
Failure calls `FUN_00220210` to deactivate that bank. Thus a nonterminal
phase or attack-bearing row alone does not establish an active attack.
Collision evaluation and accepted-hit responses belong to
[Collision](collision.md) and [Hit response](hit_response.md).

### Character-specific scene and timer selection

The recovered resident xrefs to `FUN_0021FC70` contain twelve direct call
sites in eleven functions. All eleven caller bodies were inspected. Besides
the common `FUN_0024DE40`, ten character-specific callers use another scene
or timer. They normally first call `FUN_0021FC40`, which reads the selected
registration's first word and skips publication when it is already nonzero.

| Caller | Scene/timeline supplied to the shared attack consumer |
| --- | --- |
| `FUN_002662A0` | Scene `+0x5114`, auxiliary animation-end word `+0x507C`, timer `+0x5084` |
| `FUN_0029D010` | Scene array `+0x57A0 + index * 0x120`; primary end result and timer `+0x1DC`; one branch temporarily substitutes scene rate `0x100` around the call |
| `FUN_0029F3F0` | Selected auxiliary 0x80-byte block; its scene at block `+0x78`, end word at `+0`, timer at `+8`; counted timers at fighter `+0x5528 + index * 0x80` |
| `FUN_002A9AA0` | Selected auxiliary 0x80-byte block with the same scene/end/timer offsets; counted timers at `+0x5BF8 + index * 0x80` |
| `FUN_002AF360` | Scene `+0x4EF4` or `+0x5114`, auxiliary end `+0x4E60`, timer `+0x4E68`; timer advance always reads scene `+0x4EF4` |
| `FUN_002D0050` | Scene selected from character-owned fields; primary end result and timer `+0x1DC` |
| `FUN_002DDB40` | Scene `+0x61D8`; two direct sites select bank 0 or 1, using primary end result and timer `+0x1DC` |
| `FUN_002E2E00` | Scene `+0x5084`; primary end result and timer `+0x1DC` |
| `FUN_002EC260` | Scene `+0x5494` for callback action ID `0x1E`; primary end result and timer `+0x1DC` |
| `FUN_002F3E70` | Scene selected from `+0x5880 + index * 0x20`; primary end result and timer `+0x1DC` |

The four auxiliary-timer callers above advance those timers with their
auxiliary playback scene's **unsigned** `u16(+0x94) / 256.0` when
`FUN_00224650` reports no positive pause. In `FUN_002AF360` that playback
scene remains `+0x4EF4` even when attack publication uses `+0x5114`.
During pause they call `FUN_00211F70`, which suppresses its
event flag rather than resetting positions or remainder. Shared arithmetic
belongs to [Timer primitives](../runtime/timer_primitives.md); puppet scene
ownership belongs to [Puppet control](puppet_control.md). This recovered
direct-call census does not establish complete indirect-call coverage or
all alternate attack-registration mechanisms.

There is also a direct auxiliary-bank path. `FUN_00220380` updates center
`+0xD50 + bank * 0x50`, scales its supplied radius by fighter `+0x2F0`
into `+0xD48 + bank * 0x50`, assigns a side-dependent registration mask,
and activates a bank under `+0xE18` when its `FUN_00307560` gate admits it.
The common maintenance pass `FUN_0024C440` deactivates both of these
auxiliary banks. Temari callback `FUN_002A56D0` contains a concrete caller
that builds a position from phase-payload offsets and supplies its radius
to this helper. The shared `+0xDF4` row-window consumer therefore does not
account for every fighter-owned activation path. Registration masks and
collision behavior remain with Collision.

## Input interruption of an executing action

The common input pass `FUN_00248EC0` evaluates current-state predicates in
sequence: guard handler, transformation eligibility, `FUN_0022B630` and
its admitted transition `FUN_0022BA30`, new action selection, then native
movement requests. It operates on a local logical-input mask, so an admitted
earlier branch can affect the later request. Input matching and input-mask
meaning remain in Action commands; this section records the major-8 exit
conditions established by the execution consumers.

For current major 8, `FUN_0022B630` rejects missing records, category
`0xC0000`, category `0xF00000` with outcome 1, category `0x100` with a
pending continuation, category `0x200`, and phase payload bit `0x20`.
With fighter motion classification `+0x9BA == 0` (the X-dash substate;
see [X-dash](xdash.md#state-transitions)), it requires
`FUN_00239250` to return a value in inclusive `[0.5,0.95]`. That helper
depends on the current attack payload, phase, animation, cursor, and playback
rate; the interval cannot be interpreted as an unconditional fraction of
every action's total duration. With nonzero motion classification, only
`+0x9BA == 3`, `+0x9BC == 2`, and positive vertical speed are admitted.
Outer gates also require matching tier halfwords `+0x9F6/+0x324`, zero
`+0x9F0`, zero exchange state, and `FUN_0022D5B0` returning zero. The
request requires logical bit `0x40000`.

On admission, `FUN_0022BA30` exits the action through `FUN_0023BDC0`,
clears any remaining pending index, and forces major 0 substate `0x0C`
when grounded or `0x0D` when airborne. It also assigns signed
`cursor >> 2` to a nonzero opponent timer at `+0x254` and mirrors the
result through that block's assignment fields. The later
new-action selector still runs in that input pass.

A separate request uses `FUN_002302C0`. For major 8 it requires zero
exchange and paired states, groundedness, capability mask `+0xBB4 & 0x10000`,
and the relevant logical request. It rejects category `0xC0000` through
`FUN_002440C0` and category `0x200` through `FUN_0023E250` results 3/4.
The caller clears the opponent's retained record `+0xE54` and enters
`(3,0x1F)` through the common setter. Conversely, `FUN_0022F200` rejects
major 8 outright, while `FUN_0022E760` accepts only specified native majors
0/1/2/4. Native movement requests therefore have different interruption
permissions; there is no common all-action cancel switch.

## Character execution callbacks

Dispatcher `FUN_00217670`, its channel-to-slot mapping, configured-provider
table selection and the complete callback-table census are owned by
[Character assets](../game/character_assets.md#per-character-code).
Configured-provider execution therefore needs the provider's callback table
as well as its copied rows.

Callbacks commonly identify the action through `FUN_00217860`. For ordinary
indices this returns `+0xA3C` only in major 8; for configured slots 0..3 it
maps the selected provider back to that provider's local action ID. An action
ID in a callback is consequently not always the fighter's selected array
index. `FUN_00217930(fighter, negative)` similarly returns the current
record only in major 8.

Character callbacks can author events in code, change playback rate and
writable rows, produce continuation permission, and hold or redirect phases
independently of the shipped rows. Those algorithms are owned by
[Character action callbacks](character_action_callbacks.md); a phase row
alone therefore does not fix every event, speed, continuation window, or
phase lifetime. Auxiliary-object behavior belongs to
[Projectiles](projectiles.md), [Puppet control](puppet_control.md), and
their other specific owners.

## Complete authored-array census

All 94 resident definition-table entries at `0x005A2900` were read. The
nonzero definition pointers identify 78 distinct definitions: 74 full
fighter definitions and four jutsu-only providers for IDs 26,29,30,31.
The definition inventory and shared/filler identities remain in Character
assets and [Character identity](character_ids.md). Every counted 0x54-byte
action array and every counted 0x4C-byte row array from those 78
definitions, including the providers, was read.

| Census item | Count / observed bounds |
| --- | --- |
| Action records | 3,444: 3,428 full-definition records and 16 provider records |
| Phase rows | 13,670: 13,622 full-definition rows and 48 provider rows |
| Terminal rows (`animation == -1`) | 3,671 |
| Nonterminal rows | 9,999 |
| Nonterminal condition zero | 1,140 |
| Nonterminal positive condition | 1,207; thresholds 1..48, with gaps |
| Animation-end condition `-16` | 6,286 |
| Grounded condition `-17` | 1,321 |
| Descending/grounded condition `-18` | 3 |
| End-or-grounded condition `-19` | 17 |
| End-and-grounded condition `-20` | 19 |
| Other negative conditions | 6 relative phase jumps, listed below |
| Authored nonterminal rates | Unsigned values 0..1,024; 8,424 rows use `0x100` |
| Nonzero nonterminal motion blocks | 8,943; every authored low nibble is `0x2`, selecting the secondary timeline |
| Zero nonterminal motion blocks | 1,056 |

Every action's original `+0x50` row index is within its definition's counted
row array. Every forward sequence from such an index reaches a terminal
row before the array ends. Counts of nonterminal rows in those **linear
sequences** are `1:239, 2:1455, 3:528, 4:933, 5:207, 6:79, 7:1, 8:1,
10:1`. This is a static bound check, not proof that actual control flow is
linear: condition-zero phases, relative jumps, callbacks, and interruption
can change the path.

| Definition ID | Action index / phase | Definition row index / resident address | Relative condition | Rate |
| --- | --- | --- | ---: | ---: |
| 51 | `0x2C / 3` | 173 / `0x004BB39C` | -3 | 256 |
| 53 | `0x23 / 2` | 141 / `0x004C4ADC` | -1 | 512 |
| 62 | `0x1C / 7` | 136 / `0x004F4C30` | -5 | 256 |
| 66 | `0x23 / 2` | 151 / `0x0050B7C4` | -2 | 256 |
| 69 | `0x1C / 2` | 131 / `0x0051D1C4` | -1 | 320 |
| 77 | `0x1B / 3` | 131 / `0x00543B84` | -3 | 256 |

Rate zero occurs in ID 58 row 19 (`0x004DC064`), whose progression
condition is grounded (`-17`). Rate 1 occurs in ID 93 row 93
(`0x005986DC`), whose condition is zero. These records demonstrate why
zero/slow animation rate alone does not imply a malformed action: progression
and character/native handlers are separate mechanisms. Their complete
action-specific lifetime remains outside the confirmed examples above.

## Prior outcome byte lifetime

Fighter byte `+0xA41` holds a prior action outcome beside current outcome
`+0xA40`. Resident initialization zeros it at `0x00214FE0`.

**Observed writers and clears:** attack entry calls `FUN_00238A70`, which
invokes `FUN_002391B0` to clear current outcome `+0xA40` and bytes
`+0xA42..+0xA44`, leaving `+0xA41` intact. Attack exit `FUN_00238D00`
overwrites `+0xA41` with current `+0xA40` when the requested next major is 8,
otherwise with zero (`0x00239178/0x00239184`). The common state setter
`FUN_00217E40` does not clear the byte; its exit dispatcher `FUN_00217BD0` has
no major-3 exit callback, and neutral entry `FUN_00226F10` adjusts facing and
exchange state without clearing it. These inspected transitions supply no
general fall or landing reset.

The section-transfer alternative branch writes `+0xA41 = 1` at `0x0022EE90`,
after the state setter has exited the transfer and installed fall
`(3,0x1E)`, so transfer cleanup runs before that write; see
[Section transfers](section_transfers.md#motion-stages-and-relocation).
Because attack entry leaves the byte intact, that value can reach an ensuing
attack without becoming its current-hit outcome. `FUN_00228550`,
`FUN_00235200` and `FUN_0023D980` also write 1 under their own action gates.

Seven character-specific stores at `0x0028774C`, `0x002AE5E4`,
`0x002BAB20`, `0x002BE5B4`, `0x002C5EFC`, `0x002C6304` and `0x002DA348`
copy current `+0xA40` to `+0xA41`, then zero `+0xA40`, at a
secondary-timeline zero event with a nonzero owned loop counter. This can
replace the prior value inside an attack, before attack exit. The counter is
float `+0xA60` at the first six stores and `+0xA88` in `FUN_002D9AA0`; their
action/phase loops belong to
[Character action callbacks](character_action_callbacks.md). The byte is
therefore shared action history; a value of 1 does not identify its producer.

**Observed readers:** with a current attack record and phase payload,
`FUN_0023EF50` lets prior value 1 satisfy one alternative of its
record-`+0x19` admission gate before clearing groundedness; it still requires
the record/phase masks and phase predicate. `FUN_0023F170` distinguishes
prior/current value 1 in its nonterminal grounded exit path. `FUN_0023F5D0`
uses prior value 1, negative value -2 and nonzero prior values in its
phase-motion eligibility decision, alongside facing, distance, action-record
and phase gates. These readers influence subsequent attack motion and landing
decisions; they do not admit an attack by themselves.

**Bounded store coverage:** the resident immediate byte stores with
displacement `0x0A41` are exactly the 14 physical sites above: initialization,
the two attack-exit stores, the transfer write, the three action writers and
the seven character stores. No resident immediate `addiu` with displacement
`0x0A41`, and no resident immediate `sh/sw/sq` with displacement `0x0A40`,
was found. Wider stores, other starting offsets, computed or rebased pointers
and indirect readers remain unresolved.

BTL stores with the same displacement cannot all be assigned to fighters. For
example, live `0x0077F2F0` initializes a class-5 auxiliary object and zeros
its own `+0xA41` while setting `+0xA40` to 1; its separately initialized
registry heads and layout identify a different owner, documented in
[Collision](collision.md#auxiliary-objects). This is not evidence that a
fighter outcome is copied into that object.
