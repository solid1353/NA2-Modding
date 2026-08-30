# Content availability and save-backed unlock state

This document records the resident-ELF readers that expose save-backed content
availability to the frontend, Adventure, and battle overlays. It separates the
confirmed data and call contracts from the `features.general.unlock_all` patch that
overrides those reads.

## Research coverage

- **Assigned scope:** save-backed content availability: resident accessors and
  hook seams, the stored arrays they expose, and the frontend/ETC consumers
  needed to establish native grouped-content semantics.
- **Exploration depth:** the resident reader families and bounded
  character/jutsu gates were traced; all six ETC Collection viewer groups and
  their fixed record tables were decoded; direct state-1, state-2, and state-3
  writers in ETC were inventoried; and the complete Collection-root NEW scans
  and 12-record Diorama derivation pass were checked. Coverage is exhaustive
  for those fixed group tables, viewer state transitions, and direct ETC setter
  sites, but not for every prerequisite or acquisition producer in the game.
- **Confirmed coverage:** historical savestates corroborated the resident
  layout, and an earlier user-observed Figure-viewer run corroborated the
  native stable state used by the documented override.
- **Unresolved or untested:** movie acquisition lies outside ETC; several
  eligibility tables are only bounded through their consumers; and
  indirect/computed callers may exist beyond the direct-reference inventory.
  No controlled runtime matrix exercised all groups or lifecycle values.
- **Deliberate exclusions and overlap:** Adventure consumer behavior was not
  analyzed in this pass. Human-facing labels and broader profile serialization
  remain owned by their dedicated documents.
- **Evidence limitations:** conclusions combine static resident/ETC tracing,
  historical savestates, and one earlier user-observed Figure-viewer run; they
  do not constitute exhaustive runtime validation of every acquisition path,
  group, or lifecycle value.

## Evidence and identity

Static analysis uses the canonical Ghidra 12.1.2 exports under
`@disassembly/NA2/` for clean `@source/NA2.iso.files/SLPS_258.37`:

- size: `5,273,256` bytes;
- SHA-256: `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`;
- resident segment mapping for the functions below: ELF file offset equals
  runtime address minus `0x000FFF00`.

On 2026-08-10, direct byte inspection compared the extracted `eeMemory.bin`
members of two user-supplied NA v2.28 savestates for serial `SLOP-NA228`, CRC
`7E793241`: SS1 had a fully unlocked save loaded, while SS2 had no loaded save.
The memory values observed in those captures and the static reader contracts
below are **high-confidence facts**. Later ETC analysis resolves all six
grouped-table meanings and their native `0..3` lifecycle below.

## Live manager and profile mapping

The ELF initializes `gp` to `0x0060A9F0`. Ghidra's `iGpffffcc10` therefore
resolves to the stable global at `0x00607600`. Both captures contain this
pointer chain:

```text
[0x00607600]             = 0x00CA4700  profile/state manager
[0x00CA4700 + 0x04]      = 0x00C9ED50  live profile pointer
reader base              = 0x00C9ED50 + 0x08 = 0x00C9ED58
```

The heap addresses are observations from these captures, not fixed allocation
contracts. The global address and the manager's `+0x04` field are confirmed by
the resident reader instructions.

`0x006075F8` is a neighboring global whose captured value is directly
`0x00C9ED50`. It is not the manager consumed by these wrappers and must not be
followed through the manager's `+0x04` field. The exact wider role of this
neighboring direct profile pointer remains unproven.

## Resident reader functions

The following role names are the meaningful names used by this documentation;
the canonical export currently retains its `FUN_` symbols.

| Role | Export symbol | Runtime entry | Overridden read call | ELF hook offset | Clean call bytes | Confirmed consumers |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Character unlocked | `FUN_001f54c0` | `0x001F54C0` | `0x001F54D0` | `0xF55D0` | `D08D070C` | resident ELF, `ETC.BIN`, `ADV.BIN` |
| Secondary bit unlocked | `FUN_001f5750` | `0x001F5750` | `0x001F5760` | `0xF5860` | `008E070C` | resident ELF, `ETC.BIN` |
| Small-table availability | `FUN_001f7030` | `0x001F7030` | `0x001F7040` | `0xF7140` | `1C8E070C` | resident ELF, `BTL.BIN` |
| Grouped availability | `FUN_001f70c0` | `0x001F70C0` | `0x001F70D0` | `0xF71D0` | `448E070C` | resident ELF, `ETC.BIN`, `ADV.BIN` |
| Character/jutsu availability | `FUN_001f7210` | `0x001F7210` | `0x001F729C` | `0xF739C` | `D8FD070C` | resident ELF, `BTL.BIN`, `ADV.BIN` |
| Progress word / Ultimate difficulty gate | `FUN_001f7780` | `0x001F7780` | `0x001F7790` | `0xF7890` | `508F070C` | resident ELF, `BTL.BIN` |

