# Battle status effects and item-effect lifecycle

This document records the clean-NA2 resident status-effect system and the BTL
callers that apply it. It covers definition records, per-fighter storage,
application and replacement, countdown normalization, expiry and removal,
item-driven effects, and the boundary between gameplay state and battle UI.

The findings are static unless explicitly stated otherwise. Numeric effect and
item IDs are kept numeric where no gameplay consumer proves a semantic name.
UI labels and nearby class names are not treated as proof of gameplay meaning.
Related presentation behavior is documented in
[`localization/ui/battle/item_status.md`](../localization/ui/battle/item_status.md).
Binary identities and address conventions are defined in
[Standard game file identities](../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** Clean NA2 battle status effects and item effects, including
  application, storage, definitions, countdown behavior, replacement,
  coexistence, expiry, removal, item-driven provenance, and the boundary
  between gameplay state and presentation.
- **Exploration depth:** Static and direct-call coverage is exhaustive for:
  - all 138 effect-definition records, their categories, countdowns, flags,
    presentation selectors, display descriptors, and 19 specialized
    constructors;
  - the generic resident lifecycle, both per-fighter lists, every registered
    specialized constructor and destructor, callback return behavior, bulk
    cleanup calls, and direct exact-ID removals;
  - every direct resident and BTL call to the high-level application function,
    separating literal requests from tables, wrappers, routing, and dynamic
    arguments;
  - all 116 item-metadata records, every direct-effect field, every BTL
    object-definition leading code, and the pickup, selected-use, delayed-use,
    hit-carried, and three-slot inventory paths that consume them;
  - the complete 19-row three-slot status table, its effect lanes, unread
    interleaved words, recovery branches, inventory consumption, and NUN5
    comparison;
  - all five field-item selector pools and fixed BTL distributions, their
    direct callers, authored weights, and RNG modulo boundary; and
  - the BTL generic-list helpers used by the effect containers, including raw
    instructions omitted or shifted in the preserved export.

  Status-presentation coverage includes the complete effect-to-notification
  and auxiliary visual-selector maps, Fukidasi factory dispatch, authored UI
  record maps, and independent list lifecycles. Rendering, animation beyond
  removal conditions, and localization semantics were not investigated.

  Direct application and removal sites are covered exhaustively, while the
  surrounding character and battle-controller state machines were sampled only
  where needed to establish status-facing behavior.
- **Confirmed coverage:** Binary and address identities; definition, fighter,
  node, inventory, auxiliary, and notification layouts; same-ID replacement;
  different-ID coexistence; sentinel and zero-countdown behavior; normalization
  and gated expiry; removal and cleanup order; linked/local routing; direct
  item/effect mappings; item `0x5B`'s dual path; effect `0x22`'s successor; and
  the separation of gameplay membership from caches, inventory, auxiliary
  visuals, and notifications.
- **Unresolved or untested:** User-facing meanings for most effect IDs and
  removal reasons; gameplay names for most definition payload fields and
  non-routing flag predicates; the engine phase of the secondary callback;
  the consumer of the `0x65/0x12` interleaved pair; ordinary-runtime reachability
  of the six-code selected-use fallback and recovery distribution;
  indirect or dynamically constructed calls; and most
  surrounding character-specific state machines.
- **Deliberate exclusions and overlap:** Substitution, damage formulas, broader
  timing work, rendering, media, and localization are outside this document.
  Field-item names remain owned by the localization reference. Status UI is
  covered only to establish its mapping and lifetime boundary with gameplay.
- **Evidence limitations:** Findings are static clean-binary results. No gameplay
  execution, runtime trace, or empirical countdown timing was performed. Raw
  instructions resolve export gaps and the NUN5 table provides cross-version
  corroboration, but neither substitutes for NA2 runtime validation. Results
  for externally duplicated nodes, cleanup-time list mutation, and repeated
  replacement describe code paths rather than observed runtime behavior.
  Code `29`'s user-supplied identification and external naming evidence are
  qualified in the [field-item name reference](../localization/field_item_names.md#code-29-curse-tag-chakra-points-seal).

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

The exact gameplay names of those fields remain unresolved. Fold helpers
`FUN_00306BD0..FUN_00307320` traverse every node whose countdown is nonzero and
consume other payload fields. This proves that different effect IDs can
contribute concurrently, but this document does not assign stat/formula names
without a proven consumer.

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
or another side-effecting zero-return callback. This audit is why callback
return is not a proven expiry mechanism for any clean registered gameplay
effect.

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
user-facing effect names.

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

The generic node layout is:

| Node offset | Proven role |
| ---: | --- |
| `+0x00` | Base flags byte; bit `0` is a generic removal trigger |
| `+0x02` | Base magic/tag `0x474F` |
| `+0x18` | Previous node |
| `+0x1C` | Next node |
| `+0x50` | Node vtable |
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

Effect `0x22` is a deliberate special case to the intuitive result: destroying
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
remove effect `0x07`. The `FUN_0020D690` family-removal loop deliberately
skips IDs `0x68+`; those table rows prove fighter/effect association, not
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
the per-node countdown traversal. This distinction prevents those predicates
from being misreported as lifetime rules.

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
self-removal traversal. Audit of every registered gameplay-effect vtable found
that node slot `+0x10` returns zero, even when it has side effects. No clean
registered gameplay effect is therefore proven to self-remove through that
callback return. The remaining generic trigger there is node base-flags bit
`0`. Auxiliary status-visual objects are different: `FUN_00303D40` can return
one when their animation/countdown completes, allowing their removal.

This post-countdown traversal is called even when the `FUN_003059B0`
countdown-pass gate is false. Side-effecting slot-`+0x10` callbacks can
therefore still run on such an update; the gate controls countdown ticking,
not that callback traversal.

`FUN_00305C00` at `0x00305C00/0x205D00`, called at
`0x00250758/0x150858`, performs a secondary callback pass through gameplay
node vtable `+0x14` and the auxiliary list. The exact engine phase is
unresolved, so it should not be labelled as a second gameplay tick or render
pass without further evidence.

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

These are static mutation-order results. No runtime checkpoint was used to
observe the hard-clear survivor.

## Random field-item selection

### Selector contract and pools

Resident `FUN_003AE890` at runtime/file `0x003AE890/0x2AE990` chooses an item
identity. Its input is a sequence of eight-byte `(pool_kind,
threshold_increment)` pairs. It draws one integer from the inclusive range
`0..99`, compares it to the current cumulative threshold with `<=`, and adds
the next row's increment after a miss. After row zero, loading a zero pool kind
terminates the sequence; kind `0` is therefore usable as a pool only in row
zero. If no pool yields a nonzero result, the function returns fallback code
`04`.
Both clean fixed distributions reach cumulative threshold `100`, so that
fallback is unreachable for their `0..99` draw. A shortened distribution would
produce code `04`; metadata identifies it as kind `2`, flags `0x0040`, amount
`0.75` on the positive-resource path.

The five implemented pool kinds are:

| Kind | Item-code lanes | In-pool selection | Clean resident source |
| ---: | --- | --- | --- |
| `0` | `02,03` | uniform, `1/2` per lane | runtime `0x006047A0,0x006047A4`; file `0x5048A0,0x5048A4` |
| `1` | `06,07,08,09,0A,0B,0C,25,27,2B,0D,0E` | modulo-12 draw; nominal `1/12` per lane | runtime/file `0x005B3C10..0x005B3C3F / 0x4B3D10..0x4B3D3F` |
| `2` | `24,23,27,25,2B,28,26,29,2A,2B,2C,2E,2F,30,31` | modulo-15 draw; nominal `1/15` per lane | runtime/file `0x005B3C40..0x005B3C7B / 0x4B3D40..0x4B3D7B` |
| `3` | `03` | deterministic | runtime/file `0x006047A8/0x5048A8` |
| `4` | `02,02` | deterministic result despite a two-lane draw | runtime `0x006047B0,0x006047B4`; file `0x5048B0,0x5048B4` |

Code `2B` deliberately occupies two lanes in pool `2`; this is part of its
native weight, not a duplicate to discard. The clean fixed BTL distributions
below do not reference pool `4`.

The 22 selector codes with source and official English names are owned by
[Field-item names](../localization/field_item_names.md#resident-field-item-name-table).
Codes `02` and `03` are outside that resident name table but follow the
positive-resource paths and have BTL internal identifiers `ItemRecoverLife` at
complete-file/live `0x1E4C20/0x00898B20` and `ItemChakraBall` at
`0x1E4C00/0x00898B00`, respectively. Code `29` is also outside the name
table; its metadata proves kind `3`, flags `0x0180`, and direct effect `0x0A`.
It is identified as **Curse Tag: Chakra Points Seal**; the
[name reference](../localization/field_item_names.md#code-29-curse-tag-chakra-points-seal)
records the user identification, UN2 naming source, and NUN5 translation limit.

### Fixed BTL distributions

BTL contains three byte-identical copies of the general distribution and two
copies of the recovery distribution:

| Distribution copy | Complete-file / live table | `(pool_kind, threshold_increment)` rows |
| --- | --- | --- |
| General A | `0x1DCDC0 / 0x00890CC0` | `(1,20),(2,60),(3,20),(0,0)` |
| Recovery A | `0x1DCDE0 / 0x00890CE0` | `(0,50),(3,50),(0,0)` |
| General B | `0x1DCE10 / 0x00890D10` | `(1,20),(2,60),(3,20),(0,0)` |
| Recovery B | `0x1DCE30 / 0x00890D30` | `(0,50),(3,50),(0,0)` |
| General C | `0x1DD160 / 0x00891060` | `(1,20),(2,60),(3,20),(0,0)` |

Because the draw includes zero and the comparison includes the threshold, the
authored increments are not the threshold-bucket sizes. General
selects pool `1` for rolls `0..20` (`21%`), pool `2` for `21..80` (`60%`),
and pool `3` for `81..99` (`19%`). Recovery selects pool `0` for `0..50`
(`51%`) and pool `3` for `51..99` (`49%`). The resulting nominal per-code
weights are:

General has 24 unique outcomes: all 22 codes in the resident name table plus
`03` and `29`. Recovery contains only `02` and `03`; the union is 25
codes.

| Code | General | Recovery |
| ---: | ---: | ---: |
| `02` | — | `25.5%` |
| `03` | `19%` | `74.5%` |
| `06` | `1.75%` | — |
| `07` | `1.75%` | — |
| `08` | `1.75%` | — |
| `09` | `1.75%` | — |
| `0A` | `1.75%` | — |
| `0B` | `1.75%` | — |
| `0C` | `1.75%` | — |
| `0D` | `1.75%` | — |
| `0E` | `1.75%` | — |
| `23` | `4%` | — |
| `24` | `4%` | — |
| `25` | `5.75%` | — |
| `26` | `4%` | — |
| `27` | `5.75%` | — |
| `28` | `4%` | — |
| `29` | `4%` | — |
| `2A` | `4%` | — |
| `2B` | `9.75%` | — |
| `2C` | `4%` | — |
| `2E` | `4%` | — |
| `2F` | `4%` | — |
| `30` | `4%` | — |
| `31` | `4%` | — |

The authored percentages in each column sum to `100%`. Pool `2`'s duplicated
`2B` lane contributes `8%`, which combines with its pool-`1` lane to produce
`9.75%`. The overlapping `25` and `27` lanes similarly combine to `5.75%`
each.

`FUN_00180210(n)` does not generate a mathematically uniform abstract draw; it
returns an unsigned 32-bit PRNG value modulo `abs(n) + 1`. For the top-level
modulo-100 draw, residues `0..95` each have one more source value than
`96..99`. For pool `1`, modulo 12 gives lanes `0..3` one extra source value;
for pool `2`, modulo 15 gives lane `0` one extra source value. Each difference
is one out of `2^32` source values per call. The table therefore records the
exact authored bucket/lane weights, while exact runtime frequencies also depend
on the PRNG state sequence and these negligible modulo biases.

### BTL call sites and limits

The clean raw BTL contains exactly four direct JALs to the resident selector.
One lies in a region the preserved export leaves undefined:

| Path | Complete-file / live wrapper | Complete-file / live selector call | Complete-file / live amount call | Distribution behavior |
| --- | --- | --- | --- | --- |
| A | `0x10A90 / 0x006C4990` | `0x10B80 / 0x006C4A80` | `0x10BA4 / 0x006C4AA4` | mode `1` selects Recovery A; every other mode selects General A |
| B | `0x11B20 / 0x006C5A20` | `0x11C10 / 0x006C5B10` | `0x11C34 / 0x006C5B34` | mode `1` selects Recovery B; every other mode selects General B |
| inline A copy | — | `0x12EC0 / 0x006C6DC0` | `0x12EE4 / 0x006C6DE4` | always General A |
| C | `0x1E220 / 0x006D2120` | `0x1E29C / 0x006D219C` | `0x1E2C0 / 0x006D21C0` | always General C |

Wrapper A is reached at complete-file/live `0x1099C/0x006C489C` and
`0x10A20/0x006C4920`; wrapper B is reached at `0x11A20/0x006C5920` and
`0x11AA8/0x006C59A8`. All four direct calls pass mode `0`. The inline call
copies General A and immediately passes its selected code to the spawn-amount
helper; its wider object semantics remain unresolved.

Wrapper C is reached at `0x1D030/0x006D0F30` or
`0x1D0B0/0x006D0FB0`, depending on an unresolved object state; each branch
calls it three times while varying one position component by a random offset
bounded by `10.0`. No direct call that selects either recovery table was
established. Indirect or dynamically scheduled use remains possible, so the
recovery distribution is authored and callable but not proven reachable by
the direct-call audit. The raw BTL contains exactly four direct JALs to
`FUN_003AEAF0`, paired with the four selector calls above; the resident ELF
contains no direct JAL to either function.

### Identity and amount boundary

Identity selection and spawn amount are separate. `FUN_003AE890` chooses the
item code; `FUN_003AEAF0` later applies the mode-aware Items amount setting to
reject or multiply spawn requests. The selector has no spawn-frequency input.

The amount helper reads Items through resident `FUN_001F6E40(manager)` at
runtime/file `0x003AEBA0/0x2AECA0`. Its base and probabilistic extra base calls
at `0x003AEC84/0x2AED84` and `0x003AECCC/0x2AEDCC` pass the selected item code.
Its final count-controlled loop instead calls `FUN_00373FB0` at
`0x003AED48/0x2AEE48` with literal code `04`. This is an additional source of
code `04`, independent of the identity selector's unreachable clean fallback.
The resident records for `03` and `04` both have kind `2` and flags `0x0040`;
their resource amounts are `5.0` and `0.75`, respectively.

`FUN_00373FB0` rejects a zero item code at `0x00373FC0..0x00373FD4`, but that
return does not stop the amount helper's subsequent code-`04` loop. A zero
identity therefore suppresses only the corresponding base requests, not the
complete amount-helper call. These branches and their exact call bytes were
checked through GhidrAssist against the resident executable.

Lane multiplicity determines native relative weights. Code `2B` owns two
pool-`2` lanes, while codes `25`, `27`, and `2B` occur in both general pools.
The general and recovery distributions are independent authored data. The
identity selector has no global spawn-frequency input, and its native
fallthrough result is code `04`.

Only the 24 general outcomes have established direct-call behavior. The
recovery set is authored and callable but has no proven direct runtime consumer.

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

Item `0x5B` has both mechanisms. A successful delayed use first reaches its
three-slot activation row, applying effect `0x05` with requested countdown
`180` to the using fighter. The spawned row-`0x7E` hit object carries code
`0x5B`; if its hit/result path runs on another fighter, that path separately
applies effect `0x06` with default input `-1` to the struck fighter. Codes
`0x54`, `0x57`, and `0x6E` have no three-slot status row and use their
hit-carried effect `0x07` path instead.

## Three-slot battle-item path (`0x51..0x73`)

### Collection and inventory ownership

Resident `FUN_00374190` at `0x00374190/0x274290` resolves pickups in this
range. All 19 rows described below have metadata flag `0x80`, so collection
adds them to the battle-item inventory rather than directly applying fighter
status. It calls BTL inventory-add file/Ghidra/live
`0x5C140/FUN_00710000/0x00710040` at resident callsites
`0x003742D4/0x2743D4` for side 0 and `0x00374310/0x274410` for side 1.
Each of the 19 row-backed codes adds one. Code `0x6A` is the sole special
pickup that adds three, but it has no row in this status table.

The panel holds three slot pointers at `+0/+4/+8`, side at `+0x20`, and the
selected slot index at `+0x24`. A slot stores item code at `+0` and signed count
at `+4`; count is capped at nine.

Fighter input gate `FUN_002366F0` (`0x002366F0/0x1367F0`) checks fighter
`+0x338` bit `0x01000000`. At `0x00236988/0x136A88` it calls
`FUN_00375630(item_manager, fighter_side)`, masks the returned selected-item
byte, and passes fighter plus that byte to
`FUN_00236C70(fighter,item)` at `0x002369A0/0x136AA0`. Raw instructions prove
the second argument even though the C export drops it.

Eighteen rows are ordinary kind `4` and route immediately through resident
`FUN_00375690`; its callsite in `FUN_00236C70` is
`0x00236DD0/0x136ED0`. The resident helper selects item-manager panel pointer
`+0x6C` for side `0` or `+0x70` for side `1` and enters BTL live
`0x00711380`. Item `0x5B` is the sole kind-`3` exception: it stores
the pending code at fighter `s16 +0xB70`, starts an item-use action, and reaches
the same activation only after later hit/interaction checks. Its delayed BTL
call to `FUN_00375690` is at file/Ghidra/live
`0x843CC/0x0073828C/0x007382CC`. That activation is the user-side
effect-`0x05` half of the separate dual path documented above. If those
interaction checks fail, the activation/decrement path is not reached; item
`0x5B` therefore differs from the 18 immediate rows in when consumption
becomes committed.

BTL panel activation is file `0x5D480`, preserved `FUN_00711340`, live
`0x00711380`. It resolves the fighter, calls the status dispatcher, then
consumes one matching slot count through BTL helper
`0x5C3D0/FUN_00710290/0x007102D0` at
file/Ghidra/live callsite `0x5D7E0/0x007116A0/0x007116E0`, and sets panel
byte `+0x61 = 1`.

The inventory operation is also non-transactional with gameplay status.
`FUN_00305C30` is `void`, the row dispatcher returns no per-effect success to
the panel, and the panel performs the slot decrement after dispatch. Once one
of these 19 row-backed activations reaches this path, an application rejected
by a same-ID `-2` node or a fighter guard does not preserve the item count.
Other actions in the row dispatcher, including the special recovery branches,
likewise have their own control flow and are not rolled back with a rejected
status node.

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

After a matching row and its optional recovery actions, the dispatcher calls
a BTL side/battle helper with `(panel_side + 1, 6, 1)` at
file/Ghidra/live callsite `0x5DA08/0x007118C8/0x00711908`. The encoded JAL
target is already-live `0x00715F90`; its actual wrapper starts at complete-file
`0x62090`, nominal Ghidra `0x00715F50`. The preserved export's
`FUN_00715F90` begins at complete-file `0x620D0`, live `0x00715FD0`, and is a
different adjacent wrapper. This is another place where adding or omitting the
MWo3-header shift selects the wrong function.

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
Enumerations that treat those interleaved values as effects conflict with the
dispatcher loop and the clean row bytes.

NUN5's homologous `0x2F8`-byte table at complete-file/live
`0x1EDBD0/0x008B48D0` is byte-identical. Its dispatcher is
file/Ghidra/live `0x60320/FUN_00726FE0/0x00727020` and calls resident homolog
`FUN_00310580`. This cross-version match corroborates the row layout but does
not replace NA2 runtime verification.

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
unresolved and the word may be unused legacy metadata.

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
Input `0x55` is deliberately not an effect application; it writes float `0.5`
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

The selector in `FUN_0025CEE0` is driven by internal state and RNG branches;
the set above and requested value are proven, but semantic names for the
outcomes are not. Effects `04` and `07` in this table are low normalized IDs.

Together with the condition-list dispatcher, per-fighter family code, item
dispatchers, effect-`0x22` successor, inherent `-2` installer, route recursion,
and effect-`0x09` toggle documented elsewhere, this accounts for every direct
JAL to `FUN_00305C30` in the clean resident executable. The BTL tables,
wrappers, object paths, and literal calls above likewise account for every
direct BTL JAL. This completeness claim does not include hypothetical indirect
or dynamically selected calls.

## Exact BTL generic-list helpers

Some helpers start inside export undefined-byte gaps. The complete-file and
live anchors below are authoritative.

| Role | BTL file | Preserved Ghidra/export | Live |
| --- | ---: | --- | ---: |
| Base node constructor | `55BA0` | nominal `00709A60` | `00709AA0` |
| Base destructor | `55C60` | `FUN_00709B20` | `00709B60` |
| List constructor | `55CC0` | nominal `00709B80` | `00709BC0` |
| Dispatch node vtable `+0x0C` | `55CF0` | `FUN_00709BB0` | `00709BF0` |
| Self-removal traversal | `55D70` | `FUN_00709C30` | `00709C70` |
| Dispatch node vtable `+0x14` | `55E60` | `FUN_00709D20` | `00709D60` |
| Dispatch node vtable `+0x18` | `55EE0` | `FUN_00709DA0` | `00709DE0` |
| Append | `55F60` | nominal `00709E20` | `00709E60` |
| Unlink + virtual destructor | `55FA0` | `FUN_00709E60` | `00709EA0` |
| Clear | `56040` | `FUN_00709F00` | `00709F40` |

Do not confuse the live append entry `0x00709E60` with Ghidra's shifted
`FUN_00709E60`, which labels the unlink routine.
