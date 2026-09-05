# Content availability and save-backed unlock state

This document records the resident readers and overlay consumers that expose
save-backed content availability.

## Research coverage

- **Assigned scope:** resident availability readers, their stored fields, and
  the frontend and battle consumers needed to establish native content-state
  semantics.
- **Exploration depth:** the resident reader families and bounded
  character/Jutsu gates were traced; all six ETC Collection groups and their
  fixed record tables were decoded; direct ETC state writers, Collection-root
  NEW scans, and the Diorama derivation pass were checked. The investigation
  did not trace every prerequisite or acquisition producer in the game.
- **Confirmed coverage:** the resident pointer and reader contracts, stored
  array bounds, Jutsu compatibility behavior, R1-form and Ultimate-difficulty
  progress gates, grouped-content meanings, viewer transitions, NEW scans, and
  Diorama derivation are established below.
- **Unresolved or untested:** movie acquisition, several eligibility-table
  producers, indirect callers outside the direct-reference inventory, and the
  producer for progress slot `0x6A` remain unresolved. No controlled runtime
  matrix exercised every content group and lifecycle value.
- **Deliberate exclusions and overlap:** profile serialization and the complete
  record layout belong to [Save-data record format and lifecycle](save_data.md).
  Character Select roster and selector presentation belong to
  [Native Character Select support behavior](character_select.md).
- **Evidence limitations:** static resident and ETC tracing establishes the
  control flow and fixed data. Read-only runtime-memory comparisons corroborate
  the stored values, but do not establish every acquisition path or lifecycle
  transition.

## Evidence identity

Static addresses use the clean resident ELF and conventions in
[Standard game file identities](files/file_identities.md).

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
through another `+0x04` field. Its wider role remains unresolved.

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

The Jutsu wrapper accepts only pairs allowed by `FUN_00307ed0` or
`FUN_001ff8d0`. It then derives the character's 24-byte record at
`profile + 0x38 + character_id * 0x18` and calls `FUN_001ff760` for the saved
Jutsu bit. The saved-bit read occurs after both metadata gates and therefore
cannot make an incompatible pair valid.

## Auxiliary Jutsu selectors `0x34` and `0x35`

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
`FUN_001ff8d0` are exclusions: finding a selector in the selected character's
list rejects the pair. Ordinary Jutsu Select therefore cannot admit
`Demon Wind Bomb` for a playable character even when its saved availability bit
is set.

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
difficulty tier. The producer and native unlock event for slot `0x6A` remain
unresolved.

Character Select uses an independent progression gate for linked forms.
`FUN_003b5df0` sets the selector object's form field at `+0x18` when held-input
mask `0x08` is active. Its call to `FUN_001f7fb0` at `0x003B5E3C` immediately
clears that field when the gate returns false, before `FUN_003b4a90` resolves an
eligible base character through `FUN_001f7c80`.

`FUN_001f7fb0` reads word-bank index 0 through
`FUN_001e3d40(profile + 0xDFC, 0)`, resolving to profile offset `0x1C5C`, and
returns true only when the value exceeds `0x65`. Runtime-memory comparison
corroborated values `0x66` in a fully progressed profile and `0` without a
loaded save. The wider meaning of the progression field remains unresolved.

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

The clean `ETC.BIN` identity is listed in
[Standard game file identities](files/file_identities.md).
Its MWo3 header remains resident at runtime, so live overlay addresses are the
preserved export addresses plus `0x40`; encoded absolute operands are already
live. The six viewer prologues select these groups:

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
