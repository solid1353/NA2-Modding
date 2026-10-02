# Ultimate Jutsu cinematics

This document records how retail NA2 (`SLPS-25837`) selects and adjusts the
authored Ultimate Jutsu cinematic for a given attacker, defender, and skill:
opponent-dependent stream selection, per-request participant setup, authored
appearance and draw-state changes, and defender-specific draw, placement, and
geometry substitutions. Starting the cinematic, the contest, and its outcome
belong to [Ultimate Jutsu](ultimate_jutsu.md).

## Research coverage

- **Assigned scope:** cinematic selection in `FUN_0035CF00`/`FUN_0035CA80`,
  request setup and draw callbacks of the skill-play player, SINF appearance
  substitutions, per-character texture and draw-state switches,
  defender-specific draw gates, position and object adjustments, and bone-model
  replacement.
- **Exploration depth:**
  - Every entry of the opponent-override table and the code-driven replacement.
  - Request setup, frame, draw, and end callbacks; every entry of the 142-row
    SINF appearance table; all four authored texture/draw-switch resources and
    their loader, apply, and cleanup families.
  - All 41 nonzero participant draw-gate pointers and seven code-driven
    replacements, all 15 position headers and 31 distinct entries, all nine
    object-adjustment headers, and the two 17-node replacement masks.
  - The stream-name identifier producer and comparison against all 383 retail
    `STR/` header names; the 17 secondary geometry links in each selected
    `gav/sch` body file and the corresponding targets in four `d71/d72`
    stream variants.
  - BTL and ETC SINF initialization callsites.
- **Confirmed coverage:** all opponent-dependent skill and path substitutions;
  side/role ordering of IDs and appearance flags; palette suffix selection;
  authored per-character texture/draw changes and bounded absence handling;
  defender-specific draw, position, matrix, and bone-model substitutions; the
  hit-popup clears at the interruption threshold; the shipped
  numeric-name/optional-body comparison mismatch; and selected secondary
  `shadow` geometry providers and target names.
- **Unresolved or untested:** the optional-body comparison's intended constant
  or resource; provider/target presence across every cinematic; the visible
  accumulated result of the per-frame matrix predicates; and the visible body
  animation within each omitted-draw range.