The character wrapper reads one byte through `FUN_001e3740`, masks bit 0, and
normalizes it to Boolean. Character-select call paths perform their native ID,
metadata, and linked-form filtering outside this reader. A fully unlocked save
can therefore set bit 0 for every stored ID without making every ID a roster
entry.

The secondary wrapper reads a bit from the eight-byte field through
`FUN_001e3800`. The small-table and grouped wrappers return stored bytes through
`FUN_001e3870` and `FUN_001e3910`; their values are not normalized to Boolean.

The jutsu wrapper first accepts only pairs allowed by `FUN_00307ed0` or
`FUN_001ff8d0`. It then derives the character's 24-byte record at
`profile + 0x38 + character_id * 0x18` and calls `FUN_001ff760` for the saved
jutsu bit. The hook at `0x001F729C` is after both metadata gates, so overriding
that call cannot create nonexistent character/jutsu pairs.

### Auxiliary Jutsu selectors `0x34` and `0x35`

The BTL Jutsu Select list does not enumerate every populated resident selector.
BTL export `FUN_006bc400` advances through selector IDs `2..0xBB` and admits a
candidate only when resident `FUN_001f7210` accepts the selected-character and
selector pair; `FUN_006bc610` uses the same predicate when counting the row's
available choices. This compatibility gate runs before the saved availability
bit described above.

Boot initialization populates two adjacent selector-table entries from the
auxiliary metadata object at `0x0059C7A0`:

| Mapping | Selector | Table entry | Display record | Record `+0x0C` | CCS resource |
| --- | ---: | ---: | ---: | ---: | --- |
| T2210 `Ninja Hound Summoning` | `0x34` | `0x005A24C0` | `0x0059C684` (array index 1) | `0x0034001A` | `2kkvcha1.ccs` |
| T2211 `Demon Wind Bomb` | `0x35` | `0x005A24C8` | `0x0059C72C` (array index 3) | `0x0035001A` | `2nrocha1.ccs` |

Stores at `0x005D88E8` and `0x005D88F4` write those display-record pointers as
auxiliary action base `+0x54` and `+0xFC`. `FUN_00307ED0` derives a selector's
native paired owner as `selector >> 1` and requires the record's low halfword at
`+0x0C` to match it. Both records therefore encode native metadata owner
`0x1A`; the high halfword is the selector ID. Owner `0x1A` is not a playable
character entry. Classic Naruto's runtime character ID is `0x01`.

T2210 has an explicit cross-character compatibility exception. Selector
`0x34` appears in the special-selector list at `0x005C0C70`, and the exception
row at `0x005C1440` is `0x34, 0x46, -1`, admitting character `0x46` (Kakashi).
Fresh-profile initialization separately adds bit `0x34` to character `0x46`'s
availability record. The user confirmed the resulting Jutsu Select entry as
Kakashi's `Ninja Hound Summoning`.

T2211 has no corresponding exception: selector `0x35` is absent from the
special-selector list. Its only metadata-compatible character is direct owner
`0x1A`, which has no entry in the canonical 74-character playable reference.
Consequently, ordinary Jutsu Select cannot admit `Demon Wind Bomb`, even when
all saved availability bits are forced available; the override is downstream
of this failed compatibility gate.

#### Candidate Classic Naruto assignment

Classic Naruto (`0x01`) is the deliberately selected recipient, not the clean
selector's native metadata owner. A rejected data-only candidate appended
selector `0x35` to the special-selector array and Classic Naruto's per-character
list. Slot-1 runtime evidence under build CRC `ED4F0A84` confirmed that all
three candidate words were resident, but `Demon Wind Bomb` remained absent.
Re-reading `FUN_001FF8D0` established why: the per-character lists are
exclusions. Finding selector `0x35` in Classic Naruto's list returns false, so
the candidate explicitly rejected the requested pair.

