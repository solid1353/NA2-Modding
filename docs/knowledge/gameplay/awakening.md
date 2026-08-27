# Awakening and transformation gameplay

This document records the clean NA2 awakening controller, persistent effect
state, post-Ultimate-Jutsu form replacement, and cleanup boundaries. It is a
static reverse-engineering result. No runtime replay was performed for this
investigation. Existing replay-backed identity and combo findings are linked
where they clarify a field, but animation internals and Adventure mode are out
of scope.

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

See [Battle systems](battle.md) for the broader effect-source union and
replay-backed combo owner, and [Character identity in battle](character_ids.md)
for the current, match-start, and live-fighter identity fields.

## Research coverage

- **Assigned scope:** this pass owned clean-NA2 battle awakening/transformation
gameplay state: controller eligibility and triggers, character/effect/form
mapping, controller and effect flags, post-UJ replacement, resource-object
handoff, exit/reset cleanup, and representative ownership boundaries between
resident code and `BTL.BIN`.

- **Exploration depth:** the pass decoded all 94 trigger-descriptor rows at
`0x005C1B50`, all 94 association rows at `0x005C1D30`, all 223 UJ records at
`0x005AEC40`, all 94 character UJ-list pointers and their complete pointed
lists, all per-character defaults at `0x005AFDB0`, the complete 94-entry
character factory/record table, all 12 class-3 effect records `0x68..0x73`, and
the complete 12-row effect-notification map at `0x005B0040`. Direct/raw-`jal`,
absolute-word, and conventional `lui` plus immediate reference scans covered
the whole clean BTL overlay for the resident controller, form-map, request,
effect, and table targets enumerated below. Constant callsites/writers were
fully enumerated where this document says "sole," "all," or "exactly"—notably
the UJ outcome setter, defeat-latch slot `7`, re-entry variant, transformed
effect constructor, BTL effect create/remove calls, and Tenten `+0xB78`
producers.

  **Bounded control-flow traces:** resident traces cover the
dispatcher and entry/cleanup family `FUN_0020CF40..FUN_0020EA90`, generic
effect creation/removal `FUN_003047C0..FUN_00306980`, UJ completion
`FUN_0035AF20 -> FUN_0035B3B0`, record helpers
`FUN_003729F0..FUN_00372D00`, request `FUN_001EC5E0`, route-`8` dispatch and
states `0x17/0x18`, manager save/restore/reset, and fighter setup/teardown.
BTL traces were bounded to the metadata consumer at live `0x00709860`, the UJ
outcome state machine beginning live `0x00769790`, event-counter wrappers at
live `0x00715F60..0x00716050`, and the battle-sequence lifecycle rooted at live
`0x0076E9D0`. Callers outside those ownership chains were sampled only where
identified as representative.

- **Confirmed coverage:** the sections below establish the exact
clean trigger/association data; ordinary, class-7, and Naruto-specific entry
paths; proven HP, combo, item/projectile, and action-progress predicates; the
independence of controller marker, effect-list state, and live character form;
class-3 creation/persistence/removal behavior; all 12 native UJ
effect-to-character mappings; the UJ completion gates; the state-`0x17`
resource replacement route; saved-identity restoration; BTL's adjacent but
non-owning role; and the reserved/incomplete `0x4A` slot.

- **Unresolved or untested:** the exact visible ordering of marker, effect-node, character-ID,
and rebuilt-object changes remains uncaptured. Generic UJ input and resource
admission before record execution was not exhaustively traced, nor was every
arbitrary indirect BTL computation; the negative BTL ownership result is
therefore limited to the explicit scan families above. The user-facing name of
BTL outcome value `2`, the concrete subsystem behind the Deidara/Gaara
component float pair, insertion-failure behavior at ordinary entry, and the
visible result of the Konohamaru class-7 mismatch remain unresolved.

- **Deliberate exclusions and overlap:** Adventure mode, animation
internals and timing/60-FPS evaluation, damage formulas, substitution,
widescreen/rendering, media, and localization were excluded. Broader effect
source aggregation and replay-backed combo ownership remain canonical in
`battle.md`; identity terminology remains canonical in `character_ids.md`.
Those adjacent subjects were consumed only far enough to support this file and
were not re-investigated here.
- **Evidence limitations:** this is primarily static evidence from the two
  hashed clean binaries; no runtime replay or end-to-end transformation was
  performed. Arbitrary indirect BTL computation was not exhaustively audited.