- **Deliberate exclusions and overlap:**
  - Presentation timeline, contest, damage, and interruption task belong to
    [Ultimate Jutsu](ultimate_jutsu.md).
  - General CCS transport, request tables, and player controls belong to
    [CCS runtime](../../game/files/ccs_runtime.md); record-type identities to
    [CCS object types](../../game/files/ccs_object_types.md).
  - Character asset tables belong to
    [Character assets](../../game/character_assets.md); curve evaluation and
    target application to [Animation runtime](../../runtime/animation_runtime.md).
  - Cinematic cue rows belong to
    [Battle audio](../session/battle_audio.md#authored-cinematic-frame-rows).
- **Evidence limitations:** conclusions come from static reads of the clean
  resident, BTL, and ETC images and in-memory decompression of the named clean
  CCS files. Stored provider geometry and target records do not prove live
  allocation success, and an absent optional row or helper return is not
  evidence of an observed cinematic failure. Direct-call scans do not exclude
  indirect callers.

## Addresses

Binary identities and address conversions follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Resident addresses are runtime addresses; BTL addresses are live addresses.

## Opponent-dependent cinematic selection

Before constructing the player, `FUN_0035CF00` calls
`FUN_0035CA80(side, attacker_id, defender_id, skill)` and uses any returned
replacement other than `-1`. The complete clean override table has three
defender groups and twelve entries. Its group headers occupy SINF
`[+0x1E84,+0x1E9C)` and its eight-byte entries
`[+0x1E9C,+0x1EFC)`, corresponding to decompressed
`STRMCMN.CCS [0x6AD18,0x6AD78)`. The loaded group pointer is resident
`0x0060772C`; `FUN_00357B10` relocates each group's contiguous entry list
and adds the SINF string base to its path pointers.

| Defender ID | Requested skill | Replacement skill | Stored path |
| ---: | ---: | ---: | --- |
| `0x59` | `0x48` | `0x49` | `pl/2nrtbod1.ccs` |
| `0x4C` | `0x04` | `0xB6` | `pl/2nrtbod1.ccs` |
| `0x4C` | `0x0C` | — | `str/d05_11.ccs` |
| `0x4C` | `0x18` | `0xB7` | `pl/2nrtbod1.ccs` |
| `0x4C` | `0x1C` | — | `str/d13_21.ccs` |
| `0x4C` | `0x22` | — | `str/d15_21.ccs` |
| `0x4C` | `0x3B` | — | `str/d36_21.ccs` |
| `0x4C` | `0x7A` | — | `str/d69_21.ccs` |
| `0x4C` | `0x48` | — | `str/d46_12.ccs` |
| `0x4C` | `0x84` | — | `str/d71_51.ccs` |
| `0x4C` | `0x88` | — | `str/d72_51.ccs` |
| `0x28` | `0xB0` | — | `str/d92_11.ccs` |

A dash is the stored replacement `-1`. Those nine rows preserve the skill
but let `FUN_0035C930` choose the opponent-specific stream path; it also
builds the main path by replacing `.ccs` with `e.ccs` in buffer
`0x006B3AE0` (suffix literals `0x006042D8/0x006042E0`).
`FUN_0035CC20` uses that derived path for the main resident request and the
stored path for the stream request. The three nonnegative replacements
instead change the skill before either lookup, so their stored paths are not
selected by a lookup on the new skill. The new skill's normal SINF row
supplies its resources. The general row and request-list structure belongs to
[CCS runtime](../../game/files/ccs_runtime.md#request-table-source).

There is one additional code-driven replacement. For attacker ID `0x51`,
requested skill `0x95` becomes `0x96` when the side's fighter has marker
`+0x63:0x20`. `FUN_0035CA80` calls `FUN_0020DD20` to clear the marker before
returning `0x96`. With that attacker and a valid fighter but without the
replacement condition, it still calls the clear helper before the table
lookup. No other attacker-specific branch exists in this function.

The uninitialized-table branch differs from an initialized lookup miss:
`FUN_0035CA80` returns `0` when the group pointer or count is zero, whereas a
completed search without a replacement returns `-1`. The constructor accepts
any replacement other than `-1`. This helper contract is not evidence that an
ordinary presentation calls it before initialization. A bounded direct-`jal`
search of the resident, BTL, and ETC programs found SINF initialization in
BTL setup at live `0x00769174` (Ghidra `0x00769134`) and ETC setup at live
`0x006BE76C` (Ghidra `0x006BE72C`), with no direct resident call. That search
does not exclude indirect calls.

## Participant fields and request callbacks

`FUN_0035CF00` receives two side descriptors separately from attacker side.
Each descriptor's low byte is that side's fighter ID; bits `16..23` supply
its appearance flags. Attacker side selects the attacker and defender IDs
before opponent replacement. The skill-play record retains both orders:

| Record field | Initial value |
| --- | --- |
| `+0x28` | attacker side |
| `+0x2A / +0x2C` | side-0 / side-1 fighter IDs |
| `+0x2E / +0x30` | side-0 / side-1 appearance flags |
| `+0x36 / +0x38` | attacker / defender fighter IDs |
| `+0x3A / +0x3C` | selected skill after replacement |
| `+0x16A` | stream-request ordinal, zero |

`FUN_0035A070` is the per-request setup callback. It stores the streamed
container at record `+0x04`, resolves the first resident request's container
at `+0x0C`, binds the defender's body/eye/mouth objects to `EXT_1cmn00t0`
entries, and finds the attacker's body through the side-formatted
`EXT_1xxx00t0 body` name. Appearance lookup uses each side's own retained
flags. Setup increments `+0x16A` after installing resources and the time limit.
Transport and callback order belong to
[CCS runtime](../../game/files/ccs_runtime.md#per-request-lifecycle-in-playdecode).

Its optional body-subobject construction has two explicit exclusions:
defender ID `0x5D`, and defender ID `0x0A` with parsed stream identifier
`0x200302`. They skip construction of record `+0x80`, while request setup
continues. The latter comparison contradicts the identifier producer for
the shipped numeric cinematic names and identifies no move name.

### Stream-name identifier and the optional-body comparison

**Observation:** The identifier is derived from the container's inline CCS
header name, not from its request path, selected skill, or defender ID.
`FUN_001AC290` reads the 32-byte name into container `+0x04`.
`FUN_0035A070` reads signed bytes at container `+0x05/+0x06/+0x08/+0x09`,
subtracts ASCII `0`, and computes
`(((name[1]-'0')*16 + name[2]-'0') << 8) |
((name[4]-'0')*16 + name[5]-'0')`.
The instruction sequence `0x0035A0B8..0x0035A0F0` explicitly shifts by
`4`, `8`, and `4`; the final word is stored at skill-play record `+0x00`.
For example, header `d14_20` produces `0x1420`. The parser does not read
the `d`, underscore, optional `e` suffix, or a third digit in either pair.

**Clean-file observation:** A bounded header read of all 383 CCS files in
the retail `STR/` directory found 382 names matching
`d[0-9][0-9]_[0-9][0-9]` with an optional final `e`, plus `attention`.
None produces `0x200302` under those instructions. This header check does
not decode every cinematic or prove every request is selected. The selected
SINF rows `0x20/0x84/0x88/0x95/0x96` request
`str/d14_20.ccs`, `str/d71_50.ccs`, `str/d72_50.ccs`,
`str/d81_20.ccs`, and `str/d81_30.ccs`, respectively; their matching file
headers produce `0x1420/0x7150/0x7250/0x8120/0x8130`. Request construction
is the `FUN_0035CF00 -> FUN_0035CC20` path described in
[CCS runtime](../../game/files/ccs_runtime.md#request-table-source).

**Contradiction:** For four decimal digits this producer cannot exceed
`0x9999`, but `0x0035A604..0x0035A60C` loads exactly `0x00200302`
(`lui v0,0x20; ori v0,v0,0x302`) and compares it with that word.
Thus the defender-`0x0A` numeric-name exclusion is not taken for the
inspected shipped cinematic headers. Defender `0x5D` has a separate,
unconditional exclusion. The bytes establish the mismatch, not an intended
replacement constant, intended filename, or player-facing move name.
No alternate producer between the parser store and this comparison appears
in the inspected callback.

## Authored appearance substitutions

SINF skill-row byte `+0x0A` counts appearance substitutions, and word
`+0x14` selects their first twelve-byte entry. This is separate from resource
request counts `+0x08/+0x09`. `FUN_00357B10` relocates the index to a pointer,
or sets it to zero for a zero count. The clean table is SINF
`[+0x1F04,+0x25AC)`, 142 entries. A complete bounded read of those entries
and the corresponding row fields found 57 skills referencing all 142:
96 `EXT` targets and 46 `MAT` targets.

An entry is `{source container name or zero, source palette name, target
name}`. Source zero means the request's main resident container. During
request setup, attacker-side appearance flags are masked with `5`: bit `0`
appends `c1` to the source palette name; otherwise bit `2` appends `c2`;
neither leaves it unchanged. Bit `0` wins when both are set. The suffix
literals are `0x006042B8/0x006042BC`. General character palette ownership is in
[Character assets](../../game/character_assets.md#model-and-appearance-name-consumers).

`FUN_00357FE0` handles `EXT` targets in the streamed container. It requires
the target, source container, selected palette, and target model `+0x94`
before calling `FUN_00198B10(model, 0x2000)` and applying the palette through
`FUN_00198AB0`. `FUN_00358130` handles other targets in the selected resident
container and writes their palette pointer at target `+0x04`. Both return
without substitution when a required lookup is absent; this does not prove
that such a lookup miss occurs for a shipped selection.

| Skill | Entries | Representative substitutions |
| ---: | ---: | --- |
| `0x01` | `5` | `2nrtbod1/CLT_2nrtbody` on five `EXT_2nrt00t0..04t0 body` targets. |
| `0x02` | `24` | Nine main-container copy targets, four body-provider targets, and eleven main-container material targets. |
| `0x20` | `2` | `1tovbod1/CLT_1tovbody` on `EXT_1tov00t0 body`; `1tyobod1/CLT_1tyobody` on `EXT_1tovudebody`. |
| `0x7F` | `5` | Three `1kkwbod1` and two `2kkwbod1` body targets. |
| `0x95 / 0x96` | `1` each | Both use main-container `CLT_2tywhss` on `MAT_e81hss01e`. |
| `0xB5` | `1` | Main-container `CLT_e93ssw` on `EXT_e93ssw`. |

## Per-character texture and draw-state switches

Two optional families load `BIN_` resources from `strmcmn` using the
attacker's abbreviation at resident `0x004034D0`. Their existence is
independent of the SINF substitution count. A bounded read of all directory
records and four-byte-aligned binary-block candidates in clean
`STRMCMN.CCS [0,0x6E708)` found exactly four such resource names, each with
one matching binary block:

| Resource | Directory ID | Decompressed payload | Authored changes |
| --- | ---: | ---: | --- |
| `BIN_strtc_data_kiw` | `404` | `0x68DB0` | Skill `0x8F`: source `d78_30e.ccs`, `TEX_1kiwakw1 -> TEX_1kiwakw2` on `EXT_1akw00t0 body` at frame `1`, reversed at `510`. |
| `BIN_strrev_data_itw` | `401` | `0x68C1C` | Skill `0x84`: `OBJ_rev01/OBJ_rev03`, enabled at `385`, disabled at `538`, group values `15/5`. |
| `BIN_strrev_data_kbw` | `402` | `0x68CB8` | Skill `0xAC`: `OBJ_rev01`, enabled at `235`, disabled at `263`, group value `10`. |
| `BIN_strrev_data_ksw` | `403` | `0x68D14` | Skill `0x88`: the same target names and `385/538` changes as the `itw` resource. |

Texture loader `FUN_00358560` expands all skill groups into resident
`0x00607738` before player construction. An absent resource or zero groups
returns zero; no group for the requested skill frees the table but returns
one. The constructor does not branch on that return value.
`FUN_00358AD0` does nothing with a null table. With a match, forward playback
applies an entry at its exact frame. Frame `1` or negative playback rate
instead invokes `FUN_003588D0` to reconstruct each target's texture from the
latest eligible entry. `FUN_00358BF0` checks source, target, and texture before
applying it; teardown `FUN_0035D7C0` frees the table.

Draw-state loader `FUN_00358DA0` runs during request setup, expanding into
resident `0x0060773C`. An absent resource, zero groups, or no matching skill
returns zero; the no-match branch also frees its table. A match calls
`FUN_003592C0(container, -1)` to initialize targets hidden. Per-frame calls
select the last change at or before the current frame, update a render-group
halfword through `FUN_0010A0A0`, set target `+0x84/+0x88` to `0.0/1.0`, and
use model helper `FUN_001987A0` selector `0/10`. `FUN_003590D0` frees the
table and attached helpers at request end.

These absent-table paths omit optional changes while the surrounding callbacks
continue. They do not establish a runtime failure or prove that every named
target/provider exists in every stream. The file-backed contents above come
from in-memory decompression of the identified clean CCS file; the resident
pointer slots that receive them are uninitialized in the static image.

## Defender-specific draw and placement dispatch

The draw callback `FUN_0035C110` passes defender ID, selected skill, and the
current frame to `FUN_00356E90`. A zero result omits `FUN_003556C0` for the
optional body object at record `+0x80`. Other draw-callback work still runs.
The helper's 184-pointer table at `0x005A9130` has 41 nonzero entries. Each
points to inclusive frame ranges and an optional defender list. A zero-length
defender list means the fixed IDs `{0x38,0x35,0x23,0x32,0x33,0x30}`. Outside
the selected ranges, for an unlisted defender, or with no skill table, the
helper returns one and ordinary drawing proceeds.

Seven code-driven table replacements precede the range check:

| Skill | Defender | Replacement omitted-draw ranges |
| ---: | ---: | --- |
| `0x84 / 0x88` | `0x30` | `258..274`, `426..539` |
| `0x84 / 0x88` | `0x49` | `426..635` |
| `0xB0` | `0x30` | `170..219` |
| `0x78` | `0x30` | `470..521` |
| `0x4E` | `0x35` | `333..667` |

For comparison, the ordinary `0x78` table has ranges `169..180`, `350..405`,
and `460..469`, restricted to IDs `0x49/0x30`; the override changes the
`0x30` case. Ordinary `0x84/0x88` omit `426..539` for
`{0x3B,0x30,0x38,0x33,0x32,0x49,0x4B}`. These are renderer gates, not damage,
contest-state, or cinematic-stop conditions. The table read covered every
nonzero skill pointer and all seven substitutions; it did not decode the
visible body animation in each range.

Position helper `FUN_003571F0` scans 15 skill headers at
`[0x005A9870,0x005A9924)` and their 31 distinct `0x20`-byte entries at
`[0x005A9490,0x005A9870)`. A matching defender and inclusive frame range
replaces the four-component position prepared by the per-frame callback;
no match leaves it unchanged. Shared lists cover skills `0x4F/0x54`,
`0x84/0x88`, `0xA7/0xB5`, and `0x1E/0x1F`. Representative complete entries
show the role of the replacement skill and defender:

| Skill | Defender | Frame range | Stored vector |
| ---: | ---: | --- | --- |
| `0x4F / 0x54` | `0x33` | `400..460` | `(-36,82,0,1)` |
| `0x84 / 0x88` | `0x3F` | `426..539` | `(9,-5,5,1)` |
| `0x95` | `0x28` | `421..470` | `(-144,-29,33,1)` |
| `0x96` | `0x28` | `461..510` | `(-144,-29,33,1)` |

`FUN_003572E0` separately scans all nine skill headers at
`[0x005A9CB0,0x005A9D1C)`. Its entries match a specific defender or `-1`
and an inclusive frame range, then interpret the prefix of an authored
object string. All entries in this clean table use `U `, `D `, `UU`, or `SXR`:

- `U ` clears object `+0xA8` bits `2..3`; `D ` sets those bits and restores
  `+0x84/+0x88` to `1.0` through the ordinary flag-dependent update.
- `UU` finds a named subobject of `CMP_1cmn00t0 trall` and replaces its first
  three matrix vectors with zero vectors.
- `SXR` negates the object's first matrix vector and marks its matrix dirty.

The helper also implements `SR`, `SYR`, and `SZR`, but no entry in this
bounded nine-header table uses them. They respectively negate all three,
the second, or the third matrix vector. Missing lookups simply leave the
target unchanged; this does not establish a missing shipped target.

The complete shipped dispatch is:

| Skill | Defender | Inclusive frame ranges and targets |
| ---: | --- | --- |
| `0x05` | any | From `336` through `9999`, `U ` on `EXT_e02_tdrn01/02`. |
| `0x84 / 0x88` | `0x16` / any | `UU` on the named common-body subobject at `426..539` for `0x16`; `SXR` on `EXT_e71eye02` at `0..9999` for every defender. |
| `0xA7 / 0xB5` | any | `U ` on `EXT_e93smk05c32/33/34`, `0..9999`. |
| `0x29` | any | `U ` on `EXT_1sin00t0 body`, `111..269`. |
| `0x9B` | any | `U ` on `EXT_1jrw00t0 body`, `151..168`. |
| `0x94` | any | `U ` on both `EXT_1tyw00t0` and `EXT_1cmn00t0` eye1/eye2/mou1 targets, `97..139`. |
| `0xB2` | any | On common eye1/eye2/mou1 targets: `D ` at `212..236`, `U ` at `237..281`, `D ` at `282..455`. |

These predicates can run every eligible frame, including the `SXR` matrix
operation. The static read establishes the operation and ordering, not the
accumulated visible orientation after the surrounding animation updates.

The hit-popup renderer `FUN_0035C5B0`, called by `FUN_0035C110`, provides
another interruption consumer. When contest status is `4` and
`FUN_0035DB20(0)` accepts the frame, it clears both popup-active halfwords at
record `+0x2D4/+0x2F8` and skips their normal animation work. Its bytes at
`0x0035C5E0..0x0035C610` corroborate the two clears. This uses the same
frame-`126` threshold as the presentation cut; it does not produce status `2`
or issue a cinematic branch request itself.

One setup family, `FUN_00358250`, temporarily replaces defender bone-node
models. It examines 17 named nodes from `0x005AB330`, storing each original
node model for restoration. Defender `0x32` enables all 17; defender `0x4C`
enables only `pelvis`, `spine`, and `spine1`; other IDs do no replacement in
this helper. It checks the node and provider before allocating a replacement,
and `FUN_0035AF20` restores every replaced model at request end. The 17-node
mask reads are `0x005C94A0` and `0x005C94C0`.

### Selected defender providers and cinematic targets

**Caller observation:** The replacement source is each provider object's
secondary model record at descriptor `+0x10`, not its primary model record
at `+0x0C`. `FUN_001B2670` sets these from separate words in the `0x0100`
payload; `FUN_00358250` reads `+0x10`, rejects a zero or sentinel-`4` runtime
at that record's `+0x2C`, and constructs a `0x60`-byte handle through
`FUN_001992A0`. It installs the handle at the cinematic target's `+0x9C`
while retaining the original in the skill-play record. Before that geometry
check it writes target `+0xA8` bit `5` from the node's mask, including clearing
the bit for a disabled node. Both node-name lookups pass optional flag `1`;
their miss/null handling follows
[CCS runtime](../../game/files/ccs_runtime.md#wildcards-and-secondary-values).

The body filename table at `0x00402710` and abbreviation table at
`0x004034D0` select `1gavbod1.ccs` / `gav` for defender `0x32`, and
`1schbod1.ccs` / `sch` for `0x4C`. The table words at
`0x004027D8/0x00402840` point to filename literals
`0x00402468/0x004025F8`; the abbreviation words at
`0x00403598/0x00403600` point to `0x00602EC4/0x00602F28`.
The formats at `0x005AB6C0/0x005AB6D0` are
`EXT_1cmn00t0 %s` and `OBJ_1%s00t0 %s`. General body-table ownership is in
[Character assets](../../game/character_assets.md#character-indexed-filename-families).

**Clean-file observation:** Both `PL/1GAVBOD1.CCS` and `PL/1SCHBOD1.CCS`
contain all 17 requested `OBJ_1gav00t0` / `OBJ_1sch00t0` node names at the
same directory IDs below. Every secondary link selects a model named
`MDL_1gav00t0 shadowNN` / `MDL_1sch00t0 shadowNN`, with model flags `0x0008`
and one mesh part. These are concrete geometry providers; the corresponding
primary bone-node models have zero parts and are not the helper's source.

| Node | Provider object ID | Secondary model ID / `shadow` suffix | Cinematic wrapper ID |
| --- | ---: | --- | ---: |
| `pelvis` | `6` | `72 / 17` | `118` |
| `spine` | `7` | `74 / 16` | `119` |
| `l thigh` | `8` | `76 / 12` | `120` |
| `l calf` | `9` | `78 / 11` | `121` |
| `l foot` | `10` | `80 / 10` | `122` |
| `r thigh` | `12` | `88 / 15` | `124` |
| `r calf` | `13` | `90 / 14` | `125` |
| `r foot` | `14` | `92 / 13` | `126` |
| `spine1` | `19` | `104 / 09` | `131` |
| `neck` | `20` | `106 / 08` | `132` |
| `head` | `21` | `108 / 01` | `133` |
| `l upperarm` | `33` | `132 / 04` | `145` |
| `l forearm` | `34` | `134 / 03` | `146` |
| `l hand` | `35` | `136 / 02` | `147` |
| `r upperarm` | `48` | `157 / 07` | `160` |
| `r forearm` | `49` | `159 / 06` | `161` |
| `r hand` | `50` | `161 / 05` | `162` |

The selected `pelvis/spine/spine1` source-object blocks are at decompressed
`0x257C/0x25BC/0x3478` in `1GAVBOD1.CCS`, and
`0x24BC/0x24FC/0x3238` in `1SCHBOD1.CCS`. Their secondary model blocks are
`0x14EE4/0x5038/0x4D9C` and `0x17044/0x5E48/0x5BAC`, respectively.
The `0x0800` parser `FUN_001B0C40` allocates a model runtime for their nonzero
part counts. This establishes the stored dependency and parser path, not
an observed successful allocation during a cinematic.

The cinematic column is the same in inspected `D71_50.CCS`, `D71_51.CCS`,
`D72_50.CCS`, and `D72_51.CCS`: all 17 common-node records have `0x0A00`
wrapper blocks. Their stored `OBJ_1cmn00t0` names become the caller's
`EXT_1cmn00t0` names through `FUN_001B2800`; that parser changes only the
first three name bytes. Wrapper traversal belongs to
[CCS runtime](../../game/files/ccs_runtime.md#type-0x0a00-traversal).
For the `50` variants, wrapper IDs `118/119/131` at
`0x1BEE0/0x1BF10/0x1C150` link to same-named model-instance IDs
`1161/1162/1174`. In the `51` variants, they are at
`0x1D8A0/0x1D8D0/0x1DB10` and link to `1252/1253/1265`.
Their stored parents are `117/118/119` in both variants.

The independently adjusted `EXT_e71eye02` also exists as wrapper ID `112`
in all four files: `0x1BDE0 -> 1155` in the `50` variants and
`0x1D7A0 -> 1246` in the `51` variants, with parent `72` and same-named
linked `OBJ_e71eye02` records. SINF skills `0x84/0x88` choose the `50`
variants normally; defender `0x4C` chooses the `51` variants through the
[opponent override](#opponent-dependent-cinematic-selection).
Thus these selected target names and source geometry are present. This
bounded asset check does not establish every cinematic's targets, live
allocation success, or the accumulated visible result of the repeated `SXR`
predicate.
