# Extra Hit

This document records the native Extra Hit exchange in retail NA2
(`SLPS-25837`): when a launched opponent can be chased, how the chase and
counter records are selected, the exchange roles both fighters carry at
`+0xB00`, the shrinking counter window, and teardown.

## Research coverage

- **Assigned scope:** Extra Hit eligibility, chase and counter-record
  selection, exchange-role state at fighter `+0xB00`, the counter window and
  exchange limit, teardown, and the authored records that drive them.
- **Exploration depth:** traced eligibility `FUN_00241A50` and its three kind
  tests, role writer `FUN_00241F10`, retarget helper `FUN_00242360`, receiver
  handler `FUN_002426C0`, candidate query `FUN_0023A0D0`, timing score
  `FUN_00239250`, teardown `FUN_00243EF0`, and the record-selection path
  `FUN_0023A390`, `FUN_00239530`, `FUN_00239B00` and `FUN_00240C40`. Pair
  resolver `FUN_0021ED70` was read only as far as its calls into this chain.
  The Extra Hit and counter records of all 74 primary action tables (3,428
  records) were read. Direct-offset store searches covered `+0xB00` and
  `+0xB0A`.
- **Confirmed coverage:** eligibility gates and their wait/reject results;
  the authored record layout and launch pairings; selector masks; the four
  role updates and the bits they preserve; the counter-window formula and its
  endpoints; receiver counter and missed-window handling; refusal of further
  counters at exchange count 15; initialization and teardown of the exchange
  fields.
- **Unresolved or untested:** any writer of attacker bits `8`/`0x20` beyond
  the inspected direct-store paths; geometry names for the environment fields
  `+0xBA0/+0xBA4/+0xBA8`; the player-facing meaning of the timing score;
  intermediate window values under the active rounding mode; visual labels;
  writes through adjusted-base aliases, bulk stores, or overlay writers.
