# Awakening and transformation gameplay

This document records the awakening controller, persistent effect state,
post-Ultimate-Jutsu form replacement, and cleanup boundaries in retail NA2
(`SLPS-25837`).

The native implementation has three related but independent states:

1. the fighter controller's awakened marker and character-specific trigger;
2. one or more nodes in the fighter's generic effect container; and
3. for effects `0x68..0x73`, replacement of the live character ID and its
   loaded fighter resources.

An effect can exist without the controller marker, and the marker can be
cleared without deleting an effect. A transformed fighter is reconstructed
with a protected effect node, rather than obtaining all of its state from the
base fighter's controller. Treating these layers as one `is_awakened` value
loses observable native distinctions.

The native combo object is described in [Combo accounting](combo_accounting.md);
the current, match-start, and live-fighter identity fields in
[Character identity in battle](character_ids.md).

## Research coverage

- **Assigned scope:** battle awakening and transformation state: controller
  eligibility and triggers, character/effect/form mapping, controller and
  effect flags, post-UJ replacement and transformed-form adoption, exit and
  reset cleanup, the resident/BTL ownership boundary, and selected ordinary and
  transformed character parameter overrides.
- **Exploration depth:**
  - Complete table decodes: 94 trigger-descriptor rows at `0x005C1B50`, 94
    association rows at `0x005C1D30`, all 223 UJ records at `0x005AEC40`, all
    94 character UJ lists, per-character defaults at `0x005AFDB0`, the
    94-entry character factory/record table, the 12 class-3 effect records,
    and the 12-row effect-notification map at `0x005B0040`.
  - Direct/raw-`jal`, absolute-word, and `lui` plus immediate scans of BTL for
    the controller, form-map, request, effect, and table targets; constant
    callsites are enumerated wherever this document says "sole," "all," or
    "exactly."
  - Resident traces: dispatcher and entry/cleanup family
    `FUN_0020CF40..FUN_0020EA90`, altitude control `FUN_0020EAE0`, generic
    effect creation/removal `FUN_003047C0..FUN_00306980`, UJ completion
    `FUN_0035AF20 -> FUN_0035B3B0`, record helpers
    `FUN_003729F0..FUN_00372D00`, request `FUN_001EC5E0`, route-`8` states
    `0x17/0x18`, manager save/reset, and the old-hub destruction and
    new-fighter setup chain.
  - Character code: Deidara/Gaara callbacks, mode setters, and action-slot
    partitions; Choji's constructor, setter, and callback; selected Loopy Fist
    Lee and Nine-Tailed Fourth callbacks; all 12 base/form record pairs.
  - BTL traces bounded to the metadata consumer at live `0x00709860`, the UJ
    presentation at live `0x00769790`, result-bank wrappers at live
    `0x00715F60..0x00716050`, and the pause-controller lifecycle at live
    `0x0076E9D0`.
- **Confirmed coverage:** exact trigger/association data; ordinary, class-7,
  and Naruto-specific entry paths; the HP, combo, item/projectile, and
  action-progress predicates; the independence of controller marker,
  effect-list state, and live character form; class-3
  creation/persistence/removal; ordinary insertion-failure handling;
  Konohamaru's surviving timed effect after class-7 mismatch; the
  Deidara/Gaara stick-sector override, ascent/descent consumer, and action
  variants; all 12 UJ effect-to-character mappings; the UJ completion gates,
  including outcome `2` and opposing-side metric-`14` credit; the state-`0x17`
  replacement and reconstruction order; saved-identity restoration; the
  transformed-adoption statistics increment; neutral inherent form-effect
  payloads and the 12 copied stat-field comparisons; Choji's marker-selected
  ground target; the reserved/incomplete `0x4A` slot; the post-UJ outcome
  effect, its exact match with the non-transformed `FUN_0020D030` adoption
  pairs, and its loss under contest type `0`.
