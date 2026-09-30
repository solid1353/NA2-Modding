# Battle hit-response state

This document records the native battle state entered after a hit has already
been accepted. It covers ordinary hit reactions, table-driven displacement,
launch/ground-contact branches, downed recovery, and guarded-hit reactions.
Collision-candidate generation, damage arithmetic, generic effect/status
processing, resource accounting, match outcomes, and non-battle modes are
outside its scope.

The names below describe demonstrated control-flow behavior. They are not
claims about the game's original internal terminology.

## Research coverage

- **Assigned scope:** battle hit-response state after an incoming hit has
already passed acceptance: ordinary reaction selection and timing, planar and
vertical response motion, launch/contact transitions, timed downed recovery and
get-up choices, conditional rehit protection, the Extra Hit air-chase
exchange, how attack-record fields select all of these, and guarded-reaction
entry and exit. The investigation was static and bounded rather than globally
exhaustive.

- **Exploration depth:** coverage used the exact clean resident `SLPS_258.37`
and `PRG/BTL.BIN` artifacts identified below through read-only GhidrAssist
decompilation and disassembly, earlier maintained exports, and exact clean
bytes. The resident trace
followed the representative native chain through
`FUN_002209A0`, `FUN_00231C60`, `FUN_00232B80`, `FUN_00233870`,
`FUN_002346B0`, `FUN_00234DA0`, `FUN_00235510`, `FUN_00235690`, the general
timeline/countdown drivers, guard routines `FUN_00228320`, `FUN_00228760`, and
`FUN_00228E90`, and accepted-hit classifiers `FUN_002406B0` and
`FUN_002409E0`. The per-update order was traced from `FUN_001F03E0` through
the fighter coordinator, `FUN_0024FD80`, `FUN_0024C440`, `FUN_00248580`,
`FUN_00249640`, `FUN_0024DA50`, and `FUN_0024DE40`, with the attacker-side
pause in `FUN_00220690`. Animation timing was traced through the phase
animation selector (live `0x0071F640`), `FUN_00218060`, `FUN_001B99B0`,
`FUN_001BB5C0`, `FUN_0024D1C0`, `FUN_001BB210`, and the CCS animation-chunk
loader `FUN_001B1470`. Knockback and gravity were traced through
`FUN_00232A50`, `FUN_0021ACB0`, `FUN_0024A660`, and `FUN_002183D0`.
The Extra Hit chain was traced through `FUN_00241A50`, its three kind tests,
`FUN_00241F10`, `FUN_00242360`, `FUN_002426C0`, `FUN_0023A0D0`,
`FUN_00239250`, `FUN_00243EF0`, and the record selection path
`FUN_0023A390`, `FUN_00239530`, `FUN_00239B00`, and `FUN_00240C40`, with
`FUN_0021ED70` read only as far as its calls into that chain. Their directly
required helpers and callers were traced far enough to establish field
ownership, ordering, branch thresholds, and exit consumers; unrelated callers
were not exhaustively classified.

The decoded authored-data coverage is exhaustive for these exact clean ranges:

- all 54 `0x18`-byte ordinary motion/timing rows for substates `0x27..0x5C` at
  resident runtime `0x00407670` (ELF file `0x00307770`);
- all 60 native descriptor slots, identifiers, and reachable phase records for
  substates `0x27..0x62` from the overlay descriptor table at live
  `0x0089AEB0` (preserved export `0x0089AE70`, file `0x001E6FB0`);
- all ten `0x1C`-byte guarded-response rows at resident runtime `0x00407550`
  (ELF file `0x00307650`);
- the hit-response fields (`+0x10`, `+0x14`, `+0x2C`, `+0x2D`, `+0x2E`,
  `+0x30`, `+0x32`) of all 3,428 records in the 74 primary action tables
  listed in `@resources/character_data.tsv`; and
- the animation names and animation-chunk frame counts of every slot used by
  substates `0x27..0x62` for those 74 records, from `CMN/2CMNBOD1.CCS` and the
  characters' `PL/2???BOD1.CCS` files (two characters excepted).

- **Confirmed coverage:** the ordinary/guarded accepted-hit split and exact
source-mode-specific rejection, interception, and paired-fighter side effects;
exact native selector mappings and bounded overrides, plus the authored
distribution of every selector and timing field; descriptor phase
conditions and non-default rates; native animation names and the
animation-gated length of every phase; table-driven response impulses and
damping, the attack knockback scale, and hit-response gravity; the exact
per-update order of hit routing, event `0`, receiver and attacker pauses,
lock, animation, and timeline advance, giving elapsed counts in 30 Hz fighter
updates; contact, held, and downed handoffs; exact timed/input recovery
thresholds and exits in updates; guard table initialization and transition gates; the direct
conditional-rehit predicate, its attack-record exceptions and their authored
frequency; the `+0x230` accepted-hit rejection countdown; the ordinary hit
count; and the Extra Hit eligibility, role state machine, counter window,
exchange limit, and authored record layout. Negative-result tracing was sampled
and bounded to the named target/interaction predicates near the end of this
document; it was sufficient to reject several tempting invulnerability
interpretations, not to prove all target-selection behavior.

- **Unresolved or untested:** exact ground-contact timing of `G`, `O`, and
  `B` phases, which depends on stage collision geometry; the animations of the
  two characters stored outside their `2???bod1` files; visual confirmation of animation roles and player-facing
  move names; non-default input bindings; character-specific response
  callbacks and the five overlay callers of the downed handoff; writers of
  Extra Hit attacker bits `8`/`0x20` and of `+0x1B4`; the reset of hit count
  `+0x538`; the exact roles of the other `+0x230` consumers; and the
  distinction among hurtbox, collision, and higher-level target selection.
- **Deliberate exclusions and overlap:** collision-candidate generation, damage and damage
scaling, generic status/effect processing, chakra or guard-resource accounting,
match outcomes, practice-mode mechanics, all other non-battle modes, and
character-specific behavior beyond callbacks reached by the representative
native chain. Those boundaries avoid overlap with collision, combat-arithmetic,
resource, outcome, and mode-specific research.

- **Evidence limitations:** the investigation was static and bounded rather
  than globally exhaustive. No emulator instrumentation, live-memory capture,
  frame stepping, or runtime hit-attempt matrix was performed. The static
  evidence establishes control-flow and authored values, but not those runtime
  observables. Update counts are derived from the traced update order and the
  documented 30 Hz cadence, not measured; physics-gated phases and
  character callbacks can change them.

## Evidence identity and address conventions

The clean resident and BTL inputs and their address conversions are defined in
[Standard game file identities](../game/files/file_identities.md).

Raw encoded absolute pointers and JAL targets in the overlay are already live
addresses. For example, the direct phase setter is preserved as
`FUN_0071eeb0` at export `0x0071EEB0`, but is live at `0x0071EEF0` and file
offset `0x0006AFF0`. The common phase/event updater is preserved as
`FUN_0071f120` at export `0x0071F120`, but its live entry is `0x0071F160` and
file offset `0x0006B260`. This `+0x40` rule is not applied to any resident
address.

Method: direct inspection of the maintained C and instruction exports, plus
byte decoding of the exact clean binaries for response tables and native action
identifiers, character action tables, and CCS animation chunks. No
live-memory capture was used, so native animation names are recorded without
visual confirmation and player-facing move labels remain unassigned.

## Extra Hit eligibility and action exit

Read-only GhidrAssist inspection of the clean resident ELF established these
paths. All addresses in this section are live resident addresses.

`FUN_0023B280` calls `FUN_00241A50(fighter, candidate_index)` at `0x0023B5DC`
when the candidate attack record's `+0x10` flags contain `0x1000`. Eligibility
checks the two fighters' states, reaction timing, and geometry. It returns
`1` for acceptance, `0` while waiting, and `-1` for rejection.

The branch at `0x0023B5E8` sends result `1` to `0x0023B60C`, whose call block
starts the paired sequence through `FUN_00241F10` at `0x0023B630`. That helper
writes both fighters' `+0xB00` state, clears the opponent's `+0x224`
countdown block on a fresh exchange, and transitions the initiating fighter to
the candidate attack (details below).

Results `0` and `-1` both continue at `0x0023B6DC`. This path examines the
current attack record's `+0x14` completion flags and the action-completion
argument, then uses native exit helpers including `FUN_0023BDC0`. That helper
selects standing, falling, or recovery through `FUN_00217E40`. In contrast,
`0x0023B910` is after this action-exit path; jumping there skips its work.

Native attack entry provides a distinct lifecycle boundary. The major-action
initializer `FUN_00217D30` calls `FUN_00238A70(fighter, attack_index)` at
`0x00217E28` for major action `8`. `FUN_00238A70` installs the attack index at
`+0xA3C` and record pointer at `+0xA4C`, clears pending candidate `+0xA3E` to
`-1`, and resets attack-local state. Eligibility can be checked repeatedly
between such entries.

The separate branch in `FUN_002455B0` at `0x002457C8` sends a zero predicate
to `0x002459B4`; a nonzero result enters the side-effect path at `0x002457D0`
and returns `1` through `0x002459A8`.

These are static control-flow findings. The observed instructions establish
entry, eligibility, and exit ordering; they do not establish visible timing
or exhaustive character-specific behavior.

### Eligibility conditions

`FUN_00241A50(fighter, candidate_index)` returns `-1` unless all of these hold
for the initiating fighter and its opponent at fighter `+0x20`:

- the initiator's `+0xB00` is zero and the opponent's byte `+0x61` bit `3` is
  set;
- the opponent is in ordinary response `0x3C`, `0x3D`, `0x3F`, `0x40`, or
  `0x41`;
- the global object at `gp-0x339C` has no active `+0x08 -> +0x14` value;
- the initiator is not in the `+0x68 == 0x40/0x3B` plus `+0x63` bit `5`
  exclusion also used by the ordinary-response fallback below; and
- the initiator is in major state `8` and its current attack record
  `+0xA4C` is the exact record the opponent retained as its hit provenance
  (`+0xE54`, or the same fallback chain used by `FUN_002346B0`).

It returns `0` (wait) while the opponent's primary cursor `+0x1C4` is below
`7 * opponent[+0x1AC]` or initiator byte `+0xA40` is not `1`. It then reads
candidate record `fighter[+0xA54] + candidate_index * 0x54` and dispatches on
its `+0x14 & 0x1C00` kind:

| Kind | Additional acceptance test, all on the launched opponent |
| ---: | --- |
| `0x0400` | `FUN_00241650`: airborne with byte `+0x63` bit `6` clear; `+0xBA0` is the sentinel `-17320.508` or at least `2.5 * +0xE8 * +0x2F0`; a stage probe along facing `+0x98C` must not report contact and its clearance must be at least `2 * +0xE8 * +0x2F0`. |
| `0x0800` | inline: airborne, byte `+0x64` bit `0` clear, `+0xBA8` sentinel or at least `1.5 * +0xE4 * +0x2F0`, and `FUN_0021C640` reach test returns zero. |
| `0x1000` | `FUN_00241890`: airborne, `+0xBA4` sentinel or at least `2 * +0xE4 * +0x2F0`, and stage-relative height checks against `+0xE4 * +0x2F0`. |

Every kind also re-requires one of the five launch responses above. Any other
kind returns `-1`. The environment fields `+0xBA0`, `+0xBA4`, and `+0xBA8`
are recorded raw; their geometry names are not established.

### Authored Extra Hit records