The optional Demon Wind Bomb branch of `general.unlock_all` instead guards
the native special-compatibility call at runtime `0x001F7254` / ELF
offset `0xF7354` (clean call bytes `34FE070C`). Its wrapper returns true only
for character `0x01` with selector `0x35`; every other pair delegates to clean
`FUN_001FF8D0`. The existing downstream `features.general.unlock_all` Jutsu hook
then reports the admitted pair available without changing saved progress or
exposing the selector to other characters. Runtime validation of the corrected
candidate remains pending.

The selector nevertheless has complete generic consumers. Jutsu Select row
compositor `FUN_006bcb30` resolves a selected title through `FUN_00885f00` and
resident accessor `0x00307C80`. Resident `FUN_00307c60` returns the paired CCS
resource. During fighter initialization, `FUN_00219620` decodes the selector
through `FUN_00307eb0`; even selector `0x34` copies auxiliary action records
0/1, while odd selector `0x35` copies records 2/3 into the fighter's live Jutsu
action slots. T2211 is therefore implemented and consumable if selector
`0x35` is supplied, but the clean Jutsu Select candidate producer never
supplies it for a playable character.

`FUN_001f7780` passes `profile + 0xDFC` and the caller's progress ID to
`FUN_001e3d40`, which loads the 32-bit word at `base + 0xE60 + id * 4`.
Resident selector `FUN_0038bac0` and the Practice settings consumers in
`BTL.BIN` use ID `0x6A` as a Boolean gate that lowers the six-value Strength
selector's maximum from `5` to `4` when zero. The sixth value is the displayed
Ultimate difficulty tier. The producer and native unlock event for slot
`0x6A` remain unresolved.

## Stored layout and observed values

Offsets in this table are relative to the reader base (`profile + 0x08`).

| Field | Offset | Length/count | SS1 with unlocks | SS2 without loaded save |
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

`FUN_001e39b0`, the native grouped-table reset, independently confirms the six
counts as `93`, `41`, `155`, `168`, `7`, and `12`. The paired captures confirm
the fully unlocked byte values. ETC record tables, viewer group constants, and
embedded class strings independently establish the labels above. `ETC.BIN`
consumes all six groups across Collection and other frontend paths; `ADV.BIN`
also consumes grouped values.

## Read-only unlock override

Catalog setting `features.general.unlock_all` selects injection
`general.unlock_all`. Each guarded JAL replaces only the
saved-value read inside a resident wrapper and leaves the wrapper and its
callers intact:

- character IDs below 94 report available;
- secondary IDs below 64 report available;
- small-table IDs below 32 return `FF`;
- grouped IDs are bounded by the six native counts and reproduce the SS1
  values, including `03` at group 0/index 0 and group 4/index 0;
- metadata-valid character/jutsu pairs report available after the native gates;
- progress ID `0x6A` reports `1`, while every other progress ID retains the
  native word-bank read.

No setter is hooked. The content helpers ignore the live profile pointer, and
the Ultimate helper reads the live word bank only for IDs other than `0x6A`;
none of them writes the profile. Settings, progress, currency, inventory,
statistics, and availability bytes therefore remain unchanged. Disabling the
catalog setting omits the injection and restores native save-dependent reads.

The `0xF7890` hook, clean call bytes, reader contract, and both selector
consumer families are statically verified. User runtime testing on 2026-08-21
confirmed that `unlock_all` exposes Ultimate difficulty.

### NUN5 PNACH port

Static structural matching against verified NUN5 `SLES_556.05` (SHA-256
`20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D`)
establishes the corresponding resident wrappers and saved-value call seams:

| Role | NUN5 wrapper | Overridden read call | Clean word |
| --- | ---: | ---: | ---: |
| Character unlocked | `0x001FBE20` | `0x001FBE30` | `0x0C07A52C` |
| Character Select R1-form progress | `0x001FEA10` | `0x001FEA34` | `0x0C07A6D0` |
| Progress word / Ultimate difficulty gate | `0x001FE1D0` | `0x001FE1E0` | `0x0C07A6D0` |
| Secondary bit unlocked | `0x001FC0D0` | `0x001FC0E0` | `0x0C07A55C` |
| Small-table availability | `0x001FDA10` | `0x001FDA20` | `0x0C07A578` |
| Grouped availability | `0x001FDAA0` | `0x001FDAB0` | `0x0C07A5A0` |
| Character/jutsu availability | `0x001FDC00` | `0x001FDC8C` | `0x0C081924` |