- **Deliberate exclusions and overlap:** [Hit response](hit_response.md) owns
  the launch responses, the exchange velocity multiplier and response gating
  by exchange roles; [Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions)
  owns the common major-8 transition and exits;
  [Action commands](action_commands.md#selection-mode-and-eligibility-windows)
  owns how exchange roles select input modes;
  [Practice mode](../modes/practice_mode.md#linked-attack-and-extra-hit) owns the
  Practice counter options; [Target selection](target_selection.md#retained-source-writers-and-record-lookup)
  owns retained-source contracts.
- **Evidence limitations:** static control flow and clean authored values
  establish entry, eligibility, role and exit ordering; they do not establish
  visible timing or exhaustive character-specific behavior. The air-chase role
  below is an inference.

## Evidence and address conventions

Binary identities and address conventions are in
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
All addresses in this document are live resident addresses.

## Eligibility and action exit

`FUN_0023B280` calls `FUN_00241A50(fighter, candidate_index)` at `0x0023B5DC`
when the candidate attack record's `+0x10` flags contain `0x1000`. Eligibility
checks the two fighters' states, reaction timing, and geometry. It returns
`1` for acceptance, `0` while waiting, and `-1` for rejection.

The branch at `0x0023B5E8` sends result `1` to `0x0023B60C`, whose call block
starts the paired sequence through `FUN_00241F10` at `0x0023B630`. That helper
writes both fighters' `+0xB00` state, clears the opponent's `+0x224`
countdown block on a fresh exchange, and transitions the initiating fighter to
the candidate attack (details below). Results `0` and `-1` both continue at
`0x0023B6DC` into the common exit decisions owned by
[Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions).
Major-8 entry resets the pending candidate
([action entry](combat_action_execution.md#action-entry-and-state-ownership)),
so eligibility can be checked repeatedly between such entries.

### Eligibility conditions

`FUN_00241A50(fighter, candidate_index)` returns `-1` unless all of these hold
for the initiating fighter and its opponent at fighter `+0x20`:

- the initiator's `+0xB00` is zero and the opponent's byte `+0x61` bit `3` is
  set;
- the opponent is in ordinary response `0x3C`, `0x3D`, `0x3F`, `0x40`, or
  `0x41`;
- the global object at `gp-0x339C` has no active `+0x08 -> +0x14` value;
- the initiator is not in the `+0x68 == 0x40/0x3B` plus `+0x63` bit `5`
  exclusion also used by the ordinary-response fallback in
  [Hit response](hit_response.md#dispatch-precedence-at-contact); and
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
are the movement probes described in
[Movement and physics](../stages/movement_and_physics.md#floor-side-surfaces-and-limits);
their geometry names are not established.

### Authored Extra Hit records

A scan of all 74 primary action tables in the clean ELF (3,428 records;
table ownership as in
[Substitution](../characters/substitution.md#attack-record-ownership-and-clean-elf-inventory))
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
cases described under [Receiver response](#receiver-response-and-exchange-limit).
The selector is passed to `FUN_00239E50`, which still requires `+0x254 == 0`;
in major `5` only selector `2` passes (selector `3` is rejected there; other
admitted states ignore the selector). It is then passed to `FUN_00239530`,
which hands off to `FUN_00239B00`. That routine scans only action indices
`10..18` for a record whose signature matches the input, whose chakra cost
`+0x20` does not exceed fighter `+0x70` (unless `FUN_00307480` applies), and
whose type and kind match the masks from `FUN_00240C40`. A match becomes the
pending candidate `+0xA3E`. The complete selector-mode table and the
per-candidate mask builder are owned by
[Action commands](action_commands.md#fixed-chain-eligibility-masks).

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

## Exchange state at fighter `+0xB00`

`FUN_00241F10(initiator, candidate_index)` is the paired-state writer. Direct
resident xrefs identify two caller families: `FUN_0023B280` after eligibility
returns `1`, and `FUN_002426C0` after it finds a pending candidate. The branch
at `0x00241F40`, `bne v0,zero,0x002421EC`, tests the initiator's own
`+0xB00 & 0xFF`; when it is nonzero, all role changes are skipped and only
the common tail runs. Otherwise the initiator's current role selects one of
four exact updates. `P` is the opponent.

| Initiator `+0xB00` before | Initiator after | Opponent after | Retarget |
| --- | --- | --- | --- |
| high byte clear | sets bit `0x0001` | sets bit `0x0100`; its `+0x224` countdown block is cleared unless activation is pending | no |
| any of `0x0300` | sets bit `0x0004`, clears the high byte | clears the low byte, sets bit `0x0400` | yes |
| any of `0x0C00` | sets bit `0x0010`, clears the high byte | clears the low byte, sets bit `0x1000` | yes |
| any of `0x3000` | sets bit `0x0004`, clears the high byte | clears the low byte, sets bit `0x0400` | yes |

These updates retain bits outside their stated masks; they are not
whole-word assignments (instructions `0x00241F38..0x002421EC`). A nonzero
high byte outside these three groups supplies no new role.

Every update also writes the opponent's window
`+0xB0A = max(1, cvt(12.0 - 1.7142857 * P[+0xB08]))`, where `+0xB08` is the
exchange count read before this call's increment. The multiplier is IEEE-754
`0x3FDB6DB7` and the base `0x41400000`; the float result is converted by EE
`cvt.w.s` under the active rounding mode, narrowed to a signed halfword, and a
nonpositive result is replaced by 1 (first sequence `0x00241FB4..0x00242008`,
other stores at `0x002420A4`, `0x00242144` and `0x002421E4`). Only the exact
endpoints `12` (count `0`) and the floor `1` (count `7` or more) are stated
here. The retarget rows then make the initiator retain the opponent (`+0xE58`
and `+0xC74`), clear `+0xE54`, and adopt the opponent's attack record
(`+0xE50`, or `+0xA4C` when that record's `+0x10 & 0x000C0000` is clear) as
its own retained hit provenance with its `+0x2E` repeat count and `+0x28`
transient modifier.

The common tail calls `FUN_002260D0(...,0)` for each fighter whose float
`+0x7C` is nonzero, enters the candidate attack through
`FUN_0023A9A0(initiator,index,1)`, and on a retarget row calls
`FUN_00242360`. That helper selects the response the initiator would receive
from its retained record and, when the current attack record lacks
`+0x10 & 0x1000`, copies that response's second-phase animation slot and its
complete response-table motion row into the attack's `+0x50` sub-record.
Finally both `+0xB0C` values are cleared and both `+0xB08` counts increment;
these increments do not check the dispatch return value.

Thus the low byte of `+0xB00` is the attacking role (`1`, `4`, `0x10`) and the
high byte is the receiving role (`0x100`, `0x400`, `0x1000`). The next
section shows the receiver writing `0x200`, `0x800`, or `0x2000` and the
attacker `2` when a counter window is missed. Teardown also clears attacker
bits `8` and `0x20`, but no writer of those two bits was traced.

The missed-window path `FUN_002426C0` changes receiver `0x100` to `0x200`
and paired attacker `1` to `2`. For receiver `0x400` or `0x1000`, it changes
only the receiver to `0x800` or `0x2000`; attacker `4` and `0x10` remain
set. Its own attacking-role checks then return success for those bits. The
known missed-window chain therefore does not imply attacker transitions
`4 -> 8` or `0x10 -> 0x20`. Direct word/byte-store searches and the inspected
fighter-role handlers established no writer of `8/0x20`; offset matches in
several overlay auxiliary-object routines use a different object's field and
cannot be counted as fighter-role evidence. Indirect writes remain outside
that bounded search.

### Receiver response and exchange limit

The pair hit resolver `FUN_0021ED70`, its sole recovered direct caller, calls
`FUN_002426C0(fighter)` for each fighter whose `+0xE3C` hit bit `0x1` is set,
and clears that hit (and the opponent's matching `0x100` bit) when the helper
returns nonzero. A role bit alone therefore does not schedule this handler on
every update. The handler examines the receiving roles in priority order
`0x100`, `0x400`, `0x1000`:

- Receiving role `0x100` with a pending candidate `+0xA3E != -1`: the
  receiver stages its own `+0x230` countdown to `60` (pending), then calls
  `FUN_00241F10(receiver, candidate)`, becoming the attacker. The incoming
  hit is discarded.
- Receiving role `0x100` without a candidate: the receiver moves to `0x200`,
  the attacker from `1` to `2`, the receiver's `+0x224` block is cleared unless
  pending, and the hit proceeds. This branch has no exchange-count gate.
- Receiving roles `0x400` and `0x1000` behave the same way, except that the
  receiver also clears the attacker's `+0x224` block, and a receiver whose
  `+0xB08` is at least `15` has its pending candidate discarded first
  (`slti ...,0xF` with halfword stores at `0x00242814..0x0024282C` and
  `0x0024299C..0x002429B4`). Missed windows move to `0x800` and `0x2000`.
- A fighter holding attacking role `4` or `0x10` returns `1`, so hits against
  it are discarded while that role is active.

`FUN_0023A0D0` is the candidate query for a receiver. For the three receiving
roles and no current candidate, it calls
`FUN_00239250(attacker, receiver[+0xB0A])`. That routine accepts only while the
attacker's secondary cursor `+0x1E8` lies within the last `+0xB0A` animation
frames of the attacker's current attack phase (scaled by the phase rate and
the attacker's `+0x1AC`), returning a `0..1` timing score stored at `+0xB0C`.
Role `0x100` returns `2` and also clears its own action-lock block at
`+0x248`; `0x400` returns `3`; `0x1000` returns `2`. With a pending candidate
it skips the score call and leaves `+0xB0C` unchanged. The complete mode table
is owned by [Action commands](action_commands.md#selection-mode-and-eligibility-windows).
The Practice Extra Hit Counter options that consume these high-byte roles are
documented in [Practice mode](../modes/practice_mode.md#linked-attack-and-extra-hit).

### Initialization and teardown

Fighter initialization `FUN_00214A40` clears role word `+0xB00`, count
`+0xB08`, window `+0xB0A` and score `+0xB0C` (bytes `0x00215034..0x0021504C`).

`FUN_00243EF0` tears the exchange down. It returns when both role words are
zero. With a nonzero low byte in the fighter `F`, it removes `F`'s groups
`0x3/0xC/0x30` and the opponent's corresponding groups
`0x300/0xC00/0x3000`; with `F`'s low byte zero it clears both words entirely.
It resets both `+0xB08` counts and presentation fields, and restores both
`+0x1B0` rates to `1.0` when the fighter's `+0xB00` has become zero. It does
**not** clear `+0xB0A` or `+0xB0C`, so a retained window does not prove that
a role is still admitted. Its recovered direct callers are `FUN_00216A60`,
`FUN_00226F10`, `FUN_00235100`, `FUN_0023B280`, and `FUN_002424E0`; the last
is the low-byte exchange transition and admits cleanup on terminal phase,
specified recovery substates, or the other fighter entering major 6.

## Exchange fields

| Fighter offset | Type | Use |
| ---: | --- | --- |
| `+0xB00` | flags | Exchange roles: low byte attacking (`1`, `4`, `0x10`, and missed-window `2`), high byte receiving (`0x100`, `0x400`, `0x1000`, and missed-window `0x200`, `0x800`, `0x2000`). |
| `+0xB08`, `+0xB0A`, `+0xB0C` | `s16`, `s16`, `f32` | Exchange count, counter window, and counter timing score. |

## Routine map

| Preserved symbol | EE runtime | ELF file | Demonstrated role |
| --- | ---: | ---: | --- |
| `FUN_00241a50` | `0x00241A50` | `0x00141B50` | Extra Hit eligibility. |
| `FUN_00241f10` | `0x00241F10` | `0x00142010` | Exchange-role writer and attack entry. |
| `FUN_002426c0` | `0x002426C0` | `0x001427C0` | Receiver counter or missed-window handling. |
| `FUN_0023a0d0` | `0x0023A0D0` | `0x0013A1D0` | Counter-candidate query and selector mode. |
| `FUN_00239250` | `0x00239250` | `0x00139350` | Timing-window score against the opponent's current attack phase. |
| `FUN_00243ef0` | `0x00243EF0` | `0x00143FF0` | Exchange teardown. |
| `FUN_0023a390` | `0x0023A390` | `0x0013A490` | Input action selection; asks `FUN_0023A0D0` for a selector first. |
| `FUN_00239b00` | `0x00239B00` | `0x00139C00` | Scans action indices `10..18` for the pending Extra Hit or counter candidate. |
| `FUN_00240c40` | `0x00240C40` | `0x00140D40` | Supplies the type and kind masks for that scan. |

## Interpretation

**Inference:** because Extra Hit requires the opponent to be in a launch
response caused by the initiator's current attack and each authored Extra Hit
record selects another launch response, this exchange is the native
air-chase/juggle continuation. The counter window shrinks with every
exchange and further counters are refused from exchange count `15`. Visual
labels and the player-facing meaning of the timing score were not observed.
