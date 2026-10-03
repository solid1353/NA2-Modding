# Battle hit-response state

The native battle state after a hit has been accepted in retail NA2
(`SLPS-25837`): ordinary reactions, table-driven motion, launch and contact
branches, downed recovery, and guarded reactions. Names describe demonstrated
control flow, not the game's own terminology.

## Research coverage

Established: the ordinary/guarded routing and its rejection gates, response
selection with callbacks and remaps, descriptors, animations and phase lengths,
the motion table and modifiers, gravity, the update order behind elapsed
counts, contact and held handoffs, input recoveries, timed downed recovery,
guarded transitions, rehit suppression, and the rejection countdown. Animation
roles are inferences from control flow. Open: stage-dependent timing of
grounded phases, visual confirmation of animation roles and move names,
non-default bindings, reachability of every callback branch, and
recovery-source pointer aliases.

Routines, structures and data are named by the NA2 annotations in
`@annotations/NA2`; their comments carry the per-routine detail. Addresses are
live.

Related owners: [Collision](collision.md), [Damage](damage.md),
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md),
[Chakra and guard](chakra_and_guard.md), [Match outcomes](../session/match_outcomes.md),
[Battle statistics](../session/battle_statistics.md), [Practice mode](../modes/practice_mode.md),
[Extra Hit](extra_hit.md), [Throws and captures](throws_and_captures.md),
[Combat action execution](combat_action_execution.md),
[Target selection](target_selection.md), and
[Character action callbacks](../characters/character_action_callbacks.md).

Fighter fields are named in `Fighter`. Fields whose width is not established
keep raw offsets: `+0x9B8` (low two bits choose the grounded-family variant),
`+0xE3C` (hit request bits) and `+0xBA4` (an environment boundary).
*Grounded* means `contact_flags & 0x80`.

## Accepted-hit routing

