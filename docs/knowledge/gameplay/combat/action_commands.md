# Battle action-command and input interpretation

How retail NA2 (`SLPS-25837`) turns pad input into battle actions: the
resident pad masks, the `BTL.BIN` input history and logical mask, and the
resident action-table selection.

## Research coverage

Established: the native masks and configurable bindings, the `ccCommand`
history and its matchers, logical-mask translation, the two double-tap tables,
resident hold/release and multi-press synthesis, signature construction,
selector modes and entry gates, fixed-chain masks, working-array setup, and the
static action data of all 78 character definitions. Open: user-facing names of
the object-relative direction selectors, any producer of
`BattleInput.alternate_angle`, eligibility writers outside the screened
callbacks, and observed selection frequencies.

Routines, structures and data are named by the NA2 annotations in
`@annotations/NA2`; their comments carry the per-routine detail. Addresses are
live.

Related owners: [Controller input](../../runtime/controller_input.md) (pad
production), [Combat action execution](combat_action_execution.md) (execution,
pending dispatch, interruption),
[Character action callbacks](../characters/character_action_callbacks.md),
[Extra Hit](extra_hit.md), [Battle AI](../session/battle_ai.md), and
[Battle Command List and move chart](../../localization/ui/battle/command_list_and_move_chart.md).

## Native masks and bindings

The resident pad layer produces a 16-bit active-high mask from the active-low
packet (`pad_read_packet_words`):

| Mask | Control | Mask | Control |
| ---: | --- | ---: | --- |
| `0x0001` | L2 | `0x0100` | Select |
| `0x0002` | R2 | `0x0200` | L3 |
| `0x0004` | L1 | `0x0400` | R3 |
| `0x0008` | R1 | `0x0800` | Start |
| `0x0010` | Triangle | `0x1000` | Up |
| `0x0020` | Circle | `0x2000` | Right |
| `0x0040` | Cross | `0x4000` | Down |
| `0x0080` | Square | `0x8000` | Left |

Battle bindings 0..7 default to Triangle, Circle, Cross, Square, L1, R1, L2
and R2 (`default_battle_bindings`). The input object copies them, then
`bindings_refresh` replaces them with the configured side array from
`bindings_get`, so interpretation follows the player's configuration.
Bindings are full 16-bit masks: a binding to Select, L3 or R3 is tested like
any other bit. Presentation readers are owned by the Command List document.

