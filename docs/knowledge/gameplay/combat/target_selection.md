# Target selection and locking

This document investigates target selection and locking in retail NA2
(`SLPS-25837`).

## Research coverage

- **Assigned scope:** Player/skill/support target selection and retention, side/eligibility filters, retargeting, lock release and lifetime safety.
- **Exploration depth:** Inspection covers paired geometry, all 11 resident caller functions reported by direct xrefs and four BTL callsites; direct-offset source stores and their containing bodies; collision consumption/arbitration; skill participant admission and release; all 14 final support vtables, nine distinct native attack bodies, both emitters and distinct auxiliary slots; and the field-pickup side-index selector with its final recheck.
- **Confirmed coverage:** Fighter `+0x20`, accepted-hit source `+0xE58`, copied provenance, coordinator skill participants and pickup side indexes have separate contracts. Ordinary geometry follows the paired fighter; collision candidates can overwrite one another in enumeration order; skill participants persist until explicit release; support native paths resolve sides or retain derived points rather than a selected fighter pointer. The pickup selector retains a side index, ranks two eligible fighters by distance, and is rechecked before collection.
- **Unresolved or untested:** This is not an exhaustive audit of every `+0x20` writer, character skill, resource command or indirect callback. Whole-program stale-pointer safety, cancellation paths outside the traced skill handler, and unrestricted indirect/adjusted-base aliases remain unproven. Whether the copied non-fighter prefix reaches readers outside its copied extent in a concrete state sequence remains open.
- **Deliberate exclusions and overlap:** [Battle AI](../session/battle_ai.md#primary-target-and-spatial-classification) owns AI opponent binding and alternate navigation points; [Projectile motion](../projectiles_and_items/projectile_motion.md#homing-target-data-and-the-delayed-strategy) owns projectile steering. [Battle entities](../session/battle_entities.md#initial-cross-reference-graph) owns allocation and the initial graph. [Battle item inventory](../projectiles_and_items/battle_item_inventory.md#field-pickup-object-lifecycle) owns the field-pickup object lifecycle; [Hit response](hit_response.md) and [Extra Hit](extra_hit.md) own response and exchange rules. Complete-file identities remain in [Retail game file identities](../../game/files/file_identities.md).
- **Evidence limitations:** Static retail instructions establish the bounded paths below. Missing xrefs and false overlay function boundaries prevent interpreting an absent direct reference as a whole-program exclusion.

## Evidence and address conventions

Binary identities and address conventions are in
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
A displayed BTL Ghidra address is live minus `0x40`.

## Paired opponent and geometry refresh

Resident `FUN_002174A0` reads fighter `+0x20`. When it is null, the function
writes self there and returns without updating the spatial fields. Thus the
fallback repairs the pointer only; it does not zero or recalculate cached
distance on that invocation. The initial reciprocal graph is owned by
[Battle entities](../session/battle_entities.md#initial-cross-reference-graph).

With a nonnull pointer, the position source has three exact cases:

| Gate | Position source | Index write |
| --- | --- | --- |
| `(fighter[+0x61] & 7) >> 1 == 1` | Self position, with X shifted by `-500` for `+0x990 == 1` or `+500` for `+0x990 == 0` | `+0x324 = self[+0x9F6]` |
| Other packed role, argument 2 is zero | Opponent current vector `+0x30..+0x3C` | `+0x324 = opponent[+0x9F6]` |
| Other packed role, argument 2 is nonzero | Opponent previous vector `+0x970..+0x97C` | No `+0x324` write in this branch |

The function derives bearing `+0x328`, planar distance `+0x32C`, full 3D
distance `+0x330`, and vertical delta `+0x334`. It changes side `+0x326` only
when the absolute-angle helper result lies strictly between `0.31415927` and
`2.8274333`, writing `0` for positive bearing and `1` otherwise. These are
geometry and facing fields, not a target-search score.

Standard active-fighter maintenance `FUN_0024C440` calls this helper with
argument zero at `0x0024C4D0`, before its pause/countdown handling. Near the
end of the same maintenance function it snapshots current position into
`+0x970..+0x97C`. Position-changing callers `FUN_0021CF40` and
`FUN_0021D0C0` call it with argument one after updating their own position.
They therefore use the opponent's saved position, rather than replacing
fighter `+0x20` with a different candidate.

The remaining resident direct caller functions are `FUN_0022E950`,
`FUN_002316D0`, `FUN_00240FB0`, `FUN_0024ED40`, `FUN_00276CC0`,
`FUN_002BDF80`, `FUN_002C4710` and `FUN_002D1830`. Their inspected calls
refresh geometry after position work, not candidate acquisition.
`FUN_00240FB0` uses argument one after relocation and can refresh again with
zero after field correction; the other listed callers use zero.
`FUN_0022E950` and the placement branches of `FUN_0024ED40` update both
participants before refreshing both, so each current-position lookup sees
the other participant's resulting position.

Four direct BTL callsites, Ghidra `0x0078CDA0/0x0078CDD8` and
`0x007A84B8/0x007A84F0` (live = Ghidra plus `0x40`), likewise pass zero to
refresh the fighters referenced by their enclosing object's
`+0x31C/+0x4CC`, after writing their positions. Raw callsite bytes are
necessary: false no-return annotations remove these calls from the
decompiler output. Neither these calls nor the resident caller list prove
that every character-specific target path uses this helper.

## Accepted-hit source boundary

`FUN_002209A0` reads `+0xE58` independently of paired opponent `+0x20`.
Router mode `0` uses `+0x20` as source; modes `2` and `3` require nonnull
`+0xE58`; mode `1` additionally requires source halfword `+0x02 == 0x474F`,
source word `+0x0C == 1`, and live BTL predicate `0x0072EDE0`. These
dispatch contracts identify hit provenance, not acquisition of a new aim
target. Response, repeat-hit and countdown rules remain in
[Hit response](hit_response.md#rehit-suppression).

### Collision candidates and routing order

`FUN_0021E700` is a collision-result consumer, not an opponent search. Unless
fighter byte `+0x63 & 1` is set, it first clears `+0xC74/+0xC78` and
`+0xD20/+0xD24`, then reads result summaries at `+0xDD4/+0xDD8` and
`+0xDF8/+0xDFC`. It obtains individual contacts through
`FUN_001DDD80(collection, 1/2)` and `FUN_001DD1A0(handle, contact_index)`;
`FUN_001DCA40(contact)` supplies the associated object.

| First collection summary | Candidate/result channel |
| --- | --- |
| `0x20` or `0x200` | Set result bit `1`, retain paired opponent in `+0xC74`, and derive a contact point at `+0xE40` from matching contacts |
| `0x10` or `0x100` | Set result bit `2`, retain paired opponent in `+0xC78` |
| `0x40` or `0x400` | Enumerate contacts; require object magic `0x474F`, kind `+0x0C == 1`, and live BTL predicate `0x007369A0`. Store a passing object in both `+0xE58/+0xC74`, resolve its record, and copy contact position to `+0xE40` |
| `0x100000` or `0x200000` | Enumerate contacts; require object kind `+0x0C == 2`. Store it in both `+0xE58/+0xC74`, resolve its record, and copy contact position |

The kind-1 and kind-2 branches also consult the paired opponent's current
action: record `+0x14 & 0x08000000` with opponent byte `+0xA40 == 1`
suppresses the kind-2 branch; for kind 1 it suppresses an object with byte
`+0x284 != 0` or signed halfword `+0x7A == 0x27`. These are exact
contact-routing gates, not a general side/aim eligibility rule. Both contact
loops can overwrite a prior passing candidate; neither computes a nearest
object. Their retention depends on collection order.

The kind-1 predicate itself, live `0x007369A0` (Ghidra `0x00736960`, file
`0x82AA0`), normally returns actor byte `+0x272`. It returns zero instead
when descriptor byte `+0x2F` is not 1, a fighter can be resolved through
actor side tag `+0x8A` and that fighter's paired link, and
`FUN_00307560(fighter)` succeeds. The descriptor is selected by signed
actor ID `+0x78` from live table `0x0089C910`, stride `0x68`. This is an
additional actor/state gate on the collision candidate; it does not rank
targets or validate an allocation generation. Descriptor and tag semantics
remain in [Projectiles](../projectiles_and_items/projectiles.md).

The second collection produces `+0xD20/+0xD24` and result bits
`0x200/0x100/0x400`; its kind-1 path examines only contact 1 of handle 1.
`FUN_0021ED70` then arbitrates the two fighters' summaries and current
records. Its candidate rewrites copy `+0xD20` into `+0xC74`; after arbitration,
an ordinary surviving result bit `1` installs the paired fighter in `+0xE58`
and its attack record through `FUN_00222A80`.

Coordinator `FUN_0024FD80` performs maintenance for every fighter, callback
stage 1 for every fighter, collision consumption for every active fighter,
then arbitration and accepted-hit routing. It calls `FUN_0021ED70` only for
side-bit-zero fighters. Result bits `1`, `8`, and `4` dispatch accepted-hit
modes `0`, `2`, and `1`, respectively; bit `0x100` dispatches
`FUN_00220690`. The collision pass therefore supplies candidates before the
router applies response eligibility. The lower-level shape-query algorithms
and hit-response rules have separate ownership.

### Retained-source writers and record lookup

The bounded resident `sw` audit for offsets `+0xC74/+0xE58` covers all four
possible opcode high bytes (`AC..AF`) in the real ELF mapping, excluding
alias mappings of the same bytes. Every real hit was assigned to the
functions below. This audit excludes writes through adjusted base pointers,
bulk memory copies, and other store widths. The same patterns returned no BTL
matches; that result is only a direct-offset-store negative.

| Resident function | Pointer operation established by body and store bytes |
| --- | --- |
| `FUN_00214A40`, stores `0x00215150/0x00215164` | Initial clear of `+0xC74/+0xE58` |
| `FUN_0021E390`, store `0x0021E400` | Collision setup clears `+0xC74`; does not clear `+0xE58` |
| `FUN_0021E700` | Refreshes `+0xC74` and sets both pointers for kind-1/2 contacts as above |
| `FUN_0021ED70` | Arbitration rewrites `+0xC74` and later retains paired source in `+0xE58` |
| `FUN_00232A50`, stores `0x00232AE0/0x00232AE4` | Explicit source dispatch installs both pointers, clears cached record, then selects router mode `0` for kind 0, `1` for kind 1, `2` for kind 2; kind 4 returns `1` without installing, other kinds return `-1` |
| `FUN_00232B80`, stores `0x00232BE4/0x00232BE8` | Explicit response route installs both pointers when argument 4 is nonzero and the record differs |
| `FUN_00233110`, stores `0x0023314C/0x00233150` | Kind-0 explicit contact installs both, then arbitrates the pair before mode `3` |
| `FUN_002335F0`, stores `0x00233690/0x00233694` | Explicit source/record route installs both after fighter/global-state and countdown gates |
| `FUN_00241F10`, stores `0x002421F4/0x002421F8` | Extra Hit role reversal installs paired opponent as source; the role transition belongs to [Extra Hit](extra_hit.md#exchange-state-at-fighter-0xb00) |

`FUN_00222B20` resolves the record in this order: cached `+0xE54`,
non-kind-0 source `+0xE58` through `FUN_002179F0`, non-kind-0 candidate
`+0xC74` through the same helper, then resident `PL_ATK_DUMMY` record
`0x00407C00`. `FUN_002179F0` checks magic `0x474F` and distinguishes a
fighter's current action (kind 0, class 8), transient actor record service
live `0x00734300` (kind 1), and opposite-side current support record service
live `0x00886850` (kind 2). The latter two return the dummy record when their
service produces null. Thus a source pointer and a retained attack record
are separate data contracts.

### Copied provenance and pointer lifetime limits

The final provenance stage of `FUN_00232B80` maintains another channel:
fighter `+0x7C8` identifies the source used with record `+0x7CC`. When the
source has magic `0x474F`, both receiver predicates
`FUN_00221520/FUN_00216820` return zero, and source kind is nonzero, it copies the
source prefix into receiver `+0x7D0` through `FUN_00221460`, then points
`+0x7C8` there. Kind 0 instead retains the supplied source itself.
The copier's full instructions transfer exactly bytes `0x00..0x4F`;
it does not clone pointed-to allocations. This copied provenance is separate
from `+0xE58` and does not replace that retained pointer.

The concrete maintenance replacement is in `FUN_0024C440`, instructions
`0x0024C634..0x0024C730`. When receiver byte `+0x62 & 1` is clear and
byte `+0x61` bit 3 is clear, it requires receiver magic `0x474F` and both
`FUN_00221520/FUN_00216820` to return zero. It then installs self in
`+0x7C8` for kind 0, or a fresh self-prefix copy at `+0x7D0` for other
kinds, installs `PL_ATK_DUMMY` in `+0x7CC`, and resamples receiver byte
`+0x63` bit 7 into `+0x830`. The stores at `0x0024C728/0x0024C72C`
replace this channel; they do not clear `+0xC74/+0xE58` or the paired link.
This is a gated refresh, not an unconditional end-of-frame release or an
object-removal notification.

The copy extent also limits claims about later readers. In
`FUN_0022B160`, instructions `0x0022B190..0x0022B1C4`, a nonnull
`+0x7C8` whose kind `+0x0C` is nonzero remains in argument `a1` for
`FUN_0021B460`. That router checks source magic, then sends kind 1 to
live `0x00737500` and kind 2 to live `0x00886780`. The kind-1 helper's
true body starts at Ghidra `0x007374C0`: it reads source signed ID `+0x78`
and, outside IDs `19,45..4A`, takes a vector at source `+0x90`. The
kind-2 helper calls live `0x00889100(source,1,0)`, which reads source
side byte `+0xE4` to select its separate point table. These fields are
outside the copier's `0x50`-byte extent. The bounded caller can therefore
dispatch by copied kind without proving that all subsequent field reads
come from the copied prefix. Whether a concrete producer/state sequence
reaches those branches with an embedded copy, and what values the later
receiver storage contains then, remain unresolved. This finding establishes
neither a stale-pointer failure nor a safe full-object snapshot. The helpers'
wider actor and support behavior remains with
[Projectiles](../projectiles_and_items/projectiles.md) and [Support mechanics](../characters/support_mechanics.md).

`FUN_00222B20` reads source kind `+0x0C` before `FUN_002179F0` checks magic.
Neither function checks an allocator identity or generation. The bounded
direct-`sw` audit finds `+0xE58` zeroing at initialization, while collision
refresh clears `+0xC74` but can leave `+0xE58` unchanged. These observations
do not prove a stale-pointer failure; equally, the dummy-record fallback
does not prove that dereferencing an expired object would be safe.
Ownership and removal order belong to [Battle entities](../session/battle_entities.md),
and ordinary graph scheduling to [Battle lifecycle](../session/battle_lifecycle.md#per-update-dispatch).

## Skill participants and lock release

Ultimate Jutsu connection `FUN_00244F80` selects attacker `+0x20`, then
requires the attacker's active record to match that fighter's resolved hit
provenance. It does not search for an alternative fighter. Complete start
gates and presentation behavior remain in [Ultimate Jutsu](../characters/ultimate_jutsu.md#start).

`FUN_00216EA0(attacker, level)` installs the attacker and paired target at
coordinator `+0x24/+0x28`, with level `+0x20`, when entering state 6.
These are borrowed aliases, as established by the
[coordinator ownership contract](../session/battle_entities.md#derived-fighter-registrycoordinator).
State setter `FUN_0024E380` clears `+0x18/+0x1C/+0x20` and writes the
state selector; it does not clear either participant pointer.

The complete state-6 handler `FUN_0024ED40` requires both participants and
presentation global `0x00607834` to be nonnull. Its missing-input branch,
stores `0x0024ED78..0x0024ED84`, resets the state-local words but leaves
`+0x24/+0x28` intact. The traced substates operate on the installed pair
without selecting a replacement. Initial handling sets both fighters'
byte `+0x61 & 0x80`; `FUN_00217320` responds to that bit by publishing
zero logical input, movement scalars and held-direction field. This is an
input lock on retained participants, distinct from choosing an aim target.

In final substate 4, the handler increments coordinator `+0x1C` and waits
until its previous value is greater than 30 and both fighter bytes
`+0x63` have bit 7 set. Only then does it clear both input-lock bits and
reset the state-local words. Stores `0x0024FD60/0x0024FD64` explicitly
clear coordinator `+0x28/+0x24`. This release does not clear the fighters'
paired links. No allocation-generation check appears in the handler, and
other interruption or destruction paths are outside this bounded release
proof.

## Separate side-index eligibility selector

The selector belongs to BTL field-pickup objects (registered classes
`ItemData`, `ItemRecoverLife` and `ItemChakraBall`), rather than a fighter or
support attack. Their factory, state dispatcher, admission wrappers,
collection continuation and teardown are documented in
[Battle item inventory](../projectiles_and_items/battle_item_inventory.md#field-pickup-object-lifecycle).
The object retains a side index at `+0x5C`, initialized to `-1`, never a
fighter pointer.

### Admission gate and selector body

The BTL selector has true entry live `0x0070B840`, Ghidra `0x0070B800`,
file `0x57940`; its complete raw body ends at Ghidra `0x0070BB94`. Its
input flags select the side index retained at object `+0x5C`:

| Input flags | Selection |
| --- | --- |
| Both `0x10` and `0x100` | Evaluate both primary fighters with `FUN_002167A0`; select the only eligible side, write `-1` and return zero if neither is eligible, or compare distances if both are eligible |
| Only `0x10` | Select side 0 without that eligibility predicate |
| Only `0x100` | Select side 1 without that eligibility predicate |
| Neither | The initialized mode 0 reaches the same side-1 selection branch |

Both established admission wrappers require `flags & 0x110 != 0` before
calling, so the neither-bit row describes the selector's callable body,
not a reachable input from those wrappers.

`FUN_002167A0` rejects fighter `+0x61` bit 7, major state 6, major state 5
substates `0x42..0x49`, and nonzero `+0xB00`. When both fighters pass,
live helper `0x00709FD0` (Ghidra `0x00709F90`, file `0x560D0`) compares
their current positions with object position `+0x20`, using full XYZ
Euclidean distance through `FUN_001806F0`. It selects the nearer side and
breaks equal-distance ties through `FUN_00180210(1)`, which returns 0 or 1.
The selector then resolves the fighter through `FUN_003769C0(side)`;
it retains the side index rather than storing the fighter pointer. One
later transition clears `+0x5C` back to `-1` at live `0x0070BB2C`. The
body's item resolution, inventory check and terminal results belong to the
pickup lifecycle linked above.

### Recheck before collection

Full wrapper live `0x0070B720`, Ghidra `0x0070B6E0..0x0070B7F4`,
saves the selector's byte result and examines `+0x5C`. Index `-1` returns 1.
Otherwise it freshly resolves the fighter; a null lookup also returns 1
without clearing the index. A nonnull fighter must pass
`FUN_002167A0(fighter,item_byte)`, including for the single-side selection
branches that skipped this predicate inside the selector. Failure clears
the index at live `0x0070B798` and returns 1. Therefore single-side flags
bypass the initial ranking eligibility test, not the final pickup recheck.

This proves a distinct pickup candidate-selection contract, not a global combat
eligibility rule. The predicate's state exclusions cannot be treated as
hurtbox invulnerability; see
[Hit response's eligibility limits](hit_response.md#rehit-suppression).

## Support side selection and point retention

The support factory's final vtables were read from resident
`0x005FBB40..0x005FC2B7`. All 14 final tables listed in
[Support mechanics](../characters/support_mechanics.md#factory-variants-and-attack-completion)
have approach slot `+0x50 = live 0x00889C10`. Common entry, departure and
alternate-exit slots `+0x4C/+0x58/+0x5C` are also shared. This bounds the
following target selection across the whole factory set, rather than one
sample class.

Common state 1, live `0x00889C10` (Ghidra `0x00889BD0`, file `0x1D5D10`),
loads primary fighters directly from the manager:

```text
own fighter = manager[+0xDE4 + signed support[+0xE4] * 4]
opponent    = manager[+0xDE4 + ((signed support[+0xE4] + 1) & 1) * 4]
```

Its waiting/following branch derives a point `120` X units toward the
opponent from the owning fighter; its approach branch compares opponent X
distance against object `+0x130`, then moves toward the opponent or starts
attack reason 2. It stores motion/facing state, not the resolved fighter
pointer. The side byte selects the target anew on each invocation; this path
does not search a list or rank candidate fighters. The loads assume a valid
manager and nonnull fighter slots.

The small facing helper has a false interior function label in the preserved
import. Full raw body at Ghidra `0x0088B4D0..0x0088B58C` is live
`0x0088B510..0x0088B5CC` (file `0x1D7610..0x1D76CC`). Argument 2 low byte
zero selects the owning side; nonzero selects the opposite side. It compares
the selected fighter's X with support X, writes angle `-pi/2` or `+pi/2` to
`+0xA8`, optionally negates it when argument 3 is nonzero, then copies it to
`+0x48`. No target pointer survives the call. Entry's initial positioning
calls it with `(support, 1, 0)` at live `0x00889A84`; the omitted entry tail
at live `0x00889B34..0x00889BB8` independently resolves the opposite fighter
when the side-record request selector is 1. The retained `+0x130` threshold
and motion fields are not ownership references.

Live `0x0088B980` (Ghidra `0x0088B940`, file `0x1D7A80`) likewise resolves
opposite side for argument 2 zero and owning side otherwise. It compares
the absolute difference of position component `+0x34` against `50.0`.
This is a positional gate; it does not inspect hurtbox eligibility or retain
the fighter.

### Complete native attack-slot boundary

All nine distinct final attack-slot bodies were inspected. The rows below
record their fighter-target or point-retention contract; animation completion
and support lifecycle remain in [Support mechanics](../characters/support_mechanics.md).

| Attack slot, live (Ghidra = live minus `0x40`) | Target-relevant behavior in the native body |
| --- | --- |
| `0x0088A820` | Shared completion dispatch; no fighter lookup in the body |
| `0x0088C8E0` | On newly crossed animation index 1, resolves opposite fighter, derives elevation from opponent `+0x30/+0x38`, and retains a scalar at object `+0x510`, clamped to `+/-0.47123894`; no retained fighter pointer |
| `0x0088D320` | Resource/animation dispatch and local state; no fighter lookup in the body |
| `0x0088D680` | At newly crossed index `0x5F`, resolves owning fighter and applies resident effect requests `0x0C` and `5` |
| `0x0088D780` | Same owning-fighter effect requests at index `0x5A` |
| `0x0088DC70` | Validates a separate effect record with index, active byte and generation ID; transforms that record from support position. The retained pointer is an effect object, not a selected fighter |
| `0x0088E0A0` | Creates/moves an object-local position block `+0x510..+0x51C`, then queries its motion against a field; no fighter lookup in the body |
| `0x0088E540` | Local scalar write and completion dispatch; no fighter lookup in the body |
| `0x0088E790` | Validates and advances a separately indexed/generation-checked effect record; no fighter lookup in the body |

These bounded native-body negatives do not cover animation-resource commands,
indirect effect callbacks or every emitted actor's behavior.

Every final table uses emitter slot `+0x60 = live 0x0088B040`, except table
`0x005FBDC0` (resolved code `0x24`), which uses live `0x0088D880`. The common
emitter forwards the support side and supplied spawn vectors to live
`0x00736080`. The override resolves the opposite fighter and computes a
randomly offset point around its current position, then supplies that same
point as both spawn vectors. Each emitter configures the created actor with
copied scalar metadata without retaining a fighter pointer. Both copy support
generation `+0x120` into actor `+0x288` with marker `+0x284 = 1`; that token is
[support lineage](../session/battle_entities.md#non-owning-support-lineage-on-transient-actors),
not a target identifier.

All distinct slots `+0x64..+0x74` across the 14 tables were also inspected:
they return availability, form resource names, or attach resource objects to
an animation. Their native bodies do not select a fighter. The common
availability leaf at live `0x0088B740` returns whether `+0x78` is zero; the
code-`0x2A` override at live `0x0088E3C0` returns 1. Neither true entry has a recognized
function; their full small bodies were read from memory bytes.
