# Battle status effects and item-effect lifecycle

This document records the retail NA2 (`SLPS-25837`) resident status-effect
system and the BTL callers that apply it. It covers definition records, per-fighter storage,
application and replacement, countdown normalization, expiry and removal,
item-driven effects, and the boundary between gameplay state and battle UI.

The findings are static unless explicitly stated otherwise. Numeric effect and
item IDs are kept numeric where no gameplay consumer proves a semantic name.
UI labels and nearby class names are not treated as proof of gameplay meaning.
Related presentation behavior is documented in
[`localization/ui/battle/item_status.md`](../../localization/ui/battle/item_status.md).
Binary identities and address conventions are defined in
[Standard game file identities](../../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Retail NA2 (`SLPS-25837`) battle status effects and item
  effects: definitions, per-fighter storage, application, countdown behavior,
  replacement, coexistence, expiry, removal, item-driven provenance, and the
  boundary between gameplay state and status presentation.
- **Exploration depth:** Static and direct-call coverage is exhaustive for:
  - all 138 effect-definition records, their categories, countdowns, flags,
    presentation selectors, display descriptors, and 19 specialized
    constructors;
  - the generic resident lifecycle, both per-fighter lists, every registered
    specialized constructor and destructor, callback return behavior, bulk
    cleanup calls, direct exact-ID removals, the payload-reducer family, all
    signed entry and zero-exit resource fields, and five action-facing
    membership policies with their direct consumers;
  - every direct resident and BTL call to the high-level application function,
    separating literal requests from tables, wrappers, routing, and dynamic
    arguments;
  - all 116 item-metadata records, every direct-effect field, every BTL
    object-definition leading code, and the pickup, hit-carried, and
    three-slot status-dispatch paths that consume them;
  - the complete 19-row three-slot status table, its effect lanes, unread
    interleaved words, recovery branches, and NUN5 comparison; and
  - the effect-to-notification and auxiliary visual-selector maps, Fukidasi
    factory dispatch, authored UI record maps, and their list lifecycles.

  Effect `4A`'s callbacks and destructor, the phase-2 secondary-callback
  caller, the native form save/restore helpers, and the random status/resource
  branch in `FUN_0025CEE0` were read completely. Surrounding character and
  battle-controller state machines were sampled only where needed to establish
  status-facing behavior.
- **Confirmed coverage:** Binary and address identities; definition, fighter,
  node, auxiliary, and notification layouts; same-ID replacement; different-ID
  coexistence; sentinel and zero-countdown behavior; normalization and gated
  expiry; removal and cleanup order; linked/local routing; direct item/effect
  mappings; item `0x5B`'s dual path; effect `0x22`'s successor; and the
  separation of gameplay membership from caches, inventory, auxiliary visuals,
  and notifications. Payload combination distinguishes additive factors,
  maxima, net signed deltas with strict boundary gates, and direct field
  writes. Entry and ordinary-expiry resource deltas, effect-`0B`'s membership
  veto, phase-2 secondary callbacks, pre-expiry rate sampling, and the native
  form/inventory retention boundary are established. The random callback's
  five cursor cases, nested RNG bounds, no-action lane, and separate status/HP
  requests are established without naming its native action.
- **Unresolved or untested:** User-facing meanings for most effect IDs and
  removal reasons; gameplay names for remaining numeric payload fields and
  fighter `+0x158`; wider meaning of the paired BTL pointer lanes selected by
  `00307920`; the consumer of the `0x65/0x12` interleaved pair; whether one
  pickup reaches both the resident and BTL pickup sites; ordinary-runtime
  reachability of the six-code selected-use fallback; indirect or dynamically
  constructed calls; and most surrounding character-specific state machines.
- **Deliberate exclusions and overlap:** Status UI is covered only to establish
  its mapping and lifetime boundary with gameplay; rendering, media, and
  localization semantics are excluded. Linked owners hold the related
  contracts: [Battle item inventory](battle_item_inventory.md) owns the panel,
  selection, use admission, slot consumption, and
  [random field-item selection](battle_item_inventory.md#random-field-item-selection);
  [Match outcomes](../session/battle_statistics.md#ninja-tools-and-stage-objects) owns the
  item-dispatch statistic credit;
  [Battle entities](../session/battle_entities.md#generic-intrusive-node-and-list-contracts)
  owns the generic BTL node and list contracts;
  [Character action callbacks](../characters/character_action_callbacks.md) owns character
  callback bodies; [Battle HUD](../session/battle_hud.md) and
  [Battle item-status presentation](../../localization/ui/battle/item_status.md)
  own HUD drawing and item-status labels;
  [Field-item names](../../localization/field_item_names.md) owns item names;
  [Damage](../combat/damage.md), [Chakra and guard](../combat/chakra_and_guard.md), and
  [Substitution](../characters/substitution.md) own their formulas and resource mutation;
  [Combat action execution](../combat/combat_action_execution.md) owns complete action
  machines; and [Awakening](../characters/awakening.md#state-retained-across-the-native-rebuild)
  owns form reconstruction. This document owns status membership and lifetime
  boundaries for those consumers.
- **Evidence limitations:** Findings are static retail-binary results; no
  gameplay execution, runtime trace, or empirical countdown timing was
  performed. Direct-JAL searches over the resident executable and BTL establish
  encoded direct calls, not indirect reachability; resident byte-mapped aliases
  repeat base-image matches rather than adding callsites. The NUN5 table is
  cross-game corroboration, not retail NA2 runtime evidence. Results for
  externally duplicated nodes, cleanup-time list mutation, and repeated
  replacement describe code paths rather than observed runtime behavior.
  Code `29`'s naming evidence is qualified in the
  [field-item name reference](../../localization/field_item_names.md#code-29-curse-tag-chakra-points-seal).

## Ownership summary

The resident executable owns gameplay effect definitions, nodes, application,
countdown updates, and cleanup. BTL and resident battle controllers supply
effect IDs and requested countdowns.

```text
BTL/resident source
    -> FUN_00305C30 high-level apply
    -> FUN_00306980 requested-countdown normalization
    -> FUN_00305270 replace/construct/append
    -> fighter +0x8C4 gameplay list

fighter update
    -> FUN_003059B0
    -> FUN_00304D60 per-node countdown/expiry
    -> FUN_00305040 unlink decision
    -> BTL live 0x00709EA0 unlink + virtual destructor
```

There are three distinct structures that must not be conflated:

1. gameplay nodes at fighter `+0x8C4/+0x8C8`;
2. auxiliary category-1/2 status visuals at fighter `+0x8D8/+0x8DC`;
3. short-lived Fukidasi/item notification objects in side-specific UI lists.

Inventory slot counts are a fourth, separate structure. Neither an inventory
count nor a visible notification establishes active gameplay-effect state.

## Resident effect definitions

### Definition table

The table at runtime `0x0059E2A0`, ELF file `0x49E3A0`, contains 138 records
for IDs `0x00..0x89`. Each record is `0x64` bytes; the complete range is runtime
`0x0059E2A0..0x005A1887`, file `0x49E3A0..0x4A1987`.

| Record offset | Proven role |
| ---: | --- |
| `+0x04` | Constructor pointer; populated at initialization for specialized IDs |
| `+0x08` | Effect ID copied to node `+0x68` |
| `+0x0C` | Base/default signed countdown copied to node `+0x6C` |
| `+0x10` | Routing and other flags copied to node `+0x70` |
| `+0x14..+0x58` | Parameter payload copied to node `+0x74..+0xB8` |
| `+0x5C` | Optional status-display descriptor pointer used by `FUN_00226370` |
| `+0x60` | Presentation-object implementation selector returned by `FUN_003048C0` |

`FUN_00304910` at runtime/file `0x00304910/0x204A10` constructs a generic
`0xC0`-byte node and copies the record. Some payload fields have immediate
entry/exit actions:

- record `+0x3C` / node `+0x9C`, when nonzero, is passed to
  `FUN_00306090` (`0x00306090/0x206190`) on entry. Its second argument is
  `-1.0` for a positive value and `0.1` for a negative value;
- record `+0x44` / node `+0xA4`, when nonzero, is passed to
  `FUN_00306220` (`0x00306220/0x206320`) with second argument `-1.0` on
  entry;
- record `+0x28` / node `+0x88`, when not the neutral `1.0`, first causes
  `FUN_001D87C0(0x2E, owner+0x30)` and then
  `FUN_00226E90(value,10.0,45.0,0.125,owner)` on entry. Those helpers are at
  `0x001D87C0/0x0D88C0` and `0x00226E90/0x126F90`;
- zero-countdown helper `FUN_00304E90` (`0x00304E90/0x204F90`) consumes
  record `+0x40` / node `+0xA0` through `FUN_00306090` using the same
  sign-dependent second argument, and record `+0x48` / node `+0xA8` through
  `FUN_00306220(value,-1.0,owner)`;
- generic destructor hook `FUN_00304C20` (`0x00304C20/0x204D20`) restores a
  non-neutral node `+0x88` to `1.0`. Natural reason `0` repeats the event call
  and uses `FUN_00226E90(1.0,10.0,45.0,0.125,owner)`; a forced reason uses
  `FUN_00226E90(1.0,0,0,0,owner)` instead. For natural reason `0`, categories
  `1..4` also call `FUN_00204450(owner,0x0B)`
  (`0x00204450/0x104550`); category `0` does not.

The resource consumers identify node `+0x9C/+0xA0` as signed HP deltas and
`+0xA4/+0xA8` as signed chakra deltas. Their mutation and resource gates belong
to [Damage](../combat/damage.md#damage-application) and
[Chakra and guard](../combat/chakra_and_guard.md#gain-and-clamp-behavior). The remaining
payload consumers and their different combination rules are recorded below;
numeric fields without a proven gameplay name remain numeric.

`FUN_003048C0` at runtime/file `0x003048C0/0x2049C0` returns definition
`+0x60` (`5` for the special input `-1`). `FUN_00331290` at
`0x00331290/0x231390` uses it for category-`1..3` effects, and for ID `0x89`,
to select among concrete presentation-object constructors. This selector is
orthogonal to the five gameplay categories. Representative exceptional
selectors are ID `0x3C -> 14`, `0x72 -> 15`, and `0x55 -> 16`; the clean table
contains selector values `0,1,2,3,4,5,6,9,11..16`. No gameplay stacking or
countdown rule should be inferred from that presentation selector.

The complete selector distribution is:

| Selector | Effect IDs |
| ---: | --- |
| `0` | `12,15,17,18,30,31,42,52,58,59,61,62,63,66,89` |
| `1` | `00..0D,13,14,19,1A,1B,1C,1E,20,21,24,25,35,36,37,3A,3B,3D,3F,41,43,4C,4D,4E,4F,54,56,57,6A,6C,73..88` |
| `2` | `0E,39,40,50,5B,5C,65,68,6B` |
| `3` | `11,46,67` |
| `4` | `0F,27..2B,38,4A,5D,69,6D..71` |
| `5` | `23` |
| `6` | `16,1F,3E,49,4B,53,64` |
| `9` | `10,22,26,2C..2F,44,45,47,48,5A,5E,5F,60` |
| `11` | `1D,51` |
| `12` | `32` |
| `13` | `33,34` |
| `14` | `3C` |
| `15` | `72` |
| `16` | `55` |

Only IDs `0x00..0x0C`, `0x23`, and `0x75..0x77` have non-null definition
`+0x5C` descriptors. The descriptor pool is runtime/file
`0x0059E190..0x0059E29F / 0x49E290..0x49E39F`, with this proven layout:

| Offset | Role in `FUN_00226370` |
| ---: | --- |
| `+0x00` | Resource/style word copied to fighter `+0x8F4` |
| `+0x04` | Float upper bound for fighter `+0x8F0` |
| `+0x08` | Float delta installed at the lower bound |
| `+0x0C` | Float delta installed at the upper bound |

The low IDs mostly use upper bound `40`, lower delta `4`, and upper delta
`-0.5`; ID `0x08` instead uses `40/1/-1`. IDs `0x23` and `0x75..0x77` use
`60/4/-1`. These records drive display oscillation and styling, not gameplay
duration.

Their exact style words and parameter groups are:

| Effect IDs | Descriptor `+0x00` word | Upper / lower delta / upper delta |
| --- | ---: | --- |
| `00,01` | `0000E0E0` | `40 / 4 / -0.5` |
| `02` | `000000E0` | `40 / 4 / -0.5` |
| `03` | `00C0C0C0` | `40 / 4 / -0.5` |
| `04` | `00B02020` | `40 / 4 / -0.5` |
| `05` | `00E0E020` | `40 / 4 / -0.5` |
| `06` | `00C02020` | `40 / 4 / -0.5` |
| `07` | `00C020C0` | `40 / 4 / -0.5` |
| `08` | `00010101` | `40 / 1 / -1` |
| `09..0C` | `00C0C0C0` | `40 / 4 / -0.5` |
| `23,75,76,77` | `00202020` | `60 / 4 / -1` |

### Categories

`FUN_003047C0` at runtime/file `0x003047C0/0x2048C0` classifies IDs exactly:

| Effect IDs | Category |
| --- | ---: |
| `0x00..0x0D` | `0` |
| `0x0E..0x64` | `1` |
| `0x65..0x67` | `2` |
| `0x68..0x73` | `3` |
| `0x74..0x89` | `4` |
| Outside `0x00..0x89` | invalid / `-1` |

Categories are control-flow classes, not semantic names. Categories `1..3`
bypass one fighter-state application gate. Categories `1` and `2`, but not
`3`, also allocate an auxiliary status-visual object after successful
construction.

### Routing flags

When the fourth argument to `FUN_00305C30` is nonzero:

- mask `0x04` recursively routes the same request to the linked fighter at
  fighter `+0x20`, using route argument `0`;
- if mask `0x02` is absent, local application then stops;
- mask `0x02` therefore permits local application.

The observed routing forms are `0x02` local, `0x04` linked-only, and `0x06`
linked plus local. Definition ID `0x7D` has flags `0x06`; IDs `0x7E..0x89`
have `0x04`. All earlier IDs retain local mask `0x02`. IDs `0x0A/0x7C` carry
additional bits `0x70`, while `0x0B`, `0x0E`, `0x0F`, `0x21`, `0x27..0x2B`,
and `0x38` carry additional bit `0x80`.

The non-routing bits have proven presence-query consumers:

| Flag bit | Predicate | Runtime / file |
| ---: | --- | --- |
| `0x10` | `FUN_003073A0(fighter)` | `0x003073A0/0x2074A0` |
| `0x20` | `FUN_00307410(fighter)` | `0x00307410/0x207510` |
| `0x40` | `FUN_00307480(fighter)` | `0x00307480/0x207580` |
| `0x80` | `FUN_003074F0(fighter)` | `0x003074F0/0x2075F0` |

Each scans the gameplay list and returns true on the first node whose
countdown is nonzero and whose copied flags contain its bit. Negative
sentinels therefore count as active, while a pending-expiry zero node does
not. The helpers are used as distinct higher-level condition gates, but their
user-facing/gameplay names remain unresolved; `0x10`, `0x20`, and `0x40`
happen to be co-authored on the same two clean definitions and should not be
collapsed merely because this table does not separate them.

The action-facing distinction is established by `FUN_00244190`
(`0x00244190/0x144290`), which validates a candidate from fighter action
array `+0xA54`. Its call at `0x00244314/0x144414` rejects the candidate with
return `0` when an active node has flag `0x20`, before checking cost and
before the insufficient-resource feedback branch. The subsequent nonzero-cost
branch checks flag `0x40` and current chakra. Thus `0x20` suppresses this
candidate-validation path, while `0x40` suppresses its affordability check.
Both are authored on IDs `0A/7C`; that coincidence does not merge their
consumers. Candidate selection and dispatch belong to
[Action commands](../combat/action_commands.md#working-action-arrays), and
resource gating belongs to [Chakra and guard](../combat/chakra_and_guard.md#spend-affordability-and-lower-clamp).

Routing is not transactional. `FUN_00305C30` returns `void`; when bit `0x04`
is set it invokes the linked fighter first with route argument zero and does
not receive or test a success result. A linked-only definition then returns
without attempting local construction. A linked-plus-local definition proceeds
to an independent local construction. Thus either fighter can accept the
effect while the other rejects it, for example because only one already has a
same-ID `-2` node. A successful first application is never rolled back after a
later failure, and each successful invocation performs its own notification,
auxiliary-object, and cache side effects.

### Base countdowns

These are record inputs, not seconds or frames. The outer update is gated,
some low IDs are normalized by a fighter field, and IDs `0/1` can consume
additional countdown on an allowed tick.

| Base countdown | Count | IDs or scope |
| ---: | ---: | --- |
| `-1` | 36 | `17,39,4C,4E,68..78,7B..89` |
| `30` | 2 | `79,7A` |
| `240` | 4 | `05,06,09,0D` |
| `300` | 9 | `00,01,02,03,04,07,08,0B,3C` |
| `450` | 7 | `0A,0C,23,26,48,4A,5E` |
| `600` | 77 | all other finite records |
| `900` | 1 | `4F` |
| `1200` | 2 | `1A,1B` |

No definition defaults to `-2`.

### Specialized constructors

The registry at runtime/file `0x0059E0F0/0x49E1F0` contains 19
ID/constructor pairs followed by `-1`. `FUN_00305470` at
`0x00305470/0x205570` installs these pointers into record `+0x04`; the clean
definition slots themselves are initially zero. The terminator record starts
at runtime/file `0x0059E188/0x49E288`, and the complete registry allocation
ends at `0x0059E18F/0x49E28F` immediately before the descriptor pool.

| ID | Original class | Constructor VA |
| ---: | --- | ---: |
| `0E` | `ccPlConSpl01` | `FUN_002509E0` |
| `0F` | `ccPlConSpl02A` | `FUN_00253A30` |
| `10` | `ccPlConSpl03` | `FUN_00254520` |
| `12` | `ccPlConSpl06` | `FUN_00258CD0` |
| `17` | `ccPlConSpl12` | `FUN_0025CAE0` |
| `19` | `ccPlConSpl13` | `FUN_0025D7C0` |
| `1A` | `ccPlConSpl14` | `FUN_0025EB20` |
| `1D` | `ccPlConSpl17` | `FUN_002634A0` |
| `22` | `ccPlConSpl25A` | `FUN_00303720` |
| `23` | `ccPlConSpl25B` | `FUN_00303890` |
| `39` | `ccPlConSpl57` | `FUN_00295BA0` |
| `42` | `ccPlConSpl65` | `FUN_002B70C0` |
| `44,45` | `ccPlConSpl67` | `FUN_002BCAC0` |
| `47,48` | `ccPlConSpl69` | `FUN_002C1A00` |
| `4A` | `ccPlConSpl71` | `FUN_002C8420` |
| `54` | `ccPlConSpl81` | `FUN_002E8650` |
| `7D` | `ccPlConMsnGrv` | `FUN_00303F00` |

### Specialized entry, exit, and callback behavior

Virtual destructors run for timeout, explicit removal, same-ID replacement,
and hard cleanup, so the following exit actions are not timeout-specific:

- Effects `0x0E`, `0x0F`, and `0x10` conditionally call
  `FUN_00215F10` for owner fighter IDs `1`, `2`, and `3`, respectively.
  Effect `0x39` does the same for owner ID `0x39`; effects `0x44/0x45` share
  the check for owner ID `0x43`; effects `0x47/0x48` share the check for owner
  ID `0x45`. The matched constructors set fighter byte `+0x60` bit `3`,
  reload material/resource bindings, and notify the BTL manager. Their virtual
  destructors conditionally call `FUN_00216010`, which clears the bit and
  reloads/notifies. The helpers are runtime/file
  `0x00215F10/0x116010` and `0x00216010/0x116110`.
- Effects `0x12`, `0x17`, and `0x42` call `FUN_003076C0(owner)` on entry and
  `FUN_00307700(owner)` on destruction. Those helpers, runtime/file
  `0x003076C0/0x2077C0` and `0x00307700/0x207800`, call the BTL manager with
  the fighter side and value `1` or `0`. The absolute BTL target is live
  `0x0076ECC0` (file `0xBADC0`, preserved `0x0076EC80`). This is a paired
  manager/presentation toggle, not gameplay-list ownership.
- Effect `0x19` slot-`+0x10` callback `FUN_0025D8F0`
  (`0x0025D8F0/0x15D9F0`) and effect `0x1D` callback `FUN_002635D0`
  (`0x002635D0/0x1636D0`) each call
  `FUN_00237530(owner,1)` and then return zero. Effects `0x1A` and `0x54`
  have more conditional action callbacks at `FUN_0025EC50` and
  `FUN_002E8880`; those also return zero on every path.
- Effect `0x4A` allocates a larger `0xE0`-byte node with two owned
  `0x40`-byte objects at node `+0xC4/+0xC8` and private state at
  `+0xC0/+0xD0..+0xDC`. Its slot-`+0x10` callback `FUN_002C8690`
  (`0x002C8690/0x1C8790`) conditionally writes owner and linked-fighter
  field `+0x1B4` and performs linked-fighter actions, but returns zero. It is
  also the only registered effect whose slot `+0x14` is specialized
  (`FUN_002C8900`, `0x002C8900/0x1C8A00`). Destructor `FUN_002C8580`
  (`0x002C8580/0x1C8680`) restores both `+0x1B4` fields to `1.0` and frees
  the two owned objects before generic cleanup.
- Effect `0x7D` entry `FUN_00303F60` (`0x00303F60/0x204060`) writes owner
  fields `+0xF8 = 0.5`, `+0xFC = 2.5`, and halves floats
  `+0x100/+0x104/+0x108`. Its slot-`+0x10` callback `FUN_00304070`
  (`0x00304070/0x204170`) clamps or drives several owner motion/state fields
  and returns zero. Its specialized destructor `FUN_00303FE0`
  (`0x00303FE0/0x2040E0`) performs only generic node cleanup; no paired
  restoration of those five constructor-written fields was found. Because
  the default `-1` node remains replaceable, same-ID application destroys the
  old node and then halves the already modified `+0x100/+0x104/+0x108`
  values again. Reason-`5` removal likewise leaves those constructor writes in
  place. Definition flags `0x06` perform this independently on linked and
  local fighters. External state-reset code could later overwrite the fields,
  but no inverse exists in this effect class itself.

Every other registered slot-`+0x10` implementation is a literal zero-return
or another side-effecting zero-return callback, so callback return is not an
expiry mechanism for any registered gameplay effect.

Two character-specific controllers also prove caller-managed lifetime:

- `FUN_002E8DC0` removes effect `0x54` with reason `1` at
  runtime/file callsite `0x002E8E30/0x1E8F30` after membership and three
  additional state predicates succeed. `FUN_002E99A0` independently removes
  the same effect with reason `1` at `0x002E9A4C/0x1E9B4C` when its compound
  validity check fails or fighter `+0xB00/+0xB10` is nonzero. Both paths also
  clear fighter byte `+0x63` bit `5` and reset associated presentation state.
- `FUN_002F2D70`, restricted to fighter ID `0x57`, edge-detects fighter byte
  `+0x63` bit `5` against cached `s16 +0x5626`. A rising edge applies effect
  `0x09` with requested countdown `9999` and route `1` at
  `0x002F2DF0/0x1F2EF0`; a falling edge removes effect `0x09` with reason `1`
  at `0x002F2E20/0x1F2F20`. Effect `0x09` is a low normalized ID, so `9999`
  is still a requested rather than guaranteed stored countdown.

These are explicit cancellation/toggle policies layered above the generic
countdown and replacement logic; their numeric evidence does not establish
user-facing effect names. The surrounding character callback bodies belong to
[Character action callbacks](../characters/character_action_callbacks.md);
`FUN_002F2D70` is the fighter-`0x57` channel-2 callback listed with its rate
write in [Other direct rate-writer families](../characters/character_action_callbacks.md#other-direct-rate-writer-families).

## Concurrent payload contributions

Resident helpers `0x00306BD0..0x00307398` read gameplay nodes directly. Their
common active test is `node +0x6C != 0`; they include negative sentinels and
exclude pending-expiry zero nodes. They do not consult the display choice,
last-success cache, or awakening controller marker. Different IDs therefore
contribute independently of which status is currently shown.

| Node / definition field | Consumer, runtime / ELF file | Combination of active nodes |
| --- | --- | --- |
| `+0x74 / +0x14`, `+0x78 / +0x18` | `00306BD0/206CD0`, `00306C80/206D80` | Attack and defense folds; their sums, clamps, inversion, and damage consumers belong to [Damage](../combat/damage.md#calculator-formula) |
| `+0x7C / +0x1C` | `00306D30/206E30` | Starts at `1`; adds each value minus `1`; caps at `1.25`; can then return neutral `1` under state gates |
| `+0x80 / +0x20` | `00306E80/206F80` | Starts at `1`; adds each value minus `1`; no local clamp; jump-height consumer belongs to [Movement and physics](../stages/movement_and_physics.md#jump-impulses-and-aerial-control) |
| `+0x84 / +0x24` | `00307320/207420` | Starts at `1`; adds each value minus `1`; no local clamp; representative response consumer belongs to [Hit response](../combat/hit_response.md) |
| `+0x8C / +0x2C` | `00307140/207240` | HP-recovery factor: starts at `1`; adds each value minus `1`; no local clamp |
| `+0x90 / +0x30` | `003071C0/2072C0` | Maximum positive value, starting at `0`; guard-damage consumer belongs to [Damage](../combat/damage.md#guarded-hit-damage) |
| `+0x94 / +0x34` | `00307230/207330` | Recovery fold; its resource consumer belongs to [Chakra and guard](../combat/chakra_and_guard.md#gain-and-clamp-behavior) |
| `+0x98 / +0x38` | `003072B0/2073B0` | Hit-related chakra-debit factor: maximum positive value, starting at `0` |
| `+0xAC,+0xB0 / +0x4C,+0x50` | `00306F00/207000` | Signed HP sum with aggregate boundary gate |
| `+0xB4,+0xB8 / +0x54,+0x58` | `00307020/207120` | Signed chakra sum with aggregate boundary gate |

Both maximum helpers return their result in `f0`. At `0x003071F0..0x00307200` and
`0x003072E0..0x003072F0`, `c.lt.s` replaces that register only when the next
payload is larger. Thus those fields select an extremum rather than adding
the effects. The complete clean definition table supplies these exceptional
values:

| Node field | Effect IDs and authored values |
| --- | --- |
| `+0x8C` | `77: 0.5`; every other record is neutral `1` |
| `+0x90` | `16,48: 0.5`; `35,5A: 0.25`; every other record is `0` |
| `+0x98` | `12,42,4B: 0.05`; `17,31,52: 0.15`; `18,89: 0.1`; every other record is `0` |

Values such as `0.05` and `0.1` are stored as their nearest single-precision
representation. HP-recovery scaler `FUN_00224DF0` multiplies its input by the
selected source fighter's `+0x160` and the receiving fighter's `+0x8C` fold;
instructions `0x00224DFC..0x00224E18` pass the receiving fighter to the fold. The immediate-item
dispatcher also applies this fold directly before its flag-`0x20` HP branch.
Effect `77` therefore halves those scaled recovery requests when it is the
only non-neutral contributor. It does not halve all direct HP entry deltas:
`FUN_00306090` calls the HP adder directly, bypassing this scaler.

Hit helper `FUN_0021E200` (`0x0021E200/0x11E300`) reads the `+0x98` maximum
from its receiving fighter's linked fighter, rejects specified action-record
flags, and requests a chakra debit on the receiver. Instructions
`0x0021E2F4..0x0021E34C` multiply the maximum by
`(signed_record_byte_2D % 5 + 1)` and the caller's scale, limit the request to
current chakra, and call `FUN_00225780` with bypass `0`. It performs no paired
chakra credit to the linked fighter. Canonical spend suppression still
applies. This proves the field's debit role and maximum-based coexistence,
without claiming that every hit or action record reaches this helper.

The `+0x7C` fold resets its non-neutral result to `1` if
`FUN_00244110(fighter)` is nonzero, if major state `+0x18E` is `5` or `6`, or
if that state is `8` and `FUN_002440C0(fighter)` is nonzero. This suppresses
the returned factor without deleting or changing the nodes. The response
threshold consumer and its additional limitations belong to
[Hit response](../combat/hit_response.md).

Its main maintenance consumer samples the fold before status expiry. In
`FUN_0024C440`, instructions `0x0024C46C..0x0024C49C` choose fighter
`+0x1B0` when it differs from `1`, otherwise call this fold, and store the
result to `+0x1AC`. Instructions `0x0024C4A0..0x0024C4C4` then multiply by
non-neutral `+0x1B4`. Only afterward, at `0x0024C4E8`, does the function call
the status update. A node on its final positive countdown can therefore
contribute to that update's already-sampled `+0x1AC`, then be removed by the
countdown pass. Likewise effect `4A`'s destructor can restore `+0x1B4`
without recomputing the stored `+0x1AC` in this prefix. This is a proven
sampling order, not an additional lifetime tick. Action-clock consumers of
`+0x1AC` belong to [Combat action execution](../combat/combat_action_execution.md#action-and-phase-clocks).

### Signed sums and their boundaries

For both signed-delta folds, each active nonzero delta contributes to one
sum. Positive-delta nodes also contribute their boundary to a maximum
starting at `0`; negative-delta nodes contribute their boundary to a minimum
starting at `1`. After summing, only the boundary for the **net sign** is
consulted:

- a positive sum becomes zero only when the current resource is strictly
  greater than the positive maximum;
- a negative sum becomes zero only when the current resource is strictly
  less than the negative minimum;
- a zero sum returns zero, regardless of boundaries.

The resource is fighter `+0x6C` for HP and `+0x70` for chakra. These are
whole-sum gates, not independent per-effect caps: opposing deltas cancel
before a boundary is selected, and equality permits the complete delta.
`FUN_003059B0` forwards a surviving sum with router boundary argument `-1.0`,
so the aggregate boundary does not trim a crossing to the authored limit.
Canonical resource clamps still apply. This explains code-level stacking and
boundary behavior without claiming measured update timing.

The clean HP records have positive boundaries `1.0` for effects
`22,25,26,3A,58,59,5E,87`, and negative boundaries approximately `0.1` for
`07,0F,10,27,28,29,2A,2B,38,44,45,47,48,49,4A,78,79`; all other HP delta
fields are zero. Chakra has negative deltas for
`0D,22,3A,3B,41,49,4A,54,5B,5C`, each with boundary `0`, and one positive
delta for `88`, approximately `0.05` with boundary `15.0`. Its downstream
gain/spend suppression is owned by
[Chakra and guard](../combat/chakra_and_guard.md#debit-and-reservation-behavior).

### Entry and ordinary-expiry resource deltas

The complete clean table has HP entry `+0x9C` approximately `+0.1` only for
effects `10` and `45`, and no nonzero HP zero-exit `+0xA0` field. Chakra entry
`+0xA4` is `+15.0` for `0E,0F,21,22,27,28,29,2A,2B,38,39`, `-15.0` for
`7A,7C`, and zero elsewhere. Chakra zero-exit `+0xA8` is `-15.0` only for
`0E,0F,27,28,29,2A,2B,38,7C`.

`FUN_00304E90` owns the zero-exit fields. Its direct caller is countdown
helper `FUN_00304D60`, after the countdown reaches zero. Generic destructor
`FUN_00304C20` does not call it and does not consume `+0xA0/+0xA8`.
Consequently, exact-ID removal, family switching, same-ID replacement, and
hard cleanup do not themselves apply these ordinary-expiry resource deltas.
Their virtual destructor actions still occur. This distinguishes an expiry
delta from an inverse action guaranteed on every removal; in particular,
replacing a still-positive node can repeat its entry delta without first
applying its authored zero-exit delta. Resource gates and clamps determine
the actual mutation, so repetition does not establish an uncapped gain.

### Direct field writes do not use the payload folds

Definition `+0x28` / node `+0x88` is an entry/exit target, not an active-list
reducer. The only non-neutral clean records are `1A: 1.5`, `54: 3.0`, and
`7B: 0.5`. Their generic entry calls `FUN_00226E90` with the chosen target.
The complete setter at runtime/file `0x00226E90/0x126F90` writes that target
to fighter `+0x2F4` and installs its interpolation fields; its all-zero timing
arguments branch instead writes the value directly to five fields
`+0x2E0/+0x2E4/+0x2E8/+0x2F0/+0x2F4` and clears the interpolation fields.
It neither scans active effects nor combines their targets.

Generic destruction of any one non-neutral `+0x88` node requests target `1`,
without checking whether another such node remains. Natural reason `0`
requests the timed transition; forced reasons request the direct five-field
write. Thus entry order and removal order own these shared target writes.
Different-ID list coexistence does not imply that their entry targets add or
that removing one restores a surviving node's target.

Effect `4A` has a separate pair of shared writes. Its primary callback
`FUN_002C8690` restores both fighters' `+0x1B4` to `1` on its distance/state
rejection branch, returns without modifying them for other nonzero `+0xB10`
states, or writes owner `0.75` and linked fighter `0.25` on its admitted
branch. Destructor `FUN_002C8580` writes both back to `1` without checking for
a surviving effect-`4A` node on either fighter. If both fighters have admitted
callbacks, each can overwrite the pair written by the other; no additive fold
or ownership count mediates those stores. Subsequent admitted callbacks may
write them again. Response and timeline consequences of those fields belong
to [Hit response](../combat/hit_response.md#timed-downed-recovery).
This is static shared-field behavior, not a claim about native frequency or
measured visible timing for the two-effect case.

## Per-fighter storage

The main embedded container is original class `ccPlConObjCtrl`, whose vtable
is runtime/file `0x005DA080/0x4DA180`. Generic effect nodes are original class
`ccPlConObj`, vtable `0x005DB1C0/0x4DB2C0`.

| Fighter offset | Proven role |
| ---: | --- |
| `+0x8C4` | Gameplay node count / embedded container base |
| `+0x8C8` | Gameplay list head |
| `+0x8CC` | Gameplay list tail |
| `+0x8D0` | Gameplay-container vtable |
| `+0x8D4` | Owning fighter pointer |
| `+0x8D8` | Auxiliary status-visual count |
| `+0x8DC` | Auxiliary list head |
| `+0x8E0` | Auxiliary list tail |
| `+0x8E4` | Auxiliary-container vtable |
| `+0x8E8` | `u16` last successfully applied effect-ID cache |
| `+0x8EC` | Float status-display delta |
| `+0x8F0` | Float current display phase/value |
| `+0x8F4` | Status-display resource/style word |

Removal does not clear `+0x8E8`. `FUN_003065A0` at
`0x003065A0/0x2066A0` rescans live list membership before honoring it. The
field is therefore stale-capable and is not authoritative active-effect state.
`FUN_00226370` selects a live status, reads definition `+0x5C`, and updates the
display trio; `FUN_00226900` consumes it in display setup.

Two lower-level membership helpers make no countdown test:

- `FUN_00305210(container,id)` at runtime/file
  `0x00305210/0x205310` returns the first exact-ID node pointer from the
  supplied container, or null.
- `FUN_00306420(fighter,id)` at runtime/file
  `0x00306420/0x206520` returns whether any exact-ID node is present in the
  fighter's gameplay list.

Consequently, list membership includes negative-sentinel nodes and also a
zero-countdown node during the interval before its removal. This differs from
the display selector below, which rejects countdown zero. The specialized
predicate `FUN_00306490` at `0x00306490/0x206590` scans for effect `0x1A` only
when its second argument is `-1`, returns true unconditionally when that
argument itself is `0x1A`, and returns false for every other argument.

The exact `FUN_003065A0` selection order is also display policy, not gameplay
ownership:

1. it starts with the highest active nonzero-countdown ID in `0x74..0x89`;
2. among `0x00..0x0D`, it selects the greatest **positive** countdown (the
   lower ID wins a tie because the comparison is strict);
3. an active cached low ID at `+0x8E8` with any nonzero countdown overrides
   that low-ID choice;
4. the highest active nonzero-countdown ID in each successive range
   `0x0E..0x64`, `0x65..0x67`, then `0x68..0x73` overwrites the prior choice.

The resulting priority is therefore category `3`, then `2`, then `1`, then
the selected low ID, then category `4`. Two final gates can suppress it:
effect ID `0` is suppressed when `FUN_002440C0(fighter)` is nonzero, and every
selection is suppressed while fighter byte `+0x62` bit `7` is clear.
`FUN_0033CE40` then publishes the fighter and selected ID to the side-specific
display controller even when the final ID is `-1`.

### Presence policies used by native actions

Several status-facing action helpers use membership without a
countdown test. This makes their zero-node behavior differ from the flag
scanners and payload folds:

| Helper, runtime / file | Proven policy |
| --- | --- |
| `00307560/207660` | Returns true for effect `08` membership only when `FUN_00244130(fighter) == 0`; a present zero-countdown node still qualifies |
| `00307830/207930` | Returns true for any category-`1..3` member except IDs `23` and `4E`; does not test countdown |
| `00307920/207A20` | Returns true for membership of any of `0E,0F,10`; does not test countdown |
| `00307A70/207B70` | Requires effect `4A` membership and fighter float `+0x330 <= 400`; does not test countdown |
| `00307B20/207C20` | Effect `0B` membership takes priority and returns false; otherwise `3B` or `41` membership returns true; no match returns false |

The last policy is **not** a three-ID presence OR. Instructions and bytes
`0x00307B78..0x00307B80` send a found `0B` directly to the zero-return block
at `0x00307C40`; found `3B` instead branches at `0x00307BD4` to the one-return
block `0x00307C34`, and `41` reaches the same one-return block. Consequently
`0B` vetoes the predicate even when `3B` or `41` coexists, including while
`0B` has countdown zero pending expiry.

Its direct native consumer at `0x00245230/0x145330` is the Ultimate Jutsu
connection helper `FUN_00244F80`. A result of one skips the active-flag-`0x80`
scan before the tier debit; the fighter's own spend gates still apply. A
result of zero reaches that scan. Thus `3B/41` can request a debit despite
another active spend-blocking effect, but a present `0B` removes that
exception. If `0B` itself is already at countdown zero and no other active
`0x80` node remains, the ordinary scan returns false and can still permit the
debit. Predicate result zero does not by itself mean that the debit fails.
Resource mutation belongs to
[Chakra and guard](../combat/chakra_and_guard.md#debit-and-reservation-behavior), and
connection reachability belongs to [Ultimate Jutsu](../characters/ultimate_jutsu.md#start).

The `00307920` helper has no defined function in the preserved analysis. Its
complete instruction interval `[0x00307920,0x00307A4C)` performs three
exact-ID scans that reach the one-return block at `0x00307A34` on a match,
with no `+0x6C` load; unlike the `0B` veto above, it is a plain presence OR.
Direct-JAL searches found no resident call and four BTL calls, all in one
chooser at preserved addresses `00770104,00770134,00770164,00770194` (live
addresses are `0x40` higher; complete-file offsets `BC244,BC274,BC2A4,BC2D4`),
whose preserved decompilation omits those branches. The chooser selects
between paired authored pointer lanes based on fighter identity and this
predicate; the pointers' wider meaning is unresolved.

The effect-`08` policy gates the separate attack-bank path documented in
[Combat action execution](../combat/combat_action_execution.md#character-specific-scene-and-timer-selection).
The category predicate has a representative hit consumer in
`FUN_0021F610`: when its `+0x98` maximum is zero, result `1` and eligible
record flags can emit an event. That branch does not construct or refresh a
status. The effect-`4A` predicate also has a presentation consumer in
`FUN_00287020`, which reads the linked fighter and changes local float
`+0x310` from approximately `0.99` back to `1`; it does not remove either
fighter's effect. These distinct consumers reinforce that status membership,
active payload contribution, and presentation state are separate policies.

Effect nodes begin with the generic BTL node prefix owned by
[Battle entities](../session/battle_entities.md#node-prefix): flags byte `+0x00`, whose
bit `0` is a generic removal trigger, marker `0x474F` at `+0x02`, list links
`+0x18/+0x1C`, and vtable `+0x50`. The effect-specific fields are:

| Node offset | Proven role |
| ---: | --- |
| `+0x60` | Removal reason/state, initialized to `-1` |
| `+0x64` | Owning fighter |
| `+0x68` | Effect ID |
| `+0x6C` | Signed countdown or negative sentinel |
| `+0x70` | Copied definition flags |
| `+0x74..+0xB8` | Copied definition payload |

The generic `ccPlConObj` table at runtime/file
`0x005DB1C0/0x4DB2C0` begins with class-name pointer `0x005C7000` and a null
metadata word, followed by these callable slots:

| Vtable offset | Generic target | Behavior |
| ---: | --- | --- |
| `+0x08` | `FUN_00250AB0` (`0x00250AB0/0x150BB0`) | Virtual destructor: generic cleanup, base destruction, optional free |
| `+0x0C` | `0x002509C0/0x150AC0` | No-op |
| `+0x10` | `0x00308070/0x208170` | Returns `0` |
| `+0x14` | `0x00307F30/0x208030` | No-op |
| `+0x18` | `0x002509D0/0x150AD0` | No-op |
| `+0x1C` | `0x00304E80/0x204F80` | No-op zero-exit callback |

Specialized classes replace selected entries while eventually restoring this
generic table during base destruction. This layout explains why generic nodes
do not self-remove through slot `+0x10` and why zero-countdown side effects
come from `FUN_00304E90` unless a specialized `+0x1C` overrides the final
callback.

## Initialization and inherent locked effects

`FUN_00304F40` constructs the embedded lists; the fighter constructor calls it
at runtime/file `0x0021472C/0x11482C`. `FUN_00305470` installs specialized
constructors, conditionally stores the owner at `+0x8D4`, initializes
`+0x8E8 = 0xFFFF`, and clears the display trio. Fighter reset calls it at
`0x00214EC0/0x114FC0`.

`FUN_00305FF0` at `0x00305FF0/0x2060F0` installs inherent category-3 effects
with explicit countdown `-2` during fighter initialization. Its caller is
`FUN_002151E0` at `0x0021563C/0x11573C`.

| Fighter ID | Inherent effect |
| ---: | ---: |
| `0x49` | `0x72` |
| `0x4B` | `0x73` |
| `0x2F..0x38` | fighter ID `+ 0x39`, producing effects `0x68..0x71` |

These nodes are protected from same-ID replacement and ordinary removal by
the `-2` sentinel. They still disappear under hard reason `5` cleanup.

## Application, replacement, and countdown normalization

### High-level application

`FUN_00305C30(fighter, effect_id, requested, route)` is at runtime/file
`0x00305C30/0x205D30`.

1. It rejects IDs outside `0x00..0x89`.
2. Categories `1..3` bypass the fighter guard. Categories `0` and `4` require
   fighter byte `+0x62` bit `0` clear and `FUN_00216820(fighter) == 0`.
3. A nonzero route argument applies the definition's linked/local masks.
4. Input `-1` resolves to definition `+0x0C`.
5. `FUN_00306980` normalizes the requested/base value.
6. It calls `FUN_00305270` at runtime/file callsite
   `0x00305D98/0x205E98`.

On successful construction it:

- calls `FUN_00376610` and then
  `FUN_00376160(resource, fighter_side, effect_id)` when the resource exists;
- creates low-ID positional feedback for IDs `0x00..0x0C`;
- allocates an auxiliary status visual for categories `1` and `2`;
- writes effect ID to fighter `+0x8E8`.

Failed construction does not perform those success side effects or update the
cache.

### Same-ID replacement rule

`FUN_00305270` at runtime/file `0x00305270/0x205370` scans only for the exact
same ID.

- If container owner pointer `+0x10` (fighter `+0x8D4`) is null, application
  fails before inspecting or destroying any old node.
- If a same-ID node has countdown `-2`, the new application fails.
- Otherwise the old node is immediately removed with reason `5`.
- A specialized or generic replacement node is allocated and appended.
- A normalized value other than `-1` overwrites the constructor-loaded
  countdown.
- Different IDs coexist; there is no generic category-wide eviction or stack
  count.

The same-ID lookup stops at the first matching node. Starting from the clean
API-maintained invariant, that is sufficient to keep one node per ID. It does
not repair an externally injected or corrupted list containing duplicates: a
locked first match rejects immediately, while a replaceable first match is
destroyed and the new node appended without inspecting later duplicates.
`FUN_00305510`, by contrast, walks its starting list count and requests
removal for every exact-ID match.

Replacement is destroy-first, not refresh-in-place. If allocation or the
constructor fails, the old effect is already gone. Its virtual destructor and
destructor side effects have already run.

Effect `0x22` is an exception to that result: destroying
the old `0x22` during same-ID replacement applies successor `0x23`, after which
the lower constructor appends the new `0x22`. A successful replacement can
therefore leave both IDs active; this does not violate the one-node-per-exact-ID
rule.

Consequently, the proven generic policy is one normally applied node per exact
ID, not one node per category and not additive same-ID stacking.

### Caller-enforced per-fighter effect families

Generic different-ID coexistence does not prevent a caller from enforcing its
own family. Resident table runtime/file `0x005C1D30/0x4C1E30` has `0x5E`
records indexed by fighter ID `0x00..0x5D`. Each `8`-byte record stores either
one inline effect ID, or a pointer to a `s16` list, followed by its count.
Zero-count records are omitted below:

| Fighter ID(s) | Authored effect family |
| --- | --- |
| `05,06,07` | `11`; `12`; `13` |
| `09,0A,0B` | `14`; `15`; `16` |
| `0C,0D` | `{17,18}`; `19` |
| `0F..13` | `1B..1F`, one per fighter |
| `15,16` | `20`; `21` |
| `19,1B,1C` | `24`; `25`; `26` |
| `27` | `{2C,2D}` |
| `28` | `2F` |
| `29` | `{30,31}` |
| `2A` | `32` |
| `2B` | `{33,34}` |
| `2C,2D` | `35`; `36` |
| `2E` | `{37,38}` |
| `2F..38` | `68..71`, by `effect = fighter + 39` |
| `39` | `72` |
| `3A,3B` | `3A`; `3B` |
| `3C,3D,3E` | `3D`; `3E`; `3F` |
| `3F` | `73` |
| `40,41,42` | `41`; `42`; `43` |
| `43` | `{44,45}` |
| `44` | `46` |
| `45` | `{47,48}` |
| `46,47,48` | `49`; `4A`; `4B` |
| `49` | `72` |
| `4C` | `4C` |
| `4D,4E,4F` | `4E`; `50`; `51` |
| `50` | `{52,53}` |
| `51,52,53,54` | `54`; `55`; `56`; `57` |
| `55` | `{58,59}` |
| `56` | `5A` |
| `57` | `{5B,5C}` |
| `58,59,5A` | `00`; `5D`; `5E` |
| `5B,5C,5D` | `{5F,60}`; `{61,62}`; `{63,64}` |

In the guarded transition inside `FUN_0020D690` at runtime/file
`0x0020D690/0x10D790`, every member of the indexed family whose ID is below
`0x68` is removed with reason `1` before the selected effect from fighter
`s16 +0x18A` is applied with default input `-1`. A multi-ID family therefore
has caller-enforced exclusivity on this route even though the generic
constructor would permit its different IDs to coexist. The function verifies
that the selected ID belongs to the family after application.

Related transition/query cleanup in `FUN_0020D910`
(`0x0020D910/0x10DA10`) and `FUN_0020DDC0`
(`0x0020DDC0/0x10DEC0`) consumes the same table. Fighter `0x19` has additional
explicit handling for effects `0x22/0x23`, and fighter `0x3A` can explicitly
remove effect `0x07`. The `FUN_0020D690` family-removal loop skips IDs
`0x68+`; those table rows prove fighter/effect association, not
family exclusivity.

The clean resident executable has exactly 17 direct JALs to exact-ID remover
`FUN_00305510`; raw instructions confirm that every one passes reason `1`.
This is the exhaustive direct-call grouping:

| Caller/policy | Removed ID | Runtime / file callsite(s) |
| --- | --- | --- |
| `FUN_0020D690` family switch | Inline or listed family member below `68` | `0x0020D784/0x10D884`; `0x0020D7C4/0x10D8C4` |
| `FUN_0020D910`, fighter `19` | `22` | `0x0020DA2C/0x10DB2C` |
| `FUN_0020D910`, fighter `45` transition | First member of its authored family | `0x0020DA9C/0x10DB9C` |
| `FUN_0020D910`, fighter `4D` | `4D` | `0x0020DAF0/0x10DBF0` |
| `FUN_0020DDC0`, fighter `19` cleanup | `22`; `23` | `0x0020DE24/0x10DF24`; `0x0020DE50/0x10DF50` |
| `FUN_0020DDC0`, fighter `4D` cleanup | Inline or listed family member below `68` | `0x0020DEB4/0x10DFB4`; `0x0020DEF4/0x10DFF4` |
| `FUN_0020DDC0`, fighter `3A` cleanup | `07` | `0x0020E21C/0x10E31C` |
| Effect-`54` state invalidation | `54` | `0x002E8E30/0x1E8F30`; `0x002E9A4C/0x1E9B4C` |
| Fighter-`57` falling-edge toggle | `09` | `0x002F2E20/0x1F2F20` |
| `FUN_00374190`, pickup code `0D` | `04`; `06`; `07`; `0A` | `0x0037439C/0x27449C`; `0x003743B0/0x2744B0`; `0x003743C4/0x2744C4`; `0x003743D8/0x2744D8` |

BTL contributes four further direct exact-ID calls, the mirrored code-`0D`
pickup callback sites documented below; they also pass reason `1`. This direct
inventory does not rule out a dynamically selected or indirect invocation.

### Countdown normalization

`FUN_00306980` at runtime/file `0x00306980/0x206A80` preserves any negative
input. For nonnegative inputs below effect `0x0D`, it uses fighter float
`+0x158` as a countdown scalar. Let `r` be the requested/base value and `s` the
fighter field:

| Effect IDs | Value before integer conversion |
| --- | --- |
| `00,01,04,06,07,0A` | `r * (2.0 - s)` |
| `02,03,05,08,09,0B,0C` | `r * s` |
| `0D..89` | `r` |

Negative computed results clamp to zero, then EE `cvt.w.s` converts the value
to an integer. The broader gameplay name of fighter `+0x158` is not proven.

Sentinel behavior is distinct:

- `-1` does not decrement or auto-expire, but remains replaceable and
  removable;
- `-2` does not decrement and additionally blocks same-ID replacement and
  removal reasons `0..3`;
- reason `5` can still destroy a `-2` node;
- any other negative value would also avoid generic countdown expiry, although
  no definition uses it.

## Update, expiry, and removal

### Countdown pass

Fighter update `FUN_0024C440` calls `FUN_003059B0` at runtime/file
`0x0024C4E8/0x14C5E8`. `FUN_003059B0` is at
`0x003059B0/0x205AB0`. Its countdown-pass gate is exact:

- ticking initially requires `FUN_00216820(fighter) == 0`;
- an active effect `0x1A` forces ticking when fighter `+0x18E != 8`, even if
  that first predicate failed;
- nonzero `func_0x006DBD70()` or `FUN_00244110(fighter)` then disables the
  pass unconditionally.

An earlier boolean in the same function checks fighter `+0x61` bit `7`,
`FUN_002354C0`, `+0xB00`, `+0xB10`, and `FUN_00216820`, but it gates only the
aggregate `FUN_00306F00/FUN_00307020` side-effect helpers. It does **not** gate
the per-node countdown traversal, so those predicates are not countdown
lifetime rules.

One exact-ID side effect also runs before the countdown gate. Membership
helper `FUN_00307610` (`0x00307610/0x207710`) searches for effect `0x09`
without testing its countdown. At `0x00305AAC/0x205BAC`, a match causes
`FUN_00229B70(fighter,-2)` at `0x00305AC4/0x205BC4`. Thus even a
zero-countdown effect-`09` pending gated expiry still triggers this call on a
`FUN_003059B0` pass. The semantic name of that secondary action is unresolved.

For each node, it calls `FUN_00304D60` at
`0x00305B78/0x205C78`:

- null owner returns complete;
- a positive countdown decrements by one on an allowed tick;
- for IDs `0` and `1`, if the countdown remains positive after that ordinary
  decrement, let `n` be the popcount of
  `(owner->+0x24->+0xAC) & 0xFFFFF00F`; it additionally subtracts
  `floor(3*n/2)` and clamps at zero;
- at zero, it calls exit helper `FUN_00304E90`, invokes node vtable `+0x1C`,
  and returns complete;
- negative countdowns do not decrement or auto-expire.

The caller requests reason `0` removal for a completed node at
`0x00305B94/0x205C94`.

Countdown `0` is therefore a pending-expiry state, not a constructor failure.
An application normalized or overridden to zero can still append the node and
perform all success-side effects. Exact membership helpers see it, while the
display selector excludes it. It runs the zero-exit path and is removed only
when the gated countdown pass next executes; if that pass remains disabled,
the zero-countdown node can remain in the list because the later generic
callback traversal does not remove it merely for having countdown zero.

After the countdown pass, container vtable slot `+0x0C` reaches BTL's generic
self-removal traversal. Every registered gameplay-effect vtable's slot
`+0x10` returns zero, even when it has side effects, so no registered
gameplay effect self-removes through that callback return. The remaining
generic trigger there is node base-flags bit `0`. Auxiliary status-visual objects are different: `FUN_00303D40` can return
one when their animation/countdown completes, allowing their removal.

This post-countdown traversal is called even when the `FUN_003059B0`
countdown-pass gate is false. Side-effecting slot-`+0x10` callbacks can
therefore still run on such an update; the gate controls countdown ticking,
not that callback traversal.

`FUN_00305C00` at `0x00305C00/0x205D00`, called at
`0x00250758/0x150858`, performs a secondary callback pass through gameplay
node vtable `+0x14` and the auxiliary list. The caller is
`FUN_00250690`, installed at registry vtable `0x005D9FC0 +0x10`, and runs in
battle phase 2 **after** the generic fighter-node `+0x14` pass. The complete
dispatch ordering belongs to
[Battle lifecycle](../session/battle_lifecycle.md#what-phase-2-guarantees). This callback
is not another countdown pass: `FUN_00305C00` dispatches the embedded
container's `+0x10` slot rather than calling `FUN_00304D60`.

Effect `4A`'s specialized secondary callback `FUN_002C8900` has observable
state work as well as presentation. After its owner, linked-fighter,
distance, and response gates pass, it recomputes node private word `+0xC0`
from fighter response predicates, checks linked-fighter effect-`4A`
membership, chooses its owned presentation objects' variants, and advances
private phase floats `+0xD0/+0xD4/+0xD8`. These operations belong to the
phase-2 callback; the generic countdown gate does not enclose this separate
pass. The callback's own gates can still skip it. Treating phase 2 as pure
drawing would miss its private-state and RNG updates.

### Core removal decision

`FUN_00305040(container, node, reason)` at
`0x00305040/0x205140` first stores the reason at node `+0x60`.

| Reason | Proven generic behavior |
| ---: | --- |
| `5` | Unconditional immediate unlink/destruction, including `-2` nodes |
| `3` | Categories `3/4` remain; categories `0/1/2` remove unless countdown is `-2` |
| `0,1,2` | Remove unless `-2` or the effect-`1A` hold applies |

Because the store to node `+0x60` precedes those decisions, a blocked or
deferred attempt still changes the live node's reason/state field. This
includes a `-2` node that rejects reasons `0..3`, a category-`3/4` node
deferred for reason `3`, and an effect-`1A` zero crossing held at countdown
`1`. A later request overwrites the field again before making its decision.

For effect `0x1A`, reasons `0..2` can defer destruction when fighter
`+0x18E == 8`: the countdown is reset to `1`. On natural expiry the zero-exit
hook has already run before that reset, so it can run again on a later zero
crossing until the state changes.

Immediate unlink calls BTL live `0x00709EA0` at resident callsite
`0x003051D8/0x2052D8`. This unlinks the node and invokes its virtual
destructor.

Final container destruction does not call `FUN_00305040`; BTL list-clear
invokes virtual destructors directly and leaves node `+0x60` at its last
stored value, commonly constructor value `-1`. It is therefore not a
reason-`5` event even though the generic destructor's natural-versus-forced
test treats every value other than `0` as the forced branch.

### Explicit and bulk cleanup

| Function | Runtime / ELF file | Proven scope |
| --- | --- | --- |
| `FUN_00305510(fighter,id,reason)` | `0x00305510 / 0x205610` | Every node matching one exact ID |
| `FUN_003055C0(fighter,reason)` | `0x003055C0 / 0x2056C0` | Categories `0..2`; clears display trio |
| `FUN_00305750(fighter)` | `0x00305750 / 0x205850` | One snapshot-count reason-`5` pass for each category `0..4`; clears display trio |
| `FUN_00304F90(container)` | `0x00304F90 / 0x205090` | Destroys both embedded lists |
| `FUN_00306B00(fighter,reason)` | `0x00306B00 / 0x206C00` | Every effect-`0` and effect-`1` node, then a dedicated post-cleanup helper |

`FUN_00305750` is called from `FUN_00215720` at
`0x0021574C/0x11584C`. The container destructor is called at
`0x0021492C/0x114A2C`.

Exact-ID removal, category cleanup, and hard `FUN_00305750` cleanup traverse
only the main gameplay list. They neither search nor clear the auxiliary list
at fighter `+0x8D8`; those presentation objects finish through their own
callback lifetime. `FUN_00304F90` final container destruction is the path here
that explicitly clears both lists. Thus a gameplay cleanse or hard reset can
remove status truth immediately while its already-created auxiliary visual
remains briefly present.

Both category cleanup functions zero display fields `+0x8EC/+0x8F0/+0x8F4`
after their removal attempts, but neither clears last-success cache `+0x8E8`.
`FUN_003055C0` does this even when a `-2` node rejected the requested ordinary
removal. Consequently, cleared display state and a stale cache can coexist
with a still-active protected gameplay node.

The direct bulk-cleanup call inventory is small enough to state exhaustively:

| Caller | Reason | Runtime / file callsite(s) | Fighter scope |
| --- | ---: | --- | --- |
| `FUN_00216A60` | `1` | `0x00216A90/0x116B90` | One fighter, guarded by its `+0x62` bit `0` |
| `FUN_00216D00` | `1` | `0x00216D60/0x116E60`; `0x00216DE4/0x116EE4` | Fighter and linked fighter |
| `FUN_00216EA0` | `2` | `0x00216F88/0x117088`; `0x00216F98/0x117098` | Fighter and linked fighter |
| `FUN_0024ED40` state case `1` | `3` | `0x0024EFC4/0x14F0C4`; `0x0024EFD4/0x14F0D4` | Its two participant pointers at `+0x24/+0x28` |
| `FUN_00215720` | fixed `5` through `FUN_00305750` | `0x0021574C/0x11584C` | One fighter, categories `0..4` |

Effects `0` and `1` also have a paired caller policy. `FUN_00306A60` at
`0x00306A60/0x206B60` returns true when either exact ID is present; it does
not test countdown. When called, `FUN_00306B00` scans both IDs, requests the
caller-supplied removal reason for every match, and then always calls
`FUN_00227270(fighter)` (`0x00227270/0x127370`). Its only direct callers both
pass reason `1`:

| Caller | Guard/context | Runtime / file callsite |
| --- | --- | --- |
| `FUN_00235100(fighter,value)` | `value` is `0x61` or `0x62`, and either ID is present | `0x0023516C/0x13526C` |
| `FUN_00235510(value,fighter)` | Either ID is present | `0x00235540/0x135640` |

This is caller-enforced pairing, not a generic category-`0` rule: the normal
constructor and exact-ID remover continue to treat IDs `0` and `1`
independently.

There are no other direct resident JALs to `FUN_003055C0` or
`FUN_00305750`, and clean BTL contains no direct JAL to either helper. These
call contexts distinguish engine transition boundaries, but they do not by
themselves establish user-facing names for reasons `1..3`.

### Native action and form boundaries

The scoped transition consumers distinguish removal from a pause or a form
marker change:

- `FUN_00216A60` performs its reason-`1` category cleanup while fighter
  `+0x62` bit `0` is still clear, then releases the reservation and processes
  action/exchange cleanup, and finally sets bits `0/1` in that byte. A second
  call with bit `0` already set skips this entire body. Its paired wrapper
  `FUN_00216C60` invokes it separately for both fighters. Accepted-hit and
  terminal-response contexts belong to [Hit response](../combat/hit_response.md#accepted-hit-routing).
- `FUN_00216D00` performs reason-`1` cleanup for both fighters only when the
  initiating fighter's bit `0` is clear and the coordinator exists; it then
  publishes the participants to that coordinator. The cleanup calls are not
  unconditional consequences of changing any native action.
- Ultimate Jutsu connection `FUN_00216EA0` requests reason-`2` category
  cleanup for both fighters only when a coordinator exists and is not already
  in state `6`. Post-cinematic substate `1` of `FUN_0024ED40` requests
  reason-`3` cleanup **before** attempting the outcome effect on its attacker.
  Both calls are to the category-`0..2` helper, so category-`3/4` nodes lie
  outside their traversal independently of sentinel protection. Complete
  connection/outcome sequencing belongs to [Ultimate Jutsu](../characters/ultimate_jutsu.md).
- Native form reconstruction destroys the old fighter ownership and creates
  new effect containers. Complete save/restore helpers `FUN_001ECC00` and
  `FUN_001ECDE0` preserve selected HP, chakra, timer, and inventory values;
  neither copies gameplay nodes or countdowns. The new form's inherent node
  is installed by `FUN_00305FF0` with `-2`. The rebuild and retained-value
  contract belongs to [Awakening](../characters/awakening.md#state-retained-across-the-native-rebuild).

Thus the protected inherent node, a generic timed node, and a separately
retained item count have different native lifetimes. The form's new `-2`
node is not an old timed node promoted to protected state. The complete
class-3 payload is neutral in all 12 definition records, so its generic
presence does not itself contribute the replacement form's changed character
parameters; those belong to [Awakening](../characters/awakening.md#replacement-character-parameters).

### Effect `0x22` successor

Effect `0x22` uses `ccPlConSpl25A`. Its destructor `FUN_003037C0` at
runtime/file `0x003037C0/0x2038C0` applies effect `0x23` whenever owner
`+0x64` is non-null, before base cleanup. It never checks removal reason
`+0x60`.

The successor can therefore be applied by natural expiry, explicit removal,
same-ID replacement, or an individual hard reason-`5` removal; it is not a
timeout-only transition.
Effect `0x23` has no corresponding successor. Static xrefs found no other
registered effect destructor that calls `FUN_00305C30`.

The list mutation order has additional proven consequences:

- The countdown loop snapshots its starting count and captures `next` before
  removal. A `0x23` appended by natural `0x22` expiry is not countdown-ticked
  in that same pass.
- `FUN_003055C0` and `FUN_00305750` also snapshot the count separately for
  each category. Removing `0x22` in their category-`1` pass appends a new
  category-`1` `0x23` after the pass has begun; later category passes do not
  revisit it. Thus `FUN_00305750` can finish with gameplay effect `0x23`, its
  newly allocated category-`1` auxiliary visual, and cache `+0x8E8 = 0x23`
  still present even though every pre-existing category was processed with
  reason `5`. Its caller `FUN_00215720` does not perform a second gameplay-list
  clear.
- Final container destruction is different. Raw `FUN_00304F90` calls BTL
  clear on the main gameplay list, clears the auxiliary list, then calls BTL
  clear on the main list a second time through the base destructor. The second
  pass removes a `0x23` spawned by the first, so final container destruction
  still ends empty.

## Random field-item selection

Resident `FUN_003AE890` chooses a field-item identity from authored BTL pool
distributions, and `FUN_003AEAF0` separately applies the Items amount setting.
[Battle item inventory](battle_item_inventory.md#random-field-item-selection)
owns the selector contract, pools, distributions, call sites, and amount
boundary.

## Immediate pickup/item-effect path (`0x00..0x13`)

### Resident item metadata

The resident item table starts at runtime/file
`0x005B04F0/0x4B05F0`, with exactly `0x74` records for codes
`0x00..0x73`, each `0x0C` bytes. Its exact span is runtime
`0x005B04F0..0x005B0A5F`, file `0x4B05F0..0x4B0B5F`. Runtime/file
`0x005B0A60/0x4B0B60` starts a different 12-byte configuration table and is
not item record `0x74`.

| Record offset | Proven role | Accessor |
| ---: | --- | --- |
| `+0x00` | Item kind byte | `FUN_003765B0` |
| `+0x02` | Flags | `FUN_003762F0`, `FUN_00376360`, `FUN_003763D0` |
| `+0x04` | Float amount | `FUN_00376560` |
| `+0x08` | Signed direct effect ID | `FUN_003764E0` |

Flag mask `0x20` selects one positive-resource path, `0x40` another, and
`0x80` an alternate action path. The generic resident dispatcher
`FUN_002369D0` at runtime/file `0x002369D0/0x136AD0` applies the table effect
through `FUN_00305C30(fighter,id,-1,1)` when the alternate flag is clear and
the ID is not `-1`, then performs the selected resource adjustment.

This combination is non-transactional. The status call is at
`0x00236B24/0x136C24`, returns no success value, and is followed by the
flag-`0x40` and flag-`0x20` resource branches. A rejected gameplay-node
construction therefore does not by itself suppress a resource adjustment or
the dispatcher's later presentation calls. Conversely, a resource branch can
be gated by its own fighter predicates without undoing a successfully created
status node.

### Resident pickup resolver

`FUN_00374190` at runtime/file `0x00374190/0x274290` resolves the concrete
pickup code through BTL live `0x0070C3B0`, then chooses inventory, resource,
direct-effect, or cleanse handling from the resident metadata. Its direct
effect call is `0x00374490/0x274590`; code `0x06`'s additional effect-`0x0C`
call is `0x003744B4/0x2745B4`. Code `0x0D` removes effects
`04,06,07,0A` with reason `1` at these runtime/file callsites:

| Removed ID | Runtime / file callsite |
| ---: | --- |
| `04` | `0x0037439C/0x27449C` |
| `06` | `0x003743B0/0x2744B0` |
| `07` | `0x003743C4/0x2744C4` |
| `0A` | `0x003743D8/0x2744D8` |

### BTL pickup-object callback

The BTL callback is file `0x57D20`, preserved `FUN_0070BBE0`, live
`0x0070BC20`. It copies object byte `+0x62` to active item byte `+0x61`,
resolves the fighter from object side `+0x5C`, scales the incoming magnitude
with `FUN_00376560(code)`, and calls resident `FUN_002369D0` at BTL
file/Ghidra/live callsite `0x57E38/0x0070BCF8/0x0070BD38`.

This callback implements the same direct-effect, extra code-`0x06` effect,
code-`0x0C` resource, and code-`0x0D` exact-removal decisions as the resident
resolver, but at distinct callsites. Static analysis did not establish whether
one runtime pickup reaches both sites or whether they are alternate object
phases; no double-application claim is made here.

Within the BTL callback, code `0x0D` performs its four removals before the
common `FUN_002369D0` call. The common call then handles metadata direct effect
and/or resource flags. Code `0x0C`'s separate `15.0` action and code `0x06`'s
additional effect-`0x0C` application occur afterward. The sequence has no
rollback: later resource/action failure does not restore a removed node, and a
later extra-effect rejection does not undo the metadata effect.

The relevant clean records and explicit additions are:

| Code | Kind | Flags | Amount | Table effect | Additional proven action |
| ---: | ---: | ---: | ---: | ---: | --- |
| `00,01` | `0` | `0000` | `0` | `-1` | none found |
| `02` | `1` | `0020` | `10` | `-1` | resource path only |
| `03` | `2` | `0040` | `5` | `-1` | resource path only |
| `04` | `2` | `0040` | `0.75` | `-1` | resource path only |
| `05` | `2` | `0040` | `0` | `-1` | resource path only |
| `06` | `4` | `0000` | `0` | `05` | also applies effect `0C` with default input `-1` |
| `07` | `4` | `0000` | `0` | `02` | none found |
| `08` | `4` | `0000` | `0` | `08` | none found |
| `09` | `4` | `0080` | `0` | `-1` | alternate action path; semantics outside this scope |
| `0A` | `4` | `0000` | `0` | `09` | none found |
| `0B` | `4` | `0000` | `0` | `03` | none found |
| `0C` | `4` | `0000` | `0` | `0B` | direct `15.0` secondary-resource adjustment and numeric notification `2` |
| `0D` | `1` | `0020` | `2` | `-1` | removes effects `04,06,07,0A` with reason `1`; BTL callback queues notification `4` |
| `0E` | `4` | `0080` | `0` | `-1` | alternate action path; semantics outside this scope |
| `0F..13` | `6` | `0000` | `0` | `-1` | no direct effect found |

The four code-`0x0D` removal calls are exact-ID removals, not a generic
category cleanse. Their BTL file/Ghidra/live callsites are:

| Removed ID | File / Ghidra / live callsite |
| ---: | --- |
| `04` | `0x57D9C / 0x0070BC5C / 0x0070BC9C` |
| `06` | `0x57DB0 / 0x0070BC70 / 0x0070BCB0` |
| `07` | `0x57DC4 / 0x0070BC84 / 0x0070BCC4` |
| `0A` | `0x57DD8 / 0x0070BC98 / 0x0070BCD8` |

The extra code-`0x06` application is at
`0x57F20/0x0070BDE0/0x0070BE20` and calls
`FUN_00305C30(fighter,0x0C,-1,1)`.

Selected-item resolver `FUN_00236C70` has a separate metadata-direct fallback
at runtime/file `0x00236DA8/0x136EA8`. The branch excludes kind-`3/6`
delayed items, flag-`0x10` table-driven items, special code `0x09`, and a
direct-effect value of `-1`. Across the clean `0x00..0x73` metadata table,
that leaves exactly these requests:

| Item code | Direct request |
| ---: | ---: |
| `06` | Effect `05`, default `-1`, route `1` |
| `07` | Effect `02`, default `-1`, route `1` |
| `08` | Effect `08`, default `-1`, route `1` |
| `0A` | Effect `09`, default `-1`, route `1` |
| `0B` | Effect `03`, default `-1`, route `1` |
| `0C` | Effect `0B`, default `-1`, route `1` |

This fallback applies only metadata `+0x08`; it does not contain the pickup
path's additional code-`06` effect `0x0C` or its resource adjustment logic.
These six records also lack inventory flag `0x80`, so static presence of the
fallback is not proof that ordinary battle input can select them from the
three-slot inventory.

### Direct-effect records carried by hit objects

The item-record `+0x08` field is also consumed by BTL hit/result code. The
following are **all** non-`-1` direct-effect entries from clean item records
`0x00..0x73`:

| Item/object code | Kind / flags | Direct effect | BTL object-definition row |
| ---: | --- | ---: | ---: |
| `06` | `4 / 0000` | `05` | not present |
| `07` | `4 / 0000` | `02` | not present |
| `08` | `4 / 0000` | `08` | not present |
| `0A` | `4 / 0000` | `09` | not present |
| `0B` | `4 / 0000` | `03` | not present |
| `0C` | `4 / 0000` | `0B` | not present |
| `24` | `3 / 0180` | `06` | `09` |
| `26` | `3 / 0180` | `07` | `0C` |
| `29` | `3 / 0180` | `0A` | `1C` |
| `2A` | `3 / 0180` | `04` | `1D` |
| `31` | `3 / 0180` | `01` | `85` |
| `54` | `3 / 0380` | `07` | `A1` |
| `57` | `3 / 0280` | `07` | `88` |
| `5B` | `3 / 0380` | `06` | `7E` |
| `6E` | `3 / 0280` | `07` | `9C` |

The BTL object-definition table is complete-file `0x1E8A10`, live
`0x0089C910`, with `0xB6` rows of `0x68` bytes. Its exact `0x49F0`-byte span
is file `0x1E8A10..0x1ED3FF`, live
`0x0089C910..0x008A12FF`. Constructor
file/Ghidra/live `0x772F0/FUN_0072B1B0/0x0072B1F0` writes the row's leading
`s16` code to object `+0x7A`. Hit/result helper
`0x7A840/FUN_0072E700/0x0072E740` reads that field and calls resident
`FUN_003764E0` at `0x7A930/0x0072E7F0/0x0072E830`. A mapped value other than
`-1` is then applied to the struck fighter as
`FUN_00305C30(target,effect,-1,1)` at
`0x7A954/0x0072E814/0x0072E854`.

The six low codes are consumed by the immediate pickup callback above and do
not occur as leading codes in the clean `0xB6`-row BTL object table. The nine
remaining codes do occur there at the listed rows, so their direct effect is
hit-carried. The `-1` request selects each effect definition's base countdown,
then low-ID normalization still applies. The complete clean object table's
leading codes range only from `0` through `0x6F`, so the `0x00..0x73` item
record scan covers every value this hit mapper receives from that table.

Item `0x5B` has both mechanisms. When its delayed use commits, it reaches its
three-slot activation row, applying effect `0x05` with requested countdown
`180` to the using fighter. The spawned row-`0x7E` hit object carries code
`0x5B`; if its hit/result path runs on another fighter, that path separately
applies effect `0x06` with default input `-1` to the struck fighter. Codes
`0x54`, `0x57`, and `0x6E` have no three-slot status row and use their
hit-carried effect `0x07` path instead.

## Three-slot battle-item path (`0x51..0x73`)

### Collection and inventory ownership

All 19 row codes below have metadata flag `0x80`: resident `FUN_00374190`
adds them to the side's inventory through BTL live `0x00710040` at
`0x003742D4/0x2743D4` (side 0) or `0x00374310/0x274410` (side 1) instead of
applying status. Selection, use admission, item `0x5B`'s delayed
cursor-timing commit, and the slot decrement belong to
[Battle item inventory](battle_item_inventory.md#dispatch-and-consumption-boundary).

On the status side, fighter input gate `FUN_002366F0` tests `+0x338` bit
`0x01000000`, reads the selected byte through `FUN_00375630` at
`0x00236988/0x136A88`, and calls `FUN_00236C70(fighter,item)` at
`0x002369A0/0x136AA0`. The 18 kind-`4` rows reach `FUN_00375690` at
`0x00236DD0/0x136ED0`, which selects panel `+0x6C`/`+0x70` by side and enters
panel activation `0x5D480/FUN_00711340/0x00711380`. Kind-`3` item `0x5B`
reaches the same activation only when its delayed use commits, from BTL
`0x843CC/0x0073828C/0x007382CC`; that activation is the user-side
effect-`0x05` half of its dual path. Activation runs the status dispatcher
below, then decrements the currently selected slot's code through
`0x5C3D0/FUN_00710290/0x007102D0` (callsite `0x5D7E0/0x007116A0/0x007116E0`)
and sets panel byte `+0x61 = 1`. The dispatcher returns no per-effect success,
so an application rejected by a same-ID `-2` node or a fighter guard does not
preserve the item count, and recovery branches are not rolled back with a
rejected status node.

### Dispatcher and table layout

The dispatcher is BTL file `0x5D820`, preserved `FUN_007116E0`, live
`0x00711720`. Its table is complete-file `0x1E4FF0`, live `0x00898EF0`, with
19 records of `0x28` bytes. The exact `0x2F8`-byte span is complete-file
`0x1E4FF0..0x1E52E7`, live `0x00898EF0..0x008991E7`.

| Row offset | Proven role |
| ---: | --- |
| `+0x00` | Item-code byte |
| `+0x04` | Requested countdown |
| `+0x08,+0x10,+0x18,+0x20` | Up to four effect IDs, terminated by signed `-1` |
| `+0x0C,+0x14,+0x1C,+0x24` | Interleaved authored metadata not read by this dispatcher |

Before the first effect it calls `FUN_00334FF0(fighter)`. For each listed
effect it calls `FUN_00305C30(fighter,id,row_value,1)` at BTL
file/Ghidra/live `0x5D908/0x007117C8/0x00711808`.

Multi-effect rows are sequential, not atomic. Because each high-level apply is
`void`, rejection of one effect neither stops later row entries nor rolls back
an earlier success. A row can therefore leave a partial subset active when
per-ID locks, routing, allocation, or fighter guards differ between entries.
Each successful entry performs its own success-side presentation and cache
write, so fighter `+0x8E8` ends with the last successfully constructed row
effect; a failed later entry does not overwrite the prior successful value.

After a matching row and its optional recovery actions, the dispatcher adds
one to battle-statistic metric `6` ("Special ninja tools") for side
`panel_side + 1` through a `(side, 6, 1)` call at file/Ghidra/live callsite
`0x5DA08/0x007118C8/0x00711908`; the credit is owned by
[Match outcomes](../session/battle_statistics.md#ninja-tools-and-stage-objects). The encoded
JAL target is live `0x00715F90` (complete-file `0x62090`, nominal Ghidra
`0x00715F50`); the preserved export's `FUN_00715F90` label (complete-file
`0x620D0`, live `0x00715FD0`) is a different adjacent wrapper.

| Item | Row file / live | Requested | Effects actually read | Interleaved words, not read here |
| ---: | --- | ---: | --- | --- |
| `52` | `1E4FF0 / 898EF0` | `200` | `02,05` | `05,08` |
| `53` | `1E5018 / 898F18` | `300` | `3C` | `00` |
| `55` | `1E5040 / 898F40` | `300` | `05,0C` | `08,11` |
| `56` | `1E5068 / 898F68` | `250` | `02,05` | `05,08` |
| `59` | `1E5090 / 898F90` | `200` | `05` | `08` |
| `5B` | `1E50B8 / 898FB8` | `180` | `05` | `08` |
| `5D` | `1E50E0 / 898FE0` | `0` | none | none |
| `5F` | `1E5108 / 899008` | `250` | `02` | `05` |
| `60` | `1E5130 / 899030` | `180` | `03` | `06` |
| `63` | `1E5158 / 899058` | `250` | `02,03,05` | `05,06,08` |
| `64` | `1E5180 / 899080` | `200` | `02` | `05` |
| `66` | `1E51A8 / 8990A8` | `250` | `02,03` | `05,06` |
| `67` | `1E51D0 / 8990D0` | `0` | none | none |
| `68` | `1E51F8 / 8990F8` | `250` | `03` | `06` |
| `6D` | `1E5220 / 899120` | `150` | `09,08` | `09,0C` |
| `70` | `1E5248 / 899148` | `250` | `03` | `06` |
| `71` | `1E5270 / 899170` | `250` | `02` | `05` |
| `72` | `1E5298 / 899198` | `250` | `05,03` | `08,06` |
| `73` | `1E52C0 / 8991C0` | `250` | `65` | `12` |

The proven applied set is `{02,03,05,08,09,0C,3C,65}`. Interleaved values
such as `06`, `11`, and `12` are not additional effects at this site.

NUN5's homologous `0x2F8`-byte table at complete-file/live
`0x1EDBD0/0x008B48D0` is byte-identical. Its dispatcher is
file/Ghidra/live `0x60320/FUN_00726FE0/0x00727020` and calls resident homolog
`FUN_00310580`. This cross-game match corroborates the row layout; it is not
runtime evidence for retail NA2.

Requested values override record defaults, but low IDs then pass through
fighter `+0x158` normalization. Effects `0x3C` and `0x65` retain the supplied
`300` and `250`; effect `0x65` therefore uses `250` instead of its base `600`.

### Additional recovery paths

After generic effects, items `0x5D`, `0x67`, and `0x71` run a separate positive
recovery sequence:

```text
FUN_00376560(item)
    -> FUN_00224DF0(value,fighter,0)
    -> FUN_00224D10(result,fighter,1,1)
```

| Item | Generic status first | Metadata recovery | Additional action |
| ---: | --- | ---: | --- |
| `5D` | none | `10.0` | Separate `FUN_002254A0` input `2.5`; numeric notification code `2` |
| `67` | none | `10.0` | none found |
| `71` | Effect `02`, requested `250` | `5.0` | none found |

The recovery sequence emits numeric notification code `1`. The `2.5` value for
item `0x5D` is the float encoded by `0x40200000`; it is not `5.0`.

## Gameplay state versus status presentation

This section records only the mapping and lifetime boundary between gameplay
effects and their presentation objects. HUD drawing of status glyphs and
numeric popups belongs to
[Battle HUD](../session/battle_hud.md#remaining-ordinary-presentation-forest), and label
composition belongs to
[Battle item-status presentation](../../localization/ui/battle/item_status.md).

### Resident effect-to-notification map

After successful gameplay-node construction, `FUN_00376160` consults the
12-row resident table at runtime/file `0x005B0040/0x4B0140`:

| Gameplay effect | Notification object code |
| ---: | ---: |
| `00` | `0D` |
| `02` | `05` |
| `03` | `06` |
| `04` | `0E` |
| `05` | `08` |
| `06` | `07` |
| `07` | `13` |
| `08` | `0C` |
| `09` | `09` |
| `0A` | `0F` |
| `0B` | `10` |
| `0C` | `11` |

This agrees with most low-ID interleaved table words, but the BTL item
dispatcher itself never reads those words.

The authored `65/12` pair is therefore not proof that effect `0x65` emits UI
object `0x12`: the resident 12-row map has no effect-`0x65` entry, and no
literal code-`0x12` notification call was found on this route. Its consumer is
unresolved; that the word is unused metadata is an untested hypothesis.

### Auxiliary category-1/2 visuals

Successful category-1/2 application creates a separate `0x80`-byte
`ccMode1Panel` object in the fighter's auxiliary list. `FUN_00303AA0` at
runtime/file `0x00303AA0/0x203BA0` stores effect ID as `s16 +0x6E` and side as
`s16 +0x70`; its owned pointers are at `+0x60/+0x64/+0x68` and are released
by `FUN_003039D0`.

Its 13-row effect/visual-selector table is at runtime/file
`0x0059E080/0x49E180`:

| Effect ID(s) | Signed selector | Proven constructor result |
| --- | ---: | --- |
| `22,2D,2E,30,34,38,3C,4E,4F,53,62,64` | `1` | Uses pointer-array index `1`, string `TEX_mode1name2` |
| `23` | `-1` (stored table byte `FF`) | Sets auxiliary `s16 +0x6C` to `10` and skips resource construction |
| Every unlisted category-1/2 ID | `0` | Uses pointer-array index `0`, string `TEX_mode1name1` |

The selector is loaded with signed byte `lb`, so the `0xFF` row is genuinely
the `-1` branch rather than index `255`. In particular, effect `0x65` is not a
table row and follows selector `0`; effect `0x3C` follows selector `1`. This
auxiliary path is separate from the unproven BTL metadata word `0x12`.

The auxiliary object's lifetime is independent of the gameplay countdown.
New objects start with signed `s16 +0x6C = -1`. Selector `-1`, or failure to
obtain the required presentation resource, changes it to `10`; otherwise it
stays at `-1` while `FUN_00303D40` (`0x00303D40/0x203E40`) services the two
owned presentation objects. When the primary object's completion query first
succeeds, the callback sets `+0x6C = 3`. Subsequent callback passes decrement
any nonnegative private count and return `1` once it drops below `1`, which
causes the generic auxiliary-list traversal to unlink and destroy the object.

There is no pointer from this visual back to its gameplay node, and gameplay
node destruction does not search or unlink the auxiliary list. If a
category-`1/2` effect is replaced while its prior visual is still alive, the
replacement success appends another visual; the old one continues to its own
completion. This presentation overlap does not imply same-ID gameplay
stacking.

### Fukidasi notification objects

The BTL notification factory is file `0x596F0`, preserved
`FUN_0070D5B0`, live `0x0070D5F0`. Notifications store object code at `+0x0C`
and next pointer at `+0x40`. Their update/unlink/draw paths do not call
gameplay-effect APIs.

The resident battle manager holds the two side-specific notification-list
pointers at `+0x78/+0x7C`. A BTL list object stores head at `+0`, side at
`+4`. Base notification construction starts at file/Ghidra/live
`0x5A190/FUN_0070E050/0x0070E090`; in addition to code and next pointer, it
stores state byte at `+0x0D`, callback argument at `+0x14`, and side at
`+0x18`. Per-pass list processing is
`0x59520/FUN_0070D3E0/0x0070D420`: it calls object vtable slot `+0x14`, and a
zero return causes unlink and virtual destruction. This callback convention is
the inverse of the gameplay/auxiliary generic traversal and must not be
transferred between list types.

| Notification codes | Object family |
| --- | --- |
| `1,2,14` | Numeric/recovery |
| `5,6,7,8,0E,0F,10,11` | Paired/parameter-up-down |
| `9,0A,0B,0C,0D,12,13` | Single Fukidasi |
| `4` | Fixed/condition |
| `0,3,>14` | No allocation |

Numeric objects store the displayed integer at `+0x50` with a maximum of
`999`. Code `1` rounds `magnitude * 100`; codes `2` and `0x14` round
`magnitude * 20`. Factory code `0x11` has a duplicate-suppression branch only
when its third argument is zero. These are display transformations, not
resource or gameplay-effect amounts.

For the proven item callers above, those rules yield display integer `999`
for the `10.0` code-`1` recoveries of items `5D/67` (the unbounded result is
`1000`), `500` for item `71`'s `5.0` recovery, `50` for item `5D`'s separate
code-`2` magnitude `2.5`, and `300` for immediate item `0C`'s code-`2`
magnitude `15.0`.

The clean authored UI-record maps are:

| Factory code | UI record(s) | Table file / live |
| ---: | --- | --- |
| `1` | `81` | `1E4CB0 / 898BB0` |
| `2,14` | `82` | `1E4CB0 / 898BB0` |
| `9` | `9A` | `1E4CD0 / 898BD0` |
| `0C` | `98` | `1E4CD0 / 898BD0` |
| `0D` | `99` | `1E4CD0 / 898BD0` |
| `12` | `96` | `1E4CD0 / 898BD0` |
| `13` | `97` | `1E4CD0 / 898BD0` |
| `5` | `8F / 92` | `1E4D00 / 898C00` |
| `6` | `90 / 92` | `1E4D00 / 898C00` |
| `7` | `91 / 93` | `1E4D00 / 898C00` |
| `8` | `91 / 92` | `1E4D00 / 898C00` |
| `0E` | `90 / 93` | `1E4D00 / 898C00` |
| `0F` | `82 / 9B` | `1E4D00 / 898C00` |
| `10` | `82 / 94` | `1E4D00 / 898C00` |
| `11` | `9C / 92` | `1E4D00 / 898C00` |
| `4` | fixed `8E / 8D` | direct factory path |

Other audited list anchors are manager destruction
`0x593D0/FUN_0070D290/0x0070D2D0`, count
`0x59AB0/FUN_0070D970/0x0070D9B0`, code lookup/invoke
`0x59AF0/FUN_0070D9B0/0x0070D9F0`, and the base state machine
`0x59BC0/FUN_0070DA80/0x0070DAC0`.

The class-family strings and UI record tables support presentation labels only.
They do not prove gameplay-effect meaning, countdown, stacking, or expiry.

## Direct application mappings

### Record `0x99` callback

The full callback starts at BTL file `0x8BDC0`, preserved
`FUN_0073FC80`, live `0x0073FCC0`. It is installed at resident vtable slot
`+0x30`; the resident vtable is at `0x005E0390`.

Live target `0x0073FC90` is a different small helper; the export's overlapping
`FUN_0073FC90` label is not this callback's entry.

When object `s16 +0x78 == 0x99`, it resolves a fighter from side byte `+0x8A`
and calls:

```text
FUN_00305C30(fighter, 0x0D, 0x96, 1)
```

The callsite is BTL file/Ghidra/live
`0x8BE30/0x0073FCF0/0x0073FD30`. Effect `0x0D` is outside the low-ID
normalization switch, so requested countdown `150` is retained. The callback
then queues notification code `7` and performs base cleanup.

The numeric relation between record `0x99`, effect `0x0D`, and notification
code `7` is proven. A semantic name is not; nearby poison-named strings have no
direct binding to this callback.

### Other direct numeric mappings

One BTL object path checks object `s16 +0x78` and makes these calls:

| Object value | Requested call | File / Ghidra / live callsite |
| ---: | --- | --- |
| `0xAC` | Effect `07`, requested `100`, route `1` | `0x8531C / 0x007391DC / 0x0073921C` |
| `0xAF` | Effect `01`, requested `120`, route `1` | `0x85344 / 0x00739204 / 0x00739244` |

Both effect IDs are below `0x0D`, so these are requested rather than
necessarily final stored countdowns.

BTL contains many other effect applications in character and battle-controller
code. Representative generic callers include:

| Role | Function file / Ghidra / live | Apply call file / Ghidra / live |
| --- | --- | --- |
| Three-slot item dispatcher | `5D820 / FUN_007116E0 / 00711720` | `5D908 / 007117C8 / 00711808` |
| Hit/result metadata path | `7A840 / FUN_0072E700 / 0072E740` | `7A954 / 0072E814 / 0072E854` |
| Resolver wrapper | `7C170 / FUN_00730030 / 00730070` | `7C1E4 / 007300A4 / 007300E4` |
| General wrapper | `CB580 / FUN_0077F440 / 0077F480` | `CB5B4 / 0077F474 / 0077F4B4` |

The resolver wrapper obtains its fighter from `FUN_007341A0`, forwards its
second and third arguments as effect ID and requested countdown, and uses
route `1`. When its fourth byte argument is `1`, resident
`FUN_002247A0(fighter) == 1` suppresses the application; other fourth-argument
values bypass that extra guard.

The general wrapper accepts a small controller object. When controller
`+0x48 == 0`, it applies the requested ID/countdown to fighter pointer `+0x44`
with route `1`, then writes the requested ID to controller `+0x80`. Because
`FUN_00305C30` is void, that write occurs even when gameplay-node construction
failed. Controller `+0x80` is therefore a request/lifecycle cache, not proof
that the effect is active.

The absolute target in each BTL JAL is resident `0x00305C30` and is already a
live address.

### Resident condition-list dispatcher

`FUN_001FD330` at runtime/file `0x001FD330/0xFD430` walks a resident
configuration list of `u16` codes and applies default-countdown effects to the
selected fighter. The function is gated by `FUN_00250820() == 0` and requires
the list and both fighter pointers. Its clean switch mapping is:

| Input code(s) | Effect ID(s) | Rule |
| --- | --- | --- |
| `0x41..0x47` | `0x74..0x7A` | `effect = code + 0x33` |
| `0x48` | `0x7D` | explicit |
| `0x49..0x54` | `0x7E..0x89` | `effect = code + 0x35` |
| `0x56` | `0x7C` | explicit |
| `0x57` | `0x7B` | explicit |
| `0x5B` | `0x39` | explicit |

Every mapped call is `FUN_00305C30(fighter,id,-1,1)`. Definition routing then
matters: `0x7D` is linked plus local, while `0x7E..0x89` are linked-only.
Input `0x55` is not an effect application; it writes float `0.5`
to the other fighter's `+0x6C`. These numeric mappings are proven, but the
configuration codes' user-facing names are not.

### Additional literal BTL calls

Raw JAL inventory found the following direct literal requests in addition to
the table-driven and object mappings above. These are application provenance,
not semantic effect names:

| Requested call `(id,countdown,route)` | BTL callsite(s), file / Ghidra / live |
| --- | --- |
| `(07,-1,1)` | `7C300/007301C0/00730200`; `7C388/00730248/00730288`; `8F994/00743854/00743894`; `10CC94/007C0B54/007C0B94`; `10CD8C/007C0C4C/007C0C8C`; `18B6B8/0083F578/0083F5B8` |
| `(07,150,1)` | `91CCC/00745B8C/00745BCC` |
| `(07,85,1)` | `A850C/0075C3CC/0075C40C` |
| `(07,80,1)` | `ABDC0/0075FC80/0075FCC0` |
| `(00,200,1)` | `1417E8/007F56A8/007F56E8` |
| `(06,600,1)` | `148614/007FC4D4/007FC514` |
| `(01,100,1)` | `14E830/008026F0/00802730` |
| `(06,300,1)` | `14E89C/0080275C/0080279C` |
| `(06,250,1)` | `1AC31C/008601DC/0086021C` |
| `(04,250,1)` | `1AC368/00860228/00860268` |
| `(0C,-1,1)` then `(05,-1,1)` | `1D9838/0088D6F8/0088D738` then `1D9850/0088D710/0088D750`; duplicated at `1D9938/0088D7F8/0088D838` then `1D9950/0088D810/0088D850` |

All IDs in this table are below `0x0D`; explicit nonnegative values are still
subject to `FUN_00306980`, while `-1` first resolves the definition default.
The table therefore records requested, not necessarily stored, countdowns.

### Remaining direct resident application sites

The direct resident JAL inventory adds these otherwise-unlisted callers:

| Caller | Proven request | Runtime / file callsite |
| --- | --- | --- |
| `FUN_00227CE0` | Caller-supplied effect and countdown, route `1`, after its resource/state predicate | `0x00227E7C/0x127F7C` |
| `FUN_0025CEE0` | Selects one of `02,03,05,08,09,0B,0C`, requested `450`, route `1` | `0x0025D180/0x15D280` |
| `FUN_00299100` | Effect `39`, default input `-1`, route `1`, only after an exact membership miss and other guards | `0x002991C4/0x1992C4` |
| `FUN_0029B8A0` | Effect `04`, requested `360`, route `1` | `0x0029BB60/0x19BC60` |
| `FUN_002D5320` | Effect `07`, requested `120`, route `1` | `0x002D57FC/0x1D58FC` |
| `FUN_00307690` | Caller-supplied effect, default input `-1`, route `1` | `0x003076A0/0x2077A0` |

Effects `04` and `07` in this table are low normalized IDs. The random
selector's complete status/resource branch is narrowed below without naming
its outcomes.

### Character callback's random status/resource branch

`FUN_0025CEE0` enters this branch only when `FUN_00217860(fighter)` returns
action value `3` and primary-timeline halfword `+0x1BA` bit `0` is set. It
initializes selected effect to `-1` and HP request to zero, then reads the
current primary cursor `+0x1C4`:

| Cursor | RNG call bounds and branch | Result |
| ---: | --- | --- |
| `30` | Draw `0..1`: `0` / `1` | Effect `03` / `02` |
| `40` | Draw `0..1`: `0` / `1` | Scaled HP request `0.025` / effect `0C` |
| `50` | Draw `0..5`: `0,4` / `1,2,3` / `5` | Scaled HP request `0.025` / effect `05` / no status or HP request |
| `60` | Draw `0..15`; `7` selects effect `09`. After a miss, draw `0..7`; `3` selects `08`. After that miss, draw `0..7`; `1` selects `0B` | First matched effect, or no status/HP request if all tests miss |
| `75` | Draw `0..3`: `2` / every other value | Scaled HP request `0.05` / `0.025` |
| Every other cursor | No random branch | No status or HP request |

Instructions at `0x0025CF48` preserve RNG bound `3` into the cursor-`75`
call; `0x0025CF30` supplies `5` for the cursor-`50` branch. At cursor `60`,
`a0 = 7` from `0x0025D0AC` remains the second RNG call's argument at
`0x0025D0C4`; the decompiler omits it. The third explicitly reloads `7`.
The six cursor-`50` dispatch pointers at runtime/file
`0x005C3370/0x4C3470` confirm its no-action lane `5`. Bounds use the
`FUN_00180210` modulo contract documented in
[Resident randomness](../../runtime/randomness.md#mt-wrappers); they are not
empirically measured selection frequencies.

A selected effect is requested with countdown `450` and route `1`, then
`FUN_00204450(fighter,0)` runs even if the application failed. HP branches
instead scale through `FUN_00224DF0(input,fighter,fighter)` and call the HP
adder with `(1,0)` flags before separately queuing numeric notification `1`
when its manager exists. The branch does not debit chakra or consume an item
slot. These are mutually selected status/resource requests inside this
callback, not a generic rule preventing their later coexistence with other
effects. No gameplay name or full native trigger reachability is inferred
from action value `3` alone.

Together with the condition-list dispatcher, per-fighter family code, item
dispatchers, effect-`0x22` successor, inherent `-2` installer, route recursion,
and effect-`0x09` toggle documented elsewhere, this accounts for every direct
JAL to `FUN_00305C30` in the clean resident executable. The BTL tables,
wrappers, object paths, and literal calls above likewise account for every
direct BTL JAL. This completeness claim does not include hypothetical indirect
or dynamically selected calls.

## Exact BTL generic-list helpers

Both effect containers use the shared BTL intrusive-list helpers: node
constructor live `0x00709AA0`, list constructor `0x00709BC0`, append
`0x00709E60`, unlink plus virtual destructor `0x00709EA0`, clear
`0x00709F40`, the self-removal traversal `0x00709C70`, and the node-slot
`+0x0C/+0x14/+0x18` passes `0x00709BF0/0x00709D60/0x00709DE0`. Their
contracts, complete-file offsets, and preserved export labels, including the
export's `FUN_00709E60` that labels the unlink routine rather than live append
`0x00709E60`, belong to
[Battle entities](../session/battle_entities.md#generic-intrusive-node-and-list-contracts)
and its [BTL address audit](../session/battle_entities.md#btl-liverawexport-audit).
