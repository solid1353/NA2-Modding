# Battle item inventory

This document records how retail NA2 (`SLPS-25837`) generates, stores,
selects, uses, draws, drops, and restores the per-side three-slot battle-item
inventory, how it selects random field items, and the lifecycle of field-pickup
objects. Item effects applied on use are owned by
[Battle status effects and item-effect lifecycle](battle_items_and_status_effects.md#three-slot-battle-item-path-0x510x73).
The five-slot inventories of retail NUN3 and NUN4 are recorded in
[NUN3 and NUN4 item inventories](item_wheels_nun3_nun4.md).

Addresses use `D/L/F`: preserved Ghidra address, live runtime address, and
complete-file offset
([address conventions](../../game/files/file_identities.md#address-conventions)).
Direct call targets and absolute data operands are live addresses.

## Research coverage

- **Assigned scope:** the inventory panel layout, every BTL routine that walks
  its slots, the resident wrappers that reach them, starting-item generation,
  item selection, selected-use gating, delayed dispatch and consumption, the
  item-to-projectile config mapping, the battle HUD item wheel, field-object
  drops and pickup aliases, random field-item identity selection, the
  field-pickup object lifecycle, CPU item use, and the item cache.
- **Exploration depth:** the panel routines in BTL `D 0x0070F420..0x00712840`
  were read from instruction bytes, and direct `jal` targets into them were
  searched in the resident ELF and BTL. The resident wrapper block
  `0x00375570..0x003762F0` was mapped to its BTL targets. Starting-item tables
  and resolver, accessors, add and decrement paths, drop routines and their
  direct callers, the selected-use gate, delayed-use admission, setup,
  completion and cleanup, all 93 timing records, the emitter, and cache
  capture/restore were read in full. Item external IDs were matched against
  all 182 projectile descriptor rows. The random field-item selector, its
  pools, distribution copies, direct BTL callers and amount helper were read.
  The pickup factory, its three class variants, state dispatcher, admission
  wrappers, collection callbacks and destructors were followed.
- **Confirmed coverage:** panel allocation, owned objects, slot objects,
  slot-count constants, selection advance, wheel geometry, the root draw's
  call order including the support-gauge draw, CPU use of slot relations, and
  cache layout, extent, and neighboring BSS owners. The complete
  character-to-starting-code maps, threshold
  additions, pickup aliases, controller-dependent selected-use fallback,
  count/remove branches, random and bulk field-object drops, delayed
  consumption before emission, item-to-projectile config maps, and cache code
  rewriting. The delayed timing index is active character ID minus one; its
  three lanes supply cursor bounds, animation rate, and exit cooldown. Native
  input, pending-action setup, completion and cleanup gates are distinguished
  from the commit. The random-drop callbacks are `ccProjSIWTrap` and
  `ccSkillTND001`; the root bulk-drop body and its authored-selector conflict
  with the trap override are established. The random field-item selector
  contract, its five pools, the fixed BTL distributions and their nominal
  per-code weights, its four direct BTL call sites, and the separation of
  identity from spawn amount are established. Pickup construction, class
  identities, state dispatch, admission results, collection, retained-index
  readers and teardown are established for the three factory variants.
- **Unresolved or untested:** the meaning and nonzero population of fighter
  `+0x17E`, including writes through unclassified overlapping stores or bulk
  copies; timing-lane bytes `+2/+3`; indirect callers of the timing and root
  bulk-drop bodies; native reachability of that bulk selector despite its
  authored class override; `ccSkillTND001`'s player-facing move identity and
  complete collision-result semantics; wider interruption ordering outside the
  inspected admission/completion/cleanup paths; the CPU item gate's exact draw
  bound and comparison; indirect calls into the panel; writes to the badge
  object's side field outside the panel constructor; indirect use of the
  recovery distributions, the inline selector call's object semantics, and
  wrapper C's branch state; how the internal identifiers recorded for codes
  `02/03` relate to the factory's kind-1 and code-4 branches; pickup
  admission callers beyond the traced states and ordering of the retained
  pickup index against isolated fighter removal.
- **Deliberate exclusions and overlap:** item effects and pickup metadata
  belong to [Battle status effects](battle_items_and_status_effects.md);
  field-item names to [Field-item names](../../localization/field_item_names.md);
  the pickup side-index selector body to
  [Target selection](../combat/target_selection.md#separate-side-index-eligibility-selector);
  snapshot callers and reconstruction order to
  [Battle lifecycle](../session/battle_lifecycle.md#values-crossing-the-reconstruction-boundary);
  Practice snapshot flow to [Practice mode](../modes/practice_mode.md); CPU state
  dispatch to [Battle AI](../session/battle_ai.md); the support gauge to
  [Battle HUD](../session/battle_hud.md#support-gauge); label text and the shared sprite
  record table to
  [item-status presentation](../../localization/ui/battle/item_status.md);
  projectile configuration, motion and limits to
  [Projectiles](projectiles.md); bounded-draw behavior to
  [Resident randomness](../../runtime/randomness.md); and the NUN3 and NUN4
  inventories to [NUN3 and NUN4 item inventories](item_wheels_nun3_nun4.md).
- **Evidence limitations:** findings are static retail evidence, except the
  layer-`17` texture contents, which were observed in one runtime state.
  Opcode searches establish direct calls and literal stores, not indirect calls
  or writes through calculated field pointers; resident byte-mapped aliases
  repeat base-image matches rather than adding callsites. No runtime trace
  confirmed wheel positions, animation timing, delayed-use timing, drop
  outcomes, or random field-item frequencies.

## NA2 ownership

Resident item-manager constructor `0x00373AB0` allocates one `0x80`-byte panel
per side with `0x00117150`, runs base initializer `L 0x0070F460`, then panel
constructor `L 0x0070F740` with the side, and stores the panels at manager
`+0x6C` (side 0) and `+0x70` (side 1). Resident `0x00375A60` returns the panel
for a side.

## NA2 panel layout

| Offset | Content |
| ---: | --- |
| `+0x00,+0x04,+0x08` | Pointers to three separately allocated 8-byte slot objects |
| `+0x0C` | Owned 28-byte animation object |
| `+0x10` | Owned 48-byte object |
| `+0x14` | Owned 24-byte object; receives the selected item code each update |
| `+0x18` | Owned 16-byte list object |
| `+0x1C` | Owned 44-byte support-gauge controller |
| `+0x20` | Side |
| `+0x24` | Selected slot index |
| `+0x28` | Float wheel animation offset |
| `+0x30,+0x34` | Base screen position: X `66.0` for side 0 or `446.0` for side 1, Y `340.0` |
| `+0x40` | Vector added to `+0x30` by `L 0x0070FE40` |
| `+0x44` | Float animated toward `200.0` by `L 0x00711B40`; `L 0x0070FE60` returns it |
| `+0x50` | Wheel origin used by the HUD draw |
| `+0x60..+0x63` | State bytes; `+0x61` is set by activation and `+0x62` by advance |
| `+0x64` | Inline object initialized by the base initializer |

A slot object holds the item code byte at `+0` and signed count at `+4`. A slot
is occupied only when both are nonzero. The seeded count `-1` belongs to kind-6
items, which both decrement paths exclude before checking counts. Stack updates
and subtraction clamp arithmetic to `0..9`; the detailed removal branches are
recorded below. Destructor `L 0x0070F4E0` frees the three slot objects and the
owned objects.

After allocating the slots, the constructor reads the side's fighter from
resident `0x003769C0` and seeds items in three steps. A table of 93 4-byte
`(s16 key, s8 code)` entries at live `0x00898D70` matched against fighter `+0x68`
can place a code in slot 0 with count `-1`. When resident
`0x00373970` reports `1`, the code from resident `0x00373980` is added with
count `3` if fighter `+0x68` is `0x54`, otherwise `1`. Finally, each of 26
4-byte `(s16 threshold, s8 code, s8 count)` entries at live `0x00898D00`
whose threshold does not exceed fighter `s16 +0x17E` is added.

### Starting-item generation

Fighter `+0x68` is the active character ID, as established by
[Character identity in battle](../characters/character_ids.md#active-battle-identity).
Resident `0x00373970` is the signed test `character_id >= 0x39`, encoded by
`slti v0,a0,0x39; xori v0,v0,1`. Thus the character-specific consumable is
seeded only for IDs at least `0x39`. The comparison against `0x54` gives that
character three copies of code `0x6A`; every other nonzero result starts at one.

The kind-6 table's exact `0x174`-byte span is
`D 0x00898D30..0x00898EA3`, `L 0x00898D70..0x00898EE3`,
`F 0x1E4E70..0x1E4FE3`. It covers every ID `0x01..0x5D` once, in ascending
order. These are all its code mappings; hexadecimal IDs remain numeric rather
than assigning unproved item names.

| Seed code | Character IDs |
| ---: | --- |
| `0F` | `01,03,06,0C,0E,10,12,15,16,17,1A,1D,1E,1F,20,21,2A,2F,31,33,39,3C,41,43,47,48,4E,50,51,53,56,58` |
| `10` | `02,05,07,08,09,0B,0F,13,18,25,29,2B,2C,2D,2E,30,37,3A,3D,3E,44,46,4A,4D,57,59,5B,5C,5D` |
| `11` | `0A,19,1B,1C,4C,52,54,55` |
| `12` | `04,32,3B` |
| `13` | `0D,42` |
| `15` | `11,4F` |
| `16` | `14,45` |
| `17` | `22,34` |
| `18` | `23,35` |
| `19` | `24` |
| `1A` | `36` |
| `1B` | `26,38` |
| `1C` | `27` |
| `1D` | `28` |
| `1E` | `40` |
| `1F` | `3F` |
| `20` | `49` |
| `21` | `5A` |
| `22` | `4B` |

The constructor uses the first matching table key and writes its code into
slot 0 with count `-1` through `L 0x007102A0`; a zero or unmatched key does not
make that call. All 19 distinct seeded codes have metadata kind `6`.

Resident `0x00373980(fighter)` returns zero for a null fighter. For an active
ID below `0x39`, it calls `0x00180210(4)` and indexes the five-byte list
`24,25,26,27,28` at resident `0x00604560` (`gp-0x6490`). The bounded RNG
wrapper's inclusive range is owned by
[Resident randomness](../../runtime/randomness.md). For IDs at least `0x39`, it
reads one byte from resident `0x005B042E + id*2`; the adjacent byte is not read
by this resolver. The complete supported-ID mapping is:

| Character IDs, in order | Returned codes, in order |
| --- | --- |
| `39,3A,3B,3C,3D,3E,3F,40` | `51,52,53,54,55,56,57,58` |
| `41,42,43,44,45,46,47,48` | `59,5A,5B,5C,5B,5D,5E,5F` |
| `49,4A,4B,4C,4D,4E,4F,50` | `60,73,61,62,63,64,65,66` |
| `51,52,53,54,55,56,57,58` | `67,68,69,6A,6B,6C,6D,51` |
| `59,5A,5B,5C,5D` | `6E,6F,70,71,72` |

The threshold table's exact 26-row span is
`D 0x00898CC0..0x00898D27`, `L 0x00898D00..0x00898D67`,
`F 0x1E4E00..0x1E4E67`. Each qualifying row adds one, in the group order below;
this is a cumulative threshold list, not one selected level row.

| Code | Thresholds, in stored order |
| ---: | --- |
| `27` | `5,28,50,72,96,112,142,169,186` |
| `09` | `20,44,66,88,102,134,156,178,195` |
| `26` | `40,80,120,160,190` |
| `28` | `66,147,200` |

The consumer reads fighter `s16 +0x17E`; its initializer `0x002151E0` clears
that halfword. Among literal-offset `sh +0x17E` stores in any base register,
resident executable code contains only that initializer and BTL text contains
none; the BTL match at `D 0x008D403C` is stack store `sh zero,0x17E(sp)` in the
imported data block beyond text (`0x006B3F00..0x0088F5BF`). The meaning
and any writes through other addressing forms remain unresolved; this does not
establish that positive thresholds occur in ordinary battles. Addition uses
the ordinary three-slot capacity, so earlier groups can fill the available
slots before later qualifying rows are reached.

The only literal `addiu +0x17E` in the resident ELF and BTL is resident
`0x001206B0` (with its byte-mapped aliases). Its complete function
`0x00120678` passes constant `0x17E` to `0x001207E0`; it does not form
an address from a fighter pointer. This bounds one calculated-address route,
not writes through a register supplied elsewhere. Literal word and unaligned
word stores overlapping `+0x17C..+0x17F` also have candidates in both images;
their full object identities and bulk-copy routes remain unclassified.

The inspected native rebuild does not supply the missing value. Complete
snapshot helpers `0x001ECC00/0x001ECDE0` copy fighter `+0x6C/+0x70`, timers,
and item cache through the item wrappers; they do not retain
fighter `+0x17E`. Rebuild `0x001EF330` constructs fresh fighters, whose
common setup clears that halfword. This rules out population through those
specific snapshot bodies, without proving that no other writer exists.
The rebuild and retained-state contracts remain in
[Awakening](../characters/awakening.md#state-retained-across-the-native-rebuild) and
[Practice](../modes/practice_mode.md#reconstruction-entry-and-retained-setting-owners).

## NA2 slot routines

Routines that walk the slot pointers use a literal loop bound of `3`, and the
selection wrap uses literal `2` as the last index. The HUD draw also caps its
occupied count at `3`.

| D/L/F | Role |
| --- | --- |
| `0070F420/0070F460/5B560` | Base initializer; clears the three pointers |
| `0070F700/0070F740/5B840` | Constructor; allocates three slots and seeds starting items |
| `0070FB90/0070FBD0/5BCD0` | Can-add test: a known item with a same-code slot below 9, or fewer than three occupied slots |
| `0070FC40/0070FC80/5BD80` | Full test: occupied count at least 3 |
| `0070FD00/0070FD40/5BE40` | Find slot by item code |
| `00710000/00710040/5C140` | Add: stack onto a same-code slot, else fill the next empty slot if fewer than three are occupied |
| `00710260/007102A0/5C3A0` | Put a code in slot 0 with count `-1` and set `+0x61 = 3` |
| `00710290/007102D0/5C3D0` | Decrement by item code; reselect when the selected slot empties |
| `00710430/00710470/5C570` | Decrement a selection-relative occupied entry; reselect and bump `+0x28` when the selection empties |
| `00710580/007105C0/5C6C0` | Clear every slot whose item is not special category `6` |
| `00710690/007106D0/5C7D0` | Step `n` occupied slots from `+0x24`, wrapping `0..2` |
| `00710810/00710850/5C950` | Step `n` empty slots from `+0x24`, wrapping `0..2` |
| `007109B0/007109F0/5CAF0` | Build the item cache |
| `00710AC0/00710B00/5CC00` | Restore from the item cache |
| `00710C30/00710C70/5CD70` | Count occupied slots |
| `00710CB0/00710CF0/5CDF0` | Relation of a slot to the selection: `1` selected, `2` one step forward, `3` one step back, `0` otherwise |
| `00710DE0/00710E20/5CF20` | Item category of a slot |
| `00711180/007111C0/5D2C0` | Selected item code for use |
| `00711340/00711380/5D480` | Activation |
| `00711950/00711990/5DA90` | Selection advance |
| `00711E10/00711E50/5DF50` | HUD wheel draw |
| `00712340/00712380/5E480` | Per-frame panel update |

Resident wrappers reach these routines through the manager:
`0x00374190` pickup and `0x00374B30` add; `0x00375840` can-add;
`0x00375570` and `0x003755D0` advance; `0x00375630` selected item;
`0x00375690` activate; `0x003756F0` selected code; `0x003759B0` count;
`0x003759E0` relation; `0x00375A20` category; `0x00375FD0` cache; and
`0x00376050` restore. Resident `0x00375AA0` randomly emits inventory-derived
field objects and consumes their source counts; `0x00375DF0` emits all eligible
entries and then clears non-kind-6 slots, as detailed below.

### Occupied-order access and removal

The code accessor `D/L/F 0070FD50/0070FD90/5BE90` and count accessor
`0070FC70/0070FCB0/5BDB0` take an occupied-entry displacement from the current
selection, not a raw slot index. Both first call occupied-step
`L 0x007106D0(panel, displacement)`. Zero means the first occupied slot at or
after the current selection; positive and negative values walk occupied slots
in the requested direction. An empty panel returns code/count zero. In
contrast, relation `L 0x00710CF0` and category `L 0x00710E20` use raw indexes.

Both decrement-by-code `L 0x007102D0` and decrement-by-displacement
`L 0x00710470(panel, displacement, amount)` first reject kind-6 items through
resident `0x00376480`. For the other kinds, they clear code and count when
`amount >= count` or `amount == -1`; otherwise they subtract and clamp. The
`count == -1` bypass is inside the subtraction branch, after the signed
`amount < count` test. Therefore the seeded kind-6 guard proves retention of
the native infinite entries; the later sentinel check alone is not a general
proof that every possible non-kind-6 count `-1` survives a positive removal.

When removal empties the selected slot, both routines choose occupied-step
zero and store index zero if the panel is entirely empty. Only the displacement
variant adds `1.0` to wheel offset `+0x28`. Clearing all non-kind-6 entries at
`L 0x007105C0` performs no reselection itself. These routines never compact
the three physical slots.

Addition `L 0x00710040` first seeks the same occupied code with count below
`9`. It leaves count `-1` unchanged and otherwise clamps the sum to `0..9`.
An existing occupied same-code slot at `9` rejects the request even when an
empty slot remains. If the code is absent and fewer than three slots are
occupied, it fills empty-step zero relative to the selection; it writes the
incoming count directly, without that arithmetic clamp. It returns `1` for
the stack/new-slot paths and `0` for same-code-at-capacity or full-panel paths.
This routine itself does not validate metadata flag `0x80`; caller-specific
checks and the ordinary pickup route are separate.

### Field-object drops and pickup aliases

Resident `0x00375AA0(manager, side, requests, radius, random_radius)` takes an
additional float spread input in `f12`. For each request it counts occupied
entries and finds the last kind-6 entry in occupied order. With only that entry
remaining it returns. Otherwise its inclusive RNG draw selects an occupied
displacement while skipping that kind-6 displacement. Native initialization
provides one kind-6 entry; the routine remembers one excluded displacement.

The selected code/count use the occupied-order accessors above. The emitted
object count is one, except original code `0x6A` with count at least three,
which yields `floor(count/3)`. Before emission every original code
`0x51..0x73`, including `0x6A`, becomes field code `0x0E`. The shared resident
emitter `0x00374570` receives the fighter's position with a native height
adjustment, the object count, and the spread/radius inputs. After emission the
drop routine removes that object count from the original occupied
displacement. Its later special three-count removal compares the **already
normalized** emitted code to `0x6A`; the preceding `0x51..0x73 -> 0x0E`
branch prevents original `0x6A` from taking it. Thus count three emits one
code-`0E` object and consumes one, leaving two; this is a static branch result,
not an observed match outcome.

Resident `0x00375DF0` walks every occupied displacement without changing the
inventory during the walk. It emits each non-kind-6 code unchanged, using its
full count, except `0x6A`, whose emitted count is one below three and
`floor(count/3)` otherwise. It then calls `L 0x007105C0`, clearing every
non-kind-6 entry even when no per-entry success result was checked. Unlike the
random drop, this path preserves the personal code on the field object.

All aligned direct calls in the two inspected images are these BTL sites:

| Resident target | BTL caller D / live callsite | Established inputs |
| --- | --- | --- |
| `00375AA0` | `00757FA0 / 00758034` | Side from object byte `+0x8A`; four requests; float `90.0`; radius inputs `15,10`; skipped when `s16 +0x292 == 6` |
| `00375AA0` | `008027D0 / 00802864` | Three separate one-request calls; side from object word `+0x500`; float `25.0`; radius inputs `20,10` |
| `00375DF0` | `00730100 / 007302F4` | Root projectile slot `+0x30`, record byte `+0x15 == 4`; side from projectile byte `+0x8A`; radius inputs `30,10`; another integer input chosen as `60` or `120`; final spread input `50` |

The bulk caller is a separate function with its own prologue at
`D/L/F 00730100/00730140/7C240`, after preserved `FUN_0072D1C0`. It switches
on record `u8 +0x15` through a 23-entry table at live `008C4BA0`; case `4`
points to live `00730298` (`D 00730258`). The
aligned `jal 00375DF0` is at `D 007302B4`, live `007302F4`; it is not a
case of the preceding record-`+0x18` contact-response table.

#### Drop callback identities and gates

`D/L/F 00757FA0/00757FE0/A40E0` is `ccProjSIWTrap` vtable `005DF190`
slot `+0x30`: the resident pointer at `005DF1C0` is `00757FE0`. This is the
class's replacement for the root projectile common-action callback. It first
calls live `007580B0`, whose complete body at `D 00758070..007580BC`
disables collision and signals the handle. It then suppresses both the four
random-drop requests and its separate visual-service call when cached
`s16 +0x292 == 6`. Motion body live `00757BB0` supplies that cache from the
same-tag fighter's major `s16 +0x18E` through live `007341A0`, during phase
`+0x268 == 0`. Consequently the gate is a **previously sampled major state**,
not a fresh fighter-state lookup inside the drop callback. The class phase,
counter and side contracts remain in
[Projectile motion](projectile_motion.md#stationary-and-resource-controlled-phase-timing)
and [side identity](projectiles.md#spawn-side-identity-and-lineage).

The inherited root service at live `0072D200` invokes vtable slot `+0x30`
when projectile word `+0x20C == 1`: the bytes at `D 0072D388..0072D3D0`
show the value comparison and `jalr` at `D 0072D3CC` / live `0072D40C`.
Its preceding contact helper live `0072E5D0` has a complete body at
`D 0072E590..0072E6F4`. Unless the initial byte result from
`0072F350(projectile,fighter)` is `1`, it eventually stores `+0x20C = 1`
at `D 0072E6D0`, including a branch that skips downstream contact effect
`0072E740`. Therefore this callback gate alone does not prove successful
application of that effect. It is distinct from the callback's cached
major-state exclusion above; wider contact behavior belongs to
[Projectile collision](projectiles.md#collision-facing-interface).

`D/L/F 008027D0/00802810/14E910` is reached from
`D/L/F 00800FB0/00800FF0/14D0F0`, `ccSkillTND001` vtable `005EBD30`
slot `+0x100` (pointer at `005EBE30`). The vtable's class handle is live
`008CF480`; its name pointer `008BBD08` resolves to `ccSkillTND001` at
`D 008BBCC8`. These are internal class identities, not a recovered
player-facing move name.

The complete callback is `D 00800FB0..00801590`. Signed `+0xFF6/+0xFF8` form an earlier action gate: while
the former is below the latter, it increments; a still-below-limit nonnegative
value exits before the drop countdown. Otherwise nonzero signed
`+0x11F8` decrements once, and only the resulting zero calls live `00802810`
at `D 00801118` / live `00801158`. That routine takes side word `+0x500`
and issues exactly three separate one-request random drops. It does not make
one three-request call.

The countdown is initialized to zero by this class's constructor tail
(`D 00800668`). Its nonzero producer is the phase-4 helper reached from this
same callback at live `00802540`: the complete body spans
`D 00802500..008027C4`. It samples live `0076FF40(self,self+0x200,parameter)`
and, for returned byte `2`, writes countdown `3` at `D 00802718`. Other
returned bytes take different branches; byte `3` sets `+0xFF6 = -2` and
`+0xFF8 = 15` instead. BTL contains only three literal `sh +0x11F8` stores
through this class's base register: constructor clear, update decrement, and
producer `3`. Thus
the delayed drop is distinct from entering phase 4 or merely invoking the
contact helper. The caller's numeric contact-result gate is established;
the helper's full collision semantics and the player-facing move remain open.

The root bulk-drop case calls live `00730600(self,0)` before obtaining the
item manager. It chooses integer spread input `120` when projectile float
`+0x1C0 > 0`, otherwise `60`, and invokes the bulk routine only when the
manager exists. It still makes its separate visual-service call afterward
and reaches the common tail: clear byte `+0x206`; when `s16 +0x270 == 0`,
set common state `+0x7E = 3` and signal the handle. Of all 182 projectile
descriptor rows, only config `6E` (external ID `004B`) has byte
`+0x15 == 4`. Its factory selects `ccProjSIWTrap`, whose slot `+0x30`
replacement is the random-drop callback above. Therefore this one authored
selector does **not** prove that config `6E` invokes the root bulk body
through ordinary virtual dispatch. The root body has 13 direct BTL base-call
sites and none in the resident ELF; none belongs to the SIWTrap callback
family. Unexamined indirect routes or
record mutation cannot be excluded. Wider root/projectile state transitions
are owned by [Projectiles](projectiles.md#hit-and-despawn-evidence).

Pickup resolver `D/L/F 0070C370/0070C3B0/584B0` ignores its object argument.
With a null fighter it returns the incoming code. With a fighter, code `0E`
always resolves through `0x00373980` to that fighter's personal item (or the
five-code random list for IDs below `39`). For IDs at least `39`, other codes
are compared to the adjacent alias byte in the same two-byte personal-item
record; a match also returns that fighter's personal code. All nonzero alias
records are:

| Character IDs | Alias pickup code | Personal inventory code |
| --- | ---: | ---: |
| `39,58` | `23` | `51` |
| `3C` | `26` | `54` |
| `43,45` | `24` | `5B` |
| `53` | `2F` | `69` |
| `54` | `30` | `6A` |

Every other ID `39..5D` has adjacent alias byte zero. The comparisons have a
lower-ID gate but no upper bound; this table describes the supported table
rows, not arbitrary out-of-range fighter IDs. Collection of resolved `6A`
adds three; other inventory codes add one. Downstream metadata and effect
handling remain owned by
[Battle status effects](battle_items_and_status_effects.md#resident-pickup-resolver).

### Random field-item selection

#### Selector contract and pools

Resident `FUN_003AE890` at runtime/file `0x003AE890/0x2AE990` chooses an item
identity. Its input is a sequence of eight-byte `(pool_kind,
threshold_increment)` pairs. It draws one integer from the inclusive range
`0..99`, compares it to the current cumulative threshold with `<=`, and adds
the next row's increment after a miss. After row zero, loading a zero pool kind
terminates the sequence; kind `0` is therefore usable as a pool only in row
zero. If no pool yields a nonzero result, the function returns fallback code
`04`.
Both retail fixed distributions reach cumulative threshold `100`, so that
fallback is unreachable for their `0..99` draw. A shortened distribution would
produce code `04`; metadata identifies it as kind `2`, flags `0x0040`, amount
`0.75` on the positive-resource path.

The five implemented pool kinds are:

| Kind | Item-code lanes | In-pool selection | Resident source |
| ---: | --- | --- | --- |
| `0` | `02,03` | uniform, `1/2` per lane | runtime `0x006047A0,0x006047A4`; file `0x5048A0,0x5048A4` |
| `1` | `06,07,08,09,0A,0B,0C,25,27,2B,0D,0E` | modulo-12 draw; nominal `1/12` per lane | runtime/file `0x005B3C10..0x005B3C3F / 0x4B3D10..0x4B3D3F` |
| `2` | `24,23,27,25,2B,28,26,29,2A,2B,2C,2E,2F,30,31` | modulo-15 draw; nominal `1/15` per lane | runtime/file `0x005B3C40..0x005B3C7B / 0x4B3D40..0x4B3D7B` |
| `3` | `03` | deterministic | runtime/file `0x006047A8/0x5048A8` |
| `4` | `02,02` | deterministic result despite a two-lane draw | runtime `0x006047B0,0x006047B4`; file `0x5048B0,0x5048B4` |

Code `2B` occupies two lanes in pool `2`, doubling its in-pool weight. The
fixed BTL distributions below do not reference pool `4`.

The 22 selector codes with source and official English names are owned by
[Field-item names](../../localization/field_item_names.md#resident-field-item-name-table).
Codes `02` and `03` are outside that resident name table but follow the
positive-resource paths and have BTL internal identifiers `ItemRecoverLife` at
complete-file/live `0x1E4C20/0x00898B20` and `ItemChakraBall` at
`0x1E4C00/0x00898B00`, respectively; the pickup factory classes that use
these names are described in
[Factory, classes and publication](#factory-classes-and-publication). Code `29` is also outside the name
table; its metadata proves kind `3`, flags `0x0180`, and direct effect `0x0A`.
It is identified as **Curse Tag: Chakra Points Seal**; the
[name reference](../../localization/field_item_names.md#code-29-curse-tag-chakra-points-seal)
records the user identification, UN2 naming source, and NUN5 translation limit.

#### Fixed BTL distributions

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
(`51%`) and pool `3` for `51..99` (`49%`). General has 24 unique outcomes:
all 22 codes in the resident name table plus `03` and `29`. Recovery contains
only `02` and `03`; the union is 25 codes. The resulting nominal per-code
weights are:

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
returns an unsigned 32-bit PRNG value modulo `abs(n) + 1`
([MT wrappers](../../runtime/randomness.md#mt-wrappers)). For the top-level
modulo-100 draw, residues `0..95` each have one more source value than
`96..99`. For pool `1`, modulo 12 gives lanes `0..3` one extra source value;
for pool `2`, modulo 15 gives lane `0` one extra source value. Each difference
is one out of `2^32` source values per call. The table therefore records the
exact authored bucket/lane weights, while exact runtime frequencies also depend
on the PRNG state sequence and these negligible modulo biases.

#### BTL call sites and limits

Retail BTL contains exactly four direct JALs to the resident selector:

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
bounded by `10.0`. No direct call selects either recovery table. Indirect or
dynamically scheduled use remains possible, so the recovery distribution is
authored and callable but not proven reachable. BTL contains exactly four
direct JALs to `FUN_003AEAF0`, paired with the four selector calls above; the
resident ELF contains no direct JAL to either function. Only the 24 general
outcomes therefore have established direct-call behavior.

#### Identity and amount boundary

Identity selection and spawn amount are separate. `FUN_003AE890` chooses the
item code; `FUN_003AEAF0` later applies the mode-aware Items amount setting to
reject or multiply spawn requests. The selector has no spawn-frequency input.

The amount helper reads Items through resident `FUN_001F6E40(manager)` at
runtime/file `0x003AEBA0/0x2AECA0`. Its base and probabilistic extra base calls
at `0x003AEC84/0x2AED84` and `0x003AECCC/0x2AEDCC` pass the selected item code.
Its final count-controlled loop instead calls `FUN_00373FB0` at
`0x003AED48/0x2AEE48` with literal code `04`. This is an additional source of
code `04`, independent of the identity selector's fallback, which the retail
distributions cannot reach.
The resident records for `03` and `04` both have kind `2` and flags `0x0040`;
their resource amounts are `5.0` and `0.75`, respectively.

`FUN_00373FB0` rejects a zero item code at `0x00373FC0..0x00373FD4`, but that
return does not stop the amount helper's subsequent code-`04` loop. A zero
identity therefore suppresses only the corresponding base requests, not the
complete amount-helper call.

## Field-pickup object lifecycle

Field pickups are BTL objects that choose a collecting side through the
side-index selector documented in
[Target selection](../combat/target_selection.md#admission-gate-and-selector-body).
This section owns their construction, state dispatch, admission, collection
and teardown. Its addresses are live unless labeled Ghidra (the `D` form).

### Factory, classes and publication

Resident factory `FUN_00374020` allocates `0x80` bytes and calls live
`0x0070A0B0` for its ordinary branch. That constructor's complete body is
Ghidra `0x0070A070..0x0070A0A8`; it installs resident method table
`0x005DDE40` at object `+0x10`, then calls common initializer live
`0x0070A1F0` (Ghidra `0x0070A1B0`). The table's metadata handle is live
`0x008C39A8`; its name pointer `0x00898B50` resolves to the retail string
`ItemData` at Ghidra `0x00898B10`. This establishes the registered name;
it does not recover the original source declaration.

The same factory selects live `0x0070C450` and table `0x005DDE00` for
metadata kind 1. Its handle/name chain resolves to `ItemRecoverLife`.
Both tables install live `0x0070B660` at slot `+0x08`, the admission wrapper
that invokes the selector. The code-4 special factory instead allocates
`0x1A0` bytes, calls live `0x0070C5F0`, and installs table `0x005DDDC0`;
its handle/name chain resolves to `ItemChakraBall`. Its admission slot is a
different body, live `0x0070CA00`, but that complete body at Ghidra
`0x0070C9C0..0x0070CA30` calls the same wrapper live `0x0070B720` when
handle result `+0x08` is nonzero and flags `+0x04 & 0x110` are present.
Wrapper result 2 sets object `+0x80 = 1` and returns zero; other results
return 1. It does not perform the ordinary wrapper's state-5 transition,
and unlike that wrapper it assumes a nonnull collision handle. These are
three concrete factory/admission variants, not an unrestricted class census.

Its state-2 method live `0x0070C830`, Ghidra `0x0070C7F0..0x0070C8F4`,
invokes this slot only while `+0x80 != 1` and its preceding local-motion
result permits continuation. Once admission sets `+0x80 = 1`, subsequent
state-2 calls skip selection and eventually return zero when the local
eight-entry decay helper live `0x0070CA80` reports completion. The admission
slot's zero therefore does not immediately free the object in this caller;
the retained index can survive the class's local completion interval.
Item identity and effect semantics belong to
[Battle items and status effects](battle_items_and_status_effects.md#immediate-pickupitem-effect-path-0x000x13).

The common initializer copies the supplied position/velocity vectors into
`+0x20/+0x30`, stores item byte `+0x61`, clears secondary code `+0x62`,
initializes side index `+0x5C = -1`, and enters state byte `+0x1C = 1`.
The `+0x20` field here is a vector, not the paired-fighter pointer at the
same offset in a fighter. It creates a collision handle at `+0x14` and an
owned auxiliary object at `+0x18`. Resident `FUN_00373FB0` subsequently
assigns an object serial from manager `+0x84`, links the previous head at
object `+0x74`, and publishes the new object in manager `+0x00`. Publication
does not retain a selected fighter: selection starts from the initialized
index `-1` later.

### State dispatcher and admission wrappers

The main state dispatcher has true entry live `0x0070A410`, Ghidra
`0x0070A3D0`. Its nine-entry jump table is live `0x008C3980`, read at
Ghidra `0x008C3940`. States 1/2 invoke table slots `+0x0C/+0x10`;
states 6/7 invoke `+0x14/+0x18`; state 5 invokes `+0x1C`. For the two
ordinary tables, state 2 reaches live `0x0070A6F0`, whose first action is
virtual slot `+0x08` and therefore admission wrapper live `0x0070B660`.

That wrapper requires nonnull object `+0x14`, nonzero collision-handle
word `+0x08`, and handle flags `+0x04 & 0x110`. Only then does it pass
those flags to live `0x0070B720`, the full selection/continuation wrapper.
Its byte result 2 enters object state 5 and returns 4; result 3 enters
state 5 and returns 2. Both clear the state counter `+0x64`. Other results
return 1 without that transition; a null handle returns 0. These values
are object lifecycle decisions, not fighter pointers.

### Selector continuation and terminal results

After choosing a side, the selector resolves item byte `+0x61` against the
chosen fighter through live `0x0070C3B0`, storing the result at `+0x62`.
It then obtains the item manager and, for a resolved code with metadata
flag `0x80`, checks the side inventory through
`FUN_003751A0(manager,side,code)`. A zero inventory result takes the
rejection-motion branch: unregister the collision handle through
`FUN_001DDA50`, set countdown `+0x6C = 10`, clear the side index at live
`0x0070BB2C` (store instruction; the preceding `-1` load is `0x0070BB28`),
and return 1. Inventory contents and code aliases are described in
[Field-object drops and pickup aliases](#field-object-drops-and-pickup-aliases).

Outside that branch, the selector's terminal return depends on the
constructor-supplied byte `+0x60`: value 1 returns 3 for selected side 0
and 4 for side 1; value 2 returns 3 for side 1 and 4 for side 0; other
values return zero. The no-eligible-side path also returns zero, but with
`+0x5C = -1`. These terminal values are distinct from the resolved fighter
pointer.

### Collection, retained-index readers and teardown

After the full wrapper's fighter recheck passes, it unregisters the
collision handle through `FUN_001DDA50` and clears object scalar `+0x50`.
Selector result 4 additionally invokes live `0x0070BE50`. It then calls
method slot `+0x34` with float magnitude `1.0`; resident tables select live
`0x0070BC20` for `ItemData`/`ItemChakraBall` and `0x0070C550` for
`ItemRecoverLife`. Those callbacks freshly resolve the fighter from `+0x5C`;
the ordinary callback also requires the corresponding side-control alias to
exist. Item effects belong to
[the pickup callback contract](battle_items_and_status_effects.md#btl-pickup-object-callback).
Finally, metadata flag `0x80` on active byte `+0x61` returns 3, otherwise 2,
to the admission wrapper. No fighter pointer is stored in this continuation.

The index survives the successful state-5 transition. Later table slot
`+0x24`, live `0x0070B1E0` (complete Ghidra body
`0x0070B1A0..0x0070B37C`), resolves it afresh and requires nonnull fighter
plus `FUN_00216720(fighter)`. This is a different predicate from initial
admission. State 8's live `0x0070A980` supplies `+0x5C` and item code to
`FUN_00376110`, which selects manager side inventory and asks it for a point.
These are retained-index consumers, rather than retained-fighter aliases.
State 3's live `0x0070AB40` can invoke admission slot `+0x08` again, so
the two ordinary tables have another concrete selector invocation beyond
state 2. No claim about every indirect caller follows from these paths.

The dispatcher's common tail calls live `0x0070B5B0`, Ghidra
`0x0070B570..0x0070B5AC`. A positive `+0x6C` decrements once, and its
transition to zero calls `FUN_001DD9D0` to register the retained collision
handle again. Together with the selector's index reset, this gives a
concrete rejection/retry interval; it is not fighter ownership. The resolver
`FUN_003769C0` returns the manager's primary side-0/side-1 aliases for
indexes 0/1 and null for other values. Its body assumes the manager global
exists; the caller's nonnull fighter recheck does not establish arbitrary
manager or isolated-removal safety.

Resident item-list pass `FUN_00374B30` reads `+0x5C` when dispatch result
2 adds the active code to one side's inventory. Result zero instead unlinks
the object through list field `+0x74`, then invokes destructor slot
`+0x3C`. For `ItemData`, that slot is live `0x0070A0F0`; its full
Ghidra body `0x0070A0B0..0x0070A114` calls common cleanup live
`0x0070A370`, then frees the object for positive destructor mode. Cleanup
destroys and nulls owned `+0x14/+0x18`; it does not resolve a fighter,
release a fighter allocation, or clear `+0x5C` before freeing. The recovery
destructor at live `0x0070C4A0` performs the same handle/auxiliary cleanup.
Coordinator-transition cleanup in `FUN_003747C0` also destroys the pickup
list and clears its head. These paths establish the index owner's lifetime,
not unrestricted ordering against isolated fighter removal or every alias.

## NA2 selection

Fighter input gate `FUN_002366F0` calls resident `0x003755D0`, which reaches
advance `L 0x00711990`. Advance does nothing while panel state `+0x60` is `1`
or when fewer than two slots are occupied. Otherwise it sets `+0x62`, adds
`1.0` to `+0x28`, steps one occupied slot forward, stores the new index at
`+0x24`, and plays sound `42`. Selection only moves forward and skips empty
slots; slots are not compacted.

The BTL action translator at `D 0x006F0500..0x006F056C` maps native Use Item
(action bit `0x08`) to fighter input `0x01000000` and Item Select (`0x10`) to
`0x02000000`. Linked Attack (`0x20`) first sets `0x04000000`, then replaces it
with `0x20000000`, so player input never delivers `0x04000000`. The fighter
input gate still tests `0x04000000` after `0x02000000` and would call resident
`0x00375570`, whose only caller is that gate. `0x00375570` also reaches the
forward advance through wrapper `L 0x00711970`. No other producer of
`0x04000000` was found in BTL.

### Selected-use eligibility and fallback

Native input function `0x002366F0` has a state gate before these code checks.
Major `7` returns before both selection and use, so it does not start another
item action through this input path. Selection is admitted in major-0
substates `0,3,4,5,6,7`, major-1 substates `0E..14`, majors `2,3,4,5`,
major-6 substates `5D..60`, and major `8` with `+0xB00 == 0` and
`s16 +0xB10 == 0`. Use initially requires major-0 substate `0/5`, major-1
substate `0E..14`, major `2/3/4`, or that admitted major `8`. The other
admitted states try helper `0x00238270` and require result `2` to enable use;
its complete inspected body returns only `0/1`. The caller's literal
comparison is confirmed at `0x00236948..0x0023695C`. Thus that branch does
not establish an additional native use state. Delayed dispatch imposes the
separate admission predicate below; selection admission is not sufficient
for delayed use.

Selected-code resolver `D/L/F 00711180/007111C0/5D2C0` reads the physical
selected slot's code first. Metadata flag `0x100` imposes an additional gate:
resident `0x003764B0` returns the inverse of that flag, and when it is present,
the resolver compares **side 0's** fighter `s16 +0x9F6` and `s16 +0x324`,
regardless of panel side. Only equality proceeds to the item-specific gate.
The two attempted `-1` checks compare an unsigned masked byte against signed
`-1`; instruction bytes do not establish an effective `0xFF` sentinel rejection.

Item gate `D/L/F 00710E70/00710EB0/5CFB0` first requires the projectile-manager
pointer at resident `gp-0x31D0`. It then uses per-side projectile existence
`L 0x00735910` and count `L 0x00735A30` to reject the following codes. Both
helpers walk the manager's actual list, matching signed config index `+0x78`
and inverse object-side byte `+0x8A`; pending-removal objects are not filtered
by state. Their manager lifecycle and count interpretation are owned by
[Projectile limits](projectiles.md#limits-and-pooling).

| Item code | Item-specific rejection condition |
| ---: | --- |
| `28` | Config `0D` exists for the panel side |
| `27` | Config `12` exists, or config `13` count is at least `11` |
| `2E` | Either config `2E` or `2F` exists |
| `2F` | Config `44` count is at least `2` |
| `5C` | Config `34` count is positive |
| `6E` | Config `9C` exists, or config `9D` count is at least `6` |
| `6B` | Native side predicate `L 00886750` is nonzero and helper `L 00885750(0x19, selected_character_id)` returns byte `0x35`; or config `B5` count is positive |
| `69` | Config `9B` count is positive |
| `65` | Config `99` count is at least `3` |

The helper returns one for all other byte codes when its manager pointer
exists. It does not test slot occupancy or counts; those are separate caller
conditions. The helper identities in the extra `6B` branch remain numeric
here rather than assigning a gameplay interpretation without tracing them.

When both gates pass, the selected-code resolver returns the original code.
Otherwise it reads the panel side's fighter controller nibble (`+0x60` bits
`5..8`). The relationship to pad suppression and AI dispatch is documented in
[Battle AI](../session/battle_ai.md). A zero nibble plays sound `44` and returns zero.
A nonzero nibble reads the relation of physical slot zero to the current
selection once, then performs at most two selection advances until the selected
code is kind `6`. Relation `2` selects advance `L 00711990`; other relations
select wrapper `L 00711970`, which calls that same forward advance. The
resolver returns the resulting selected code even if no kind-6 entry was
reached or the advance was blocked. It does not rerun item eligibility after
this fallback. Each successful advance retains the ordinary selection sound
and wheel-offset changes.

### Dispatch and consumption boundary

Resident `0x00236C70(fighter, code)` requires the item manager. The delayed-use
predicate `0x00376400` selects metadata kind `3` or `6` with flag `0x10` clear.
Those codes first require `fighter s16 +0xB72 == 0` and the action-facing
predicate `0x002375C0`, then pending-use setup `0x002378F0` stores code
`s16 +0xB70` and enters major action `7`, substate `0x63`, `0x64`, or `0x65`.
It does not decrement the inventory there. Kind-4 flag-`0x10` codes use the
same readiness check but call panel activation immediately. Other immediate
metadata effects and their six-code fallback are owned by
[Battle status effects](battle_items_and_status_effects.md#btl-pickup-object-callback).

After either accepted dispatch path, the resident dispatcher calls live
`0x00737D70(fighter,code)`, before any delayed commit is guaranteed. Complete
bytes `D 00737D30..00737DE8` show that a nonzero code samples
`0x00180210(99)`; a result below `50` samples `0x00180210(2)` and chooses
one of event indices `3,4,5` from words at `D 008A14E0..008A14E8`
(`L 008A1520..008A1528`). It passes the chosen index to
`0x002040D0(fighter,index,-1,1)`. This is a fighter voice-event request;
its downstream suppression and audio command contract belong to
[Battle audio](../session/battle_audio.md#fighter-voice-event-selection). It neither
decrements the inventory nor proves that emission or audible playback occurred.

#### Admission and pending-action setup

Readiness wrapper `0x002378A0` requires signed cooldown `+0xB72 == 0` and
`0x002375C0`. The latter admits major `0` only in substates `0,3,4,5`, major
`1` only in `0E..13`, and majors `2,3,4` without an additional substate gate.
Other majors are rejected except `8`. In major-1 substates `12/13` it also
approaches horizontal/vertical motion scalars `+0x994/+0x998` toward zero;
the admission predicate is not purely a read.

For major `8`, the predicate requires current record `+0xA4C`, rejects record
flag `0x200`, rejects flag `0x100` when pending continuation `+0xA3E != -1`,
and rejects nonzero `+0xB00` or `s16 +0xB10`. With record flags `0xC0000`,
it returns whether primary cursor `+0x1C4 < 16`. Otherwise nonzero byte
`+0xB97` admits immediately; failing that, helper `0x00239250` must return
a value in inclusive `0.5..0.95` when supplied the current animation's final
frame. The action-record and cursor contracts belong to
[Combat action execution](../combat/combat_action_execution.md#action-entry-and-state-ownership).

Setup `0x002378F0` saves the supplied code to `s16 +0xB70`, copies `+0xB74`
to `+0xB76`, clears `+0xB74`, and increments `+0xB78` after state entry; that
counter's awakening use belongs to
[Awakening](../characters/awakening.md#proven-hp-and-counter-prerequisites). If
the old major is `8`, it clears the attack banks through `0x0023BDC0`, clears
their inline work fields, and resets a pending continuation to `-1`. Ground
bit `u8 +0x63 & 0x80` chooses substate `63` when set, `64` when clear. If
`u8 +0x9B8 & 3 >= 2`, grounded entry instead uses `65` after clearing
`+0x994/+0x998`; airborne entry calls `0x0022E5D0(fighter,0)` and uses `64`.
The meaning of the two-bit `+0x9B8` value remains outside this trace.

#### Timing-record producer and exit cooldown

Resident major-state updater `0x00249640` dispatches major `7` to
`0x00237D00`. Its instructions `lw v0,0x68(s1); addiu s0,v0,-1` at
`0x00237D28/2C`, followed by `move a2,s0; jal 0x00737E30` at
`0x00237E30/34`, prove that the timing index is the **active character ID
minus one**. The pending code comes from `s16 +0xB70`. This resident call and
its two byte-mapped aliases are the only direct JALs to the helper in the
resident ELF and BTL; indirect calls are not excluded.

The 93 supported-character records occupy
`D 0x008A14F0..0x008A1DA7`, `L 0x008A1530..0x008A1DE7`,
`F 0x1ED630..0x1EDEE7`. Each record contains three 8-byte lanes at offsets
`0,8,16` for substates `63,64,65`. The updater does not range-check its ID
before indexing. Lane `s8 +0/+1` bounds the kind-6 cursor emissions, and
`u16 +6` supplies both animation rate and the non-kind-6 secondary rate
described below.

The rate selector is a separate body, `D/L/F 00738300/00738340/84440`.
Bytes through `D 007383A0` prove that it chooses the same lane and returns
`lhu +6`. Resident animation update `0x0024D1C0` calls it at `0x0024D248`
only for major `7`, using substate `s16 +0x190` and active ID minus one;
other majors use fighter `u16 +0xB90`. The selected rate is multiplied by
fighter float `+0x1AC`, converted to an integer, and written as a halfword
to primary animation player `(fighter.+0xE70)+0x94` at `0x0024D2DC/E0`.
Nonzero fighter `+0xB88` then overrides that halfword with zero before
evaluation. The player consumes this step in units of `1/256` frame, as
owned by [Animation runtime](../../runtime/animation_runtime.md#advance-and-end-behavior).
Live `00738340` has no other direct JAL in the resident ELF or BTL besides
this resident call and its two aliases.

Major-7 old-state cleanup `0x00217BD0` calls `0x002375A0`, which calls
`0x00237FA0`. That helper obtains the current substate and the same
`character_id - 1` index for live BTL `0x007383F0`, then stores its result at
cooldown `s16 +0xB72`. Thus cooldown assignment belongs to leaving major `7`,
including interruption through the common state setter. This helper does not
activate or decrement an inventory slot. BTL function
`D 007383B0..00738450` selects the same three lanes and returns their signed
halfword `+4`. For every supported ID, lane
`64` supplies cooldown `8` and lane `65` supplies `24`; lane `63` supplies
`16` except IDs `05/0A`, which supply `12`. The default selector retains a
null lane pointer before `lh +4`; the established major-7 paths use
substate `63..65`.

Resident `0x0024C440` decrements nonzero `+0xB72` by one in its generic
node-bit-1 update branch. It does so before the later `+0x20C` pause gate,
without multiplying the decrement by fighter delta. Signed negative values
are also decremented rather than clamped; the supported authored lane values
above are positive. Literal `sh +0xB72` stores in any base register occur
at five resident sites and one BTL site, plus resident aliases. Besides the
generic reset, lane assignment and decrement, resident `0x00304070` can
overwrite it with `30` on its major-7/substate-64 animation-end exit, and
`0x002C8690` clears it in a character-specific helper. BTL
`D 008563DC` writes an unrelated skill-object `+0xB72 = 8`, amid that
object's own `+0xB60..+0xB8F` work initialization; it is not a proven fighter
cooldown writer.

#### Authored lanes and action completion

The three native descriptors for substates `63,64,65` at
`D 0089B188..0089B19F` name `ACT_ITM_0/1/2`. Their first rows at
`D 0089A7F0/0089A800/0089A810` select animation slots `42/43/1B`
respectively, with progression conditions `-0x10/-0x11/-0x10` (animation
end / grounded / animation end), start zero and rate `0x100`; each is
followed by a terminal row. These conditions use the shared phase machinery
owned by [Combat action execution](../combat/combat_action_execution.md#shared-phase-progression).

Representative full-table variants below show that the timing lanes differ
by character even when the starting item is the same. Cursor bounds and
cooldowns are decimal; IDs and rate halfwords are hexadecimal. Each cell is
`[start,end), cooldown, rate`; bytes `+2/+3` are omitted here because
the inspected commit, rate and cooldown consumers do not load them.

| Character ID | Lane `63` | Lane `64` | Lane `65` |
| --- | --- | --- | --- |
| `01` | `[7,11),16,01A0` | `[5,9),8,0100` | `[5,9),24,0100` |
| `02` | `[7,11),16,0180` | `[5,9),8,0100` | `[5,9),24,0100` |
| `05` | `[10,14),12,0100` | `[5,9),8,0100` | `[5,9),24,0100` |
| `0A` | `[9,13),12,0140` | `[4,8),8,0100` | `[7,11),24,0100` |
| `22` | `[5,9),16,0170` | `[4,9),8,0100` | `[8,12),24,0100` |
| `23` | `[7,11),16,01A0` | `[5,9),8,0100` | `[8,12),24,0100` |
| `40` | `[5,11),16,01A0` | `[7,13),8,0100` | `[7,13),24,0100` |
| `5B` | `[4,7),16,01A0` | `[4,8),8,0100` | `[5,9),24,0100` |

After shared phase progression, resident `0x00248580` dispatches major `7`
to `0x00237A60(fighter,terminal)`. For substate `63`, terminal exits to
major/substate `(0,0)` when grounded, `(3,1E)` when airborne with matching
`+0x98C/+0x990`, or `(3,25)` otherwise. Substate `64` exits to `(4,26)`
on grounding even without terminal; terminal while airborne chooses `(3,21)`
or `(3,25)` using that same equality. Substate `65` terminal first enters
`(1,13)` and advances its phase when zero. Its subsequent fresh ground-bit
check, even without terminal, can clear the airborne motion setup, set the
ground bit, approach `+0x994` toward `10`, set `+0x998` to float bits
`3851B717`, and enter `(7,63)`. The helper performs these statements in
order, so they are not three mutually exclusive completion outcomes.

The late physical helper `0x00304070` supplies another substate-64 exit when
fighter byte `+0x62` bit `0` is clear, its contact query is null, and
`+0xB88` is nonzero, then explicitly assigns cooldown `30`. Common cleanup
applies on these state changes too. Neither completion helper calls item
activation: interruption or exit before a
successful commit has no decrement in the traced cleanup chain, whereas an
already reached activation is not refunded by that chain. This is a static
control-flow boundary, not a timing or input-reachability observation.

The delayed commit helper `D/L/F 00737DF0/00737E30/83F30` selects an
eight-byte timing lane for substate `0x63/0x64/0x65`, within a 24-byte record at
live `0x008A1530 + index*0x18`. For kind-6 codes it checks authored primary
cursor positions with resident `0x002118A0`; fighter float `+0x15C` influences
emission count and spacing. Other delayed codes require primary cursor-zero
check to return zero and a secondary-cursor check to return nonzero; that
secondary target is half the action frame length divided by lane `u16 +6 / 256`.
Only a successful timing check calls activation and then emitter
`L 0x007378C0`. The direct activation callsite is `D/L 0073828C/007382CC`.
The helper returns one for kind-6 or code `2B`, zero for other codes, independent
of whether its timing check committed that invocation. This is a cursor gate,
not evidence that a projectile hit is required before ordinary delayed use.

Panel activation `L 0x00711380(panel, supplied_code)` first requires both the
manager and side's fighter and at least one occupied slot. A zero argument
resolves selected use; a nonzero argument is used directly. Code `27` has a
separate eligibility rejection before the common tail; codes `0x51..0x73` call the
linked status dispatcher. The common tail then reads the **currently selected
slot**, takes its code for `L 0x007102D0(panel, selected_code, 1)`, and sets
`+0x61 = 1`. Thus the supplied dispatch code and decremented slot code are
distinct operands, although ordinary selection supplies the same code. The
tail has no per-effect success check. Kind-6 items remain through the decrement
guard; positive counts remove one after activation reaches this tail.

The activation tail also calls `L 0x00713680` twice for finite counts and once
for count `-1`. This auxiliary routine records distinct used codes for fighters
whose controller nibble is zero: it scans 116 bytes, ignores an existing code,
stores a new code at the first zero byte, and increments its word `+0x74` only
on new insertion. Repeated calls therefore do not double-count one code. When
that word reaches three it calls resident `0x001FD850(side+1, 42, 1)`.
The player's inventory count and this distinct-code bookkeeping are separate.

### Item codes and projectile config indexes

Delayed emitter `D/L/F 00737880/007378C0/839C0` passes its incoming item code
unchanged as an external projectile ID. It searches the 182 `0x68`-byte records
at live `0x0089C910` for the first matching signed leading halfword, then calls
spawn `L 0x00736080` with that row index, fighter `+0x60` bit `0`, and vector
arguments. Spread zero uses the direct target vector; nonzero spread perturbs
the vector before the same lookup/spawn. The post-loop sound lookup uses the
same code and reads row `s16 +0x30`. The item code, external ID, config index,
and factory selector are separate values; constructor classes and motion
remain owned by [Projectile configuration](projectiles.md#configuration-and-factory).

These are the complete config mappings for all 19 seeded kind-6 codes,
the generic inventory codes in `23..31`, and all 17 personal kind-3 codes.
All values in these tables are hexadecimal and paired left to right.

| Seeded kind-6 codes | Projectile config indexes |
| --- | --- |
| `0F,10,11,12,13,15,16` | `00,01,02,03,0E,0F,11` |
| `17,18,19,1A,1B,1C,1D` | `36,37,38,39,3C,3A,3B` |
| `1E,1F,20,21,22` | `8A,91,7C,AE,92` |

| Generic inventory codes | Projectile config indexes |
| --- | --- |
| `23,24,25,26,27,28,29` | `04,09,0B,0C,12,0D,1C` |
| `2A,2B,2C,2E,2F,30,31` | `1D,0A,2B,2F,30,35,85` |

Code `27` reaches config `12` through panel activation's direct external-ID
wrapper `L 0x007362E0`, rather than the delayed emitter. The missing `2D` in
this generic inventory table has metadata flag `0x80` clear; its external
projectile mapping is config `2E`, which does not by itself prove collection
into ordinary inventory.

| Personal kind-3 codes | Projectile config indexes |
| --- | --- |
| `51,54,57,58,5A,5B,5C,5E` | `7D,A1,88,8C,83,7E,84,A2` |
| `61,62,65,69,6A,6B,6C,6E,6F` | `93,90,98,9A,80,B5,AD,9C,B0` |

All other `0x51..0x73` codes are kind `4` and use the immediate status path linked
above. `5B` participates in both the delayed projectile path and a status row.
Metadata kind-6 code `14` is not produced by the character seed table and has
no matching leading external ID in the complete projectile table. The emitter
passes lookup failure `-1` onward; it does not cancel the preceding activation
or refund a consumed count when the lookup or later construction fails. This
records the failure boundary without asserting native reachability of code `14`.

## NA2 HUD wheel

Draw `L 0x00711E50` counts occupied slots `n` (at most 3). It draws the panel
background at `+0x50`, then one empty-slot frame for each wheel position `k`
from `n` to `2`, then each occupied item at positions `k = -1..n-1` shifted by
the animation offset `+0x28`. For position `k`:

```text
x = -45 * sin(0.2 * pi * k)     (negated for side 1)
y = -20 * k
first factor  = 1 - 0.10 * |k|
second factor = 1 - 0.15 * |k| for k >= 0, else 1 - |k|
```

The root draw `L 0x007127B0` first stores `+0x30 + +0x40` at the wheel
origin `+0x50`. It draws the item-select button badge before the wheel, and
after the wheel it calls the `+0x18` and `+0x14` objects and the support-gauge
draw for `+0x1C` (`L 0x0071D270`, which updates the controller and draws the
support block while its visibility byte `+0x0A` is nonzero). The support
gauge's sampling and drawing belong to
[Battle HUD](../session/battle_hud.md#child-update-and-draw-boundaries). Its object at
panel `+0x10` holds the badge offset from the wheel
(`-38.0, 16.0`, with `x` negated for side 1) at `+0x10`, its scale at `+0x20`,
and the sprite at `+0x24`. Resident `0x00376F10(side, action)` reads the side's
binding for the action and maps it through six `(button mask, sprite)` pairs at
`0x005B00B0`: `R1 0x76`, `R2 0x77`, `L1 0x74`, `L2 0x75`, `L1+R1 0x74`,
`L2+R2 0x75`. The badge frame is sprite `0x7B`, and the button sprite is dimmed
to `0.8` when fewer than two slots are occupied. The draw passes the badge
object's `+0x00` as the side, but the panel constructor clears it to `0` for
both panels, so both show P1's binding. Byte `+0x28`, set to `1` by the
constructor, selects action `4` (Item Select); zero would select action `5`.
An action whose binding is not in the six-pair table maps to sprite `-1`, and
the frame is still drawn.

Battle sprite IDs index the resident 12-byte record table at `0x005B0A60`,
also used by the item-status renderers in
[Battle item-status presentation](../../localization/ui/battle/item_status.md#substitution-doll-pickup-atlas-binding).
Each record holds a mode byte, flag byte, then `u`, `v`, width, and height as
halfwords, then the sprite layer. `0x00377260` copies a record into the layer's
sprite; flag bit `0` sets sprite flag `0x20` (horizontal mirror) and bit `1`
sets `0x40`. The badge buttons `0x74..0x77` are 32x16 cells at `(190, 222)`,
`(190, 239)`, `(223, 222)`, and `(223, 239)` on layer `17`, and the frame
`0x7B` is a 36x24 cell on layer `16`. Layer `17`'s other cells are 30x30 item
icons.

Position `0` is the selection, and later slots in selection order take
positions `1..n-1`. At rest the second factor is `0` at `k = -1`, so the
previous item is visible only while the animation offset is nonzero. Resting
positions are therefore `0..2`, and `x` is `0` again at `k = 5`. The selected
slot's count is drawn beside the wheel, with a separate element for count
`-1`. The per-frame update clamps `+0x28` to `-1..1` and moves it toward zero.
In `D 0x00712360..0x007123BC`, it reads and clamps the offset, then calls
`L 0x006C12A0` with target `0.0`, step `0.2` (float bits `0x3E4CCCCD`), and
the address of `+0x28`. The occupied-count loop starts afterward at
`D 0x007123C0`. Thus repeated advance calls can accumulate an offset beyond
one before this update, but the clamp discards that excess before drawing.

The same complete update clears event bytes `+0x61/+0x62/+0x63` at its tail
(`D 0x0071273C..0x00712744`). They are per-update signals rather than retained
consumption state. It updates the `+0x18` list, supplies occupied-step-zero code
(or zero for an empty panel) to the `+0x14` object, and updates the support-gauge
controller through the pulse updater described in
[Battle HUD](../session/battle_hud.md#child-update-and-draw-boundaries). The item-select badge scale moves down by `0.1` when `+0x62` is
set and up by `0.1` otherwise, clamped to `0.8..1.0`.

Item draw `D/L 00711BF0/00711C30` forwards its scale and opacity floats to
resident sprite draw `0x00377720`. The separate auxiliary draw
`D/L 00712BE0/00712C20` handles codes `0x51..0x73` through a model object;
its arguments contain scale and position but no opacity value.

## NA2 CPU item use

Battle AI state `25` handler `D/L/F 006F4ED0/006F4F10/41010` works in raw slot
indexes. With no target stored, it tries each index below the occupied count,
keeps the first whose category is `3`, `4`, or `6` and that passes a random
gate with threshold `30`, and stores it at AI work record `+0x58`. The gate's
draw bound and comparison are not recorded here, so it is not established as
an exact 30% probability; the bounded draw's modulo behavior is described in
[Resident randomness](../../runtime/randomness.md#mt-wrappers) and the AI's
`0..100` threshold convention in
[Battle AI](../session/battle_ai.md#direct-profile-parameter-consumers). The loop bound is an occupied count, but the indexes
are raw slot positions. With a target stored, it asks relation
`L 0x00710CF0`: relation `1` can set input mask `0x01000000` (use) in record
`+0x10`, relations `2` and `3` set `0x02000000` (item select), and relation `0`
resets the state. The relation routine recognizes only one step in each
direction.

## Item cache

The BTL BSS cache at `0x008D6A60` holds two sides of three 2-byte
`(code, count)` entries, `6` bytes per side. BTL static construction builds it
as two six-byte objects with element constructor `0x007139F0`
([Overlay ABI](../../runtime/overlay_abi.md#constructor-interval)). Build and
restore use the literal side stride `6` and loop bound `3`. Live BTL
`0x0070F1E0` zeroes all three records of both sides. BTL constructor 3
(Ghidra `0x008D5DE0..0x008D5E1F`) passes `0x008D6A60`, element size `6` and
count `2` to `0x00119290`, so the cache occupies `0x008D6A60..0x008D6A6B`.
The following bytes belong to other owners:

| Live range | Owner and evidence |
| --- | --- |
| `0x008D6A6C..0x008D6A6F` | No instruction or pointer reference in the resident executable or BTL (byte searches for the `0x6A6C` immediate with base `0x008D` and for `0x008D6Axx` pointer words). **Inference:** alignment padding before the next object. |
| `0x008D6A70..0x008D6A7B` | Three-word cleanup node. BTL constructor 4 (Ghidra `0x008D5E84..0x008D5E9C`) passes it as `a2` to resident `FUN_00119A60`, which stores the previous head, callback `0x0071A7A0` and object `0x008D6A80` at node `+0/+4/+8`; see [Overlay ABI](../../runtime/overlay_abi.md#replacement-and-exit). |
| `0x008D6A7C..0x008D6A7F` | No instruction or pointer reference found by the same searches. **Inference:** alignment padding before the bank. |
| `0x008D6A80..0x008D6AEF` | Two-side source bank, cleared by the same constructor; see [Battle statistics](../session/battle_statistics.md#btl-score-tier-and-point-accumulator-handoff). |

Item state is mask bit `0x20` of resident snapshot helpers `FUN_001ECC00`
(capture) and `FUN_001ECDE0` (restore). Capture calls `0x00375FD0` for the
selected side; when given a single side (`1` or `2`) it first calls
`0x0070F1E0`, so both sides' stale records are cleared before the requested
side is captured. Restore calls `0x00376050`. Callers, masks and the
reconstruction order belong to
[Battle lifecycle](../session/battle_lifecycle.md#values-crossing-the-reconstruction-boundary);
the Practice controller's use belongs to
[Practice mode](../modes/practice_mode.md#discrete-practice-controller-reset).

Capture `L 0x007109F0(panel, buffer)` accepts an explicit buffer; zero selects
the BSS record for the panel side. It clears all three output pairs, walks
physical slots in index order, and omits kind-6 entries. It copies every other
slot, including empty pairs, into the next output position; only kind-6 omission
changes the output index. Counts are narrowed to one byte. This cache records
codes/counts, not the selected index or wheel offset.

Restore `L 0x00710B00(panel, buffer)` likewise accepts an explicit buffer and
uses the side's BSS record when it is zero. It resets selected index to zero,
clears only non-kind-6 slots, and skips cached pairs with zero code or count.
For each nonempty cached code `0x51..0x73`, it calls `0x00373980` on the **current**
fighter and writes a differing result back into the cache itself before adding
the pair. Counts are read as signed bytes. Restoration therefore can normalize
an old personal item to the current fighter's code, and changes the stored
cache as well as the live inventory. For an ID below `39`, each such pair
independently uses the five-code random resolver. Kind-6 live slots survive and
are never restored from the cache; add failures are not checked here.

Resident capture/restore wrappers `00375FD0/00376050` interpret mask bit `1`
as side 0 and bit `2` as side 1, checking each panel pointer before dispatch.