A read-only scan of all 74 primary action tables in the clean ELF (3,428
records; table ownership as in
[Substitution](substitution.md#attack-record-ownership-and-clean-elf-inventory))
found exactly three records per table with `+0x10 & 0x1000`, always at action
indices `10`, `11`, and `12`, with `+0x14` kinds `0x0400`, `0x0800`, and
`0x1000` respectively. Their authored response selectors (`+0x2C`) are `0x12`
(73 tables; one table uses `0x13`), `0x15`, and `0x14`, so each Extra Hit
attack itself sends the opponent into another launch response (`0x3C/0x3D`
or `0x3E`, `0x40`, or `0x3F`). All have `+0x2E == 1`.

Indices `13..15` (`+0x10 == 0x2000`) and `16..18` (`+0x10 == 0x4000`) repeat
the same three kinds and selectors in every table without the `0x1000` flag.
Their `+0x14` values add one extra bit per kind (`0x80`, `0x200`, `0x100`).
They are the receiver's counter records, selected as described next.

### Selecting Extra Hit and counter records

Normal input action selection `FUN_0023A390` first asks `FUN_0023A0D0` for a
selector while no candidate is pending. Selector `1` is returned when the
fighter's `+0xB00` is zero and its current attack record has one of
`+0x14` bits `0x80`, `0x100`, or `0x200`, no `+0x10 & 0x00F00000` type, and
current phase-record flag `0x10`. Selectors `2` and `3` are the receiver
cases in the next section. The selector is passed to `FUN_00239E50`, which
still requires `+0x254 == 0`; in major `5` only selector `2` passes (selector
`3` is rejected there; other admitted states ignore the selector). It is then
passed to `FUN_00239530`, which hands off to `FUN_00239B00`. That routine
scans only action indices `10..18` for a record whose signature matches the
input, whose chakra cost
`+0x20` does not exceed fighter `+0x70` (unless `FUN_00307480` applies), and
whose type and kind match the masks from `FUN_00240C40`. A match becomes the
pending candidate `+0xA3E`.

`FUN_00240C40` supplies those masks:

| Selector and state | Allowed `+0x10` type | Allowed `+0x14` kind |
| --- | --- | --- |
| `1` (attacker in major `8`) | `0x1000` (indices `10..12`) | from the current attack: `0x80 -> 0x400`, `0x100 -> 0x800`, `0x200 -> 0x1000` |
| `2`/`3`, receiver not attacking | `0x2000` (indices `13..15`) | the kind of the opponent's current Extra Hit record |
| `2`/`3`, receiver already in a counter attack | switches between `0x2000` and `0x4000` unless `FUN_00180210(3)` returns `0` (nominally 1 in 4) | the kind of the receiver's own current record |

In the clean tables, 867 records outside indices `10..18` carry exactly one of
those launch bits, in all 74 tables. The dominant pairings are `0x80` on 434
records with selector `0x12` (`0x3C/0x3D`), `0x100` on 159 with `0x14`
(`0x3F`), and `0x200` on 167 with `0x15` (`0x40`). Thus a `0x3C/0x3D` launch
normally offers record `10` (another `0x3C/0x3D`), a `0x3F` launch offers
record `11` (`0x40`), and a `0x40` launch offers record `12` (`0x3F`).

### Exchange state at fighter `+0xB00`

`FUN_00241F10(initiator, candidate_index)` is the paired-state writer named
above. The branch at `0x00241F40`, `bne v0,zero,0x002421EC`, tests the
initiator's own `+0xB00 & 0xFF`; when it is nonzero, all role changes are
skipped and only the common tail runs. Otherwise the initiator's current role
selects one of four exact updates. `P` is the opponent.

| Initiator `+0xB00` before | Initiator after | Opponent after | Retarget |
| --- | --- | --- | --- |
| high byte clear | sets bit `0x0001` | sets bit `0x0100`; its `+0x224` countdown block is cleared unless activation is pending | no |
| any of `0x0300` | sets bit `0x0004`, clears the high byte | clears the low byte, sets bit `0x0400` | yes |
| any of `0x0C00` | sets bit `0x0010`, clears the high byte | clears the low byte, sets bit `0x1000` | yes |
| any of `0x3000` | sets bit `0x0004`, clears the high byte | clears the low byte, sets bit `0x0400` | yes |

Every update also writes the opponent's window
`+0xB0A = max(1, cvt(12.0 - 1.7142857 * P[+0xB08]))`, where `+0xB08` is the
exchange count. The conversion is EE `cvt.w.s` under the active rounding
mode, so only the exact endpoints `12` (count `0`) and the floor `1` (count
`7` or more) are stated here. The retarget rows then make the initiator
retain the opponent (`+0xE58` and `+0xC74`), clear `+0xE54`, and adopt the
opponent's attack record (`+0xE50`, or `+0xA4C` when that record's
`+0x10 & 0x000C0000` is clear) as its own retained hit provenance with its
`+0x2E` repeat count and `+0x28` transient modifier.

The common tail calls `FUN_002260D0(...,0)` for each fighter whose float
`+0x7C` is nonzero, enters the candidate attack through `FUN_0023A9A0`, and on
a retarget row calls `FUN_00242360`. That helper selects the response the
initiator would receive from its retained record and, when the current attack
record lacks `+0x10 & 0x1000`, copies that response's second-phase animation
slot and its complete response-table motion row into the attack's `+0x50`
sub-record. Finally both `+0xB0C` values are cleared and both `+0xB08`
counts increment.

Thus the low byte of `+0xB00` is the attacking role (`1`, `4`, `0x10`) and the
high byte is the receiving role (`0x100`, `0x400`, `0x1000`). The next
section shows the receiver writing `0x200`, `0x800`, or `0x2000` and the
attacker `2` when a counter window is missed. Teardown also clears attacker
bits `8` and `0x20`, but no writer of those two bits was traced.

### Receiver response and exchange limit

The pair hit resolver `FUN_0021ED70` calls `FUN_002426C0(fighter)` for each
fighter whose `+0xE3C` hit bit `0x1` is set, and clears that hit (and the
opponent's matching `0x100` bit) when the helper returns nonzero:

- Receiving role `0x100` with a pending candidate `+0xA3E != -1`: the
  receiver stages its own `+0x230` countdown to `60` (pending), then calls
  `FUN_00241F10(receiver, candidate)`, becoming the attacker. The incoming
  hit is discarded.
- Receiving role `0x100` without a candidate: the receiver moves to `0x200`,
  the attacker from `1` to `2`, the receiver's `+0x224` block is cleared unless
  pending, and the hit proceeds.
- Receiving roles `0x400` and `0x1000` behave the same way, except that the
  receiver also clears the attacker's `+0x224` block, and a receiver whose
  `+0xB08` exceeds `14` has its candidate forcibly cancelled. Missed windows
  move to `0x800` and `0x2000`.
- A fighter holding attacking role `4` or `0x10` returns `1`, so hits against
  it are discarded while that role is active.

`FUN_0023A0D0` is the candidate query for a receiver. For the three receiving
roles and no current candidate, it calls
`FUN_00239250(attacker, receiver[+0xB0A])`. That routine accepts only while the
attacker's secondary cursor `+0x1E8` lies within the last `+0xB0A` animation
frames of the attacker's current attack phase (scaled by the phase rate and
the attacker's `+0x1AC`), returning a `0..1` timing score stored at `+0xB0C`.
Role `0x100` returns `2` and also clears its own action-lock block; `0x400`
returns `3`; `0x1000` returns `2`. The Practice Extra Hit Counter options that
consume these high-byte roles are documented in
[Practice mode](practice_mode.md#linked-attack-and-extra-hit).

`FUN_00243EF0` tears the exchange down: it clears the resolved role pairs (or
both words when the fighter holds no attacking role), resets both `+0xB08`
counts and presentation fields, and restores both `+0x1B0` rates to `1.0` when
the fighter's `+0xB00` has become zero.

**Inference:** because Extra Hit requires the opponent to be in a launch
response caused by the initiator's current attack and each authored Extra Hit
record selects another launch response, this exchange is the native
air-chase/juggle continuation. The counter window shrinks with every
exchange and further counters are refused after the fifteenth. Visual labels
and the player-facing meaning of the timing score were not observed.

## Fighter fields used by the response machine

These fields are statically confirmed by reads and writes in the routines
described below:

| Fighter offset | Type | Demonstrated use |
| ---: | --- | --- |
| `+0x18E` | `s16` | Major action state. Ordinary accepted hits enter `5`; timed downed recovery uses `6`; guard stance/reactions use major `0`. |
| `+0x190` | `s16` | Action substate. Ordinary response substates occupy `0x27..0x5C`; downed recovery uses `0x5D..0x62`; guard uses `5..7`. |
| `+0x192` | `s16` | Phase within the current action. The overlay phase setter writes it directly. |
| `+0x1AC` | `f32` | Current fighter update-rate scalar used to advance the action timelines and decrement the action-lock block. |
| `+0x1B0` | `f32` | Local override source for `+0x1AC`; response `0x4F` temporarily changes it on both paired fighters. |
| `+0x1C4` | `s32` | Primary action-timeline cursor tested by reaction completion and downed-recovery thresholds. |
| `+0x1E8` | `s32` | Secondary action-timeline cursor tested by positive phase-record thresholds and guarded-response gates. |
| `+0x20C` | `s32` | Current count in the fighter-update pause block at `+0x200`; positive values stop normal action-timeline and per-action updates. |
| `+0x230` | `s32` | Current count in a secondary countdown block at `+0x224`. While positive, accepted-hit router modes `0`, `2`, and `3` discard new hits; attack record `+0x32`, ordinary-response row `+0x16`, guarded-response row `+0x16`, and several fixed values initialize it. See [Accepted-hit rejection countdown](#accepted-hit-rejection-countdown). |
| `+0x538`, `+0x53A` | `s16`, `s16` | Receiver's accepted ordinary-hit count (saturating at `9999`) and its running maximum; see [Hit count](#hit-count). |
| `+0xB00` | flags | Extra Hit exchange roles; see [Exchange state](#exchange-state-at-fighter-0xb00). |
| `+0xB08`, `+0xB0A`, `+0xB0C` | `s16`, `s16`, `f32` | Extra Hit exchange count, counter window, and counter timing score. |
| `+0x254` | `s32` | Current count in the action-lock block at `+0x248`; native action selection refuses actions until it reaches zero. |
| `+0x338` | `u32` | Current logical input bits; guard is `0x10000000`, while downed choices test newly pressed binding 2 (`0x00010000`, default Cross) and binding 1 (`0x00001000`, default Circle). |
| `+0x994` | `f32` | Oriented planar response speed written by the reaction table. |
| `+0x998` | `f32` | Vertical response speed written by the reaction table. |
| `+0x9B4` | `f32` | Gravity argument for the next movement pass, copied from response-table field `+0x10` when that field differs from `1.0` and reset to `1.0` after each pass; see [Gravity and airtime](#gravity-and-airtime). |
| `+0x9B8` | flags | Low two bits participate in choosing the grounded-family reaction variant. |
| `+0xA30` | pointer | Current action-descriptor row; for native substates below `0x66`, the state setter indexes the overlay descriptor table directly. |
| `+0xB88` | `u32` | Latest animation-advance completion result. Animation selection clears it; the animation driver rewrites it with the nonzero end result consumed by phase records. |
| `+0xB84` | pointer | Animation-object table indexed by phase-record animation slot. |
| `+0xB90` | `u16` | Current secondary-timeline and animation rate loaded from the phase record's fourth halfword and interpreted as a `/256` fixed-point factor. |
| `+0xB94` | `s16` | Animation start frame loaded from the phase record's third halfword. |
| `+0xB9A` | `s16` | Consecutive grounded-update count, saturating at `0x7FFF`; reset to zero while airborne. |
| `+0xB9C` | flags | Ground/air history for the current action: low nibble `1` means entered grounded and `2` means entered airborne; `0x20` latches a later airborne update for the former, while `0x10` latches a later grounded update for the latter. |
| `+0x95A` | `s16` | Guard temporal state/counter; `< 1` selects ordinary response and `>= 1` selects guarded response. |
| `+0x95C` | `s16` | Guard-input timing state. |
| `+0x95E` | `s16` | Direction/facing-adjusted guarded-response index. |
| `+0x960`, `+0x962` | `s16`, `s16` | Private stage and per-stage invocation counter used by ordinary response `0x4F`. |
| `+0xB66` | `s16` | Automatic downed-recovery threshold. |
| `+0xB68` | `s16` | Earliest input-driven downed-recovery threshold. |
| `+0xB6E` | `s16` | Raw repeat/response count used by the rehit exception and by the scaled `0x3A/0x3B` downed handoff. No player-facing name is assigned. |
| `+0xB60`, `+0xB64` | pointer, `s16` | Retained attack record and consecutive ordinary-response streak count used by two final selector overrides; both are reset on leaving major state `5`. |
| `+0xE54` | pointer | Attack-record pointer retained for the active response. |
| `+0xE58` | pointer | Source object retained for the active response. |
| `+0xE5C` | `s16` | Attack-record repeat/sample countdown copied from attack record `+0x2E`. |

The high bit of fighter byte `+0x63` is used consistently as the grounded
branch in the traced paths: guard stance is entered only when it is set, and
guard release goes to neutral only when it is set. References below therefore
say *grounded* for that tested condition.

## Resident routine map

| Preserved symbol | EE runtime | ELF file | Demonstrated role |
| --- | ---: | ---: | --- |
| `FUN_00217e40` | `0x00217E40` | `0x00117F40` | Central action-state setter; stores major/substate, resets action cursors, and selects the state descriptor. |
| `FUN_00218190` | `0x00218190` | `0x00118290` | Selects a descriptor-specified animation slot and clears `+0xB88` when that selection changes. |
| `FUN_00211d80` | `0x00211D80` | `0x00111E80` | Advances a generic integer/fractional timeline block by a floating-point rate. |
| `FUN_00211e70` | `0x00211E70` | `0x00111F70` | Decrements a generic integer/fractional countdown block and clamps its current count at zero. |
| `FUN_0021acb0` | `0x0021ACB0` | `0x0011ADB0` | Shared response-table motion/event-gate engine. |
| `FUN_002209a0` | `0x002209A0` | `0x00120AA0` | Accepted-hit router that selects ordinary or guarded response from `+0x95A`. |
| `FUN_00224510` | `0x00224510` | `0x00124610` | Initializes the fighter-update pause channel from attack record `+0x30`. |
| `FUN_00228320` | `0x00228320` | `0x00128420` | Updates guard-input age/temporal state and enters guard stance when eligible. |
| `FUN_00228760` | `0x00228760` | `0x00128860` | Guarded-hit state selection and guarded-response initialization. |
| `FUN_00228e90` | `0x00228E90` | `0x00128F90` | Guard stance/reaction continuation and exit selection. |
| `FUN_00231a40` | `0x00231A40` | `0x00131B40` | Runs the paired update-rate sequence required by the normal `0x4F` exit. |
| `FUN_00231c60` | `0x00231C60` | `0x00131D60` | Converts attack record `+0x2C` plus fighter context into an ordinary response substate. |
| `FUN_00232b80` | `0x00232B80` | `0x00132C80` | Enters ordinary major state `5`, retains hit provenance, and initializes response side effects. |
| `FUN_00233870` | `0x00233870` | `0x00133970` | Ordinary-response transition dispatcher, including completion, contact, and downed handoffs. |
| `FUN_002346b0` | `0x002346B0` | `0x001347B0` | Applies response-table timing/lock values and related per-response side effects. |
| `FUN_00234da0` | `0x00234DA0` | `0x00134EA0` | Per-update ordinary-response driver; advances table motion and event impulses. |
| `FUN_00235510` | `0x00235510` | `0x00135610` | Initializes timed downed recovery and enters `(6,0x5D)`. |
| `FUN_00235690` | `0x00235690` | `0x00135790` | Updates downed/recovery substates `0x5D..0x62`. |
| `FUN_00239e50` | `0x00239E50` | `0x00139F50` | Action-entry eligibility predicate; returns false while `+0x254` is nonzero. |
| `FUN_002406b0` | `0x002406B0` | `0x001407B0` | Classifies current response windows for conditional rehit suppression. |
| `FUN_002409e0` | `0x002409E0` | `0x00140AE0` | Combines incoming-attack, current-response, and repeat-record conditions into the router's response-gate bits. |
| `FUN_00249640` | `0x00249640` | `0x00149740` | Per-action update dispatcher; sends major `5` to `FUN_00234da0` and major `6` to the recovery updater. |
| `FUN_0024c440` | `0x0024C440` | `0x0014C540` | Main fighter countdown maintenance, including the ordered `+0x20C` then `+0x254` updates. |
| `FUN_0024d1c0` | `0x0024D1C0` | `0x0014D2C0` | Advances the current animation and stores its end result at `+0xB88`. |
| `FUN_0024d5e0` | `0x0024D5E0` | `0x0014D6E0` | Advances the primary and secondary action timelines while fighter-update pause is inactive. |
| `FUN_0024fd80` | `0x0024FD80` | `0x0014FE80` | Active-fighter loop that suppresses normal action updates while `+0x20C` is positive. |
| `FUN_00248ec0` | `0x00248EC0` | `0x00148FC0` | Normal battle-input update that passes logical input `+0x338` to `FUN_00228320`. |
| `FUN_001f03e0` | `0x001F03E0` | `0x000F04E0` | Battle update that calls the registry slots `+0x0C`, `+0x10`, and `+0x14` in that order. |
| `FUN_0024de40` | `0x0024DE40` | `0x0014DF40` | Fighter virtual slot `+0x18`; advances action timelines through `FUN_0024D5E0`. |
| `FUN_0021ed70` | `0x0021ED70` | `0x0011EE70` | Pair hit resolver; edits both fighters' `+0xE3C` hit bits and calls `FUN_002426C0`. |
| `FUN_00224870` | `0x00224870` | `0x00124970` | Initializes countdown `+0x230` from attack record `+0x32`. |
| `FUN_00241a50` | `0x00241A50` | `0x00141B50` | Extra Hit eligibility. |
| `FUN_00241f10` | `0x00241F10` | `0x00142010` | Extra Hit exchange-role writer and attack entry. |
| `FUN_002426c0` | `0x002426C0` | `0x001427C0` | Extra Hit receiver counter or missed-window handling. |
| `FUN_0023a0d0` | `0x0023A0D0` | `0x0013A1D0` | Extra Hit counter-candidate query. |
| `FUN_00239250` | `0x00239250` | `0x00139350` | Timing-window score against the opponent's current attack phase. |
| `FUN_00243ef0` | `0x00243EF0` | `0x00143FF0` | Extra Hit exchange teardown. |
| `FUN_0023a390` | `0x0023A390` | `0x0013A490` | Input action selection; asks `FUN_0023A0D0` for an Extra Hit selector first. |
| `FUN_00239b00` | `0x00239B00` | `0x00139C00` | Scans action indices `10..18` for the pending Extra Hit or counter candidate. |
| `FUN_00240c40` | `0x00240C40` | `0x00140D40` | Supplies the type and kind masks for that scan. |
| `FUN_00220690` | `0x00220690` | `0x00120790` | Attacker-side handling of a landed hit, including the attacker pause. |
| `FUN_00232a50` | `0x00232A50` | `0x00132B50` | Retains a new attack record, repeat count, and knockback scale, then re-enters the router. |
| `FUN_00248580` | `0x00248580` | `0x00148680` | Runs the phase updater and the per-major exit dispatchers. |
| `FUN_0024da50` | `0x0024DA50` | `0x0014DB50` | Fighter virtual slot `+0x10`; movement and animation pass, or input selection during a pause. |
| `FUN_0024a660` | `0x0024A660` | `0x0014A760` | Movement, ground contact, and gravity application. |
| `FUN_002183d0` | `0x002183D0` | `0x001184D0` | Applies gravity to a vertical speed. |

## Accepted-hit routing

`FUN_002209a0` is downstream of collision acceptance. Its representative
native branch is exact:

```text
fighter[+0x95A] < 1   -> FUN_00232b80(...)  ordinary response
fighter[+0x95A] >= 1  -> FUN_00228760(...)  guarded response
```

Before that selection, attack-record `+0x14` flag `0x00800000` can change a
nonzero `+0x95A` to sentinel `-1` under the shown facing condition, and flag
`0x00400000` clears it to zero. Both values route the accepted hit through the
ordinary branch. Static code proves guard invalidation/bypass, but not the
authoring names of those two flags.

The complete resident router occupies `0x002209A0..0x0022111F`. Its
decompilation and instructions establish four source-object modes (`0`, `1`,
`2`, and `3`). Their normal paths converge on the
same ordinary-versus-guarded decision, but their admission gates and side
effects are not interchangeable:

| Mode | Exact additional behavior before the response branch |
| ---: | --- |
| `0` | May replace the record returned by `FUN_00222B20` with `FUN_00222A40(fighter[+0x20])` when retained source `+0xE58` is non-null, source `+0x0C` is nonzero, original attack `+0x50` is zero, and the replacement is non-null. It rejects the hit when `FUN_002247A0(fighter)` is nonzero or `FUN_00222BD0(fighter)` is zero. |
| `1` | Requires retained source `+0xE58`, source halfword `+0x02 == 0x474F`, source word `+0x0C == 1`, and a nonzero result from live overlay target `0x0072EDE0(source,fighter)`. It runs the interception predicate described below before invoking a source virtual callback at vtable `+0x58` and live overlay target `0x0072E5D0(1.0,source,fighter,attack)`. |
| `2` | Requires retained source `+0xE58` and `FUN_002247A0(fighter) == 0`, then runs the same interception predicate. On its normal route it writes paired fighter `fighter[+0x20] + 0xB58` to `1` for ordinary response or `-1` for guarded response; its intercepted route writes `-2`. |
| `3` | Requires retained source `+0xE58` and `FUN_002247A0(fighter) == 0`, then performs the common guard invalidation and ordinary/guarded branch without mode `0`'s replacement-record and positive-repeat gates. |

`FUN_002247A0` is exactly the predicate `fighter[+0x230] > 0`.
`FUN_00222BD0` returns positive retained repeat value `+0xE5C` while
`+0xB00 == 0`, otherwise zero, and returns `1` while `+0xB00 != 0`; thus the
mode-`0` admission test is specifically a nonzero expected-repeat requirement,
not a generic validity check. `FUN_00222B20` itself selects retained attack
`+0xE54`, then source-derived records, and finally the resident
`PL_ATK_DUMMY` record, in that order.

Modes `1` and `2` call
`FUN_00229130(fighter,attack,5,selected_response,1)`. A zero result continues
to ordinary or guarded response. A nonzero result diverts into
`FUN_002297D0`: mode `1` supplies code `0x21`, while mode `2` supplies `0x41`.
That diversion stores the code at fighter `+0x964`, clears the complete
action-lock block and conditionally primes the secondary countdown to `-20`,
brings planar and vertical response speeds toward zero, and force-enters
`(major,substate) = (0,8)`. Subject to its internal gates, it also subtracts
`1.0` from fighter float `+0x70`, clamps the result at zero, and writes `15.0`
to `+0x1A0`. These are observed state mutations; the player-facing meaning of
the interception, codes, and two float fields remains unresolved.

The intercepted paths return `0` from `FUN_002209A0` without entering the
ordinary/guarded response. A normally routed accepted hit returns `1` after
the branch. On mode `2`, `FUN_00233540(fighter,1)` consumes the paired
`+0xB58` marker after routing: among the three values written here, only
ordinary marker `1` passes its notification condition; guarded `-1` and
intercepted `-2` do not. This proves a mode-specific paired-fighter side effect
without establishing names for the four source modes.

## Ordinary response selection

`FUN_00232b80` calls `FUN_00231c60`, then forcibly enters
`(major,substate) = (5, selected_response)` through `FUN_00217e40(...,1)`.
The selected response is not simply an animation number. It indexes a resident
state slot whose descriptor table is in the battle overlay at live
`0x0089AEB0`, preserved Ghidra/export `0x0089AE70`, and `BTL.BIN` file offset
`0x001E6FB0`, plus the separate resident motion table described below.

The primary authored selector is attack-record byte `+0x2C`. The following is
the direct mapping before later callback and repeat-hit remaps. A
*grounded-family* choice additionally requires fighter `(+0x9B8 & 3) < 2` and
the grounded bit at `+0x63`.

| Attack `+0x2C` | Grounded-family result | Other result |
| ---: | --- | --- |
| `0x00`, `0x01` | `0x27`, `0x28` | `0x2F` |
| `0x02`, `0x03` | `0x29`, `0x2A` | `0x30` |
| `0x04..0x07` | `0x2B..0x2E`, one-for-one | `0x31` |
| `0x08`, `0x09`, `0x0A` | `0x2F`, `0x30`, `0x31` | same |
| `0x0B..0x0E` | `0x32..0x35`, one-for-one | same |
| `0x0F` | `0x36` | `0x37` |
| `0x10`, `0x11` | `0x38`, `0x39` | same |
| `0x12` | `0x3C` or `0x3D` from orientation | same |
| `0x13..0x16` | `0x3E..0x41`, one-for-one | same |
| `0x17..0x1B` | `0x4A..0x4E`, one-for-one | same |
| `0x1C` | `0x50` | same |
| `0x1D..0x20` | odd `0x51/53/55/57` | paired even `0x52/54/56/58` |
| `0x21` | `0x59` | same |
| `0x22..0x24` | random member of `0x27/28`, `0x29/2A`, or `0x2B/2C` | `0x2F`, `0x30`, or `0x31` |
| `0x25` | random `0x27..0x2A` | random `0x2F..0x30` |
| `0x26` | random `0x29..0x2C` | random `0x30..0x31` |
| `0x27` | random `0x27..0x2C` | random `0x2F..0x31` |
| any other byte | `0x27` | `0x2F` |

A read-only scan of all 74 primary action tables (3,428 `0x54`-byte records)
gives the authored use of this selector. Among the 2,484 records with nonzero
damage `+0x24`:

| `+0x2C` | Direct result | Records |
| --- | --- | ---: |
| `0x00..0x07` | light family `0x27..0x2E` / `0x2F..0x31` | 645 |
| `0x08..0x0A` | `0x2F..0x31` | 61 |
| `0x0B..0x0E` | `0x32..0x35` | 131 |
| `0x0F` | `0x36` / `0x37` | 95 |
| `0x10`, `0x11` | `0x38`, `0x39` | 135 |
| `0x12` | `0x3C` / `0x3D` | 490 |
| `0x13` | `0x3E` | 24 |
| `0x14` | `0x3F` | 390 |
| `0x15` | `0x40` | 433 |
| `0x16` | `0x41` | 22 |
| `0x17..0x19` | held `0x4A..0x4C` | 10 |
| `0x1C` | `0x50` | 2 |
| `0x1D`, `0x1E` | `0x51/0x52`, `0x53/0x54` | 46 |

No damaging record uses `0x1A`, `0x1B`, `0x1F..0x27`, or any other byte, so
the random selectors `0x22..0x27` are unused by stock damaging attacks. The
300 records with `+0x2C == 0xFF` are all non-damaging. The guarded-response
byte `+0x2D` on damaging records is `0..4` on 2,311 and `6..9` on 173; no
record uses `5` or a negative value.

Additional proven selection behavior prevents treating this as a final
one-to-one enum:

- a guard-invalidated call requests response `0x4F` directly;
- a missing attack record starts from `0x27`;
- a failed contextual query selects `0x3A` or `0x3B` according to source
  object presence;
- before the byte mapping, an attack with nonzero `+0x50` returns `0x37` when
  the receiver is in `(5,0x3F)` with `+0x230 < 1` and negative vertical speed,
  a standard source is present, and receiver `+0xBA4` is neither the sentinel
  `-17320.508` nor at least `2 * source[+0xE4] * source[+0x2F0]`;
- a standard source object (raw field `+0x0C == 0`) can dispatch a response
  callback whose result overrides the authored mapping when it returns anything
  other than `-1`; and
- the active-effect path can force response `0x37` for response classes it
  does not accept.

When that source callback is absent or returns `-1`, a repeat-collapse pass is
possible. It requires the standard source object, attack record
`(+0x10 & 0x00F00000) == 0`, and an expected repeat count greater than `1`.
Authored results `0x52/0x54/0x56/0x58` are explicitly exempt. The remaining
exact remaps are:

| Authored result | Repeat-collapse result |
| --- | --- |
| `0x37` | `0x30` |
| `0x3F` | `0x32` |
| `0x40/0x41` | `0x2C` for the grounded-family condition, otherwise `0x35` |
| `0x3C..0x3E` | `0x2B` when grounded-family and the source is grounded; `0x35` when grounded-family and the source is airborne; otherwise `0x30` |
| `0x32` | `0x30` |
| `0x36`, `0x38`, `0x39`, `0x4A..0x50` | random `0x29/0x2A` when the fighter's grounded bit is set, otherwise `0x30` |

All other results survive this pass unchanged. The *expected repeat count* is
the same raw value used later by the rehit exception: positive `+0xE5C`
(otherwise zero) while `+0xB00 == 0`, or `1` while `+0xB00 != 0`.

Two subsequent streak checks can still force `0x37`. The count at `+0xB64`
increments only when the accepted attack satisfies raw gates at `+0x10` and
`+0x50`, its signed `+0x2E` equals the expected repeat count, and retained
record `+0xB60` is null or the same record. A provisional `0x2F` becomes
`0x37` when the expected repeat count is below `2`, `+0xB64 > 2`, and the
standard source is grounded. Independently, any provisional result becomes
`0x37` when the receiver is grounded, `+0xB64 > 3`, and attack byte `+0x19`
is zero. The raw attack gates are intentionally not given speculative content
names.

Two final substates are initializer overrides rather than direct `+0x2C`
selector results. `FUN_002346b0` zeros both response-speed fields and enters
`0x5B` if grounded or `0x5C` if airborne when all three raw prerequisites hold:
fighter byte `+0x62` bit `0` is clear, `FUN_00244f80(fighter[+0x20])` returns
zero, and attack record `+0x10 & 0x00F00000` is nonzero. The first two
prerequisites and the attack mask are left unnamed because their player-facing
meanings are not established.

These are confirmed mechanics, but the static evidence does not justify names
such as “light stagger,” “crumple,” “wall splat,” or “guard crush” for any raw
substate.

When the selected result is `0x3A` or `0x3B`, ordinary-response initialization
increments fighter `+0xB6E` up to `3`. If it is already `3` and secondary block
`+0x224` has no pending activation (`flag 0x0004` clear), initialization instead
primes `+0x230` with `60`. The
later downed handoff reads the updated `+0xB6E`, so its
`1.0 - 0.25 * +0xB6E` scale progresses through `0.75`, `0.50`, and `0.25`.
This is also why the `0x3A/0x3B` rehit predicate's `+0x230 <= 0` condition is
material on a capped repeat.

There is a second ordinary-response source for that countdown. When the
primary timeline crosses event `0`, `FUN_002346B0` tests raw attack halfword
`+0x32`. If it equals `0x7FFF` and secondary block pending flag `0x0004` is
clear, the routine stages `+0x230` from the response row's `+0x16` value after
an update-rate adjustment. Let receiver rate `r` and paired-fighter rate `p` be
their respective `+0x1AC` values. Starting from the row base, the exact
instruction sequence multiplies by `2-r` when `r != 1`, multiplies by `2-r`
again when `p > 1`, and multiplies by `2-p` when `p < 1`. The repeated `r` in
the `p > 1` branch is present in the clean instructions and is not normalized
to a symmetric formula. The result is converted by EE `cvt.w.s` under the
active FPU rounding mode and stored through a signed halfword; this local path
does not set that rounding mode. The unadjusted bases are `6` for `0x3A` and
`8` for `0x3B`.

The capped-repeat `60` competes with the attack's own `+0x32` value, which
`FUN_00224870` applies earlier in the same initializer. That call leaves the
pending flag set for a positive or zero `+0x32`, so the `60` is written only
when `+0x32` is sentinel `0x7FFF` (with no earlier pending value) or negative.
The `60` is written positive with the pending flag clear. With the sentinel,
the event-`0` path then replaces it with the adjusted `6`/`8` base; per
[Hit update order](#hit-update-order-and-elapsed-updates), that replacement
happens in the hit update itself unless a pause is already active. With a
negative `+0x32`, the `60` remains.

### Native action identifiers

The overlay descriptor table is indexed directly by substate and has an
`0x08`-byte row containing two encoded live pointers: a NUL-terminated action
identifier and descriptor data. Because those pointers are already live
values, each target's file offset was decoded as `pointer - 0x006B3F00`; the
preserved export's target labels are `0x40` too high under the header-omission
convention. The exact relevant identifiers are:

| State | Native identifier | State | Native identifier | State | Native identifier |
| ---: | --- | ---: | --- | ---: | --- |
| `0x27` | `ACT_DMG_NSH` | `0x3B` | `ACT_DMG_DDL` | `0x4F` | `ACT_DMG_GBR` |
| `0x28` | `ACT_DMG_NSL` | `0x3C` | `ACT_DMG_BSF` | `0x50` | `ACT_DMG_CNT` |
| `0x29` | `ACT_DMG_NMH` | `0x3D` | `ACT_DMG_BSB` | `0x51` | `ACT_DMG_AND` |
| `0x2A` | `ACT_DMG_NML` | `0x3E` | `ACT_DMG_BSG` | `0x52` | `ACT_DMG_ANDA` |
| `0x2B` | `ACT_DMG_NLH` | `0x3F` | `ACT_DMG_BR` | `0x53` | `ACT_DMG_AFD` |
| `0x2C` | `ACT_DMG_NLL` | `0x40` | `ACT_DMG_BD` | `0x54` | `ACT_DMG_AFDA` |
| `0x2D` | `ACT_DMG_NHH` | `0x41` | `ACT_DMG_BS` | `0x55` | `ACT_DMG_ATD` |
| `0x2E` | `ACT_DMG_NHL` | `0x42` | `ACT_DMG_SSF` | `0x56` | `ACT_DMG_ATDA` |
| `0x2F` | `ACT_DMG_NAS` | `0x43` | `ACT_DMG_SSB` | `0x57` | `ACT_DMG_AWD` |
| `0x30` | `ACT_DMG_NAM` | `0x44` | `ACT_DMG_SR` | `0x58` | `ACT_DMG_AWDA` |
| `0x31` | `ACT_DMG_NAL` | `0x45` | `ACT_DMG_SD` | `0x59` | `ACT_DMG_XF` |
| `0x32` | `ACT_DMG_NB12` | `0x46` | `ACT_DMG_SD2` | `0x5A` | `ACT_DMG_XD` |
| `0x33` | `ACT_DMG_NB13` | `0x47` | `ACT_DMG_SD3` | `0x5B` | `ACT_DMG_XB` |
| `0x34` | `ACT_DMG_NB14` | `0x48` | `ACT_DMG_SBS` | `0x5C` | `ACT_DMG_XB` |
| `0x35` | `ACT_DMG_NB15` | `0x49` | `ACT_DMG_SBD` | `0x5D` | `ACT_DWN_0` |
| `0x36` | `ACT_DMG_ND` | `0x4A` | `ACT_DMG_HOLD` | `0x5E` | `ACT_DWN_1` |
| `0x37` | `ACT_DMG_NDA` | `0x4B` | `ACT_DMG_HOLD_A` | `0x5F` | `ACT_DWN_2` |
| `0x38` | `ACT_DMG_NDH` | `0x4C` | `ACT_DMG_HOLD_L` | `0x60` | `ACT_DWN_3` |
| `0x39` | `ACT_DMG_NDL` | `0x4D` | `ACT_DMG_HOLD_D` | `0x61` | `ACT_DDM_0` |
| `0x3A` | `ACT_DMG_DDS` | `0x4E` | `ACT_DMG_HOLD_F` | `0x62` | `ACT_DDM_1` |

These strings are canonical authored identifiers, not licenses to expand `NSH`,
`GBR`, `DWN`, or other abbreviations into unverified player-facing names.

### Descriptor phase control

The descriptor row's second live pointer targets an array of `0x08`-byte phase
records. For native actions, the first signed halfword selects an animation
slot, the second signed halfword controls phase advancement, and a first
halfword of `-1` is the terminal record. The third halfword is the animation
start frame written to `+0xB94` (a negative value counts back from the
animation's frame count), while the fourth sets the secondary action-timeline
and animation rate at `+0xB90` (preserved overlay fragment `0x0071F640`).

Live overlay `0x0071F160` (preserved export `FUN_0071f120` at
`0x0071F120`) interprets every second-halfword form used by substates
`0x27..0x62` as follows:

| Phase condition | Proven advance condition |
| ---: | --- |
| `-0x10` | Current animation reaches its end (`+0xB88 != 0`). |
| `-0x11` | Fighter is grounded. |
| `-0x12` | Vertical response speed is negative, or the fighter is grounded. |
| `-0x13` | Current animation reaches its end, or the fighter is grounded. |
| `-0x14` | Current animation reaches its end and the fighter is grounded. |
| `0` | No automatic phase advance in this common updater. |
| positive | Secondary cursor `+0x1E8` reaches the authored value. Relevant values are `3`, `4`, and `6`. |

Decoding every ordinary-response descriptor from the exact clean image gives
the following complete phase-condition sequences. Each sequence is read from
phase `0` toward its terminal record. `E` is animation end (`-0x10`), `G` is
grounded (`-0x11`), `D` is negative vertical speed or grounded (`-0x12`), `O`
is animation end or grounded (`-0x13`), `B` is animation end and grounded
(`-0x14`), `C<n>` is secondary cursor `<n>`, `H` is held condition `0`, and
`T` is the terminal `-1` record.

| Phase-condition sequence | Ordinary substates |
| --- | --- |
| `E, E, T` | `0x27..0x2E`, `0x47` |
| `D, C6, T` | `0x2F..0x31` |
| `C4, E, T` | `0x32..0x34` |
| `C4, B, T` | `0x35` |
| `D, G, E, E, T` | `0x36` |
| `D, G, E, T` | `0x37`, `0x52/0x54/0x56/0x58` |
| `G, E, T` | `0x38/0x39`, `0x42..0x44` |
| `E, T` | `0x3A/0x3B`, `0x45/0x46`, `0x4F`, `0x51/0x53/0x55/0x57`, `0x5B` |
| `E, C4, G, E, T` | `0x3C/0x3D` |
| `E, E, E, T` | `0x3E` |
| `E, D, G, E, T` | `0x3F`, `0x59` |
| `O, O, E, E, T` | `0x40/0x41` |
| `C3, G, E, T` | `0x48/0x49` |
| `H, T` | `0x4A..0x4E`, `0x50` |
| `O, G, E, T` | `0x5A` |
| `C4, C6, G, E, T` | `0x5C` |

The two timeline cursors do not always share one time base. On each unpaused
steady-state call to `FUN_0024D5E0`, `FUN_00211D80` advances the primary block
at `+0x1B8` by fighter scalar `+0x1AC`, so its current integer cursor is
`+0x1C4`. It advances the secondary block at `+0x1DC` by
`+0x1AC * (+0xB90 / 256)`, making `+0x1E8` the current integer cursor. A
newly selected/restarted animation has a separate one-shot reset path, and a
positive `+0x20C` pause suppresses both advances.

Most response-phase records author `+0xB90 = 256` (`1.0`). The complete set of
non-default rates in substates `0x27..0x62` is:

| Substate and phase | Authored `+0xB90` | Secondary rate |
| --- | ---: | ---: |
| `0x29/0x2A`, phases `0/1` | `240` | `0.9375` |
| `0x2B/0x2C`, phases `0/1` | `224` | `0.875` |
| `0x2D`, phases `0/1` | `176` | `0.6875` |
| `0x2E`, phases `0/1`; `0x3B`, phase `0` | `192` | `0.75` |
| `0x32..0x35`, phase `1`; `0x3E`, phase `1`; `0x60`, phase `0` | `512` | `2.0` |
| `0x5A`, phase `0` | `64` | `0.25` |
| `0x5B`, phase `0`; `0x5E`, phase `0` | `384` | `1.5` |

Thus ordinary hit-response duration is not one fixed hitstun counter. Most
substates advance at authored animation/contact/timeline conditions, while the
`H` rows require state-specific external progression because the common phase
updater cannot advance condition `0` by itself. The animation-gated lengths
are decoded in
[Animations and animation-gated phase lengths](#animations-and-animation-gated-phase-lengths);
physics-gated phases have no static length.

This is stronger than inferring contact from an action name: `+0xB88` is
cleared when `FUN_00218190` changes animation and is later overwritten by the
return from the resident animation-advance routine. That return becomes
nonzero when the animation reaches its end.

The recovery descriptors independently corroborate the resident recovery
dispatcher. Their complete sequences and authored secondary rates are:

| Recovery substate | Phase sequence | Non-default rate |
| ---: | --- | --- |
| `0x5D` | `H, T` | none |
| `0x5E` | `G, T` | phase `0`: `384/256 = 1.5` |
| `0x5F` | `D, T` | none |
| `0x60` | `C3, T` | phase `0`: `512/256 = 2.0` |
| `0x61` | `E, H, T` | none |
| `0x62` | `G, E, H, T` | none |

Thus the common updater cannot complete held `0x5D` by itself; the resident
threshold dispatcher owns its choices. It completes `0x5E` when grounded,
`0x5F` when vertical response is negative or the fighter is grounded, and
`0x60` at secondary cursor `3`. The separate `0x61/0x62` route ultimately
reaches held phases as well, matching its external state-specific placement
progression rather than the `0x5D` threshold logic.

### Animations and animation-gated phase lengths

The animation slot indexes fighter pointer `+0xB84`, whose entries are the
animation objects that `FUN_001A8F00` looks up by name from the character
record's `ANM_` name array (record `+0x44/+0x48`); `FUN_00219620` shows that
index correspondence directly for the entries it fills. It compares each
name's character-code field with a short constant and selects file
`2cmnbod1` on a match; every `ANM_pcmn` name used below was found in
`CMN/2CMNBOD1.CCS` and every other name in the character's own `2???bod1`. Across all 74 primary
character records, every slot used by substates `0x27..0x62` resolves to the
same animation role: either the shared `ANM_pcmn????` name (some characters
substitute their own code with the same suffix) or a per-character
`ANM_p???????` name with a fixed suffix. For example, slot `1` is `htn4`, slot
`31..33` are `col0..col2`, slot `34` is `kno0`, slot `47` is `gbr0`, and slot
`48` is `ost0`.

The resident CCS loader `FUN_001B1470` stores an animation chunk's
(`0xCCCC0700`) second word as the animation object's frame count `+0x0C`.
`FUN_0024D1C0` advances the animation by `+0xB90 * +0x1AC` in `1/256`-frame
units once per update while `+0x20C < 1`, and `FUN_001BB210` reports the end
once the position reaches `(frame_count - 1) * 256` (non-looping animations).
When a new animation starts, `FUN_00218060` loads it through
`FUN_001B99B0(..., 0)`, which discards any blend object and creates none, then
seeks to start frame `S`; a phase with `R < 256` and `S == 0` is instead
seeked to frame `1`. An animation-end phase with frame count `F`, effective
start `S`, and rate `R` therefore needs `n = max(1, ceil((F - 1 - S) * 256 /
R))` animation advances, one per unpaused update at `+0x1AC == 1.0`.

Within one update, `FUN_00248580` runs the phase updater (live `0x0071F160`)
on the previous animation result, `FUN_00249640` ends by selecting the current
phase's animation (live `0x0071F640`), and the animation pass
(`FUN_0024DA50` -> `FUN_0024D1C0`, reached through the coordinator's removal
pass after `FUN_0024FD80`) then advances it. An animation-end phase therefore
occupies exactly `n` updates, and a timeline phase `C<k>` occupies
`ceil(k * 256 / R)` updates. The state setter does not clear `+0xB88`, but a
state entered by hit routing cannot consume the previous animation's latched
end: the routing pass of `FUN_0024FD80` sets fighter byte `+0x63` bit `0`
while primary event `0` is armed, `FUN_00248580` returns immediately while
that bit is set, and `FUN_0024DA50` clears it after the animation pass.

Decoding every referenced animation chunk in `CMN/2CMNBOD1.CCS` and the
characters' `PL/2???BOD1.CCS` files gives these per-phase counts. Each cell is
the phase condition, the animation-name suffix, and `n` (or `ceil` form for
`C<k>`); a range gives the minimum and maximum across characters with the
median in parentheses. `G` and `D` phases end on physics, so only their
animation is listed; `O` ends no later than `n`, `B` no earlier. Two
characters whose animations are in other files (codes `kmv` and `kdv`) are
omitted.

| Substate | Phases and animation-gated update counts |
| --- | --- |
| `0x27/0x28` | E `htn4` 3, E `hxn4` 3..11 (7) |
| `0x29` | E `htn0` 3, E `hxn0` 3..15 (10) |
| `0x2A` | E `htn1` 3, E `hxn1` 3..12 (12) |
| `0x2B` | E `htn0` 3, E `hxn0` 3..16 (11) |
| `0x2C` | E `htn1` 3, E `hxn1` 3..13 (13) |
| `0x2D` | E `htn0` 3, E `hxn0` 3..21 (14) |
| `0x2E` | E `htn1` 3, E `hxn1` 3..15 (15) |
| `0x2F..0x31` | D `fht0`, C6 `jmp2` 6 |
| `0x32..0x34` | C4 `fht0` 4, E `jpz1` 8..15 (9) |
| `0x35` | C4 `fht0` 4, B `jpz1` 8..15 (9) |
| `0x36` | D `fht0`, G `fxk0`, E `fxk2` 2, E `col1` 8..28 (28) |
| `0x37` | D `fht0`, G `fxk0`, E `col2` 13..28 (28) |
| `0x38/0x39` | G `spn0`, E `col1` 8..28 (28) |
| `0x3A` | E `col0` 8 |
| `0x3B` | E `col0` 10 |
| `0x3C` | E `nxf1` 3, C4 `fht1` 4, G `fxk1`, E `col1` 8..28 (28) |
| `0x3D` | E `nxf0` 7, C4 `fht0` 4, G `fxk0`, E `col1` 8..28 (28) |
| `0x3E` | E `nxf0` 7, E `yft0` 20, E `col1` 8..28 (28) |
| `0x3F`, `0x59` | E `nxf2` 2..10 (4), D `fht2`, G `fxf0`, E `col2` 13..28 (28) |
| `0x40` | O `nxf3` 4, O `fal0` 10, E `fxk2` 2, E `col0` 8 |
| `0x41` | O `nxf3` 4, O `yft0` 40, E `fxk0` 6, E `col1` 8..28 (28) |
| `0x42` / `0x43` / `0x44` | G `fxc1` / `fxc0` / `fxc2`, E `col2` 13..28 (28) |
| `0x45/0x46` | E `col2` 13..28 (28) |
| `0x47` | E `fxk0` 6, E `col1` 8..28 (28) |
| `0x48` | C3 `fxc1` 3, G `spn0`, E `col1` 8..28 (28) |
| `0x49` | C3 `col2` 3, G `bnd0`, E `col1` 8..28 (28) |
| `0x4A..0x4E`, `0x50` | H `hth0`, `hah0`, `hth1`, `nxf3`, `hth2`, `hth0` |
| `0x4F` | E `gbr0` 14..34 (24) |
| `0x51/0x53/0x55/0x57` | E `htn3` 40..60 (40) |
| `0x52/0x54/0x56/0x58` | D `fht0`, G `fxk0`, E `col2` 13..28 (28) |
| `0x5A` | O `fxk1` 20..24 (24), G `fal0`, E `col1` 8..28 (28) |
| `0x5B` | E `ost0` 27..30 (27) |
| `0x5C` | C4 `fht0` 4, C6 `jmp2` 6, G `dow0`, E `lan0` 9..20 (10) |

For example, a grounded light hit `0x27` on a median character occupies about
`3 + 7 = 10` unpaused updates of animation before it returns to neutral, in
addition to the attack pause described below, while the downed `col` phases
dominate the knockdown rows. **Inference:** the `htn`/`hxn` pairs are hit and
recovery halves of the light reactions and `col` is the landing/collapse
animation; the names are recorded, not visually confirmed.

The recovery substates use `kno0` (`0x5D`, two frames), the shared `jmp2`
for `0x5E..0x60`, `col0` then `kno0` for `0x61`, and per-character `dow0`,
`lan0`, `nut0` for `0x62`. Timeline phase `0x60` therefore completes after
`ceil(3 * 256 / 512) = 2` updates, and the `col0` phase of `0x61` after 8.

## Table-driven knockback and launch

The ordinary response table begins at resident runtime `0x00407670`, ELF file
offset `0x00307770`. It has `0x18`-byte entries indexed by
`substate - 0x27`, covering all 54 rows through `0x5C`. The bytes immediately
after the `0x5C` row begin unrelated pointer/data content, independently
confirming the table boundary. Decoding the exact clean bytes and tracing every
consumed field establishes this layout:

| Entry offset | Type | Demonstrated consumer behavior |
| ---: | --- | --- |
| `+0x00` | `u16` flags | Low bits choose the primary/secondary action timeline; high byte chooses replacement/addition behavior for the two response-speed fields. |
| `+0x02` | `s16` event gate | Timeline point tested before applying the entry's motion. Values used here are `0..3`. |
| `+0x04` | `f32` | Planar response speed ultimately stored at fighter `+0x994`, with orientation and combat modifiers. |
| `+0x08` | `f32` | Vertical response speed ultimately stored at fighter `+0x998`, with combat modifiers. |
| `+0x0C` | `f32` | Approach/damping factor used while moving `+0x994` toward zero on updates that do not cross the event gate. |
| `+0x10` | `f32` | Gravity argument copied to fighter `+0x9B4` when not `1.0`; in hit response it only lifts the terminal-speed clamp. |
| `+0x14` | `s16` | Event impulse copied, with sign handling, into the `+0x204..+0x21C` response channel. |
| `+0x16` | `s16` | Minimum raised into general timer/lock `+0x254`; an attack-record `+0x30` contribution may be added. |

`FUN_00234da0` invokes the common table updater every action update. All 54
rows select the primary timeline. On the exact update where that cursor crosses
the row's event gate, the updater writes the two response-speed components and
preserves a copy of the attack-owned motion scale. On every invocation that
does not cross the gate, including later ones, it instead approaches planar
speed `+0x994` toward zero using the row's damping factor. The gate is therefore
a one-shot event edge, not a condition that remains true after the threshold.
The auxiliary value `+0x10` is copied whenever this updater runs and it differs
from `1.0`.

A separate crossing test applies entry `+0x14` to the pause channel. With
fighter `+0xB00 == 0`, it uses the row's authored event gate; with `+0xB00`
nonzero, it uses primary event `0` instead. Therefore displacement is not
encoded in the substate alone: it is the substate's table row plus event edge,
orientation, attacker and defender modifiers, and current motion.

The complete clean table is compacted below only where rows are byte-equivalent.
`R` means flags `0x0101`: use the primary timeline and replace both speed
components. `A` means `0x0201`: use the primary timeline and add both speed
components to their current values.

| Substate(s) | Mode | Gate | Planar | Vertical | Damping | Aux | Pause | Lock |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0x27/0x28` | R | `0` | `10` | `0` | `0.35` | `1` | `1` | `5` |
| `0x29/0x2A` | R | `0` | `30` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2B/0x2E` | R | `0` | `45` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2C` | R | `0` | `40` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2D` | R | `0` | `50` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2F` | R | `0` | `30` | `25` | `0.25` | `1` | `1` | `5` |
| `0x30` | R | `0` | `40` | `30` | `0.25` | `1` | `1` | `5` |
| `0x31` | R | `0` | `50` | `35` | `0.25` | `1` | `1` | `5` |
| `0x32` | R | `0` | `10` | `50` | `0.125` | `1` | `2` | `5` |
| `0x33` | R | `0` | `30` | `45` | `0.125` | `1` | `2` | `5` |
| `0x34` | R | `0` | `50` | `40` | `0.125` | `2` | `5` | `0` |
| `0x35` | R | `0` | `65` | `25` | `0.12` | `1` | `2` | `5` |
| `0x36` | R | `0` | `55` | `20` | `0.10` | `1` | `1` | `120` |
| `0x37` | R | `0` | `50` | `32.5` | `0.15` | `1` | `1` | `120` |
| `0x38` | R | `0` | `50` | `40` | `0.075` | `2.5` | `1` | `120` |
| `0x39` | R | `0` | `60` | `25` | `0.075` | `2` | `1` | `120` |
| `0x3A` | R | `0` | `10` | `0` | `0.25` | `1` | `1` | `6` |
| `0x3B` | R | `0` | `30` | `0` | `0.25` | `1` | `1` | `8` |
| `0x3C/0x3D` | R | `0` | `60` | `20` | `0.075` | `1` | `2` | `120` |
| `0x3E` | R | `0` | `80` | `0` | `0` | `1` | `2` | `120` |
| `0x3F` | R | `0` | `0` | `55` | `0.35` | `1` | `2` | `120` |
| `0x40` | R | `0` | `0` | `-50` | `0.35` | `1.25` | `1` | `120` |
| `0x41` | R | `0` | `60` | `-50` | `0.05` | `0.8` | `2` | `120` |
| `0x42/0x45` | R | `2` | `0` | `0` | `0.35` | `1` | `2` | `120` |
| `0x43` | R | `3` | `0` | `0` | `0.35` | `1` | `2` | `120` |
| `0x44` | A | `2` | `0` | `-30` | `0.35` | `1` | `2` | `120` |
| `0x46` | R | `1` | `15` | `7.5` | `0.075` | `1` | `2` | `120` |
| `0x47` | A | `1` | `20` | `0` | `0.05` | `1` | `1` | `120` |
| `0x48` | R | `2` | `0` | `40` | `0.075` | `1` | `2` | `5` |
| `0x49` | R | `3` | `10` | `40` | `0.075` | `0.75` | `2` | `5` |
| `0x4A/0x4B/0x4C/0x4E` | R | `0` | `0` | `0` | `0.35` | `1` | `1` | `0` |
| `0x4D` | R | `0` | `0` | `0` | `0.35` | `1.5` | `1` | `0` |
| `0x4F` | R | `0` | `20` | `0` | `0.5` | `1` | `0` | `5` |
| `0x50` | R | `0` | `0` | `0` | `0.35` | `1` | `4` | `0` |
| `0x51/0x53/0x55/0x57` | R | `0` | `40` | `0` | `0.35` | `1` | `1` | `120` |
| `0x52/0x54/0x56/0x58` | R | `0` | `40` | `30` | `0.075` | `1` | `1` | `120` |
| `0x59` | R | `0` | `0` | `55` | `0.075` | `1` | `2` | `120` |
| `0x5A` | A | `0` | `0` | `0` | `0.25` | `1` | `0` | `120` |
| `0x5B` | R | `0` | `40` | `0` | `0.10` | `1` | `0` | `5` |
| `0x5C` | R | `0` | `40` | `40` | `0.10` | `1` | `1` | `6` |

Negative vertical values are preserved as authored and processed through the
same velocity field; this document does not assume which screen-space
direction the content author considered positive.

### Velocity modifier order

The table values are authored bases, not guaranteed final speeds.
`FUN_0021ACB0` first applies orientation and the row's replace/add flags, then
uses the following mutually exclusive source/receiver modifier chain:

1. If `FUN_00307320(source)` returns scalar `s != 1.0`, planar speed is
   multiplied by `s` and vertical speed by `1 + 0.5 * (s - 1)`.
2. Otherwise, in ordinary major state `5` with `(fighter[+0xB00] & 0xFF00)`
   nonzero, both components are multiplied by `1.25`.
3. Otherwise, source field `+0x154` applies the same planar/full and
   vertical/half-strength formula. Receiver field `+0x150` is then clamped to
   `[0,2]`; for clamped value `q`, planar speed is multiplied by
   `1 - 0.75 * (q - 1)` and vertical speed by `1 - 0.25 * (q - 1)`.

After that chain and the shared response-coupling helper, transient fighter
modifiers at `+0x9A0`, `+0x9A8`, and `+0x9AC` can further scale both
components, planar only, and vertical only respectively. Each consumed
transient is reset to `1.0`. The source object itself is accepted for this
chain only when non-null and its raw field `+0x0C` is zero. These facts explain
why the clean table supports reproducible base comparisons but cannot alone
predict character- and situation-specific displacement.

`+0x9A0` is the attack's own knockback scale. When a hit arrives with a new
attack record, `FUN_00232A50` (or the retarget path of `FUN_00241F10`)
retains the record, resets the repeat count `+0xE5C` from record `+0x2E`,
and, when that count is nonzero, copies record float `+0x28` to `+0x9A0`.
At the row's event edge `FUN_0021ACB0` saves it to `+0x9A4` and, for scale
`s != 1.0`, multiplies planar speed by `s` and vertical speed by
`1 + 0.5 * (|s| - 1)` when `|s| > 1`; for `|s| <= 1` vertical speed is
multiplied by `|s|`, or by the half-strength form when the source scalar is
below `1.0`. Before replacing or adding the row speeds, the same edge clamps
the current planar speed to the character-table limit at `+0x60` (grounded)
or `+0x74` (airborne) and the current airborne vertical speed to at least
`-3 * +0x70` of the table selected by `FUN_00307C50`.

Of the 2,484 damaging records, 1,859 author `+0x28 == 1.0`; 423 are
stronger (`1.5` on 154, `1.25` on 149, `1.2` on 37, `2.0` on 33, and other
values from `1.1` to `3.0` on 50), 200 are weaker (`0.75` on 63,
`0.8` on 29, down to `0.0` on 11), and two are negative (`-0.5`, `-2.0`),
which reverses the planar direction.

### Gravity and airtime

The movement pass `FUN_0024A660` (called from `FUN_0024CFD0` in the
`FUN_0024DA50` animation pass, so only while `+0x20C < 1`) moves the fighter
by its current speeds times `+0x1AC` and then, while airborne, applies
`FUN_002183D0(+0x9B4, fighter, &+0x998)`. For a fighter in major state `5`,
with nonzero `+0xB00`, or with byte `+0x61` bit `7` set, that routine uses a
fixed gravity of `3.0 * +0x1AC` per update and a terminal vertical speed of
`-90`; other states use the character record's `+0x6C` and `+0x70` scaled by
`+0x9B4`. Thus the response row's auxiliary field `+0x10`, copied to
`+0x9B4` on every response update, does not scale hit-response gravity: a
nonzero value only removes the `-90` clamp when it differs from `1.0`, and
`+0x9B4` is reset to `1.0` after each movement pass.

Because the launch speed is written in the hit update and the first movement
pass follows in the same update, an ordinary response launched with final
vertical speed `v > 0` (row value after the modifiers above) at rate `1.0`
reaches a negative vertical speed, satisfying a `D` phase, after
`floor(v / 3) + 1` active updates. **Inference:** over flat ground at the
launch height the fighter lands after roughly `2v/3 + 1` active updates,
for example about 14 to 15 for the unmodified `0x3C/0x3D` value `20` and
about 38 for the `55` of `0x3F`; ground contact is decided by stage collision
geometry, so these are not exact. The pause updates add to these counts
because they suspend movement.

## Fighter-update pause and action lock

The response timing uses two ordered generic countdown blocks rather than one
undifferentiated “hitstun timer”:

1. The current count at `+0x20C` is decremented at a fixed rate of `1.0`.
   While it is positive, the main fighter loop does not run the normal action
   timeline or per-action update dispatch. The displayed position instead uses
   a jittered copy whose variation is driven by this count. This establishes a
   fighter-update pause, conventionally comparable to hitstop, without assuming
   a display-frame duration.
2. Only after `+0x20C < 1` does the main timer update decrement `+0x254`, using
   the fighter's update-rate scalar at `+0x1AC`. `FUN_00239e50`, which is called
   by native action-selection and input-action paths, returns false whenever
   `+0x254` is nonzero. This establishes an action-entry lock.

The generic blocks have a pending-activation sign convention. Initializers
normally write authored positive value `N` as `-N` and set block flag
`0x0004`. On the next `FUN_0024C440` maintenance pass, that flag causes all
integer and floating count views to be sign-flipped to positive and clears the
flag; no decrement occurs during that activation pass. A live observation made
between initialization and activation can therefore see a negative `+0x20C`
or `+0x230` even though the ensuing active count is positive.

After activation, `FUN_00211E70` implements the decrement phase. It subtracts
the requested rate from the block's fractional accumulator at block offset
`+0x1C`, decrements the integer count at block offset `+0x0C` whenever that
accumulator crosses `-1.0`, and clamps the integer count at zero. This also
explains why a newly staged pause is not shortened on its activation pass.

Ordinary response-table field `+0x14` feeds the `+0x20C` pause channel at its
timeline event, subject to the `+0xB00` event-`0` override above. A positive
table value is staged negative with pending flag `0x0004`, but only when that
flag is not already set; when activated, the pause suspends both action
timelines and the per-action dispatcher.

Attack-record signed halfword `+0x30` feeds the same channel earlier, during
accepted-hit initialization (`FUN_00224510(fighter, attack, 0)` from
`FUN_00232B80`). An authored positive `N` is staged as `-N` with the pending
flag, while an authored negative `-N` is written immediately as positive `N`
without that flag. Zero clears the block but leaves the pending flag set with
a zero count, and sentinel `0x7FFF` does not touch the block. Because the row
pause is skipped while the flag is pending, a positive or zero attack value
suppresses the row's `+0x14` pause on a gate-`0` row; the row value applies
after sentinel `0x7FFF` or a negative attack value, or on a later gate.

`FUN_002346B0` applies the row's `+0x16` action-lock minimum when the primary
timeline crosses event `0`. When the table minimum raises `+0x254`, the
absolute attack-record `+0x30` contribution is added unless it is sentinel
`0x7FFF`; when the current lock already meets the minimum, the lock is left
unchanged. The lock is written directly as a positive count without a pending
flag.
Attack-record `+0x10` bit `0x00000002` instead forces a count of `20`. With
that bit clear, the table minimum is bypassed when either raw attack type mask
`0x00F00000` or `0x000F0000` is nonzero.
The full time before a fighter can act therefore includes
the ordered pause and action-lock counts as well as the response state's own
timeline and exit conditions; `+0x254` alone is not total hitstun. The exact
update-by-update order is in
[Hit update order and elapsed updates](#hit-update-order-and-elapsed-updates).

`FUN_00239e50` makes that last distinction concrete. Once `+0x254` is zero,
ordinary major state `5` still rejects ordinary action entry throughout
`0x27..0x5A`; `0x5B/0x5C` are immediately eligible, while a special selector
value `2` can bypass the ordinary-state rejection. In recovery major state `6`,
`0x5D/0x5E` remain ineligible, `0x5F` becomes eligible at action cursor
`+0x1C4 >= 8`, and `0x60` becomes eligible at cursor `>= 3`. Other recovery
substates are rejected by this predicate. These are action-entry gates, not
animation-completion tests.

## Hit update order and elapsed updates

Native battle gameplay advances fighter updates at 30 Hz at nominal speed
([Battle lifecycle](battle_lifecycle.md#battle-update-cadence)). Within one
update, resident `FUN_001F03E0` calls the fighter coordinator's registry slot
`+0x0C` (`FUN_002504B0`), then slot `+0x10`, then slot `+0x14`
(`FUN_00250800`). `FUN_002504B0` runs `FUN_0024FD80` and then the generic
removal pass (live `0x00709C70`, see
[Battle entities](battle_entities.md)), which calls every fighter's virtual
slot `+0x10`, `FUN_0024DA50`: while `+0x20C < 1` it runs the movement pass
`FUN_0024CFD0` and the animation pass `FUN_0024D1C0`. Coordinator slot
`+0x14` finally calls every fighter's virtual slot `+0x18`, `FUN_0024DE40`,
which advances both action timelines through `FUN_0024D5E0` while
`+0x20C < 1`.

`FUN_0024FD80` itself runs these passes in order over the fighter list:

1. `FUN_0024C440` maintenance for every fighter (lock decrement while the
   pause count is below `1`, secondary and pause block activation or
   decrement);
2. pair and interaction helpers, then for each active fighter the pair hit
   resolver `FUN_0021ED70` and the `+0xE3C` hit bits: `0x100` calls
   `FUN_00220690`, `0x1` calls router mode `0`, `0x8` mode `2`, and `0x4`
   mode `1`;
3. removal of fighters whose slot `+0x1C` requests it;
4. for every fighter with `+0x20C < 1`: `FUN_00217320`, `FUN_002173D0`,
   `FUN_00248580`, input update `FUN_00248EC0`, and per-action dispatcher
   `FUN_00249640`; and
5. `+0xE3C` bit `0x2` handling through `FUN_00221600`.

The action-state setter clears the primary block with its step flag set, so
`FUN_002118A0(block, 0)` reports event `0` on the first per-action update
after entry and stops reporting it once `FUN_0024D5E0` advances the cursor.
Because routing (pass 2) precedes the per-action pass (pass 4) in the same
update, event `0` of a new ordinary response runs in the hit update itself
whenever `+0x20C` is still below `1` after routing. That is the case for a
positive, zero, or sentinel attack `+0x30` with no active pause, because the
positive form is only staged negative. It is not the case for a negative
`+0x30`, which activates the pause immediately and delays event `0` until the
pause ends.

For an authored positive attack pause `N`, rates `+0x1AC == 1.0` for both
fighters, and no already-pending blocks, the exact sequence is:

| Update | Receiver behavior |
| ---: | --- |
| `0` | Accepted hit routed; `(5, response)` entered; pause staged `-N`; per-action pass runs event `0`: gate-`0` response motion, gated attack damage (see [Damage](damage.md)), action lock, and the `+0x230` countdown staging below; row pause skipped because the attack pause is pending; first movement and gravity step and first animation advance; the timeline advances to cursor `1`. |
| `1` | Maintenance decrements the lock once (pause still `-N` at that check), then activates the pause at `N`. Per-action, movement, animation, and timeline passes are suppressed. |
| `2..N` | Pause counts down; everything action-related remains suppressed and the lock does not decrement. |
| `N+1` | Maintenance sees pause `1` at the lock check (no lock decrement), then reaches `0`; the per-action pass and timelines resume. |

The freeze is not total. While `+0x20C >= 1`, slot `+0x10` (`FUN_0024DA50`)
skips the animation pass but, for fighters whose `+0x60` bits `5..8` are
zero, still runs the command bridge `FUN_00217320`, input action selection
`FUN_0023A390` with `+0x338`, and the `+0x95C` guard-input age update. A
candidate such as an Extra Hit counter can therefore be chosen during the
pause.

Thus an authored pause of `N` suspends the receiver's action, timeline, and
animation updates for exactly `N` updates after the hit update, or `N/30` s
at nominal speed. If the row minimum `L` set the lock
to `L + N` in update `0`, the lock reaches zero in update `2N + L`. For a
negative authored `-N`, updates `0..N-1` are frozen and event `0` runs in
update `N`; if the row pause then applies, a second freeze of the row's
`+0x14` count follows. A rate other than `1.0` scales the lock and timeline
steps, but not the pause, which always decrements by `1.0`.

The attacker receives a matching pause through `+0xE3C` bit `0x100`, handled
by `FUN_00220690(attacker)` in the same routing pass. It applies the router's
two early-return bit patterns to the result of the sibling classifier
`FUN_00240990` and requires the defender's `+0x230`
to be non-positive and either attack `+0x10` bit `0x2` or a nonzero expected
repeat count. Unless `+0x10` bit `0x2` is set, it then calls
`FUN_00224510(attacker, attack, 1)`, whose attacker/guard mode inverts the
sign convention: an authored positive `N` is written as an active `N`
immediately, so the attacker is suspended in updates `0..N-1`, one update
earlier than the receiver. Attack `+0x14` bit `0x00020000` skips the
attacker pause entirely (151 records, 138 damaging). With sentinel `0x7FFF`,
the attacker instead takes the `+0x14` pause of the response row that
`FUN_00231C60` selects for the defender, or of the guarded-response row when
the defender's `+0x95A` guard state applies, also active immediately.

The clean attack tables give the following authored pause values. Of 2,484
records with nonzero damage `+0x24`, `+0x30` is `2` on 914, `3` on 415, `1`
on 271, `4` on 194, `5` on 86, sentinel `0x7FFF` on 477, zero on 44, and a
negative value on 66; the remaining 17 use `6..16`.

## Response exits, contact stages, and downed handoff

Live overlay `0x0071F160` (preserved export `FUN_0071f120` at
`0x0071F120`) produces the common phase/event-completion signal. The resident
per-frame dispatcher passes that signal to `FUN_00233870`. The following
transitions are direct static facts:

| Current ordinary substate | Completion/contact behavior |
| --- | --- |
| `0x27..0x2E` | Completion enters neutral `(0,0)`. |
| `0x2F..0x31` | Completion enters `(4,0x26)` if grounded, otherwise `(3,0x1E)`. |
| `0x32..0x35` | Completion enters `(4,0x26)` if grounded, otherwise `(3,0x25)`. |
| `0x36..0x39` | Completion calls the timed-down handoff with scale `1.0`. |
| `0x3A..0x3B` | Completion calls the same handoff with scale `1.0 - 0.25 * fighter[+0xB6E]`. |
| `0x3C..0x41` | Completion calls the timed-down handoff; grounded/contact conditions can first redirect to `0x42..0x47`. |
| `0x42..0x49` | Completion calls the timed-down handoff. |
| `0x4A..0x4E` | Their held descriptors call the separate `FUN_002316d0` handoff every update; its exact paired-fighter matrix is below. |
| `0x4F` | Uses the dual neutral-exit gates detailed below; animation completion alone is not always sufficient. |
| `0x50` | Enters neutral immediately when the paired fighter is not in major state `8`; while the pair remains in major `8`, it requires an external nonzero completion signal. |
| `0x51..0x58` | Completion calls the timed-down handoff. |
| `0x59` | Crossing primary-timeline event `1` calls the separate paired callback `FUN_00216d00(...,5)`; descriptor completion itself causes no transition in this switch. |
| `0x5A` | While grounded and below phase `2`, each dispatch forces phase `2`; completion calls the timed-down handoff. |
| `0x5B` | On completion, nonzero `+0xB10` on either paired fighter transfers this fighter to `(8,0x14)`; otherwise it enters neutral. While its own `+0xB10` is nonzero, it also runs a dedicated planar-motion continuation helper. |
| `0x5C` | On completion, the same paired `+0xB10` condition transfers to `(8,0x14)`; otherwise it enters neutral if grounded or `(3,0x1E)` if airborne. It uses the same continuation helper. |

For held `0x4A..0x4E`, `FUN_002316D0` first inspects the fighter at `+0x20`.
When there is no non-null major-state-`8` current action record, paired recovery
`(6,0x61/0x62)` transfers this fighter to `(6,0x61)`; every other paired state
enters `(2,0x1D)`. Before the latter entry, the routine restores the saved
response position at `+0xAE0..+0xAEC` when the paired action pointer is null,
or its `+0x10 & 0x00000F00` mask is zero, or its
`+0x14 & 0x04000000` flag is zero. It then refreshes facing/position state. No
player-facing name is assigned to `(2,0x1D)`.

When the paired fighter is in major state `8` with a non-null current action
record, these are the complete remaining branches:

| Paired action/event condition | Held fighter result |
| --- | --- |
| action `+0x14 & 0x04000000` nonzero | no transition |
| that flag clear, action `+0x10 & 0x00000100` nonzero, and current event-record bit `0x2` clear | neutral `(0,0)` |
| same action bit set and event-record bit `0x2` set | no transition |
| action bits `0x100` and `0x200` both clear | neutral `(0,0)` |
| action bit `0x100` clear, bit `0x200` set, and current event-record bit `0x8` set | re-enter `FUN_00232B80` with that paired action, allowing another ordinary response to be selected |
| preceding action-bit form but event-record bit `0x8` clear | no transition |

Thus the condition-`0` descriptor is an externally held response synchronized
to paired-fighter state, not indefinite hitstun or an autonomous timer.

Response `0x4F` has a separate paired-rate sequence. At primary event `0`,
`FUN_00231A40` clears private stage/counter `+0x960/+0x962`. On that same
driver invocation, stage `0` writes `0.1` to both paired fighters' `+0x1B0`,
runs a separate paired effect, and enters stage `1`. Stage `1` advances to
stage `2` when the pre-increment counter is greater than `4`, which takes six
driver invocations from counter zero. Stage `2` likewise takes six invocations,
approaches both `+0x1B0` values toward `1.0` on each call, and finally enters
stage `3`, explicitly restoring both values to `1.0`. Counting the initial
stage-`0` call, stage `3` is reached on the thirteenth unpaused
`FUN_00231A40` invocation.

The exit dispatcher sends `0x4F` to neutral under either exact condition:

```text
paired fighter is major 8, has a non-null current action record,
and action[+0x10] & 0x00F00000 is nonzero

or

the 0x4F animation descriptor is complete and fighter[+0x960] == 3
```

The first branch also clears the complete `+0x248` action-lock block. The
second proves why descriptor completion can remain latched for additional
updates until the paired-rate sequence finishes. The native identifier
`ACT_DMG_GBR` is not expanded into a speculative gameplay label.

Response `0x50` is another externally held row. Its descriptor is `H, T`, so
the common updater cannot complete it. The ordinary exit switch converts a
zero completion signal to nonzero whenever the paired fighter is not in major
state `8`, then enters neutral. If the pair remains in major `8`, `0x50` stays
held until another path supplies a nonzero completion signal. This is paired
state synchronization, not a fixed counter.

Before that per-state switch, `FUN_002310F0` can replace a live launch response
with `0x48` or `0x49`. Fighter byte `+0x63` bit `6` proposes `0x48` from
`0x3C`, `0x3D`, or `0x41`, and from `0x3E` while phase is below `2`; the
grounded bit proposes `0x49` from `0x40/0x41`. The replacement additionally
requires a retained attack record, saved motion scale `+0x9A4 > 0.5`, external
mode zero, and the exact attack-flag gate
`(+0x14 & 0x00080000) == 0`, plus either cursor below the path's ceiling or
`(+0x14 & 0x00100000) != 0`. A nonzero `+0xB00` also requires that latter
attack flag. The cursor ceiling is `5` except that the `0x3E` proposal has no
practical ceiling. These are raw prerequisites, not named collision classes.

If that pre-switch replacement does not occur, the staged transitions are:

| Current | Non-completion transition |
| --- | --- |
| `0x3C` | Airborne plus fighter byte `+0x63` bit `6` set enters `0x42`. |
| `0x3D` | The same condition enters `0x43`. |
| `0x3E` | Fighter byte `+0x63` bit `6` set enters `0x43`, without the additional airborne test. |
| `0x3F` | Fighter byte `+0x64` bit `0` set enters `0x44`. |
| `0x40` | On becoming grounded, enters `0x46` when primary cursor is below `4` and external mode is zero; otherwise enters `0x45`, clears the grounded bit, and writes vertical speed as `-0.5 * +0x9B0` using the saved pre-contact component. |
| `0x41` | On becoming grounded, enters `0x47` and clears the grounded bit. |

This proves staged launch/contact reactions and explains why `0x42..0x49`
are not direct attack-byte selections. It does not prove the visual meaning of
fighter byte `+0x63` bit `6`, byte `+0x64` bit `0`, or each stage, so their raw
forms remain canonical.

The top-level `FUN_00233870` gate separately bypasses all of its ordinary
response handling for an initial substate in `0x3C..0x41` whenever
`fighter[+0xB00] & 0x1500` is nonzero. This is a whole-dispatch suppression for
that update, not merely an input-recovery restriction.

After the state switch and later input-recovery test, the dispatcher has one
more raw fallback. It skips the check only when the fighter is currently
`(5,0x45)` or `(5,0x5A)`. Otherwise it forces `(5,0x5A)` with transition
argument `1` when all of the following are true:

```text
fighter[+0xBA4] is the exact sentinel -17320.508
    or fighter[+0xBA4] >= fighter[+0xE4] * fighter[+0x2F0]
not ((fighter[+0x68] == 0x40 or 0x3B) and fighter byte +0x63 bit 5 is set)
fighter signed halfword +0xB8C is in 0x1E..0x22 inclusive
```

Because the major/substate exclusion is read after the switch, the code does
not require the fighter still to be in major state `5`; the fallback can
replace a transition just taken earlier in the same dispatch. `+0xB8C` is the
selector maintained by `FUN_00218190`, but the static trace does not justify
names for its values or for the `+0xBA4` boundary, so this is recorded as an
environment-dependent response fallback rather than a named collision event.

### Input-driven recovery actions during ordinary response

The same ordinary-response dispatcher has two binding-2 recovery paths before
the timed-down handoff. Both consume logical input bit `0x00010000`, already
established as newly pressed binding 2 (default Cross), but they have different
windows and native destinations.

The earlier path is available in substates
`0x36..0x39`, `0x3C/0x3D`, `0x3F..0x41`, and `0x48/0x49`. It requires primary
cursor `+0x1C4 >= 2`, position component `+0x38 > -500.0`, a retained attack
pointer other than the dummy-drop record when that pointer is non-null,
`FUN_00306A60(fighter) != 1`, the fighter's grounded bit clear, and contact
history count `+0xB9A == 1`. For the eligible `0x3C/0x3D` and `0x3F..0x41`
states, the top-level fighter `(+0xB00 & 0x1500)` must also be zero. When input
is present, the dispatcher calls `FUN_0022AF10(1.0,1.0,fighter,1)`, which forces
`(0,0x0A)`, clears the action-lock block, and clears the secondary block when
its pending flag is clear. The clean descriptor names this state `ACT_RCV_1`.

The later path can run only if the earlier path did not return and the fighter
is still in ordinary major state `5`. Its shared gates are:

```text
substate is 0x38/0x39, 0x3C/0x3D, 0x3F, or 0x48/0x49
external mode == 0
fighter[+0x20C] < 1
fighter[+0xB00] == 0
FUN_00306A60(fighter) != 1
retained source +0x7C8 and attack record +0x7CC are both non-null
input +0x338 has 0x00010000
FUN_00217260(fighter,0x00010000,5,0) == 0
```

It then requires the primary cursor to lie inside one of these inclusive
windows:

| Current substate | Additional raw conditions | Inclusive `+0x1C4` window |
| --- | --- | --- |
| `0x38/0x39`, `0x48/0x49` | none | `4..6` |
| `0x3C/0x3D` | unless source `+0x0C == 0` and attack `+0x10 & 0x200` is set | `4..8` |
| `0x3C/0x3D` | source `+0x0C == 0` and attack `+0x10 & 0x200` set; random `r` in `0..3` | `r+4 .. r+6` |
| `0x3F` | source `+0x0C == 0`, attack `+0x14 & 0x2` set, and vertical speed `+0x998 >= 0`; random `r` in `0..2` | `r+3 .. r+5` |

A successful later path forces `(0,0x09)` and clears the complete action-lock
block. Its clean native identifier is `ACT_RCV_0`. Descriptor `ACT_RCV_0` has
sequence `D, T`; on completion it enters `(4,0x26)` if grounded and
`(3,0x24)` otherwise. `ACT_RCV_1` has sequence `E, E, G, E, T`, with a
`2.0` secondary rate in phase `0` and `1.0` thereafter; on completion it
enters neutral if grounded and `(3,0x1E)` otherwise. While airborne with
`+0xB00 == 0`, `ACT_RCV_1` can also enter `(3,0x1E)` as soon as vertical speed
becomes negative. These are exact native recovery transitions, but the static
evidence does not establish their player-facing move names.

## Timed downed recovery and get-up choices

`FUN_00235510(scale,fighter)` is the common handoff from the response groups
above. It enters `(6,0x5D)`. When fighter byte `+0x61` bit `3` is set, it also
initializes two action-timeline thresholds:

| Profile condition | Automatic threshold `+0xB66` | Earliest input threshold `+0xB68` |
| --- | ---: | ---: |
| fighter byte `+0x62` bit `5` clear | `45` | `8` |
| fighter byte `+0x62` bit `5` set | `90` | `40` |

Both values are multiplied by the handoff scale and then by the temporary
factor returned by `FUN_00306d30` when that factor is below `1.0`. The units are
the same primary action-timeline cursor at `+0x1C4`. Each multiplication is
followed by EE `cvt.w.s` under the active FPU rounding mode and a signed-halfword
store; when the temporary factor applies, that is a second multiply, conversion,
and store. This local path does not set the rounding mode, so static evidence
does not justify describing fractional results as unconditional truncation
toward zero.

The temporary factor cannot apply on the resident path. `FUN_00306D30` adds
the `+0x7C - 1.0` contributions of the fighter's active effect list at
`+0x8C8` (count `+0x8C4`), caps the sum at `1.25`, and then forces exactly
`1.0` whenever the fighter is in major state `5` or `6` (and in some other
conditions). All resident calls to `FUN_00235510` are in the ordinary-response
dispatcher `FUN_00233870`, before the handoff itself enters major `6`, so the
factor is `1.0` there. Five overlay sites also call the handoff (preserved
`0x0078AE58`, `0x007C2D2C`, `0x007C4730`, `0x007CDA7C`, `0x007D4EAC`; live
addresses are `+0x40`); their state context was not traced.

The same neutralization makes `+0x1AC` exactly `1.0` in every update whose
maintenance pass starts in major `5` or `6`, unless fighter `+0x1B0` or `+0x1B4` differs from `1.0`
(`FUN_0024C440` uses `+0x1B0` when it is not `1.0`, otherwise the factor, and
then multiplies by `+0x1B4` when that is not `1.0`). The state setter zeros the
cursor on entry and the same update's timeline pass advances it, so the
threshold tests in update `k` after entry see cursor `k`. At nominal speed
and rate `1.0`, the default profile therefore auto-recovers in update `45`
(1.5 s at 30 Hz) and accepts recovery input from update `9` (the test is a
strict `>`), and the `+0x62` bit-`5` profile uses updates `90` (3.0 s) and
`41`. The `0x3A/0x3B` scale shortens both proportionally.

If fighter byte `+0x61` bit `3` is clear, `FUN_00235690` returns immediately
from its `0x5D` case. It neither initializes nor consumes the two thresholds on
this path, so no automatic or input-driven `0x5D` exit is proven there. With
the bit set but the fighter airborne, `(fighter[+0xBB8] & 0x00F0F0F0)` values
`0x202020` and `0xE0E000` hold `0x5D`; other values divert back to ordinary
response `(5,0x5A)`. The static evidence does not justify a gameplay name for
that environment-class field. An external global value of `3` separately
forces the automatic `0x5E` branch without waiting for `+0xB66`.

While `(6,0x5D)` is active and the timed branch is enabled,
`FUN_00235690` performs these exact choices:

```text
+0x1C4 >= +0xB66                         -> (6,0x5E)
+0x1C4 >  +0xB68 and input 0x00010000    -> (6,0x5F)
+0x1C4 >  +0xB68 and input 0x00001000    -> (6,0x60)
```

The two input tests are sequential, not mutually exclusive: if both bits are
present in the same update, the later `0x00001000` test changes the final state
to `0x60`. More precisely, the automatic test and binding-2 test form an
`if/else if`, while the binding-1 test is a separate final `if`. Binding 1 can
therefore also replace an automatic `0x5E` selection made earlier in that same
update whenever its own threshold and input condition hold.

At the first primary-timeline event of `0x5D`, `FUN_00235B70` primes secondary
count `+0x230` to `1` only if that countdown channel is inactive, and
unconditionally clears the complete `+0x248` action-lock block, including
`+0x254`. `0x5D` nevertheless remains ineligible for action entry and exits
only through the state-specific branches above. This is direct evidence that
the downed lockout is not an extension of the ordinary `+0x254` lock timer.

On completion, `0x5E` and `0x60` enter neutral `(0,0)`, while `0x5F` enters
`(3,0x20)`. The code therefore proves one automatic recovery and two
input-selected recoveries, one of which continues through a different major
state. The battle input translator independently establishes that
`0x00010000` is newly pressed binding 2 (default Cross) and `0x00001000` is
newly pressed binding 1 (default Circle), then the resident bridge copies those
logical bits directly to fighter `+0x338`. These are default bindings rather
than hard-wired physical-button requirements. Animation names remain unassigned.

Their entry motion also differs. At its initial timeline event, automatic
branch `0x5E` zeros planar response speed and computes a vertical impulse from
native motion scalar `+0xF8` and constant `125`. Binding-2 branch `0x5F` sets
planar speed to `20` and computes the same form with constant `250`.
Binding-1 branch `0x60` sets facing/orientation fields but no corresponding
explicit response-speed impulse in this updater. These are native numeric
effects, not inferred animation labels.

The normal input update also exposes a separate recovery cancel before the
per-action recovery dispatcher runs. `FUN_0022B630` accepts logical input bit
`0x00040000` throughout `0x5E` and `0x60`, and during `0x5F` while primary
cursor `+0x1C4 < 3`. It additionally requires all of these raw gates:

```text
fighter[+0x9F6] == fighter[+0x324]
fighter[+0x9F0] == 0
FUN_0022D5B0() == 0
fighter[+0xB00] == 0
```

When the gates and input bit hold, its sole caller invokes `FUN_0022BA30`,
which forces recovery major state `6` to `(0,0x0B)`. The clean descriptor names
that destination `ACT_BST_0`. The battle input translator derives
`0x00040000` from binding-2 input plus directional/condition tests, so no single
physical-button name is assigned here. This cancel does not include `0x5D` and
is distinct from the three threshold choices and normal completion exits.

Substates `0x61/0x62` are a separate recovery/placement route used by the
special `0x4A..0x4E` handoff. In `0x61`, a nonzero external mode or primary
cursor `+0x1C4 > 0x13` triggers the next branch: fighter byte `+0x61` bit `3`
set enters `0x62`, while that bit clear routes back through an ordinary
dummy-record response instead. In `0x62`, the resident updater performs its
placement event at cursor `0x1E`. It may return to neutral only after
`+0x1C4 > 0x1E` and when at least one of fighter halfwords `+0x308` or
`+0x318` is zero. These substates must not be folded into the timed `0x5D`
profile.

## Guarded-hit transitions

The normal fighter input path passes `+0x338` to `FUN_00228320`. When guard
input `0x10000000` is held and the fighter passes its state/lock predicates,
that routine enters guard stance `(0,5)` and increments `+0x95A` up to
`0x7FFF`; release or ineligibility clears `+0x95A`. This establishes the
temporal state consumed by the hit router without treating it as a resource.

The two temporal fields have distinct update rules. When nonnegative,
`+0x95C` increments once per guard-held input update and resets to zero on
release; a negative value instead increments toward zero regardless of current
guard input. Eligible guard-held updates likewise increment `+0x95A`, but with
explicit saturation at `0x7FFF`; release clears it. Ineligibility clears
`+0x95A`, except that the `(0,6)` and `(0,7)` guarded-reaction states bypass
this input-side mutation while active. Thus `+0x95A >= 1` is proven guard
temporal state, while `+0x95C` is a separate guard-input age/window value.

`FUN_00228760` reads signed attack-record byte `+0x2D`, remaps values `0..4`
to `5..9` when the defender is airborne (grounded bit clear), and stores the
result at fighter `+0x95E`. A grounded defender keeps the authored index.
It then chooses:

- grounded reactions with adjusted indices `5..9`: `(0,7)`;
- other grounded adjusted indices: `(0,6)`; and
- non-grounded reactions: `(0,7)`.

Both reactions are forced state changes. Their per-update descriptors are the
`0x1C`-byte table at resident runtime `0x00407550`, ELF file offset
`0x00307650`, indexed by `+0x95E`. The action updater routes both `(0,6)` and
`(0,7)` through the same table engine used by ordinary response motion.

The same native descriptor table used by ordinary responses names guard stance
`(0,5)` as `ACT_GDN_0`, grounded guarded reaction `(0,6)` as `ACT_GDN_1`, and
the `(0,7)` reaction as `ACT_GDA_1`. Each descriptor begins with an
animation-end (`-0x10`) phase and then a condition-`0` phase. The common phase
updater therefore advances into, but cannot leave, that held second phase;
`FUN_00228E90` owns the exits described below. The identifiers are recorded
verbatim and are not expanded into unverified terms.

Decoded as in
[Animations and animation-gated phase lengths](#animations-and-animation-gated-phase-lengths),
the phases animate per-character `nxg0` then held `gdn0` for `(0,5)`,
`ght0` (7..11 frames, median 7) then held `gdn0` for `(0,6)`, and `gha0`
(6..9 frames, median 7) then held `dow0` for `(0,7)`. The first phase's clean
rates (`256` and `192`) are replaced at run time by the guarded-row rate
described below.

The exact clean table rows are:

| Index | Planar `+0x04` | Vertical `+0x08` | Damping `+0x0C` | Pause `+0x14` | Secondary `+0x16` | Action lock `+0x18` | Phase rate `+0x1A` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `30` | `0` | `0.35` | `1` | `2` | `8` | `176` |
| `1` | `30` | `0` | `0.35` | `1` | `2` | `8` | `160` |
| `2` | `35` | `0` | `0.35` | `1` | `2` | `8` | `144` |
| `3` | `40` | `0` | `0.35` | `1` | `3` | `12` | `128` |
| `4` | `40` | `0` | `0.125` | `0` | `3` | `24` | `128` |
| `5` | `20` | `15` | `0.25` | `1` | `2` | `8` | `192` |
| `6` | `25` | `20` | `0.25` | `1` | `2` | `8` | `176` |
| `7` | `30` | `20` | `0.25` | `1` | `2` | `8` | `160` |
| `8` | `40` | `20` | `0.35` | `1` | `2` | `12` | `128` |
| `9` | `40` | `30` | `0.125` | `1` | `2` | `24` | `64` |

Every row also has flags `0x0101`, event gate `0`, and auxiliary multiplier
`1.0`. Guarded-hit initialization sends `+0x16` to secondary count `+0x230`
unless attack `+0x32` already staged a value there (see
[Accepted-hit rejection countdown](#accepted-hit-rejection-countdown)), and
raises action lock `+0x254` to at least `+0x18`. Field `+0x1A` is written
into halfword `+0x06` of the current phase record, the rate field that
[phase control](#descriptor-phase-control) loads into `+0xB90`. The authored
values `64..192` therefore set the guarded reaction's animation and secondary
timeline rate to `0.25..0.75`, decreasing with the row index within the
grounded rows `0..4` and the airborne rows `5..9`. The write modifies the
shared overlay descriptor data rather than a per-fighter field.

The positive `+0x16` values are staged as negative pending counts and become
positive on countdown maintenance. The positive `+0x18` action lock is written
directly without a pending activation. Maintenance can activate the secondary
count while a pause is active, but it does not decrement `+0x254` until
`+0x20C` has cleared.

Guard field `+0x14` is specifically an attack-pause fallback. The initializer
first processes signed attack halfword `+0x30` in guard mode. Finite nonzero
values provide their absolute count, but retain a sign-dependent activation
edge: authored positive `N` is written immediately as positive `N`, while
authored negative `-N` is staged as negative `-N` with pending flag `0x0004`.
Thus the positive-authored form is eligible to decrement on the first following
maintenance pass, whereas the negative-authored form activates without a
decrement on that pass. Zero explicitly clears the pause block. Only sentinel
`0x7FFF` reports the attack pause as unhandled and causes the selected guard
row's `+0x14` to initialize `+0x20C`; a positive fallback value is also written
directly without the pending flag. Attack flag
`+0x14 & 0x00020000` instead reports the pause as handled without changing the
block, so it also suppresses the table fallback. This arbitration prevents the
guard table's Pause column from being misread as an unconditional duration.

`FUN_00228e90` owns the return from guard stance and guarded response:

| `+0x254` | Guard input `0x10000000` | Grounded | Next state |
| ---: | --- | --- | --- |
| `0` | released | yes | neutral `(0,0)` |
| `0` | released | no | `(3,0x21)` |
| `0` | held | yes | guard stance `(0,5)` and phase `1` |
| `0` | held | no | `(3,0x21)` |
| nonzero | either | yes | guarded response `(0,6)` and phase/cursor `1` |
| nonzero | either | no | guarded response `(0,7)` and phase/cursor `1` |

The state updater reaches that exit matrix through different gates:

- guard stance `(0,5)` calls it when guard temporal state `+0x95A` reaches
  zero;
- guarded response `(0,7)` calls it directly while grounded; and
- guarded response `(0,6)` calls it at phase `1` after the secondary action
  timeline at `+0x1E8` is positive and the `+0x254` countdown block crosses
  zero, or under the same phase/timeline condition if the fighter is airborne.

Those gates explain why a nonzero `+0x254` can re-enter the appropriate guarded
response with phase/cursor `1` rather than exit immediately.

The action-exit dispatcher sends guard stance `(0,5)` to cleanup
`FUN_00228130` and both guarded reactions to `FUN_00228550`. Thus guard
reaction is a short action-state lifecycle governed by the same general timer
channel, not merely a branch that leaves the fighter in guard stance.

## Conditional rehit suppression and target-eligibility limits

A direct trace into the accepted-hit router establishes two rehit gates: the
state-window predicate described here and the time-based
[`+0x230` countdown](#accepted-hit-rejection-countdown). Neither is a
hurtbox-level invulnerability or global untargetability timer.
`FUN_002409e0` calls `FUN_002406b0(fighter)`. It sets result bit `0x10` only
when that predicate returns zero. At the top of `FUN_002209a0`, an otherwise
accepted hit returns without entering a new response when either:

```text
(result & 0x0F) == 0, (result & 0x10) == 0, (result & 0x20) != 0
(result & 0x0F) != 0, (result & 0x10) == 0
```

Consequently, `FUN_002406b0 == 1` marks response windows that suppress most
ordinary rehits. Other attack/repeat-result bits can still let a hit proceed,
so this is a conditional accepted-hit gate, not proof of absolute invulnerability.
The predicate returns one in these exact state-dependent windows:

| Response window | Additional condition |
| --- | --- |
| substate `0x5D` | always |
| `0x40`, `0x41`, `0x45`, `0x46`, `0x47` | grounded and action cursor `+0x1C4 > 3` |
| `0x3A`, `0x3B` | secondary count `+0x230 <= 0` |
| `0x36..0x39`, `0x3C`, `0x3D`, `0x3F`, `0x42..0x44`, `0x52`, `0x54`, `0x56`, `0x58`, `0x5A` | grounded after the current action has included airborne motion: entered airborne (`+0xB9C & 0x0F == 2`), or entered grounded and later left ground (`+0xB9C & 0x0F == 1` and flag `0x20`) |
| `0x48`, `0x49` | the preceding ground-after-air condition with more than four consecutive grounded updates (`+0xB9A > 4`), or phase `+0x192 == 2` |
| `0x3E` | phase `+0x192 == 2` |

When `FUN_002406b0 == 1`, the router can proceed only if the result's low
nibble and bit `0x20` are both clear. The low nibble is clear only for a
non-null incoming attack record satisfying either of these raw flag forms:

```text
attack[+0x14] & 0x00200000
(attack[+0x14] & 0x00000011) == 0x00000011
    and (attack[+0x10] & 0x00F00000) == 0
```

Bit `0x20` remains clear only while fighter `+0xB6E < 3` and either the incoming
record differs from retained record `+0xE54`, or it is the same record and its
signed `+0x2E` equals the expected repeat count. That expected count is positive
`+0xE5C` (otherwise zero) when `+0xB00 == 0`, and `1` when `+0xB00 != 0`.
These conditions describe the bypass exactly without assigning speculative
names to the attack flags or `+0xB00`.

The clean primary tables show how rare the attack-side exception is. Only 13
records carry `+0x14 & 0x00200000`, and 152 satisfy the `0x11` form (150 of
them damaging); together 158 records (156 damaging, about 6% of 2,484) in 72
of the 74 tables. All other damaging records cannot bypass the protected
windows above. Related guard flags are also sparse: `+0x14 & 0x00800000`
occurs on 109 damaging records, while `+0x14 & 0x00400000` occurs on none.

The action-state setter writes the initial `+0xB9C` low nibble, while the main
movement update maintains `+0xB9A` and latches the two transition flags. The
contact-history interpretation above is therefore direct static behavior, not
an animation-name inference. Substate `0x5D` is notable because its
rehit-suppression predicate is unconditional throughout the traced timed-down
state, even though its recovery thresholds and input choices remain separate.

Four tempting resident predicate groups were checked and rejected as proof:

- `FUN_002167a0` returns false for all major state `6`, for ordinary substates
  `0x42..0x49`, and for several unrelated fighter flags. Its traced BTL callers
  use the result to choose or suppress a participant in an overlay-managed
  presentation/selection path; they do not establish an attack-acceptance
  gate.
- `FUN_002166a0` and `FUN_00216720` reject recovery substates `0x61/0x62` plus
  unrelated flags. A traced BTL caller uses that result in a visual-state path,
  again not enough to name combat invulnerability.
- `FUN_00230f20` and `FUN_00230ff0` classify broad sets of ordinary response
  substates for interaction and motion handling. Membership is not itself an
  untargetability window.
- `FUN_0022b630` explicitly recognizes recovery `0x5E/0x60` and early `0x5F`,
  but its only resident caller passes the mutable logical-input word and uses a
  nonzero result to enter `ACT_BST_0`. It establishes the recovery cancel above,
  not an accepted-hit or target-selection gate.

Accordingly, the confirmed target-eligibility claim remains bounded: the direct
accepted-hit path proves conditional suppression for the states above, while
the rejected predicates only show that some non-combat consumers also treat
downed/contact substates as ineligible. A runtime hit-attempt matrix would still
be required to confirm these gates in play and to distinguish hurtbox,
collision, and higher-level target-selection behavior frame by frame.

### Accepted-hit rejection countdown

Countdown `+0x230` is a second, time-based rehit gate. `FUN_002247A0` is
exactly `fighter[+0x230] > 0`, and `FUN_002209A0` returns without a response
in router mode `0` (the paired fighter as source), mode `2`, and mode `3`
whenever it is true. Mode `1` does not test it. The pair hit resolver
`FUN_0021ED70` and helpers `FUN_0021F610` and `FUN_00304070` also consult it;
their exact roles were not traced here. `FUN_00220690` uses it to withhold
the attacker's pause while the defender is protected.

The block is decremented at a fixed rate `1.0` only while `+0x20C < 1`, but a
pending value is activated even during a pause. Its writers on the hit path
are:

| Source | Value |
| --- | --- |
| attack `+0x32` through `FUN_00224870`, from both `FUN_00232B80` and guarded `FUN_00228760` | `0` clears (leaving the pending flag set); positive `M` is staged pending; negative `-M` is active immediately as `M`; sentinel `0x7FFF` leaves the block unchanged |
| ordinary event `0` in `FUN_002346B0`, only for attack `+0x32 == 0x7FFF` and no pending value | response row `+0x16`, rate-adjusted as above |
| guarded-response row `+0x16`, written by `FUN_00228B50` after the attack value and only when that left nothing pending | `2` or `3` |
| capped `0x3A/0x3B` repeat | `60`, subject to the conditions above |
| receiver that counters an Extra Hit | `60`, staged pending |
| downed `0x5D` first event | `1`, when the channel is inactive |
| generic setter `FUN_002247D0(fighter, v, force)` | count `-v`, pending when `v > 0`, skipped while a value is pending unless forced; the router uses it to clear the countdown when `FUN_002409E0` returns `0`, and the [Ultimate Jutsu](ultimate_jutsu.md) contest start sets both fighters to an active `60` |

With a positive attack pause `N`, a positive `+0x32 == M` activates in update
`1`, holds through the pause, and starts decrementing in update `N+2`, so
mode-`0` hits are discarded in updates `1..N+M` and accepted again from update
`N+M+1`. The row value used by the sentinel follows the same pattern from
update `0`.

The clean tables show how often each form is authored. Of 2,484 damaging
records, `+0x32` is sentinel `0x7FFF` on 1,462, `1` on 761, `2` on 173, `3`
on 33, `4` on 18, zero on 16, negative on 13, and `5..16` on 8. The sentinel
therefore uses the response row: `5` updates for most light and airborne
reactions and `120` for the knockdown and launch rows `0x36..0x39`,
`0x3C..0x47`, and `0x51..0x5A` (the complete row values are in the table
above). An Extra Hit clears the receiver's `+0x224` block when it starts the
exchange, which is consistent with launch rows otherwise refusing mode-`0`
rehits for their row count.

This is a rejection inside the accepted-hit router, not a hurtbox or
collision change; whether the collision owner still records contact during
the countdown belongs to [Collision](collision.md). No hurtbox-disable field
or global untargetability interval was established. `+0x254` is an
action-entry lock and guard-exit input, but it is not consulted by either
rehit gate. Guard substates `5..7` do not match any case in `FUN_002406B0`,
although guarded hits do set `+0x230`.

### Hit count

`FUN_00232B80` increments receiver halfword `+0x538`, saturating at `9999`,
and raises `+0x53A` to the new value when larger. It does so for every
ordinary accepted hit except when the source's `+0x0C` is `4`, the record is
`PL_ATK_DUMMYDROP`, attack `+0x10` bit `0x2` is set, or receiver byte `+0x62`
bit `0` is set. Guarded hits instead increment `+0x53C` (maximum `+0x53E`) in
`FUN_00228B50` under the same `+0x62` exception. A direct store
search of the resident ELF found no other halfword writer, so no in-match
reset was established. The only traced consumer is the condition evaluator
`FUN_00223450`, whose case `0x1B` reports `+0x538 < 1` as satisfied (when
fighter byte `+0x62` bit `0` is set) and any positive count as failed; case
`0x19` does the same for `+0x53C`. That evaluator's owning mode was not
traced.

## Confidence and remaining limits

- **High static confidence:** binary identities; resident/file mappings;
  overlay `+0x40` convention; action fields; ordinary-versus-guarded router;
  authored-byte mapping; response table layout and exact values; response
  transition groups; ordered pause/action-lock countdowns and the per-update
  order; downed thresholds and input masks; guard reaction and exit
  transitions; conditional rehit gate; `+0x230` router rejection; Extra Hit
  state writes and gates; authored record counts; animation frame counts and
  the phase-length formula; hit-response gravity.
- **Strong inference, explicitly bounded:** major `5` is the ordinary
  hit-response family; major `6`, substate `0x5D`, is a timed downed state; the
  two threshold-triggered paths are get-up/recovery choices; the Extra Hit
  exchange is the native air-chase continuation. The control flow and inputs
  establish these roles, but animations were not visually observed.
  Conversions to seconds assume the documented nominal 30 Hz fighter update
  and rate `1.0`; landing times assume flat ground.
- **Unresolved:** see the Research coverage list at the top.

The maintained disassembly was inspected read-only. No names or metadata were
written back to it, and no transient analysis artifact was retained.