- **Unresolved or untested:**
  - The exact visible moment of marker, effect-node, character-ID, and
    rebuilt-object changes; the visible result of the Konohamaru class-7
    mismatch; the exact visible timing of the action-progress trigger.
  - Which character and UJ record the contest-type-`0` runtime experiment
    used. For a non-transforming record the static outcome-effect path
    explains the observation; for one of the 12 transforming records no
    static dependency of the form request on contest type was found (see
    [Post-UJ outcome effect](#post-uj-outcome-effect)).
  - Whether skill plays of class-7 records also seed the outcome effect, and
    the use of UJ record `0`, whose effect field is `0`.
  - Later character overrides of the copied parameter fields beyond the
    selected paths; arbitrary indirect BTL computation.
- **Deliberate exclusions and overlap:**
  - Generic effect-list mechanics belong to
    [Battle items and status effects](battle_items_and_status_effects.md);
    effect aggregation and damage formulas to [Damage](damage.md).
  - UJ connection, contest, and skill-play admission belong to
    [Ultimate Jutsu](ultimate_jutsu.md); the command interpreter and
    move/input bindings to [Action commands](action_commands.md).
  - The result bank belongs to [Battle statistics](battle_statistics.md);
    session rebuild, save/restore, and statistics-bank reload to
    [Battle lifecycle](battle_lifecycle.md); the pause controller to
    [Pause and replay](pause_and_replay.md); the combo object to
    [Combo accounting](combo_accounting.md).
  - Shared movement fields belong to
    [Movement and physics](movement_and_physics.md); callback dispatch to
    [Character action callbacks](character_action_callbacks.md); response
    modifiers to [Hit response](hit_response.md).
  - Adventure mode and animation internals are excluded.
- **Evidence limitations:** conclusions are static analysis of the two clean
  binaries, plus the modified-runtime observation recorded under
  [Post-UJ outcome effect](#post-uj-outcome-effect).
  Arbitrary indirect BTL computation was not exhaustively audited. A store
  displacement alone does not identify its destination object; the parameter
  findings distinguish fighter, stack, and scratch bases.

## Evidence identity and address mapping

Address conversions follow
[Retail game file identities](../game/files/file_identities.md#address-conventions);
the BTL header fields are listed in
[Overlay ABI](../runtime/overlay_abi.md#exact-clean-layouts). Resident
`gp = 0x0060A9F0`; a `gp`-relative address is that value plus the
instruction's sign-extended 16-bit displacement.

Confidence labels used below are:

- **High**: direct clean-binary instructions, fields, table bytes, or exhaustive
  direct/conventional reference scans;
- **Medium**: a role inferred from control flow, or a negative scan that cannot
  exclude arbitrary indirect address computation;
- **Open**: the numeric behavior is known but its gameplay name is not.

## Resident ownership and the BTL boundary

Core awakening ownership is resident. BTL contains no decoded direct call, raw
`jal`, direct data operand, or conventional `lui` plus immediate reference to:

- controller functions `FUN_0020CF40`, `FUN_0020D030`, `FUN_0020D5D0`,
  `FUN_0020D690`, `FUN_0020D910`, `FUN_0020DD20`, `FUN_0020DDC0`, or
  `FUN_0020E280`;
- transformed-form constructor `FUN_00305FF0` or mapping
  `FUN_00372D00`;
- trigger table `0x005C1B50` or association table `0x005C1D30`;
- form request `FUN_001EC5E0` or its post-Ultimate-Jutsu owner
  `FUN_0035B3B0`.

This is a high-confidence static negative for ordinary references, not proof
against an exotic computed indirect call.

BTL does consume adjacent Ultimate-Jutsu metadata:

| BTL use | Exported | Live | File | Observed effect |
| --- | ---: | ---: | ---: | --- |
| `FUN_00372B10` call | `0x007098E8` | `0x00709928` | `0x00055A28` | Copies the selected UJ record's effect ID into descriptor `+0x0A` |
| `FUN_00372C00` call | `0x007697E0` | `0x00769820` | `0x000B5920` | Reads UJ category for battle-side construction |
| `FUN_00372C00` call | `0x00769B54` | `0x00769B94` | `0x000B5C94` | Reads UJ category for battle-side construction |

The enclosing BTL function begins at exported/Ghidra `0x00709820`, live
`0x00709860`, complete-file `0x00055960`. It obtains a UJ record index from BTL
per-side state `+0x38`, validates a value returned by resident
`FUN_00372C40` into descriptor `+0x08`, stores the `FUN_00372B10` result at
`+0x0A`, and sends the descriptor through an indirect resident constructor
table at `0x005A2900`. This propagates transform-capable metadata into
battle-object construction; it neither applies the effect nor requests a form
replacement.

BTL has 23 decoded calls to generic effect entry `FUN_00305C30`. Its immediate
IDs are only `0`, `1`, `4`, `5`, `6`, `7`, `0x0C`, and `0x0D`. One table-driven
site can select `2`, `3`, `5`, `6`, `8`, `9`, `0x0C`, `0x11`, `0x12`, `0x3C`,
or `0x65`; three wrappers accept dynamic caller values. No BTL site explicitly
constructs a transformed-form effect `0x68..0x73`, although the dynamic
wrappers are not range-proofed. Its six decoded `FUN_00305510` removal calls
likewise use only IDs `0`, `1`, `4`, `6`, `7`, and `0x0A`.

**Conclusion, high confidence:** descriptor eligibility, state flags,
association lookup, form mapping, and controller cleanup are resident-owned.
BTL's proven awakening-adjacent role is UJ metadata propagation plus generic
effect-list services.

The resident controller calls three live BTL targets. These operands are
already live addresses:

| Observed use | Live target | Complete-file offset |
| --- | ---: | ---: |
| Set command stick-sector widths | `0x006F09D0` | `0x0003CAD0` |
| Restore default stick-sector widths | `0x006F09E0` | `0x0003CAE0` |
| Per-side result-bank read wrapper | `0x00716050` | `0x00062150` |

The setter stores `f12` to `+0xA8` and `f13` to `+0xA4` of the fighter's
`ccCommand` input object at fighter `+0x24`; the restorer writes raw float
bits `0x3FC90FDB` (`pi/2`, 90 degrees) to `+0xA8` and `0x40278B7F`
(`5*pi/6`, 150 degrees) to `+0xA4`. Awakening activation supplies
`0x40060723` (`2*pi/3`, 120 degrees) to both fields. These are the variable
up/down and left/right stick-sector widths of the side's command interpreter;
the interpreter, its sector predicate, the restorer's use in generic
`ccCommand` initialization, and the direction-bit table are described in
[Action commands](action_commands.md#logical-mask-translation). No other BTL
instruction in the `ccCommand` implementation range reads or writes `+0xA4`
or `+0xA8`.


**Conclusion, high confidence:** in retail play the four absolute stick
commands use 150-degree left/right sectors and 90-degree up/down sectors. A
stick within 15 degrees of vertical sets only the vertical bit, 15 to 45
degrees sets both a vertical and a horizontal bit, and beyond 45 degrees sets
only the horizontal bit. Awakened Deidara `0x40` and Gaara `0x3B` switch the
variable pair to 120 degrees each, moving those boundaries to 30 and 60
degrees: up/down recognition widens by 15 degrees on each side and left/right
narrows by the same amount; the
fixed-width bits `0x10..0x200` are unaffected. Cleanup restores the 150/90
split.

The widened vertical sectors have a proven awakening-specific consumer.
Resident `FUN_00217320` copies `ccCommand +0xAC` to fighter `+0x338`; see
[Action commands](action_commands.md#resident-bridge-and-action-dispatch) for
the common input bridge. `FUN_0020EAE0` reads that word only for Deidara
`0x40` or Gaara `0x3B` with controller marker `+0x63:0x20` set. Its sole
direct caller is `FUN_0024DA50` at `0x0024DAA8`, after the same update route
calls the awakening dispatcher at `0x0024DA80`.

This consumer changes fighter vertical velocity `+0x998`, which
`FUN_0024A660` copies into the movement delta for position component `+0x38`.
Major actions `6` and `8` return without changing it. Up/down input is
accepted in major action `1`, or major action `0` with substate `0` or `4`:

- Bit `0x04` adds the upward increment and clamps to the upward limit. It
  has priority when both vertical bits are set.
- Otherwise bit `0x08` adds the negative downward increment and clamps to
  the substate-`4` limit or the ordinary downward limit. This branch clears
  gravity scalar `+0x9B4`.
- With neither accepted input, including other major/substate combinations
  except `6` and `8`, the function clears `+0x9B4` and moves velocity toward
  zero without crossing it. Negative velocity uses the ordinary return
  increment; positive velocity uses the major-`4` increment in major action
  `4` and the ordinary increment otherwise.

The complete seven-float consumer records are Gaara's resident `0x004074F0`
and Deidara's `0x00407510` (ELF file offsets `0x003075F0` and `0x00307610`):

| Record field | Gaara `0x3B` | Deidara `0x40` |
| --- | ---: | ---: |
| `+0x00`, upward increment | `12.5` | `4` |
| `+0x04`, downward increment | `-3.75` | `-4` |
| `+0x08`, upward limit | `20` | `20` |
| `+0x0C`, ordinary downward limit | `-22.5` | `-20` |
| `+0x10`, substate-`4` downward limit | `-2` | `-2` |
| `+0x14`, ordinary return increment | `1.25` | `3` |
| `+0x18`, major-`4` positive-velocity return increment | `1.5` | `2` |

The bit tests are at `0x0020EBD4` and `0x0020EC10`; velocity writes and
clamps occupy `0x0020EBEC..0x0020EC58`, and the neutral return path is
`0x0020EC68..0x0020ECF0`. No time or distance unit is established here.
`FUN_00248EC0` explicitly bypasses its ordinary bit-`0x04` held-history
transition `(major,substate)=(0,0)->(0,3)` and bit-`0x08` transition
`(0,0)->(0,4)` for these same two awakened identities. The wider sectors
therefore affect direct ascent/descent control rather than routing through
those ordinary held-input transitions. Other move-specific uses of command
bits remain owned by the action-command research.

The read wrapper at live `0x00716050` returns one signed halfword of the BTL
result bank at live `0x008D6A80` (two `0x38`-byte side rows of 28 halfwords);
the bank and its clear/add/set/max wrappers are described in
[Battle statistics](battle_statistics.md#btl-score-tier-and-point-accumulator-handoff).
Awakening uses metric `10` ("Hidden power"; awakening-entry credits) and
metric `14` ("Defeat an enemy Ultimate"; defender interruption credit).

### Pause-controller gate

The pointer at resident `0x00607834` is the pause controller described in
[Pause and replay](pause_and_replay.md#shared-ownership-and-controller-lifecycle),
not an awakening object. Its signed byte `+0x10` is a three-state lifecycle
(`0` inactive, `1` construction pending, `2` child active), and BTL writes only
those three values. The awakening dispatcher permits normal descriptor work
when the controller is absent or its state is `0` (it also tolerates `-1`),
and suppresses it while state is `1` or `2`. This gate coordinates awakening
with the controller's presentation branches; it is not an awakening
eligibility resource or persistent transformed-state flag.

## Controller tables and fighter state

### Association table

The controller association table is 94 eight-byte entries at runtime
`0x005C1D30`, resident file `0x004C1E30`:

| Entry field | Meaning |
| ---: | --- |
| `+0x00` word | Inline effect ID when count is one; pointer to a `u16` array when count is greater than one |
| `+0x04` word | Associated-effect count; zero means no association |

`FUN_0020CF40` tests whether any associated effect is live through
`FUN_00306420`. `FUN_0020D690` validates a selected class-7 UJ effect against
the same list. `FUN_0020D910` chooses an entry for ordinary activation, and
`FUN_0020DDC0` reconciles controller state against the list. Membership is not
proof that a native trigger reaches that effect.

### Trigger descriptors

The trigger descriptor table is 94 four-byte records at runtime `0x005C1B50`,
resident file `0x004C1C50`:

| Entry field | Proven use |
| ---: | --- |
| `+0x00` signed `s16` | Passed to `FUN_002040D0(fighter,value,-1,1)` after ordinary entry when it is not `-1` |
| `+0x02` low byte | Dispatch flags consumed by `FUN_0020E280` |
| `+0x03` | Zero in every clean row |

Every non-`-1` first field in the clean active rows is `0x001F`. Its semantic
name is not established. Active rows with `-1` are character IDs `0x2E`,
`0x3B`, `0x3D`, `0x3E`, `0x43`, `0x44`, `0x46`, `0x47`, `0x4D`, `0x50`,
`0x51`, and `0x54`.

The flag meanings are:

| Bit | Route or predicate | Clean rows |
| ---: | --- | --- |
| `0x01` | Adopt an already-present or constructor-owned state through `FUN_0020D030` | Used alone and in combinations |
| `0x02` | HP `<= 0.15`, only Classic Hinata `0x0C` and Sasori (Hiruko) `0x4C` | `0x0C`, `0x4C` |
| `0x04` | Character-specific counter threshold | Classic Tenten `0x0D`, Tenten `0x42` |
| `0x08` | Native current-combo threshold through `FUN_0020D5D0` | `0x06`, `0x3C`, `0x41`, `0x48`, `0x56` |
| `0x10` | Raw fighter-state predicate through `FUN_002274C0` | Broad ordinary-trigger family |
| `0x20` | A Sakura-only branch exists in code | No clean descriptor uses it |
| `0x40` | Exact selected class-7 UJ effect through `FUN_0020D690` | `0x0A`, `0x0B`, `0x27..0x2B`, `0x55` |

The complete nonzero clean flag groups are:

| Flags | Character IDs |
| ---: | --- |
| `0x01` | `01..04`, `0E`, `0F`, `16`, `22..26`, `2F..39`, `3F`, `49`, `4B`, `5A`, `5D` |
| `0x02` | `4C` |
| `0x03` | `0C` |
| `0x04` | `42` |
| `0x05` | `0D` |
| `0x08` | `3C`, `48`, `56` |
| `0x09` | `06`, `41` |
| `0x10` | `07`, `10`, `12`, `13`, `3A`, `3B`, `3D`, `3E`, `45`, `47`, `4D`, `4E`, `4F`, `51..54`, `59` |
| `0x11` | `05`, `11`, `2E`, `40`, `43`, `44`, `46`, `50`, `57`, `5B`, `5C` |
| `0x40` | `0A`, `0B`, `27..2B` |
| `0x41` | `55` |

This exhaustive decode is useful for coverage, but it must be combined with
the hard-coded predicates. For example, not every bit-`0x01` row has a true
case in `FUN_0020D030`.

### Relevant fighter and manager fields

| Location | Type | Proven observation |
| --- | --- | --- |
| fighter `+0x00` bit `0x02` | bit | Gates the representative call to the controller from `FUN_0024DA50` |
| fighter `+0x60` | `u16` | Low bits select side and the per-side combo object |
| fighter `+0x62` bit `0x01` | bit | Suppresses ordinary controller dispatch and some effect classes |
| fighter `+0x63` bit `0x10` | bit | Paired special state used for Deidara `0x40` and Gaara `0x3B` |
| fighter `+0x63` bit `0x20` | bit | Controller's awakened marker |
| fighter `+0x68` | character ID | Live fighter form |
| fighter `+0x6C` | `float` | Normalized HP used by proven low-HP routes |
| fighter `+0x18A` | `u16` | Exact selected class-7 UJ effect |
| fighter `+0x18E` | `s16` | Major action state |
| fighter `+0x190` | `s16` | Action substate/index within the major state |
| fighter `+0x192` | `s16` | Phase within the current action |
| fighter `+0x1DC` | embedded `0x24`-byte object | Scalar action-progress tracker queried for exact/crossed positions |
| fighter `+0x8C4/+0x8C8/+0x8CC` | count/head/tail | Authoritative intrusive effect list |
| fighter `+0x8E8` | `s16` | Last successfully added effect ID cache; not cleared on removal |
| fighter `+0x956` | `u16` | Required to be zero by `FUN_002274C0` |
| fighter `+0xA4C` | pointer | Additional class-7 object-state gate |
| fighter `+0xA45` | signed byte | Pending accepted hits consumed by the combo object |
| fighter `+0xB78` | signed `s16` | Accepted item-use and Tenten projectile-create counter; not chakra |
| `0x006076B8/+0x006076BC` | pointers | Player 1/2 native combo objects; current count is signed `s16 +0x34` |
| `0x00607834` | pointer | Pause controller; signed byte `+0x10` is lifecycle `0/1/2` and gates dispatch |

The effect list, not `+0x8E8`, is current truth. There are only three resident
access families for `+0x8E8`: initialize to `0xFFFF`, write after successful
insertion, and a reader that cross-checks the live list. No removal path clears
it, so it may be stale.

## Per-fighter dispatch

`FUN_0024DA50` is a representative update caller. At `0x0024DA80`, while
fighter `+0x00` bit `0x02` is set, it calls `FUN_0020E280(fighter)` before the
remaining fighter update calls.

`FUN_0020E280` proceeds in this order:

1. If fighter `+0x62` bit `0x01` is set, return unless `FUN_0020EA90` succeeds.
   That helper succeeds only for Deidara `0x40` or Gaara `0x3B` while the
   controller marker `+0x63:0x20` is set.
2. If the pause controller at `0x00607834` is null, or its signed lifecycle
   byte `+0x10` is `0` or `-1`, continue normal descriptor handling. BTL
   writes only `0`, `1`, and `2` to that byte.
3. In lifecycle states `1` or `2`, suppress descriptor handling. An existing controller marker is
   cleared for ordinary characters, but preserved for IDs `0x2F..0x38`,
   `0x49`, `0x4A`, `0x4B`, and `0x51`. Clearing Deidara or Gaara also clears
   bit `0x10` and calls `SUB_006F09E0(fighter+0x24)`. No effect is removed.
4. Give bit `0x40` first priority. `FUN_0020D690` success runs its bookkeeping
   tail and exits; failure falls through.
5. If `+0x63:0x20` is already set, call `FUN_0020DDC0` and exit.
6. Otherwise try bit `0x01` through `FUN_0020D030`, then OR successful
   predicates from bits `0x02..0x20`. Any success enters `FUN_0020D910`.

### Already-present and constructor-owned adoption

`FUN_0020D030` uses authoritative presence function `FUN_00306420` for these
exact character/effect pairs:

| Character ID | Effect presence accepted |
| ---: | --- |
| `0x05` | `0x11` |
| `0x06` | `0x12` |
| `0x0C` | `0x18` |
| `0x0D` | `0x19` |
| `0x0F` | `0x1B` |
| `0x11` | `0x1D` |
| `0x16` | `0x21` |
| `0x2E` | `0x37` or `0x38` |
| `0x40` | `0x41` |
| `0x41` | `0x42` |
| `0x43` | `0x45` |
| `0x44` | `0x46` |
| `0x46` | `0x49` |
| `0x50` | `0x52` |
| `0x55` | `0x58` |
| `0x57` | `0x5B` or `0x5C` |
| `0x5A` | `0x5E` |
| `0x5B` | `0x5F` |
| `0x5C` | `0x62` |
| `0x5D` | `0x63` or `0x64` |

Every accepted effect in this table except character `0x57`'s `0x5C`
is the effect field of one of that character's own UJ records, so these pairs
adopt the [post-UJ outcome effect](#post-uj-outcome-effect).

It also returns true without an effect lookup for transformed IDs
`0x2F..0x38`, `0x49`, `0x4A`, and `0x4B`. On success, the dispatcher sets
`+0x63:0x20` and runs the controller bookkeeping tail. A call to live BTL read wrapper
`0x00716050` with `(side,10)` reads result-bank metric `10`. A nonzero
metric reduces the transformed-ID route to only
`FUN_00223140(fighter,0x11,0)`.

Descriptor bit `0x01` does not independently make the 12 native
transformation-UJ owners triggerable. Classic base IDs `0x01..0x04`, `0x0E`,
and `0x22..0x26` have association count zero. Base Naruto `0x39` and Sasori
`0x3F` have one associated effect (`0x72` and `0x73` respectively), but
`FUN_0020D030` has no case for either base ID. Conversely, reconstructed forms
`0x2F..0x38`, `0x49`, and `0x4B` pass the helper solely by identity without
testing their effect list. This includes Sasori form `0x4B`, whose association
row contains inline word `0x73` but count zero, so ordinary association readers
ignore it. The constructor-owned `-2` effect and the adopted controller marker
are therefore parallel persistent states; the former is not the latter's
entry prerequisite on a reconstructed form.

The connection to ordinary entry is exact. `FUN_00223360` maps its event-code
argument through a ten-entry jump table at `0x005C2150`; code `6` maps to BTL
result-bank metric `10` and adds its third argument through live wrapper
`0x00715F90`. Both ordinary and successful class-7 tails call
`FUN_00223360(fighter,6,1)`, so they increment that side's metric `10`. The transformed
adoption branch tests that same slot and omits `FUN_00223360` when it is already
nonzero. The read/increment/branch chain is directly proven; that its purpose
is to prevent a repeated credit on the reconstructed form is an inference.

The other tail helper, `FUN_00223140(fighter,0x11,0)`, is a statistics update,
not an action-state transition. Unless fighter `+0x62:0x01` is set, it
increments the signed-halfword pair's current value at
`fighter+0x4F0+0x11*4` (`+0x534`), clamps it to `9999`, and raises the
adjacent high-water value at `+0x536` when exceeded. Its zero third argument
selects the fighter's own statistics block. This distinguishes fighter
statistics from the BTL result-bank metric used to suppress a repeated tail.

`0x00607678` is a shared battle re-entry phase, not an awakening-only flag. Its
normal observed progression is:

| Phase | Proven producer | Meaning supported by consumers |
| ---: | --- | --- |
| `0` | initial BSS state; no resident zero writer was found | ordinary battle setup |
| `1` | `FUN_001EC5E0` at `0x001EC5E4`; alternate re-entry route in `FUN_001F2E70` at `0x001F3360` | replacement/re-entry requested |
| `2` | end of state-`0x17` handler `FUN_001EE1C0` at `0x001EE3A0`; end of alternate state-`0x18` handler `FUN_001EE500` at `0x001EE804` | identity/resource preparation finished; controller and fighters await reconstruction |
| `3` | `FUN_001EC3B0` at `0x001EC4D4` | phase-`2` reconstruction attempt finished |

The second phase-`1` writer proves that the phase is shared by more than the
form-swap request path. An exhaustive raw scan found no direct BTL store to the
corresponding GP-relative slot `-0x3378`; all listed writers are resident.

Route value `8` has a separate re-entry-variant word at `0x0060767C`.
`FUN_001EC5E0` writes variant `1` at `0x001EC5E8`; the alternate
`FUN_001F2E70` route writes variant `2` at `0x001F3368`. These are the only
direct GP-relative writers in the clean resident binary, and BTL has none.
`FUN_001EDD10` dispatches route `8`, variant `1` to state `0x17` at
`0x001EDDCC`, and variant `2` to state `0x18` at `0x001EDDDC`. The native
post-UJ form request is therefore specifically the state-`0x17` path.

`FUN_001F0F40` is the phase-`1` readiness barrier. When the phase is not `1`, it
clears byte `0x00607680` and returns `0`. On its first phase-`1` pass it clears
each allocated side object's `+0x48` and sets that byte. It then services each
side through live BTL functions `0x0071AF30` and `0x0071B2E0`, builds an
allocated-side mask, and compares it with the mask of side objects whose
`+0x54` is nonzero. It returns `2` while they differ and `3` once every
allocated side is ready, then clears the handshake byte. `FUN_001EF9C0` is a
representative caller in manager substate `4`.

`FUN_001EC3B0` clears both result-bank rows through live `0x00715F60` whenever
it creates a controller outside phase `2`. In phase `2` the clear is skipped
and the function advances the global to `3`. This is the exact preservation
boundary for the result bank across reconstructed-form re-entry.
The phase-`3` write is outside the allocation-success branch; phase `3` alone
does not prove that a controller or fighter was successfully allocated.

For Deidara `0x40`, detecting `0x41` additionally sets `+0x63:0x10` and calls
the live BTL setter `0x006F09D0` with fighter `+0x24` and duplicated
`0x40060723` float arguments, setting both variable stick-sector widths of
its [`ccCommand` interpreter](action_commands.md#logical-mask-translation)
to 120 degrees. The matching cleanup target, live `0x006F09E0`, restores the
default 150/90-degree widths.

### Proven HP and counter prerequisites

The descriptor HP route is narrowly hard-coded:

- Classic Hinata `0x0C`: trigger when fighter `+0x6C <= 0.15`;
- Sasori (Hiruko) `0x4C`: the same threshold.

The Tenten-family counter route is also exact:

- Classic Tenten `0x0D`: fighter `+0xB78 >= 0x19` (`25`);
- Tenten `0x42`: fighter `+0xB78 >= 0x28` (`40`).

An exhaustive aligned resident-instruction scan found five signed loads and
seven halfword stores at offset `+0xB78`. They reduce to three zeroing sites and
four increment sites; there is no other clean resident writer, decrement, or
cap:

| Runtime store | Owner | Exact write condition |
| ---: | --- | --- |
| `0x002150C8` | common fighter initializer `FUN_00214A40` | initialize to zero |
| `0x0020E868` | dispatcher `FUN_0020E280` | threshold accepted; reset to zero before ordinary entry |
| `0x0020E1EC` | reconciliation `FUN_0020DDC0` | Tenten-family associated state remains; hold at zero |
| `0x00237A44` | item-use starter `FUN_002378F0` | increment once after `FUN_002378A0` accepts the selected item route |
| `0x0025E4EC` | Classic Tenten callback `FUN_0025DEF0` | increment after successful BTL creation of resource ID `0x34`, `0x35`, or `0x11` |
| `0x002BB8FC` | Tenten callback `FUN_002B9660` | increment after successful BTL creation of resource ID `0x50` |
| `0x002BB914` | Tenten callback `FUN_002B9660` | increment after successful BTL creation of resource ID `0x23` |

The generic item route is selected by `FUN_00376400`: item metadata kind `3`
or `6` and flag `0x10` clear. In the complete clean `0x00..0x73` metadata table
at `0x005B04F0`, 82 rows satisfy that predicate; `0x27` is the sole kind-`3`/
kind-`6` row excluded by flag `0x10`. `FUN_002378A0` additionally requires
fighter `s16 +0xB72 == 0` and its secondary acceptance predicate before
`FUN_002378F0` starts the action and increments the counter.

The Tenten-specific callbacks increment only after BTL object creation returns
a non-null result. The two callbacks are anchored to the Classic Tenten and
Tenten character implementations by their resident callback tables at
`0x0043D340` and `0x00508020`, respectively; the corresponding static character
records point to those tables at record `+0x1C`. The latter implementation also
directly checks active character `0x42` and associated effect `0x43`.

Thus the thresholds count accepted item/action creations, including the exact
Tenten projectile/resource cases above. The implementation never reads fighter
chakra for this route; `+0xB78` must not be labeled chakra.

`FUN_0020D5D0` compares the native combo object's signed `s16 +0x34` against:

| Character | ID | Required current combo |
| --- | ---: | ---: |
| Asuma | `0x56` | `10` |
| Kisame | `0x48` | `15` |
| Neji | `0x41` | `30` |
| Kankuro | `0x3C` | `20` |
| Classic Neji | `0x06` | `15` |

The per-side native combo object and its current count `+0x34` are described in
[Combo accounting](combo_accounting.md#resident-owner-and-update-order). This
route is not a chakra or awakening-gauge check.

### Raw state predicate

Descriptor bit `0x10` calls `FUN_002274C0(fighter,2,selector,0)`. The selector
is `6` only for Deidara `0x40` and `0` for every other clean row. All of these
numeric gates must pass:

- fighter `+0x18E == 0`;
- fighter `+0x190 == 3`;
- fighter `+0x956 == 0`;
- fighter `+0x192 == 2`;
- `FUN_002118A0(fighter+0x1DC, selector) != 0`.

The state tuple is therefore exact: major action `0`, substate `3`, phase `2`.
`FUN_00217E40` is the resident transition owner for the major/substate pair,
and other gameplay knowledge independently establishes `+0x192` as the phase
within that action.

The final predicate is not a meter or resource comparison. The embedded
tracker has these relevant fields:

| Tracker / fighter offset | Type | Proven role |
| ---: | --- | --- |
| `+0x02` / `+0x1DE` | `u16` | Crossing flags; bit `0x01` serves `FUN_002118A0`, bit `0x02` serves `FUN_00211A20` |
| `+0x08` / `+0x1E4` | `s32` | Previous integer position |
| `+0x0C` / `+0x1E8` | `s32` | Current integer position |
| `+0x10` / `+0x1EC` | `float` | Previous scalar position |
| `+0x14` / `+0x1F0` | `float` | Current scalar position |
| `+0x18` / `+0x1F4` | `float` | Projected next scalar position |
| `+0x1C` / `+0x1F8` | `float` | Fractional accumulator |

`FUN_00211770` zeros the positions and accumulator and initializes both
crossing bits. `FUN_002117A0` resets all integer/float positions to a
caller-supplied value. `FUN_00211D80` advances the tracker by a scalar delta,
moving whole units into the integer position and retaining the fraction;
fighter update `FUN_0024D5E0` is a representative caller for the tracker at
`+0x1DC`.

`FUN_002118A0(tracker,n)` returns true at an enabled exact integer boundary or
when nonzero position `n` lies in the tracker's crossed/projected interval.
Position `0` is intentionally special: it can succeed only through the exact
boundary case, not the general nonzero crossing calculation. Thus native
bit-`0x10` awakening is synchronized to position `0` in the action above,
except Deidara's position `6`. `FUN_00211A20` implements the same position test
against independent crossing bit `0x02`; the class-7 route uses that variant at
position `0`.

**Conclusion, high confidence:** these selectors are action-progress
positions, not resource quantities. Their exact user-visible timing is not
established; progress rendering and playback internals belong to
[Timer primitives](../runtime/timer_primitives.md#event-and-interval-predicates).

The dormant bit-`0x20` branch would call the same helper with selector `0` only
for Sakura `0x3A`, but no clean descriptor has that bit. Semantic names for
the action-progress source beyond the proven tracker behavior are not needed
for eligibility.

There is no general chakra, meter, or universal low-HP prerequisite in
`FUN_0020E280`. Only the exact HP and counters above are proven.

### Deidara and Gaara character variants

Their controller marker, associated effect, altitude consumer, and
character-specific action variant are separate gates. The variant changes
record categories in each fighter's working action array and selects a
different animation-pointer array. Named records and their shipped signatures
remain in [Action commands](action_commands.md#complete-static-action-data-census).

| Character | Mode byte | Ordinary enabled partition | Alternate enabled partition | Animation pointer `+0xB84`, ordinary / alternate |
| --- | ---: | --- | --- | --- |
| Deidara `0x40` | `+0x5940` | restore source categories for slots `21..41`; zero `42..45` | zero `21..41`; set `42..45` category `1` | fighter `+0x1110` / `+0x5944` |
| Gaara `0x3B` | `+0x57E2` | restore source categories for slots `21..43`; zero `44..47` | zero `21..43`; restore source categories for `44..47` (all `1`) | fighter `+0xEE0` / `+0x57E8` |

Slots below `21` are unchanged by these partition switches. Deidara's normal
constructor path calls `FUN_002B49C0(fighter,0)` through `FUN_002B42D0` at
`0x002B4404`. Gaara's `FUN_0029BF90` sets mode zero and clears slots
`44..47`. Thus the shipped alternate rows begin disabled in the working
arrays even though their source categories are nonzero.

Deidara's callback table at `0x004FC750` points at `FUN_002B4D60` in slot
`+0x04`. After confirming character `0x40`, the callback tests association
presence through `FUN_0020CF40` at `0x002B5184`: presence requests
`FUN_002B4860(fighter,1)` at `0x002B519C`; absence requests mode zero at
`0x002B51EC`. The setter changes `+0x5940`, animation pointers, movement
coefficients, and the record partition through `FUN_002B49C0` only when the
requested byte differs. It defers a change when `FUN_00217860` returns
effective current action index `6`—this is not a major-action-`6` test.
The callback therefore keys the variant to the effect list, independently of
the controller marker used by altitude control. On a successful switch to
mode one it also calls `FUN_00218250(20.0,1.0,fighter,&fighter->+0x998)`.

Gaara's callback table at `0x004E0680` points at `FUN_0029D7E0` in slot
`+0x04`. Its character-`0x3B` branch behaves differently:

- With controller marker `+0x63:0x20` set, absence of effect `0x3B` requests
  `FUN_0029C1E0(fighter,0)` at `0x0029D87C`; presence retains the variant.
- With the marker clear, a previous mode-one byte first requests mode zero
  at `0x0029D8A4`. The callback then calls
  `FUN_002274C0(fighter,1,0x2F,1)` at `0x0029D8BC`. Success requests mode one
  at `0x0029D8E0`, after an encoded live BTL `0x0071EF70` call, and applies
  the same `FUN_00218250(20.0,1.0,...)` vertical-velocity helper.

That helper gate requires major/substate `(0,3)`, `+0x956 == 0`, phase
`+0x192 == 1`, and progress selector `47` in tracker `+0x1DC`. Its fourth
argument `1` also permits the helper's exact-current-position case when the
crossing bit is set. This phase-`1` variant gate differs from the common
phase-`2` controller trigger at selector `0`; setting the Gaara variant is
not proof that the controller marker is already set. `FUN_0029C1E0` changes
the byte and partition only when the request differs, with the same effective
action-index-`6` deferral as Deidara.

The mode setters also replace these resident float fields; no time or distance
units are assigned to them here:

| Character / field | Ordinary | Alternate |
| --- | ---: | ---: |
| Deidara `+0xEC` | `20` | `30` |
| Deidara `+0xF0` | `0.25` | `0.3125` |
| Deidara `+0xF4` | approximately `0.3` | approximately `0.375` |
| Gaara `+0xEC` | `16` | `25` |
| Gaara `+0xF0` | `0.25` | `0.3125` |
| Gaara `+0xF4` | `0.25` | `0.125` |
| Gaara `+0x110` | `350` | `200` |

The shared consumers identify `+0xEC` as the ground directional target,
`+0xF0/+0xF4` as proportional acceleration/braking, and `+0x110` as the first
jump-height input; their formulas and limits remain in
[Movement and physics](movement_and_physics.md#character-movement-parameters).

Deidara's defaults are read from `0x00501AD0..0x00501AD8` and multiplied by
`1.5/1.25/1.25`; Gaara's restored defaults come from
`0x004E5C90/0x004E5C94/0x004E5C98/0x004E5CB4`. The exact category writes
are `FUN_002B49C0` and `FUN_0029C1E0`; the general action selector rejects
zero-category records. Active alternate records still pass the ordinary
signature, state, continuation, and action validation gates described in
Action commands. Their direction contributions `0x200/0x400/0x4000` are
built from fixed-width logical bits `0x10/0x20/0x100`, so the variable-sector
widening does not generate those attack-direction contributions. Its proven
direct vertical consumer is the altitude path above.

### Choji's marker-selected parameter override

Choji `0x51` supplies a separate example of a working parameter that differs
from its copied record even before controller adoption. Record `0x0055F020`
contains `13.5` at `+0x60` (`0x0055F080`, bytes `00 00 58 41`), copied by
`FUN_002151E0` to fighter `+0xEC`. Constructor `FUN_002E8C10` then sets mode
byte `+0x6238` to `1` and calls `FUN_002E8E90(fighter,0)`, forcing the
mode-zero branch. That branch loads `16.0` from `0x004E5C90` and writes
`+0xEC` at `0x002E90A4`; it does not restore Choji's own `13.5` record value.
The loaded address is also Gaara's ordinary ground-target field. This
establishes the shared source address, not a reason for the choice.

Choji's record `+0x1C` points to callback vector `0x00559080`, whose `+0x04`
entry is `FUN_002E9AB0`. After confirming actual character ID `0x51`, that
callback calls the setter with the boolean controller marker `+0x63:0x20`
at `0x002E9B30`. A changed request performs these writes:

| Requested mode | Fighter `+0xEC` | Working action categories | Action `0x13`'s pointed row `+0x70` |
| ---: | ---: | --- | ---: |
| `0` | `16.0` | Restore source slots `0x15..0x2A`; zero `0x2B..0x37` | `80.0` |
| `1` | `25.0` | Zero slots `0x15..0x2A`; restore source `0x2B..0x37` | `150.0` |

The row pointer is working-action-array `+0x68C`; the two row values come
from `0x00603D48/0x00603D4C`. No time or distance unit is assigned to that
row field here. The ground-target stores are explicit at
`0x002E8FA8/0x002E90A4`, with the fighter retained in `s1`. Returning to mode
zero can first cancel the current action through `FUN_0023E460` when record
flag `0x200` is set, or flag `0x100` is set together with fighter
`+0xA40 == 1`. The mode comparison otherwise avoids repeating the partition
and parameter writes.

Before that comparison, effective action index `6` calls
`FUN_00226E90(3.0,0.0,0.0,0.0,fighter)`, including when the mode byte already
matches. Unlike Deidara/Gaara's setters, this does not defer the mode change.
The helper's direct size-target writes are a separate mechanism from generic
payload aggregation; see
[Battle status effects](battle_items_and_status_effects.md#direct-field-writes-do-not-use-the-payload-folds).
The same Choji callback separately tests effect `0x54` for its subsequent
contact/presentation branch. That presence test does not select this mode:
the mode uses the marker, so marker cleanup can request `16.0` while an
effect node still exists. The setter directly changes none of the four
damage/resource fields compared below, nor `+0xF0/+0xF4/+0x110`.
The static call order establishes these writes, not their visible timing.

## Entry paths

### Ordinary controller entry

`FUN_0020D910` first requires
`FUN_001FE200(((fighter u16 +0x60) & 0x1FF) >> 5) == 0`. It normally selects
the association's inline/first effect, with these hard-coded exceptions:

| Character ID | Selection or pre-entry behavior |
| ---: | --- |
| `0x5D` `[0x63,0x64]`, `0x5C` `[0x61,0x62]` | Return if the second effect is present; otherwise select the first |
| `0x5B` `[0x5F,0x60]`, `0x57` `[0x5B,0x5C]`, `0x55` `[0x58,0x59]`, `0x50` `[0x52,0x53]` | Return if the first effect is present; otherwise select the second |
| `0x4D` | Remove constructor-owned `0x4D`, then apply associated `0x4E` |
| `0x40`, `0x3B` | Set special bit `0x10`, call `SUB_006F09D0`, then continue with `0x41` or `0x3B` |
| `0x45` `[0x47,0x48]` | If already marked awakened, stop at `0x48`; replace `0x47` with `0x48` |
| `0x19` | Remove `0x22`, then apply associated `0x24` |
| `0x2F..0x38`, `0x49`, `0x4A`, `0x4B` | Set controller bit `0x20` and return without constructing an effect |

The ordinary tail is:

1. `FUN_00305C30(fighter,effect,-1,1)`;
2. set fighter `+0x63:0x20`;
3. `FUN_00223360(fighter,6,1)`;
4. `FUN_00223140(fighter,0x11,0)`;
5. when `FUN_00250820() == 0`, optionally call
   `FUN_002040D0(fighter,descriptor_s16,-1,1)`, then
   `FUN_001D87C0(0x3A,fighter+0x30)` and `FUN_00334FF0(fighter)`.

The controller does not test whether `FUN_00305C30` actually inserted the
effect before setting its marker. The failure behavior is statically resolved:
`FUN_00305C30` returns no status to this caller, and a rejected or failed
insertion still reaches the marker, counter, and bookkeeping tail above.
`FUN_00305270` returns zero for an absent container owner (`+0x10`), an existing
same-ID node with state `-2`, or a null allocation/factory result. Its generic
allocation is `0xC0` bytes at `0x00305380`; the null check at `0x00305388` and
common null-result branch at `0x003053A8` reach return zero without appending.
For a replaceable duplicate, the old node is force-removed at `0x0030534C`
**before** allocation, with no restoration if allocation fails. Clean
class-1/2/3 records bypass the root eligibility gate, so that gate cannot reject
their controller insertion. These branches establish the response to failure,
not how often allocation failure occurs in ordinary play.

With no associated effect left after that tail, the next unsuppressed marked
controller pass reaches `FUN_0020DDC0` and clears the marker. Deidara/Gaara's
special flag and sector-width changes occur before insertion and are undone by
that reconciliation. A rejected duplicate protected by state `-2` is different:
the effect already remains present, so rejection alone does not imply marker
cleanup. This distinction follows the list-based reconciliation rather than an
insertion return value.

### Exact class-7 UJ entry

`FUN_0020D690` requires every one of these gates:

- fighter `+0x18E == 8`;
- fighter `+0xA4C` is non-null;
- pointed `+0x10 & 0x00F00000` is nonzero;
- pointed `+0x14 & 0x00010000` is nonzero;
- `FUN_00217930(fighter,-3) != 0`;
- fighter `+0x192 == 2`;
- `FUN_00211A20(fighter+0x1DC,0) != 0`.

It then performs an important order of operations:

1. remove every associated effect below `0x68` with reason `1`;
2. apply selected `u16` effect `fighter+0x18A` through
   `FUN_00305C30(fighter,effect,-1,1)`;
3. only afterward test whether that effect belongs to the association list;
4. on membership, set controller bit `0x20` and return success;
5. on mismatch, call `FUN_0020DD20` and return failure.

`FUN_0020DD20` clears flags but does not remove an effect. Therefore an invalid
selected effect can remain after the mismatch path. An exhaustive decode of
the clean bit-`0x40` character lists proves that native data does **not**
prevent this edge.

Character UJ-list pointers begin at runtime `0x005ACFB0`, file
`0x004AD0B0`; each pointed list is an `s16` count followed by `s16` UJ-record
indices. The UJ records at `0x005AEC40` additionally contain selector key
`s16 +0x06`, class byte `+0x08`, and effect `u16 +0x0E`. Per-character default
record indices are at runtime `0x005AFDB0`, file `0x004AFEB0`.

| Character | UJ-list pointer | Class-7 record index: key -> effect | Association | Result |
| --- | ---: | --- | --- | --- |
| Haku `0x0A` | `0x00604360` | `22/0x16`: `3 -> 0x15` | `[0x15]` | Match |
| Zabuza `0x0B` | `0x00604368` | `25/0x19`: `3 -> 0x16` | `[0x16]` | Match |
| Yellow Flash `0x27` | `0x00604400` | `75/0x4B`: `2 -> 0x2C`; `77/0x4D`: `1 -> 0x2D` | `[0x2C,0x2D]` | Both match |
| Konohamaru Squad `0x28` | `0x00604408` | `78/0x4E`: `2 -> 0x2E`; `79/0x4F`: `3 -> 0x2F` | `[0x2F]` | Record `78` mismatches |
| Hanabi `0x29` | `0x00604410` | `81/0x51`: `2 -> 0x30`; `83/0x53`: `1 -> 0x31` | `[0x30,0x31]` | Both match |
| First Hokage `0x2A` | `0x00604418` | `85/0x55`: `3 -> 0x32` | `[0x32]` | Match |
| Second Hokage `0x2B` | `0x00604420` | `87/0x57`: `2 -> 0x33`; `89/0x59`: `1 -> 0x34` | `[0x33,0x34]` | Both match |
| Shizune `0x55` | `0x00604500` | `195/0xC3`: `3 -> 0x58` | `[0x58,0x59]` | Match; no class-7 record yields `0x59` |

`FUN_003729F0` begins with the character's default UJ record and substitutes a
local-list record whose selector key matches the request. Instructions in
`FUN_002449C0` establish its three tier requests as keys `2`, `3`, and `1`
(`a1 = 2` is set at `0x00244B18` for the first). Konohamaru's key-2
record `78` is class `7` and writes effect `0x2E` to fighter `+0x18A`. Once
`FUN_0020D690`'s runtime gates pass, it attempts to
insert clean effect `0x2E`, finds only `0x2F` in the association, clears the
controller flags, and returns failure. If insertion succeeds, this call site
does not remove `0x2E`. The other 11 class-7 records in these eight local lists
all belong to their character's association set.

The surviving effect's gameplay state can be narrowed further without assigning
it an on-screen name. Its record anchor is resident `0x0059F49C` (effect
`0x2E`, file `0x0049F59C`): stored ID `0x2E`, default lifetime `600`, flags `2`,
and attack/defense fields `+0x14/+0x18` both approximately `1.1` (raw
`0x3F8CCCCD`). The factory-registration list at `0x0059E0F0..0x0059E188`
contains no `0x2E` entry; initialization `FUN_00305470` therefore leaves this
effect using generic `FUN_00304910`. The node is class `1`, not a form-replacing
class-3 node. On successful insertion it starts at lifetime `600`; generic
`FUN_00304D60` decrements positive lifetimes once per eligible effect update,
and `FUN_003059B0` owns the update eligibility and expiry removal.

The attack and defense folds `FUN_00306BD0` and `FUN_00306C80` consult nonzero
node lifetime and the effect list, **not** controller bit `+0x63:0x20`.
Consequently, if `0x2E` is the only contributing effect, its surviving node
supplies approximately `1.1` to the attack fold and `1.1` to the defense fold
(approximately `0.9` incoming factor where the damage flags enable that fold).
The full calculation and multi-effect aggregation remain in
[Damage](damage.md#calculator-formula).

Konohamaru's clean descriptor is only `0x40`: after the class-7 mismatch there
is no bit-`0x01` adoption or ordinary-trigger route to restore the marker, and
the success-only event/bookkeeping tail is skipped. Repeated qualifying class-7
calls can replace the unprotected `0x2E` node and restart its lifetime; they
still fail association membership. Thus the proven mismatch is a timed generic
effect whose damage contributions can remain active while the awakening marker
is clear. Its animation, visual presentation, and perceived result remain
unestablished by this static trace.

Successful class-7 dispatch calls `FUN_00223360(fighter,6,1)`,
`FUN_00223140(fighter,0x11,0)`, and, outside the alternate state,
`FUN_001D87C0(0x3A,fighter+0x30)` plus `FUN_00334FF0(fighter)`. It does not call
the descriptor's `FUN_002040D0` path.

### Naruto's separate low-HP effect

Naruto's character callback table at runtime `0x004D56D0` contains
`FUN_00299100` at slot `+0x04`. It applies effect `0x39` when all of these are
true:

- normalized HP at fighter `+0x6C <= 0.15`;
- effect `0x39` is absent;
- fighter `+0x62` bit `0x01` is clear;
- `FUN_00250820() == 0`.

The call is `FUN_00305C30(fighter,0x39,-1,1)`. This branch does not set
controller bit `0x20` and does not run either controller bookkeeping tail.
Naruto's direct low-HP effect is consequently distinct from both the
descriptor's two low-HP characters and his effect-`0x72` form replacement.

### Post-UJ outcome effect

The selected UJ record's effect field `+0x0E` reaches the attacker after the
cinematic through a contest-owned global, independently of the
[form request](#effect-to-form-mapping-and-resource-replacement).

Skill-play constructor `FUN_0035CF00` calls `FUN_0036C120 -> FUN_0036B6D0`
outside manager mode `6`. `FUN_0036B6D0` replaces type `1` with a random type
and then constructs a contest for types `2..6`, each through the shared
initializer `FUN_0035E360`; type `0` constructs nothing. The initializer
writes:

| Global | Value | Evidence |
| --- | --- | --- |
| `0x00604310` | Effect ID of the attacker's selected record `manager+0x60+side*0x28`, through `FUN_00372B10` (record `99` for skill `0x49`); `-1` without a manager | `0x0035E430..0x0035E494` |
| `0x00604314` | `1` | `0x0035E49C` |
| `0x00607754` | `0` | `0x0035E4A0` |

Battle setup `FUN_001EEE30` calls `FUN_0036C0D0` at `0x001EEFA8`, which
writes `0x00607754 = 0`, `0x00604310 = -1`, and `0x00604314 = 1`. Apart from
these two routines, the only writers of `0x00604310` are the contest classes'
status-`4` clears. With contest type `0`, `0x00604310` therefore stays `-1`
for that Ultimate Jutsu unless an earlier one left another value.

The only reader of `0x00604310` is getter `FUN_0036C1E0`, whose sole caller
is post-cinematic state `1` of coordinator `FUN_0024ED40`. In order, that
state:

1. calls `FUN_003055C0(participant,3)` for attacker and target at
   `0x0024EFC4/0x0024EFD4`, removing their unprotected class-`0..2` nodes
   (see
   [Battle status effects](battle_items_and_status_effects.md#native-action-and-form-boundaries));
2. when the target is not defeated and `FUN_0036C1E0()` at `0x0024F034` is not
   `-1`, calls `FUN_00307690(attacker,effect)` at `0x0024F054`, which is
   exactly `FUN_00305C30(attacker,effect,-1,1)`;
3. reads `0x00604314` through `FUN_0036C1F0` at `0x0024F060` to choose its
   next state.

The resulting node then enters the ordinary controller. On the next
unsuppressed dispatcher pass with the marker clear, descriptor bit `0x01`
calls `FUN_0020D030`, whose effect-presence pairs are exactly the
non-transforming outcome effects that belong to the character's association
set. Its success sets marker `+0x63:0x20` and runs the adoption bookkeeping.
The complete clean decode of the 94 character UJ lists and default records,
excluding record `0` (effect `0`), gives these UJ records of record class `3`
with an outcome effect:

| Outcome | Character: record (category) -> effect |
| --- | --- |
| Effect adopted by `FUN_0020D030`; sets the marker | `0x05`: `11` (`1`) -> `0x11`; `0x06`: `13` (`3`) -> `0x12`; `0x0C`: `27` (`2`) -> `0x18`; `0x0D`: `31` (`3`) -> `0x19`; `0x0F`: `35` (`2`) -> `0x1B`; `0x11`: `42` (`3`) -> `0x1D`; `0x16`: `54` (`3`) -> `0x21`; `0x2E`: `97` (`3`) -> `0x37`, `99` (`1`) -> `0x38`; `0x40`: `135` (`2`) -> `0x41`; `0x41`: `140` (`3`), `141` (`1`) -> `0x42`; `0x43`: `146` (`3`) -> `0x45`; `0x44`: `148` (`3`) -> `0x46`; `0x46`: `154` (`3`) -> `0x49`; `0x50`: `179` (`2`) -> `0x52`; `0x55`: `196` (`1`) -> `0x58`; `0x57`: `200` (`2`) -> `0x5B`; `0x5A`: `211` (`3`) -> `0x5E`; `0x5B`: `214` (`3`) -> `0x5F`; `0x5C`: `217` (`3`), `218` (`1`) -> `0x62`; `0x5D`: `219` (`2`) -> `0x63`, `220` (`3`) -> `0x64` |
| Effect only; `FUN_0020D030` has no case | `0x01`: `1` (`2`) -> `0x0E`; `0x02`: `3` (`2`) -> `0x0F`; `0x03`: `6` (`3`) -> `0x10`; `0x0E`: `33` (`2`) -> `0x1A`; `0x19`: `56` (`2`), `57` (`3`) -> `0x22`; `0x22..0x26`: `65`, `67`, `69`, `71`, `73` (`2`) -> `0x27..0x2B`; `0x4D`: `171` (`3`) -> `0x4D`; `0x54`: `191` (`2`) -> `0x22` |
| Transforming effect `0x68..0x73` | The 12 records in [Effect-to-form mapping](#effect-to-form-mapping-and-resource-replacement) |

Category-to-tier selection is described in
[Effect-to-form mapping](#effect-to-form-mapping-and-resource-replacement).
The only accepted `FUN_0020D030` effect outside these records is character
`0x57`'s `0x5C`. Class-7 records are applied through
[the class-7 entry](#exact-class-7-uj-entry) instead; whether their skill
plays also seed `0x00604310` was not traced.

**Conclusion, high confidence:** for every non-transforming outcome record,
this application is the only source of the post-UJ effect, and for the
adopted effects above also of the controller marker that follows it. Under
contest type `0` step 2 is skipped while step 1 still runs, so the attacker
leaves the UJ with neither the outcome effect nor any earlier unprotected
class-`0..2` effect.

For the 12 transforming records the outcome effect is the record's class-3
effect, inserted with state `-1` on the base fighter. No static reader links
it to the form request: `FUN_0020D030` has no case for any of the 12 base
IDs; the request's sole stager `FUN_0035B3B0` gates on the selected record,
mode, outcome word, and slot-`7` latch, not on the effect list (no resident
`FUN_00306420` caller lies in the UJ-completion or manager re-entry code);
the old fighter's teardown force-removes the node; and the replacement
fighter receives its own `-2` node from `FUN_00305FF0` by identity.

The other contest globals do not reach the controller or the form gates:

- `0x00604314` keeps its setup value `1` under contest type `0`, the value an
  uninterrupted contest also leaves. Its readers are `FUN_0035B740` at
  `0x0035BA3C` (the slot-`7` defeat latch below) and getter `FUN_0036C1F0`,
  whose callers are `FUN_0024ED40` and `FUN_0020BBB0` at `0x0020BC9C`; the
  latter rebuilds a fighter's per-action statistics rows and calls no
  controller function.
- Damage total `0x00607754` stays `0`. Its readers are contest resolution
  `FUN_0035F610` and getter `FUN_0036C1D0`, called only by `FUN_0035AF20`
  (displayed percentage) and per-hit damage `FUN_0035B740`, so each hit deals
  its unscaled fraction as described in
  [Ultimate Jutsu](ultimate_jutsu.md#damage).
- Without a contest object, `FUN_0036C1A0` returns status `0`, so the BTL
  presentation cannot write outcome `2` to `0x00607780`.

**Observation from modified-runtime testing:** in a runtime experiment that
left the contest global empty by forcing contest type `0`, post-UJ awakening
no longer occurred. In a second experiment that kept the contest object and
removed only the sole resident call to `FUN_0036BFF0` at `0x001F0940` (ELF
file offset `0xF0A40`), the post-UJ awakening path still ran; because that
call also advances the contest timer and result display, the contest stayed
invisible and never resolved. The second experiment still ran
`FUN_0035E360`, so it kept the outcome effect. The tested character and
record were not recorded. For a non-transforming outcome record the
conclusion above explains both results. **Inference:** for a transforming
record, static evidence predicts that the form request is still made under
contest type `0`, so such a result would remain unexplained.

## Generic effect state

The fighter's effect list, its classifier, high-level application, same-ID
replacement, removal reasons, and teardown cleanup belong to
[Battle items and status effects](battle_items_and_status_effects.md#categories);
see also its [application](battle_items_and_status_effects.md#application-replacement-and-countdown-normalization),
[removal](battle_items_and_status_effects.md#update-expiry-and-removal), and
[notification map](battle_items_and_status_effects.md#resident-effect-to-notification-map)
sections. `FUN_00306420` is the authoritative presence test. The
class-specific facts awakening depends on follow.

### Class-3 transformed-form records

`FUN_003047C0` classifies effect IDs `0x68..0x73` exactly as class `3`, so the
complete transformed-form family is class `3`. Using
`0x0059E2A4 + effect_id * 0x64` as the anchor, records `0x68..0x73` all have:

- null factory, so creation uses generic `FUN_00304910`;
- stored ID matching the record;
- default state `-1`;
- flags exactly `0x2`.

There is no per-effect model/resource-swap callback in these 12 records. Flag
`0x4`, which would propagate the effect to the opponent, is absent, so class-3
records are owner-only. Classes `1`, `2`, and `3` bypass the ordinary
fighter-`+0x62`/`FUN_00216820` eligibility gate. The 12-row notification map at
`0x005B0040` contains no class-3 ID, the positional event switch handles only
IDs `0..0x0C`, and the auxiliary sidecar at fighter `+0x8D8` is allocated only
for classes `1` and `2`. A successful class-3 insertion therefore performs none
of those BTL/event/sidecar hooks and only reaches the final write of its ID to
fighter `+0x8E8`.

### Persistence and removal

`FUN_00305FF0`, called during fighter setup by `FUN_002151E0`, creates
transformed-form effects with explicit node state `-2`, not their record
default `-1`. This makes them persistent:

- duplicate creation refuses to replace a `-2` node;
- removal reasons `0`, `1`, and `2` preserve a `-2` node;
- reason `3` preserves all class-3 and class-4 nodes, and also preserves
  `-2` nodes in classes `0..2`;
- reason `5` force-removes any node.

`FUN_003055C0` bulk-removes only classes `0..2` and leaves transformation
class `3` intact. `FUN_00305750` force-removes classes `0..4` and is called by
fighter teardown `FUN_00215720`; fighter teardown is the proven terminal
cleanup for even constructor-owned `-2` transformation effects.

### Authored lifetime and resource behavior

Ordinary awakened effects are not all protected or permanent. Representative
record reads establish the following defaults and recurring contributions.
The delta fields are record-base `+0x4C/+0x54`, copied to node
`+0xAC/+0xB4`; these decimals approximate the authored single-precision values.

| Effect / character context | Default countdown | HP delta per eligible contribution pass | HP boundary | Chakra delta |
| --- | ---: | ---: | ---: | ---: |
| `0x10`, Classic Rock Lee `0x03` | `600` | `-1/3000` | `0.1` | `0` |
| `0x3A`, Sakura `0x3A` | `600` | `+1/4000` | `1.0` | `-1/120` |
| `0x3B`, Gaara `0x3B` | `600` | `0` | no HP contribution | `-1/120` |
| `0x41`, Deidara `0x40` | `600` | `0` | no HP contribution | `-1/120` |
| `0x47`, Might Guy `0x45`, first stage | `600` | `-1/12000` | `0.1` | `0` |
| `0x48`, Might Guy `0x45`, second stage | `450` | `-1/4500` | `0.1` | `0` |
| `0x54`, character `0x51` | `600` | `0` | no HP contribution | `-1/120` |

Classic Lee's effect `0x10` is recorded in his local UJ record `6`
(record `0x005AECB8`, selector `3`, effect field at `0x005AECC6`), not by an
association row: the base ID's association count is zero. The other rows use
the controller associations already described above.

Every nonzero chakra delta above has boundary field `+0x58 = 0`.
`FUN_00306F00` and `FUN_00307020` aggregate active nodes before evaluating
their HP/chakra boundary. For a sole negative contributor, equality with the
boundary still permits the contribution; a value below it disables that
contribution. The boundary is therefore an eligibility comparison, not an
exact floor imposed on the final HP write. Positive Sakura HP contribution
is eligible while HP is at or below `1.0`; the ordinary recovery helper clamps
the actual result to full HP. Multiple-node aggregation belongs to
[Battle status effects](battle_items_and_status_effects.md#concurrent-payload-contributions).

`FUN_003059B0` passes the aggregate values to `FUN_00306090` and
`FUN_00306220` with second argument `-1.0`, so those calls do not request
another per-call boundary clamp. The HP helper routes a negative contribution
through `FUN_00225050`, while the chakra helper routes it through
`FUN_00225780`, which clamps chakra at zero. Neither aggregate helper nor
these resource consumers removes an effect or clears the controller marker
at the boundary. The generic lifetime and character-specific exit remain
separate. This scope does not exclude independent removal by a character
callback such as the documented effect-`0x54` cancellation paths.

The recurring contribution pass and the countdown pass have different gates
inside `FUN_003059B0`; they must not be equated. The resource helper further
requires root suppression `+0x62:0x01` clear, `FUN_00244110 == 0`, and
`FUN_00244130 == 0` for both owner and linked opponent. The latter predicate
means major action `8`, a non-null action record with `+0x10 & 0xC0000`, and
signed byte `+0x19 >= 1`. Chakra debit can also be blocked by its own effect,
fighter-byte, or flag gates, described in
[Chakra and guard](chakra_and_guard.md#debit-and-reservation-behavior).
An authored negative chakra delta therefore does not prove uninterrupted
draining in every combat state.

At `0x00304D9C..0x00304DA0`, the ordinary lifetime tick subtracts exactly
one from positive node `+0x6C`; it does not read fighter rate `+0x1AC`.
These effect IDs are all at least `0x0D`, so their countdowns also bypass the
low-ID scalar normalization. Authored count `600` is neither a confirmed
elapsed-frame duration nor an action-progress duration: ticking can be gated,
and explicit exits/replacements can end or restart it. The complete countdown
contract remains in
[Battle status effects](battle_items_and_status_effects.md#countdown-pass).

The action-rate field is separate again. Record `+0x1C` supplies `1.25` for
`0x10/0x47/0x48` and `1.1` for `0x3A`; it is neutral for `0x3B/0x41/0x54`.
`FUN_00306D30` caps the effect fold at `1.25` and neutralizes it in major
states `5/6`, on nonzero `FUN_00244110`, or in major `8` when
`FUN_002440C0` succeeds. Fighter maintenance `FUN_0024C440` uses this fold
only if override `+0x1B0 == 1.0`, then applies `+0x1B4`. The action-timeline
consumer is owned by [Hit response](hit_response.md#descriptor-phase-control).
Thus a faster action-rate contribution does not shorten the generic effect's
counter through the countdown routine, and an active controller marker does
not guarantee that the rate contribution survives its combat gates.

## Effect-to-form mapping and resource replacement

The selected-UJ table contains 223 records of size `0x14` at runtime
`0x005AEC40`. `FUN_00372B10` reads each record's effect ID at `+0x0E`.
`FUN_00372D00(record_index)` reads that same field and maps only:

| Effect | Replacement character ID | Character/form |
| ---: | ---: | --- |
| `0x68` | `0x2F` | Naruto (Nine-Tailed) |
| `0x69` | `0x30` | Second Stage Sasuke |
| `0x6A` | `0x31` | Loopy Fist Lee |
| `0x6B` | `0x32` | Possessed Gaara |
| `0x6C` | `0x33` | Super Choji |
| `0x6D` | `0x34` | Second Stage Jirobo |
| `0x6E` | `0x35` | Second Stage Kidomaru |
| `0x6F` | `0x36` | Second Stage Tayuya |
| `0x70` | `0x37` | Second Stage Sakon |
| `0x71` | `0x38` | Second Stage Kimimaro |
| `0x72` | `0x49` | Nine-Tailed Fourth Awakened State |
| `0x73` | `0x4B` | Sasori (Puppet) |

Every other effect returns form `0`.

The complete 223-record table contains exactly 12 records whose effect is in
`0x68..0x73`. Each appears in exactly one native character-local UJ list:

| Base character | Local-list pointer | Record (`+0x04`) | Category `+0x06` | Default record? | Effect -> form |
| --- | ---: | ---: | ---: | --- | --- |
| Classic Naruto `0x01` | `0x00604320` | `2` (`2`) | `3` | No; default `1` | `0x68 -> 0x2F` |
| Classic Sasuke `0x02` | `0x00604328` | `4` (`5`) | `3` | No; default `3` | `0x69 -> 0x30` |
| Classic Rock Lee `0x03` | `0x00604330` | `5` (`7`) | `2` | Yes | `0x6A -> 0x31` |
| Classic Gaara `0x04` | `0x00604338` | `8` (`0x0B`) | `3` | No; default `7` | `0x6B -> 0x32` |
| Classic Choji `0x0E` | `0x00604380` | `34` (`0x1E`) | `3` | No; default `33` | `0x6C -> 0x33` |
| Jirobo `0x22` | `0x006043D8` | `66` (`0x34`) | `3` | No; default `65` | `0x6D -> 0x34` |
| Kidomaru `0x23` | `0x006043E0` | `68` (`0x37`) | `3` | No; default `67` | `0x6E -> 0x35` |
| Tayuya `0x24` | `0x006043E8` | `70` (`0x3A`) | `3` | No; default `69` | `0x6F -> 0x36` |
| Sakon `0x25` | `0x006043F0` | `72` (`0x3D`) | `3` | No; default `71` | `0x70 -> 0x37` |
| Kimimaro `0x26` | `0x006043F8` | `74` (`0x40`) | `3` | No; default `73` | `0x71 -> 0x38` |
| Naruto `0x39` | `0x00604460` | `111` (`0x4C`) | `3` | No; default `110` | `0x72 -> 0x49` |
| Sasori `0x3F` | `0x005ACF50` | `132` (`0x63`) | `3` | No; default `131` | `0x73 -> 0x4B` |

`FUN_003729F0(character,category)` begins with the character's default record
and replaces it with a local-list record whose `+0x06` category matches the
request. `FUN_002449C0` derives a UJ tier in this priority order: controller
marker `fighter+0x63:0x20` set gives tier `2`; otherwise HP
`fighter+0x6C <= 0.5` gives tier `1`; otherwise tier `0`. `FUN_001FE150` then
applies a per-side signed-byte tier remap. Its disabled behavior and the clean
initialized rows at `0x006B3128..0x006B3136` are identity mappings `0,1,2`.
After that remap, tier `0` requests category `2`, tier `1` category `3`, and
tier `2` category `1`.

Consequently, under the clean identity mapping, 11 transformation records are
the low-HP (`<= 50%`) category-3 UJ selection. Classic Rock Lee is the sole
exception: effect `0x6A` is his category-2/high-HP (`> 50%`) record, while his
category-3 record is non-transforming. This is a record-selection prerequisite,
not the post-UJ form request itself; the completion owner consumes the record
already stored in the manager and applies the separate gates below. Earlier
connection and presentation/resource gates are described in
[Ultimate Jutsu](ultimate_jutsu.md#start) and its
[skill-play admission](ultimate_jutsu.md#skill-play-admission) section; those
gates do not replace the completion predicates below.

`FUN_0035AF20` owns the demonstrated UJ-completion path. After tearing down its
17 owned entries and transient handles, it passes the side index from its
object `+0x28` to `FUN_0035B3B0` at direct callsite `0x0035B15C`.
`FUN_0035B3B0(side_index)` then reaches a form request only after these ordered
gates:

1. the battle manager exists;
2. manager mode `+0x0C` is not `6` (the clean Mode Select crosswalk identifies
   `6` as Collection);
3. `FUN_00373790()` does not return `2` (return `2` instead increments BTL
   result-bank metric `14` for the opposing side and returns);
4. `FUN_00372D00` maps the selected record at
   `manager+0x60+side_index*0x28` to a nonzero form;
5. `FUN_001FDB40(side_index+1,7) != 1`.

Only then does it call `FUN_001EC5E0(side_index+1,form_id)`, at the sole direct
callsite `0x0035B704`.

`FUN_00373790` itself only reads the resident word at `0x00607780`; its paired
setter is `FUN_00373780`. An exhaustive direct-`jal` scan found no resident
caller of that setter and exactly three BTL callers in the presentation/UJ
state machine beginning at exported `0x00769750`, live `0x00769790`:

| Value | BTL exported call | Live call | File offset | Proven condition |
| ---: | ---: | ---: | ---: | --- |
| `0` | `0x0076A0E8` | `0x0076A128` | `0x000B6228` | initialization path |
| `2` | `0x0076A54C` | `0x0076A58C` | `0x000B668C` | presentation state `4`, contest status `4`, and `FUN_0035DB20(0) != 0` |
| `1` | `0x0076A584` | `0x0076A5C4` | `0x000B66C4` | owned handle passes `FUN_001CDD80` |

Gate value `2` is the cinematic branch for the contest's defender
interruption, the event that result-bank metric `14` ("Defeat an enemy
Ultimate"; see [Battle statistics](battle_statistics.md#all-28-retail-metric-labels))
credits. Resident `FUN_0035F610` writes contest
status `4` exactly when the attacker-relative meter is below `-5`;
`FUN_0036C1A0` reads that status from contest `+0xD8`. In BTL presentation
state `4`, the status-`4` branch waits for `FUN_0035DB20(0)`, writes outcome
`2`, requests cinematic branch `2` through `FUN_001CDDD0`, and moves to state
`5`. `FUN_0035DB20` compares the cinematic's current frame against the selected
skill's halfword branch-frame entry. The full meter and cinematic behavior
belong to [Ultimate Jutsu](ultimate_jutsu.md#resolution).

In the BTL branch, the comparison with `4` is live `0x0076A568` and the
frame-gate call is live `0x0076A578`, followed by the outcome setter above.

The resident early-return path at `0x0035B430..0x0035B454` computes wrapper
side `(side_index == 0) + 1`: attacker index `0` increments side `2`, and
attacker index `1` increments side `1`. It therefore credits the opposing
side's result-bank metric `14`, then suppresses all subsequent completion
bookkeeping and the form request. A merely negative meter in `[-5,0)` produces contest status
`1`, not this branch; reduced UJ damage alone is not the outcome-`2` gate.

When the resident contest-object global at `0x00607750` is empty, the main
manager skips both the object's update dispatcher `FUN_0036BF10` and render
dispatcher `FUN_0036BFF0`, and `FUN_0036C1A0` returns status zero. The contest
timer and result-display dependencies are described in
[Ultimate Jutsu](ultimate_jutsu.md#contest-objects). None of these completion
gates reads the contest object, and `FUN_0035AF20` calls `FUN_0035B3B0`
unconditionally. What contest type `0` does remove is the separate
[post-UJ outcome effect](#post-uj-outcome-effect).

The final gate is a per-side UJ defeat latch, not a chakra or resource check.
`FUN_001FDB40(side,index)` reads a `3 * 0x5D` state matrix at `0x006B2B40`,
with side stride `0x174`; slot `7` is `0x006B2CD0` for side 1 and
`0x006B2E44` for side 2. `FUN_001FD7D0` initializes every entry to `-1`, and
`FUN_001FD850` is its writer. The sole statically decoded constant-slot-`7`
setter writes `1` from `FUN_0035B740` when the UJ-global flag at
`0x00604314` equals `1` and the target fighter's HP at `+0x6C` is at or below
zero. Five reset/abort branches at callsites `0x00362D24`, `0x003649C4`,
`0x00365634`, `0x00366C90`, and `0x00368C84` restore slot `7` to `-1`.
Therefore value `1` specifically suppresses replacement on this proven
defeat outcome; initialized/reset value `-1` permits the form gate.

`FUN_001EC5E0` stages the replacement rather than editing the live fighter:

- sets phase `0x00607678 = 1`, re-entry variant `0x0060767C = 1`, and
  route `0x00607670 = 8`;
- writes the pending form to manager `+0x50` for side 1 or `+0x78` for side 2.

The relevant manager-side fields are:

| Side | Current character | Pending character | Match-start/saved character |
| ---: | ---: | ---: | ---: |
| 1 | `+0x4C` | `+0x50` | `+0xC8` |
| 2 | `+0x74` | `+0x78` | `+0xF0` |

Because `FUN_001EC5E0` writes re-entry variant `1`, `FUN_001EDD10` sends the
request to state `0x17`, `FUN_001EE1C0`. That routine identifies the side with
the nonzero pending ID and, after destroying the old battle state, calls
`FUN_001E8EE0`. That helper releases the target side's cached-resource mask
`0x113` through `FUN_001E8960` when its current character differs from the
other side, then releases its additional
slots `5..7` and two trailing handles without freeing a pointer still shared
by the other side. The handler resets the side's cached slots through
`FUN_001E7FE0`, copies the pending ID into its current-character field at
`0x001EE320`, reinitializes the side record, recomputes its selected UJ data
through `FUN_001F4F70`, and loads the new character's full resource mask
through `FUN_001E80F0(manager,target_side,0x1FF,1)` at `0x001EE36C`.
`FUN_001E80F0` returns no status and the handler has no post-load failure or
rollback branch: it proceeds to phase `2` at `0x001EE3A0`, clears both pending
IDs and manager `+0x9A` through `FUN_001F4F20`, and selects manager state
`0x0D`.

Crucially, this state-`0x17` form path does **not** call `FUN_001F4DD0`, so it
does not overwrite the saved/match-start configuration. State `0x18`, reached
only by the separately proven variant-`2` route, has different ownership: it
can release and restore an altered other side through `FUN_001E8960` and
`FUN_001EE3E0`, and it calls `FUN_001F4DD0` after installing its pending ID.
It also finishes at phase `2`, which is why the phase is a shared rebuild
boundary rather than proof of an awakening swap by itself.
Subsequent controller creation by `FUN_001EC3B0` preserves the result bank and
advances the phase to `3`.

`FUN_001E80F0` loads the per-side cached resource arrays using the current
character field. `FUN_001E8EE0` and `FUN_001E8960` own the corresponding
pending-side release and masked release, with shared-pointer protection. These
manager helpers, not the generic class-3 effect records, own resource
replacement.

On construction of the replacement fighter, `FUN_00305FF0` mirrors the same
mapping:

- character `0x2F..0x38` receives effect `character_id + 0x39`, or
  `0x68..0x71`;
- character `0x49` receives `0x72`;
- character `0x4B` receives `0x73`;
- each call is `FUN_00305C30(fighter,effect,-2,1)`.

This constructor does not set controller bit `+0x63:0x20`. The next controller
pass can adopt the transformed identity through bit `0x01`/
`FUN_0020D030`.

### Replacement character parameters

All 12 class-3 records have the same neutral gameplay payload at record-base
`+0x14..+0x58`: `1.0` at `+0x14..+0x2C` and `+0x34`, and zero at
`+0x30/+0x38..+0x58`. Their differing IDs and presentation selectors do not
change those values. Generic construction copies this payload to node
`+0x74..+0xB8`. Thus the inherent `-2` node contributes no attack, defense,
update-rate, jump, motion, recovery, recurring HP/chakra, or guard-damage
modifier through the scoped generic consumers. Flags `2` also grant none of
the `0x10/0x20/0x40/0x80` effect-list privileges. Payload and flag consumers
are owned by
[Battle status effects](battle_items_and_status_effects.md#concurrent-payload-contributions).
This does not classify the replacement form's move-specific attack flags.

The replacement instead selects a different static character record.
`FUN_002151E0` copies all 55 words of that record `+0x00..+0xD8` into the new
fighter `+0x8C..+0x164`. Targeted reads of every native base/form pair establish
these changes in the four fields with confirmed resource/damage meanings:

| Base -> form | Offense `record +0xBC` | Durability `+0xC0` | HP recovery `+0xD4` | Chakra recovery `+0xD8` |
| --- | --- | --- | --- | --- |
| `0x01 -> 0x2F` | `1.10 -> 1.25` | `0.90 -> 1.20` | `1.00 -> 1.10` | `1.20 -> 1.50` |
| `0x02 -> 0x30` | `1.10 -> 1.20` | `1.00 -> 1.10` | `0.90 -> 0.90` | `1.00 -> 0.90` |
| `0x03 -> 0x31` | `1.05 -> 1.20` | `1.10 -> 1.15` | `0.85 -> 1.10` | `0.80 -> 1.10` |
| `0x04 -> 0x32` | `0.90 -> 1.30` | `1.10 -> 1.20` | `1.00 -> 1.00` | `0.90 -> 0.90` |
| `0x0E -> 0x33` | `1.05 -> 1.25` | `1.05 -> 1.10` | `0.85 -> 0.85` | `0.85 -> 0.90` |
| `0x22 -> 0x34` | `1.05 -> 1.25` | `1.05 -> 1.20` | `0.85 -> 1.20` | `0.85 -> 1.20` |
| `0x23 -> 0x35` | `1.00 -> 1.20` | `1.00 -> 1.10` | `1.00 -> 1.00` | `1.00 -> 1.00` |
| `0x24 -> 0x36` | `0.95 -> 1.30` | `0.95 -> 0.85` | `1.10 -> 0.90` | `1.10 -> 0.90` |
| `0x25 -> 0x37` | `1.05 -> 1.20` | `0.90 -> 1.10` | `0.95 -> 1.05` | `0.95 -> 1.00` |
| `0x26 -> 0x38` | `1.10 -> 1.20` | `0.95 -> 1.10` | `1.05 -> 1.05` | `1.00 -> 1.00` |
| `0x39 -> 0x49` | `1.10 -> 1.25` | `0.90 -> 1.20` | `1.00 -> 1.10` | `1.20 -> 1.50` |
| `0x3F -> 0x4B` | `1.10 -> 1.10` | `0.90 -> 0.90` | `1.00 -> 1.00` | `1.20 -> 1.20` |

Values are rounded decimal presentations of the copied single-precision
fields, not additional effect multipliers. Record addresses and character
names remain in the [character reference](../../../resources/character_data.tsv);
the durability conversion and recovery consumers remain in
[Damage](damage.md#confirmed-character-record-fields).
Tayuya's `0x24 -> 0x36` pair lowers the durability parameter, and Sasori's
`0x3F -> 0x4B` pair changes none of these four fields. Native form replacement
therefore does not impose a universal increase in all confirmed stat fields.
The comparison covers the copied records; it does not prove that no later
character callback can alter another working field.

#### Selected transformed callbacks and destination bases

The selected post-copy audit distinguishes concrete callback work from a
second stat multiplier. Loopy Fist Lee `0x31` uses record `0x004B2110`, whose
callback-vector pointer is `0x004AC720`. Its `+0x04/+0x08` entries are
`FUN_00283430/FUN_00283A70`; the `+0x0C` response entry is `FUN_00284FE0`.
Under major/substate `(0,0)`, the first callback adds `0.25` times the float
at fighter `+0xC50` to the transient vector at `+0x4E0`
(`0x0028347C..0x002834B0`). The shared movement consumer adds this vector
to displacement, and the enclosing update clears it; see
[Movement and physics](movement_and_physics.md#shared-movement-fields-and-ordering).
This is action-dependent motion, not a change to the copied ground target
or the neutral class-3 payload.

Nine-Tailed Fourth `0x49` uses record `0x00535D50` and callback vector
`0x00530B80`: `+0x00` is the literal `jr ra; nop` body at `0x002D12C0`,
`+0x04/+0x08` are `FUN_002D1380/FUN_002D1830`, and `+0x0C` is
`FUN_002D2560`. The second callback performs action-selected position/vector
work, including stores to `+0x30/+0x970` and clearing velocity fields
`+0x994/+0x998`. Its apparent `+0xEC/+0xF0/+0xF4/+0x110` stores instead
use `sp`; they are stack values, not primary-fighter movement overrides.

Both selected response callbacks conditionally write the receiver's
`+0x9A0/+0x9A8/+0x9AC` during invocation mode `2`, in addition to returning
a response choice and changing selected attack-record fields. The source/
receiver convention and downstream meanings remain in
[Hit response](hit_response.md#character-response-callbacks).
In these complete callback instruction bodies, no direct primary-fighter
write to offense `+0x148`, durability `+0x14C`, or recovery
`+0x160/+0x164` was found. This negative result covers the listed bodies,
not every callback slot, delegated helper, or update path of either form.
The callback dispatch contract remains in
[Character action callbacks](character_action_callbacks.md#evidence-convention-and-ownership).

Other matching displacements also need their register bases resolved.
`FUN_00251230`, `FUN_0028CA80`, `FUN_00296740`, and `FUN_0029FEB0` load a
scratch pointer through `gp-0x35F4`, then manager `+0x1C0`, reserve `0x120`
bytes, and use that pointer for the apparent `+0xF0/+0xF4` writes.
Representative pairs are `0x00252078/0x00252080`,
`0x0028EA48/0x0028EA50`, `0x0029877C/0x00298784`, and
`0x002A1A4C/0x002A1A54`. The first body uses `s3` for this allocation and
`s0` for the primary fighter; the other three use `s1` for the allocation
and `s4` for the fighter. These stores do not establish
overrides of the primary fighter's identically numbered fields. A full
audit of all indirectly addressed parameter writers remains open.

### Static reconstruction order

The native swap changes one manager-side character ID but reconstructs the
whole primary-fighter graph. The relevant instruction order is:

1. State `0x17` first saves both sides' HP/chakra through
   `FUN_001ECC00(...,-2,-1)` at `0x001EE1EC`. It then calls the existing
   battle-state destructor `FUN_001EECD0(...,1)` at `0x001EE20C`, before
   releasing the target side's character resources or installing its pending
   ID. The destructor reaches `FUN_001EEFD0`, clears manager fighter aliases,
   and destroys the old hub through live BTL `0x00709280`. The fighter registry
   destructor `FUN_0024E250` removes all its nodes; every table-selected
   concrete fighter destructor reaches `FUN_00215720`, whose
   `FUN_00305750` call force-removes its effect container. The complete
   lifetime dispatch evidence is in
   [Battle entities](battle_entities.md#complete-table-selected-concrete-lifetime-paths).
2. The state-`0x17` handler installs the target's pending character at
   `0x001EE320`, loads its resources at `0x001EE36C`, writes phase `2`, and
   routes through manager states `0x0D` and `0x0E`. State `0x0E` handler
   `FUN_001EDB00` waits for its two preparation predicates, then calls
   `FUN_001EC3B0` at `0x001EDB3C`.
3. On successful battle-state allocation, `FUN_001EC3B0` calls
   `FUN_001EF330`, whose live BTL `0x00709480` call at `0x001EF3C0` constructs
   both fighters. Live `0x00709860` reads each current manager-side identity
   and dispatches through resident factory table `0x005A2900`. Common base
   constructor `FUN_002145D0` calls `FUN_00214A40` at `0x00214810`, clearing
   controller marker `+0x63:0x20` and initializing a fresh effect container.
   Common setup `FUN_002151E0` then copies the selected record identity to
   fighter `+0x68` at `0x002153BC`; it does not rewrite the old fighter in place.
4. In successful setup, `FUN_002151E0` calls transformed-effect constructor
   `FUN_00305FF0` at `0x0021563C`, initializes action `(0,0)`, and only then
   enables node update bit `+0x00:0x02` at `0x00215670`. Thus the replacement
   identity and any
   successfully inserted constructor-owned `-2` node precede update enable,
   while the awakening marker remains clear until controller adoption.
5. The setup route republishes both new fighter aliases through live BTL
   `0x007099C0` at resident calls `0x001EF3F8` and `0x001EF40C`, then restores
   the saved values through `FUN_001ECDE0` for re-entry variant `1` (see
   [Battle lifecycle](battle_lifecycle.md#values-crossing-the-reconstruction-boundary)).
   Subsequent eligible controller dispatch adopts each recognized transformed
   identity. The adoption gate is identity-based, so it does not certify
   successful insertion of the protected effect node.

These are ordered static writes/calls, not measured animation or display
boundaries. Old effect nodes are destroyed and replacement nodes are newly
constructed; neither the pending-ID write nor phase `3` transfers an old
effect container into the new fighter.

### State retained across the native rebuild

The state-`0x17` route saves and restores both sides' HP, chakra, remaining
and elapsed timer words, and eligible inventory entries (side `-2`, mask
`-1`), and preserves the BTL result bank and both external fighter-statistics
banks through continuation phase `2`. Everything else on the new fighters,
including native combo objects, action/progress state, Tenten counter `+0xB78`,
and controller bits, is freshly constructed. The save/restore contract and the
statistics-bank reload belong to
[Battle lifecycle](battle_lifecycle.md#values-crossing-the-reconstruction-boundary).

#### Reconstruction adoption increment

Later transformed-identity adoption does not repair the statistics reload
ordering described in
[Battle lifecycle](battle_lifecycle.md#fighter-statistics-across-reconstruction).
`FUN_0020D030` and the dispatcher route traced above operate on the new
fighter and retained result-bank metric `10`. A nonzero metric skips the
event increment but still calls `FUN_00223140(fighter,0x11,0)`; the zero block
argument selects the new local `+0x4F0` block. Unless root suppression
`+0x62:0x01` blocks that helper, adoption increments local `+0x534` and may
raise `+0x536`, even when the result bank suppresses a repeated event credit.
It neither reloads bank one nor writes either external bank. A subsequently
adopted transformed fighter therefore adds its local awakening statistic to
the pair values copied by its common constructor.

**Conclusion, high confidence:** native replacement preserves selected battle
values and external statistics banks while reconstructing both fighters'
local action, combo, and effect ownership. This is a bounded audit of the
save/restore helpers and cited constructors, not a claim that every field in
the rebuilt battle graph was classified.

### Reserved transformed slot `0x4A`

Resident helper `FUN_001F7C80` at `0x001F7C80` maps every normal/form pair used
by the roster helpers. Among the proven pairs it maps Chiyo `0x3E` to `0x4A`,
maps Sasori `0x3F` to `0x4B`, and maps Naruto `0x39` to `0x49`. It also returns
each transformed ID when that transformed ID is supplied. `FUN_001F7BC0` at
`0x001F7BC0` classifies `0x4A` with the other transformed IDs. This establishes
a Chiyo-to-`0x4A` pairing in clean resident code.

The pairing is asymmetric and incomplete:

- roster-validity filter `FUN_001F7AA0` at `0x001F7AA0` explicitly rejects
  `0x4A`; roster consumers test this result before accepting an ID;
- reverse mapper `FUN_001F7E70` at `0x001F7E70` maps `0x4B -> 0x3F` and
  `0x49 -> 0x39`, plus `0x2F..0x38` to their normal forms, but has no `0x4A`
  case and returns `-1`;
- the complete eight-byte character factory/record entry at `0x005A2B50` is
  byte-for-byte the ID-`0x01` entry at `0x005A2908`: factory `0x00250C00` and
  static record `0x0040DB70`; that record's `+0x00` identity is `0x01`, not
  `0x4A`;
- its UJ-list pointer at `0x005AD0D8` is null, descriptor row at `0x005C1C78`
  is `{-1, flags 0}`, and association row at `0x005C1F80` is empty;
- neither `FUN_00372D00` nor transformed-fighter constructor
  `FUN_00305FF0` has a `0x4A` mapping.

Unlock helper `FUN_001F5500` can mark the forward-mapped slot alongside its
base ID, but the roster-validity filter still excludes `0x4A`. In battle, the
controller's transformed-ID special cases recognize an already-existing
`0x4A`: ordinary entry would set marker `+0x63:0x20` without constructing an
effect, and reconciliation returns immediately. No clean path found here can
construct a genuine `0x4A` fighter or request it after a UJ.

**Conclusion, high confidence:** `0x4A` is a reserved/incomplete transformed
identity paired forward with Chiyo, backed by the ID-`0x01` fallback factory
and record rather than its own character implementation. The pairing is useful
as cut/incomplete-form evidence, but it is not a native reachable awakening.

## Controller exit and reconciliation

`FUN_0020DD20` is flag cleanup only:

- if controller bit `+0x63:0x20` is clear, return `0`;
- otherwise clear it and return `1`;
- for Deidara `0x40` or Gaara `0x3B`, also clear `+0x63:0x10` and call
  `SUB_006F09E0(fighter+0x24)`;
- never remove an effect node.

`FUN_0020DDC0` reconciles an already-marked fighter against its association
list; it is not a universal effect destructor:

- Taijutsu Chiyo `0x4D`: when
  `FUN_002274C0(fighter,2,0,0)` succeeds, remove associated effects below
  `0x68` (natively `0x4E`), raise event `0x3A`, and clear the controller marker.
- Character `0x19`: remove effects `0x22` and `0x23` if present, then continue
  reconciliation against associated `0x24`.
- Transformed IDs `0x2F..0x38`, `0x49`, `0x4A`, and `0x4B`: return immediately.
- Might Guy `0x45`: while an associated effect remains and the raw predicate
  succeeds, re-enter `FUN_0020D910` to advance its stage.
- Sakura `0x3A`: while associated state remains, remove effect `0x07` if live.
- Tenten `0x42` and Classic Tenten `0x0D`: reset `+0xB78` while associated
  state remains.
- If no associated effect remains, clear controller bit `0x20`; Deidara/Gaara
  also receive the paired special cleanup.

An additional caller, `FUN_0035CA80` in the resident UJ factory (see
[Ultimate Jutsu cinematics](ultimate_jutsu_cinematics.md#opponent-dependent-cinematic-selection)), resolves the
live fighter for character `0x51` and calls `FUN_0020DD20`. For requested ID
`0x95` while marked awakened, it clears the marker and substitutes `0x96`.
This agrees with the controller suppression gate specially preserving
character `0x51`, but the surrounding gameplay label was not established.

The lifecycle therefore has distinct exits:

- global suppression may clear only controller flags;
- association reconciliation may clear flags after effects disappear;
- targeted `FUN_00305510` calls remove selected nodes;
- constructor-owned transformed nodes survive ordinary reasons;
- fighter teardown force-removes the whole effect container.

### Manager identity and resource reset

The manager keeps a saved copy of the battle configuration rather than
requesting an inverse live transformation. `FUN_001F4DD0` copies `0x78` bytes
from current configuration `manager+0x20..+0x97` to saved configuration
`manager+0x9C..+0x113`, plus bytes `+0x98..+0x9A` to `+0x114..+0x116`.
Consequently current character fields `+0x4C/+0x74` are snapshotted at
`+0xC8/+0xF0`. The post-UJ form path changes the current target record through
state `0x17`, which contains no `FUN_001F4DD0` call, and therefore does not
overwrite this saved copy. The variant-`2` state-`0x18` route does snapshot
its new current configuration and must not be conflated with the native
post-UJ transformation route.

Reset helper `FUN_001FE920` compares each current character field with its
saved counterpart and builds a changed-side mask. It first releases cached
resources through `FUN_001E8960(manager,side,0x1FF)` for every changed side.
After that release loop, it calls `FUN_001F4ED0` once to copy the entire saved
`0x78`-byte configuration and three trailing bytes back over the current copy.
It then loops over the mask again and reloads each changed side through
`FUN_001E80F0(manager,side,0x1FF,...)`.

`FUN_001FED10` calls this reset at direct callsite `0x001FEE50` on its result
choice `0`, after the battle-state transition it owns. This restores manager
identity and resource ownership outside the live awakening controller. Fighter
teardown remains responsible for force-removing the old fighter's class-3
effect node.

There is no decoded direct in-battle reverse request. Resident
`FUN_001EC5E0` has exactly one direct `jal`, at `0x0035B704` in
`FUN_0035B3B0`; its input comes from `FUN_00372D00`, which returns only forward
form IDs `0x2F..0x38`, `0x49`, or `0x4B`. The separate inverse identity helper
`FUN_001F7E70` has ten direct callers, but none belongs to the manager swap
chain or calls `FUN_001EC5E0`; those callers normalize local IDs for
event/selection logic. The supported lifecycle is therefore one-way replacement
inside a live battle, followed by saved-configuration restoration and object
teardown at reset, not an in-place transformed-to-base swap.

## Address index

All addresses in this table are live resident runtime addresses unless marked
BTL.

| Address | Symbol/data | Established role |
| ---: | --- | --- |
| `0x0020C270` | `FUN_0020C270` | Allocate per-side combo object |
| `0x0020C3D0` | `FUN_0020C3D0` | Reset newly allocated combo counts and timer |
| `0x0020C420` | `FUN_0020C420` | Consume pending accepted hits into current combo |
| `0x0020CF40` | `FUN_0020CF40` | Test associated-effect presence |
| `0x0020D030` | `FUN_0020D030` | Adopt existing or constructor-owned state |
| `0x0020D5D0` | `FUN_0020D5D0` | Character-specific combo thresholds |
| `0x0020D690` | `FUN_0020D690` | Exact class-7 selected-effect path |
| `0x0020D910` | `FUN_0020D910` | Ordinary controller entry and selection |
| `0x0020DD20` | `FUN_0020DD20` | Clear controller/special flags |
| `0x0020DDC0` | `FUN_0020DDC0` | Reconcile marked state and associations |
| `0x0020E280` | `FUN_0020E280` | Per-fighter descriptor dispatcher |
| `0x0020EA90` | `FUN_0020EA90` | Deidara/Gaara exception to root suppression |
| `0x0020EAE0` | `FUN_0020EAE0` | Awakened Deidara/Gaara variable up/down input and altitude control |
| `0x00114B40` | `FUN_00114B40` | Convert a pad stick to angle and magnitude |
| `0x00180D10` | `FUN_00180D10` | Test angle within half a sector width of a target |
| `0x00211770` | `FUN_00211770` | Initialize/reset scalar progress tracker |
| `0x002117A0` | `FUN_002117A0` | Set all progress positions to one value |
| `0x002118A0` | `FUN_002118A0` | Test position with tracker crossing bit `0x01` |
| `0x00211A20` | `FUN_00211A20` | Test position with tracker crossing bit `0x02` |
| `0x00211D80` | `FUN_00211D80` | Advance scalar progress tracker |
| `0x002151E0` | `FUN_002151E0` | Fighter setup caller of transformed-effect constructor |
| `0x00214A40` | `FUN_00214A40` | Clear side before common local-state/statistics initialization |
| `0x00215720` | `FUN_00215720` | Fighter teardown caller of force cleanup |
| `0x00217320` | `FUN_00217320` | Copy the command interpreter word to fighter `+0x338` |
| `0x00217E40` | `FUN_00217E40` | Transition major action state and substate |
| `0x00223360` | `FUN_00223360` | Map event code `6` to result-bank metric `10` and increment it |
| `0x00223140` | `FUN_00223140` | Increment capped current/high-water statistics; awakening uses index `0x11` |
| `0x00222F00` | `FUN_00222F00` | Reset local statistics, preserve external bank during phase `2`, then reload |
| `0x00223040` / `0x002230A0` | statistics save/reload | Copy 24 pairs between fighter and side-indexed external bank |
| `0x00223250` | `FUN_00223250` | Clear one of 63 local five-halfword action-statistic rows |
| `0x002274C0` | `FUN_002274C0` | Exact raw fighter-state gate |
| `0x002378A0` | `FUN_002378A0` | Validate pending item-use action before counter increment |
| `0x002378F0` | `FUN_002378F0` | Start accepted kind-`3`/`6` item route and increment `+0xB78` |
| `0x002449C0` | `FUN_002449C0` | Request class-7 UJ selector keys |
| `0x00248EC0` | `FUN_00248EC0` | Bypass ordinary held-up/down transitions for awakened Deidara/Gaara |
| `0x0024A660` | `FUN_0024A660` | Consume vertical velocity in the fighter movement delta |
| `0x0024DA50` | `FUN_0024DA50` | Representative fighter update caller |
| `0x0025DEF0` | `FUN_0025DEF0` | Classic Tenten projectile-create counter producer |
| `0x00299100` | `FUN_00299100` | Naruto direct low-HP effect callback |
| `0x002B9660` | `FUN_002B9660` | Tenten projectile-create counter producer |
| `0x0029BF90` | `FUN_0029BF90` | Initialize Gaara's ordinary variant and disable alternate slots |
| `0x0029C1E0` | `FUN_0029C1E0` | Switch Gaara action categories, animation pointers, and float fields |
| `0x0029D7E0` | `FUN_0029D7E0` | Gaara variant's marker/effect/progress gates |
| `0x002B4860` | `FUN_002B4860` | Switch Deidara variant byte, animation pointers, and float fields |
| `0x002B49C0` | `FUN_002B49C0` | Switch Deidara ordinary/alternate action categories |
| `0x002B4D60` | `FUN_002B4D60` | Deidara association-presence variant gate |
| `0x002E8C10` | `FUN_002E8C10` | Choji constructor forcing the mode-zero parameter overwrite |
| `0x002E8E90` | `FUN_002E8E90` | Choji marker-selected mode, ground-target, and action-category setter |
| `0x002E9AB0` | `FUN_002E9AB0` | Choji callback selecting mode from the controller marker |
| `0x00283430` / `0x00283A70` | Loopy Fist Lee callbacks | Selected transient-motion and action work |
| `0x002D1380` / `0x002D1830` | Nine-Tailed Fourth callbacks | Selected contact/presentation and action-position work |
| `0x00284FE0` / `0x002D2560` | selected form response callbacks | Receiver response-field writes, separate from copied primary stats |
| `0x003047C0` | `FUN_003047C0` | Effect classifier |
| `0x00304D60` | `FUN_00304D60` | Generic positive-lifetime decrement |
| `0x00305040` | `FUN_00305040` | Removal-reason and unlink decision |
| `0x00305210` | `FUN_00305210` | Find exact effect node |
| `0x00305270` | `FUN_00305270` | Construct/replace and append effect node |
| `0x00305470` | `FUN_00305470` | Initialize fighter effect container/cache |
| `0x00305510` | `FUN_00305510` | Remove all nodes with exact ID |
| `0x003055C0` | `FUN_003055C0` | Bulk-remove effect classes `0..2` |
| `0x00305750` | `FUN_00305750` | Force-remove classes `0..4` |
| `0x003059B0` | `FUN_003059B0` | Per-frame effect expiry/removal pass |
| `0x00305C30` | `FUN_00305C30` | High-level effect entry |
| `0x00305FF0` | `FUN_00305FF0` | Constructor-owned transformed effect mapping |
| `0x00306420` | `FUN_00306420` | Authoritative effect presence traversal |
| `0x00306D30` | `FUN_00306D30` | Effect action-rate fold and combat neutralization gates |
| `0x00306F00` / `0x00307020` | HP/chakra contribution folds | Aggregate recurring values and test resource boundaries |
| `0x0024ED40` | `FUN_0024ED40` | Post-cinematic coordinator; state `1` clears class-`0..2` nodes and applies the outcome effect |
| `0x00307690` | `FUN_00307690` | `FUN_00305C30(fighter,effect,-1,1)` wrapper |
| `0x0035CF00` | `FUN_0035CF00` | Skill-play constructor; starts the contest outside mode `6` |
| `0x0035E360` | `FUN_0035E360` | Shared contest initializer; seeds the outcome effect |
| `0x0036B6D0` | `FUN_0036B6D0` | Contest factory; type `0` constructs nothing |
| `0x0036C0D0` | `FUN_0036C0D0` | Battle-setup reset of the contest globals |
| `0x0036C1E0` | `FUN_0036C1E0` | Read the outcome effect ID |
| `0x0036C1F0` | `FUN_0036C1F0` | Read `0x00604314` |
| `0x0035AF20` | `FUN_0035AF20` | UJ-completion teardown and direct owner of the form-map call |
| `0x0035B3B0` | `FUN_0035B3B0` | Apply post-UJ gates and request a mapped replacement form |
| `0x0035B740` | `FUN_0035B740` | Set per-side UJ defeat latch when its flag and target-HP tests pass |
| `0x0035F610` | `FUN_0035F610` | Write contest status `4` for attacker-relative meter below `-5` |
| `0x0036C1A0` | `FUN_0036C1A0` | Read the contest status consumed by BTL presentation |
| `0x00376160` | `FUN_00376160` | Map selected small effect IDs to a BTL notification; class `3` has no row |
| `0x00376610` | `FUN_00376610` | Resolve the active battle object for optional effect notification |
| `0x00373780` | `FUN_00373780` | Set the BTL-owned UJ outcome/state word |
| `0x00373790` | `FUN_00373790` | Read the BTL-owned UJ outcome/state word |
| `0x003729F0` | `FUN_003729F0` | Select default/keyed character-local UJ record |
| `0x00372B10` | `FUN_00372B10` | Read UJ record effect field |
| `0x00372D00` | `FUN_00372D00` | Map UJ effect to replacement character ID |
| `0x001EC5E0` | `FUN_001EC5E0` | Stage pending form and replacement globals |
| `0x001EC3B0` | `FUN_001EC3B0` | Battle-controller creation and result-bank clear/preserve boundary |
| `0x001EC960` | `FUN_001EC960` | Main dispatcher containing re-entry states `0x17` and `0x18` |
| `0x001ECC00` | `FUN_001ECC00` | Save both fighters' HP/chakra, match-timer words, and inventory before native swap teardown |
| `0x001ECDE0` | `FUN_001ECDE0` | Restore scoped values after native re-entry reconstruction |
| `0x001E80F0` | `FUN_001E80F0` | Load per-side character resources |
| `0x001E8EE0` | `FUN_001E8EE0` | Release pending side's old resources with shared-pointer protection |
| `0x001E8960` | `FUN_001E8960` | Release per-side cached resources |
| `0x001EDD10` | `FUN_001EDD10` | Dispatch route `8` by re-entry variant to state `0x17` or `0x18` |
| `0x001EE1C0` | `FUN_001EE1C0` | Native post-UJ form/resource replacement; preserves saved configuration |
| `0x001EE3E0` | `FUN_001EE3E0` | Restore saved side record |
| `0x001EE500` | `FUN_001EE500` | Variant-`2` pending-ID rebuild; snapshots its new configuration |
| `0x001EECD0` | `FUN_001EECD0` | Destroy the old battle-state object and its hub |
| `0x001EEFD0` | `FUN_001EEFD0` | Session destructor; destroys and frees the pause controller |
| `0x001EF330` | `FUN_001EF330` | Session builder; allocates and initializes the pause controller |
| `0x001EF9C0` | `FUN_001EF9C0` | Representative caller of phase-`1` readiness barrier |
| `0x001F0F40` | `FUN_001F0F40` | Synchronize allocated side objects during phase `1` |
| `0x001F4DD0` | `FUN_001F4DD0` | Snapshot current manager configuration into the saved baseline |
| `0x001F4ED0` | `FUN_001F4ED0` | Restore saved manager configuration over current copy |
| `0x001F4F20` | `FUN_001F4F20` | Clear pending form IDs |
| `0x001F7AA0` | `FUN_001F7AA0` | Roster-validity exclusion including reserved ID `0x4A` |
| `0x001F7BC0` | `FUN_001F7BC0` | Classify transformed character IDs including `0x4A` |
| `0x001F7C80` | `FUN_001F7C80` | Forward normal-to-transformed pairing, including `0x3E -> 0x4A` |
| `0x001F7E70` | `FUN_001F7E70` | Reverse transformed pairing; omits `0x4A` |
| `0x001FD7D0` | `FUN_001FD7D0` | Initialize the three-side event/state matrix to `-1` |
| `0x001FD850` | `FUN_001FD850` | Write one side/index event-state entry |
| `0x001FDB40` | `FUN_001FDB40` | Read one side/index event-state entry |
| `0x001FE920` | `FUN_001FE920` | Release, restore, and reload sides whose current identity differs from saved |
| `0x001FED10` | `FUN_001FED10` | Reset-state caller of manager identity/resource restoration |
| `0x00607678` | shared re-entry phase | `0` ordinary, `1` requested, `2` prepared, `3` reconstruction attempted |
| `0x0060767C` | re-entry variant | Route `8`: `1` selects state `0x17`; `2` selects state `0x18` |
| `0x00607780` | BTL-owned UJ outcome/state | `2` diverts post-UJ completion away from form replacement |
| `0x00604314` | UJ outcome flag | Value `1` plus target HP `<= 0` sets side state slot `7` to `1`; also selects `FUN_0024ED40`'s state after state `1` |
| `0x00604310` | post-UJ outcome effect ID | Seeded by `FUN_0035E360`; `-1` from setup and status-`4` clears |
| `0x006B2B40` | per-side condition-status matrix | Three rows of `0x5D` words; row stride `0x174` |
| `0x006B31D0` | external fighter statistics | Two banks selected by side bit; stride `0x2D6`, pair-copy length `0x60` |
| `0x005A2900` | character factory/record table | 94 eight-byte entries; factory at `+0`, record pointer at `+4` |
| `0x0059E2A4` | effect-record factory anchor | Base used with stride `0x64` |
| `0x005B0040` | effect-notification map | Twelve `(effect ID, BTL selector)` rows; no class-3 ID |
| `0x005ACFB0` | character UJ-list pointer table | Lists of `s16` UJ-record indices |
| `0x005AEC40` | UJ record table | 223 records, stride `0x14` |
| `0x005AFDB0` | default UJ-record index table | Per-character default selection |
| `0x005C1B50` | trigger descriptor table | 94 records, stride `4` |
| `0x005C1D30` | association table | 94 records, stride `8` |
| `0x005DDD30` | `ccCommand` vtable | Fighter `+0x24` command-input interpreter |
| `0x004074F0` / `0x00407510` | altitude-control float records | Gaara / Deidara increments, limits, and neutral return rates |
| BTL `0x006EF810` | direction test | Map a direction code to a target angle and test the stick against a sector width |
| BTL `0x006EFDC0` | command builder | Build command word `+0xAC` from the stick and button history |
| BTL `0x006F0EA0` | `ccCommand` update | Snapshot pad input, refresh relative angles, build commands |

## Negative results and open questions

- **High:** clean descriptor bit `0x20` is unused; the controller dispatcher
  has no general chakra read or universal HP test.
- **High:** association membership alone does not prove an entry route, and a
  bit-`0x01` descriptor alone does not prove `FUN_0020D030` can succeed.
- **High:** the effect cache at fighter `+0x8E8` is not authoritative after
  deletion.
- **High:** class-3 records `0x68..0x73` contain no custom factory or resource
  swap callback; the manager state machine owns form/resource replacement, and
  transformed-form construction does not set the controller marker.
- **High:** character ID `0x4A` is a reserved/incomplete transformed slot with
  no native reachable transformation route.
- **Medium:** BTL has no conventional direct ownership of the controller, but
  dynamic wrapper inputs and indirect computation are not excluded.
- **Open:** the exact visible timing of the action-progress trigger, controller
  bits, effect nodes, character identity, and presentation changes.
- **Open:** later primary-parameter writers and delegated helpers of the
  selected transformed forms have not all been audited.
- **High:** contest type `0` removes the post-UJ outcome effect, which is the
  whole post-UJ awakened state for non-transforming records; the form
  request's gates have no static contest dependency.
- **Open:** the character and record used in the contest-type-`0` runtime
  experiment; a transforming record there would remain unexplained.