## Evidence identity and address mapping

All resident observations come from clean `SLPS_258.37`:

- size: `5,273,256` bytes;
- SHA-256:
  `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`;
- mapping in the documented resident region:
  `file offset = runtime address - 0x000FFF00`;
- ELF `.reginfo` establishes resident `gp = 0x0060A9F0`; addresses derived
  from a `gp`-relative instruction use that value plus its sign-extended
  16-bit displacement.

All overlay observations come from clean `PRG/BTL.BIN`:

- size: `0x222300` (`2,237,184`) bytes;
- SHA-256:
  `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`;
- `MWo3` kind `1`, load base `0x006B3F00`, text span `0x001DB6C0`,
  BSS size `0x6E80`, internal name `BTL_product.bin`;
- loaded file end `0x008D6200` and effective end including BSS
  `0x008DD080`;
- raw file offset `x` is live address `0x006B3F00 + x`;
- the preserved export omits the `0x40`-byte header, so its displayed code
  address is the live address minus `0x40`.

The last distinction prevents a common `0x40` address error. Direct operands
in the BTL listing still contain runtime addresses.

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

The resident controller also contains encoded absolute calls into three BTL
targets. These operands are already live addresses; the export column is the
header-omitting baseline, not the encoded value:

| Observed use | Export baseline | Live target | Complete-file offset |
| --- | ---: | ---: | ---: |
| Set component float pair | `0x006F0990` | `0x006F09D0` | `0x0003CAD0` |
| Restore component float-pair defaults | `0x006F09A0` | `0x006F09E0` | `0x0003CAE0` |
| Per-side event-counter read wrapper | `0x00716010` | `0x00716050` | `0x00062150` |

The setter is 16 bytes: it stores `f12` to component `+0xA8`, stores `f13` to
component `+0xA4`, and returns. The restorer is 32 bytes: it writes raw float
bits `0x3FC90FDB` to `+0xA8` and `0x40278B7F` to `+0xA4`, then returns. Neither
calls another function. The resident awakening paths pass the component
pointer from fighter `+0x24`; activation supplies `0x40060723` to both fields.

An exhaustive aligned BTL `jal` scan found no BTL caller of the setter and one
caller of the restorer. Its call instruction is export `0x006EF4E0`, live
`0x006EF520`, file `0x0003B620`. The enclosing exported
`FUN_006EF4A0` actually starts at live `0x006EF4E0`, file `0x0003B5E0`, with
live bounds `[0x006EF4E0,0x006EF554)`. It initializes the component, installs
vtable `0x005DDD30` at `+0x50`, clears `+0x60/+0x64/+0x84/+0x88`, restores the
float defaults, and continues generic initialization. The restore function is
therefore demonstrably generic component initialization reused by awakening
cleanup. The component's concrete gameplay subsystem remains unknown.

The event-counter read wrapper demonstrates the intra-overlay `jal` labeling
hazard directly. Its call instruction is export `0x0071602C`, live
`0x0071606C`, file `0x0006216C`, and encodes the already-live target
`0x007161A0`. The true callee is therefore export baseline `0x00716160`, live
`0x007161A0`, file `0x000622A0`; the export instead labels bytes at displayed
`0x007161A0`, which are live `0x007161E0` and belong to different code.

The wrapper reads a signed halfword from a BTL BSS matrix at live
`0x008D6A80`, export baseline `0x008D6A40`, BSS offset `+0x880`. The matrix has
two `0x38`-byte side rows, each containing 28 signed halfwords. Its address is
`0x008D6A80 + (side-1)*0x38 + slot*2`. Related exact wrappers are:

| Operation | Export baseline | Live | File |
| --- | ---: | ---: | ---: |
| Clear both rows | `0x00715F20` | `0x00715F60` | `0x00062060` |
| Add a value | `0x00715F50` | `0x00715F90` | `0x00062090` |
| Store an exact value | `0x00715F90` | `0x00715FD0` | `0x000620D0` |
| Read signed value | `0x00716010` | `0x00716050` | `0x00062150` |

These roles come from raw target bodies, not the shifted Ghidra callee labels.

### Owner and lifecycle of the global suppression gate