`hit_route_accepted` sends a hit to `guard_enter_response` when
`guard_state >= 1` and to `response_enter_ordinary` otherwise. Attack flag
`0x00800000` can turn a guard into sentinel -1 (a facing condition) and
`0x00400000` clears it; both go ordinary. Sentinel -1 forces response `0x4F`
before any mapping or callback; a cleared guard uses normal selection
([Chakra and guard](chakra_and_guard.md#guarded-hit-selection-and-break-like-flags)).

Four router modes share that split with different gates:

| Mode | Request bit | Extra behavior |
| ---: | --- | --- |
| 0 | `0x1` (paired fighter as source) | Can substitute a replacement record; rejected while `hit_rejection_active` or when `hit_expected_repeat` is zero |
| 1 | `0x4` | Requires a retained source with type halfword `0x474F` and word `+0x0C == 1` and an overlay admission (`hit_mode1_check`); runs the substitution check, then source callbacks |
| 2 | `0x8` | Requires a retained source and no rejection; substitution check; writes a paired marker (1 ordinary, -1 guarded, -2 intercepted), of which only 1 notifies |
| 3 | — | Requires a retained source and no rejection; plain split |

The substitution check is `input_match_trigger_binding`. A match diverts to
`hit_intercept` (code `0x21` for mode 1, `0x41` for mode 2), which clears the
action lock, damps both speeds, forces `(0,8)` and adjusts two private floats;
the hit then returns without a response. Record lookup is owned by
[Target selection](target_selection.md#retained-source-writers-and-record-lookup).

`hit_retain_source` can write recovery provenance and a pending combo count
([Combo accounting](combo_accounting.md#explicit-and-pending-updates)) without
creating a response; a retained recovery source therefore does not imply a new
response. Its record setup and damage belong to
[Damage](damage.md#all-fifteen-btl-source-retaining-calls). Its tail runs
`fighter_end_exchange` on both fighters.

## Ordinary response selection

`response_enter_ordinary` gets a substate from `response_select_substate` and
forces `(5, substate)`. The substate indexes both the descriptor table
(`action_descriptor_table`) and `response_motion_table`.

The authored selector is `ActionRecord.response_selector`. The
*grounded-family* column applies when `(+0x9B8 & 3) < 2` and the receiver is
grounded.

| Selector | Grounded family | Otherwise |
| ---: | --- | --- |
| `0x00`, `0x01` | `0x27`, `0x28` | `0x2F` |
| `0x02`, `0x03` | `0x29`, `0x2A` | `0x30` |
| `0x04..0x07` | `0x2B..0x2E` | `0x31` |
| `0x08..0x0A` | `0x2F..0x31` | same |
| `0x0B..0x0E` | `0x32..0x35` | same |
| `0x0F` | `0x36` | `0x37` |
| `0x10`, `0x11` | `0x38`, `0x39` | same |
| `0x12` | `0x3C`/`0x3D` by orientation | same |
| `0x13..0x16` | `0x3E..0x41` | same |
| `0x17..0x1B` | `0x4A..0x4E` | same |
| `0x1C` | `0x50` | same |
| `0x1D..0x20` | `0x51/53/55/57` | `0x52/54/56/58` |
| `0x21` | `0x59` | same |
| `0x22..0x24` | random of `0x27/28`, `0x29/2A`, `0x2B/2C` | `0x2F`, `0x30`, `0x31` |
| `0x25` | random `0x27..0x2A` | random `0x2F..0x30` |
| `0x26` | random `0x29..0x2C` | random `0x30..0x31` |
| `0x27` | random `0x27..0x2C` | random `0x2F..0x31` |
| other | `0x27` | `0x2F` |

Authored use across the 74 primary tables (2,484 damaging records):

| Selector | Result | Records |
| --- | --- | ---: |
| `0x00..0x07` | light `0x27..0x2E` / `0x2F..0x31` | 645 |
| `0x08..0x0A` | `0x2F..0x31` | 61 |
| `0x0B..0x0E` | `0x32..0x35` | 131 |
| `0x0F` | `0x36` / `0x37` | 95 |
| `0x10`, `0x11` | `0x38`, `0x39` | 135 |
| `0x12` | `0x3C` / `0x3D` | 490 |
| `0x13` / `0x14` / `0x15` / `0x16` | `0x3E` / `0x3F` / `0x40` / `0x41` | 24 / 390 / 433 / 22 |
| `0x17..0x19` | held `0x4A..0x4C` | 10 |
| `0x1C` | `0x50` | 2 |
| `0x1D`, `0x1E` | `0x51..0x54` | 46 |

The random selectors are unused by damaging records; the 300 records with
selector `0xFF` are non-damaging. `guard_selector` is 0..4 on 2,311 damaging
records and 6..9 on 173.

Selection order around that mapping:

1. Guard sentinel → `0x4F`; missing record → `0x27`; failed context query →
   `0x3A`/`0x3B`.
2. An attack with a nonzero `row` against a falling `(5,0x3F)` receiver with
   no rejection count gives `0x37` under an environment-boundary test.
3. The source's character callback (below) replaces the mapping unless it
   returns -1.
4. Without a callback result, a repeat collapse applies for non-jutsu attacks
   with an expected repeat above 1 (`0x52/54/56/58` exempt):

   | Authored | Collapsed |
   | --- | --- |
   | `0x37`, `0x32` | `0x30` |
   | `0x3F` | `0x32` |
   | `0x40/0x41` | `0x2C` grounded family, else `0x35` |
   | `0x3C..0x3E` | `0x2B` grounded family with grounded source, `0x35` with airborne source, else `0x30` |
   | `0x36`, `0x38`, `0x39`, `0x4A..0x50` | random `0x29/0x2A` if grounded, else `0x30` |

5. Streak checks: `response_streak` counts consecutive responses to the same
   record at its expected repeat. A provisional `0x2F` becomes `0x37` when the
   expected repeat is below 2, the streak exceeds 2 and the source is
   grounded; any result becomes `0x37` for a grounded receiver with a streak
   above 3 and a zero `streak_exempt`. `response_exit_cleanup` resets the
   streak when leaving major 5.
6. With effect 0 or 1 attached, an airborne receiver keeps only `0x36..0x49`,
   `0x51..0x58` or `0x5A`; others become `0x37`.

`response_apply_table_timing` overrides the result with `0x5B` (grounded) or
`0x5C` and zero speeds for a jutsu-category attack when
`status_flags & 0x01` is clear and `opponent_lock_override` is zero.

`0x3A`/`0x3B` increment `response_repeat_count` up to 3; at 3 the receiver's
rejection count is primed to 60 if nothing is pending. The downed handoff
scale `1.0 - 0.25 * response_repeat_count` therefore steps through 0.75, 0.50
and 0.25. For an attack `rejection_count` of `0x7FFF`, event 0 stages the
row's lock value (6 for `0x3A`, 8 for `0x3B`) as the rejection count. With
receiver rate `r` and paired rate `p`, it multiplies by `2 - r` when `r != 1`,
again by `2 - r` when `p > 1`, and by `2 - p` when `p < 1`; the asymmetry is in
the code.

No static evidence justifies names such as "stagger", "crumple" or "guard
crush" for any substate.

### Character callbacks

Each source character's `<character>_hit_response(source, receiver, mode)`
can replace the response; -1 keeps the generic result. The receiver-side
lookup `receiver_vector_predicate` always returns zero, so the source's
callback is used. The initializer calls it in mode 2; `hit_classify_pair`
calls it in mode 0 earlier. Most motion writes are gated on mode 2, but live
attack-record writes are not, so the mode-0 call is not read-only.

`hit_repeat_value` is the repeat value callbacks compare: the receiver's
expected repeat when the source's current record is the retained one,
otherwise that record's `repeat_count`.

All 74 primary characters have a callback (annotated by character). First
Hokage's returns -1; Second Stage Kidomaru's returns -1 after the repeat query;
Sakura's and Ino's always return -1 but change motion or record fields. The
other 70 have non-default branches, so authored selector counts do not
describe final reactions. Examples that matter for the shared machine:

- Fourth Awakened Naruto, action `0x28`: `0x40`, then random reactions when
  grounded; rewrites the record's repeat, pause and rejection values.
- Rock Lee action `0x18` phase 3 and Might Guy action `0x1C` phase 3 write
  rejection count `0x7FFF`, so the row's count applies.
- Loopy Fist Lee action `0x1B` selects held `0x4A` without an authored held
  selector.
- Hanabi action `0x18` writes `attack_scale` in both modes.

The callbacks write `attack_scale`, `planar_scale` and `vertical_scale`,
consumed by the response motion. Response choice can therefore change with
phase, repeat value, grounding, private fields and randomness, and can move a
hit into or out of the states that the recovery and contact rules below
accept.

### Native identifiers

| State | Identifier | State | Identifier | State | Identifier |
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

The abbreviations are not expanded into player-facing names.

## Phases, animations and lengths

Each descriptor lists `PhaseRecord`s whose conditions are owned by
[Combat action execution](combat_action_execution.md#shared-phase-progression).
Notation: `E` animation end, `G` grounded, `D` falling or grounded, `O` end or
grounded, `B` end and grounded, `C<n>` secondary cursor `n`, `H` held
(condition 0), `T` end of list.

| Phases | Ordinary substates |
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

| Recovery substate | Phases | Rate |
| ---: | --- | --- |
| `0x5D` | `H, T` | — |
| `0x5E` | `G, T` | phase 0: 1.5 |
| `0x5F` | `D, T` | — |
| `0x60` | `C3, T` | phase 0: 2.0 |
| `0x61` | `E, H, T` | — |
| `0x62` | `G, E, H, T` | — |

Non-default phase rates in `0x27..0x5C`: `0x29/0x2A` phases 0/1 0.9375;
`0x2B/0x2C` 0.875; `0x2D` 0.6875; `0x2E` phases 0/1 and `0x3B` phase 0 0.75;
`0x32..0x35` phase 1, `0x3E` phase 1 2.0; `0x5A` phase 0 0.25; `0x5B` phase 0
1.5.

Hitstun is therefore not one counter: phases end on animation, contact or
timeline conditions, and held rows need external progression.

### Animation-gated lengths

Animation slots resolve through the character's `ANM_` names
(`CMN/2CMNBOD1.CCS` for `pcmn` names, otherwise the character's
`PL/2???BOD1.CCS`). An animation with frame count `F`, start frame `S` (1 when
the rate is below 256 and `S` is 0) and rate `R` ends after
`n = max(1, ceil((F - 1 - S) * 256 / R))` unpaused updates at update rate 1.0;
a `C<k>` phase lasts `ceil(k * 256 / R)` updates. Within one update the phase
updater reads the previous animation result, the dispatcher selects the
phase's animation, and the animation pass advances it, so an `E` phase lasts
exactly `n` updates. A state entered by hit routing cannot consume the
previous animation's end: the routed-this-update contact bit blocks the phase
updater until the animation pass.

Counts across all 74 primary characters (minimum..maximum, median); `G` and
`D` end on physics, `O` ends no later than `n`, `B` no earlier:

| Substate | Phases and updates |
| --- | --- |
| `0x27/0x28` | E `htn4/htn0` 3, E `hxn4/hxn0` 3..11 (7) |
| `0x29` | E `htn0` 3, E `hxn0` 3..15 (10) |
| `0x2A` | E `htn1` 3, E `hxn1` 3..12 (12) |
| `0x2B` | E `htn0` 3, E `hxn0` 3..16 (11) |
| `0x2C` | E `htn1` 3, E `hxn1` 3..13 (13) |
| `0x2D` | E `htn0` 3, E `hxn0` 3..21 (14) |
| `0x2E` | E `htn1` 3, E `hxn1` 3..15 (15) |
| `0x2F..0x31` | D `fht0`, C6 `jmp2` 6 |
| `0x32..0x34` | C4 `fht0` 4, E `jpz1/jmp0/jmp3` 8..15 (9) |
| `0x35` | C4 `fht0` 4, B `jpz1/jmp0/jmp3` 8..15 (9) |
| `0x36` | D `fht0`, G `fxk0`, E `fxk2` 2, E `col1` 8..28 (28) |
| `0x37` | D `fht0`, G `fxk0`, E `col2` 13..28 (28) |
| `0x38/0x39` | G `spn0`, E `col1` 8..28 (28) |
| `0x3A` / `0x3B` | E `col0` 8 / 10 |
| `0x3C` | E `nxf1` 3, C4 `fht1` 4, G `fxk1`, E `col1` 8..28 (28) |
| `0x3D` | E `nxf0` 7, C4 `fht0` 4, G `fxk0`, E `col1` 8..28 (28) |
| `0x3E` | E `nxf0` 7, E `yft0` 20, E `col1` 8..28 (28) |
| `0x3F`, `0x59` | E `nxf2` 2..10 (4), D `fht2`, G `fxf0`, E `col2` 13..28 (28) |
| `0x40` | O `nxf3` 4..5 (4), O `fal0` 10, E `fxk2` 2, E `col0` 8 |
| `0x41` | O `nxf3` 4..5 (4), O `yft0` 40, E `fxk0` 6, E `col1` 8..28 (28) |
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
| `0x5B` | E `ost0` 26..30 (27) |
| `0x5C` | C4 `fht0` 4, C6 `jmp2` 6, G `dow0`, E `lan0` 9..20 (10) |

Hiruko uses `htn0`/`hxn0` where others use `htn4`/`hxn4`, and Hiruko and
Classic Kankuro use `jmp0`/`jmp3` where others use `jpz1`. A median grounded
light hit `0x27` takes about 10 unpaused updates. **Inference:** `htn`/`hxn`
are the hit and recovery halves of light reactions and `col` is the collapse;
these are resource names, not visual confirmation.

Recovery animations: `kno0` for `0x5D`, `jmp2` for `0x5E..0x60`, `col0` then
`kno0` for `0x61`, and `dow0`, `lan0`, `nut0` for `0x62`. `0x60` completes after
2 updates and `0x61`'s `col0` phase after 8.

## Response motion

`response_motion_table` has one `ResponseMotionRow` per substate
`0x27..0x5C`. `response_update_ordinary` runs `response_motion_update` every
action update: on the update where the primary timeline crosses the row's
event gate it writes both speeds and saves `attack_scale`; on every other
update it damps planar speed toward zero. The pause value is applied by a
separate event test, which uses event 0 instead of the row's gate while an
exchange role is set.

`R` replaces both speeds, `A` adds them; rows are merged only when identical.

| Substates | Mode | Gate | Planar | Vertical | Damping | Aux | Pause | Lock |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0x27/0x28` | R | 0 | 10 | 0 | 0.35 | 1 | 1 | 5 |
| `0x29/0x2A` | R | 0 | 30 | 0 | 0.35 | 1 | 1 | 5 |
| `0x2B/0x2E` | R | 0 | 45 | 0 | 0.35 | 1 | 1 | 5 |
| `0x2C` | R | 0 | 40 | 0 | 0.35 | 1 | 1 | 5 |
| `0x2D` | R | 0 | 50 | 0 | 0.35 | 1 | 1 | 5 |
| `0x2F` | R | 0 | 30 | 25 | 0.25 | 1 | 1 | 5 |
| `0x30` | R | 0 | 40 | 30 | 0.25 | 1 | 1 | 5 |
| `0x31` | R | 0 | 50 | 35 | 0.25 | 1 | 1 | 5 |
| `0x32` | R | 0 | 10 | 50 | 0.125 | 1 | 2 | 5 |
| `0x33` | R | 0 | 30 | 45 | 0.125 | 1 | 2 | 5 |
| `0x34` | R | 0 | 50 | 40 | 0.125 | 2 | 5 | 0 |
| `0x35` | R | 0 | 65 | 25 | 0.12 | 1 | 2 | 5 |
| `0x36` | R | 0 | 55 | 20 | 0.10 | 1 | 1 | 120 |
| `0x37` | R | 0 | 50 | 32.5 | 0.15 | 1 | 1 | 120 |
| `0x38` | R | 0 | 50 | 40 | 0.075 | 2.5 | 1 | 120 |
| `0x39` | R | 0 | 60 | 25 | 0.075 | 2 | 1 | 120 |
| `0x3A` | R | 0 | 10 | 0 | 0.25 | 1 | 1 | 6 |
| `0x3B` | R | 0 | 30 | 0 | 0.25 | 1 | 1 | 8 |
| `0x3C/0x3D` | R | 0 | 60 | 20 | 0.075 | 1 | 2 | 120 |
| `0x3E` | R | 0 | 80 | 0 | 0 | 1 | 2 | 120 |
| `0x3F` | R | 0 | 0 | 55 | 0.35 | 1 | 2 | 120 |
| `0x40` | R | 0 | 0 | -50 | 0.35 | 1.25 | 1 | 120 |
| `0x41` | R | 0 | 60 | -50 | 0.05 | 0.8 | 2 | 120 |
| `0x42/0x45` | R | 2 | 0 | 0 | 0.35 | 1 | 2 | 120 |
| `0x43` | R | 3 | 0 | 0 | 0.35 | 1 | 2 | 120 |
| `0x44` | A | 2 | 0 | -30 | 0.35 | 1 | 2 | 120 |
| `0x46` | R | 1 | 15 | 7.5 | 0.075 | 1 | 2 | 120 |
| `0x47` | A | 1 | 20 | 0 | 0.05 | 1 | 1 | 120 |
| `0x48` | R | 2 | 0 | 40 | 0.075 | 1 | 2 | 5 |
| `0x49` | R | 3 | 10 | 40 | 0.075 | 0.75 | 2 | 5 |
| `0x4A/0x4B/0x4C/0x4E` | R | 0 | 0 | 0 | 0.35 | 1 | 1 | 0 |
| `0x4D` | R | 0 | 0 | 0 | 0.35 | 1.5 | 1 | 0 |
| `0x4F` | R | 0 | 20 | 0 | 0.5 | 1 | 0 | 5 |
| `0x50` | R | 0 | 0 | 0 | 0.35 | 1 | 4 | 0 |
| `0x51/0x53/0x55/0x57` | R | 0 | 40 | 0 | 0.35 | 1 | 1 | 120 |
| `0x52/0x54/0x56/0x58` | R | 0 | 40 | 30 | 0.075 | 1 | 1 | 120 |
| `0x59` | R | 0 | 0 | 55 | 0.075 | 1 | 2 | 120 |
| `0x5A` | A | 0 | 0 | 0 | 0.25 | 1 | 0 | 120 |
| `0x5B` | R | 0 | 40 | 0 | 0.10 | 1 | 0 | 5 |
| `0x5C` | R | 0 | 40 | 40 | 0.10 | 1 | 1 | 6 |

Negative vertical values are kept as authored; screen direction is not
assumed.

### Modifiers

The table holds bases. At the motion event, in order:

1. Planar speed is clamped to the character's grounded or airborne limit and
   airborne vertical speed to the character table's lower bound.
2. One of: a source `fighter_knockback_scalar` `s != 1` (planar × `s`,
   vertical × `1 + 0.5(s - 1)`); otherwise ×1.25 on both in major 5 with a
   high exchange role; otherwise the source's `knockback_given` with the same
   form, then the receiver's `knockback_taken` `q` clamped to 0..2 (planar ×
   `1 - 0.75(q - 1)`, vertical × `1 - 0.25(q - 1)`).
3. `attack_scale` `s`: planar × `s`; vertical × `1 + 0.5(|s| - 1)` above 1,
   otherwise × `|s|` (or the half-strength form with a source scalar below 1).
4. `planar_scale` and `vertical_scale`. Each consumed transient resets to 1.0.

`attack_scale` comes from `ActionRecord.knockback_scale` when
`response_retain_attack_record` (or the Extra Hit retarget) retains a new
record with a nonzero repeat count. Authored scales: 1.0 on 1,859 damaging
records; above 1 on 423 (1.5 ×154, 1.25 ×149, 1.2 ×37, 2.0 ×33, others up to
3.0); below 1 on 200 (down to 0.0); `-0.5` and `-2.0` once each, which reverse
the planar direction.

### Gravity

In major 5, with an exchange role, or with `state_flags & 0x80`, the movement
pass applies a fixed gravity of `3.0 × update_rate` per update with terminal
speed -90; other states use the character gravity
([Movement and physics](../stages/movement_and_physics.md#gravity-and-input-smoothing)).
The row's aux value only removes the -90 clamp when it is not 1.0.

The launch is written in the hit update and the first movement follows in the
same update, so a launch with final vertical speed `v > 0` starts falling (a
`D` phase) after `floor(v / 3) + 1` active updates. **Inference:** on flat
ground it lands after about `2v/3 + 1` updates (14–15 for `0x3C/0x3D`, about
38 for `0x3F`); stage geometry decides the exact contact. Pause updates add to
these counts.

## Pause, lock and update order

Two countdowns run in order:

1. `update_pause` decrements by 1.0. While positive, action timelines,
   the per-action dispatcher, movement and animation stop; the displayed
   position jitters. This is the hitstop.
2. `action_lock` decrements by `update_rate`, only once the pause is
   below 1. `action_entry_allowed` refuses entry while it is nonzero.

Staged values are written as `-N` with a pending flag and become `N` on the
next maintenance pass without decrementing
([Timer primitives](../../runtime/timer_primitives.md#fractional-integer-cursor-block)).

Pause sources:

- the attack `update_pause` at initialization: positive staged, negative
  active immediately, zero clears but leaves the pending flag, `0x7FFF`
  untouched;
- the row pause at its event, only when nothing is pending, so a positive or
  zero attack pause suppresses a gate-0 row pause.

The row lock applies at event 0. When it raises the lock, the absolute attack
pause is added (unless `0x7FFF`); category `0x2` forces 20; jutsu and
hold/companion categories bypass the row minimum.

Within one 30 Hz battle update ([Battle lifecycle](../session/battle_lifecycle.md#battle-update-cadence)),
`battle_dispatch_phases` calls `fighters_phase_slot_0c` (running
`fighters_update`, then each fighter's movement/animation slot), then
`fighters_phase_slot_14` (each fighter's timeline slot). `fighters_update`
runs:

1. countdown maintenance for every fighter;
2. pair helpers and `hit_resolve_pair`, then the hit requests: `0x100`
   `hit_attacker_landed`, `0x1` mode 0, `0x8` mode 2, `0x4` mode 1;
3. removals;
4. for fighters with no active pause: bridge, `fighter_pre_phase_step`,
   `fighter_update_phase_and_exits`, `fighter_consume_logical_input`,
   `fighter_dispatch_action_update`;
5. request `0x2` (`hit_handle_bit2`).

Because routing precedes the per-action pass, event 0 of a new response runs
in the hit update unless a pause is already active. With a positive attack
pause `N`, update rates 1.0 and nothing pending:

| Update | Receiver |
| ---: | --- |
| 0 | hit routed; response entered; pause staged; event 0 runs motion, damage ([Damage](damage.md)), lock and rejection staging; first movement and animation step |
| 1 | lock decrements once, then the pause activates at `N` |
| 2..N | suspended; the lock does not decrement |
| N+1 | pause reaches 0; action updates resume |

The receiver is suspended for exactly `N` updates after the hit update. With
row lock `L`, the lock reaches zero in update `2N + L`. A negative attack
pause `-N` freezes updates `0..N-1` and runs event 0 in update `N`. Update
rate scales the lock and timelines but not the pause.

During the pause the movement slot still runs the bridge, action selection
and the guard-input age, so a candidate such as an Extra Hit counter can be
chosen.

The attacker's pause comes from request `0x100` (`hit_attacker_landed`):
when the defender's rejection count is not positive and the attack has category
`0x2` or a nonzero expected repeat, the attack pause is applied immediately
(none for category `0x2`), so the attacker is suspended in updates `0..N-1`. Flag `0x20000` skips it
(151 records, 138 damaging); `0x7FFF` uses the defender's selected response or
guard row pause.

Authored `update_pause` on damaging records: 2 (914), 3 (415), 1 (271), 4
(194), 5 (86), `0x7FFF` (477), 0 (44), negative (66), 6..16 (17).

`action_entry_allowed` keeps `0x27..0x5A` ineligible after the lock ends;
`0x5B/0x5C` are eligible at once, and mode 2 bypasses the rejection. In major
6, `0x5F` is eligible from cursor 8 and `0x60` from cursor 3; others are not.

## Response exits

`response_dispatch_transition` receives the phase-completion signal
(`phase_event_completion`):

| Substate | Exit |
| --- | --- |
| `0x27..0x2E` | neutral `(0,0)` |
| `0x2F..0x31` | `(4,0x26)` grounded, else `(3,0x1E)` |
| `0x32..0x35` | `(4,0x26)` grounded, else `(3,0x25)` |
| `0x36..0x39`, `0x42..0x49`, `0x51..0x58` | downed handoff, scale 1.0 |
| `0x3A/0x3B` | downed handoff, scale `1 - 0.25 × response_repeat_count` |
| `0x3C..0x41` | downed handoff, then the contact checks below |
| `0x4A..0x4E` | `response_held_handoff` every update |
| `0x4F` | neutral under the two conditions below |
| `0x50` | neutral once the paired fighter leaves major 8 |
| `0x59` | primary event 1 calls `fighter_paired_event`; completion does nothing |
| `0x5A` | forced to phase 2 when grounded below it; completion hands off to downed |
| `0x5B` | `(8,0x14)` if either fighter's `+0xB10` is set, else neutral |
| `0x5C` | the same, else neutral grounded or `(3,0x1E)` |

Held `0x4A..0x4E` follow the paired fighter:

| Paired fighter | Held fighter |
| --- | --- |
| not in major 8 with a record, paired in `(6,0x61/0x62)` | `(6,0x61)` |
| not in major 8 with a record, otherwise | `(2,0x1D)`, restoring `saved_response_position` unless the paired action keeps it |
| action flag `0x04000000` | stays |
| category `0x100`, event bit `0x2` clear / set | neutral / stays |
| categories `0x100` and `0x200` clear | neutral |
| `0x200` only, event bit `0x8` set / clear | re-enters an ordinary response / stays |

These are paired synchronization, not hitstun timers
([Throws and captures](throws_and_captures.md#common-entry-handoff-and-interruption)).

`0x4F` runs `response_4f_rate_sequence`: event 0 sets both fighters'
`update_rate_override` to 0.1, then after six invocations eases both back to
1.0 over six more, reaching stage 3 on the thirteenth unpaused call. `0x4F`
exits to neutral when the paired fighter executes a jutsu-category action
(this also clears the lock), or when its animation is complete and the stage
is 3.

### Contact rebounds

Before the state switch, `response_contact_proposal` can replace a launch
with a contact rebound (ordinary major 5, upward speed 40 at its event):

| Current and contact | Destination | Cursor ceiling |
| --- | --- | ---: |
| `0x3C/0x3D/0x41`, side contact | `0x48` | 5 |
| `0x3E`, side contact, phase below 2 | `0x48` (attack scale 2.0) | none |
| `0x40/0x41`, grounded | `0x49` | 5 |

Grounding is tested last, so it wins for `0x41`. Every proposal needs a
retained attack, `saved_attack_scale > 0.5`, external mode 0, and flag
`0x80000` clear; then a cursor below the ceiling or flag `0x100000` (which an
exchange role also requires). `contact_consume_chakra` follows and can spend
the struck fighter's chakra ([Chakra and guard](chakra_and_guard.md)).
`response_contact_enter` turns the fighter for `0x48` and clears its repeat
count, or restores `attack_scale` for `0x49`. Both later hand off to downed.

Contact facts come from `fighter_apply_movement`, which refreshes the side,
grounded and ceiling bits each pass
([Movement and physics](../stages/movement_and_physics.md#floor-side-surfaces-and-limits)).

Authored: one record has `0x80000` (Classic Choji action 25) and 25 damaging
records have `0x100000`. Callback writers change them on the source's live
record: Rock Lee action `0x36` (by a private byte incremented on each mode-2
call, reset while the opponent leaves major 5), Deidara action `0x2C` (set
when the receiver's streak read before its increment is at least 3), and Might
Guy action `0x25` (`0x100000` by a chain byte owned by
[Substitution](../characters/substitution.md#callback-ordering-and-counter-ownership)).
Re-entering an attack or resetting a counter does not restore the shipped bits
(`fighter_enter_action_record` leaves flags alone). Deidara's action `0x2C`
also picks `0x41` with rejection `0x7FFF` while the repeat value is within 3 of
a per-chain baseline; action `0x2B` picks `0x3F` with `0x7FFF` below repeat 3.

Later in the switch:

| Current | Transition |
| --- | --- |
| `0x3C` / `0x3D` | airborne side contact → `0x42` / `0x43` |
| `0x3E` | side contact → `0x43` |
| `0x3F` | ceiling contact → `0x44` |
| `0x40` | on grounding: `0x46` if the cursor is below 4 and external mode is 0, else `0x45` with vertical speed `-0.5 × landing_vertical_speed` |
| `0x41` | on grounding → `0x47` |

The downed handoff in `0x3C..0x41` does not return, so a contact transition
can replace a downed state entered in the same dispatch; after the handoff the
cursor reads zero, so `0x40` can pick `0x46`. The `0x45` bounce normally reads
zero, because `response_exit_cleanup` clears `landing_vertical_speed` without
an exchange role.

Dispatch precedence: the first-grounded input recovery (below) runs before the
proposal, then the proposal, then the switch, the late input recovery, and a
final fallback. `0x3C..0x3E` with side contact first test a stage correction
(`stage_correct_position`) and return early when the position jumps by more
than 500. Initial `0x3C..0x41` skip all handling while exchange role bits
`0x1500` are set. The final fallback forces `(5,0x5A)` (except from `0x45` or
`0x5A`) when the environment boundary `+0xBA4` is unset or reached, a
side-contact exception does not apply, and `animation_slot` is `0x1E..0x22`
(`fxk2`, `col0`, `col1`, `col2`, `kno0`); it can replace an earlier
transition in the same dispatch.

### Input recoveries

Two binding-2 (`0x00010000`) recoveries run inside the ordinary response; they
are separate from the contact rebounds, downed choices and the Extra Hit
counter. `ACT_RCV_0/1` do not establish which one players call a rebound.

- **First grounded** (`ACT_RCV_1`, `(0,0x0A)`): substates `0x36..0x39`,
  `0x3C/0x3D`, `0x3F..0x41`, `0x48/0x49`; cursor at least 2; height above
  -500; not the dummy-drop record; no effect 0/1; exactly the first grounded
  update; no exchange role bits `0x1500` for `0x3C..0x41`. Enters through
  `recovery1_enter` and returns at once.
- **Late** (`ACT_RCV_0`, `(0,0x09)`): still in major 5 at `0x38/0x39`,
  `0x3C/0x3D`, `0x3F` or `0x48/0x49`; external mode 0; no pause; no exchange
  role; no effect 0/1; a retained `recovery_source` and `recovery_record`; the
  press not in the previous five stored samples (`input_history_has`); and the
  cursor inside:

  | Substate | Window |
  | --- | --- |
  | `0x38/0x39`, `0x48/0x49` | 4..6 |
  | `0x3C/0x3D` | 4..8, or `r+4..r+6` (`r` 0..3) for a standard source and category `0x200` |
  | `0x3F` | `r+3..r+5` (`r` 0..2) for a standard source, flag `0x2` and rising speed |

  Random windows are drawn on every query (`recovery_late_window`). The
  history ring is appended after the timelines and outside the pause guard,
  so five samples need not be five cursor updates.

`ACT_RCV_0` (`D, T`) exits to `(4,0x26)` grounded or `(3,0x24)`; its motion
(`recovery0_motion`) rises with `sqrt(2g × 250) - g/2`, `g = 3 × motion_scale`,
and clears a non-pending rejection count. `ACT_RCV_1` (`E, E, G, E, T`, phase
0 rate 2.0) exits to neutral grounded or `(3,0x1E)`, also as soon as it falls
without an exchange role; its motion uses `planar_scale` and
`vertical_scale`. Both player entries count statistic 12 unless
`status_flags & 0x01`; no resource is spent.

The effect 0/1 test (`fighter_has_effect_0_1`) checks only the struck
fighter's own list and ignores node countdowns, so a node awaiting removal
still blocks. Attacker-only effects do not count; IDs 0/1 install only on the
supplied fighter (`effect_apply`, `object_apply_effect1`). The same membership
drives the airborne `0x37` remap and Extra Hit candidate checks. Entering
`0x5D` or `0x61/0x62` requests their removal
([Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#update-expiry-and-removal)).

Other entries skip these gates: effect `0x7D` enters `ACT_RCV_0` after cursor
60 (`effect_7d_update`), `attack_landing_recovery` enters `ACT_RCV_1` on the
grounded completion of a category-`0x200`/flag-`0x04000000` attack, and two
character callbacks enter `ACT_RCV_1` in action `0x29`; none count the
statistic.

`recovery_source`/`recovery_record` are retained provenance, not a fresh-hit
marker. `fighter_init` clears them; `response_enter_ordinary` and
`guard_enter_response` (non-jutsu attacks) write them for a source of type `0x474F` when
`status_flags & 0x01` is clear and `context_mode_word` is zero; a failed gate
keeps the old pair. `hit_enter_trade` and `hit_retain_source` also write
them. No response or recovery exit clears them; countdown maintenance and
`0x61`'s first event replace them with a self/`atk_dummy_record` pair. Copy
limits are owned by
[Target selection](target_selection.md#copied-provenance-and-pointer-lifetime-limits).

## Timed downed recovery

`downed_recovery_enter(scale, fighter)` enters `(6,0x5D)`. With
`state_flags & 0x08` it sets the thresholds:

| Profile | `downed_auto_recovery` | `downed_input_recovery` |
| --- | ---: | ---: |
| `status_flags & 0x20` clear | 45 | 8 |
| set | 90 | 40 |

Both are multiplied by the scale (and an effect factor that is always 1.0 on
this path, since the call happens in major 5). The float-to-integer conversion
uses the active FPU rounding mode. Five overlay entries (`downed_override_a..e`)
instead force thresholds of 45 (or arguments) without setting the enable bit.

Update rate is 1.0 in majors 5 and 6 unless `update_rate_override` or
`update_rate_multiplier` is set, and the cursor starts at 0 on entry, so the
default profile recovers automatically in update 45 (1.5 s) and accepts input
from update 9; the slow profile uses 90 (3.0 s) and 41. `0x3A/0x3B` shorten
both. `paired_rate_sequence`, `exchange_rate_cleanup` and `effect_4a_callback`
also write those rate fields
([Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#specialized-entry-exit-and-callback-behavior));
effect `0x4A` can turn a paired `0x5D` into `0x5F` and redirect `0x61`.

`downed_recovery_update` for `0x5D`:

- enable bit clear: returns, no exit;
- airborne: two environment classes hold `0x5D`, others divert to `(5,0x5A)`;
- cursor ≥ `downed_auto_recovery` → `(6,0x5E)`; else cursor >
  `downed_input_recovery` with binding 2 → `(6,0x5F)`; then, only if the state
  did not change, binding 1 → `(6,0x60)`.

At default thresholds both inputs choose `0x5F` before the automatic exit.
`downed_first_event` primes the rejection count to 1 and clears the action
lock, yet `0x5D` stays ineligible for action entry. `0x5E` and `0x60` exit to
neutral and `0x5F` to `(3,0x20)`. `0x5E` rises with constant 125, `0x5F` with
250 and planar 20, `0x60` only turns.

`recovery_exit_cleanup` stages short rejection counts on leaving: 4 from
`0x5E`, 3 from `0x5F`, 2 from `0x60` (unless one is pending). It clears
`response_repeat_count` except toward `(5,0x3A/0x3B)`. The `0x5D` choices do
not test effects 0/1, contact flags or input history.

`action_rewrite_logical_mask` gives a recovery cancel: logical `0x00040000`
in `0x5E`, `0x60` and `0x5F` below cursor 3 forces `(0,0x0B)` (`ACT_BST_0`)
when `section` equals halfword `+0x324`, halfword `+0x9F0` is zero, the
fighter is in the grounded-family variant (`fighter_reaction_variant_high` is
zero) and no exchange role is set.

`0x61` (`H` after `col0`) moves on when external mode is set or the cursor
passes `0x13`: to `0x62` with the enable bit, otherwise through a dummy-record
ordinary response. `0x62` places the fighter at cursor `0x1E` from the stage's
`DMY_pp1_010`/`DMY_pp2_010` node (`stage_placement_section`,
[Stages](../stages/stages.md#resident-generic-factories-and-mandatory-records))
and returns to neutral after it when one of two fighter halfwords is zero.

## Guarded hits

Guard stance and the guard state consumed by the router are owned by
[Chakra and guard](chakra_and_guard.md#guard-input-and-action-lifecycle).

`guard_enter_response` takes `ActionRecord.guard_selector`, adds 5 to 0..4
when airborne, stores it in `guard_response_index`, and forces `(0,7)` for rows
5..9 or airborne and `(0,6)` otherwise. Descriptors: `(0,5)` `ACT_GDN_0`
(`nxg0`, held `gdn0`), `(0,6)` `ACT_GDN_1` (`ght0` 7..11, median 7; held
`gdn0`), `(0,7)` `ACT_GDA_1` (`gha0` 6..9, median 7; held `dow0`). The held
second phase is left only by `guard_update_stance`.

`guard_response_table`:

| Row | Planar | Vertical | Damping | Pause | Rejection | Lock | Phase rate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 30 | 0 | 0.35 | 1 | 2 | 8 | 176 |
| 1 | 30 | 0 | 0.35 | 1 | 2 | 8 | 160 |
| 2 | 35 | 0 | 0.35 | 1 | 2 | 8 | 144 |
| 3 | 40 | 0 | 0.35 | 1 | 3 | 12 | 128 |
| 4 | 40 | 0 | 0.125 | 0 | 3 | 24 | 128 |
| 5 | 20 | 15 | 0.25 | 1 | 2 | 8 | 192 |
| 6 | 25 | 20 | 0.25 | 1 | 2 | 8 | 176 |
| 7 | 30 | 20 | 0.25 | 1 | 2 | 8 | 160 |
| 8 | 40 | 20 | 0.35 | 1 | 2 | 12 | 128 |
| 9 | 40 | 30 | 0.125 | 1 | 2 | 24 | 64 |

All rows replace speeds at event 0 with aux 1.0. `guard_response_init`
stages the rejection count unless the attack already did, raises the lock to
the row value, and writes the phase rate into the shared descriptor, so
guarded reactions animate at 0.25..0.75, slower for higher rows. The row pause
is a fallback used only when the attack pause is `0x7FFF`: in guard mode a
positive attack pause is active immediately, a negative one is staged, zero
clears, and flag `0x20000` suppresses both.

`guard_update_stance`:

| Lock | Guard input | Grounded | Next |
| ---: | --- | --- | --- |
| 0 | released | yes | neutral |
| 0 | any | no | `(3,0x21)` |
| 0 | held | yes | stance `(0,5)` phase 1 |
| nonzero | any | yes | `(0,6)` phase 1 |
| nonzero | any | no | `(0,7)` phase 1 |

Stance calls it when `guard_state` reaches zero, `(0,7)` while grounded, and
`(0,6)` at phase 1 once the secondary timeline is positive and the lock
crosses zero. Exits go through `guard_stance_exit` and `guard_response_exit`.

## Rehit suppression

Two gates inside the accepted-hit router stop new responses; neither is a
hurtbox change or global invulnerability ([Collision](collision.md) owns
contact).

**State windows.** `hit_response_gate_bits` sets bit `0x10` unless
`rehit_classify_response_window` returns 1. The router drops the hit when the
low nibble is set without `0x10`, or when the nibble is clear, `0x10` is clear
and `0x20` is set. The classifier returns 1 in:

| Window | Condition |
| --- | --- |
| `0x5D` | always |
| `0x40`, `0x41`, `0x45..0x47` | grounded with cursor above 3 |
| `0x3A`, `0x3B` | rejection count not positive |
| `0x36..0x39`, `0x3C`, `0x3D`, `0x3F`, `0x42..0x44`, `0x52/54/56/58`, `0x5A` | grounded after the action included airborne motion |
| `0x48`, `0x49` | that condition with more than 4 grounded updates, or phase 2 |
| `0x3E` | phase 2 |

Inside a window a hit passes only with a clear low nibble (attack flag
`0x200000`, or flags `0x11` on a non-jutsu attack: 158 records, 156
damaging, in 72 tables) and a clear `0x20` (`response_repeat_count` below 3,
and a different record or the same one at its expected repeat). Guard flag
`0x800000` is on 109 damaging records and `0x400000` on none. Guard states do
not match any window.

Rejected as invulnerability evidence: `fighter_participant_eligible`,
`fighter_placement_check_a/b`, `response_class_interaction/motion` and
`action_rewrite_logical_mask` classify states for other consumers.

**Rejection countdown.** While `hit_rejection_active`, router modes 0, 2 and 3
drop hits (mode 1 does not), `hit_classify_pair` rejects the attacker's request
before routing (unless its classifier returns exact zero), and the attacker's
pause is withheld. Simultaneous hits reach `hit_enter_trade` only when neither
count is positive.

| Writer | Value |
| --- | --- |
| attack `rejection_count` (`hit_init_rejection_count`, ordinary and guarded) | 0 clears, positive staged, negative active, `0x7FFF` untouched |
| ordinary event 0, attack `0x7FFF`, nothing pending | row lock value, rate-adjusted |
| guard row | 2 or 3 when the attack staged nothing |
| capped `0x3A/0x3B` repeat | 60 |
| Extra Hit counter receiver | 60 staged ([Extra Hit](extra_hit.md#receiver-response-and-exchange-limit)) |
| `0x5D` first event | 1 if inactive |
| `hit_set_rejection` | router clear on gate result 0; Ultimate Jutsu contest start sets 60 on both ([Ultimate Jutsu](../characters/ultimate_jutsu.md)) |
| recovery exits | 4 / 3 / 2 |
| `effect_7d_update` | cleared in grounded phases of listed responses |

The count decrements by 1.0 only without a pause but activates during one.
With attack pause `N` and positive `rejection_count` `M`, mode-0 hits are
dropped in updates `1..N+M`.

Authored `rejection_count` on damaging records: `0x7FFF` (1,462), 1 (761), 2
(173), 3 (33), 4 (18), 0 (16), negative (13), 5..16 (8). The sentinel uses the
row lock value: 5 for most light and airborne reactions, 120 for knockdowns
and launches. An Extra Hit clears the receiver's count when it starts.

## Hit count

`response_enter_ordinary` increments statistic 18 (ordinary hits, maximum
tracked) except for source type 4, `PL_ATK_DUMMYDROP`, attack category `0x2`,
or `status_flags & 0x01`; `guard_response_init` increments statistic 19 under
the same flag. `fighter_init` clears all 24 pairs with `stats_reset_block` and
then reloads them from a per-side bank
([Awakening](../characters/awakening.md#state-retained-across-the-native-rebuild)).
No in-match reset exists. `stats_condition` is the only reader
([Battle statistics](../session/battle_statistics.md#statistic-derived-conditions)).