The battle history does not use the pad's repeat or raw-history words. It
copies held, pressed and released words, both stick angles and magnitudes,
then recomputes the press and release edges against the previous normalized
battle record ([Controller input](../../runtime/controller_input.md#publication-lifetime-and-consumer-snapshots)).

## Battle input object and history

Each side has one `BattleInput` (original class `ccCommand`, list owner
`ccCommandCtrl`). Battle setup creates sides 0 and 1, links each to its
fighter and the opponent, and retains both pointers.

Update order: `battle_create_graph` refreshes bindings once through the list
phase; afterwards `battle_dispatch_phases` reaches `input_object_update` in
its input phase each battle update, through the controller's virtual slots.
No seconds conversion is applied anywhere in this path.

The history is a ring of `InputRecord`s whose capacity is `300 / pacing`,
where `pacing` is the system context's display-count divisor read once at
construction (1 or 2; owned by
[Task system](../../runtime/task_system.md#root-pacing-and-the-engine-gate)
and [Battle lifecycle](../session/battle_lifecycle.md#battle-update-cadence)).
Capacity is therefore 300 or 150 records. **Inference:** this keeps the
history span constant across both pacing settings. Matcher windows are record
counts and are not divided.

### Normalization

`input_normalize_record` rewrites each new record:

- Left-stick magnitude below `0x40` becomes zero; `0x40..0x7F` becomes
  `((m - 0x40) * 3) / 2 + 0x20`; `0x80` and above is kept.
- With no held direction bit, the stick synthesizes one only when the
  normalized magnitude is strictly above `0xA0`. Angular predicates need only a
  nonzero magnitude, so raw magnitudes `0x40..0xA0` can satisfy angular tests
  without creating native direction bits.
- A held direction with zero magnitude supplies magnitude `0xFF` and the table
  angle for nibbles 1, 2, 3, 4, 6, 8, 9 and 12. Other nibbles (opposing
  directions) get angle and magnitude zero; the held bits and edges are not
  rewritten.
- When both a digital direction and a nonzero stick exist, the digital bits
  drive history matching and the angle drives angular tests; they need not
  agree.

While the fighter's input-suppression bits are set, the translator's outputs
are zeroed but the history keeps recording.

## History matchers

`input_history_match` scans `distance + 1` records newest to oldest from
`skip` records back, masks each candidate with `filter`, and returns 1 on the
first subset (or exact) match. Two behaviors matter:

- A diagonal press request accepts a record whose pressed direction edge is
  completed by that record's held direction, so a diagonal can be formed
  from an already-held cardinal. Cardinal requests get no such leniency.
- Nothing is clamped: a binding index, a skip or a distance beyond the ring
  wraps and can revisit records. Retail callers stay within 16 records for
  boolean tests and 31 for counts.

`input_history_count` counts every match in the window instead and has no
diagonal repair. A zero binding matches every candidate.

Resident consumers outside the translator: `input_match_trigger_binding`
accepts a press of binding 6 or 7 within 0..3 records (substitution);
`input_match_binding1_release` tests a binding-1 release in the current record.

## Logical mask

`input_build_logical_mask` writes `BattleInput.logical_mask`:

| Native condition | Logical bits |
| --- | ---: |
| press binding 0 (Triangle) | `0x08000000` |
| press binding 1 (Circle) | `0x00001000`, `0x40000000` |
| press binding 2 (Cross) | `0x00010000`, plus modifiers below |
| press binding 3 (Square) | `0x01000000` |
| press binding 4 (L1) | `0x02000000` |
| press binding 5 (R1) | `0x20000000`, clearing `0x04000000` |
| hold binding 6 or 7 (L2/R2) | `0x10000000` |

A binding-2 press adds `0x00080000` with native Up or `0x00100000` with native
Down (pi/2 tolerance). If the same binding was also pressed at record ages
1..7, it adds `0x00040000` when selector 9 holds and `0x00020000` otherwise.

Angular sector bits:

| Selector test | Bits |
| --- | ---: |
| 5 / 4 at `sector_threshold_45` | `0x1` / `0x2` |
| 2 / 3 at `sector_threshold_23` | `0x4` / `0x8` |
| 2 / 3 at pi/2 | `0x10` / `0x20` |
| 6 / 7 at about 5pi/6 | `0x40` / `0x80` |
| 14 / 15 at about 5pi/6 | `0x100` / `0x200` |

The double-tap classifier adds `0x400` (group 0) or `0x800` (group 1).

### Direction selectors

`input_direction_in_sector` accepts when the wrapped difference between the
stick angle and the selector's target is below half the tolerance. Zero
magnitude succeeds only for selectors 0 and 1.

| Selector | Target |
| ---: | --- |
| 2, 3, 4, 5 | native Up, Down, Left, Right |
| 6 / 7 | `opponent_angle` / its opposite |
| 8 / 9 | sign of `opponent_angle` / opposite, as a half-plane (±pi/2) |
| 10..13 | `alternate_angle` and opposite, only while `alternate_valid` |
| 14 / 15 | sign of `facing_angle` / opposite, as a half-plane |

`opponent_angle` points from the fighter to the opponent including the height
difference, signed by the camera view; at equal height it is native Right or
Left. `facing_angle` is the fighter's own yaw relative to the view. The two
pairs `0x40/0x80` and `0x100/0x200` can therefore differ.
`input_history_advance` computes both before translation.

Selectors 10..13 are unused: every direct call is in the translator and none
passes them, and nothing writes `alternate_angle` or `alternate_valid`. The
translator's result `-2` branch of the double-tap classifier is unreachable.
The defaults of `sector_threshold_23/45` are pi/2 and about 5pi/6; two
resident fighter states widen both to about 2.094 rad and others restore the
defaults.

### Resident synthesis after translation

The first per-fighter pass of `fighters_update` runs two synthesizers before
action selection:

- `input_synthesize_hold_release` (binding 1): while `hold_progress_cap` is
  nonzero, the release latch is clear, the major state is not 5 or 6 and the
  cooldown is zero, holding to `hold_threshold` adds logical `0x00002000` and
  advances progress up to the cap; once progress exists, release or loss of
  the hold adds `0x00004000`. Either bit latches and stops synthesis until
  reset. `input_match_binding1_release` provides the reset for a major-8
  hold/companion action, reloading the cooldown.
- `input_synthesize_multi_press` (binding 1): more than
  `multi_press_threshold` presses within `multi_press_distance + 1` records
  adds `0x00008000`. Defaults are 2 and 12, so more than two presses in 13
  records.

Hold/release is disabled by default. Constructors override the parameters
through `input_params_apply`:

| Character ID | Cooldown reload | Hold threshold | Progress cap |
| ---: | ---: | ---: | ---: |
| 40 | 2 | 2 | 60 |
| 48 | 24 | 24 | 60 |
| 53 | 24 | 12 | 36 |
| 54 | 24 | 24 | 60 |
| 57 | 16 | 16 | 30 |
| 64 | 2 | 2 | 36 |
| 77 | 16 | 8 | 90 |
| 84 | 16 | 12 | 90 (60 in `tsunade_set_mode` mode 1) |
| 85 | 16 | 5 | 60 |

These are exactly the nine definitions with hold/release signatures. Fifteen
constructors widen the multi-press window (threshold stays 2): distance 16 for
IDs 14, 38, 49, 51, 62, 66, 67, 69, 76 and 86, and 30 for IDs 6, 16, 65, 75 and
77.

## Double-tap tables

The only static `ccCommand` tables (`command_groups`) are two-step exact
direction presses: group 0 is Down, Down and group 1 is Up, Up.
`command_tables_evaluate` matches each step's nearest press within 16
candidates, newest step first, with the two presses in different records, and
compares only the direction nibble. A requested Right/Left is swapped by
`Fighter.facing`; Up and Down are unaffected.

With newer press age `n` and older age `o`: `0 <= n <= 15` and
`n + 1 <= o <= n + 16`. No history is consumed, so the same pair stays
recognized while `n` remains in range. If both groups match, the larger `n`
wins and a tie keeps group 0. These are double-tap recognizers, not attack
strings or the jutsu selector.

## Bridge and dispatch order

`fighter_copy_input_outputs` copies the logical mask and stick outputs to the
fighter; if both `0x00001000` and `0x01000000` are present it drops
`0x01000000`. `fighter_consume_logical_input` then runs, in order:

1. `guard_update_input`, which consumes `0x10000000`
   ([Chakra and guard](chakra_and_guard.md#guard-input-and-action-lifecycle));
2. `chakra_staged_gate` for Triangle `0x08000000`;
3. `action_rewrite_logical_mask`, which handles `0x00040000`: if `section`
   differs from fighter halfword `+0x324` it becomes `0x00020000`
   (selecting the slot-19 variant); otherwise an accepted current-action
   transition consumes it through `action_consume_binding2_route`;
4. `action_select_from_signature`;
5. the Cross family's parallel consumers: `jump_request` for `0x00010000`
   ([jump requests](../stages/movement_and_physics.md#jump-requests-and-state-selection))
   and `section_transfer_request` for the Up/Down modifiers
   ([Section transfers](../stages/section_transfers.md#input-order-and-selected-action)).

The complete per-fighter order is owned by
[Combat action execution](combat_action_execution.md#ordinary-dispatch-order).
`fighter_update_movement_slot` also runs the bridge and selection during an
update pause. Direction bits `0x4/0x8` also feed `awakened_vertical_input`
([Awakening](../characters/awakening.md#resident-ownership-and-the-btl-boundary)).

## Action signature

`action_select_from_signature` requires a bit in `0x0003F000`, no queued
chain, a non-negative `action_selector_mode`, a zero
`paired_binding1_intercept`, and `action_entry_allowed`. With a queued chain
it continues that chain instead (`action_queue_dispatch`).

| Logical | Signature |
| ---: | ---: |
| `0x00001000` | `0x00100000` |
| `0x00002000` | `0x00400000` |
| `0x00004000` | `0x00800000` |
| `0x00008000` | none; passes the entry gate |
| `0x00010000` | `0x01000000`, or `0x02000000` with `0x00020000` |
| `0x01000000` | `0x10000000` |
| `0x10/0x20/0x40/0x80` | `0x200/0x400/0x1000/0x2000` |
| `0x100/0x200` | `0x4000/0x8000` |
| `0x400/0x800` | `0x10000/0x20000`, replacing direction context |

Priorities: the action family is the first present of `0x1000`, `0x10000`,
`0x01000000`, `0x2000`, `0x4000`. Direction bits choose the first of
`0x10..0x80`, then `0x100` before `0x200`. A double-tap (`0x400` before
`0x800`) replaces all direction context and resets mode 1 to mode 0. In modes
2 and 3 only `0x40` is considered, as `0x1000`, and double-taps are ignored.

Context bits come first: `0x4` or `0x2` from grounded/airborne state, then
one of `0x20`, `0x40` (vertical centers within 150) or `0x80` from the
opponent's height. When `0x2000` is present a lookup for category `0x41` or
`0x42` can replace it with `0x1000` under a threshold comparison.

## Selector modes and entry gates

`action_selector_mode`:

| Fighter state | Mode |
| --- | --- |
| effect 0 or 1 attached | 0 |
| no exchange role | 1 for a major-8 record in the mode-1 group with a chainable payload, else 0 |
| role `0x100`, `0x400` or `0x1000` (in that priority) | 2, 3, 2, if no pending action and the opposite fighter's window progress is valid; else -1 |
| other role | 0 |

The successful `0x100` branch clears the action lock, so mode calculation can
change state even when selection then fails. Roles are written by Extra Hit
([Extra Hit](extra_hit.md#exchange-state-at-fighter-0xb00)); the window
interval is not decremented and survives teardown, but the role and pending
gates come first.

`action_entry_allowed` rejects everything while the action lock is nonzero.
Otherwise:

| Major | Accepted |
| ---: | --- |
| 0 | substates 0, 3, 4, 5, 7 |
| 1 | substates `0x0E..0x14` |
| 2, 3, 4 | all |
| 5 | `0x5B`, `0x5C`, or mode 2 |
| 6 | `0x60` from cursor 3, `0x5F` from cursor 8 |
| 8 | current record not in category `0xC0000` |

Cursor bounds count the action timeline, not history samples.

## Action selection

`action_select_record` runs, in order:

1. `action_scan_jutsu_slots`, when chakra is staged: the highest matching slot
   4..9 with jutsu category and affordable cost. During major 8 the match is
   staged in `pending_action` instead and selection continues.
2. Signature `0x02000000` tests only slot 19 (`action_slot19_allowed`).
3. Mode 0: the ordinary ascending scan, excluding categories `0x2`, `0xF000`
   and `0xF00000`; continuation must be -1 or -2. During major 8 a match
   whose continuation equals `current_action` is staged instead.
4. Modes 1..3, only with nothing pending: `action_stage_chain_slot` stages the
   first qualifying slot 10..18.

Matching normalizes the signature by the candidate and then requires
equality:

| Candidate signature | Constructed signature rewrite |
| --- | --- |
| bit `0x1` | bits `0xF` become `0x1` |
| bit `0x10` | bits `0xF0` become `0x10` |
| bit `0x100` | bits `0xFFF00` become `0x100` |
| any of `0x3000` | clear `0xC000` |
| any of `0xC000` | clear `0x3000` |
| `0x200000` with constructed `0x100000` | swap to `0x200000` |

`action_validate_candidate` returning zero clears signature bits `0xF0000`
and retries; any other result reaches `action_dispatch_index`, which accepts
1 and -1 and runs `action_prepare_companion` for 2 and 3. Dispatch ends in
`fighter_set_action_state(fighter, 8, index, mode)`
([Combat action execution](combat_action_execution.md#action-entry-and-state-ownership)).

### Pending-action rules

`pending_action` is one signed halfword, not a queue. Ordinary and jutsu
staging overwrite it; the chain scan and modes 2/3 require it empty. A jutsu
match therefore blocks a mode-1 chain but can be overwritten by a mode-0
match. `special_admission` rejects any exchange role, so jutsu staging never
competes with modes 2/3. No age or expiry is attached; execution and cleanup
belong to
[Combat action execution](combat_action_execution.md#continuation-and-common-exit-decisions).

Other pending writers:

| Writer | Effect |
| --- | --- |
| `fighter_init`, `action_entry_cleanup` | clear |
| `action_queue_set`, `action_queue_dispatch` | Battle AI direct chain ([Battle AI](../session/battle_ai.md#action-record-selection-and-direct-queues)) |
| `action_stage_exchange_candidate` | AI staging by full-mask match; its five calls are in AI states 12, 13 (two), 19 and the main reaction stage |
| `chakra_cancel_stage` | clears a jutsu-category pending action |
| `fighter_attached_object_update` | clears in its attached-object branch |
| `paired_state_update` | state 7 clears the other fighter's pending action |
| `action_consume_binding2_route`, `action_exit_clear_pending` | clear after their action exit |
| `action_stage_outcome_continuation` | stages an outcome continuation |
| `exchange_receiver_update` | discards or consumes at the exchange limit |
| `lee_loopy_channel3` | replaces 0x22's pending companion with 0x23 when unaffordable |

`action_find_by_masks` requires all requested category and secondary bits,
unlike the chain scan's nonempty intersections; it is AI selection and must
not be equated with input modes 2/3.

### Chain masks

`action_build_chain_masks` runs for each candidate slot 10..18; a slot needs
a nonempty intersection with both masks.

| Mode / current record | Category mask | Secondary mask |
| --- | ---: | --- |
| 1, record present | `0x1000` | current `0x380` group `0x80/0x100/0x200` becomes `0x400/0x800/0x1000` |
| 1, none | 0 | 0 |
| 2/3, none | `0x2000` | opponent's current `0x1C00` group, if its low exchange byte is set |
| 2/3, current group `0x1000`/`0x2000` | `0x2000` if `prng_inclusive(3)` is 0, else `0x4000` | current `0x1C00` group |
| 2/3, current group `0x4000` | `0x4000` if 0, else `0x2000` | same |
| 2/3, other | `0x4000` | same |

The random draw repeats for every candidate. Modes 2/3 drop the `0xFFF00`
group from both signatures when the candidate uses it. Mode 1 rewrites
category `0x200`/secondary `0x80` requests by window progress (at least 0.75)
and side.

## Working action arrays

`fighter_load_character_record` points `actions` at the fighter's writable
array (constructors such as `naruto_classic_construct` redirect it there), and
`actions_setup_working_array` fills it:

- records 0..3 come from the two configured jutsu selectors: selector 1 copies
  `null_action_record`; otherwise `jutsu_selector_character` picks the source
  character and moving a pair shifts continuations by two and rewrites the
  `0xF0000` direction group;
- records 4.. come from the default array; among 4..9 only the slot chosen by
  `jutsu_slot_config` (0..2 → 4..6, 4..6 → 7..9) keeps its category and gets a
  configured display name, the others lose their category.

Later `jutsu_slots_rewrite` rewrites category, name and cost of 4..9
([Ultimate Jutsu](../characters/ultimate_jutsu.md)); `actions_resolve_rows`
and `actions_resolve_thresholds` convert row indices and threshold sentinels.
Selection therefore runs on values that can differ from the shipped arrays.

Twelve character callbacks change record `flags` after setup (bounded screen of
the callback slots of all 78 definitions; see the channel-3 and response
annotations of IDs 40, 48, 58, 64, 66, 67, 69, 76 and 84). Bitwise updates keep
the `0x380` and `0x1C00` groups; the whole-word restores of IDs 64 (action
`0x17`) and 76 (action `0x1E`) zero the `0x1C00` group, and ID 64's restores
mode-1 group `0x100`. ID 67 also rewrites embedded records that are not
current. Callback installation is owned by
[Character action callbacks](../characters/character_action_callbacks.md#complete-bounded-classslot-census).

## Static action data

`character_definition_table` has 78 distinct definitions with 3,444 records:
four auxiliary definitions (IDs 26, 29, 30, 31) with four records, and 74
fighters with 37..62. Every debug name is empty; display names are 1,064
distinct strings. Shared fields of all 74 fighters:

| Slot | Category | Signature | Continuation | Cost |
| ---: | ---: | ---: | ---: | ---: |
| 7 | `0x00100000` | `0x00100112` | -2 | 5 |
| 8 | `0x00200000` | `0x00100112` | -2 | 10 |
| 9 | `0x00400000` | `0x00100112` | -2 | 15 |
| 10 | `0x00001000` | `0x00101011` | -2 | 0 |
| 11 | `0x00001000` | `0x00100211` | -2 | 0 |
| 12 | `0x00001000` | `0x00100411` | -2 | 0 |
| 13..15 | `0x00002000` | `0x00101011` | -2 | 0 |
| 16..18 | `0x00004000` | `0x00101011` | -2 | 0 |
| 19 | `0x00000002` | `0x02000011` | -1 | 0 |
| 20 | `0x04000000` | `0x02000011` | -1 | 0 |

Exceptions: slots 4/5 match 7/8 but have category zero for IDs 47..52, 54,
55, 56 and 73; slot 6 is like 9 with signature `0x00100111` for IDs 19, 48
and 61. Slot 21 is category 1, signature `0x00100012`, continuation -1, except
ID 53 (signature `0x00100212`) and ID 70 (category 0, signature `0x00110012`,
continuation -2).

From slot 20 on, signature families are `0x00100000` (1,627 records),
`0x08000000` (209), `0x02000000` (74), `0x00200000` (16), `0x00400000` (11) and
`0x00800000` (11). The hold/release families occur only in IDs 40, 48, 53 (three
pairs), 54, 57, 64, 77, 84 and 85. The `0x08000000` family is not produced by
the direct input mapping.

Named examples (display text without reading markup):

| Character / slot | Signature | Continuation | Name |
| --- | ---: | ---: | --- |
| Naruto (57) / 24 | `0x00100211` | 23 | 飛影昇撃 |
| Naruto / 25 | `0x00104011` | 23 | 特攻蹴撃 |
| Naruto / 35 | `0x00800112` | 34 | 風魔追撃 |
| Kazekage Gaara (59) / 44 | `0x00100012` | -1 | 漠撃・圧葬 |
| Kazekage Gaara / 45 | `0x00100212` | -1 | 漠撃・滅葬 |
| Kazekage Gaara / 46 | `0x00104012` | -1 | 漠撃・天葬 |
| Kazekage Gaara / 47 | `0x00100412` | -1 | 豪砂甚雨 |
| Deidara (64) / 29 | `0x00800112` | 28 | 起爆粘土・蜘蛛 |
| Deidara / 42 | `0x00100012` | -1 | 起爆粘土・蜘蛛 |
| Deidara / 43 | `0x00100212` | -1 | 大型鳥粘土・翔 |
| Deidara / 44 | `0x00100412` | -1 | 大型鳥粘土・襲 |
| Deidara / 45 | `0x00104012` | -1 | 大型鳥粘土・突 |

All are category 1 except Naruto 35 and Deidara 29 (category `0x10`). The
Gaara and Deidara alternatives are switched by their variant routines
([Awakening](../characters/awakening.md#deidara-and-gaara-character-variants)).
Character records are owned by
[Character assets](../../game/character_assets.md#character-records). The
Command List and move chart read the working arrays but take no part in
selection.

## Representative paths

- Ordinary attack: a Circle press gives logical `0x00001000`, signature
  `0x00100000`, and in mode 0 the ordinary scan picks the character's first
  matching record.
- Jutsu: a Triangle press stages chakra through `chakra_staged_gate`; a later
  Circle press reaches `action_scan_jutsu_slots`, which picks the highest
  affordable matching slot 4..9 before the ordinary scan. Jutsu is a
  staged-state path, not a hidden `ccCommand` sequence.