The pointer at resident `0x00607834` is not an awakening object. Resident
`FUN_001EF330` allocates a `0x6C0`-byte battle-global object, initializes its
resident-owned subobjects, and invokes its BTL constructor with both character
IDs and the battle mode. Resident `FUN_001EEFD0` runs the corresponding BTL
cleanup, destroys the subobjects, frees the allocation, and nulls the global.

The relevant outer-object routines are exact raw BTL functions whose export
labels are shifted:

| Operation | Export baseline | Live | File |
| --- | ---: | ---: | ---: |
| Construct `0x6C0` object | `0x0076E990` | `0x0076E9D0` | `0x000BAAD0` |
| Request/reinitialize inner sequence | `0x0076F0F0` | `0x0076F130` | `0x000BB230` |
| Tear down current inner sequence | `0x0076F160` | `0x0076F1A0` | `0x000BB2A0` |

The constructor's true bounds are live `[0x0076E9D0,0x0076EC10)` and it writes
outer signed byte `+0x10 = 0` at live `0x0076EAA4` (export `0x0076EA64`, file
`0x000BABA4`). The request routine first calls teardown when `+0x10` is
nonzero, then writes `+0x10 = 1` at live `0x0076F168` (export `0x0076F128`,
file `0x000BB268`) and records selectors at `+0x0C/+0x0D`. Three selector
families promote the outer state to `2` after successfully constructing their
inner object:

| Outer `+0x10 = 2` store | Export baseline | Live | File |
| --- | ---: | ---: | ---: |
| Selector `+0x0D == 0` | `0x0076F738` | `0x0076F778` | `0x000BB878` |
| Selector `+0x0D == 1` | `0x0076FA74` | `0x0076FAB4` | `0x000BBBB4` |
| Selector `+0x0D == 0x0D` | `0x0076FCA8` | `0x0076FCE8` | `0x000BBDE8` |

The teardown routine frees the selected inner object, clears outer pointers
`+0x1C/+0x220/+0x224`, and writes outer `+0x10 = 0` at live `0x0076F230`
(export `0x0076F1F0`, file `0x000BB330`). BTL update paths distinguish state
`1` while constructing the inner object from state `2` while servicing it.
An exhaustive raw scan of this implementation found no outer `-1` write. A
zero at live `0x0076FCDC` belongs to a newly allocated inner object; it is not
another outer-state transition.

**Interpretation, high confidence:** outer `+0x10` is a three-state BTL
battle-sequence lifecycle (`0` idle, `1` requested/pending construction, `2`
inner object live). The awakening dispatcher permits normal descriptor work
when this global is absent or its state is `0` (and defensively also `-1`), and
suppresses it while state is `1` or `2`. This gate coordinates awakening with
another battle-global sequence; it is not an awakening eligibility resource
or persistent transformed-state flag.

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
| `+0x00` signed `s16` | Passed to `FUN_002040D0(value,-1,1)` after ordinary entry when it is not `-1` |
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
| `0x00607834` | pointer | BTL `0x6C0` battle-sequence object; signed byte `+0x10` is lifecycle `0/1/2` and gates dispatch |

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
2. If `0x00607834` is null, or its pointed signed byte `+0x10` is `0` or `-1`,
   continue normal descriptor handling. BTL itself writes `0` for idle, `1`
   for requested/pending construction, and `2` for an installed inner object;
   no outer `-1` writer was found in that implementation.
3. In BTL states `1` or `2`, suppress descriptor handling. An existing controller marker is
   cleared for ordinary characters, but preserved for IDs `0x2F..0x38`,
   `0x49`, `0x4A`, `0x4B`, and `0x51`. Clearing Deidara or Gaara also clears
   bit `0x10` and calls `SUB_006F09E0(fighter+0x24)`. No effect is removed.
4. Give bit `0x40` first priority. `FUN_0020D690` success runs its transition
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

