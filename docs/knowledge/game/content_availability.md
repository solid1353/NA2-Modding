# Content availability and state ownership

This document records the availability gates of retail NA2 (`SLPS-25837`)
and the saved, resident, and temporary state consumed by the frontend and
battle selectors.

## Research coverage

- **Assigned scope:** resident availability readers, their stored fields, and
  the roster, stage, mode, Jutsu and Collection consumers needed to establish
  native content-state semantics and ownership.
- **Exploration depth:**
  - The resident reader families, fighter/form and support roster predicates,
    fresh defaults, and the complete resident stage-bit reader/setter family
    were traced with their direct consumers.
  - All 26 special Jutsu selectors, 43 character/list mappings, 12 exclusion
    lists, and the one exception row were decoded.
  - All six ETC Collection groups and their fixed record tables were decoded;
    direct ETC state writers, Collection-root NEW scans, Diorama derivation,
    and Movie list-cache construction, confirmation rereads and disposal were
    checked.
  - In-scope Mode Select list and controller-port confirmation gates were
    read. Wider availability restores were followed only to the excluded
    controller boundary; not every prerequisite or acquisition producer was
    traced.
- **Confirmed coverage:** resident pointer and reader contracts; stored bounds;
  fighter/form and support dependencies; resident stage bits and mode gates;
  Jutsu owner and cross-character admission; form and difficulty progress
  gates, including one `0x6A` writer on the finite Survival result path; and
  grouped-content meanings, viewer transitions, Movie cache ownership, NEW
  scans, and Diorama derivation.
- **Unresolved or untested:** movie acquisition, several eligibility-table
  producers and indirect callers outside the direct-reference inventory remain
  unresolved, as do other producers of word `0x6A`.
- **Deliberate exclusions and overlap:** profile serialization and the complete
  record layout belong to [Save-data record format and lifecycle](save_data.md).
  Character Select roster and selector presentation belong to
  [Native Character Select flow](character_select.md). Stage loading and slot
  identity belong to [Stages](../gameplay/stages.md); Mode Select construction
  and dispatch belong to [Mode flow](mode_flow.md). The Survival result
  producer of word `0x6A` belongs to [Survival](../gameplay/survival.md).
  Master Mode and Shop are excluded; acquisition branches entering those
  controllers stop at that boundary.
- **Evidence limitations:** static resident, BTL and ETC tracing establishes
  the bounded control flow and fixed data. Read-only runtime-memory
  comparisons corroborate stored values, but do not establish every
  acquisition path or lifecycle transition. Direct-call searches exclude
  neither indirect calls nor inlined memory access; split function bodies
  required instruction bytes.

## Evidence identity