NUN5 grouped reset `FUN_001E9720` independently confirms the same six bounds:
`0x5D`, `0x29`, `0x9B`, `0xA8`, `7`, and `0x0C`. The clean Ultimate call
word is also verified directly at ELF file offset `0xFE360`. Resident selector
and BTL consumers pass progress ID `0x6A` through this shared wrapper.

The normal PNACH reuses the unchanged bounded C helpers and places
their 208 immutable bytes at `0x01FF5310..0x01FF53E0`, after the No Support
mutable storage and inside the same allocator-tail reservation. Its seven
guarded calls include a 32-byte leaf helper that returns `1` only for progress
ID `0x6A` and performs the native word-bank read for every other ID. The file
reserves the allocator tail, and its heap-end guard prevents payload and hook
writes before a clean boot has established the reservation. Each hook
additionally checks both halves of its clean NUN5 call word before replacing
it. Native wrapper, metadata, and caller behavior remain intact. User runtime
testing on 2026-08-21 confirmed that this port exposes Ultimate difficulty.

## Rejected character mask and correction

The first character implementation incorrectly treated the value from
`0x006075F8` as the availability manager. Applying the manager chain to that
direct profile pointer loaded `0x002DB117` from `profile + 0x04`; adding the
reader offsets then sampled resident executable bytes rather than the character
status array. Those bytes produced the false masks `FFFFFFFF`, `C1FFFFFF`, and
`3F003D81`.

The rejected mask hid valid characters and admitted the wrong set, which the
user observed as an inadequate and displaced character roster. The corrected
helper returns available for every bounded ID `0..93`, matching bit 0 of all 94
SS1 status bytes while retaining native roster filtering. On 2026-08-10, the
user confirmed in-game that this correction works.

## Character Select R1 form gate

On 2026-08-11, two user-supplied savestates captured the same Character Select
cell with R1 held under the `SLOP-NA228` / `7E5D178F` build:

- loaded-save SS1 (`BCBF29E676B3C2D81D75570F4BC1F5E5EB56A0C605594F335977D98640E44268`)
  displayed Naruto's linked form;
- no-save SS3 (`34C9DEC1A69DC2517A89E9FA45D1602EAA892959DB36B0C69DAE0ADC92121D16`)
  remained on ordinary Naruto even though `unlock_all` exposed the roster.

Their extracted `PAD.bin` members are byte-identical. In
`FUN_003b5df0` (`0x003B5DF0`), held-input mask `0x08` sets the Character
Select object's form-selection field at `+0x18`. The sole call to
`FUN_001f7fb0` at `0x003B5E3C` immediately clears that field when the function
returns false. `FUN_003b4a90` later consumes the field and maps eligible base
characters to their linked form through `FUN_001f7c80`.

`FUN_001f7fb0` (`0x001F7FB0`) reads saved integer index 0 through
`FUN_001e3d40(profile + 0xDFC, 0)`, which resolves to `profile + 0x1C5C`, and
returns true only when the value exceeds `0x65`. The loaded save contains
`0x66`; the no-save profile contains `0`. The wider meaning of this progression
field remains unresolved, but its role as the R1-form gate and the compared
values are high-confidence facts from the matching input and static call path.

The existing character-unlocked override cannot satisfy this independent
gate: it replaces the bit-0 character-status read inside `FUN_001f54c0`, while
the R1 path reads `profile + 0x1C5C`. The accepted implementation adds one
guarded JAL at ELF offset `0xF80D4` (runtime `0x001F7FD4`, clean bytes
`508F070C`) so only `FUN_001f7fb0` receives the fully unlocked reference value
`0x66`. It does not write the live profile or change other saved progression
reads. On 2026-08-11, the user confirmed in-game that R1 forms are accessible
without a loaded save.

## Collection figure lifecycle state

On 2026-08-11, three user-supplied Collection Figure savestates captured the
same Sakura viewer frame with byte-identical `PAD.bin` members:

- loaded-save SS2 with `unlock_all` enabled
  (`FD2D49C722D8ECBE5F9E39B795A0C9D3380D7FB14F9BE0E16BE6B4480DE0B7DA`)
  omitted the pedestal;