It also returns true without an effect lookup for transformed IDs
`0x2F..0x38`, `0x49`, `0x4A`, and `0x4B`. On success, the dispatcher sets
`+0x63:0x20` and runs the controller transition. A call to the encoded BTL
target at export baseline `0x00716010`, live `0x00716050`, file `0x00062150`
with `(side,10)` reads the event-counter matrix described above. A nonzero
slot reduces the transformed-ID route to only
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
matrix slot `0x0A` and adds its third argument through live wrapper
`0x00715F90`. Both ordinary and successful class-7 tails call
`FUN_00223360(fighter,6,1)`, so they increment side slot `10`. The transformed
adoption branch tests that same slot and omits `FUN_00223360` when it is already
nonzero. Preventing a repeated event-count update on the reconstructed form is
the supported interpretation; the numeric read/increment/branch chain is
directly proven.

`0x00607678` is a shared battle re-entry phase, not an awakening-only flag. Its
normal observed progression is:

| Phase | Proven producer | Meaning supported by consumers |
| ---: | --- | --- |
| `0` | initial BSS state; no resident zero writer was found | ordinary battle setup |
| `1` | `FUN_001EC5E0` at `0x001EC5E4`; alternate re-entry route in `FUN_001F2E70` at `0x001F3360` | replacement/re-entry requested |
| `2` | end of state-`0x17` handler `FUN_001EE1C0` at `0x001EE3A0`; end of alternate state-`0x18` handler `FUN_001EE500` at `0x001EE804` | resource/object rebuild completed; controller reconstruction pending |
| `3` | `FUN_001EC3B0` at `0x001EC4D4` | controller reconstructed after phase `2` |

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

`FUN_001EC3B0` clears both event-matrix rows through live `0x00715F60` whenever
it creates a controller outside phase `2`. In phase `2` the clear is skipped
and the function advances the global to `3`. This is the exact preservation
boundary for awakening event counters across reconstructed-form re-entry.

For Deidara `0x40`, detecting `0x41` additionally sets `+0x63:0x10` and calls
the encoded live BTL target `SUB_006F09D0` (export baseline `0x006F0990`, live
`0x006F09D0`, file `0x0003CAD0`) with fighter `+0x24` and duplicated
`0x40060723` float arguments. The matching cleanup target `SUB_006F09E0`
(export baseline `0x006F09A0`, live `0x006F09E0`, file `0x0003CAE0`) is
the generic component float-pair default restorer documented above.

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

