# Stage polygon and surface attributes

This document investigates the attribute word carried by retail NA2
(`SLPS-25837`) collision polygons, its authored source, and the consumers that
classify stage contact. Numeric predicates remain numeric unless evidence
establishes their meaning.

## Research coverage

- **Assigned scope:** native polygon/surface attribute producers, movement and
  query consumers, contact classification, and per-stage authored flags in
  unmodified retail NA2.
- **Exploration depth:**
  - Complete resident CCS hit-resource parser `0x001B3040..0x001B3448` and
    triangle attribute producer `0x001ABEB0..0x001AC230`, including the
    attribute-masking and orientation-threshold instructions.
  - Both environment-query walkers' attribute predicates; complete
    special-ground, jump, and footprint selectors.
  - The common fighter constructor/reset, a bounded contact-word writer/alias
    review, current-word effect overrides, effect-manager inputs, and
    selected character-specific readers.
  - Generated wire construction, attribute refresh, and teardown.
  - A structurally checked hit-block scan of all 24 stage archives.
  - Consumer coverage is bounded to these families, rather than a
    whole-program census.
- **Confirmed coverage:** batch-authored attributes become each triangle's
  low 29 bits; the high three bits are replaced by a normal-derived query
  class. Established distinctions include fighter versus generic query
  eligibility, constructor clearing and current versus retained ground words,
  temporary effect overrides, numeric contact/effect dispatch, effect-manager
  code inputs and row-mask selection, the 17-code footprint table, per-stage
  word counts, and the generated wire's additional `0x00D0D0` source.
