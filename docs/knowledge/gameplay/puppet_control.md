# Puppet and auxiliary-character control

This document investigates puppet and auxiliary-character control in retail
NA2 (`SLPS-25837`): how subordinate scenes and playbacks follow the primary
fighter, and the linked string/trail presentation helpers that join those
playbacks to the primary model, including their sample lifetimes and curve
equations.

## Research coverage

- **Assigned scope:** Control/state/ownership of puppet and auxiliary-model battle actors, independent action dispatch, linkage to the primary fighter, positioning, attack routing and teardown; authored attachment definitions and string/trail sample lifetimes and equations.
- **Exploration depth:** Inspection covers construction, setup, animation synchronization, ordinary/presentation update wrappers, attack bridges and owned teardown for Classic Kankuro `0x12`, Kankuro `0x3C`, Chiyo `0x3E` and Sasori `0x3F`. It also covers their default action callback tables, the shared root-motion layout/consumer paths, linked presentation-helper lifetime and the distinct construction paths for playable Sasori IDs `0x4B/0x4C`. The 13 distinct definitions published by these four constructors, attachment resolution, fixed sample pools, expiry, temporal insertion, smoothing and curve producers are decoded below. Large action-specific deformation routines were inspected for their control/ownership connections, without decoding every authored constant or matrix operation.
- **Confirmed coverage:** Two-record Kankuro/Chiyo ownership; Classic Kankuro's authored speed multiplier; Sasori's second-playback activation and shared local attack timer; Chiyo's shipped action/phase origin selector; primary callback ordering and gates; primary-owned attack-bank publication; root-motion/query coupling; helper definition/playback retention, attachment precedence, fixed capacities, sample expiry/smoothing, distinct spatial/temporal tangents and teardown; selected action-produced curve controls and Sasori's registered particle-generator creation path.
- **Unresolved or untested:** Complete action-by-action deformation equations, all generated presentation-object descendants, and the visibly active string/trail configuration for every action remain unresolved. Chiyo's deformation decay reads primary `+0x5710`, whose nonzero writer is not established. The selected Sasori generator's resource-catalog outcome and its descendants' actual material/appearance are not sampled. Missing-attachment fallback reachability, degenerate curve normalization, original action names and wall-clock sample retention remain unknown. The inspected control paths do not establish separate controller input, independent fighter registration or an independently damageable puppet; this is not a whole-program proof that such behavior never exists.
- **Deliberate exclusions and overlap:** [Battle entities](battle_entities.md) owns standard fighter/registry lifetime; [character assets](../game/character_assets.md#auxiliary-model-animation-providers) owns animation-name/provider tables; [collision](collision.md) owns generic interaction descriptors and pair filters; [combat action execution](combat_action_execution.md) owns common action dispatch; [model runtime](../runtime/model_runtime.md) and [animation runtime](../runtime/animation_runtime.md) own general scene and playback mechanics. [Scene playback owners](../runtime/scene_playback_owners.md#fighter-animation-ownership) owns general caller scheduling, with [generator child ownership](../runtime/scene_playback_owners.md#generator-child-ownership) owning shared generated-playback lifetimes. Complete-file evidence identities remain in [Retail game file identities](../game/files/file_identities.md).
- **Evidence limitations:** Static inspection of retail resident `SLPS_258.37`. Function names are preserved analysis labels, not recovered source names. Decompiler vector expressions and omitted calling arguments require instruction corroboration; uninspected branches remain unknown.

## Evidence conventions

Addresses in the resident executable are EE addresses. `record[i]` below means
`fighter + 0x5BF0 + i * 0x80`, with `i` in `0..1`, for Chiyo's ID `0x3E` class.
An auxiliary scene is not automatically an independently registered battle
actor. The allocation, callback and attack-consumer paths below establish the
particular relationship without assigning a broader entity category.

## Chiyo's two subordinate records

**Observation, high confidence:** Resident constructor `FUN_002A8E40`
(`0x002A8E40..0x002A909C`) calls the common fighter constructor, installs
table `0x005DA830` at fighter `+0x50`, constructs two `0x80`-byte records and
points their animation arrays into the same fighter allocation. Setup
`FUN_002A9150` (`0x002A9150..0x002A969C`) allocates one `0xB0` scene,
one `0xA0` scene and one `0x120` playback object for each record. It binds
playback to that record's `0xA0` scene and the primary fighter's body
container. The animation-name and material/palette lookup belongs to
[character assets](../game/character_assets.md#auxiliary-model-animation-providers).

| Record field | Absolute field for record 0 | Established use |
| --- | --- | --- |
| `u32 +0x00` | `+0x5BF0` | Playback result/state: reset to 0 on switching; the updater stores a playback result while zero and writes 2 on later visits when nonzero. |
| `s16 +0x04` | `+0x5BF4` | Main-fighter animation index copied from `+0xB8C` when switching; also selects positioning/presentation branch. |
| `s16 +0x06` | `+0x5BF6` | Last synchronized main index; compared with primary `+0xB8C` to trigger switching. |
| `+0x08` | `+0x5BF8` | Embedded `0x24`-byte timer initialized with `FUN_00211770`, assigned zero by `FUN_002117A0` on switching, and advanced or event-suppressed by the attack callback. |
| `+0x70` | `+0x5C60` | Owned `0xB0` scene pointer. |
| `+0x74` | `+0x5C64` | Owned `0xA0` scene pointer. |
| `+0x78` | `+0x5C68` | Owned `0x120` playback object pointer. |
| `+0x7C` | `+0x5C6C` | Borrowed pointer to embedded animation lookup array: fighter `+0x5720` or `+0x59B4`. |

**Observation:** `FUN_002AD430` (`0x002AD430..0x002AD53C`) switches the
requested subordinate animation. If the requested lookup is null and the
record's result is zero it returns 0; otherwise it uses slot `0x29`.
Requesting `0x29` with result zero and saved synchronized index greater than
`0x55` also returns 0. An accepted switch copies primary `+0xB8C` into
record `+0x04`, clears record `+0x00`, calls `FUN_001B99B0` with its own
lookup result, optionally applies primary `u16 +0xB94 << 8`, and resets
record `+0x08`. These are separate playback instances with explicit primary
state coupling.

**Observation:** `FUN_002AD880` copies `+0xB8C` into each record's `+0x06`
only when that record's `+0x04` matches it. `FUN_002AD910`
(`0x002AD910..0x002ADA7C`) and `FUN_002ADA80`
(`0x002ADA80..0x002ADC2C`) require primary byte `+0x00` bit 1 and a
non-1 result from `FUN_00224650`. For each record they switch on an index
mismatch, copy playback `+0x94` from primary playback `+0xE70`, advance the
subordinate playback, update its placement and copy primary playback `+0x88`.
The latter wrapper additionally gates that update with primary byte `+0x61`
bit 4 clear and then invokes its presentation path. Their shared downstream
movement consumer is `FUN_002AA3D0`.

## Chiyo positioning and attack origin selection

**Observation:** `FUN_002AD570` (`0x002AD570..0x002AD7CC`) uses a distinct
placement branch when record `s16 +0x04` is below `0x23` and differs from
`0x1C`. That branch starts at primary position `+0x30`, applies a record-index
dependent Y offset and, for indices `0..3`, an X offset. Primary
`s16 +0x990` selects the sign of both offsets. It sets
the subordinate playback transform using primary rotation `+0x40` and scale
`+0x2E0`. It resolves object name `0x004F6E30` in that playback, obtains its
matrix and copies it to record `+0x70`'s matrix at scene `+0x40`, marking
scene byte `+0x8D = 1`. Other record indices use the primary transform
directly. Bytes at `0x004F6E30` identify the attachment as
`OBJ_2kgt00t0 spine1`; movement separately resolves the `trall` object at
`0x004F6E10`.

**Observation:** `FUN_002A98E0` (`0x002A98E0..0x002A9A9C`) chooses a
subordinate record using the common action selector `FUN_00217860`. Selector
0 uses record 1; selectors 4/5/6 use record 0; other selectors below `0x15`
return null. Selector `0x1C` chooses by primary phase `+0x192` and integer
`+0x1E8`; the remaining selectors use signed bytes at `0x005C3C5B + selector`.
This is action-dependent origin selection, not an input-device assignment.

The bytes at `0x005C3C70` give the following mapping within the shipped
44-action definition at `0x004F6BB0+0x28`. The selector itself has no upper
bound check before this lookup; the table below does not assign behavior
to values beyond the authored range.

| Selected record | Normalized selectors |
| --- | --- |
| 0 | `4/5/6`, `0x15`, `0x17..0x1A`, `0x1E`, `0x20/0x21`, `0x24/0x25`, `0x27`, `0x2A` |
| 1 | `0`, `0x16`, `0x1B`, `0x1D`, `0x1F`, `0x22/0x23`, `0x26`, `0x28/0x29`, `0x2B` |
| Null | Other values below `0x15` |
| Phase-dependent | `0x1C`, as below |

For selector `0x1C`, record 0 is the default; the following signed
`fighter+0x1E8` conditions select record 1. Instruction range
`0x002A9954..0x002A9A40` establishes the comparisons and phase jump table.

| Primary phase `+0x192` | Condition selecting record 1 |
| ---: | --- |
| 0 | Count >= 10 |
| 1 | Count < 5 |
| 2 | Always |
| 3 | Count >= 11 |
| 4 | Count < 4 or count >= 10 |
| 5, 6 | Count >= 10 |
| 7 | Count < 5 |

Other phase values return record 0, including negative values rejected by
the unsigned phase-range comparison.

**Observation:** `FUN_002A9AA0` (`0x002A9AA0..0x002A9C9C`) redirects
the common authored-action consumer only when major state `+0x18E == 8`,
the current action word has bit 1 set, `FUN_00224650 != 1`, mask
`fighter+0xB00 & 0xFF00` is zero and the selector returns a record.
For each of two action banks whose `FUN_0021FC40` result is zero it passes
`FUN_0021FC70` the current `0x18`-byte action-bank entry, selected playback
record `+0x78`, result `+0x00` and state `+0x08`. Thus the fighter action
remains the source, while a selected puppet supplies the scene and local
state. Afterwards, `FUN_00224650 == 0` advances both states with each
playback object's `u16 +0x94 / 256.0`; a nonzero result clears both timers'
event flag through `FUN_00211F70` and can call the linked visual helper when primary byte
`+0x61` bit 6 is set. The common consumer's attack/collision details retain
their neighboring owners.

## Chiyo-owned teardown

**Observation:** `FUN_002A96A0` (`0x002A96A0..0x002A979C`) loops over both
records and destroys playback `+0x78`, scene `+0x74` and scene `+0x70` in
that order with deleting argument 1, nulling each owning field. It then
destroys and nulls primary field `+0x5CFC`. The constructor allocates that
8-byte helper with `FUN_00210600`, linking the primary fighter and first
playback, and adds the second through `FUN_002109F0`. Deleting destructor
`FUN_002A90A0` explicitly invokes this cleanup, destroys both embedded
records through `FUN_00119220(..., 0x0029EC10, 0x80, 2)`, then invokes the
common primary destructor `FUN_00214840`. Table `0x005DA830+0x08` contains
that deleting destructor. Its helper lifetime is detailed under
[Linked presentation helpers](#linked-presentation-helpers).

## Kankuro's two-record variant

**Observation, high confidence:** ID `0x3C` constructor `FUN_0029E9E0`
creates two records at fighter `+0x5520 + i*0x80`. They share Chiyo's
result/index/state fields at record `+0x00/+0x04/+0x06/+0x08`, but have only
the `0xA0` scene and `0x120` playback pair at record `+0x74/+0x78`.
Setup `FUN_0029ED70` creates both pairs and binds each to the primary body
container. Record `+0x7C` points into embedded arrays at fighter `+0x5058`
and `+0x52BC`. This is two subordinate scenes owned by one primary fighter.

**Observation:** `FUN_002A2D00` follows primary `+0xB8C`, compares the
record's synchronized index, clears its result and switches its own playback
on mismatch. A null requested animation uses slot `0x29`; if both are null
it writes result 3. Result 3 skips placement/playback work. Result zero copies
primary playback `+0x94`, advances the subordinate and stores its result;
other non-3 results become 2. Placement begins with the primary transform,
and copies playback `+0x88`. `FUN_002A37F0` publishes primary `+0xB8C` to
both record `+0x06` fields. Update wrappers `FUN_002A3870` and
`FUN_002A38E0` call this synchronizer and movement `FUN_0029FEB0`, under
the same primary-active and `FUN_00224650 != 1` gates seen in Chiyo.

**Observation:** Action callback `FUN_002A39C0` reaches `FUN_0029F3F0`.
Under the same authored-action gate as Chiyo, normalized selectors
`0x1F..0x22` choose record 1 (`+0x55A0`); every other selector chooses
record 0 (`+0x5520`). Both attack banks receive that record's playback,
result and timer. Both local timers advance from their own playback
`u16 +0x94 / 256.0` or have their event flag cleared through `FUN_00211F70` when
`FUN_00224650` succeeds.

**Observation:** Constructor `FUN_0029E9E0` creates two 8-byte linked helpers
at `+0x5620/+0x5624`, each with two subordinate nodes and one playback
pointer. Cleanup `FUN_0029F1A0` destroys and nulls both playback/scene pairs,
then both helpers. Deleting destructor `FUN_0029ECC0` calls that cleanup,
destroys the two embedded records and calls the common fighter destructor.

## Classic Kankuro ID `0x12`: one playback with an authored rate

**Observation, high confidence:** Constructor `FUN_00265B10` installs
table `0x005DADC0` and embeds result `+0x507C`, animation indices
`+0x5080/+0x5082` and timer `+0x5084`. Setup `FUN_00265D70` allocates
one `0xA0` scene at `+0x5110` and one `0x120` playback at `+0x5114`,
binds them to the primary body container and selects slot `0x29`. After
setup returns, the constructor creates an 8-byte helper at `+0x5374`
with five nodes. Lookup pointer `+0x5370`
addresses embedded array `+0x5118`; provider details belong to
[character assets](../game/character_assets.md#auxiliary-model-animation-providers).

**Observation:** `FUN_0026A2B0` follows primary animation `+0xB8C`, clears
result `+0x507C`, and switches a nonnull lookup into the subordinate playback,
resetting its timer to zero. Its speed rule differs from ID `0x3C`:

```text
base = fighter+0x1AC                           when major state == 8
base = s16(primary_playback+0x94) / 256.0       otherwise
authored = s16(name_table + animation_index*8 + 4) / 256.0
subordinate_playback+0x94 = trunc(base * authored * 256.0)
```

The stored result is a halfword. Result zero advances playback and stores its
return; an already nonzero result becomes 2. Placement starts at the primary
position/rotation/scale, and playback `+0x88` follows the primary playback.
`FUN_0026A630` publishes primary `+0xB8C` into synchronized index `+0x5082`.
Wrappers `FUN_0026A680` and `FUN_0026A7A0` run the synchronizer and movement
`FUN_00266CA0` under the primary-active and `FUN_00224650 != 1` gates;
the latter uses the additional byte `+0x61` bit 4 gate before presentation.

**Observation:** `FUN_0026A990` reaches attack bridge `FUN_002662A0`.
Both authored-action banks use the one playback, result and timer above.
The local timer increment reads the resulting playback speed as **unsigned**
`u16 / 256.0`, despite the signed inputs in the speed calculation.
Cleanup `FUN_00266220` destroys and nulls playback, scene and helper.
Deleting destructor `FUN_00265CD0` calls that cleanup before destroying
the primary fighter.

## Sasori ID `0x3F`: one local timer, two playback choices

The primary ID and name are taken from [character identity](character_ids.md)
and the character reference. Its subordinate animation resources use `kkg`
names, as recorded in [character assets](../game/character_assets.md#auxiliary-model-animation-providers).
This ID is distinct from the separately constructed playable IDs `0x4B`
and `0x4C`.

**Observation:** Constructor `FUN_002AEA00` and setup `FUN_002AEC80` own a
`0xA0` scene at `+0x4EF0`, a `0x120` playback at `+0x4EF4`, a second
`0x120` playback at `+0x5114`, and an 8-byte linked helper at `+0x50EC`.
The primary subordinate state is `+0x4E60`, animation/synchronized indices
are `+0x4E64/+0x4E66`, and the one local timer is `+0x4E68`.
The animation array pointer at `+0x50E0` addresses embedded `+0x4EF8`.
The second playback has state `+0x50F0`, remembered selector `+0x50F4` and
transform snapshot `+0x5120`. Setup initializes its state to 2 and resolves
its separate seven animation slots at `+0x50F8..+0x5110`; resource identities
remain with the asset document.

**Observation:** `FUN_002B1C90` switches the first playback when primary
index `+0xB8C` changes, resets the local timer and calls `FUN_002B1F50`.
Selector `0x19`, phase 2 preserves that playback's current animation while
still calling the second-playback selector. Speed `+0x94` is copied to both
playbacks from primary playback, except selector `0x20` uses fighter
`u16 +0xB90`. The first playback's result/transform and `+0x88` follow the
primary. `FUN_002B28C0` and `FUN_002B2A10` invoke this synchronizer,
movement `FUN_002AFBE0`, a named subordinate attachment position consumer,
and the second-playback updater `FUN_002B22A0`.

**Observation:** `FUN_002B1F50` maps normalized selectors to the second
playback's animation slots:

| Selector | Slot in `+0x50F8` |
| --- | ---: |
| `0x1C` | 0 |
| `0x1D` | 1 |
| `0x20` | 2 |
| `0x1B` | 3 |
| `0x1E` | 4 |
| `0x19`, `0x22` | 5 |
| 0 | 6 |

It starts a nonnull selected animation only in primary phase 0, stores state
2 and remembers the normalized selector. For other selectors a separate
global gate can return the second state to 2. `FUN_002B20B0` writes the
second state; state 0 also sets its transform and snapshot. Selector `0x20`
starts at primary X minus/plus 100 by facing. `0x1C/0x1D` can use the linked
fighter's position or a facing-dependent 200-unit offset from the primary,
then call live BTL `0x00708CE0` for a positional result; its sentinel
`-32768.0` returns placement to the primary. No broader BTL geometry meaning
is assigned by this call alone.

**Observation:** `FUN_002B22A0` advances the second playback only while its
state is zero, stores the result, sets `+0x88 = 1.0`, and updates placement
for selectors `0x19/0x22`. Selector `0x22` also scales `+0x88` from remaining
animation frames when fewer than five remain. Any already nonzero state
becomes 2. Attack wrapper `FUN_002B2BA0` reaches `FUN_002AF360`: it chooses
first playback `+0x4EF4` when second state is 2 or selector is `0x19/0x22`,
otherwise second playback `+0x5114`. In both cases the common consumer gets
the same result `+0x4E60` and timer `+0x4E68`. Thus changing the visual origin
does not allocate a second local attack timer in this path.

**Observation:** Cleanup `FUN_002AF1E0` destroys and nulls first playback,
scene, helper and second playback, in that order. The deleting destructor
is `FUN_002AEBE0`, selected at table `0x005DA800+0x08`.

### Sasori's activation comes from primary action callbacks

**Observation:** Default channel-3 callback `FUN_002B2C30` supplies the
state-zero transitions used by `FUN_002B22A0`. It derives its selector,
phase and event predicates from the primary fighter, then calls
`FUN_002B20B0(primary, 0)` at these points:

| Selector | Primary event that activates the second playback |
| --- | --- |
| `0`, `0x1E` | Timer `+0x1B8`, event 1 |
| `0x1C`, `0x1D`, `0x20` | Phase 0, timer `+0x1B8`, event 1 |
| `0x1B` | Timer `+0x1B8`, event 11 |
| `0x19` | Phase 0, timer `+0x1DC`, event 8 |
| `0x22` | Phase 0, timer `+0x1DC`, event 4 |

The ID check limits these owned-state calls to primary ID `0x3F`.
The same callback can create presentation objects from a stored transform
or a bone in the second playback through `FUN_002B26F0`. That helper
calls `FUN_00349BA0`, sets the returned object's transform and material,
then registers it through `FUN_00349A80`. These are battle particle
generators, separate from the two embedded playback pointers and their
owned teardown. Shared generator scheduling and retirement belong to
[particle runtime](../runtime/particle_runtime.md#battle-particle-generator-extension),
with the concrete Sasori producer described next.

### Sasori's generated presentation descendant

**Observation:** `FUN_002B26F0` accepts only primary ID `0x3F`. Mode zero
copies fighter snapshot `+0x5120`; nonzero mode resolves `OBJ_gpos_stt`
(`0x004FC4F0`) in the second playback `+0x5114` and returns without creating
anything if the name is missing. Unlike the string producer's missing-name
path, this caller has no root-position substitute. It copies the attachment
translation before calling the generator factory; the returned generator
does not retain that attachment pointer in this caller.

Default channel 3 supplies mode zero for normalized selector `0x21` while
primary integer `+0x1C4 < 19`. It constructs the snapshot from primary
position plus `(60,0,150)`, reversing X when `s16 +0x990 == 1`.
Selectors `0x1B/0x1E/0x20` supply mode one while second state `+0x50F0`
is zero. `0x1D` calls mode one across its inspected callback branch;
`0x1C` calls mode one in phase 1, and in phase 0 while that second state is
zero. Instructions `0x002B3058..0x002B308C` retain `a1=1` on the phase-0
path where the decompiler omits the argument. These are callback-call predicates,
not recovered player-facing action names or observed emission frequencies.

Every successful call supplies the same generator descriptor
`0x004FC490` and force descriptor `0x004FC4D0` to `FUN_00349BA0`.
It chooses one of borrowed materials at primary `+0x5130/+0x5134` through
`FUN_00180210(1)`, sets the generator transform, sets byte `+0x264=1`
and copies the position into generator `+0x270`. It applies the chosen
material to the generator's embedded object via
`FUN_0034A4B0 -> FUN_001C45B0(..., material, 2)`, then registers the
generator with `FUN_00349A80(generator, 0)`. The zero second argument
requests no returned tracking handle; this caller stores no generator
pointer on the primary. Material lookup/provider ownership remains with
[character assets](../game/character_assets.md#auxiliary-model-animation-providers).

The sampled descriptor copies emitter lifetime 5 to generator `+0x1EC`,
particle lifetime 5 to `+0x1F4`, emission value 10 to `+0x200`, variation
2 to `+0x208`, and fade halfwords `0x0400/0x0080` to `+0x214/+0x216`.
It requests the shared estimated-capacity path rather than a primary-owned
playback allocation. These values yield capacity 16 under the
[pool-sizing formula](../runtime/particle_runtime.md#pool-sizing-and-lazy-visual-resources).
Finite emitter expiry consequently uses the shared `age > 5` predicate,
followed by retention until live visuals drain, under the manager's own
update gates. Primary puppet teardown is not the demonstrated owner of
this registered generator. Its default resource-catalog index is 0 with
one choice (descriptor `s16 +0x0E=0`, byte `+2` low nibble zero, promoted
to count 1 by registration). `FUN_0034A530` derives resource kind from the
loaded catalog object, so the descriptor alone does not fix whether the
generated child is a sprite, model or playback. That loaded catalog outcome
remains unsampled; the shared child
construction/reuse contract belongs to
[scene playback owners](../runtime/scene_playback_owners.md#generator-child-ownership).

**Evidence:** complete `FUN_002B2C30/002B26F0/00349BA0/00349A80`
decompilation, factory setup arguments at `0x00349C40..0x00349C54`,
registration bytes `0x002B2848..0x002B2857`, resource conversion
`FUN_0034A530`, and descriptor/name bytes
`0x004FC490..0x004FC4FF`, `0x004FC530..0x004FC53F`. This is one concrete
generated-descendant path; other overlay creation calls in Sasori's
callback are not classified here.

### Playable Sasori variants use distinct construction paths

**Observation:** ID `0x4B` constructor `FUN_002D2A60` installs table
`0x005DA570` and resolves three borrowed material pointers at
`+0x5648/+0x564C/+0x5650`. Its slot-`+0x24` callback `FUN_002D2C60`
can reach presentation creator `FUN_002D2DC0` under primary action-timer
gates. This inspected constructor/callback path does not construct the
ID `0x3F` playback/timer family described above.

ID `0x4C` constructor `FUN_002D42D0` installs table `0x005DA540`,
constructs two `0x1C`-byte records at `+0x4F08` and calls
`FUN_002D46A0`. That setup walks 17 named bone definitions at
`0x005C3D60`, can allocate `0x60`-byte geometry objects and substitute
bone `+0x9C`, preserving the prior pointer in fighter-local records.
Cleanup `FUN_002D4910` destroys those owned geometry objects and restores
nonnull saved pointers. These are model/bone ownership paths, not evidence
that playable `0x4B/0x4C` are aliases for ID `0x3F`'s controlled auxiliary
playbacks. General bone mechanics belong to
[model runtime](../runtime/model_runtime.md).

## Primary dispatch and subordinate update order

**Observation, high confidence:** Callback dispatch through `FUN_00217670`
follows the [common contract](../game/character_assets.md#per-character-code)
and passes the original primary fighter pointer. The four default character
definitions point to these resident tables:

| Primary ID | Definition's `+0x1C` table | Channel 2 | Channel 3 | Channel 5 |
| --- | --- | --- | --- | --- |
| `0x12` | `0x00458770` | `0x0026A9B0` | `0x0026AD30` | Null |
| `0x3C` | `0x004E6930` | `0x002A39E0` | `0x002A4060` | `0x002A49A0` |
| `0x3E` | `0x004F1A90` | `0x002ADC50` | `0x002ADE20` | Null |
| `0x3F` | `0x004F7BA0` | `0x002B2BC0` | `0x002B2C30` | Null |

Their default channel 1/6/7 pointers are null. This is an inventory of
these definitions, not of every configured-jutsu replacement. The primary
per-action dispatcher `FUN_00249640` invokes channels 2 and 3 before its
common major-state work. Character callbacks inspect primary action/phase
timers and may manipulate subordinate presentation state; they are not
separate callbacks attached to independently registered puppet nodes.

**Observation:** `FUN_002504B0` calls the action/list pass
`FUN_0024FD80`, removal maintenance, then `FUN_00250230`.
The last routine walks surviving primary fighters first through
`FUN_0024D3C0`, then their virtual slot `+0x20`, then channel 5.
The puppet classes override slot `+0x20` with the ordinary update wrappers
documented above. The lower generic node pass uses `FUN_0024DA50`, whose
completion sets byte `+0x61` bit 4 for an active fighter. Later phase-2
submission `FUN_0024DD70` calls the class's slot `+0x28`; its puppet wrapper
performs playback/movement work only when that bit is clear. Therefore
reaching both wrappers does not by itself prove two subordinate advances.
The complete session order belongs to
[battle lifecycle](battle_lifecycle.md#what-phase-2-guarantees).

The late common callback `FUN_0024DE40` processes primary attack banks
before calling the class's slot `+0x2C`, which reaches the puppet attack
bridge. This ordering matters: the bridge operates on the same primary
bank state, checking `FUN_0021FC40` before each redirected bank.

## Root movement remains coupled to the primary

**Observation:** The following character-local blocks use matching root
position/target fields; the listed consumers and resetters establish their
ownership independently of the animation-provider arrays.

| Primary ID | Motion block(s) | Root consumer | Reset routine |
| --- | --- | --- | --- |
| `0x12` | `+0x4FB0` | `0x00266CA0` | `0x002665D0` |
| `0x3C` | `+0x4FF4`, `+0x5258` | `0x0029FEB0` | `0x0029F6A0` |
| `0x3E` | `+0x56BC`, `+0x5950` | `0x002AA3D0` | `0x002A9D00` |
| `0x3F` | `+0x4DF8` | `0x002AFBE0` | `0x002AF580` |

| Motion-block offset | Confirmed use |
| --- | --- |
| `+0x00/+0x04` | Dimensions derived through `FUN_002163A0/002163C0` from primary dimensions and scale. |
| `+0x08..+0x10` | Cached XYZ position, with sentinel `0xC6875104` after reset. |
| `+0x14` | Root-motion mode; a nonzero value enables the root consumer. |
| `+0x18/+0x1C/+0x20/+0x24` | Previous X, current X, target X and authored interpolation parameter. |
| `+0x28/+0x2C/+0x30/+0x34` | Previous Z, current Z, target Z and authored interpolation parameter. |
| `+0x3C/+0x40` | Vertical delta and its per-eligible-call decrement parameter. |
| `+0x44` | Stored Y component of the previous-position vector. |

The resetters clear `0x19` words (`0x64` bytes), restore dimensions and
the cached-position sentinel, and clear the preceding scene-query result
field. Some also reset a separate deformation block; that block is not
another playback/timer record.

**Observation:** The outbound initializers `FUN_00266790`,
`FUN_0029F8C0`, `FUN_002A9EC0` and `FUN_002AF6D0` choose the current
subordinate position when its cache is valid, otherwise the primary position.
They derive a destination through `FUN_0021CC00` using linked fighter
`+0x20` and a scaled authored offset, set mode 1 and initialize both axes.
Related mode-2 and return helpers can instead choose primary-relative
destinations. The event gates which select these helpers are primary timers
`+0x1B8/+0x1DC`, normalized action and phase.

In the root consumers, positive primary `+0x20C` preserves the current
interpolation position. Otherwise each enabled axis calls `FUN_00180CE0`
with primary step `+0x1AC` divided by its stored interpolation parameter.
That helper implements `current += (target-current) * factor`; these
stored parameters therefore control convergence per eligible call.
The consumer passes previous/proposed positions and dimensions to
`FUN_0021C640(dimensions, primary, previous, proposed)`, then queries the scene through
`FUN_001BF100(..., 0x20000001, 1, 0, -1)`. A `-1.0` result clears the
preceding result field; another result stores global `0x0061F6E8` there.
When the query returns `-1.0` and the primary gate is clear, vertical delta
decreases by `3 * block[+0x40]` and is added to Z. Otherwise Z takes the
query endpoint and vertical delta becomes zero. The resulting position
is written into the subordinate playback with primary rotation and scale.
These are explicit local movement fields using the primary collision/query
context; they do not establish a separate fighter movement dispatcher.
General query semantics belong to [collision](collision.md).

## Linked presentation helpers

**Observation:** `FUN_002109F0` owns a linked list of allocated `0xE0`-byte
nodes, each built by `FUN_0020ED00`. Node `+0x00/+0x04/+0x08` borrow an
authored definition, primary fighter and subordinate playback. Four names
at definition `+i*0x1E` resolve through primary resource container `+0xE6C`.
Definition `+0x7A/+0x7C` controls sample allocation and subdivision;
the node owns the buffer at `+0x1C` and uses `+0xD0` for the next node.

For Classic Kankuro, the first definition at `0x0045CFF0` names primary
`OBJ_2cmn00t0 r clavicle` / `r finger0` and puppet
`OBJ_2krs00t0 l finger0` / `l clavicle`. `FUN_00210730` visits each
node through `FUN_0020FFA0`, which expires older samples, adds a new
sample through `FUN_0020FE90`, smooths sampled positions and multiplies
sample alpha by subordinate playback `+0x88`. `FUN_002107B0` submits
segmented geometry through `FUN_002103C0/0020FB00` and packet routine
`FUN_002088B0`. `FUN_00210830` instead resets node samples through
`FUN_0020EE40`; it is not a playback advance.

**Inference, high confidence:** The named primary/puppet attachments and
segmented, fading presentation support identifying these helpers as the
puppet-string/trail presentation family. This does not establish which
sample configuration is visibly active in every action. Their inspected
allocation and cleanup do not own an input object or primary battle slot:
`FUN_00210640` frees the owned sample buffer and each node, then the helper,
while leaving the borrowed fighter/playback pointers to their owners.

### Published definitions and retained attachments

**Observation, high confidence:** Constructor calls supply definition arrays
directly; no action index selects a replacement array in the inspected helper
API. `FUN_002109F0` advances its definition pointer by `0x88` after each
successful node construction and appends the node to the helper's list.
Chiyo appends the same two definitions a second time with a different playback.
Sasori's helper retains the first playback even when attacks later select the
second. The definitions are resident borrowed data; sample reset does not
rebind them or the retained playback.

| Primary | Helper field | Definition starts / node count | Retained playback |
| --- | --- | --- | --- |
| Classic Kankuro `0x12` | `+0x5374` | `0x0045CFF0`, five consecutive entries | `+0x5114` |
| Kankuro `0x3C` | `+0x5620` | `0x004E6710`, two entries | `record[0]+0x78` (`+0x5598`) |
| Kankuro `0x3C` | `+0x5624` | `0x004E6820`, two entries | `record[1]+0x78` (`+0x5618`) |
| Chiyo `0x3E` | `+0x5CFC` | `0x004F1980`, two entries, appended twice | First pair `+0x5C68`; second pair `+0x5CE8` |
| Sasori `0x3F` | `+0x50EC` | `0x004F7A90`, two entries | `+0x4EF4` |

`record` in the Kankuro rows uses that character's `+0x5520+i*0x80`
layout. Successful construction yields 15 nodes from 13 distinct definitions,
rather than 15 different authored attachment configurations.

| Definition offset | Established consumer |
| --- | --- |
| `+0x00/+0x1E/+0x3C/+0x5A` | Four fixed 30-byte name slots; sampled in that order. |
| `u16 +0x78` | New sample's lifetime; reciprocal decrement for surviving sample fade. |
| `s16 +0x7A` | Pool slot count copied to node `+0x62`; allocation is count times `0x310`. |
| `s16 +0x7C` | Spatial point count copied to node `+0x64`; parameters are `i/(count-1)`. |
| `u16 +0x7E` | Extra temporal samples inserted between retained samples once at least four are active. |
| `float +0x80` | Curve tension used by the spatial BTL helper and resident temporal helper. |
| `+0x84` | Zero in these sampled definitions; no meaning established by the inspected consumers. |

All 13 definitions contain lifetime 4, pool count 8, point count 16 and
tension `-1.0`. Extra temporal count is 2 only at `0x0045D210`,
`0x004E6798` and `0x004E68A8`; it is zero in the other ten definitions.
Thus each selected node owns `8*0x310 = 0x1880` bytes. A sample has a
`0x10`-byte header followed by 16 `0x30`-byte point records. These are
capacities established for the published data, not a proof that arbitrary
definition counts are safe: the embedded parameter array also has room for
16 floats, and the inspected code does not clamp the authored counts.

**Observation:** `FUN_0020ED00` resolves every name against the primary's
resource container `+0xE6C`, retaining each result at node
`+0x0C/+0x10/+0x14/+0x18`. For each sample, `FUN_0020F170` prefers that
cached pointer. Only a null cached pointer invokes
`FUN_001BAB40(retained_playback, name, 1)`; this result is local and is
looked up again on later samples. If both lookups fail, the function uses
the retained playback's root matrix translation. There is no missing-name
rejection in this producer. The fallback's existence does not establish
whether any shipped action reaches it; name presence and actual lookup
success in every relevant resource/pose remain unmeasured.

The complete named configurations below preserve slot order. Each primary
suffix completes `OBJ_2cmn00t0 `; each auxiliary suffix completes the listed
prefix plus a space. "Prefix alone" denotes the exact name without a suffix.

| Definition | Primary suffixes `P0 / P1` | Auxiliary prefix | Auxiliary suffixes `P2 / P3` |
| --- | --- | --- | --- |
| `0x0045CFF0` | `r clavicle / r finger0` | `OBJ_2krs00t0` | `l finger0 / l clavicle` |
| `0x0045D078` | `l clavicle / l finger0` | `OBJ_2krs00t0` | `r finger0 / r clavicle` |
| `0x0045D100` | `r forearm / r finger0` | `OBJ_2krs00t0` | `l calf / l foot` |
| `0x0045D188` | `l forerarm / l finger0` | `OBJ_2krs00t0` | `r calf / r foot` |
| `0x0045D210` | `r forearm / r hand` | `OBJ_2krs00t0` | `head01 / spine` |
| `0x004E6710` | `l forearm / l finger0` | `OBJ_2krs00t0` | `l calf / l foot` |
| `0x004E6798` | `r forearm / r hand` | `OBJ_2krs00t0` | `head01 / spine` |
| `0x004E6820` | `l forearm / l finger0` | `OBJ_2kar00t0` | Prefix alone / `bone13` |
| `0x004E68A8` | `r forearm / r hand` | `OBJ_2kar00t0` | `head / bone01` |
| `0x004F1980` | `l clavicle / l finger0` | `OBJ_2kgt00t0` | `l hand / l forearm` |
| `0x004F1A08` | `r clavicle / r finger0` | `OBJ_2kgt00t0` | `r hand / r forearm` |
| `0x004F7A90` | `r clavicle / r finger0` | `OBJ_2kkg00t0` | `l hand / l forearm` |
| `0x004F7B18` | `l clavicle / l finger0` | `OBJ_2kkg00t0` | `r hand / r forearm` |

Classic Kankuro definition `0x0045D188` literally spells its first
attachment `OBJ_2cmn00t0 l forerarm`. This spelling is confirmed data,
without a claim that the resource lookup fails.

**Evidence:** resident constructor calls at `0x00265C98`,
`0x0029EBAC/0029EBE4`, `0x002A9020/002A9044` and `0x002AEBA8`;
complete constructor decompilation and definition-byte ranges
`0x0045CFF0..0x0045D297`, `0x004E6710..0x004E692F`,
`0x004F1980..0x004F1A8F`, `0x004F7A90..0x004F7B9F`;
attachment instructions `0x0020F1D0..0x0020F2DC`.

### Pool reuse, expiry and smoothing

**Observation:** Node `s16 +0x60` counts linked active samples; `+0x20`
is newest and `+0x24` oldest. Sample header `s16 +2` is remaining lifetime,
`float +4` is fade, and `+8/+0x0C` point toward newer/older samples.
`FUN_0020EFE0` chooses the first pool slot with zero lifetime and increments
active count. If none exists it detaches/reuses the oldest slot without
increasing count. It initializes fade to 1, clears point projection-cache
bits and regenerates point colors with parameter `t_i=i/(N-1)`; the new
point alpha is the integer conversion of `128*t_i`, clamped to a byte by
`FUN_00208280`. `FUN_0020FE90` prepends the new slot, writes lifetime 4,
and computes its points. This is reuse of fixed storage, not an allocation
per update.

For each call to `FUN_0020FFA0`, the operations are ordered as follows.

1. Visit the previously active samples, decrement lifetime by one, unlink
   and mark a slot free when the result is nonpositive. A surviving sample
   instead updates `fade = max(0, fade - 1/L)`, using definition lifetime
   `L`, not playback speed or a timer increment.
2. Insert one current sample and, where requested, temporal samples.
3. For point `i`, hold the newest sample's XYZ as target `H_i`. Every older
   active sample independently updates
   `P_i += (H_i-P_i)*(1-sin(pi*i/(N-1)))`. The target is not advanced to
   the preceding older sample; this is not a cascading average. Point
   projection-cache bit 0 is cleared after smoothing.
4. Overwrite each point's alpha byte with the integer conversion of its
   **currently stored alpha** times sample fade times retained playback
   `float +0x88`, preserving the low 24 color bits. Therefore repeated
   updates compound alpha attenuation; they do not recalculate it from
   the original `128*t_i` each time.

The newest sample is not smoothed in step 3. With the shipped lifetime 4,
an ordinary sample can survive insertion and three subsequent eligible
updates, then expires before the fourth new insertion. Draw admission is
separate. This is an update-call lifetime, not a measured number of display
frames. Pool reuse and temporal insertion can shorten a particular slot's retention.
`FUN_00210830 -> FUN_0020FF80 -> FUN_0020EE40` clears sample lifetimes,
links and active count and regenerates parameters/colors; it preserves
the node's definition, cached attachments, borrowed owner/playback and
deformation fields.

**Evidence:** decompilation of `FUN_0020EE40/0020EFE0/0020FE90`;
complete update instructions `0x0020FFA0..0x002103BC`, particularly the
held target at `0x00210170`, older-sample loop
`0x00210190..0x00210228`, and stored-alpha read/write at
`0x002102AC..0x00210358`. The sine/cosine identities are supported by the
polynomial kernels `FUN_0016DD28/0016D370` and their quadrant wrappers
`FUN_0016F2E8/0016EFB8`.

### Spatial curve and temporal subdivision equations

Let `H00=2t^3-3t^2+1`, `H10=t^3-2t^2+t`,
`H11=t^3-t^2`, `H01=-2t^3+3t^2` and `s=(1-tension)/2`.
The spatial producer passes the four sampled/modified attachments as
`P0/P1/P2/P3` to live BTL `0x00706FF0` (preserved `0x00706FB0`),
with `t=i/(N-1)` and definition tension `-1`, hence `s=1`.
Its curve is

```text
C(t) = H00*P1 + H10*s*(P2-P0) + H11*s*(P3-P1) + H01*P2
```

It forces W to 1, then adds
`sin(pi*t/2)*FUN_00180350(5.0,1.0)` to Z for each point.
The random-number owner is [Randomness](../runtime/randomness.md);
this caller fixes the two arguments but does not establish a visible
amplitude distribution or reproducible sequence here.

**Observation:** Temporal subdivision `FUN_0020F8E0` snapshots the newest
four samples as `Q0/Q1/Q2/Q3`, then inserts the authored extra count `k`
between `Q1` and `Q2`. Its parameters are `t=j/(k+1)`, `j=1..k`.
The insertion positions use the original four snapshots even as the list
changes. Its resident scalar helper `FUN_00208360` has a different first
tangent:

```text
D(t) = H00*Q1 + H10*s*(Q1+Q2-2*Q0) + H11*s*(Q3-Q1) + H01*Q2
```

This difference is in the instructions: the scalar helper subtracts the
first point twice at `0x00208390/002083C4`, while the spatial vector
helper subtracts the first and then the second point. The two helpers
therefore do not share the same tangent formula. Inserted samples set header
bit 0 and get lifetime
`convert(max(1, prev_lifetime - t*(prev_lifetime-Q2_lifetime)))`.
Here `prev_lifetime` belongs to `Q1` for the first insertion and to the
previous inserted sample thereafter; it is not held at the original
`Q1` value. Fade/color initialization comes from pool reuse, not
interpolation of the endpoint fade values.

**Evidence:** complete resident temporal instructions
`0x0020F8E0..0x0020FAFC` and scalar polynomial
`0x00208360..0x002084F4`; spatial caller
`0x0020F7D0..0x0020F894`; BTL instruction bytes
`0x00706FF0..0x0070717B` for the spatial helper's tangent subtraction,
weighted vector sums, W assignment and return.

### Action-produced curve deformation

**Observation:** `FUN_002108B0(amplitude, decay, helper, node, channel)`
sets node `+0x28=1`, resets selected phase `+0x30+4*channel`, and writes
amplitude at `+0x40+4*channel` and decay at `+0x50+4*channel`. Node `-1` selects all nodes;
the function caps an excessive node index at the last node and clamps
channel to `0..3`. The inspected character wrappers request channels 0 and
1. Decompiler signatures omit the first call's float arguments in several
wrappers; instructions show retained `f12/f13` at that call and explicitly
restore them for the second, so both channels receive the same pair.

Let `A0/A1` be the first two cached attachment translations and `A2/A3`
the last two, before modification. Each sample advances phases by
`pi/16`, `pi/32`, `pi/64` at node `+0x30/+0x34/+0x38`, wrapping to
`[-pi,pi]`. The inspected producer uses only the first two phases.
For nonzero envelope `q=+0x28`, it first moves `A0` toward `A1` and
`A3` toward `A2` with factor `q`. It then builds curve controls:

```text
U0 = normalize(A0-A1), with positive U0.z negated
U1 = normalize(A2-A3)
P0 = A1 + U0*(1+sin(phase0))*(amplitude0 != 0 ? amplitude0 : 50)
P1 = A1
P2 = A2
P3 = A2 + U1*cos(phase1)*(amplitude1 != 0 ? amplitude1 : 50)
```

Each nonzero amplitude then moves toward zero by its own stored decay
factor through `FUN_00180CE0`, and is cleared when the result is below 1.
The nonzero envelope independently moves toward zero by factor `0.25`,
so `q_next=0.75*q` per produced sample. Sample reset leaves these fields
untouched. The equations specify the observed operations; zero-length
normalization and resulting visible geometry are not established for every
attachment/pose combination.

**Concrete producer:** Classic Kankuro channel 2 (`FUN_0026A9B0`) in
major state 0, minor state 3 checks each node's channel-0 amplitude below
50 and requires `FUN_00180210(1)==0`. It sets both channels to
`300+FUN_001802B0(100)` and decay
`0.05+FUN_001802B0(0.025)`. Kankuro `0x3C` channel 2
(`FUN_002A39E0`) uses the same numeric predicate and pair, with each node's
decision taken from the first helper. An accepted decision applies to the
corresponding node in **both** nonnull helpers whose associated record
result is not 3. Thus the second puppet does not make an independent random
deformation decision in this callback. The signed-scaled RNG semantics
remain with [Randomness](../runtime/randomness.md#mt-wrappers).

Chiyo's root-motion producer supplies a distinct deterministic event lead.
At normalized selector `0x2A`, phase 0, timer `+0x1DC` event 3
(`0x004F6DD0`) sets the routine's deformation request. Its shared final
block calls `FUN_002AD800(primary, -1)` for all four helper nodes, with
amplitude 400 if the current action pointer `+0xA4C` is null or its float
`+0x24` is zero; otherwise amplitude is
`300*(action_float/0.015)`. Decay is
`0.75/(fighter[+0x5710]/fighter[+0x1AC])`. This publishes curve controls
without replacing the definition or resetting the sample pool. Other
branches sharing the request block were not exhaustively assigned new
action-specific equations here.

The nonzero writer of `+0x5710` remains an open lead. It is motion block
`+0x56BC` offset `+0x54`, cleared by `FUN_002A9D00` along with the block.
The inspected outbound/mode-2/return initializers
`FUN_002A9EC0/002AA090/002AA2C0` do not assign that offset; neither do
the two playback-update wrappers `FUN_002AD910/002ADA80` or the default
channel-2/3 callbacks `FUN_002ADC50/002ADE20`. These bounded reads do not
establish the value used by every deformation request or how a zero
denominator is avoided.

**Evidence:** setter instructions `0x002108B0..0x002109E0`;
sample producer `0x0020F2F4..0x0020F7CC`; paired wrapper instructions
`0x0026A5B0..0x0026A628`, `0x002AD800..0x002AD878`,
`0x002B1ED0..0x002B1F48`; Classic/Kankuro channel-2 instructions
`0x0026A9D8..0x0026AB08`, `0x002A3A08..0x002A3B80`;
Chiyo selector/event instructions `0x002AC85C..0x002AC91C`, request
argument instructions `0x002AD350..0x002AD3EC` and event bytes
`0x004F6DD0..0x004F6DD3`; Chiyo reset/initializer/update/default-callback
decompilation for the bounded `+0x5710` writer search.

### Draw admission, update and reset remain separate

**Observation:** The four setup routines enable bit 1 in character-local
flags through small setters. Their constructors first clear that bit.
The inspected presentation callbacks use it as their common outer gate:

| Primary | Flag field / setter | Helper presentation callback |
| --- | --- | --- |
| `0x12` | `+0x4FA8`, `FUN_00266570` | `FUN_0026A7A0` |
| `0x3C` | `+0x4FEC`, `FUN_0029F640` | `FUN_0029F2A0` |
| `0x3E` | `+0x56B4`, `FUN_002A9CA0` | `FUN_002A97A0` |
| `0x3F` | `+0x4DF0`, `FUN_002AF520` | `FUN_002AF280` |

Inside that gate, helper **update** additionally requires primary byte
`+0x00` bit 1 and byte `+0x61` bit 5. Helper **submission** needs only a
nonnull helper after the outer gate. Kankuro `0x3C` also requires its
associated record result not equal to 3 for both operations. A closed
sample-update gate therefore does not by itself prohibit submitting retained
samples. Conversely, submission does not age, insert or smooth samples.
Sasori's helper still reads the first playback's alpha even when the
presentation callback separately submits the second playback.

The class's later presentation wrapper resets helper samples when primary
byte-0 bit 1 is set and byte `+0x61` bit 4 is clear, independently of
whether `+0x20C` suppresses its subordinate playback/movement work.
It then reaches the presentation callback above. Sasori also resets before
ordinary movement when `FUN_002508B0` returns nonzero; the inspected helper
returns 1 only for the global owner object's numeric states `+0x14==6`
and `+0x18==4`. No broader state name is assigned here. Classic Kankuro,
Kankuro and Chiyo attack bridges can reset samples while primary `+0x20C`
is positive and `+0x61` bit 6 is set; Sasori's inspected attack bridge has
no corresponding reset call. Generic scheduling and primary-flag ownership
remain with [scene playback owners](../runtime/scene_playback_owners.md#fighter-animation-ownership)
and [battle lifecycle](battle_lifecycle.md#what-phase-2-guarantees).

`FUN_002103C0` counts active pool slots and reserves space for
`4*active_slots*(N-1)+6` units of `0x20` bytes. A nonzero returned packet
pointer admits traversal of the active sample list, one segment per
adjacent point pair, and final submission. A failed reservation skips that
node's segments. Projection-cache bits are cleared before this traversal;
the draw function does not alter the sample remaining-lifetime count.
Shared packet ownership belongs to [render submission](../runtime/render_submission.md),
and view mathematics to [renderer coordinates](../runtime/renderer_coordinates.md).

**Evidence:** complete presentation disassembly at
`0x0026A7A0..0x0026A98C`, `0x0029F2A0..0x0029F3EC`,
`0x002A97A0..0x002A98D0`, `0x002AF280..0x002AF35C`;
setup enable bytes at `0x002661E0..0x002661EF`,
`0x0029F15C..0x0029F16B`, `0x002A965C..0x002A966B`,
`0x002AF064..0x002AF073`; reset-wrapper and
`FUN_002103C0/0020FB00/002508B0` decompilation. Teardown remains the owned
sample/node/helper cleanup documented above; these operations leave the
borrowed playback to the character's separate cleanup path.

## Attack results remain primary-owned

**Observation, high confidence:** The shared attack consumer
`FUN_0021FC70` and its scene/timer arguments are owned by
[Combat action execution](combat_action_execution.md#character-specific-scene-and-timer-selection).
For the puppet bridges, the selected subordinate playback supplies the
animation length (playback `+0x90 -> animation+0x0C`), speed `u16 +0x94`
and the lookup scene for the bank's node name, and the selected local timer
supplies the event window. The publication itself stays on the primary: the
bank word goes to primary `+0xC98 + bank*0x50`, the position to primary
`+0xCA0 + bank*0x50` with its Y component replaced by primary `+0x34`, the
registration under primary `+0xDF4`, and `FUN_00222A30(primary,
primary+0xA4C)` receives the primary's current record. A subordinate
scene/bone can therefore supply the spatial origin, but this does not
establish an independently damageable actor for either Chiyo or Kankuro's
scene.

## Shared local clock and primary gate

**Observation:** Resident `FUN_00224650` is exactly
`return *(s32 *)(fighter+0x20C) > 0`. The callbacks above use that primary
field to suppress normal advance and clear local timer flags bit 1 with
`FUN_00211F70`; the five instructions at `0x00211F70..0x00211F80`
preserve all positions and the remainder. Each local increment comes from
its clock-owning playback's unsigned 8.8 speed (`u16 +0x94 / 256.0`).
Sasori's one timer always reads the **first** playback `+0x4EF4`,
including attacks routed through second playback
`+0x5114`. `FUN_00211D80` adds that increment to a fractional
accumulator, carries complete units into its integer position, and updates
previous/current/next positions. The general timer contract belongs to
[timer primitives](../runtime/timer_primitives.md), and the census of
auxiliary-timer attack callers to
[Combat action execution](combat_action_execution.md#character-specific-scene-and-timer-selection).

**Inference, high confidence within these callbacks:** Separate puppet
playback, pose and local clocks permit action-relative motion and event timing.
The inspected path still derives dispatch from the primary's normalized
action, activity bit, `+0x20C` gate and current attack banks. Separate scene
allocation is therefore insufficient evidence of an independent fighter
controller or battle-registry slot. That wider negative has not been claimed.