Static addresses use the clean resident ELF and the conventions in
[Retail game file identities](files/file_identities.md#address-conventions).
Resident addresses are live addresses; overlay `FUN_` names use the preserved
import address.

## Live manager and profile mapping

The ELF initializes `gp` to `0x0060A9F0`. Ghidra's `iGpffffcc10` therefore
resolves to the global at `0x00607600`. The native reader chain is:

```text
[0x00607600]          = profile/state manager
[manager + 0x04]      = live profile pointer
reader base           = live profile pointer + 0x08
```

The manager global and its `+0x04` field are established by the resident reader
instructions. Heap addresses observed in runtime captures are allocation
instances, not fixed contracts.

`0x006075F8` is a neighboring global that points directly to the live profile.
It is not the manager consumed by these wrappers and must not be followed
through another `+0x04` field. [Save-data lifecycle](save_data.md#key-resident-function-map)
establishes that the save worker owns this allocation and manager construction
assigns it to manager `+0x04`; these paths share one live profile.

## Resident readers

The role names below are descriptive; the canonical export retains `FUN_`
symbols.

| Role | Export symbol | Runtime entry | Saved-value call | ELF file offset | Clean call bytes | Confirmed consumers |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Character unlocked | `FUN_001f54c0` | `0x001F54C0` | `0x001F54D0` | `0xF55D0` | `D08D070C` | resident ELF, `ETC.BIN` |
| Secondary bit unlocked | `FUN_001f5750` | `0x001F5750` | `0x001F5760` | `0xF5860` | `008E070C` | resident ELF, `ETC.BIN` |
| Small-table availability | `FUN_001f7030` | `0x001F7030` | `0x001F7040` | `0xF7140` | `1C8E070C` | resident ELF, `BTL.BIN` |
| Grouped availability | `FUN_001f70c0` | `0x001F70C0` | `0x001F70D0` | `0xF71D0` | `448E070C` | resident ELF, `ETC.BIN` |
| Character/Jutsu availability | `FUN_001f7210` | `0x001F7210` | `0x001F729C` | `0xF739C` | `D8FD070C` | resident ELF, `BTL.BIN` |
| Progress word | `FUN_001f7780` | `0x001F7780` | `0x001F7790` | `0xF7890` | `508F070C` | resident ELF, `BTL.BIN` |

The character wrapper reads one byte through `FUN_001e3740`, masks bit 0, and
normalizes it to Boolean. Character Select performs its ID, metadata, and
linked-form filtering outside this reader, so a set availability bit does not
by itself make an ID a roster entry.

The secondary wrapper reads a bit from the eight-byte field through
`FUN_001e3800`. The small-table and grouped wrappers return stored bytes through
`FUN_001e3870` and `FUN_001e3910`; their results are not normalized to Boolean.

The small table is not the stage-unlock bank. Its first 22 entries are indexed
by the resident [field-item name table](../localization/field_item_names.md#resident-field-item-name-table).
BTL `FUN_00876230` transfers units between these saved bytes and temporary
selection bytes at object `+0x1C + index`: adding a selected unit decrements
the saved byte, removing one increments it, and cancellation returns selected
units through `FUN_001f7000`. Thus this consumer treats them as counts rather
than simple unlock flags. BTL has six direct calls to the reader (encoding
`0C DC 07 0C`); ETC has none. The saved
mirror into the secondary byte bank belongs to
[Save-data layout](save_data.md#header-settings-and-resident-availability-state).
The semantics of small-table indices `22..31` remain unassigned. The selection
controller's return-all loop at BTL import/live `0x00876420/0x00876460` is
bounded to 22 indices, and its editable cursor ranges from 0 through `0x15`.
The decrement store is import/live `0x008766A0/0x008766E0`; the preceding
instructions explicitly pass cursor `+0x10` as `a1`. These counts and cursor
writes cannot produce indices `22..31` on the investigated native path.

Fresh/reset wrapper `FUN_001f6f90` clears all 32 bytes through
`FUN_001e3860`; this is a confirmed producer of zero for the unnamed ten
entries. The wider resident snapshot/restore pair also handles all 32 bytes,
but its lifecycle leads into the excluded Adventure controller and does not
establish an in-scope acquisition or a name for the ten entries. Its storage-copy contract remains with
[Save-data lifecycle](save_data.md#secondary-block-and-opaque-tail).

The Jutsu wrapper accepts only pairs allowed by `FUN_00307ed0` or
`FUN_001ff8d0`. It then derives the character's 24-byte record at
`profile + 0x38 + character_id * 0x18` and calls `FUN_001ff760` for the saved
Jutsu bit. The saved-bit read occurs after both metadata gates and therefore
cannot make an incompatible pair valid.

## Fighter and support availability dependencies

**Observation, high confidence:** `FUN_003b3db0` first applies the numeric and
fixed-metadata filters owned by
[Character identity](../gameplay/character_ids.md#selector-id-filters). It then
uses inverse mapper `FUN_001f7e70` to check the base of a recognized form before
reading the original ID's status bit through `FUN_001f54c0`. With the retail
inverse map, a base ID has no predecessor and needs only its own bit; a form
needs both its own bit and its base's bit. The decompilation expands additional
inverse checks, but every mapped retail base returns `-1`, so the recorded
mapping terminates after one dependency. No stronger arbitrary-chain behavior
is needed to explain the retail roster.

Ordinary editable form resolution in `FUN_003b4a90` calls this predicate for
the mapped form. A fixed-fighter constructor choice bypasses that saved-bit
check while retaining numeric and metadata filtering. Constructor and final
choice ownership belong to
[Character Select](character_select.md#appearance-fixed-choices-and-final-handoff).

The final saved-bit branches at resident `0x003B4024..0x003B409C` accept
when the manager global is null. This is a caller-side bypass, not a promise
that the resident reader accepts a null manager. The ordinary constructed
manager points to a fresh or loaded live profile.

`FUN_003bb210` assigns each of the 33 native support IDs state 4 when its
saved secondary bit is set, state 5 when clear, and state 7 to sentinel
`0x24`. Instructions `0x003BB258..0x003BB288` explicitly pass the table's
support ID as reader argument `a1`; the decompiler omits that argument.
The manager-null branch also produces state 4. The support selection path's
recommendation exception and compatibility predicate are independent of this
saved-bit reader; their complete rules belong to
[Character Select compatibility](character_select.md#compatibility).

Fresh/reset profile initialization grants the fixed 22-character set and
leaves all secondary support bits clear. The exact defaults and record writes
belong to [Fresh-profile initialization](save_data.md#fresh-profile-initialization).
Consequently, a clear support bit does not alone prove that support cannot be
selected: the recommendation exception must also be evaluated. Conversely,
granting a bit does not bypass compatibility.

## Resident stage-slot availability

**Observation, high confidence:** resident setter `FUN_001f57f0` and the
unrecognized reader at `0x001F58B0` access the word bitset rooted at
`gp - 0x3368 = 0x00607688`. They ignore their manager argument and use the
slot argument to select word `slot / 32` and bit `slot % 32`. The setter can
set or clear that bit; the reader normalizes it to Boolean. The reader's
complete `0x001F58B0..0x001F590B` instruction bytes were read directly
because no function is defined there. In particular,
`addiu v0,gp,-0x3368` at `0x001F58E8`, the word load at `0x001F58F0`,
and the mask/normalization sequence establish the same storage as the setter.

Initializer `FUN_001f5780`, called by fresh/reset initialization
`FUN_001f47d0` at `0x001F4878`, passes true for the exact 24-byte sequence
`0..23` at `0x005C06E0`. This enables every native Stage Select slot.
The direct resident setter inventory contains only initializer call
`0x001F57B8`; BTL and ETC contain no direct call (encoding `FC D5 07 0C`).
This bounds the observed producer inventory; indirect calls or a differently expressed
memory access are not excluded.

BTL import/live `FUN_00714420` / `0x00714460` tests all slots `0..23`
through resident `0x001F58B0` and appends accepted slots to the temporary
selector list. A null manager admits each slot directly. The list is therefore
all 24 slots after the recorded initialization. Its complete loop and call
bytes were corroborated at import `0x00714420..0x007144D3`; the direct call
is import/live `0x00714464/0x007144A4`, with bytes `2C D6 07 0C`.

This bitset is resident global state, separate from the serialized profile's
32-byte small table and from the manager's active or remembered stage slot.
The selector list is a temporary copy of eligibility. Active slot `+0x98`,
snapshot slot `+0x114`, preselection and battle-load handoff are owned by
[Stages](../gameplay/stages.md#archive-preload-adoption-and-switching).
The initializer sets the 24 native bits without clearing other bit positions;
the investigated selector reads only those 24 positions.

## In-scope mode gates

**Observation, high confidence:** the list builder `FUN_00384690` admits
physical Mode Select slots from the sign of the fixed result table at
`0x005D51D0`. This construction does not read profile availability. Free
Battle, Practice, Collection and Options have nonnegative results in the clean
table. Their complete slot/result mapping and remembered selection belong to
[Mode flow](mode_flow.md#mode-select-result-table).

Confirmation `FUN_00384760` accepts port 0 for each of those admitted slots;
port 1 is accepted directly only for Free Battle and Practice. Collection and
Options take the rejection-modal path for port 1. This is an input-source
restriction, not a saved unlock: `FUN_003849c0` passes 0 or 1 from the two
Circle actions decoded by `FUN_00384cd0`. Instructions
`0x00385524..0x00385538` in `FUN_003854f0` corroborate the two source words
from input context `+0x84/+0xFC` into controller `+0x3C/+0x40`.
The accepted port is copied to temporary manager field `+0x18`; this path
does not write the live profile. The gate is bounded to these four modes;
other branch semantics are outside this investigation.

## Jutsu admission and saved bits

**Observation, high confidence:** `FUN_001f7210` accepts a pair when either
native owner predicate `FUN_00307ed0` returns exactly 1 or cross-character
predicate `FUN_001ff8d0` returns nonzero. Only then does it read the saved
selector bit. `FUN_00307ed0` checks both `character == selector >> 1` and
the display record's signed owner halfword at `+0x0C`; matching the numerical
pair alone is insufficient. The owner path bypasses the cross-character
exclusion tables.

Within the selector domain used by the native screen, the cross-character
predicate has these fixed data inputs:

| Input | Resident address | Complete bounded extent |
| --- | ---: | --- |
| Character IDs rejected by this predicate | `0x005C0C50` | 10 signed halfwords |
| Special selectors eligible for cross-character checks | `0x005C0C70` | 26 words |
| Selector-exclusion lists | `0x005C0CE0` | 12 rows of 32 words, each terminated by `-1` |
| Character-to-list mapping | `0x005C12E0` | 43 pairs of words |
| Restricted selector exception | `0x005C1440` | one `0x28`-byte row |

The rejected character IDs are `0x1A, 0x1D, 0x1F, 0x21, 0x08, 0x14,
0x17, 0x18, 0x1E, 0x20`. The 26 special selectors, in source order, are:

```text
8D 16 19 1B 1F 21 45 47 4B 57 5D 69 3F
75 85 89 8B 9B AB 91 8F A5 A9 A7 34 83
```

A selector outside that set is rejected by the cross-character path. For a
mapped character, finding the selector in its list rejects it; a first-word
`-1` rejects every special selector. An unmapped character otherwise starts
admitted after the preceding gates. The final exception for `0x34` restricts
it to character `0x46`; it does not admit a pair that failed an earlier gate.
All table bytes `0x005C0C50..0x005C1467` were read. The table below
records every character/list mapping; numeric IDs avoid assigning unrecovered
display names. Entries are exclusions from the special set, before the `0x34`
exception.

| List | Character IDs, hexadecimal | Excluded selectors, hexadecimal |
| ---: | --- | --- |
| 0 | `2F 30 33 31 32 26 38 25 37 24 36 23 35 22 34 49 4B` | All (`-1` first word) |
| 1 | `03 28 43` | `8D 16 19 21 45 47 4B 57 5D 69 3F 75 85 89 8B 9B AB 91 8F A7 34 83` |
| 2 | `29` | `8D 16 19 21 45 47 4B 57 5D 69 3F 75 85 89 8B 9B AB 91 8F A7 34` |
| 3 | `4C` | `8D 19 1B 1F 21 45 47 4B 57 5D 69 3F 75 89 8B 91 A5 A9 A7 34 83` |
| 4 | `07 06 0A 41 47 48 40 53 59 4D 3F 5D` | `8D` |
| 5 | `01 27 39` | `A7` |
| 6 | `0F` | `8D 1B AB` |
| 7 | `2E` | `8D A7` |
| 8 | `55` | `8D 1B` |
| 9 | `4E` | `21` |
| 10 | `3E` | `9B 8D` |
| 11 | `3D` | `8D 1B 1F 4B A5 A9` |

For example, character `0x03` admits special selectors `0x1B, 0x1F, 0xA5,
0xA9`; character `0x29` additionally admits `0x83`. Character `0x4C` admits
`0x16, 0x85, 0x9B, 0xAB, 0x8F`. A form assigned list 0 can still use its
metadata-valid own pair through the earlier owner predicate. Each admitted
pair still needs its saved bit, so the tables establish eligibility rather
than acquired content.

Fresh initialization `FUN_001f7180 -> FUN_001ff670` clears each 24-byte record
and grants the two own selector bits, plus `0x34` for character `0x46`.
The third default slot is `-1` at resident `0x00406AE0` for other characters.
Setter `FUN_001f72d0` checks only the cross-character predicate when adding a
bit (`value == 1`); clearing skips that predicate. Default own bits therefore
come from the initializer rather than requiring that setter to admit them.
The reader's owner-or-cross-character contract remains decisive after a bit
has been written.

### Auxiliary Jutsu selectors `0x34` and `0x35`

BTL `FUN_006bc400` advances through selector IDs `2..0xBB` and includes a
candidate only when resident `FUN_001f7210` accepts the selected-character and
selector pair. `FUN_006bc610` uses the same predicate when counting the row's
available choices. This compatibility gate runs before the saved availability
bit.

Boot initialization populates two adjacent selector-table entries from the
auxiliary metadata object at `0x0059C7A0`:

| Mapping | Selector | Table entry | Display record | Record `+0x0C` | CCS resource |
| --- | ---: | ---: | ---: | ---: | --- |
| T2210 `Ninja Hound Summoning` | `0x34` | `0x005A24C0` | `0x0059C684` (array index 1) | `0x0034001A` | `2kkvcha1.ccs` |
| T2211 `Demon Wind Bomb` | `0x35` | `0x005A24C8` | `0x0059C72C` (array index 3) | `0x0035001A` | `2nrocha1.ccs` |

Stores at `0x005D88E8` and `0x005D88F4` write the display-record pointers as
auxiliary action base `+0x54` and `+0xFC`. `FUN_00307ed0` derives a selector's
native paired owner as `selector >> 1` and requires the record's low halfword
at `+0x0C` to match it. Both records therefore encode metadata owner `0x1A`;
the high halfword is the selector ID. Owner `0x1A` is not a playable character
entry. Classic Naruto's runtime character ID is `0x01`.

Selector `0x34` has an explicit cross-character exception. It appears in the
special-selector list at `0x005C0C70`, and the exception row at `0x005C1440` is
`0x34, 0x46, -1`, admitting Kakashi (`0x46`). Fresh-profile initialization also
adds bit `0x34` to character `0x46`'s availability record.

Selector `0x35` is absent from the special-selector list. Its only
metadata-compatible owner is `0x1A`, which has no entry in the canonical
74-character playable reference. The per-character lists read by
`FUN_001ff8d0` are exclusions from the cross-character path. Ordinary Jutsu
Select therefore cannot admit `Demon Wind Bomb` for a playable character even
when its saved availability bit is set.

The selector has complete generic consumers. Jutsu Select compositor
`FUN_006bcb30` resolves its title through `FUN_00885f00` and resident accessor
`0x00307C80`; resident `FUN_00307c60` returns the paired CCS resource. Fighter
initialization `FUN_00219620` decodes the selector through `FUN_00307eb0` and
copies odd selector `0x35` records 2 and 3 into the fighter's live Jutsu action
slots. The selector is consumable when supplied, but the native producer does
not supply it for a playable character.

## Progress gates

`FUN_001f7780` passes `profile + 0xDFC` and the caller's progress ID to
`FUN_001e3d40`, which loads the 32-bit word at `base + 0xE60 + id * 4`.
Resident selector `FUN_0038bac0` and Practice settings consumers in `BTL.BIN`
use ID `0x6A` as a Boolean gate. A zero value lowers the six-value Strength
selector's maximum from `5` to `4`; the sixth value is the displayed Ultimate
difficulty tier. One producer for slot `0x6A`, on the finite Survival result
path, is summarized below.

The absolute profile offset for word-bank index `0x6A` is `0x1E04`. It is
independent of byte-bank index `0x6A` at `0x216A`. Resident input
`FUN_0038bac0` and draw `FUN_0038c160` both reduce their maximum only when
the manager exists and the word is zero; a null manager retains maximum 5.
Four BTL input/draw call sites use the same condition: import/live
`0x0087FE6C/0x0087FEAC`, `0x00880548/0x00880588`,
`0x0088199C/0x008819DC`, and `0x00881EE4/0x00881F24`.
Instruction bytes preceding the split input bodies establish their default maximum
from the appropriate row-count table, then its reduction to 4. Menu row
ownership and the separate enabled-row conditions belong to
[Practice mode](../gameplay/practice_mode.md#row-availability).

### Recovered difficulty-word producer

**Observation, high confidence:** BTL routine export/live
`0x006EC570/0x006EC5B0` writes `FUN_001f7750(manager, 0x6A, 1)` when the
finite Survival result controller's course index is at least `0x18`. In the
native 25-course domain only course 24 satisfies that test, so acknowledging an
eligible result for that course sets word `0x6A` unless it is already exactly
1. Obtaining a top-three time is not required. The producer, its admission
gates, the course table and the final-result text announcing the Ultimate
difficulty tier are recorded in
[Survival](../gameplay/survival.md#difficulty-word-producer). BTL has four
direct calls to `FUN_001f7750` and ETC none; other writers, inlined writes, and
indirect calls remain possible.

### Form progress gate

Character Select uses an independent progression gate for linked forms.
`FUN_003b5df0` sets the selector object's form field at `+0x18` when held-input
mask `0x08` is active. Its call to `FUN_001f7fb0` at `0x003B5E3C` immediately
clears that field when the gate returns false, before `FUN_003b4a90` resolves an
eligible base character through `FUN_001f7c80`.

`FUN_001f7fb0` reads word-bank index 0 through
`FUN_001e3d40(profile + 0xDFC, 0)`, resolving to profile offset `0x1C5C`, and
returns true only when the value exceeds `0x65`. Runtime-memory comparison
corroborated values `0x66` in a fully progressed profile and `0` without a
loaded save. The complete `0x001F7FB0..0x001F8007` instructions show a signed
comparison and a zero/false result when the manager is null. This differs from
the manager-null admission branches in the roster and difficulty consumers.
[Save-data lifecycle](save_data.md#secondary-block-and-opaque-tail) identifies
this word as a main-progression ordinal, without assigning individual story
chapters. The ordinal's acquisition flow is outside this investigation.

## Stored availability fields

[Save-data record format and lifecycle](save_data.md#record-layout) owns the
complete profile layout. Offsets below are relative to the reader base
(`profile + 0x08`).

| Field | Offset | Length/count | Fully unlocked loaded profile | No-save runtime profile |
| --- | ---: | ---: | --- | --- |
| Character status | `0x900` | 94 bytes | ID 0 is `FF`; IDs 1-93 are `03` | Mostly `00`; `03` at IDs 57-61, 65-70, 73, and 78-87 |
| Secondary bitset | `0x960` | 8 bytes / 64 bits | all `FF` | all `00` |
| Small availability table | `0x968` | 32 bytes | all `FF` | all `00` |
| Group 0, Figures/Dolls | `0x988` | 93 bytes | index 0 is `03`; remainder `FF` | all `00` |
| Group 1, Music | `0x9E5` | 41 bytes | all `FF` | all `00` |
| Group 2, Voice | `0xA0E` | 155 bytes | all `FF` | all `00` |
| Group 3, Skills/Ultimate Jutsu | `0xAA9` | 168 bytes | all `FF` | all `00` |
| Group 4, Movies | `0xB51` | 7 bytes | index 0 is `03`; remainder `FF` | all `00` |
| Group 5, Dioramas | `0xB58` | 12 bytes | all `FF` | all `00` |

Native grouped-table reset `FUN_001e39b0` independently confirms the six counts
as `93`, `41`, `155`, `168`, `7`, and `12`. ETC record tables, viewer group
constants, and embedded class strings establish the labels. `ETC.BIN` consumes
all six groups across Collection and other frontend paths.

## Native grouped-content lifecycle

Overlay addresses follow
[Retail game file identities](files/file_identities.md#address-conventions).
The six viewer prologues select these groups:

| Group | Content | Count | Record table, live | Record size |
| ---: | --- | ---: | ---: | ---: |
| 0 | Figures/Dolls | 93 | `0x006DADE0` | `0x30` |
| 1 | Music | 41 | `0x006DF7B0` | `0x10` |
| 2 | Voice | 155 | `0x006E0E00` | `0x0C` |
| 3 | Skills/Ultimate Jutsu | 168 | `0x006DDE70` | `0x10` |
| 4 | Movies | 7 | `0x006DF170` | `0x10` |
| 5 | Dioramas | 12 | `0x006E1F70` | `0x88` |

Figure and Voice content also have 31-entry character-bundle tables. Their
`0x14`-byte records contain character ID, price, first record, count, and
pointer. The live tables are `0x006DBF50` and `0x006E1550`.

The grouped bytes have these native meanings:

| Value | Meaning |
| ---: | --- |
| `0` | default/unowned/not yet promoted; prerequisite tables can still make the item eligible |
| `1` | available or announced, still unowned |
| `2` | owned and NEW/unviewed |
| `3` | owned and viewed/stable |

ETC writes `0 -> 1` only for Figure, Voice, and Music offers. Skills can be
eligible while still zero, and no group-3 state-1 writer was found. The common
award dispatcher at live `0x006CAE30` writes state 2. Figure and Voice awards
operate on a character bundle; Skill and Music awards write one ID. No ETC
writer of Movie state 1 or 2, or Diorama state 1, was found.

Every Collection viewer requires a value greater than 1 and persists 3 after
opening the item. Setter sites are live `0x006BA834` (Figure), `0x006BBAE8`
(Diorama), `0x006C0694` (Skill), `0x006C2BE8` (Voice), `0x006C3FB0` (Movie),
and `0x006C569C` (Music). Exact-2 scans used for NEW badges corroborate state 2
across all six groups.

Figure records at `0x006DADE0` use their record index as the group-0 content
ID. `FUN_006ba590` reads the current entry through `FUN_001f70c0`; when its
value is greater than 1, it calls grouped setter `FUN_001f7090` with state 3
and changes the cached list-node byte to 3. State 3 is therefore the native
stable viewed-and-unlocked Figure state.

### Movie list state and acquisition limits

**Observation, high confidence:** Movie list initialization creates separate
`0x10`-byte nodes and copies grouped state into node byte `+0x08`. It reads
group 4 using the movie record's ID at import/live
`0x006C3678/0x006C36B8`, allocates a node at
`0x006C36A0/0x006C36E0`, and writes its cached byte at
`0x006C36F0/0x006C3730`; node `+0x04` holds that movie ID and `+0x0C` links
the next node. The loop first removes any old list nodes. Instruction bytes
`0x006C3600..0x006C3717` establish this continuation, which
`FUN_006c3440`'s decompilation omits. These are list-local copies, not pointers to
the saved movie-byte bank.

The confirmation path in `FUN_006c3d70` first requires cached node `+0x08`
to exceed 1. It then rereads group 4 for node `+0x04` at import/live
`0x006C3F3C/0x006C3F7C` and rejects a saved byte below 2. Only after both
checks does import/live `0x006C3F70/0x006C3FB0` write saved state 3; the
following list traversal also changes the cached byte to 3. Thus an admitted
cached node alone cannot bypass the current saved ownership check. Cleanup
`FUN_006c3250` releases the list nodes and list owner at viewer `+0x5C`;
this lifecycle contains no producer of newly owned movies.

The wider resident availability restore reaches all seven movie bytes, but
its enclosing lifecycle enters the excluded Adventure controller, whose
acquisition logic is not interpreted here. The copy layout is
owned by [Save-data lifecycle](save_data.md#secondary-block-and-opaque-tail).
Literal callback-pointer searches for resident grouped setters
`0x001F7090`/`0x001E3880` and small-table setter `0x001E3860` found no
embedded pointers in the resident ELF, BTL or ETC. This bounds only
descriptor-based callbacks: register-built
targets, register-carried interior profile pointers and other bulk writes are
not excluded. Movie state-1/state-2 acquisition and nonzero producers or
semantics for small-table indices `22..31` remain unresolved within scope.

### Collection-root NEW badges

The Collection-root render callback at export/live
`0x006B53C0/0x006B5400` builds three category flags:

- Characters scans all Dioramas, then Figure, Skill, and Voice entries grouped
  through the 75-entry master character table at live `0x006D9840`;
- Movie scans all seven group-4 entries;
- Music scans all 41 group-1 entries.

Every scan tests exactly for state 2. A category draws NEW only when its flag
was set.

### Derived Diorama unlocks

Diorama list initialization at export/live `0x006BB550/0x006BB590` visits all
12 records. A record contains up to six signed linked character IDs at
`+0x14 + n * 0x0C`. For a Diorama whose state is below 2, the initializer skips
negative IDs and tests whether any linked character owns any Figure, meaning a
group-0 state greater than 1. The first success persists Diorama state 2; the
viewer later converts it to state 3. The rule is any linked character, not all
six.
