# Character asset tables

This document records how retail NA2 (`SLPS-25837`) names, stores, and loads
the files and static data that make up a playable fighter, and how that
storage differs from NUN3 (`SLUS-21727`). It does not own the general CCS
runtime, the disc-wide file inventory, or battle behavior driven by the
fighter data.

## Research coverage

- **Assigned scope:** Character-indexed CCS filename tables, the disc
  placement and contents of fighter CCS files, the static character record and
  its asset-bearing sub-tables, per-character code entry points, the
  jutsu-resource filename table, and the per-character voice archive layout, in
  NA2 and in the NUN3 lineage it extends.
- **Exploration depth:**
  - Filename tables: all 94 NA2 and 57 NUN3 rows, NA2's 188 jutsu selector
    mappings and 197 resource names, NUN3's 114 selector mappings and 116
    resource names, and the 188 resident animation-provider names.
  - Records: layouts, loaders and constructors in both boot ELFs; the first
    four action records and the callback tables of all 78 distinct NA2
    records; model, material, palette and texture lookups from common fighter
    setup; eight records in four base/form pairs; Chiyo's and Hiruko's
    complete auxiliary animation arrays.
  - CCS files: headers, section types and cross-container references for
    representative body, low-detail body and jutsu files, including every
    NUN3-only body file; all 184 NA2 skill-stream request rows.
  - Voice: the complete NA2 and NUN3 `PLVOICE.AFS` headers, member tables and
    name directories; all 93 voice descriptors; the 94-slot voice-number
    list table, compared with every archive directory.
  - A bounded instruction search for consumers of the copied effect-name
    field in the resident ELF, BTL and ETC.
- **Confirmed coverage:** The four NA2 filename families and their complete
  ID-to-code mapping; the homologous NUN3 tables; disc placement; the
  dependency of every `3EYE` file on its `1???BOD1` model; the shared
  record layout and loader offsets; the action-record and animation-table
  lineage; the per-character factory and callback shape; the shared
  skeleton-container dependency and its NA2/NUN3 difference; the retained NUN3
  prefix of NA2's jutsu-resource table; the model/material/palette/texture
  name consumers and selector arithmetic; the jutsu-selector-to-resource map,
  including the auxiliary record mappings; the ID-indexed voice archive's
  dense NA2 versus sparse NUN3 member layout; the 13 skill-stream rows that
  explicitly request `1???BOD1`; cinematic model replacement; the complete
  callback-table population and jutsu-owner selection; the physical voice
  member bounds and static filename-number lists; reserved jutsu animation
  binding; the animation index, duration, and start-frame row fields;
  Chiyo/Hiruko auxiliary-model animation selection; and NUN3's two jutsu
  index domains and the seven mappings changed in NA2's retained prefix.
  The common fighter instance teardown is separate from manager-owned CCS
  release; the inspected form pairs select different body providers.
- **Unresolved or untested:** The consumer of the record's effect name slot,
  the meaning of most action-record and `0x4C`-stride row fields, and
  character-specific asset setup beyond the paths traced here remain open.
  Whether compact battle voice controls reach physical voice members, as the
  explicit BTL voice-number producers do, is not established. The
  effect-name search does not exclude consumers through differently formed
  aliases or unsearched instruction forms.
