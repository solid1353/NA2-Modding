# Character asset tables

This document records how the retail game names, stores, and loads the files
and static data that make up a playable fighter, and how that storage differs
from NUN3 (`SLUS-21727`). It does not own the general CCS runtime, the
disc-wide file inventory, or battle behavior driven by the fighter data.

## Research coverage

- **Assigned scope:** Character-indexed CCS filename tables, the disc
  placement and contents of fighter CCS files, the static character record and
  its asset-bearing sub-tables, per-character code entry points, the
  jutsu-resource filename table, and the per-character voice archive layout, in
  NA2 and in the NUN3 lineage it extends.
- **Exploration depth:** All 94 rows of the NA2 filename tables and all 57 rows
  of the NUN3 tables were read. Record layouts, action records, animation-name
  tables, and one callback table were compared between the games for shared
  and NUN3-only IDs. CCS headers, section-type counts, and cross-container
  references were compared for representative body, low-detail body, and
  jutsu files, including every NUN3-only body file. Constructors and record
  loaders were compared in both boot ELFs through GhidrAssist MCP.
- **Confirmed coverage:** The four NA2 filename families and their complete
  ID-to-code mapping; the homologous NUN3 tables; disc placement; the
  dependency of every `3EYE` file on its `1???BOD1` model; the shared
  record layout and loader offsets; the action-record and animation-table
  lineage; the per-character factory and callback shape; the shared
  skeleton-container dependency and its NA2/NUN3 difference; the retained NUN3
  prefix of NA2's jutsu-resource table; and the ID-indexed voice archive.
- **Unresolved or untested:** Where jutsu sequences use `1???BOD1`, the
  consumers of the record's colour, texture, model, and
  effect name slots, the meaning of most action-record and `0x4C`-stride row
  fields, how the jutsu-resource table is indexed, per-character code outside
  the factory/constructor/callback entry points, and the internal layout of
  voice sub-archives remain open.
- **Deliberate exclusions and overlap:** General CCS parsing, lookup,
  cross-container resolution, and lifetime belong to
  [Resident CCS runtime](files/ccs_runtime.md); CCS tag identities belong to
  [CCS object types](files/ccs_object_types.md); the disc inventory belongs to
  [Disc and archive file inventory](files/disc_files.md). Character-ID
  semantics and the definition-table rows belong to
  [Character identity in battle](../gameplay/character_ids.md). Fighter
  construction and dispatch belong to
  [Battle entities](../gameplay/battle_entities.md); record fields with battle
  consumers belong to [Damage](../gameplay/damage.md), and action-record
  selection to [Action commands](../gameplay/action_commands.md).
- **Evidence limitations:** All findings are static reads of clean files and
  the maintained read-only analyses. No live-memory trace establishes load
  timing, residency, or how the game behaves with a missing or foreign asset.
  NUN3 findings say nothing about NUN3 runtime behavior. Working identities
  below are descriptive, not recovered original symbols.

## Evidence and address conventions

The clean resident identities and address conversions follow
[Retail game file identities](files/file_identities.md). Addresses are
resident EE addresses unless labelled as an overlay live address. CCS files
were gzip-decompressed in memory; no source file was modified.

## Character-indexed filename families

The boot ELF stores adjacent pools of 16-byte, NUL-terminated lowercase CCS
basenames. Each observed name has the form below, where `???` is a three-byte
character code:

| Family | String-pool runtime range | Pointer-table base | Direct resident references |
| --- | ---: | ---: | --- |
| `2???bod1.ccs` | `0x00401C48..0x004020E7` | `DAT_004020F0` / `0x004020F0` | `FUN_001E1530`, `FUN_001E80F0`, `FUN_00354640` |
| `1???bod1.ccs` | `0x00402268..0x00402707` | `DAT_00402710` / `0x00402710` | `FUN_001E1530`, `FUN_001E80F0`, `FUN_00354640`, `FUN_00358250` |
| `3???3eye.ccs` | `0x00402888..0x00402D27` | `DAT_00402D30` / `0x00402D30` | `FUN_001E1530`, `FUN_001E90F0`, `FUN_001E9180` |
| `3???3pct.ccs` | begins `0x00402EA8` | `DAT_00403350` / `0x00403350` | `FUN_001E80F0`, `FUN_001E93C0`, `FUN_00202640` |