`FUN_0020C270` allocates each `0x3C`-byte per-side combo object.
`FUN_0020C420` accumulates fighter pending-hit byte `+0xA45` into current count
`+0x34` and clears the pending byte. Existing synchronized captures documented
in [Battle systems](battle.md#native-combo-owner) establish `+0x34` as the
native current combo count. This route is not a chakra or awakening-gauge
check.

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
positions, not resource quantities. Their exact user-visible timing was not
runtime-captured here, and progress rendering/playback internals are outside
this document's scope.

The dormant bit-`0x20` branch would call the same helper with selector `0` only
for Sakura `0x3A`, but no clean descriptor has that bit. Semantic names for
the action-progress source beyond the proven tracker behavior are not needed
for eligibility.

There is no general chakra, meter, or universal low-HP prerequisite in
`FUN_0020E280`. Only the exact HP and counters above are proven.

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
   `FUN_002040D0(descriptor_s16,-1,1)`, then
   `FUN_001D87C0(0x3A,fighter+0x30)` and `FUN_00334FF0(fighter)`.

The controller does not test whether `FUN_00305C30` actually inserted the
effect before setting its marker. This is a direct control-flow observation;
whether clean data can make insertion fail at this point was not runtime
tested.

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
local-list record whose selector key matches the request. Raw instructions in
`FUN_002449C0` prove that its three tier requests are keys `2`, `3`, and `1`;
the decompiler's apparent one-argument key-`2` call is misleading because
`a1 = 2` remains live from `0x00244B18`. Konohamaru's key-2
record `78` is class `7` and writes effect `0x2E` to fighter `+0x18A`. Once
`FUN_0020D690`'s runtime gates pass, it attempts to
insert clean effect `0x2E`, finds only `0x2F` in the association, clears the
controller flags, and returns failure. If insertion succeeds, this call site
does not remove `0x2E`. The other 11 class-7 records in these eight local lists
all belong to their character's association set. No runtime capture in this
pass tested the surviving node or its visible result.

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
controller bit `0x20` and does not run either controller transition tail.
Naruto's direct low-HP effect is consequently distinct from both the
descriptor's two low-HP characters and his effect-`0x72` form replacement.

## Generic effect state

### Classification and records

`FUN_003047C0` classifies the full effect domain exactly:

| Effect IDs | Class |
| --- | ---: |
| `0x00..0x0D` | `0` |
| `0x0E..0x64` | `1` |
| `0x65..0x67` | `2` |
| `0x68..0x73` | `3` |
| `0x74..0x89` | `4` |
| Outside `0x00..0x89` | invalid (`-1`) |

The complete transformed-form family is therefore exactly class `3`.

Per-effect metadata has stride `0x64`. Using
`0x0059E2A4 + effect_id * 0x64` as the anchor, observed fields are factory
`+0x00`, stored ID `+0x04`, default node state/lifetime `+0x08`, and flags
`+0x0C`. Records `0x68..0x73` all have:

- null factory, so creation uses generic `FUN_00304910`;
- stored ID matching the record;
- default state `-1`;
- flags exactly `0x2`.

There is no per-effect model/resource-swap callback in these 12 records. Flag
`0x4`, which would recursively propagate to the fighter at `+0x20`, is absent.

### Container and creation

The fighter's effect container begins at `+0x8C4`:

| Field | Meaning |
| ---: | --- |
| fighter `+0x8C4` | node count |
| fighter `+0x8C8` | head |
| fighter `+0x8CC` | tail |
| fighter `+0x8D0` | container vtable |
| fighter `+0x8D4` | owner backpointer |
| node `+0x18/+0x1C` | previous/next |
| node `+0x60` | last removal reason supplied |
| node `+0x64` | owning fighter |
| node `+0x68` | 32-bit effect ID |
| node `+0x6C` | state/lifetime/sentinel |

`FUN_00306420` traverses this list and is the authoritative presence test.

`FUN_00305C30` classifies the ID, resolves a default parameter, and calls
`FUN_00305270` to insert it. Classes `1`, `2`, and `3` bypass the ordinary
fighter-`+0x62`/`FUN_00216820` eligibility gate. With final argument nonzero,
record flag `0x2` permits application and flag `0x4` would propagate it to the
opponent; class-3 records are therefore owner-only.

`FUN_00305270` refuses an unowned container, finds an existing duplicate, and:

- refuses replacement if duplicate node `+0x6C == -2`;
- otherwise force-removes the duplicate with reason `5`;
- invokes the per-effect factory or generic constructor;
- appends the node and overrides `+0x6C` when the caller did not pass `-1`.

After a successful insertion, `FUN_00376610` resolves the active battle object
(or returns zero). If it exists, `FUN_00376160` scans the complete 12-row map at
`0x005B0040` before optionally notifying BTL live `0x0070D5F0`. The map is
`0->0x0D`, `2->5`, `3->6`, `4->0x0E`, `5->8`, `6->7`, `8->0x0C`, `9->9`,
`7->0x13`, `0x0B->0x10`, `0x0A->0x0F`, and `0x0C->0x11`. It contains neither
ID `1` nor any class-3 ID `0x68..0x73`; a transformed-form insertion therefore
returns from `FUN_00376160` without making the BTL call. The following positional
event switch also handles only IDs `0..0x0C`, and the auxiliary sidecar at
fighter `+0x8D8` is allocated only for classes `1` and `2`. Thus a successful
class-3 insertion performs none of those BTL/event/sidecar hooks and only reaches
the unconditional final write of its ID to fighter `+0x8E8`.

The exact BTL append primitive is live `0x00709E60`, file `0x00055F60`. It was
not defined as a function in the header-shifted export, whose equivalent
address is `0x00709E20`. It appends at the tail and increments the count. Erase
is live `0x00709EA0`, file `0x00055FA0`; the export labels this code
`FUN_00709E60` because of the `0x40` shift. It repairs both links/head/tail,
decrements the count, and dispatches the node delete slot.

### Persistence and removal

`FUN_00305FF0`, called during fighter setup by `FUN_002151E0`, creates
transformed-form effects with explicit node state `-2`, not their record
default `-1`. This makes them persistent:

- duplicate creation refuses to replace a `-2` node;
- removal reasons `0`, `1`, and `2` preserve a `-2` node;
- reason `3` preserves all class-3 and class-4 nodes, and also preserves
  `-2` nodes in classes `0..2`;
- reason `5` force-removes any node.

For ordinary `-1` nodes, reason `0`, `1`, or `2` normally erases immediately.
If `FUN_00306490(owner,effect)` succeeds while owner `+0x18E == 8`, removal is
deferred by writing node `+0x6C = 1`. `FUN_003059B0` decrements only positive
values, so `-1` and `-2` are both indefinite while `-2` has the extra
protections above.

`FUN_00305510` safely walks and removes every matching effect ID.
`FUN_003055C0` bulk-removes only classes `0..2`; it leaves transformation class
`3` intact. `FUN_00305750` force-removes classes `0..4` and is called by fighter
teardown `FUN_00215720`. Fighter teardown is the proven terminal cleanup for
even constructor-owned `-2` transformation effects.

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
already stored in the manager and applies the separate gates below. Generic UJ
input/resource admission was not exhaustively traced in this pass.

`FUN_0035AF20` owns the demonstrated UJ-completion path. After tearing down its
17 owned entries and transient handles, it passes the side index from its
object `+0x28` to `FUN_0035B3B0` at direct callsite `0x0035B15C`.
`FUN_0035B3B0(side_index)` then reaches a form request only after these ordered
gates:

1. the battle manager exists;
2. manager mode `+0x0C` is not `6` (the clean Mode Select crosswalk identifies
   `6` as Collection);
3. `FUN_00373790()` does not return `2` (return `2` instead increments BTL
   event-matrix slot `0x0E` for the side and returns);
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
| `2` | `0x0076A54C` | `0x0076A58C` | `0x000B668C` | state `4` and `FUN_0035DB20(0) != 0` |
| `1` | `0x0076A584` | `0x0076A5C4` | `0x000B66C4` | owned handle passes `FUN_001CDD80` |

Thus gate value `2` is a BTL-produced UJ outcome/state, but its exact
user-facing name remains open. The resident consumer's behavior is exact:
value `2` diverts to side event slot `0x0E` and suppresses the form request.

The former Ultimate-Jutsu type-`0` candidate left the resident contest-object
global at `0x00607750` empty, so the main manager skips both the object's update
dispatcher `FUN_0036BF10` and render dispatcher `FUN_0036BFF0`. The user
established at runtime that enabling this implementation prevents post-UJ
awakening. Static analysis establishes that object suppression removes the
shared nonvisual contest lifecycle used alongside the BTL-produced completion
state, but it does not isolate a single omitted field as the cause. The
accepted correction keeps native contest-object creation and updates, retains
the two BTL input-read suppressions, and NOPs only the sole resident call to
`FUN_0036BFF0` at `0x001F0940` (clean ELF file offset `0xF0A40`). User runtime
testing on 2026-08-21 confirmed that the corrected post-UJ awakening path
executes while the contest remains invisible and unresponsive to both players.

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
the nonzero pending ID and first calls `FUN_001E8EE0`. That helper releases the
target side's cached-resource mask `0x113` through `FUN_001E8960` when its
current character differs from the other side, then releases its additional
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
Subsequent controller creation by `FUN_001EC3B0` preserves the event matrix and
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

### Reserved transformed slot `0x4A`

Resident helper `FUN_001F7C80` at `0x001F7C80` maps every normal/form pair used
by the roster helpers. Among the proven pairs it maps Chiyo `0x3E` to `0x4A`,
maps Sasori `0x3F` to `0x4B`, and maps Naruto `0x39` to `0x49`. It also returns
each transformed ID when that transformed ID is supplied. `FUN_001F7BC0` at
`0x001F7BC0` classifies `0x4A` with the other transformed IDs. This establishes
an intended Chiyo-to-`0x4A` pairing in clean resident code.

The pairing is deliberately asymmetric and incomplete:

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

An additional caller, `FUN_0035CA80` in the resident UJ factory, resolves the
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
| `0x00211770` | `FUN_00211770` | Initialize/reset scalar progress tracker |
| `0x002117A0` | `FUN_002117A0` | Set all progress positions to one value |
| `0x002118A0` | `FUN_002118A0` | Test position with tracker crossing bit `0x01` |
| `0x00211A20` | `FUN_00211A20` | Test position with tracker crossing bit `0x02` |
| `0x00211D80` | `FUN_00211D80` | Advance scalar progress tracker |
| `0x002151E0` | `FUN_002151E0` | Fighter setup caller of transformed-effect constructor |
| `0x00215720` | `FUN_00215720` | Fighter teardown caller of force cleanup |
| `0x00217E40` | `FUN_00217E40` | Transition major action state and substate |
| `0x00223360` | `FUN_00223360` | Map event code `6` to per-side counter slot `10` and increment it |
| `0x002274C0` | `FUN_002274C0` | Exact raw fighter-state gate |
| `0x002378A0` | `FUN_002378A0` | Validate pending item-use action before counter increment |
| `0x002378F0` | `FUN_002378F0` | Start accepted kind-`3`/`6` item route and increment `+0xB78` |
| `0x002449C0` | `FUN_002449C0` | Request class-7 UJ selector keys |
| `0x0024DA50` | `FUN_0024DA50` | Representative fighter update caller |
| `0x0025DEF0` | `FUN_0025DEF0` | Classic Tenten projectile-create counter producer |
| `0x00299100` | `FUN_00299100` | Naruto direct low-HP effect callback |
| `0x002B9660` | `FUN_002B9660` | Tenten projectile-create counter producer |
| `0x003047C0` | `FUN_003047C0` | Effect classifier |
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
| `0x0035AF20` | `FUN_0035AF20` | UJ-completion teardown and direct owner of the form-map call |
| `0x0035B3B0` | `FUN_0035B3B0` | Apply post-UJ gates and request a mapped replacement form |
| `0x0035B740` | `FUN_0035B740` | Set per-side UJ defeat latch when its flag and target-HP tests pass |
| `0x00376160` | `FUN_00376160` | Map selected small effect IDs to a BTL notification; class `3` has no row |
| `0x00376610` | `FUN_00376610` | Resolve the active battle object for optional effect notification |
| `0x00373780` | `FUN_00373780` | Set the BTL-owned UJ outcome/state word |
| `0x00373790` | `FUN_00373790` | Read the BTL-owned UJ outcome/state word |
| `0x003729F0` | `FUN_003729F0` | Select default/keyed character-local UJ record |
| `0x00372B10` | `FUN_00372B10` | Read UJ record effect field |
| `0x00372D00` | `FUN_00372D00` | Map UJ effect to replacement character ID |
| `0x001EC5E0` | `FUN_001EC5E0` | Stage pending form and replacement globals |
| `0x001EC3B0` | `FUN_001EC3B0` | Battle-controller creation and event-matrix clear/preserve boundary |
| `0x001EC960` | `FUN_001EC960` | Main dispatcher containing re-entry states `0x17` and `0x18` |
| `0x001E80F0` | `FUN_001E80F0` | Load per-side character resources |
| `0x001E8EE0` | `FUN_001E8EE0` | Release pending side's old resources with shared-pointer protection |
| `0x001E8960` | `FUN_001E8960` | Release per-side cached resources |
| `0x001EDD10` | `FUN_001EDD10` | Dispatch route `8` by re-entry variant to state `0x17` or `0x18` |
| `0x001EE1C0` | `FUN_001EE1C0` | Native post-UJ form/resource replacement; preserves saved configuration |
| `0x001EE3E0` | `FUN_001EE3E0` | Restore saved side record |
| `0x001EE500` | `FUN_001EE500` | Variant-`2` pending-ID rebuild; snapshots its new configuration |
| `0x001EEFD0` | `FUN_001EEFD0` | Destroy and free the global BTL battle-sequence object |
| `0x001EF330` | `FUN_001EF330` | Allocate and initialize the global BTL battle-sequence object |
| `0x001EF9C0` | `FUN_001EF9C0` | Representative caller of phase-`1` readiness barrier |
| `0x001F0F40` | `FUN_001F0F40` | Synchronize allocated side objects during phase `1` |
| `0x001F4DD0` | `FUN_001F4DD0` | Snapshot current manager configuration into the saved baseline |
| `0x001F4ED0` | `FUN_001F4ED0` | Restore saved manager configuration over current copy |
| `0x001F4F20` | `FUN_001F4F20` | Clear pending form IDs |
| `0x001F7AA0` | `FUN_001F7AA0` | Roster-validity exclusion including reserved ID `0x4A` |
| `0x001F7BC0` | `FUN_001F7BC0` | Classify transformed character IDs including `0x4A` |
| `0x001F7C80` | `FUN_001F7C80` | Forward normal-to-transformed pairing, including `0x3E -> 0x4A` |
| `0x001F7E70` | `FUN_001F7E70` | Reverse transformed pairing; deliberately omits `0x4A` |
| `0x001FD7D0` | `FUN_001FD7D0` | Initialize the three-side event/state matrix to `-1` |
| `0x001FD850` | `FUN_001FD850` | Write one side/index event-state entry |
| `0x001FDB40` | `FUN_001FDB40` | Read one side/index event-state entry |
| `0x001FE920` | `FUN_001FE920` | Release, restore, and reload sides whose current identity differs from saved |
| `0x001FED10` | `FUN_001FED10` | Reset-state caller of manager identity/resource restoration |
| `0x00607678` | shared re-entry phase | `0` ordinary, `1` requested, `2` rebuilt, `3` controller reconstructed |
| `0x0060767C` | re-entry variant | Route `8`: `1` selects state `0x17`; `2` selects state `0x18` |
| `0x00607780` | BTL-owned UJ outcome/state | `2` diverts post-UJ completion away from form replacement |
| `0x00604314` | UJ outcome flag | Value `1` plus target HP `<= 0` sets side state slot `7` to `1` |
| `0x006B2B40` | per-side event/state matrix | Three rows of `0x5D` words; row stride `0x174` |
| `0x005A2900` | character factory/record table | 94 eight-byte entries; factory at `+0`, record pointer at `+4` |
| `0x0059E2A4` | effect-record factory anchor | Base used with stride `0x64` |
| `0x005B0040` | effect-notification map | Twelve `(effect ID, BTL selector)` rows; no class-3 ID |
| `0x005ACFB0` | character UJ-list pointer table | Lists of `s16` UJ-record indices |
| `0x005AEC40` | UJ record table | 223 records, stride `0x14` |
| `0x005AFDB0` | default UJ-record index table | Per-character default selection |
| `0x005C1B50` | trigger descriptor table | 94 records, stride `4` |
| `0x005C1D30` | association table | 94 records, stride `8` |

## Negative results and open questions

- **High:** clean descriptor bit `0x20` is unused.
- **High:** no general chakra read or universal HP test occurs in the controller
  dispatcher. Its HP route covers only the two descriptor characters; Naruto's
  callback is separate, and `FUN_002449C0` separately uses HP `<= 0.5` to select
  UJ category `3`.
- **High:** association membership alone does not prove an entry route, and a
  bit-`0x01` descriptor alone does not prove `FUN_0020D030` can succeed.
- **High:** the effect cache at fighter `+0x8E8` is not authoritative after
  deletion.
- **High:** class-3 records `0x68..0x73` contain no custom factory or resource
  swap callback; the manager state machine owns form/resource replacement.
- **High:** class-3 creation has no entry in the resident-to-BTL effect
  notification map and bypasses the small-ID positional event and class-1/2
  sidecar paths.
- **High:** transformed-form construction applies persistent effects but does
  not set the controller marker.
- **High:** character ID `0x4A` is the reserved/incomplete transformed slot
  paired forward with Chiyo `0x3E`. It is rejected by roster validation,
  omitted by the reverse mapper and native form constructors, and backed by
  the complete ID-`0x01` fallback factory/record entry. No native reachable
  transformation route is established.
- **Medium:** BTL has no conventional direct ownership of the controller, but
  arbitrary dynamic wrapper inputs and exotic indirect computation cannot be
  excluded by static reference scans alone.
- **High:** the global `0x00607834` suppression byte is a BTL sequence lifecycle,
  not an awakening resource. Its native outer-object writers use only `0`, `1`,
  and `2`; the dispatcher also tolerates `-1`, but no BTL outer `-1` writer was
  found.
- **Open:** the concrete component subsystem whose float pair is overridden by
  `SUB_006F09D0`. The action-state tuple and `+0x1DC` progress predicate are
  structurally resolved, but their exact user-visible transition moment was
  not runtime-captured.
- **High:** clean Konohamaru data reaches the class-7 apply-before-membership
  mismatch through default record `78`; the other 11 class-7 records in the
  eight descriptor characters' local lists match their associations.
- **Open:** no runtime capture in this pass verifies the exact visible moment
  at which controller bits, effect nodes, current character ID, and rebuilt
  fighter object change relative to one another.