- **Unresolved or untested:**
  - Complete consumer enumeration, original names of the masked codes,
    complete character-specific callback coverage, and the remaining low-bit
    meanings.
  - Any semantic consumer of cached stage-line `+0x2C`; the bounded census is
    in [Stages](stages.md#cached-line-attribute-consumers).
  - Whether an archive record's model is registered or enabled at every point
    in a battle.
  - Whole-fighter copying and `+0xBB8` writers through other computed aliases,
    beyond the bounded writer review below.
  - Effect-row descriptor replacement and resource availability.
  - The fighter query `FUN_00211420` and walker `FUN_00210D80` beyond their
    attribute predicate: their registry walk, distance selection, and result
    storage are not yet documented in [Collision](collision.md).
- **Deliberate exclusions and overlap:** generic collision geometry, the
  generic query, and result layout belong to [Collision](collision.md);
  movement state and arithmetic to
  [Movement and physics](movement_and_physics.md); stage lifecycle, line
  construction, and background effect variants to [Stages](stages.md); CCS
  object dispatch to [CCS object types](../game/files/ccs_object_types.md);
  surface-dependent SFX selection to
  [Battle audio](battle_audio.md#surface-dependent-sfx); HP arithmetic of the
  bit-`0x400` damage selector to
  [Battle damage](damage.md#damage-caller-coverage).
- **Evidence limitations:** static retail executable, overlay, and archive
  evidence can establish encoded predicates and data flow. It cannot by itself
  establish measured gameplay behavior, original enum names, or reachability
  of every possible input combination.

## Evidence conventions

Resident addresses need no shift. BTL addresses are labeled preserved, live,
or complete-file offset as defined in
[Retail game file identities](../game/files/file_identities.md#address-conventions);
encoded call and data operands are already live addresses.

## Authored word and geometric class

**Confirmed — source layout.** Resident `FUN_001B3040` reads a 16-byte
header from the CCS stream, resolves two resource indices, and constructs the
hit resource when the unsigned halfword at header `+8` is nonzero. Header
`+0x0C` is an integer total vertex count. For each of the header's batches it reads two `u32` words:
vertex count and attributes. The count is divided by three; nine floats per
triangle supply three XYZ vertices, followed by a second bank of the same
number of XYZ triples that is read but not used by this parser. One authored
word therefore applies to every triangle in that batch, rather than being
read separately for each triangle.

Instruction evidence is the two stream-word calls at `0x001B317C/0x001B3188`,
the saved attribute word at `0x001B3190`, and the load into `a3` at
`0x001B3228` immediately before triangle-builder call `0x001B3238`.
The parser packs all batch triangles into one runtime group: the group count
at aggregate `+0x1C` is one, and its triangle count is the total vertex count
divided by three. Authored batches are consequently not separate runtime
group-enable bits. General resource attachment belongs to
[CCS object types](../game/files/ccs_object_types.md#confirmed-identities).

**Confirmed — output equation.** `FUN_001ABEB0` constructs the geometric
cache and writes primitive `+0x0C` as:

```text
primitive_flags = (authored_word & 0x1FFFFFFF) | geometric_class
```

The `dsll32`/`dsrl32` pair at `0x001AC12C/0x001AC134` retains exactly the
low 29 bits. `or` at `0x001AC13C` and `sw` at `0x001AC148` combine and
store them as integer bits. The authored word cannot override the derived
top bits through this producer.

The builder derives a polygon normal, zeros its third component in a temporary
copy, computes that copy's magnitude, and calls `0x0016F4C0` with the original
normal's third component and the planar magnitude. Its downstream
`0x0016BCB0` has the quadrant/sign and arctangent structure supporting an
`atan2(n.z, sqrt(n.x*n.x+n.y*n.y))` interpretation. The encoded angle is the
low 16 bits of the integer conversion of
`((angle + pi) * 32768 / pi) - 32768`. The exact integer branches are:

| Encoded unsigned angle | Geometric class | Query role established by movement masks |
| --- | ---: | --- |
| `0x1C01..0x63FF` | `0x20000000` | Ordinary-axis downward contact selection |
| `0xA001..0xDFFF` | `0x80000000` | Ordinary-axis upward contact selection |
| Every other value | `0x40000000` | Ordinary-axis side contact selection |

The threshold instructions are `0x001AC0DC..0x001AC128`. Winding and normal
direction therefore matter independently of the authored low bits. These
classes describe the query selection contract; they do not establish an
original developer enum or guarantee every polygon is reachable by a fighter.

**Bounded call coverage.** `0x001ABEB0` has two recovered direct resident
callers: the CCS parser at `0x001B3238` and `FUN_003A8BE0` at
`0x003A8DA4`; no BTL direct reference was recovered. The latter resident
producer constructs generated wire geometry, traced below. These are the
recovered direct-reference sets, not a proof against computed callers.

## Attribute data flow

The [resident environment query](collision.md#resident-segmentenvironment-broad-and-narrow-phases)
copies primitive `+0x0C` into result `+0x48`, then publishes the winner at
resident `0x0061F6E8`.
Polygon attributes and the separate stage/position effect classifier have
distinct producers. A matching visual effect alone does not establish which
producer supplied its classification.

**Confirmed — current and retained contact words.** In resident movement
`FUN_0024A660`, instructions `0x0024B15C..0x0024B164` load the winning
polygon word from `0x0061F6E8` and store the same integer into fighter
`+0xBB4` and `+0xBB8`. The selectively passable branches clear current
`+0xBB4` at `0x0024B1D4` or `0x0024B238`; a nonzero special-ground
classifier return clears it at `0x0024B280`. Those branches leave `+0xBB8`
unchanged. The no-hit branch also clears `+0xBB4` at `0x0024B148` without
clearing `+0xBB8`. This establishes a retained selected word on these paths,
including a rejected ground contact. The constructor boundary below limits
that retention; bulk copying and other aliased writers are separately bounded.

**Confirmed — constructor reset.** The complete resident common fighter
constructor `FUN_002145D0` calls `FUN_00214A40` at `0x00214810`.
That reset explicitly clears side, current-ground, retained-ground, and
ceiling words: `sw zero,+0xBB0(s0)`, `sw zero,+0xBB4(s0)`,
`sw zero,+0xBB8(s0)`, and `sw zero,+0xBBC(s0)` at
`0x00215130..0x0021513C`. In particular, the retained word begins as zero
through this constructor; its movement retention does not imply persistence
through object reconstruction. The resident direct xref set for the reset
contains this constructor call, and the BTL direct xref set contains none.
This bounds direct callers, not computed dispatch or bulk copies. General
fighter creation and removal remain owned by
[Battle entities](battle_entities.md#primary-fighter-factory-and-lookup).

**Confirmed — temporary current-word overrides.** `FUN_0020A910` saves
the fighter's current `+0xBB4` at scratch record `+0xD8`, substitutes its
supplied attribute argument at `0x0020AA70`, invokes the effect selector
`FUN_0020A800`, then restores the saved word at `0x0020AB44`. It likewise
saves and restores the fighter position. `FUN_0020B000` has the same
save/substitute/select/restore pattern at `0x0020B6C0`, `0x0020B6D0`,
and `0x0020B7A0`, with a saved register holding the old word and scratch
record `+0xD8` supplying the replacement. Complete instruction bodies show
no retained `+0xBB8` write in either helper. These are temporary effect
inputs rather than new retained ground selections, and they prevent treating
every `+0xBB4` store as an update of both ground words.

### Bounded writer and alias coverage

**Confirmed within the operand search.** Aligned immediate `+0xBB8`
instructions in the resident program include exactly two stores, both word
stores: constructor zero at `0x00215138` and movement publication at
`0x0024B164`. The remaining decoded resident occurrences are the three
retained readers below and an unrelated integer constant in an effect loop.
The current `+0xBB4` word has eleven recovered direct stores, all covered
by four families above or in the query table: constructor clearing,
movement publication/clearing, the two temporary effect overrides, and
`FUN_0024A310`'s OR of a newly queried masked code at `0x0024A5B0`.
That OR changes current code only; it does not copy the full new primitive
word to either ground field.

Common post-constructor setup `FUN_002151E0` copies character-record
`+0x00..+0xD8` to fighter `+0x8C..+0x164`, rather than copying an
existing fighter's contact block. Its complete body, common cleanup
`FUN_00215720`, and common destructor `FUN_00214840` contain no direct
retained-word reset or reconstruction. Their object ownership remains in
[Battle entities](battle_entities.md#primary-fighter-factory-and-lookup).
This body-level observation does not exclude a callee or computed writer.

**Confirmed — other object layouts reuse the offset.** The BTL immediate
stores and quadword stores spanning numeric `+0xBB8` cannot be assigned
to the fighter merely by offset. The inspected families are:

| BTL instruction/body evidence, preserved addresses | Established use of the same numeric region |
| --- | --- |
| `0x00817560`; `0x0084162C`; `FUN_008424B0`; `FUN_0085A8E0`; scalar setter `0x0085B3F0` and resets `0x00859CB0/0x00859E88/0x0085B24C` | Auxiliary coordinate or velocity floats. `FUN_008424B0` instead stores its queried polygon code at `+0xC50`; `FUN_0085A8E0` uses separate code cache `+0xBC8`. |
| `0x00835BF4/0x00835FA4` and `FUN_00873930` store `0x00873974` | An owned animation/resource handle: allocation/initialization publishes it, and the latter destructor calls resident `0x001951A0(handle,1)` before clearing it. Its installed table is `0x005F8720`, followed by auxiliary-base destruction. |
| `0x0083B164`, `0x0083B5B4/0x0083B5C8`, `0x0083C51C` | Byte flag in the object's own parameter block, alongside byte `+0xBB0` and integer `+0xBB4`; these are not retained polygon-word stores. |
| Quadword stores `0x008172BC`, `0x0081C460`, `0x00829820`, `0x008414AC`, `0x00841618`, `0x0085B7AC` | Auxiliary vec4 initialization/copy/contact-position replacement at `+0xBB0..+0xBBC`. `FUN_00829810` copies the prior `+0xB10` position, then derives a midpoint using `+0xD40`; `FUN_0085B700` copies a corrected query position. |

The nearby-alias review covered address formation with offsets `+0xB80`,
`+0xB90`, `+0xBA0`, `+0xBB0`, `+0xBB4`, and `+0xBB8`, plus
direct stores starting at `+0xBB9..+0xBBB` and wider stores at
`+0xBB0/+0xBB4`. No resident spanning/partial store was recovered.
Resident address-forming candidates used independent buffers or static
addresses. BTL aliases additionally expose embedded records and vectors:
for example, preserved `0x007C5D4C` calls resident `0x0030E770` on an
auxiliary's `+0xB90` animation object; that constructor's `+0x28` float
write lands at the owner's numeric `+0xBB8`. Its complete reset
`FUN_0030E8D0` again writes float 1.0 there. This is a concrete aliased
write in a different layout, not fighter contact reconstruction.

No additional fighter retained-word writer was established by these local
traces. Other address constructions, virtual callees, whole-object copies,
and programs beyond the resident executable and BTL were not exhaustively
followed. The confirmed lifetime claim is therefore constructor zero followed
by retained movement selection, rather than a proof of only two writers
throughout the game.

The movement publication supplies the contact code consumed by the airborne
recovery branch documented in [Hit response](hit_response.md#response-exits-contact-stages-and-downed-handoff)
and the wire reaction's `+0xBB8` matching predicate documented in
[Stages](stages.md#animated-and-breakable-background-evidence). It does not
establish an original name for the field.

## Query eligibility and contact classes

**Confirmed — distinct selection contracts.** The generic resident query
`FUN_001BF100` uses triangle walker `FUN_001BF8C0`. Each of its two mask/mode
pairs must pass the following integer predicate against primitive word `F`:

| Mode | Accepted predicate for mask `M` |
| ---: | --- |
| `0` | `(F & M) != 0` |
| `1` | `(F & M) == M` |
| `2` | `(F & M) != M` |
| `3` | `F != M` |
| Any other value | No restriction from that pair |

The integer instructions at `0x001BFB28..0x001BFC54` establish the
predicates. Zero mask with
mode `0` rejects every triangle; zero mask with mode `1` passes that mask
pair for every triangle. Mode `-1` is the unrestricted choice used by
inspected callers.

The fighter query `FUN_00211420` uses the separate walker `FUN_00210D80`.
At `0x00210F20..0x00210F64` it first requires `F & 1`, then accepts any
overlap with the requested mask when its mode is zero, or requires all mask
bits for every nonzero mode. It has no second independent mask pair. Thus
the geometric high class alone is insufficient for ordinary fighter contact:
authored bit `1` must also survive into the primitive word. The two queries
publish the same chosen-word location `0x0061F6E8`. [Collision](collision.md)
documents the generic query's registry, geometry, and result storage; the
fighter query's are not yet documented there.

**Confirmed — low-bit and code consumers.** The following predicates read
attributes after query selection; they are not additional geometric classes:

| Consumer | Attribute selection | Established consequence / boundary |
| --- | --- | --- |
| `FUN_0022DC10` | side flags `fighter+0xBB0 & 0x100` | Permits the documented aerial entry to surface-axis states after its axis/input-duration gates. |
| `FUN_0022D6C0` | generic query `(0x40000001, mode 1)` followed by winner `& 0x100` | Retains surface-axis eligibility; a missing query substitutes `0x100` and also retains eligibility. |
| `FUN_0022F3D0` | side flags `fighter+0xBB0 & 0x100`, side-contact bit, and contact side different from desired direction | Sets wall-jump byte `+0x9B8` mask `0x04` after its direction handling; absent qualification clears it. |
| `FUN_0022FAD0` | grounded bit and ground flags `fighter+0xBB4 & 0x800` | Doubles the first-jump height input at impulse initialization. This does not double the resulting speed or establish a measured apex. |
| `FUN_002312B0` | side `+0xBB0` for response `0x42/0x43`, ceiling `+0xBBC` for `0x44`, current ground `+0xBB4` for `0x45..0x47`, each tested with `& 0x400` | Selects raw damage input `0.04` instead of `0.02` through calculator flags `0x122`, after the contact-entry gates. Response `0x48/0x49` does not set this selector. HP arithmetic is owned by [Battle damage](damage.md#damage-caller-coverage); the only stage word carrying bit `0x400` is listed under [Stage-authored attribute distribution](#stage-authored-attribute-distribution). |
| `FUN_00249D70` | ground flags `fighter+0xBB4 & 0xF0F0F0` | Classifies `0x00D0D0 -> 3`, `0xE0A000 -> 2`, and either `0x202020` or `0xE0E000 -> 1`; every other code remains zero. Only classes 1 and 2 take its special contact handling. |
| `FUN_0024A310` | fresh downward fighter query, then the same four-code classification | Only class 1 changes contact-phase bits and invokes the extra descent/contact path. It ORs the queried masked code into existing `+0xBB4` rather than replacing the entire word. |
| `FUN_0033AA10` | code `0xE0A000` or `0xE0E000` | Calls `FUN_0033AF40(fighter,0)` when the supplied integer cursor is divisible by 15. Other codes have no such call in this helper. |

The complete special-ground classifier `0x00249D70..0x0024A300` also has
state, battle-sequence, attack, and fighter-resource gates. Code class 2 always
returns zero to its caller; class 1 can return one and enter the separate
contact descent helper. Therefore a matching code alone does not establish
that ordinary grounding is rejected. Detailed response exits belong to
[Hit response](hit_response.md#response-exits-contact-stages-and-downed-handoff),
and the motion state paths belong to [Movement and physics](movement_and_physics.md).
No material or terrain names are inferred from the repeated color-like bytes.

## Effects reached from polygon codes

Masked polygon codes also select common SFX events through
`FUN_001D53F0` and `FUN_001D5690`; their complete maps are owned by
[Battle audio](battle_audio.md#surface-dependent-sfx).

### Retained-word consumers

**Confirmed — response/effect readers.** The resident direct `+0xBB8`
loads outside movement are `0x00205128`, `0x0023570C`, and `0x002363D4`.
All three mask the retained word with `0xF0F0F0`, independently of the
current `+0xBB4` value:

| Reader | Retained-code consequence |
| --- | --- |
| `FUN_00204610`, major 6 / substate `0x61`, after `FUN_00211A20(fighter+0x1B8,0)` succeeds | Codes `0xE0E000` and `0xE0A000` suppress its `FUN_001D87C0` sound call. Other codes take that call. |
| `FUN_00235690`, airborne substate `0x5D` with byte `+0x61` bit 3 set | Codes `0x202020` and `0xE0E000` retain the recovery state; other codes take its ordinary-response handoff. |
| `FUN_00235C60`, substate `0x61`, after its animation-entry predicate | Codes `0x202020`, `0xE0E000`, and `0xE0A000` suppress the paired `FUN_0024C370` / `FUN_0024C230` calls in this branch. Code `0x00D0D0` does not suppress them. |

The response machine and complete surrounding gates belong to
[Hit response](hit_response.md#timed-downed-recovery-and-get-up-choices);
the first reader's cue is listed in
[Battle audio](battle_audio.md#fighter-action-cue-production). These readers support retained-code behavior after current contact has gone
away; they do not refresh the retained word themselves.

**Confirmed — `ccSkillTMR001` associated-fighter readers.** Two complete
BTL helper bodies begin at preserved/live/file
`0x007BB190 / 0x007BB1D0 / 0x1072D0` and
`0x007BB360 / 0x007BB3A0 / 0x1074A0`. Each starts with code zero and only
loads `owner[+0x4CC]->+0xBB8 & 0xF0F0F0` when owner byte `+0x539` is
nonzero and resident `0x003083A0(owner[+0x4CC])` succeeds. The instruction
bytes of resident leaf `0x003083A0..0x003083C8` establish its precise gate: argument nonnull and global `gp-0x339C` nonzero. It does
not query collision or inspect the associated fighter's contents.

The first helper emits no object for codes `0x90B0C0`, `0xE0A000`,
`0x202020`, or `0xE0E000`. Every other code, including the substituted zero,
creates two objects through `FUN_00349BA0` using the two resident data pairs
`0x005B83C0/0x005B8400` and `0x005B8460/0x005B84A0`, then applies each
object's setup/registration calls. This default branch separately obtains a
stage/position effect-variant column and stores `column+0x22` at object
`+0x228`; that column is the independent classifier owned by
[Stages](stages.md#background-classifier-and-slot-specific-objects).
The polygon code selects whether this branch runs, rather than supplying its
stage-variant column.

The second helper leaves live BTL word `0x008AF6B0` unchanged for
`0xE0A000`, `0x202020`, and `0xE0E000`, while calling resident
`0x00345B20` for its stage-dependent scalar. Code `0x90B0C0` writes
selector `0x72`; every remaining code writes `0x70`. The scalar is placed
in scratch storage and not used afterward in this body. These are numeric
effect/selector distinctions; a player-facing move name or terrain label is
not established.

The class join uses constructor bytes at preserved `0x007B9340..0x007B93D8`
and destructor `FUN_007B93F0`, both installing resident vtable
`0x005F7C90` at owner `+0x110`. That table's RTTI descriptor is live BTL
`0x008CFF38` (preserved `0x008CFEF8`), pointing to live string
`0x008BC348` (preserved `0x008BC308`), exactly `ccSkillTMR001`.
Its slot `+0x100` points to live `0x007B9950` (preserved `0x007B9910`),
which dispatches owner state `+0x1004`. The state-0 body calls live
`0x007BA010(owner,1)` at preserved `0x007BA3D0`; that state-entry helper
calls the first retained-code helper at preserved `0x007BA1A0`.
The state-1 body calls the second helper at preserved `0x007BA618` when
the old `+0x100C` counter has low two bits equal to three. This connects
both readers to the installed class methods, independently of nearby names.
The retained loads, predicates, object creation, and selector stores above
come from the complete instruction bytes `0x007BB190..0x007BB464`, including
the continuation after the Boolean leaf. Neither helper writes the associated fighter's
retained word. This is a bounded class-specific trace, not a complete skill
callback census.

### Effect-manager code inputs

**Confirmed — a separate shared code word.** Resident `FUN_00308DC0`
handles event type `0x8002` by publishing supplied fighter `+0xBB4 &
0xF0F0F0`, or zero for a missing fighter, to effect manager
`gp-0x3300 -> +0x3154` (`iGpffffcd00`). Instruction `0x00308E54`
stores it before the effect dispatch. At the end of the helper,
`0x00308FA4` writes `0xF0F0F0`, including on paths with another event
type. It does not restore an earlier manager value or write fighter
`+0xBB8`. The grounded response-`0x41` branch in `FUN_00233870`
likewise publishes current ground code, calls `FUN_00338990`, and resets
the manager word to `0xF0F0F0` at `0x00234034/0x00234050`.

Character callback `FUN_002EE660`, action `0x2C` / phase 2 after its
animation predicate, publishes current ground code at `0x002EF498` and
calls `FUN_00338B70`. Its complete body has no paired reset of the manager
word. Manager setup `FUN_0030C710` clears it at `0x0030C918`.
These distinct lifetimes prevent treating this shared effect input as another
retained fighter contact field. This is the bounded direct-store set for
immediate `+0x3154` in the two inspected programs; computed or aliased
manager writes are not excluded.
The final `0xF0F0F0` value is itself a recognized code in
`FUN_00338B70`, reaching its ordinary numeric effect/sound branch;
it cannot be treated as an unused value merely because dispatch writes it
afterward.

`FUN_0033FC50` uses a supplied fighter's current `+0xBB4`, or this manager
word when its fighter argument is null, masks the result, and calls
`FUN_0033FA00`. That selector creates its numeric pooled-effect branch for
`0x90B0C0`, calls `FUN_0033ADA0` for `0xE0A000` or `0xE0E000`, and
has no selected branch for other codes. `FUN_00338B70` and
`FUN_0033BB40` also read the manager word; effect-manager dispatch
`FUN_0030CCF0` passes it to `FUN_0033B540` for event `0x25` and
`FUN_0033C770` for `0x29`. Thus an effect helper without a fighter-word
load can still consume polygon-derived code through the shared manager.

**Confirmed — effect-row masks use containment.** Resident
`FUN_0030C4A0` walks 20 descriptor slots at `0x005A3280`. For each
available named resource it resolves the configured animation record,
copies the remaining three words of each 16-byte source row to manager
`+0x2F0 + index*0x10`, and stores the row count at `+0x3F0`.
The three complete consumers select the first row satisfying:

```text
kind_bit = fighter[+0xB00] == 0 ? 2 : 1
code = selected_contact_word & 0xF0F0F0
(row[+4] & kind_bit) == kind_bit
(row[+8] & contact_bit) == contact_bit
(row[+0x0C] & code) == code
```

`FUN_00338990` and `FUN_00339040` use current ground `+0xBB4`
and contact bit 1; `FUN_0033B8F0` uses side contact `+0xBB0` and
contact bit 2. Instructions `0x00338A30..0x00338A60`,
`0x00339114..0x00339144`, and `0x0033B9A8..0x0033B9D8`
corroborate the three predicates. A mask can accept more than one code,
and code zero passes the final predicate. No match selects record ID zero;
a nonzero selected ID reaches the manager's pooled animation setup.

The static initial descriptor array has only slot 0 nonnull. It points to
`0x005C7C80`, naming `s01.ccs` and one row at `0x005C7C70` for
`ANM_st01_bom_00`, with kind mask 0, contact mask 1, and code mask
`0x003060`. That row's zero kind mask fails both kind choices above;
its presence alone therefore does not establish an emitted effect.
The resource lookup's success and any replacement of these descriptor
slots remain unresolved. These row predicates are distinct from both query
eligibility and the footprint table's exact code comparisons.

The manager readers also preserve helper-specific differences. Inside
`FUN_0033BB40`'s `0x202020` / `0xE0E000` branch, a nonzero third
argument permits `FUN_0033AB10`; its variant is selected by
`(manager[+0x3154] & 0x202020) != 0`, not by equality with `0x202020`.
Both admitted codes pass that bit test and choose variant 3. In contrast,
`FUN_00338B70` chooses variant 3 only for exact `0x202020` and variant
0 for `0xE0E000`. Instructions `0x0033BCD8..0x0033BCF4`
corroborate the former bit test. A shared mask or similar effect helper
therefore does not establish identical dispatch semantics.

**Confirmed — bounded character/current-word selection.** Four complete
resident readers use the same numeric ground-effect choice after their own
action/animation gates: `FUN_0025EC50`, `FUN_0026FAA0`,
`FUN_00287F50`, and `FUN_002E8880`. All mask current `+0xBB4`
with `0xF0F0F0`; their selected branch is:

| Current masked code | `FUN_001D8A30` first / third arguments |
| --- | --- |
| Zero or `0x00D0D0` | Suppresses this sound/effect branch and its paired ground-effect calls |
| `0xE0A000` or `0xE0E000` | `0x49 / 0x40` |
| `0x0060C0` | `0x21 / 0x3C` |
| Every remaining code | `0x25 / 0x3C` |

The first reader requires definition ID `0x0E`, while the fourth requires
`0x51`; each accesses the fighter through its owner's `+0x64`. Their
complete instruction bodies establish the code/default distinction at
`0x0025ED28..0x0025EE40` and `0x002E8978..0x002E8A90`.
Their animation gates and placement differ, so a code match alone does not
cause emission. This is a bounded reader family, not a complete callback
census or an assignment of original material names.

### Current-word activation

**Confirmed — class-specific activation.** In `FUN_00249D70`, class 2
(`0xE0A000`) reaches `FUN_0030B300` outside major states 2, 3, and 6.
Class 1 (`0x202020` or `0xE0E000`) reaches the thin wrapper
`FUN_0033A9E0 -> FUN_0030B3F0` in major states 0 or 1 when fighter byte
`+0x63` bit `0x10` is clear. Each helper resolves or creates a per-side
effect object and sets its activation byte. Their constructors and RTTI
establish the following identities:

| Activation helper | Constructor / vtable | RTTI descriptor / name bytes | Activation field |
| --- | --- | --- | --- |
| `0x0030B300` | `0x00315100 / 0x005DC620` | `0x005C8AF0 / 0x005A6418`, `ccEffWash` | effect `+0x40 = 1` |
| `0x0030B3F0` | `0x00317320 / 0x005DC590` | `0x005C8A98 / 0x005A63D0`, `ccEffLeakChakra` | effect `+0x5C = 1` |

The first helper excludes fighter definition ID `0x4C` (76), identified as
Sasori (Hiruko) by [Character IDs](character_ids.md). The second helper
requires fighter float `+0x6C != 0`; it does not check current chakra
`+0x70`. These are specific activation gates, not a complete character
exception census. The RTTI names establish internal effect names without
identifying the polygon code's original terrain or material label.

`FUN_0033AA10` has the separate periodic call listed above. Its target
`FUN_0033AF40(fighter,0)` derives placement from the fighter transform and
reaches `FUN_0033ADA0`, which acquires an effect through the manager's
`+0x41C` pool and calls `FUN_0030F610(effect,0x21,0)`. No original effect
name is established for that numeric argument.

The class-1 contact path also conditionally debits the current chakra float
at fighter `+0x70`, lower-clamps it to zero, and writes `15.0` to `+0x1A0`
(`0x0024A248..0x0024A280`). It uses polygon-derived ground codes; no
input-history field feeds its initial classification. Resource fields and
the wider spend contract belong to [Chakra and guard](chakra_and_guard.md).

## Footprint surface selection

**Confirmed — complete selector table.** Resident `FUN_003A6CC0` masks
the selected polygon word with `0xF0F0F0`, then checks the 17 bits enabled
in its owner's `+0x28` selection mask. It returns true if any enabled bit's
code matches. The recovered table is:

| Selection bit index | Required masked polygon code |
| ---: | ---: |
| 0 | `0x003060` |
| 1 | `0x90B0C0` |
| 2 | `0xE0E000` |
| 3 | `0xE0A000` |
| 4 | `0xE0E090` |
| 5 | `0x606060` |
| 6 | `0x80D0F0` |
| 7 | `0x005000` |
| 8 | `0x0060C0` |
| 9 | `0x00D000` |
| 10 | `0x8080F0` |
| 11 | `0x00D0D0` |
| 12 | `0xE0E0E0` |
| 13 | `0x0010C0` |
| 14 | `0x202020` |
| 15 | `0xF0F0F0` |
| 16 | `0xF0D0D0` |

Resident `FUN_003A6A70` stores the configuration's integer token into that
selection mask. The exact S12, S16, and S18 footprint configurations retained
in [Stages](stages.md#animated-and-breakable-background-evidence) each supply
token `2`, enabling only bit index 1. Each archive below contains four
triangles authored `0x0090B0C1`, whose masked code is exactly `0x90B0C0`.
This connects the authored attribute to the footprint acceptance predicate;
model placement, pooling, and fade behavior belong to Stages. The table does
not supply original material names or prove that every listed code is used
by a retail footprint configuration.

## Stage-authored attribute distribution

**Observed — archive data.** The following counts come from the gzip-decoded
retail archives `STAGE/S01.CCS` through `S24.CCS`, whose location is owned by
[Stages](stages.md). Each four-byte-aligned location after chunk
3 was examined for low-halfword tag `0x0B00`. A retained candidate had an
in-bounds declared payload, valid directory indices naming `HIT_` and linked
`MDL_` records, vertex counts divisible by three, batch vertex sum equal to
the header total, and an exact payload endpoint after both vector banks.
All retained candidates passed those internal checks. This avoids relying on
unrelated blocks' occasionally inaccurate declared lengths, documented in
[CCS runtime](../game/files/ccs_runtime.md#parsing-type-dispatch-and-publication).

The entries below are **authored word: triangle count**, before high-bit
orientation classification. They count records present in the archive,
including object hit meshes; they are not a count of active, reachable, or
floor-facing polygons. Resource names are retained exactly where cited.

| Archive | Hit meshes / batches / triangles | Authored word: triangle count |
| --- | --- | --- |
| S01 | 5 / 8 / 1623 | `000061C1:8`, `0080D0F1:10`, `00E000E1:32`, `00E002EA:1573` |
| S02 | 7 / 10 / 749 | `00606061:28`, `00606161:8`, `0080D0F1:4`, `00E000E1:16`, `00E002E2:693` |
| S03 | 7 / 12 / 834 | `00003061:4`, `00005001:8`, `000063CF:2`, `0000D801:6`, `00606161:8`, `00E000E1:12`, `00E002E2:790`, `00E0E001:2`, `00E0E002:2` |
| S04 | 8 / 20 / 397 | `00003061:16`, `00606061:10`, `00606161:8`, `00E000E1:26`, `00E002E2:337` |
| S05 | 5 / 13 / 2179 | `00003161:34`, `00606161:12`, `00E000ED:9`, `00E002EE:1955`, `00E0A001:18`, `00E0E002:151` |
| S06 | 6 / 11 / 742 | `00003061:10`, `00005001:10`, `000061C1:2`, `000062CA:86`, `0000D80D:8`, `00606161:2`, `00E000E1:18`, `00E002EE:606` |
| S07 | 6 / 13 / 1125 | `00003061:12`, `00005001:8`, `000061C1:8`, `000062CE:236`, `0000D801:8`, `00E000E1:8`, `00E002E2:845` |
| S08 | 7 / 13 / 395 | `000060C1:34`, `000061C1:8`, `0000D801:16`, `00959595:2`, `00E000EF:24`, `00E002E2:311` |
| S09 | 5 / 13 / 976 | `00005001:12`, `000060C1:10`, `000061C1:2`, `00606061:12`, `0060606F:8`, `00606161:6`, `00E000E1:20`, `00E002E2:898`, `00E0A001:8` |
| S10 | 6 / 10 / 1471 | `000060CD:2`, `00606061:38`, `00606161:8`, `00E000E1:8`, `00E002E2:1409`, `00E0A001:4`, `00E202EA:2` |
| S11 | 6 / 12 / 1844 | `00003061:14`, `00005001:4`, `000060C1:4`, `000061C1:8`, `0000D801:8`, `00606161:2`, `00E000E1:16`, `00E002EA:1786`, `00E0A001:2` |
| S12 | 5 / 7 / 614 | `00606161:8`, `0090B0C1:4`, `00E000E1:8`, `00E002E2:594` |
| S13 | 13 / 20 / 593 | `0000D801:6`, `00606061:12`, `00606161:6`, `0080D0F1:14`, `00E000EF:24`, `00E002E2:413`, `00E0E001:2`, `00E0E002:100`, `00E202E6:16` |
| S14 | 7 / 13 / 456 | `00003061:14`, `00005001:6`, `000061C1:4`, `0000D805:16`, `00606161:4`, `00E000E1:10`, `00E002E2:402` |
| S15 | 4 / 13 / 410 | `00005001:22`, `000061C1:4`, `00202021:8`, `00606061:16`, `00606161:2`, `00E000E1:12`, `00E002E2:155`, `00E202E2:191` |
| S16 | 5 / 8 / 284 | `00005001:12`, `000061C1:8`, `0090B0C1:4`, `00E000E1:8`, `00E002E2:252` |
| S17 | 5 / 7 / 778 | `00005001:4`, `00606161:8`, `00E000E1:8`, `00E002E2:758` |
| S18 | 5 / 7 / 583 | `00606161:8`, `0090B0C1:4`, `00E000E1:8`, `00E002E2:563` |
| S19 | 6 / 10 / 812 | `00003061:4`, `00005001:16`, `000060C1:6`, `000061C1:8`, `0000D801:8`, `00E000E1:16`, `00E002E2:754` |
| S20 | 6 / 10 / 513 | `000061C1:4`, `00606061:2`, `0080D0F1:6`, `0080D1F1:4`, `00E000E1:24`, `00E002E2:473` |
| S21 | 5 / 7 / 360 | `00606061:4`, `00606161:8`, `00E000E1:12`, `00E002E2:336` |
| S22 | 5 / 11 / 1084 | `00003061:12`, `00005001:4`, `000061C1:2`, `00606161:4`, `0080D0F1:2`, `0080D1F1:2`, `00E000E1:12`, `00E002E2:1046` |
| S23 | 6 / 13 / 355 | `00606061:2`, `008080F1:10`, `008080FF:8`, `0080D0F1:22`, `00E000E1:20`, `00E000EF:4`, `00E002E2:86`, `00E202E2:95`, `00E202E6:108` |
| S24 | 5 / 8 / 738 | `0000326F:4`, `0060626F:28`, `0080D0FF:32`, `00E000EF:32`, `00E002E6:642` |

**Confirmed implications within this scan.** Every retained word is below
`0x20000000`, so orientation classification preserves the entire authored
word in these records. Class-1 ground codes occur in S03 and S13 as
`0xE0E001`, and in S15 as `0x202021`; class-2 `0xE0A001` occurs in S05,
S09, S10, and S11. Several `0xE0E002` batches lack required fighter-query
bit `1`, so masked class membership alone cannot make them a fighter floor.
No retained stage batch masks to special code `0x00D0D0`.

The only retained stage word with bit `0x10000` is `0x00959595`: two triangles
in S08 `HIT_s08are00_hit_s3`. Its masked code is `0x909090`, outside the four
special-ground codes. This bounds the authored source of the selectively
passable flag documented by [Movement and physics](movement_and_physics.md#floor-side-surfaces-and-limits);
it does not name that surface or prove its registration/position. The same
word is also the only retained stage word with bit `0x400`, the contact-damage
selector bit read by `FUN_002312B0`.

## Generated wire polygon attributes

**Confirmed — additional producer outside archive hit blocks.**
`ccElectricWire` creates sixteen `0x1F0`-byte `ccWireHitModel` elements, each
holding a resident environment-query object and two generated triangles.
The factory/configuration and reactive simulation remain owned by
[Stages](stages.md#animated-and-breakable-background-evidence); their polygons'
attribute path belongs here.

The relevant BTL locations distinguish import and live addresses:

| Operation | Preserved / live / complete-file offset |
| --- | --- |
| Wire configuration start | `0x006C8490 / 0x006C84D0 / 0x0145D0` |
| Segment array builder | `0x006C88D0 / 0x006C8910 / 0x014A10` |
| Segment attribute store | `0x006C8BBC / 0x006C8BFC / 0x014CFC` |
| Wire update | `0x006C8EC0 / 0x006C8F00 / 0x015000` |
| Dirty geometry refresh | `0x006C9550 / 0x006C9590 / 0x015690` |

The configuration's complete instruction interval is
`0x006C8490..0x006C8780`. At preserved `0x006C8534..0x006C853C`, `lui 0x2001`, `ori 0xD9D1`, and
`sw ...,+0x28` set the wire word to `0x2001D9D1`. The segment builder calls
resident `0x003A8520` for each endpoint pair, then writes that wire word to
segment `+0x190` at the store indexed above. The constructor callback is live
`0x006C8C50` (preserved `0x006C8C10`), and raw resident initializer
`0x003A8490..0x003A84BC` initially clears `+0x190`.

Resident `0x003A88A0` creates the environment object, sets its hierarchy
pointer to the segment record, builds the two triangles through
`0x003A8BE0`, and `0x003A8520` registers it through `0x001BEFA0`.
Construction builds geometry before the BTL attribute store. Those initial
triangles therefore have zero authored bits, with only their derived geometric
class; the later segment-word store alone does not update them. The wire starts
dirty: its configuration sets byte `+0xF4 = 1` and invokes the installed update
slot. The eligible wire update
calls live `0x006C9590`, whose complete body is preserved `FUN_006C9550`.
That helper rebuilds every dirty segment through resident `0x003A85A0`, which
updates endpoints and calls `0x003A8BE0`, then clears the dirty byte. Further
dirty refreshes use the same path. Segment teardown calls resident
`0x003A84C0`, releasing its environment object and visual model.

The instruction bytes at preserved `0x006C9550` establish the helper's
prologue, dirty-byte test, two resident `0x003A85A0` call sites, and
dirty-byte clear. Update eligibility and the zero/nonzero
amplitude branches belong to [Stages](stages.md#animated-and-breakable-background-evidence).

**Confirmed — shared query registration, separate reaction condition.**
`FUN_001BEFA0(object,0)` appends the environment object to the chain rooted
at `gp-0x353C` (`iGpffffcac4`). Both `FUN_001BF100` and
`FUN_00211420` walk that root and advance through object `+4`, agreeing with
the registration described by Stages. Their attribute predicates still differ.
The wire reaction compares the full retained fighter word with `0x2001D9D1`;
after a refreshed triangle has retained low bits `0x0001D9D1`, this equality
also requires its derived geometric class to be exactly `0x20000000`.
A wire triangle selected under another geometric class, or an initial triangle
whose authored bits are still zero, does not satisfy that equality solely by
belonging to the registered wire. The retained fighter word can also survive a
movement contact rejection, so equality alone does not prove current grounding.

At each such rebuild the ordinary triangle builder removes the supplied
`0x20000000` bit and derives a fresh geometric class from the current
triangle normal. The retained authored bits are `0x0001D9D1`, so these generated
polygons carry fighter-query bit `1`, side/surface eligibility bit `0x100`,
first-jump input multiplier bit `0x800`, selectively passable bit `0x10000`,
and masked code `0x00D0D0` (special-ground class 3). This explains a static
source for that classifier code absent from the stage hit-block table.
It establishes participation in the environment-query system, not damage:
the inspected path contains no fighter hit or HP write.

RTTI corroborates the element identity: resident vtable `0x005DD9D0` points
to live BTL descriptor `0x008C2290`; the descriptor at preserved `0x008C2250`
points to live string `0x00891448`, whose bytes at preserved `0x00891408`
spell `ccWireHitModel`.