- no-save SS4 with `unlock_all` enabled
  (`5164F206FAAFD04378C4ED2E32D7AF832DD5A77369D563F7DA6E6C69D0BABD16`)
  produced the same screenshot and omitted the pedestal;
- loaded-save SS5 with `unlock_all` disabled
  (`7D7ADA1C34B951AB9072DCBED7B1E2AA1C1AB62657091D7BF45D05730F5D893A`)
  rendered the pedestal.

SS2 and SS5 contain the same fully unlocked availability arrays. In both, the
current group 0/index 3 entry is `03`; SS4's initially empty profile also
contains `03` at that entry after the viewer opens. Static ETC analysis explains
the transition: the Collection figure records at `0x006DADE0` use their record
index as the group 0 content ID, and the Sakura record is index 3.
`FUN_006ba590` reads the current entry through `FUN_001f70c0`; when its value is
greater than 1, it calls grouped setter `FUN_001f7090(..., 0, content_id, 3)`
and changes the cached list-node byte to `3`. Thus `3` is the native stable
viewed-and-unlocked figure state, not merely another arbitrary reference value.

The previously accepted `unlock_all` implementation returned `FF` for group 0
entries other than index 0. That masked the native setter on every subsequent
read and fed the figure loader a state the normal viewer immediately replaces
with `3`.
This is the only functional availability difference between the matching SS2
and SS5 loaded-save captures for the selected entry.

The accepted implementation therefore returns `3` for every bounded group 0
ID while retaining the existing values for groups 1 through 5. It continues to
expose all 93 figure entries, but represents each one in the native stable
unlocked state and no longer masks the viewer's `3` with `FF`. On 2026-08-11,
the user confirmed in-game that Collection figure pedestals render with
`unlock_all` enabled.

## Native grouped-content lifecycle

Clean `ETC.BIN` has SHA-256
`8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`.
Its MWo3 header remains resident at runtime, so live overlay addresses are the
preserved export addresses plus `0x40`; encoded absolute operands are already
live. The six viewer prologues independently select groups 0 through 5:

| Group | Content | Count | Record table, live | Record size |
| ---: | --- | ---: | ---: | ---: |
| 0 | Figures/Dolls | 93 | `0x006DADE0` | `0x30` |
| 1 | Music | 41 | `0x006DF7B0` | `0x10` |
| 2 | Voice | 155 | `0x006E0E00` | `0x0C` |
| 3 | Skills/Ultimate Jutsu | 168 | `0x006DDE70` | `0x10` |
| 4 | Movies | 7 | `0x006DF170` | `0x10` |
| 5 | Dioramas | 12 | `0x006E1F70` | `0x88` |

Figure and Voice content also have 31-entry character bundle tables, each
using `0x14`-byte records containing character ID, price, first record, count,
and pointer. Their live tables are `0x006DBF50` and `0x006E1550`.

The safe native meanings of grouped bytes are:

| Value | Meaning |
| ---: | --- |
| `0` | default/unowned/not yet promoted; eligibility can still come from prerequisite tables |
| `1` | available or announced, still unowned |
| `2` | owned and NEW/unviewed |
| `3` | owned and viewed/stable |

This qualification on zero matters: ETC writes `0 -> 1` only for Figure,
Voice, and Music offers. Skills can be eligible while still zero, and no
group-3 state-1 writer was found. The common award dispatcher at live
`0x006CAE30` writes state 2. Figure and Voice awards are bulk operations over a
character bundle; Skill and Music awards write a single ID.

Every Collection viewer requires a value greater than 1 and persists 3 after
opening the item. The setter sites are live `0x006BA834` (Figure),
`0x006BBAE8` (Diorama), `0x006C0694` (Skill), `0x006C2BE8` (Voice),
`0x006C3FB0` (Movie), and `0x006C569C` (Music). Exact-2 scans used for NEW
badges corroborate state 2 across all six groups. No ETC writer of Movie state
1 or 2, or Diorama state 1, was found; Movie acquisition lies outside this
overlay, and Diorama acquisition is derived as described next.

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
negative IDs and tests whether **any** linked character owns **any** Figure
(group-0 state greater than 1). The first success persists Diorama state 2;
the viewer later converts it to state 3. The rule is any linked character, not
all six.