**Observation:** Each pointer table has 94 slots indexed by character ID
`0..93`. For every ID, all four families are either null or name the same
three-byte code. The populated IDs are exactly the IDs with a dedicated row in
the [character-definition table](../gameplay/character_ids.md#character-definition-table):

```text
1 nrt  2 ssk  3 roc  4 gar  5 sik  6 nej  7 skr
10 hak 11 zbz 12 hnt 13 ten 14 tyo 15 ino 16 kib 17 sin 18 knk 19 tmr
22 hkg
34 jrb 35 kdm 36 tyy 37 skn 38 kmm 39 fou 40 khm 41 hnb 42 fir 43 sec
46 ank 47 nrv 48 ssv 49 rov 50 gav 51 tov 52 jrv 53 kdv 54 tyv 55 skv 56 kmv
57 nrw 58 skw 59 gaw 60 knw 61 tmw 62 chy 63 sco 64 ddr 65 new 66 tew
67 row 68 siw 69 guw 70 kkw 71 itw 72 ksw 73 nwv 75 scv 76 sch 77 cyb
78 kiw 79 snw 80 hnw 81 tyw 82 inw 83 jrw 84 tnw 85 szw 86 asw 87 krw
89 orw 90 kbw 91 ymt 92 sai 93 ssw
```

All other IDs, including 0, are null in all four tables. A valid numeric
character ID is therefore not by itself proof that any asset family exists for
that ID.

### NUN3 filename tables

NUN3 `SLUS_217.27` has the same four families as adjacent 60-slot pointer
tables:

| Family | NUN3 pointer-table base |
| --- | ---: |
| `2???bod1.ccs` | `0x0047D2F0` |
| `1???bod1.ccs` | `0x0047D3E0` |
| `3???3eye.ccs` | `0x0047D4D0` |
| `3???3pct.ccs` | `0x0047D5C0` |

**Observation:** Slot 0 and slots `57..59` are null. Slots `1..56` are all
populated. The rows NUN3 fills with a copy of the ID 1 definition (IDs 29, 31,
and 33), and the jutsu-bearing ID 26, repeat the `nrt` names instead of being
null. Every other slot names the same code as the NUN3 definition row. For IDs
present as fighters in both games, the NUN3 and NA2 codes are identical. The
NUN3-only codes are `kks` (8), `orc` (9), `guy` (20), `jry` (21), `itc` (23),
`ksm` (24), `tnd` (25), `szn` (27), `kbt` (28), `anb` (30), `nrz` (32), `asm`
(44), and `krn` (45).

## Disc placement and file contents

NA2 keeps fighter files in `DATA.CVM` directory `PL/`, with `3EYE/` holding the
`3???3EYE` and `3???3PCT` families. NUN3 keeps its `1???BOD1`, `2???BOD1`, and
`2???CHA0/1` files at the `DATA.CVM` root and the `3EYE`/`3PCT` pair in `3EYE/`.
The four filename tables hold bare basenames; the directory comes from the
resident path construction described under the per-fighter load path below.

### CCS format

**Observation:** Both games' fighter CCS files begin with the same header
section `0xCCCC0001` carrying `CCSF`, the container name, and version word
`0x123`, followed by the table of contents `0xCCCC0002`. Both use the same
section-type set in fighter files: `0x0100`, `0x0200`, `0x0300`, `0x0400`,
`0x0700`, `0x0800`, `0x0900`, `0x0A00`, `0x0C00`, `0x2000`, and, in some NA2
files, `0x1900` and `0x2400`, besides `0x0005` and `0xFF01`. The object-type
identities are in [CCS object types](files/ccs_object_types.md). NUN3's clean
`STAGE/S04.CCS` has the same header version.

**Observation:** The file families contain:

| Family | Content in the compared files |
| --- | --- |
| `2???BOD1` | Battle body: roughly 110 `ANM_` animations, the body `MDL_`/`OBJ_` hierarchy, one `TEX_` and several `CLT_` palettes, and `CMP_eff_dummy_*` effect anchors. NUN3 `2NRTBOD1` and NA2 `PL/2NRTBOD1` both hold 118 source files and 111 animations; NA2's copy has more `OBJ_` rows (4,467 against 3,492). |
| `1???BOD1` | A second, animation-free model: about 88 `OBJ_`/`MDL_` pairs, eye, mouth, and body textures. NUN3's compared copies (`1NRT`, `1KKS`, `1ASM`) also contain a `x\name\???\name.bmp` source; NA2's compared copies (`1NRT`, `1KKW`) do not. |
| `2???CHA0`, `2???CHA1` | Jutsu resources: `ANM_p???cha0*`/`cha1*` animations, effect models, and textures, bound to both the `2cmn` and `1cmn` skeleton containers. |
| `3???3EYE` | Every file in both games (78 in NA2, 52 in NUN3) names its own `#c\1???\max\1???bod1.max` as an external source; all but two NA2 files and one NUN3 file also contain `c\3???\anm\3???win*` animation sources. |
| `3???3PCT` | Name and portrait visuals; see [Disc and archive file inventory](files/disc_files.md#ccs-directory-map). |

**Inference (high confidence):** `1???BOD1` is a second character model,
separate from the `2cmn`-based battle body, that the `3EYE` win animations
use. **Hypothesis:** because `CHA` files bind to the `1cmn` skeleton container,
jutsu sequences may use the same model family.

**Observation:** NA2's `3EYE/` also holds `3EYE` and `3PCT` files for
NUN3-only codes `guy`, `itc`, `kks`, and `ksm`, which the NA2 filename tables do
not name. Their `3PCT` files contain only a `p\cut_sp\sp_???.bmp` source and no
`TEX_name` object; they are the four name-less `3PCT` members noted in the disc
inventory. Their `3EYE` files reference `1???bod1` models that are not on the
NA2 disc.

**Observation:** NA2 `PL/` also contains `1???BOD1` files for NUN3-only codes
`asm`, `jry`, `kbt`, `krn`, `orc`, `szn`, and `tnd`, and for `ukn`/`ukv`. Each
is smaller than, and not byte-identical to, the NUN3 file of the same name. No
`2???BOD1` file exists on the NA2 disc for any NUN3-only code, and the only
NUN3-only `CHA` file is `2KBTCHA0`. No NA2 executable or overlay contains any of
these `1???bod1.ccs` names as a string.

### Shared skeleton containers

Every compared body and jutsu file names `#c\2cmn\max\2cmnbod1.max` as an
external source, and jutsu files also name `#c\1cmn\max\1cmnbod1.max` and the
`1cmn` textures. The `#` rows are cross-container references resolved against
already loaded containers by name; see
[Cross-container references](files/ccs_runtime.md#cross-container-references).
The boot ELF names the providers `cmn/2cmnbod1.ccs` and `pl/1cmnbod1.ccs`.

**Observation:** NA2's `CMN/2CMNBOD1.CCS` holds 178 object names, all of which
are also in NUN3's 191. The 13 NUN3-only names are the `muffler` chain
(`OBJ_`/`MDL_2cmn00t0 muffler`, `muffler d`, and `muffler1..3`) and
`CMP_`/`OBJ_eff_dummy_cmnrun0` and `OBJ_eff_dummy_spn0`. NA2's
`PL/1CMNBOD1.CCS` lacks NUN3's `1cmn00t0 cloth3`, `joe d`, and `joe01` object
and model rows.

**Observation:** Checking every external `2cmnbod1` reference in the thirteen
NUN3-only `2???BOD1` files against NA2's provider: `jry`, `guy`, `szn`, `kbt`,
and `anb` resolve completely. `kks`, `orc`, `itc`, `ksm`, `krn`, `nrz`, and
`asm` each reference the four `OBJ_2cmn00t0 muffler*` rows; `tnd` also
references `muffler d`. NUN3 `2KKSCHA0` and `2ASMCHA0` reference
`OBJ_1cmn00t0 joe01` and `cloth3`, which NA2's `1cmnbod1` lacks.

**Inference (high confidence):** NA2's providers have no record for those
names, and the NA2 resolver leaves an unmatched `#` record at runtime sentinel
`4`, which is not a usable object pointer.

## Character records

The definition table's record pointer (see
[Character identity](../gameplay/character_ids.md#character-definition-table))
selects a static record in the boot ELF. The same record layout is used by
NUN3.

| Offset | NA2 and NUN3 content |
| ---: | --- |
| `+0x00` | Character ID |
| `+0x04` | Shift-JIS display name |
| `+0x08` | `2???bod1.ccs` basename |
| `+0x0C` | 12 × `0x1E`-byte colour-palette names, for example `CLT_2nrtbody`, `CLT_2nrtbodyc1`, `CLT_2nrtbodyc2` |
| `+0x10` | Two `0x1E`-byte texture names, for example `TEX_2nrtbody` |
| `+0x14` | Two `0x1E`-byte model names, for example `MDL_2nrt00t0 body` |
| `+0x18` | Effect-anchor object name `OBJ_eff_dummy_???hol0` |
| `+0x1C` | Callback-function table (see below) |
| `+0x28` / `+0x2C` | Action-record count / `0x54`-byte action records |
| `+0x30` | Optional alternate action-record pointer, zero in the compared rows |
| `+0x38` / `+0x3C` | Row count / `0x4C`-byte rows |
| `+0x44` / `+0x48` | Animation count / array of `ANM_` name pointers |
| `+0x58..+0xD8` | Physical and balance parameters; confirmed consumers are in [Damage](../gameplay/damage.md#confirmed-character-record-fields) |
| `+0xE0` | Pointer to the record itself, used by the constructor as the record descriptor |

**Observation:** For Classic Naruto (ID 1) and Classic Sakura (ID 7) every
parameter word in `+0x58..+0xDC` is identical in the two games; only
pointers, the action count, and the row count differ. Classic Naruto has 47
action records and 183 rows in NUN3 against 48 and 190 in NA2.

**Observation:** The NUN3 record loader `FUN_001A6190` copies the same 55
record words (`+0x00..+0xD8`) that NA2's `FUN_002151E0` copies, but to fighter
`+0x80..+0x158` instead of `+0x8C..+0x164`. Later derived fields also move: for
example the action count goes to NUN3 `+0x988`/`+0x98A` against NA2
`+0xA38`/`+0xA3A`, and the action-record pointer to NUN3 `+0x9A4` against NA2
`+0xA54`. NA2's loader also runs setup steps with no NUN3 counterpart, such as
allocating the `0x24`-byte object stored at fighter `+0xB30`.

### Action records

**Observation:** Both games use `0x54`-byte action records. Aligning Classic
Naruto's and Classic Sakura's records on words `+0x0C..+0x18`, NA2 has one
extra record inserted at index 20 in both characters; records before it match
on those words, and many later ones differ. Other words differ even in matching
records, for example `+0x2C` `0x0001041A` against `0x0001041D`. Word `+0x00`
is a debug name
such as `PL01_ATK_CHA1` in NUN3 and an empty string in NA2; `+0x08` is the
display name (English in NUN3 `SLUS`, Japanese with ruby markup in NA2).
Word `+0x0C` packs the jutsu selector in its high halfword and the owning
character ID in its low halfword; for example NA2 Sai's record 3 holds
`0x00B9005C` and Sasuke's holds `0x00BB005D`. Word `+0x20` is the chakra cost
covered in [Chakra and guard](../gameplay/chakra_and_guard.md). Apart from the
three string pointers, the compared records contain no pointers.

**Observation:** Records 0..3 follow the order `CHB0`, `CHA0`, `CHB1`, `CHA1`
in NUN3's debug names, and records 1 and 3 carry the two jutsu display names
in both games. For example, `0x00594DFC` is Sai's (ID 92) record 3 `+0x20`,
in the record named `忍法・超獣偽画　狛犬`, and `0x0059AE8C` is Sasuke's (ID 93)
record 3 `+0x20`, in the record named `千鳥`; both chakra costs are `2.625`.

### Animation-name and `0x4C`-stride tables

**Observation:** The animation-name arrays of IDs 1, 2, 7, and 34 are identical
in the two games, and ID 47 differs in two names. Every compared array begins
with shared `ANM_pcmn*` names before character-specific `ANM_p???*` names,
except NUN3 Kisame (ID 24) and Anbu (ID 30), whose arrays use their own code
in those leading positions, for example `ANM_pksmjmp2` for `ANM_pcmnjmp2`.

**Observation:** The `0x4C`-stride rows contain skeleton object names such as
`OBJ_2cmn00t0 l foot`. Their field-level meaning was not decoded.

## Per-character code

**Observation:** Each populated definition row's factory is a small resident
function that allocates a concrete fighter and calls its constructor. The
constructor calls the common base constructor, installs a class vtable at
fighter `+0x50`, patches three record fields with pointers into the fighter,
calls the common record loader, and runs a character-specific initializer.
NUN3 and NA2 constructors have the same shape:

| Step | NUN3 Classic Naruto | NA2 Classic Naruto |
| --- | --- | --- |
| Factory / allocation size | `FUN_001D9D50` / `0x5630` | `FUN_00250C00` / `0x5980` |
| Common base constructor | `FUN_001A5650` | `FUN_002145D0` |
| Record fields patched | `+0x4C`, `+0x30`, `+0x40` ← fighter `+0xE00`, `+0x1070`, `+0x1FDC` | Same fields ← fighter `+0xEE0`, `+0x1150`, `+0x2110` |
| Record loader | `FUN_001A6190` | `FUN_002151E0` |

**Observation:** The record `+0x1C` table holds up to seven function pointers.
Resident `FUN_00217670` calls entries 0..2 and 4..6 for events 1..3 and 5..7.
Classic Naruto's table holds functions only in entries 1..4 in both games
(NUN3 `0x001DC0B0..0x001DCFE0`, NA2 `0x00252C20..0x002539E0`). NUN3's per-
character factories span `0x001D9D50..0x0022F590` in its boot ELF; NA2's span
`0x00250C00..0x00300090`. Neither game places these entry points in a battle
overlay.

**Observation:** NUN3 Kakashi's (ID 8) event-3 callback `0x001E4260` reads the
fighter halfword `+0x184`, calls NUN3 resident helpers such as
`FUN_001A89F0`, `FUN_001A3200`, `FUN_0019C380`, and `FUN_00263F40`, and reads
fighter `+0xAD4`. These are NUN3 addresses and NUN3 field offsets.

**Inference (high confidence):** NUN3 per-character code is compiled against
NUN3's fighter layout and NUN3's resident function addresses, both of which
differ from NA2's. It cannot run in NA2 as copied bytes.

## Jutsu-resource filename table

The BTL overlay holds a flat pointer table of `2???cha?.ccs` names at live
`0x008A7AA0`; NUN3 `BATTLE.BIN` holds one at live `0x00923DA0`.

**Observation:** The first 116 entries of the two tables are identical, name
for name, including every NUN3-only code's `cha0`/`cha1` pair. NA2 appends its
own entries after them, ending with `2bdycha0..4`. The table is not in
character-ID order. Of the 116 retained names, 33 have no file on the NA2 disc,
including all NUN3-only characters' files except `2kbtcha0`; eight retained
names, such as `2forcha0` and `2dtucha0`, have no file on the NUN3 disc either.
How the table is indexed was not traced.

## Voice archive

**Observation:** NA2's `DATA/PLVOICE.AFS` has 93 outer entries. Reading entry
`n` as character ID `n + 1`, the null entries are exactly IDs 8, 9, 20, 21,
23..33, 39, 44, 45, 51, 74, and 88. NUN3's 112 entries form two 56-entry banks
with the same null pattern in each bank; read the same way, they are null at
IDs 26, 29, 31, 33, 39, and 51. NA2's populated sub-archives hold about 40
members for most base characters and fewer for forms; each NUN3 sub-archive
declares 209 members.

**Inference (high confidence):** The outer index is character ID minus one in
both games. The null sets match the definition-table rows without a dedicated
fighter, except IDs 39 and 51, which have fighters but no voice sub-archive in
either game. The member numbering used by battle code was not traced.

## Selection and loading consumers

### `FUN_001E1530` — publish six match asset selections

`FUN_001E1530(uint fighter_1, uint fighter_2)` clears bit `0x100` from both
arguments, multiplies each result by four, and indexes the `2BOD1`, `1BOD1`,
and `3EYE` pointer tables. It writes the resulting six filename pointers to
runtime `0x006B26F0..0x006B2704` as three family pairs.

The function then visits all three families for both fighters. For each selected
basename it:

1. calls `FUN_001AA450` (`ccs_find_container`), storing the returned container
   pointer at runtime `0x006B26D0..0x006B26E4`; and
2. packs filename bytes 1, 2, and 3 into a 24-bit character code stored at
   runtime `0x006B2710..0x006B2724`.

**Observation:** There is no null check between table lookup and reading the
selected filename. Callers must therefore supply an index populated in all
three tables after the `0x100` flag is removed. The container lookup itself may
return null; that result is retained in the six-pointer publication block.

### `FUN_001E80F0` — per-fighter conditional load/queue path

For player slots 1 and 2, `FUN_001E80F0` reads the fighter character ID from a
`0x28`-byte selection record and conditionally builds resource paths according
to a bit mask. Mask bit `0x01` selects `DAT_00402710` (`1BOD1`), bit `0x02`
selects `DAT_004020F0` (`2BOD1`), and bit `0x10` selects
`DAT_00403350` (`3PCT`). Each constructed path is checked through
`FUN_001AA450`; the function then either calls blocking
`FUN_00116DE0` (`ccs_load_if_absent`) or queues it through `FUN_001CF9E0`
(`ccs_enqueue_unique_load`), depending on its queue-mode argument and current
residency.

The function stores newly returned load/container handles in per-player fields
separate from the path buffers. Other mask bits construct support and shared
resource paths through different helpers rather than through these four static
character tables.
