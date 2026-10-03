# Substitution Knowledge

This document owns the substitution acceptance predicate, cost and
transition, input-history timing, sentinel exceptions, and character-specific
timing mutations in retail NA2 (`SLPS-25837`).

## Research coverage

- **Assigned scope:** native substitution cost, acceptance, input-history
  timing, guard-age sentinels, commit/exit behavior, and fighter reset.
- **Exploration depth:** complete control flow of `FUN_00229130`, its four
  direct resident callers, the five direct commit callers, the conditional
  debit, commit effects, and the seven-phase transition handler. A static
  census covered the action records of 74 primary and four auxiliary metadata
  owners (3,444 records). The six direct timing-writer records were followed
  through callback dispatch, counter producers, and reset/retention branches;
  the two BTL sentinel writers were resolved through the 43-entry AI state
  table. Coverage outside these paths and inventories is not a whole-program
  semantic census.
- **Confirmed coverage:** signed timing normalization, exact unsigned modulo
  probabilities, physical guard-history windows, ordinary eligibility gates,
  effect-9 and item-9 distinctions, AI sentinel states 20/39, guard-age
  maintenance and unsaturated wrap, independent resource validation/debit
  exemptions, route-dependent statistics, transition phases, repeated-hit and
  chain-counter ownership, Guy's retained timing, and static callback order.
- **Unresolved or untested:** gameplay roles and predicate reachability of the
  exceptional-timing records; observed distributions and correlations of
  negative timing; all indirect action-table reloads; roster-wide reachability
  of callback-mutated records; and whether a retail battle permits enough
  uninterrupted guard-age increments to reach signed wrap. The isolated
  sentinel's lifetime is stated in maintenance calls, without assigning a
  wall-clock cadence. Static transition/reset paths do not establish observed
  animation durations or a once-per-battle construction count.