- **Deliberate exclusions and overlap:** General CCS parsing, lookup,
  cross-container resolution, and lifetime belong to
  [Resident CCS runtime](files/ccs_runtime.md); CCS tag identities belong to
  [CCS object types](files/ccs_object_types.md); the disc inventory belongs to
  [Disc and archive file inventory](files/disc_files.md). Character-ID
  semantics and the definition-table rows belong to
  [Character identity in battle](../gameplay/characters/character_ids.md). Fighter
  construction and dispatch belong to
  [Battle entities](../gameplay/session/battle_entities.md); record fields with battle
  consumers belong to [Damage](../gameplay/combat/damage.md), and action-record
  selection to [Action commands](../gameplay/combat/action_commands.md). Character
  callback timing and repeated-hit response state belong to
  [Substitution](../gameplay/characters/substitution.md). Selected file dependency sets
  and the nine per-side request, adoption and release slots belong to
  [Asset dependency graphs](files/asset_dependencies.md#all-nine-per-side-selection-slots);
  the 3EYE presentation controller and its appearance overrides belong to
  [End-demo presentation](../gameplay/modes/end_demo_presentation.md); voice
  requests and event selection belong to
  [Battle audio](../gameplay/session/battle_audio.md). Model
  materialization and skeleton binding belong to
  [Model and skeleton runtime](../runtime/rendering/model_runtime.md); generic playback,
  texture/material binding and render submission belong to their respective
  [animation](../runtime/animation_runtime.md),
  [texture/material](../runtime/rendering/texture_material_runtime.md) and
  [render](../runtime/rendering/render_submission.md) owners. Form selection
  and whole-fighter reconstruction belong to
  [Awakening](../gameplay/characters/awakening.md#static-reconstruction-order).
- **Evidence limitations:** All findings are static reads of clean files and
  the maintained read-only analyses. No live-memory trace establishes load
  timing, residency, or how the game behaves with a missing or foreign asset.
  NUN3 findings say nothing about NUN3 runtime behavior. Working identities
  below are descriptive, not recovered original symbols. NA2's IOP-side
  `SNDBASE.IRX` voice-command handling was not inspected.

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
the [character-definition table](../gameplay/characters/character_ids.md#character-definition-table):

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
use. The [end-demo presentation lookup](../gameplay/modes/end_demo_presentation.md#request-and-lookup)
directly selects those animations and the 1BOD1 body/face resources together.
Explicit skill-stream dependencies and the cinematic replacement path below
also establish use of the family during jutsu presentation.

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

### Explicit jutsu-stream body dependencies

**Clean-file observation:** The `SINF` request data in `STRMCMN.CCS` has 184
skill rows. The [request-table source](files/ccs_runtime.md#request-table-source)
owns the blob framing, relocation, and stream transport. Reading every row's
extra resident paths yields exactly these 13 rows with a `pl/1???bod1.ccs`
dependency:

| Skill row | Extra resident body files |
| --- | --- |
| `0x06` | `1ssvbod1.ccs` |
| `0x08` | `1rocbod1.ccs` |
| `0x0B` | `1gavbod1.ccs` |
| `0x1E`, `0x1F` | `1tovbod1.ccs` |
| `0x20` | `1tovbod1.ccs`, `1tyobod1.ccs` |
| `0x34` | `1jrvbod1.ccs` |
| `0x35` | `1jrbbod1.ccs` |
| `0x3C`, `0x3D` | `1uknbod1.ccs` |
| `0x40` | `1kmvbod1.ccs` |
| `0x4A` | `2nrwbod1.ccs`, `1nwvbod1.ccs` |
| `0x4D` | `1nrwbod1.ccs` |

These skill-row IDs are a separate domain from the two-per-character jutsu
selectors below. `FUN_0035CF00` selects the skill row and installs
`FUN_0035A070` as the stream player's `+0x88` callback; `FUN_0035CC20`
turns its extra paths into requests. Thus `1uknbod1` has a data-driven
selection path even though its basename is absent from executable strings.
This census covers explicit extra requests, not every model reference
embedded in a cinematic CCS.

**Observation:** `FUN_0035A070` calls `FUN_003544F0(..., flags=2, ...)`, whose
constructor enters `FUN_00354640`. With flag bit 0 clear, that function
selects `1cmnbod1.ccs`, `CMP_1cmn00t0 trall`, and `OBJ_1cmn00t0 body`; with
bit 0 set it selects the corresponding `2cmn` names. It looks for each
replacement resource first in the selected character's `1BOD1` container,
then in `2BOD1`. A row whose subtype `((row_word0 >> 2) & 0xF)` is 3 calls
`FUN_00355C70`, which materializes the selected shared composition, creates
the resolved character model, and attaches it to that shared body object.
This is a direct model-selection/attachment consumer, beyond the file-level
skeleton references.

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
[Character identity](../gameplay/characters/character_ids.md#character-definition-table))
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
| `+0x58..+0xD8` | Physical and balance parameters; confirmed consumers are in [Damage](../gameplay/combat/damage.md#confirmed-character-record-fields) |
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

### Model and appearance name consumers

**Observation:** NA2 resident `FUN_00215950` uses record `+0x08` (copied to
fighter `+0x94`) to require the fighter's body container at fighter `+0xE64`.
It separately requires the shared `2cmnbod1` container named at
`0x00407498` and stores it at `+0xE60`. The shared composition
`CMP_2cmn00t0 trall`, named at
`0x00407D10`, becomes the scene object at `+0xE6C`. Record `+0x14` (fighter
`+0xA0`) supplies the model name at a `0x1E`-byte stride; fighter byte `+0x60`
bit 4 selects slot 0 or 1. An empty slot 1 clears bit 4 and retries slot 0.
The model lookup is in the fighter container, and its materialized object is
stored at `+0xE68` and attached to `OBJ_2cmn00t0 body` in the shared scene.

**Observation:** Three cached lookups use that same fighter container. A
zero cache or force argument `1` causes a new lookup through `FUN_001A8F00`:

| Function | Name source and slot | Fighter cache |
| --- | --- | ---: |
| `FUN_00216110` | Fixed `MAT_clut` / `MAT_clut01` names at `0x00407D28 + bit4 * 0x1E` | `+0xE78` |
| `FUN_00216190` | Record `+0x0C` / fighter `+0x98`, slot `colour + 3 * bit3 + 6 * bit4` | `+0xE7C` |
| `FUN_00216250` | Record `+0x10` / fighter `+0x9C`, slot `bit3 + 2 * bit4` | `+0xE80` |

Here `bit3` and `bit4` are the corresponding bits of fighter byte `+0x60`,
and `colour = (byte >> 1) & 3`. The material selector's unsigned extraction
is confirmed by instructions `0x0021613C..0x0021616C`; its decompiler renders
the shift as signed and would misleadingly suggest a negative slot.
The palette and texture helpers return zero for an empty name. They do not
check an upper slot bound. The observed Classic Naruto palette array at
`0x00408118` has 12 slots, with `body/bodyc1/bodyc2` followed by
`bod2/bod2c1/bod2c2` and six empty slots. Its texture array at `0x00408280`
has two names, `TEX_2nrtbody` and `TEX_2nrtbod2`; the model array at
`0x004082C0` has a populated first slot and an empty second slot. The selector
formulas alone do not prove that every encoded flag combination is used.

**Observation:** Initial model setup calls `FUN_00198A60(model, palette,
material)` when both lookups succeed. `FUN_00216010` handles a set bit 3 by
clearing it, forcing the material/texture/palette lookups, and applying the
texture and palette to the shared scene through `FUN_00194790` and
`FUN_00194600`. This establishes consumers of all three name arrays; the
player-facing meaning and writers of the appearance flag combinations are
not assigned by this asset trace.

A separate nine-row BTL lookup resolves additional hair, mask, accessory, and
glasses models from selected body containers. Its complete table and cache
setup are recorded under [Setup helpers after fighter publication](../gameplay/session/battle_lifecycle.md#setup-helpers-after-fighter-publication).

### Form records and instance ownership

**Observation:** The following four native base/form pairs were read at their
record heads and complete palette, texture and model-name arrays.
Each side of each pair supplies its own body filename and slot-0 model name:

| Character IDs | Record addresses, base / form | Body basenames, base / form | Slot-0 models, base / form |
| --- | --- | --- | --- |
| `1 -> 47` | `0x0040DB70` / `0x004A68A0` | `2nrtbod1.ccs` / `2nrvbod1.ccs` | `MDL_2nrt00t0 body` / `MDL_2nrv00t0 body` |
| `57 -> 73` | `0x004DAD80` / `0x00535D50` | `2nrwbod1.ccs` / `2nwvbod1.ccs` | `MDL_2nrw00t0 body` / `MDL_2nwv00t0 body` |
| `36 -> 54` | `0x00476B70` / `0x004CA870` | `2tyybod1.ccs` / `2tyvbod1.ccs` | `MDL_2tyy00t0 body` / `MDL_2tyv00t0 body` |
| `63 -> 75` | `0x004FC230` / `0x0053B630` | `2scobod1.ccs` / `2scvbod1.ccs` | `MDL_2sco00t0 body` / `MDL_2scv00t0 body` |

Only ID 57 has a nonempty slot-1 model among these eight records:
`MDL_2nrw01t0 body`. IDs 1 and 57 have six nonempty palette slots; the
other six records have three. All palette names use their selected body's
code. IDs 1, 47, 57 and 73 have two texture names; IDs 36, 54, 63 and 75
have only slot 0 populated. These are stored-name observations, not a claim
that every appearance-selector combination is reachable. In particular,
ID 57's second model is a slot in its existing body container, whereas the
`57 -> 73` identity change selects the separate `2nwvbod1` provider.
The pairing and replacement gates belong to
[Awakening](../gameplay/characters/awakening.md#static-reconstruction-order).

**Observation:** Common setup `FUN_00215950` obtains existing CCS containers
through required lookup; it does not issue a file request. It creates the
shared composition, animation controller and selected model as fighter-owned
instances. `FUN_00215E70` destroys those instances and the fourth optional
handle, nulling `+0xE70`, `+0xE6C`, `+0xE68` and `+0xE74` in that order.
Its complete body contains no container-destruction call and does not clear
the borrowed provider pointers at `+0xE60/+0xE64` or the appearance caches at
`+0xE78..+0xE80`. The established caller `FUN_00215720` is the common
fighter teardown. Full concrete lifetime dispatch is owned by
[Common fighter-owned children](../gameplay/session/battle_entities.md#common-fighter-owned-children),
and instance construction/binding by
[Model and skeleton runtime](../runtime/rendering/model_runtime.md).
Manager handle release below therefore concerns a different allocation layer
from the fighter's model and animation instances.

**Unresolved, bounded search:** Record effect-name pointer `+0x18` is copied
to fighter `+0xA4` by `FUN_002151E0`, but no consumer of that copied name is
established. All `lw` and `addiu` instructions with immediate `+0xA4` in the
resident ELF, BTL and ETC were checked:

- The 17 aligned resident `lw` sites in fighter code `0x002145D0..0x00300090`
  load stack words or animation-array slot `0x29`, including Chiyo/Hiruko's
  fallback bindings.
- The 39 BTL and 8 ETC `lw` sites load stack data, vtable entries,
  presentation/controller fields, camera resources, action-instance state,
  counters or animation-array slot `0x29`. For example, preserved
  `0x0078B2E0..0x0078B304`, `0x007BAE30..0x007BAE48` and
  `0x0080154C..0x00801570` first load fighter `+0xB84`, then array `+0xA4`,
  and pass that animation to `FUN_001B99B0`: the same numeric offset on a
  different allocation.
- The `addiu` matches are literals or stack addresses, except one ETC
  embedded presentation object passed to its destructor at preserved
  `0x006D1488`; the sole resident fighter-code match is literal
  `a0 = 0xA4` at `0x002C8304`.

The representative `OBJ_eff_dummy_nrthol0` pointer at `0x00408300` has only
the record-field data reference `0x0040DB88` and its two mapped ELF aliases.
None of these sites reads the fighter's copied name. Direct static-record
access, other load opcodes and aliases formed by another offset or arithmetic
sequence remain open; this is not evidence that the field is unused.

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
covered in [Chakra and guard](../gameplay/combat/chakra_and_guard.md). Apart from the
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

**Observation:** Initial `FUN_00215950` looks up the animation-name array in
the shared `2cmnbod1` container for names whose three bytes at name `+0x05`
are `cmn`, otherwise in the fighter's body container. Empty names and indices
`0x46..0x4D` are left as zero in the lookup array at fighter `+0xB84`.
Those eight indices are populated later by `FUN_00219620` from the configured
jutsu owner's record `+0x48` animation-name array:

| Source action slot | Source animation-name indices |
| ---: | --- |
| 0 | `0x46..0x48` |
| 1 | `0x49` |
| 2 | `0x4A..0x4C` |
| 3 | `0x4D` |

The configured selector's parity can swap source action pairs. The loader
then copies each source range into its destination pair's corresponding
lookup slots. It obtains the jutsu container basename through
`FUN_00307C60(selector)`, strips the extension, and requires that container
alongside `2cmnbod1`. Names containing `cmn` at the same three-byte position
resolve in the shared container; other names resolve in the selected jutsu
container. Thus record animation names select objects, while the configured
selector separately selects their provider.

**Observation:** `FUN_00218FE0` copies all record `+0x3C` rows from fighter
`+0xC8` into its writable row array at `+0xCC`. Configured jutsu selection
can replace destination rows 0..5 or 6..11 with the selected owner's first or
second six-row group. Copying the second source group into the first remaps
animation indices `0x4A..0x4D` to `0x46..0x49`; copying the first into the
second performs the reverse remap. The conversion writes `-1` for values
outside the expected four animation indices. The associated action-pointer
conversion is owned by [Action-table source and setup](../gameplay/combat/action_commands.md#working-action-arrays).

**Observation:** Resident `FUN_002189D0` establishes the first three signed
halfword fields of a `0x4C` row:

| Offset | Confirmed consumer |
| ---: | --- |
| `+0x00` | Animation lookup-array index; `-1` ends the row sequence. |
| `+0x02` | Explicit duration. A value below 1 derives duration from the selected animation's `+0x0C` frame count, minus one and the row's start frame. |
| `+0x04` | Animation start frame used in that duration calculation. |

The rows also contain skeleton object names: Classic Naruto's first row at
`0x00409110` has pointer `+0x28` to `OBJ_2cmn00t0 l foot`. The consumer of
that name and the meaning of most remaining fields are unassigned.

### Auxiliary-model animation providers

**Observation:** Chiyo's ID-62 record at `0x004F6BB0` is selected through
the descriptor at `0x004F6C90` by constructor `FUN_002A8E40`. Its
`FUN_002A9150` setup builds two auxiliary animation lookup arrays with 139
slots each, backed by fighter `+0x5720` and `+0x59B4`. The source table at
`0x005C3810` interleaves two name pointers per slot; all 278 pointers were
read. Its names use `ANM_poya*`, `ANM_pfat*`, and `ANM_pmot*`. Outside
indices `0x46..0x4D`, a nonempty name resolves in the fighter body container
at `+0xE64`.

For a reserved slot whose main-fighter lookup is populated, the helper
copies that animation object's name and rewrites bytes `+0x05..+0x07` to
`fat` for auxiliary array 0 or `mot` for array 1. Slots `0x46..0x48` use
jutsu selector `+0x184`; slots `0x4A..0x4C` use `+0x186`. The corresponding
container comes from `FUN_00307C60`. An optional named lookup through
`FUN_001A8F00(..., 1)` supplies the auxiliary animation; a missing result
uses auxiliary slot `0x29`. Reserved slots `0x49` and `0x4D` also take that
slot directly. The slot-`0x29` names are `ANM_pfatnut0` and
`ANM_pmotnut0`. If the main animation is absent, the auxiliary reserved
slot remains zero. The byte substitutions are explicit at
`0x002A92C0..0x002A9304`.

The same helper resolves `CMP_2kgt00t0 trall` at `0x004F6D20` from the
fighter body container and creates one auxiliary scene per array. It
resolves `MAT_2kgtbody` at `0x004F0EB0` and the two palette names beginning
at `0x004F0E48`, `CLT_2kgtbody` and `CLT_2kgtbodyc1`, for those scenes.
These auxiliary resources are additional consumers of the body archive,
separate from the common fighter model setup.

**Observation:** Hiruko's ID-63 record at `0x004FC230` is selected through
descriptor `0x004FC310` by constructor `FUN_002AEA00`. It gives
`FUN_002AEC80` a 120-entry `ANM_pkkg*` name array at `0x004F78B0`, with its
lookup array at fighter `+0x4EF8` and pointer at `+0x50E0`. All 120 source
pointers were read. Nonreserved names resolve in the fighter body container.
For populated main-fighter reserved slots, the helper rewrites the same
three name bytes to `kkg` (`0x002AED98..0x002AEDAC`). It takes selector
`+0x184` for indices `0x46..0x49` and `+0x186` for `0x4A..0x4D`, resolves
their jutsu container, and uses the same optional-lookup/slot-`0x29` rule.
Here slot `0x29` is `ANM_pkkgnut0`; `0x49` and `0x4D` take it directly.

Hiruko's auxiliary scene uses body-container composition
`CMP_2kkg00t0 trall` at `0x004FC380`. The helper also resolves six separate
body animations from `0x004F70D0`: `ANM_2kkgstt10`, `ANM_2kkgstt00`,
`ANM_2kkgstt40`, `ANM_2kkgstt50`, `ANM_2kkgstt60`, and
`ANM_2kkgskm00`. If either configured selector is `0x7E` and
`2scocha0.ccs` is already found, it additionally resolves
`ANM_2kkgchb00` into fighter `+0x5110`. The helper's explicit filename at
`0x004FC398` agrees with selector 126 in the resident table below.
This traces auxiliary asset binding, not the downstream battle behavior
of the auxiliary scene or its animations.

## Per-character code

**Observation:** Each dedicated fighter's definition row selects a small resident
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

**Observation:** Reading all 78 distinct NA2 records' seven-pointer tables
gives the following complete population. All nonzero pointers are resident,
between `0x00252C20` and `0x00303710`.

| Table slot | Tables with a nonzero pointer |
| ---: | ---: |
| 0 | 25 |
| 1 | 74 |
| 2 | 78 |
| 3 | 74 |
| 4 | 44 |
| 5 | 13 |
| 6 | 13 |

The four auxiliary records (IDs 26, 29, 30, and 31) have only slot 2
populated, with `0x003036D0`, `0x003036F0`, `0x00303700`, and
`0x00303710`, respectively. Every dedicated fighter has slots 1, 2, and 3
populated. Slot 3's existence does not make it an event-4 target in
`FUN_00217670`, which has no event-4 case.

**Observation:** Callback-table selection can follow the configured jutsu
owner. When fighter major state `+0x18E` is 8 and action index `+0xA3C` is
0..3, `FUN_00217670` takes selector `+0x184` for actions 0/1 or `+0x186`
for actions 2/3. `FUN_00307EB0` derives its owner ID; a positive owner selects
that definition's record `+0x1C` table. Otherwise the dispatcher takes the
copied table at fighter `+0xA8`. The intervening `FUN_00307A50` returns zero
in the retail executable, so the fallback uses this fighter's table.
The callback receives the original fighter pointer even when its table comes
from another jutsu owner.
Callback bodies and their battle effects belong to the gameplay documents.

**Observation:** NUN3 Kakashi's (ID 8) event-3 callback `0x001E4260` reads the
fighter halfword `+0x184`, calls NUN3 resident helpers such as
`FUN_001A89F0`, `FUN_001A3200`, `FUN_0019C380`, and `FUN_00263F40`, and reads
fighter `+0xAD4`. These are NUN3 addresses and NUN3 field offsets.

**Inference (high confidence):** NUN3 per-character code is compiled against
NUN3's fighter layout and NUN3's resident function addresses, both of which
differ from NA2's.

## Jutsu-resource filename table

The BTL overlay holds a flat pointer table of `2???cha?.ccs` names at live
`0x008A7AA0`; NUN3 `BATTLE.BIN` holds one at live `0x00923DA0`.

**Observation:** The first 116 entries of the two tables are identical, name
for name, including every NUN3-only code's `cha0`/`cha1` pair. NA2 appends its
own entries after them, ending with `2bdycha0..4`. The table is not in
character-ID order. Of the 116 retained names, 33 have no file on the NA2 disc,
including all NUN3-only characters' files except `2kbtcha0`; eight retained
names, such as `2forcha0` and `2dtucha0`, have no file on the NUN3 disc either.

### Selector-to-resource mapping

**Observation:** NA2 has two index domains. The 188 signed words at BTL live
`0x008CB160..0x008CB44F` translate a jutsu selector `0..187` into a resource
index. The 197 filename pointers at live `0x008A7AA0..0x008A7DB3` then
translate that resource index into a CCS basename. The preserved byte
ranges are respectively `0x008CB120..0x008CB40F` and
`0x008A7A60..0x008A7D73`; encoded pointers already contain live addresses.
Consequently Ghidra's pointer-table label `PTR_s_2skrcha0_ccs_008a7aa0`
misidentifies the first runtime entry: resource 0 actually names
`2nrtcha0.ccs`, not Sakura's file.

**Observation:** Across all 78 distinct records selected by the 94-row
definition table, action record 1 stores selector `2 * record_ID` and action
record 3 stores `2 * record_ID + 1` in the high halfword of `+0x0C`.
Their low halfwords equal that record's ID. This includes the four auxiliary
records, so the general selector relationship does not imply a playable
fighter or a same-code CCS. The translation map starts with two `-1` entries
(selectors 0 and 1). Important non-fighter mappings are:

| Record ID | Selector | Resource index | Filename |
| ---: | ---: | ---: | --- |
| 26 | 52 / 53 | 154 / 115 | `2kkvcha1.ccs` / `2nrocha1.ccs` |
| 29 | 58 / 59 | 192 / 193 | `2bdycha0.ccs` / `2bdycha1.ccs` |
| 30 | 60 / 61 | 194 / 195 | `2bdycha2.ccs` / `2bdycha3.ccs` |
| 31 | 62 / 63 | 196 / 45 | `2bdycha4.ccs` / `2kbtcha0.ccs` |

For comparison, selectors 184/185 for ID 92 map to resources 188/189
(`2saicha0/1.ccs`), while selectors 186/187 for ID 93 map to resources
190/191 (`2sswcha0/1.ccs`). ID 12's selectors 24/25 map to resources 19/18,
respectively: the filename pool places `2hntcha1` before `2hntcha0`.

**Observation:** The setup fragment preserved as `FUN_0077E1A0` (live
`0x0077E1E0`) reads four selectors from manager `+0x58/+0x5C/+0x80/+0x84`.
Instructions preserved at `0x0077E214..0x0077E238` check the selector against
188 and read the translation word; `0x0077E334..0x0077E344` indexes the
filename table with the translated value. The setup cache at live
`0x008DAAA0` is cleared over `0x314` bytes, exactly 197 pointers. Another
consumer, the fragment at preserved `0x0077DE10` (live `0x0077DE50`), reads
fighter selector `+0x186`, translates it, and accepts resource indices below
`0xC5` (197) before indexing per-resource data. The helper family at
preserved `0x006F26C0` reads both fighter `+0x184` and `+0x186` through the
same translation map.

These reads establish asset selection, not the battle behavior of the
auxiliary records. Their behavior is owned by the gameplay documents.

### NUN3 selector comparison

**Observation:** NUN3 has the same two index domains. Its 114 signed
translation words are at BATTLE live `0x0093E800..0x0093E9C7` (preserved
`0x0093E7C0..0x0093E987`), and its 116 filename pointers are at live
`0x00923DA0..0x00923F6F` (preserved `0x00923D60..0x00923F2F`). The next
pointer begins the material-name table with `MAT_cmneye1`, bounding this
filename family. All 116 filenames agree with NA2's first 116 resources.
Comparing all 114 translation words gives 107 identical mappings and these
seven differences:

| Selector | NUN3 resource / filename | NA2 resource / filename |
| ---: | --- | --- |
| 52 | 114 / `2nrocha0.ccs` | 154 / `2kkvcha1.ccs` |
| 58 / 59 | 55 / 56, `2forcha0/1.ccs` | 192 / 193, `2bdycha0/1.ccs` |
| 60 / 61 | 53 / 54, `2anbcha0/1.ccs` | 194 / 195, `2bdycha2/3.ccs` |
| 62 / 63 | 65 / 66, `2nrvcha0/1.ccs` | 196 / 45, `2bdycha4.ccs` / `2kbtcha0.ccs` |

**Observation:** The translation helper at preserved
`0x0086E680..0x0086E6BC` (live entry `0x0086E6C0`) accepts selectors below
114 and loads their signed resource word; negative selectors and selectors
at or above 114 return zero. Valid selectors 0 and 1 instead read the table's
`-1` entries. The consumer preserved as `FUN_00875480` (live
`0x008754C0`) reads NUN3 fighter selectors `+0x178` and `+0x17A` through
this helper, and indexes two resource caches of `0x1D0` bytes each, exactly
116 pointers. This distinguishes selector bounds from resource capacity.

The filename getter at preserved `0x0086C090..0x0086C0A8` (live entry
`0x0086C0D0`) directly loads `table[index]` after shifting its argument left
by two, without an internal bounds check. The request wrapper preserved as
`FUN_0086B910` (live `0x0086B950`) passes its resource argument to that
getter and forwards the filename to resident `0x00160870`. This establishes
a direct asset-request consumer in addition to the selector-dependent cache
setup; it does not make a raw character ID interchangeable with either
index domain.

### Resident animation-provider filenames

**Observation:** The resident executable has a separate 188-entry,
eight-byte-stride selector table at `0x005A2320..0x005A28FF`.
`FUN_00307C60(selector)` directly returns its second word, at
`0x005A2324 + selector * 8`; it does not use the BTL translation map.
Selectors 0 and 1 both name `2cmnbod1.ccs`. All other selectors have a CCS
filename, including selector 126, whose `2scocha0.ccs` string is stored at
`0x004FC398` rather than in the adjacent pool.

**Observation:** Comparing all remaining 186 resident names with the BTL
selector map gives 170 identical names and 16 differences. For IDs 8, 20,
23, 24, 32, 33, 74, and 88, the resident pair names `2nrtcha0/1.ccs` while
the BTL map names the corresponding retained character-code pair. These IDs
have no dedicated NA2 fighter definition. The two tables therefore describe
different lookup paths and cannot be substituted for each other merely
because they share selector arithmetic.

## Voice archive

**Observation:** NA2's `DATA/PLVOICE.AFS` has 93 outer entries. Reading entry
`n` as character ID `n + 1`, the null entries are exactly IDs 8, 9, 20, 21,
23..33, 39, 44, 45, 51, 74, and 88. NUN3's 112 entries form two 56-entry banks
with the same null pattern in each bank; read the same way, they are null at
IDs 26, 29, 31, 33, 39, and 51.

**Inference (high confidence):** The outer index is character ID minus one in
both games. The null sets match the definition-table rows without a dedicated
fighter, except IDs 39 and 51, which have fighters but no voice sub-archive in
either game. In NA2, every populated member's directory filename begins with
`PL` followed by its outer-entry character ID, strengthening that indexing
interpretation independently of the null pattern.

### Nested member layout

**Clean-file observation:** NA2 `DATA/PLVOICE.AFS` is 22,192,128 bytes and
NUN3's is 34,574,336 bytes; their tables were read from the clean
extraction. At both outer and inner levels, bytes `+0x00..+0x03` are `AFS` plus NUL,
`+0x04` is the little-endian member count, and `+0x08` begins `{offset,size}`
pairs of eight bytes. Inner offsets are relative to the sub-archive start.
Immediately after the inner member table is a pair giving its filename
directory's relative offset and length. All inspected directory lengths are
`member_count * 0x30`; each entry begins with a 32-byte filename. All
nonempty member offsets are aligned to `0x800`, and every member fits within
its owning outer entry's declared size.

| Game | Populated sub-archives | Declared slots per sub-archive | Populated clips | Inner layout |
| --- | ---: | --- | ---: | --- |
| NA2 | 72 | `1..48`; commonly `39..44` for base fighters | 2,232 | Every declared slot is nonempty; first clip always starts at `+0x800`. |
| NUN3 | 100, across two banks | `209..256`; 76 archives declare 209 | 2,525 | Every archive is sparse; first clip starts at `+0x800` except the two 256-slot archives, which start at `+0x1000`. |

All 4,757 nonempty clips share first 12 header bytes
`80 00 00 20 11 00 00 01 00 00 5D C0`, consistent with the AHX type-`0x11`,
mono, 24-kHz classification in [Disc and archive file inventory](files/disc_files.md).
No dialogue meaning is inferred from those headers.

**Observation:** NA2's dense physical index is different from the numeric
suffix retained in its filenames. Classic Naruto's 40-member sub-archive at
outer file offset `0x800` starts with `PL01_000.ahx`, `PL01_002.ahx`,
`PL01_003.ahx`, and `PL01_045.ahx` in physical slots 0..3. Nine-Tailed
Naruto's four members (outer index 46 / ID 47) are named
`PL47_213.ahx`, `PL47_214.ahx`, `PL47_215.ahx`, and `PL47_217.ahx`.
Thus a voice number such as 213 cannot be used directly as a physical inner
index in that NA2 archive.

**Observation:** NUN3 retains sparse numbering: its ID 1 bank-0 archive has
27 populated slots at
`0..3, 6..7, 23..24, 45, 47, 49..50, 68..69, 85, 92, 111..112, 118,
125, 151, 165..167, 199, 202, 208`. Its ID 47 archives declare 218 slots,
with only `213..217` populated; ID 56 declares 256 slots, with only
`249..255` populated. Corresponding banks have identical populated-index
sets for every ID except 40: bank 1 additionally has member 182. The two
banks' language and the battle-request-to-member translation require code
evidence beyond these archive layouts.

### Voice descriptors and filename-number lists

**Observation:** The resident table at `0x003FDFF0` has 93 eight-byte
descriptors, one for each character ID minus one. Each begins with a
halfword archive handle `150 + outer_index`; its halfword at `+0x06` is the
physical inner-member count. All 93 counts agree with the clean archive,
including every null sub-archive. The audio setup `FUN_001D6550` loads these
nested headers through `FUN_001D6C70`. `FUN_001D97D0(..., family=3)` selects
the descriptor, checks the requested physical member against its count, and
passes the descriptor handle and that member to `FUN_001D6F60` /
`FUN_001371F0`. The pending-voice consumer `FUN_001D2C20` uses this family
when a queue row's alternate-family field is zero.

**Observation:** A separate 94-slot pointer table at `0x003FF900` is indexed
directly by character ID. Its null slots match the archive's null IDs, plus
ID 0. Sixty-two pointers select signed-halfword lists in
`0x003FE4E0..0x003FF8FB`; ten select compact initialized lists in
`0x00602C58..0x00602C9F`. Every list ends with `-1`. Every value, in order,
matches the numeric suffix of the corresponding physical member's filename:
all 2,232 clips were compared without a mismatch. For ID 1 the first four values
are `0, 2, 3, 45`; for ID 47 they are `213, 214, 215, 217`.
The compact lists belong to IDs 34, 35, 36, 38, 49, 52, 53, 54, 55, and 75
and cover 21 clips; for example ID 34 holds `149, 150, 151`, while ID 75
holds `347, 348, 349`.

**Observation:** Preserved instructions at `0x001D2DE0..0x001D2E7C` search
the selected halfword list for a requested number, retaining the matching
position as the physical member or `-1` when absent. They write character
ID minus one, member position, and player slot into a `0x14`-byte queue row.
Its four BTL callers, which queue explicit voice numbers, are recorded under
[Recovered BTL PLVOICE producers](../gameplay/session/battle_audio.md#recovered-btl-plvoice-producers).
The ordinary fighter voice-event path selects compact control records rather
than AFS members or filename suffixes; it is owned by
[Fighter voice-event selection](../gameplay/session/battle_audio.md#fighter-voice-event-selection).

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

### Per-side request, adoption and release

`FUN_001E80F0` builds the per-fighter `1BOD1`, `2BOD1` and `3PCT` paths from
`DAT_00402710`, `DAT_004020F0` and `DAT_00403350` (mask bits `0x01`, `0x02`
and `0x10`), together with the jutsu-provider and support/cut-in paths. Its
nine-slot path/handle layout, deferred adoption, cache reset, masked release,
pending-side release and established callers are recorded under
[All nine per-side selection slots](files/asset_dependencies.md#all-nine-per-side-selection-slots).

The separate 3EYE request, adoption and release helpers `FUN_001E90F0`,
`FUN_001E9180` and `FUN_001E91E0`, and the end-demo controller that consumes
3EYE together with 1BOD1, are recorded in
[End-demo presentation](../gameplay/modes/end_demo_presentation.md).

### Loading-presentation portrait selection

**Observation:** `FUN_001E93C0(character_ID,deferred)` separately requests
`loading/spload.ccs` and the selected character's `3PCT` file. Its portrait
path is stored at manager `+0xD1C` and any new synchronous container return
at `+0xC90`. Those are exactly the
[nine-slot layout's](files/asset_dependencies.md#all-nine-per-side-selection-slots)
**side-2** portrait buffer and handle, rather than a newly allocated cache.
As in the ordinary request helper `FUN_001E80F0`, a published portrait goes through `FUN_00116DE0` and produces
no adopted handle from that call. Deferred mode starts the queue worker with
progress argument 1. `FUN_001E94E0` releases only the separate
`loading/spload` global handle at `0x00607648`.

Its resident caller `FUN_00202640` passes synchronous mode, then independently
looks up the portrait container before selecting `TEX_name` and creating
presentation objects. Thus the consumer can obtain a published portrait
even when the shared manager slot was not filled by the load-if-absent call.
This is a concrete consumer of 3PCT's name image; it does not establish the
full loading screen's presentation or input behavior.