- **Deliberate exclusions and overlap:**
  - Hit-response remapping, character response callbacks, and shared
    `+0xB60/+0xB64` state belong to [Hit response](../combat/hit_response.md).
  - Chakra and guard-stance internals belong to
    [Chakra and guard](../combat/chakra_and_guard.md).
  - Pad publication and the input-history ring belong to
    [Controller input](../../runtime/controller_input.md).
  - Character callback vectors outside the timing writers belong to
    [Character action callbacks](character_action_callbacks.md).
  - Combo counting belongs to [Combo accounting](../combat/combo_accounting.md).
  - AI state selection belongs to [Battle AI](../session/battle_ai.md); item production
    to [Battle item inventory](../projectiles_and_items/battle_item_inventory.md).
  - The support gauge and other HUD presentation belong to
    [Battle HUD](../session/battle_hud.md#support-gauge); the battle clock to
    [Match outcomes](../session/match_outcomes.md#timer-path); session construction to
    [Battle lifecycle](../session/battle_lifecycle.md).
- **Evidence limitations:** conclusions come from static analysis of the clean
  resident ELF and BTL, plus the one bounded Practice observation recorded in
  [Retail observation](#retail-observation). Table membership proves data
  ownership, not gameplay reachability.

## Stable references

- Target: retail NA2 (`SLPS-25837`), boot ELF `SLPS_258.37`.
- Clean source and address convention:
  [Retail game file identities](../../game/files/file_identities.md#address-conventions).
- Native substitution-cost site: ELF offset `0x1299BC`.

Function names below are Ghidra-generated labels in the preserved resident or
BTL analysis.

## Substitution-cost mechanism

At resident virtual address `0x002298BC` / ELF file offset `0x1299BC`,
`FUN_002297d0` contains `lui v0, 0x3F80`, represented by little-endian
instruction bytes `80 3F 02 3C`. The function moves the resulting float32
`1.0` to `f0`, subtracts it from the object's `+0x70` float field, and clamps
the result to zero.

The native subtraction and the predicate's separate minimum-resource comparison
both use `1.0`. Spending and acceptance are distinct decisions; their
conditional paths are described below.

Fighter `+0x6C` is normalized HP, `+0x70` chakra, and `+0x74` support fill.
These fields are distinct from the substitution phase and guard-age fields
described below. The battle clock provides no per-substitution cooldown; its
accumulator belongs to [Match outcomes](../session/match_outcomes.md#timer-path).

### Conditional native spending and commit effects

The subtraction is conditional. At `0x00229858..0x002298B4`,
`FUN_002297D0(fighter, route, charge)` bypasses resource arithmetic when
`charge == 0`, an active temporary-effect entry has behavior flag `0x80`,
fighter byte `+0x169` equals `1`, or fighter byte `+0x62` has bit `0x02` set.
The effect query is `FUN_003074F0`: it traverses the list at fighter `+0x8C8`,
bounded by `+0x8C4`, and requires entry `+0x6C != 0` and `+0x70 & 0x80`.
These are spending exemptions; they do not remove the predicate's independent
requirement of at least `1.0` resource for ordinary charged callers. The
generic chakra field and debit-inhibit gates are owned by
[Chakra and guard](../combat/chakra_and_guard.md).

When arithmetic runs, instructions `0x002298B8..0x002298EC` subtract
`1.0`, clamp negative resource to zero, and write `15.0` to fighter
`+0x1A0`. Charged entry also calls `FUN_00334E40` and the sound dispatcher
before checking the exemptions (`0x00229860..0x00229884`), so exempting the
debit does not skip those charged-entry calls. In contrast, `charge == 0`
skips the whole charged block.

Every commit stores the route at fighter `+0x964` and enters major/substate
`0/8` through `FUN_00217E40(fighter, 0, 8, 1)` at `0x00229AAC`. It clears
the action-lock countdown at `+0x248`; if the accepted-hit countdown at
`+0x224` has no pending bit `+0x226 & 4`, it stages `-20` in its integer
fields and `-20.0` in its float fields, then sets that pending bit
(`0x00229920..0x002299B0`). Activation of that staged countdown belongs to
the common fighter updater, as described in [Hit response](../combat/hit_response.md).
An existing pending countdown is preserved by this branch.

The statistics tail (`0x00229AB4..0x00229B40`) excludes routes with bit
`0x200` and routes whose low nibble is `2`. Other routes increment signed
halfword `+0x51C`, saturate it at `9999`, and update the high-water value at
`+0x51E`, provided fighter `+0x62` bit `0x01` is clear; they then call
`FUN_00223360(fighter, 1, 1)`. Thus effect-9 route `0x211` and item route
`2` omit this statistics/event tail, while ordinary routes `0x11`, `0x21`,
and `0x41` include it. Free spending and omission from this tail are separate
decisions.

### Native substitution transition and exit

`FUN_00249640` dispatches major/substate `0/8` to `FUN_00229B80`.
The handler's primary animation event `0` starts phase `1` at signed
halfword `+0x966` and clears phase counter `+0x968`
(`0x00229BA8..0x00229BC8`). Its subsequent phase dispatch has these
confirmed branches:

| Phase | Native transition |
| ---: | --- |
| `1` | Calls `FUN_00226B00`, selecting argument `1` for route low nibble `1` and `0` for nibble `2`; stages the accepted-hit countdown if needed, sets phase `2`, and initializes movement fields. |
| `2` | Adjusts movement toward zero/opponent values; advances to `3` when either fighter field `+0x308` or `+0x318` is zero, or when the previous phase counter is at least `5`. |
| `3` | Selects phase `6` when the opponent is in `0/10`, phase `4` when the opponent has byte `+0x63` bit `0x80`, otherwise phase `5`; it updates its own bit `0x80` and calls the associated movement/animation setup. |
| `4` | Advances to `7` when `+0x308` or `+0x318` is zero, or the previous phase counter is at least `9`. |
| `5` | Initially matches opponent movement fields; advances to `7` immediately with own bit `0x80`, otherwise on the same zero-field condition or previous phase counter at least `5`. |
| `6` | Tracks the opponent's movement/direction fields while the opponent remains in `0/10`; otherwise advances to `7`. |
| `7` | Clears the opponent's `+0xA3E` selection, own action-lock countdown fields, and own guard-active age `+0x95A`, then calls `FUN_00228E90`. |

These counters count handler calls; no wall-clock duration is inferred.
The phase-3 setup also chooses argument `6` rather than `4` for
`FUN_0021D0C0` when route bit `0x100` is set
(`0x0022A2F8..0x0022A328`); none of the five direct commit routes listed
below has that bit. This branch's existence does not establish another
retail route producer.

Instructions `0x0022A6EC..0x0022A72C` confirm phase-7 cleanup. Because the
cleared action-lock current value `+0x254` is zero, the exit helper uses
logical guard bit `0x10000000` and own byte `+0x63` bit `0x80`: with
bit `0x80`, it enters `0/5` when guard is held and `0/0` otherwise; without
that bit it enters `3/0x21` in either case
(`0x00228F88..0x00229038`). This exit clears `+0x95A`, not the separate
input-history age `+0x95C`.

For a newly initialized fighter, `FUN_00214A40` clears both guard ages,
route `+0x964`, phase `+0x966`, and phase counter `+0x968`
(`0x00214F78..0x00214F94`). This proves new-object initialization rather
than a once-per-battle call count. Battle construction and teardown are owned
by [Battle lifecycle](../session/battle_lifecycle.md).

## Acceptance predicate

`FUN_00229130` at boot-ELF virtual address `0x00229130` / file offset
`0x129230` is the substitution acceptance predicate. The boot ELF has exactly
four physical calls to it, at `0x0021F7D8`, `0x0021F81C`, `0x00220B28`, and
`0x00220CE4`. The nearby addresses `0x0021F7F4`, `0x0021F838`, `0x00220B44`,
and `0x00220D18` are the four resulting calls to `FUN_002297D0`, the
resource-decrement and substitution-transition function; they are not
predicate call sites.

| Caller/branch | Predicate arguments that vary | Commit after success |
| --- | --- | --- |
| `FUN_0021F610`, temporary-effect-9 attempt | selector `0` with response `6`, or selector `5` with `FUN_00231C60` response; resource validation `0` | `FUN_002297D0(fighter, 0x211, 0)` at `0x0021F7F4` |
| `FUN_0021F610`, ordinary/fallback attempt | same definition, selector, and response; resource validation `1` | `FUN_002297D0(fighter, 0x11, 1)` at `0x0021F838` |
| `FUN_002209A0`, dispatcher branch `param_2 == 2` | selector `5`; `FUN_00231C60` response; resource validation `1` | `FUN_002297D0(fighter, 0x41, 1)` at `0x00220B44` |
| `FUN_002209A0`, dispatcher branch `param_2 == 1` | selector `5`; `FUN_00231C60` response; resource validation `1` | `FUN_002297D0(fighter, 0x21, 1)` at `0x00220D18` |

Every one of those four commits requires a nonzero result from its immediately
preceding predicate call. `FUN_00236C70` has a separate fifth physical commit
call at `0x00236D74` for item/status ID `9`; as documented below, that path does
not call the predicate. The four clean predicate call sites pass selector `0`
or `5`; no direct caller passes selector `8`, which the predicate rejects. The
predicate is therefore the shared upstream acceptance gate for the ordinary
hit-dispatch routes, separate from the item commit.

### Input path and history

The BTL input translator `FUN_006efd80` builds a logical action mask at input
object `+0xAC`. `FUN_00217320` copies that mask to fighter `+0x338`, the analog
magnitude at input `+0xB0` to fighter `+0x33C`, and the directional value at
input `+0xB4` to fighter `+0x340`. The two configurable physical guard bindings
are input-map entries 6 and 7, stored at input object `+0x74` and `+0x76`.
Either binding sets logical action bit `0x10000000`. Pad publication and the
history ring's producer belong to
[Controller input](../../runtime/controller_input.md).

The input object also owns a circular history:

| Input-object field | Meaning |
| --- | --- |
| `+0x94` | pointer to `0x18`-byte input-history records |
| `+0x9C` | current record index |
| `+0xA0` | record count |

The resident code calls BTL accessor live address `0x006EF7F0` to resolve map
entries 6 and 7. The accessor reads the signed halfword at
`input + 0x68 + index * 2`, proving that these calls read exactly `+0x74` and
`+0x76`. It then calls the BTL history-search helper at live `0x006EFAC0`.
The clean BTL body reads the current index at `+0x9C`, applies the caller's zero
record skip, wraps through the count at `+0xA0`, and tests the requested number
of records while decrementing and wrapping after each test. Each substitution
call requests history word 1 at record `+0x04`, subset matching, no mask
filter, and the current record plus the normalized number of earlier records.
This proves that substitution consumes buffered physical guard input; it is
not based only on the current logical mask at fighter `+0x338`.

Fighter signed halfword `+0x95C` separately counts guard-held maintenance
calls. The ordinary timing path rejects a nonnegative count of 16 or greater.
Negative values take the sentinel path described below, including signed wrap
under the stated uninterrupted-update condition.

### Per-attack timing byte

The selected attack/hit definition's signed byte at `+0x1A` controls the input
window. `FUN_00229130` transforms it as follows before searching both guard
bindings:

| Effective `+0x1A` | Behavior |
| ---: | --- |
| `0` | current input-history record only |
| `1` | current record plus 1 earlier record |
| `2` | current record plus 2 earlier records |
| `3` | current record plus 3 earlier records |
| `4..127` | clamped to `3` |
| negative `-n` | first require one specific modulo result out of `2n + 1`, then search only the current record |

The negative branch uses `(fighter[+0x88] XOR 0x80000000) % (2n + 1)` and
accepts only remainder `2n`. `fighter[+0x88]` is not an opaque hit counter:
`FUN_0024c440` writes one raw 32-bit MT19937 result from `FUN_001801e0` there
once per fighter update, immediately before `FUN_00224970` and
`FUN_0021ba20` reach hit/substitution processing. `FUN_0024fd80` invokes that
update once for every linked fighter object. Multiple predicate calls during
the same fighter update therefore reuse the same word, including the two calls
made by `FUN_0021f610`; the predicate itself draws no new word. See
[Runtime randomness](../../runtime/randomness.md) for the generator evidence.

For a uniformly selected 32-bit word, the exact pass fraction for raw timing
`-n` is
`floor(2^32 / (2n + 1)) / 2^32`: `-1` is
`1431655765 / 4294967296`, `-2` is
`858993459 / 4294967296`, and `-3` is
`613566756 / 4294967296`. These are respectively just below the convenient
nominal values `1/3`, `1/5`, and `1/7`. The modulo gate is confirmed from clean
instructions `0x002295C8..0x00229604`; live attack trials can still be
correlated by fighter-update scheduling and by other consumers of the shared
MT stream, so an observed short run need not look independent.

Attack flags `0x000C0000` at definition `+0x10` are a special case: when the
timing byte is zero, the predicate changes it to `-1`, producing the same
modulo-three gate and a current-record-only input check. That conversion is at
`0x002295A4..0x002295C4`.

After normalizing the timing byte, the predicate rejects guard age at least
16 at `0x00229620`, then searches binding 6 at
`0x00229638..0x00229670` and binding 7 at
`0x00229678..0x002296AC`.

### Negative guard-age sentinel and temporary-effect ID 9

There is one confirmed route around the attack timing and input-history tests.
After the ordinary eligibility checks, a negative fighter `+0x95C` value jumps
directly to the predicate's final optional resource gate when the `+0xC74`
object's state is `0`. States `1` and `2` take the same shortcut only when the
fighter does **not** currently carry temporary-effect ID `9`. This shortcut
skips timing normalization, the MT modulo test, the 16-count held limit, and
both guard-history searches. It also branches before the ordinary
player-controlled-mode rejection, so a negative sentinel can admit a CPU-mode
fighter. It does not skip the earlier fighter-state, response, `+0xC74`, or
definition-flag checks, and a caller requesting normal validation still runs
the final resource/state checks.

`FUN_00307610` establishes effect ID `9` by walking the fighter's linked
temporary-effect list at `+0x8C8` for `+0x8C4` entries and comparing each
entry's `+0x68` word with `9`. At the start of `FUN_0024c440`, before the new
MT word and hit processing, `FUN_003059b0` calls that scan and writes `-2` to
fighter `+0x95C` through `FUN_00229b70` whenever effect `9` is present.

`FUN_0021f610` gives this effect a second special behavior. When effect `9` is
present, it first calls the predicate with resource validation disabled and,
on success, commits `FUN_002297d0(..., 0x211, 0)`, which does not deduct
substitution resource. Only if that attempt fails does it make the ordinary
resource-validating call. Consequently effect `9` can produce an automatic,
free substitution when the negative-sentinel shortcut is available, or a free
timing/input-gated substitution when it is not. The producer and player-facing
name are not generic attack metadata. The only direct temporary-effect-`9`
producer found in the clean boot ELF is Kurenai's awakened controller callback.

Kurenai metadata at runtime `0x0057FD20` stores `0x0057ACE0` at `+0x1C`. That
character-specific callback vector stores `FUN_002F2D70` at `+0x04`.
`FUN_002F2D70` itself rejects every live character ID except Kurenai `0x57`.
Outside its internal state-`6` exclusion, it watches fighter `+0x63` bit
`0x20`, which the awakening controller independently establishes as its
awakened marker. On a `0 -> 1` edge it calls
`FUN_00305C30(fighter, 9, 9999)`; on a `1 -> 0` edge it calls
`FUN_00305510(fighter, 9)`; and it records the last marker value at fighter
`+0x5626`. Thus the free/automatic route is a Kurenai-awakening exception. The
literal `9999` argument is proven, but its unit is not assigned here. The
callback does not distinguish Kurenai's associated effects `0x5B` and `0x5C`,
so this evidence does not justify attaching the exception to only one named
awakening variant.

Temporary-effect ID `9` and item/status ID `9` have separate producers and
consumers. Item handler `FUN_00236C70` receives a selected item/status
ID. Its ID-`9` branch, after its own state and current-definition
`+0x10:0x00000200` guard, calls `FUN_002297D0(fighter, 2, 0)` directly. It does
not call `FUN_00229130`, does not inspect attack `+0x1A`, does not search guard
history, and does not charge the normal resource. The surrounding
`FUN_002366F0` route requires the item-use logical action and an available item
from the item manager before making that call. This is a separate free
item/status substitution, outside the per-attack timing policy.

#### Guard-age maintenance and other sentinel sources

The sentinel is maintained in fighter updates, not by the predicate consuming
an input edge. `FUN_00228320` reads signed halfword `+0x95C` at
`0x00228350`. A negative value increments toward zero regardless of guard
input; a nonnegative value clears when logical guard `0x10000000` is absent
and increments when held (`0x00228350..0x00228384`). Thus one isolated
`-2` write supplies at most two maintenance calls with a negative value,
depending on where the subsequent predicate falls in the update order. Effect
9 refreshes `-2` in the active-fighter portion of `FUN_0024C440` before hit
processing; this differs from a one-time sentinel write.

During positive fighter hit-stop, `FUN_0024DA50` skips its ordinary
animation/action-callback branch but still translates and selects player
input, then performs the same signed guard-age update at
`0x0024DB30..0x0024DB64`. That alternative branch requires controller mode
`((fighter[+0x60] & 0x1FF) >> 5) == 0`. The full guard-stance state machine
and distinction between `+0x95A` and `+0x95C` belong to
[Chakra and guard](../combat/chakra_and_guard.md#guard-input-and-action-lifecycle).

Both held-input increments use `addiu` followed by `sh`, without saturation;
the separate guard-active age `+0x95A` does saturate. **Derived static
consequence:** starting at zero, 32,768 uninterrupted held-input maintenance
increments wrap `+0x95C` to `-32768`. A negative value then follows the
predicate's sentinel shortcut if its other gates pass, and moves toward zero
even after release. This is an arithmetic consequence under an uninterrupted
update sequence, not an observed player-facing exploit or a guarantee that
every battle state permits that sequence.

Clean `BTL.BIN` has two additional direct calls to `FUN_00229B70(fighter,
-2)`, at preserved/live/file
`0x006FBE40/0x006FBE80/0x00047F80` and
`0x006FC27C/0x006FC2BC/0x000483BC`. Both have call bytes `DC A6 08 0C` and
a preceding `addiu a1,zero,-2`; the target fighter is loaded from
`0x008D65AC + slot * 0x1E0`. These writers do not require the effect-9
scanner. The 43-entry direct-state table at live `0x008C3810`
(preserved `0x008C37D0`, file `0x0020F910`) resolves the first writer to
state `20` (`0x14`), whose entry is live `0x006FBD7C`, and the second
to state `39` (`0x27`), entry live `0x006FC2A8`. The first case reaches
its setter conditionally; the second directly writes the sentinel. These are
zero-based table indices, distinct from the setter-call addresses. State
selection and logical-input production belong to
[Battle AI](../session/battle_ai.md#direct-state-constructors). The setter census is also
recorded in
[Chakra and guard](../combat/chakra_and_guard.md#guarded-hit-selection-and-break-like-flags).

### Attack-record ownership and clean-ELF inventory

The timing byte is file-backed character action data, not a transient field
invented by the hit handler. `FUN_002151e0` initializes each fighter from its
character metadata as follows:

| Character metadata | Fighter field | Meaning |
| ---: | ---: | --- |
| `+0x28` | `+0xA38` | action-record count |
| `+0x2C` | `+0xA54`, `+0xA58`, initially `+0xA4C` | primary action-record base |
| `+0x30` when nonzero | same fields | optional replacement action-record base |

`FUN_00238a70` stores the selected signed action index at fighter `+0xA3C` and
computes `fighter[+0xA4C] = fighter[+0xA54] + index * 0x54`. Each action record
is therefore `0x54` bytes, and a selected definition can be mapped back to an
owner and index with `(definition - owner_base) / 0x54`. An incoming definition
at the defender's `+0xE50` or `+0xE54` normally maps against the attacker's
table, not the defender's. Record pointer `+0x08` names the record's retail
move-name string; the owner ID plus record index identifies a native record.

In the clean boot ELF, every one of the 74 primary-roster character metadata
records has a zero optional base at `+0x30` and uses the primary base at
`+0x2C`. The exact timing-byte virtual address for record index `i` is:

```text
character[+0x2C] + i * 0x54 + 0x1A
```

File offsets follow the
[address conventions](../../game/files/file_identities.md#address-conventions).

The 74 primary-roster tables contain 3,428 action records with these raw
timing values:

| Raw `+0x1A` | Record count | Predicate policy |
| ---: | ---: | --- |
| `-3` | 6 | nominal `1/7`, current record only |
| `-2` | 30 | nominal `1/5`, current record only |
| `-1` | 319 | nominal `1/3`, current record only |
| `0` | 2,794 | current record only, except the flag conversion below |
| `1` | 261 | current plus one earlier record |
| `2` | 18 | current plus two earlier records |

Exactly 148 of the raw-zero records have `+0x10 & 0x000C0000 != 0`, so their
effective timing is `-1`. The stock tables contain no raw timing `3` or value
above `3`. These are record counts, not a claim that every record is a distinct
reachable attack; dummies, transitions, and non-damaging actions share the same
table format.

In those primary tables, the separate predicate-level `+0x14` rejection flags
occur on 109 records:
91 contain `0x00008000`, and 18 contain both `0x00008000` and `0x02000000`;
no clean primary-table record contains only `0x02000000`. Eighty-four also
have exceptional timing: 83 resolve to effective `-1` and one to effective
`-3`. These 84 records demonstrate the distinction between timing and
eligibility: the predicate rejects their flags before reading `+0x1A`, so
their timing is not consulted in that state. Table membership still does not
prove that every internal record reaches the hit path.

Clean authored response byte `+0x2C` uses values `0x00..0x1E` plus `0xFF`;
none of the 74 primary tables uses authored `0x1F..0x27`. The response function
supports a broader domain because context, callbacks, and repeat-hit handling
can replace the authored result dynamically.

Four additional clean-ELF fighter-metadata blocks have the same count at
`+0x28`, action base at `+0x2C`, zero optional base at `+0x30`, and `0x54`-byte
record layout, but their IDs are outside the primary roster. Each owns four
records:

| Scope | Metadata | ID | Count | Action base |
| --- | ---: | ---: | ---: | ---: |
| auxiliary | `0x0059C7A0` | `0x1A` | 4 | `0x0059C630` |
| auxiliary | `0x0059CF80` | `0x1D` | 4 | `0x0059CE10` |
| auxiliary | `0x0059D750` | `0x1E` | 4 | `0x0059D5E0` |
| auxiliary | `0x0059DF20` | `0x1F` | 4 | `0x0059DDB0` |

These are evidence-backed auxiliary fighter IDs, not inferred player-facing
owner names. Records 1 and 3 of each have these fields:

| Auxiliary ID/index | Timing address | `+0x10` | `+0x14` block subset | Stock effective policy |
| --- | ---: | ---: | ---: | --- |
| `0x1A/1` | `0x0059C69E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1A/3` | `0x0059C746` | `0x00080000` | `0` | exact modulo-three gate |
| `0x1D/1` | `0x0059CE7E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1D/3` | `0x0059CF26` | `0x00080000` | `0` | exact modulo-three gate |
| `0x1E/1` | `0x0059D64E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1E/3` | `0x0059D6F6` | `0x00080000` | `0` | exact modulo-three gate |
| `0x1F/1` | `0x0059DE1E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1F/3` | `0x0059DEC6` | `0x00080000` | `0x00008000` | rejected before timing |

All eight have raw timing zero. Their `+0x10` conversion flags make the
effective timing `-1`; therefore the seven without a block bit use the exact
`1431655765 / 4294967296` current-record gate when all other eligibility
conditions pass. All eight use authored response selector `0x0F`, whose normal
grounded/other results `0x36/0x37` are both inside the predicate whitelist.
Record `0x1F/3` is different: `+0x14 & 0x00008000` rejects it before timing
is read. Reachability of each auxiliary record through a particular gameplay
setup remains a runtime question; the table ownership and fields are static
facts.

Including these four tables gives 78 metadata owners and 3,444 records. The
combined raw counts are `-3: 6`, `-2: 30`, `-1: 319`, `0: 2810`, `1: 261`,
and `2: 18`; the combined effective counts are `-3: 6`, `-2: 30`, `-1: 475`,
`0: 2654`, `1: 261`, and `2: 18`. The flag conversion affects 156 records.
There are 790 exceptional records. The block totals become 110 records, split
as 92 with `0x00008000` and 18 with `0x02008000`; 85 also have exceptional
timing.

#### Runtime-mutated action records

The clean tables are an initial/template inventory. Fighter initialization
relocates the selected action table, and `FUN_00217930(fighter, -3)` returns the
current live record. Six records have character-specific callbacks that
directly write that live record's timing byte. For the template-reading
branches, the source address is exactly
`fighter[+0xB8] + index * 0x54 + 0x1A`; other branches supply literal
alternatives independently of that template.

| Owner/index | Stock effective timing | Direct writer and possible live timing |
| --- | ---: | --- |
| Deidara `43` | `-3` | `FUN_002B5250`: template, `-1`, or `0` |
| Deidara `44` | `-3`, stock blocked | `FUN_002B5250` then `FUN_002B68F0`: template, retained, `-1`, `-2`, `0`, or `2` |
| Deidara `45` | `-3` | `FUN_002B5250`: template, `-1`, or `0` |
| Rock Lee `39` | `-3` | `FUN_002BDF80`: template or `0` |
| Might Guy `42` | `0` | `FUN_002C55B0`: retained at chain count `<=1`, then `1`, `2`, or `3` from fighter `+0x69B0` |
| Sasori (Hiruko) `30` | `-1` | `FUN_002D5320`: template plus `0`, `1`, or `2` from fighter `+0x4E3E` chain count |

`FUN_002B5250` also sets or clears predicate block bit `0x00008000` on all
three Deidara records. `FUN_002BDF80` does the same on Rock Lee record `39`.
Thus Deidara record `44`'s stock block can be cleared at runtime, while the
other three records can become blocked despite an unblocked clean template.
The nearby `0x00080000` mutations in hit callbacks are a different flag and do
not satisfy the predicate's block mask.

##### Callback ordering and counter ownership

`FUN_002151E0` copies character metadata `+0x1C` to fighter `+0xA8`.
For these six action indices, `FUN_00217670` resolves the ordinary
character callback vector: selector `1` uses vector `+0x00`, selector `2`
uses `+0x04`, and selector `3` uses `+0x08`. The alternative effect-associated
vector selection for major state `8` concerns action indices below `4`, not
these records. The other queried selector, `FUN_00307A50`, returns zero in
the clean resident program. The callback vectors' other entries belong to
[Character action callbacks](character_action_callbacks.md).

`FUN_0024FD80` updates all linked fighters through `FUN_0024C440`, then
performs selector-1 callbacks, builds collisions, and processes pairwise hit
responses. Later, when fighter hit-stop `+0x20C < 1`, it reaches input/action
processing and `FUN_00249640`; that function calls selectors `2` and `3`
at `0x00249658` and `0x00249668` before its major-state dispatch. Thus the
Deidara and Lee selector-3 timing writers run after hit processing in this
outer update. Guy and Hiruko's selector-2 resets precede their selector-3
chain increments. The response query `FUN_00231C60` separately invokes the
character vector's `+0x0C` callback during hit handling, allowing its timing
write to affect the subsequent substitution predicate. These are static call
orders, not measurements of wall-clock cadence.

| Character | Metadata callback vector | Selector-2 callback | Selector-3 callback | Hit-response callback |
| --- | ---: | --- | --- | --- |
| Deidara | `0x004FC750` | `FUN_002B4D60` | `FUN_002B5250` | `FUN_002B68F0` |
| Rock Lee | `0x0050DD40` | `FUN_002BDB50` | `FUN_002BDF80` | `FUN_002BF9A0` |
| Might Guy | `0x00519F50` | `FUN_002C4010` | `FUN_002C4710` | `FUN_002C55B0` |
| Sasori (Hiruko) | `0x0053BAF0` | `FUN_002D4AB0` | `FUN_002D4C10` | `FUN_002D5320` |

Deidara and Lee read signed halfword `+0xB64`, which is a response
repeated-hit counter, not an awakening tier. The constructor
`FUN_00214A40` initializes the associated record pointer `+0xB60` and count
to zero. In `FUN_00232B80`, the final repeated-hit branch requires an
incoming record with nonnull `+0x50` and neither `+0x10` flag mask
`0x01000000` nor `0x000C0000`. It compares that record's signed `+0x2E`
with an effective repeat value: `1` when receiver `+0xB00` is nonzero,
otherwise positive receiver `+0xE5C`, or zero when that count is nonpositive.
Instructions `0x00232F44/0x00232F50` read `+0xB00` and place `1` in
register `a0`; they do not write the field. When the values match, the branch
increments `+0xB64` when `+0xB60` is null or names the same incoming record,
then stores the record at `+0xB60`
(`0x00232F6C..0x00232F98`). Response-exit cleanup
`FUN_00230A70` clears both fields when entering a major state other than `5`.
Their wider response semantics belong to
[Hit response](../combat/hit_response.md#character-callbacks).

`FUN_002B5250` reads Deidara's own count. Below `2`, records `43..45`
use template timing and set block bit `0x8000` when action phase byte
`+0xA40 == 1`; otherwise they use `-1` and clear that block. At count
`>=2`, records `43` and `45` use `0` and clear the block; record `44`
clears the block but retains its timing byte. Lee's `FUN_002BDF80` uses
the same phase condition below count `2`, choosing template timing plus the
block or timing `0` without it; at count `>=2` it chooses `0` without
the block. Deidara's hit-response callback instead reads the **defender's**
`+0xB64`: record `44` becomes `-2` below `2`, `0` at `2`, and `2` at
`>=3`. Instructions `0x002B6B14..0x002B6B84` confirm these writes and
the separate `0x80000` flag update.

Guy's signed byte `+0x69B0` is initialized by `FUN_002C1BF0` and cleared
by `FUN_002C4010` when the opponent's action query returns `-1` and the
opponent's substate is zero (`0x002C445C`). `FUN_002C4710` increments it
on primary animation event `0` for action `42` (`0x002C4B50..0x002C4B58`)
and action `38` (`0x002C5334..0x002C533C`), and on secondary event `0`
in phase `1` for action `37` (`0x002C518C..0x002C5194`). The action-42
hit response writes timing `1` at count `2`, `2` at `3`, and `3` at
`>=4`. At count `<=1` it does **not** write timing
(`0x002C5940..0x002C59D8`). Generic action entry `FUN_00238A70` selects
the same live record and calls `FUN_002391B0`, which clears action phase
fields `+0xA40/+0xA42/+0xA43/+0xA44` rather than restoring record timing.
Consequently clearing this chain counter alone does not restore the clean
timing byte; this conclusion does not rule out a separate table reload.

Hiruko's signed halfword `+0x4E3E` is cleared by `FUN_002D4AB0` when
the opponent's major state is not `5` (`0x002D4B28`). `FUN_002D4C10`
increments it on primary animation event `0` for actions `30`
(`0x002D4F24..0x002D4F2C`) and `31` (`0x002D4FF8..0x002D5000`).
The action-30 hit response reads this own-fighter count, using template
timing below `2`, template plus `1` at `2`, and template plus `2` at
`>=3` (`0x002D5600`, `0x002D5658`, `0x002D56A8`). With the clean
template `-1`, these values are `-1`, `0`, and `1`.

The six records' live timing can differ from their clean templates. Their
`0x8000` eligibility mutations are separate from timing. The table counts
above describe the stored records and direct writer families, not all
possible indirect live mutations.

Kakashi (ID 70) is a concrete example. His metadata selects 48 records at
virtual base `0x00524BF0`. Records `0x01` and `0x03` contain raw zero with
`0x00040000` and `0x00080000` respectively and therefore become effective
`-1`. Records `0x17` and `0x18` contain raw `-1`. Records `0x23`, `0x2B`, and
`0x2C` contain `1`; all other records contain zero. Record `0x17`'s timing
byte is virtual `0x00525396`, ELF file offset `0x425496`. Its raw
`0xFF` is signed `-1`, so this record uses the modulo-three gate. Records
`0x01` and `0x03` have the same effective negative timing through flag
conversion despite their raw zero; positive timing values bypass that
zero-specific conversion.

### Other eligibility gates

The timing byte does not override the predicate's other eligibility gates.
The early gates are established by instructions `0x002291D4..0x00229250`:
byte `+0x61` bit `0x80`, nonzero response state `+0xB00`, linked
temporary-effect ID `0` or `1`, and already being in major/substate `0/8`
reject the attempt before timing or resource handling. `FUN_00306A60` checks
those two effect IDs in the bounded list; unlike the resource-flag queries, it
does not require entry `+0x6C != 0`.

The remaining gates reject:

- reaction selector `8` and reaction values outside its explicit whitelist;
- attack-definition `+0x14` flags `0x02000000` or `0x00008000`;
- unsupported state of the fighter object at `+0xC74`;
- non-player-controlled fighter modes identified from fighter `+0x60`, except
  the earlier negative-sentinel shortcut; and
- an active temporary-effect entry with behavior flag `0x40`, reported by
  `FUN_00307480`, or resource below `1.0` at fighter `+0x70`, when the
  caller requests normal resource validation.

These are eligibility controls, not attack-specific timing probabilities.
`FUN_00229130` compares chakra with its own `1.0` constant, independently of
the `1.0` subtraction in `FUN_002297D0`; the latter clamps the remaining
resource to zero. The effect-ID-9 route is separate from this ordinary
eligibility and spending pair. `FUN_00307480` scans the same bounded effect
list as the debit exemption query but tests flag `0x40` rather than `0x80`;
an entry is active only when its `+0x6C` is nonzero.

When no definition argument is supplied, instructions
`0x00229160..0x002291D0` first use fighter `+0xE54`, then query the
objects at `+0xE58` and `+0xC74` when their `+0x0C` states are nonzero,
and finally select resident `PL_ATK_DUMMY` at `0x00407C00` if no record
was recovered. A null `+0xC74` still fails its later state gate: the
fallback does not bypass that requirement. Nonzero controller mode
`((fighter[+0x60] & 0x1FF) >> 5)` clears a positive `+0x95C` to zero
at `0x002294EC..0x002294F8`, retaining zero and negative values; the negative
shortcut is checked before ordinary mode rejection.

When the resource amount is insufficient, the failed-validation branch calls
`FUN_0020CAA0` on the side's feedback object when present and dispatches the
sound referenced at resident `0x00406FE0` only while signed countdown
`+0x19C` is zero, then sets it to `15`
(`0x00229748..0x002297A8`). The active-effect-`0x40` rejection
occurs earlier and does not reach that shortage feedback. Both failures return
zero and leave the corresponding caller's commit unexecuted.

The response test can be stated exactly. The predicate rejects selector
argument `8`, then accepts only response values in this set:

```text
0x06, 0x07,
0x27..0x39,
0x3C..0x41,
0x48..0x59
```

`FUN_00231C60` normally derives that response from attack-record byte `+0x2C`
plus grounded/orientation/current-response context. The ordinary authored
families fall in accepted ranges, but failed contextual queries return
`0x3A/0x3B`, and callbacks or repeat-hit remapping can select other values.
Both `0x3A/0x3B` and `0x42..0x47` are outside the whitelist. See
[Hit response](../combat/hit_response.md) for the complete `+0x2C` mapping and dynamic
remaps.

## Timing arithmetic bounds

All signed negative timing bytes use the same unsigned modulo arithmetic.
For `-n`, `1 <= n <= 128`, the denominator is `2n + 1`, giving
nominal fractions from `1/3` to `1/257` and the exact floor formula
above. Positive values greater than `3` have the same four-record search
as `3`.

A nonnegative timing window still requires a guard edge in its searched
physical-history records, guard age below 16 on the ordinary
path, and every earlier eligibility/resource gate. Raw zero is not effective
zero when definition flags `0x000C0000` are present. The sentinel, Kurenai
effect, and direct item route have their own boundaries described above.

## Retail observation

A Practice observation selected Naruto action record `21` with P1 Circle
input. When the hit landed, P2 `+0xE54` changed to the relocated P1 record
`21`, whose clean timing is `-1`. P2 health changed from `1.0` to `0.98` and
then regenerated under Practice rules. This sample confirms the
incoming-definition owner/index calculation, in addition to the static pointer
arithmetic.

Slot-1 L2 input independently produced newly-pressed native mask
`0x00000001` in the Practice defender's input-history word 1 and the matching
released mask in word 2. The fighter's logical action and `+0x95C` nevertheless
remained zero because this Practice opponent had non-player mode value
`((fighter[+0x60] & 0x1FF) >> 5) == 1`; the suppression behavior matches the
static input and predicate gates. No runtime memory patch was used in that
sample. These observations do not establish roster-wide success rates.

## Remaining evidence limits

The acceptance predicate, direct callers, effect/item routes, two AI sentinel
states, six timing-writer records, and native transition are resolved within
the stated static scope. Negative-timing pass fractions describe arithmetic
over uniformly selected words, not measured battle success rates.

Static searches of direct stores cannot exclude indirect table replacement.
Guy's retained timing is established for the inspected writer, counter reset,
and generic action entry; it is not a claim that every form change preserves
the same table. The signed guard-age wrap likewise requires the stated
uninterrupted maintenance sequence. No current evidence establishes that
sequence as an observed retail event.
