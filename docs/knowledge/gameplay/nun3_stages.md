# NUN3 battle stages

This document owns established and unresolved knowledge about the retail
NUN3 (`SLUS-21727`) battle-stage implementation: its `STAGE/` archives, the
compiled `BATTLE.BIN` stage tables and scene records, summon-scene switching,
and selected object behavior. It compares them with the retail NA2
(`SLPS-25837`) implementation documented in
[Battle stage gameplay knowledge](stages.md).

## Research coverage

- **Assigned scope:** the retail NUN3 battle-stage archives in `STAGE/`, the
  `BATTLE.BIN` stage tables and scene-record construction, summon-scene
  selection and archive switching, selected object parsers and reactive-object
  state, and their correspondence with retail NA2 stage archives and records.
- **Exploration depth:**
  - Exhaustive over assets and tables: all 28 NUN3 and all 24 NA2 stage
    archives were decompressed and section-walked; all 27 NUN3 stage tables
    were decoded; shared content was measured by section comparison for every
    NA2/NUN3 archive pair, with texture sections compared only by raw payload
    hash.
  - Construction census: the scene constructor, its jump table, and the
    category 0, 1, 2, 10, 11, 13, and 14 handlers were read; the full subtype
    dispatch/construction intervals of categories 3..9 cover all 100 retail
    types and 666 records in categories 3..8, plus the empty category-9
    handler.
  - Bounded traces: common model ownership and the seven draw/update loops;
    parsers for ordinary/rotating sky, frame animation, glare, wire,
    transparency, bridge, base breakables, and training dolls; the complete
    update methods and derived destructors of types `0x801/0x871`, `0x803`,
    `0x813`, `0x81C`, and `0x81D`; resident model advance `0x00171140`; scene
    method `0x007C24C0` and restriction producer `0x007D1600`; the eight-row
    summon mapping, preload/request path, and the resident manager's switch,
    release, and restoration branches.
- **Confirmed coverage:** the archive set and CCS format compatibility; the
  stage table and record layout; the fog, line, player, and lighting
  categories; complete retail construction routing; object-list draw/update
  consumers and update gates; training-doll node preparation; shared break
  transitions, the training-doll reset sequence, lantern/wind-bell motion,
  and scoped derived cleanup; selected parser-format differences from NA2;
  summon selection and the bounded archive switch/return path; availability
  in every NUN3 stage archive of the nodes NA2's mandatory records request;
  and the NA2 archives that reuse NUN3 stage content.
- **Unresolved or untested:**
  - state machines and derived teardown of subtypes outside the bounded
    `0x801/0x871/0x803/0x813/0x81C/0x81D` set;
  - the complete upstream scene-object binding and every indirect destruction
    path; the summon-manager trace is not a proof over every battle mode;
  - the full mode meanings of the restriction conditions and of global
    predicate `0x0030F870`, the producer of the wind-bell scalar, and the
    effect semantics of resident `0x0030FCB0/0x0030FD30`;
  - whether texture pixels are shared between NA2 and NUN3 archives;
  - complete token formats and update-state equivalence for the NA2
    correspondences supported only by labels and resources;
  - local update counts do not establish elapsed time.
- **Deliberate exclusions and overlap:** the NA2 implementation belongs to
  [Battle stage gameplay knowledge](stages.md); resident CCS section types
  belong to
  [Resident CCS object-type identities](../game/files/ccs_object_types.md);
  input identities and address conversion belong to
  [Retail game file identities](../game/files/file_identities.md). NUN3
  RPG-mode stages (`RPGSTAGE/`) and the NUN3 stage-select presentation were not
  examined.
- **Evidence limitations:** validation was static against the retail NUN3
  `SLUS_217.27`, `BATTLE.BIN`, and `STAGE/` archives and the retail NA2
  `STAGE/` archives, whose sizes match their `GZLIST.TXT` entries. No runtime
  validation was performed.

## Evidence and address convention

NUN3 inputs are identified in
[Retail game file identities](../game/files/file_identities.md); the stage
archives are the retail NUN3 `DATA.CVM` extraction's `STAGE/` directory.
`BATTLE.BIN` addresses in this document are live addresses unless stated; their
conversion follows the
[address conventions](../game/files/file_identities.md#address-conventions).

## Archive set and CCS format

**Observations:**

- NUN3 `STAGE/` holds `S01.CCS` through `S20.CCS` and eight summon archives,
  `KTYS_BNT`, `KTYS_KTY`, `KTYS_MND`, `KTYS_SKK`, `KTYS_SKK2`, `KTYS_SKR`,
  `KTYS_STR`, and `KTYS_TYO`. NA2 `STAGE/` holds only `S01` through `S24`.
- Every archive in both directories is a gzip CCS stream whose compressed and
  decompressed sizes equal that game's `GZLIST.TXT` entry, whose chunk-2
  version halfword is `0x123`, and whose section walk ends at the type-5
  terminator.
- The section tags used by NUN3 `S01` through `S20` are a subset of the
  resident dispatcher documented in
  [Resident CCS object-type identities](../game/files/ccs_object_types.md):
  `0x0100..0x0400`, `0x0600..0x0B00`, `0x0C00`, `0x0E00`, `0x1300`, `0x1400`,
  `0x1900`, `0x2000`, plus one `0x0500` camera in `S12` and
  `0x0D80`/`0x0D90` generator records in `S10` and `S17`. NUN3 `S05` has three
  `0x0600` lights; every other `Sxx` archive in both games has exactly one,
  `LGT_dis_0`. No NUN3 stage archive contains a
  `0x2400` section or a `BIN_bgdata` object; every NA2 stage archive does.
- Decompressed sizes: NA2 `S01..S24` range from 531,692 bytes (`S17`) to
  1,323,828 bytes (`S24`). NUN3 `S01..S20` range from 1,032,152 bytes (`S13`)
  to 1,412,076 bytes (`S08`); 13 of the 20 exceed NA2's largest archive
  (`S01`, `S03`, `S04`, `S07`, `S08`, `S09`, `S12`, `S14`, `S15`, `S17`,
  `S18`, `S19`, `S20`).

| NUN3 archive | Compressed | Decompressed | NUN3 archive | Compressed | Decompressed |
| --- | ---: | ---: | --- | ---: | ---: |
| `S01` | 574,632 | 1,352,844 | `S11` | 495,333 | 1,149,440 |
| `S02` | 600,237 | 1,266,532 | `S12` | 801,730 | 1,367,924 |
| `S03` | 638,320 | 1,375,380 | `S13` | 459,399 | 1,032,152 |
| `S04` | 626,606 | 1,355,476 | `S14` | 730,753 | 1,399,060 |
| `S05` | 431,639 | 1,187,584 | `S15` | 559,613 | 1,388,844 |
| `S06` | 599,084 | 1,273,552 | `S16` | 530,068 | 1,083,280 |
| `S07` | 601,986 | 1,386,132 | `S17` | 616,814 | 1,394,120 |
| `S08` | 675,392 | 1,412,076 | `S18` | 591,845 | 1,360,832 |
| `S09` | 457,467 | 1,344,808 | `S19` | 617,828 | 1,351,304 |
| `S10` | 409,507 | 1,177,460 | `S20` | 671,990 | 1,404,100 |

**Confirmed shared encoding:** for NA2/NUN3 archive pairs that carry the same
stage content (next table), same-named `0x0800` model, `0x0100` object, and
`0x1300` dummy sections are frequently byte-identical, or identical in length
with differences only in words below `0x4000` (object-table indices, which
differ because the two archives number their objects differently). For
example, 198 of the 223 `MDL_` sections in NA2 `S14` match NUN3 `S16` this
way, and 209 of 223 `0x0100` sections do. Model, object, and dummy sections
therefore use the same payload encoding in both games; the two archives differ
in their object-table index references.

## Stage content already shared with NA2

Comparing hit-mesh payloads (ignoring their first four words), same-named
model sections, and dummy positions gives these pairs:

| NA2 archive (slot / logical ID) | NUN3 archive (table index, name) | Evidence |
| --- | --- | --- |
| `S08` (7 / 8) | `S07` (6, 木ノ葉の森, Konoha forest) | 38 identical and 36 index-only-different of 137 models; 3 of 7 hit meshes |
| `S09` (8 / 9) | `S03` (2, 第４４演習場死の森, Forest of Death) | 5 of 5 hit meshes; 65 identical of 68 dummies; line counts below |
| `S10` (9 / 10) | `S14` (13, 終末の谷, Valley of the End) | 5 of 6 hit meshes; 45 identical dummies |
| `S13` (12 / 13) | `S10` (9, ナルト大橋, Great Naruto Bridge) | 7 of 11 hit meshes; 48 index-only-different models |
| `S14` (13 / 14) | `S16` (15, 中忍試験会場, Chunin exam arena) | 198 of 223 models, 209 of 223 objects |
| `S15` (14 / 15) | `S18` (17, 短冊街のはずれ, Tanzaku outskirts) | 72 of 102 models; 35 identical dummies |
| `S16` (15 / 16) | `S13` (12, 君麻呂戦の草原, Kimimaro battle field) | 5 of 5 hit meshes; 132 identical dummies |
| `S23` (22 / 3) | `S15` (14, 物見やぐら, watchtower) | 60 of 78 models; 55 identical dummies |
| `S24` (23 / 4) | `S09` (8, 短冊街, Tanzaku Town) | 5 of 5 hit meshes; 83 identical dummies; line counts below |

No pair is an identical copy: every pair also has differing models,
animations, and dummies. Texture sections were compared only by raw
payload hash, and none matched; whether texture pixels are shared was not
established. No match of
this kind was found for NUN3 `S01`, `S02`, `S04`, `S05`, `S06`, `S08`, `S11`,
`S12`, `S17`, `S19`, or `S20`, nor for NA2 `S01..S07`, `S11`, `S12`, or
`S17..S22`.

## NUN3 stage table and scene records

**Confirmed:** NUN3 has no `BIN_bgdata` parser, no `takaCreateBackGround`
string, and no `ccBg*`, `ccField`, or `ccBgControl` class names in either
`SLUS_217.27` or `BATTLE.BIN`. Its per-stage scene configuration is compiled
into `BATTLE.BIN` as record tables.

The stage table is 27 pointers at live `0x00913450` (file `0x157C50`),
terminated by a zero word. Each pointer addresses a zero-terminated array of
`0x20`-byte records:

| Offset | Field |
| ---: | --- |
| `+0x00` | Shift-JIS label pointer (an empty string for unlabeled records) |
| `+0x04` | record type: category in bits 8..15, subtype in bits 0..7 |
| `+0x08`, `+0x0C`, `+0x10` | resource-name pointers (for example `ANM_..._n1`, `_d1`, `_n2`), or zero |
| `+0x14` | configuration: consecutive NUL-terminated tokens read by resident `0x0018F190(string, n)`, which returns the `n`th token |
| `+0x18`, `+0x1C` | two signed integers, `-1` when unused |

Record 0 of every table is type 1; its label is the stage name and `+0x08` is
the archive path. The table indices are:

| Index | Archive | Label |
| ---: | --- | --- |
| 0 | `stage/s01.ccs` | ラーメン一楽 |
| 1 | `stage/s02.ccs` | 歴代火影の顔岩 |
| 2 | `stage/s03.ccs` | 第４４演習場死の森 |
| 3 | `stage/s04.ccs` | 英雄の慰霊碑 |
| 4 | `stage/s05.ccs` | 桔梗城天守閣 |
| 5 | `stage/s06.ccs` | 木ノ葉温泉 |
| 6 | `stage/s07.ccs` | 木ノ葉の森 |
| 7 | `stage/s08.ccs` | 風影の屋敷 |
| 8 | `stage/s09.ccs` | 短冊街 |
| 9 | `stage/s10.ccs` | ナルト大橋 |
| 10 | `stage/s11.ccs` | 砂肝亭と仏像 |
| 11 | `stage/s12.ccs` | 音忍戦の森 |
| 12 | `stage/s13.ccs` | 君麻呂戦の草原 |
| 13 | `stage/s14.ccs` | 終末の谷 |
| 14 | `stage/s15.ccs` | 物見やぐら |
| 15 | `stage/s16.ccs` | 中忍試験会場 |
| 16 | `stage/s17.ccs` | サバイバル演習場 |
| 17 | `stage/s18.ccs` | 短冊街のはずれ |
| 18 | `stage/s19.ccs` | ザブザの隠れ家 |
| 19 | `stage/s20.ccs` | 修練の崖 |
| 20..26 | `stage/ktys_skk/str/bnt/kty/mnd/skr/tyo.ccs` | 口寄せ（…）summon scenes |

`stage/ktys_skk2.ccs` is present as a `BATTLE.BIN` string but not in this
table or the character-to-summon-scene mapping below.

## NUN3 summon selection and archive lifetime

**Confirmed:** resident `0x00373A50(index)` returns a `0x10`-byte row from
the eight-row table at `0x00673590` (ELF file `0x573690`). The row fields are
mapping index, character ID, stage-table index, and a zero word:

| Mapping index | Character ID | Scene index | Archive |
| ---: | ---: | ---: | --- |
| 0 | `0x04` | 20 | `stage/ktys_skk.ccs` |
| 1 | `0x10` | 21 | `stage/ktys_str.ccs` |
| 2 | `0x15` | 22 | `stage/ktys_bnt.ccs` |
| 3 | `0x01` | 22 | `stage/ktys_bnt.ccs` |
| 4 | `0x19` | 23 | `stage/ktys_kty.ccs` |
| 5 | `0x09` | 24 | `stage/ktys_mnd.ccs` |
| 6 | `0x07` | 25 | `stage/ktys_skr.ccs` |
| 7 | `0x0E` | 26 | `stage/ktys_tyo.ccs` |

Live BATTLE `0x00866BE0(character)` scans all eight rows, compares row
`+0x04`, and returns row `+0x00`, or `-1` if absent. `0x00866BB0(index)`
returns row `+0x08`. Resident `0x0028AB50(character, side)` accepts exactly
the eight listed IDs, sets bit `0x80` of the battle context's byte `+0x01`,
stores the selected scene in byte `+0x7B`, and stores `side + 1` in byte
`+0x7C`. The context pointer is resident `gp-0x5AA4`. These numeric IDs are
not stage slots; two character IDs deliberately resolve to scene 22.

The resident sequence at `0x002E4900` preloads before it publishes that
request. In state 2, when signed halfword counter `+0x16` is 85, calls at
`0x002E4E4C/0x002E4E58` map the selected character and
`0x002E4E64` calls `0x0028AC30(scene)`. That helper takes record 0's
`+0x08` path from the overlay table, queues `0x0018EE90(path, 0)`, and calls
`0x0018EFF0`. The sequence subsequently waits for `0x0018F0C0` to return
zero and calls `0x0018F0D0`; state 4 publishes the character/side request
through `0x0028AB50` at `0x002E517C`.

The table's archive helpers have distinct behavior:

| Live BATTLE entry | Behavior |
| --- | --- |
| `0x007D1FC0` | Queue record 0's path through `0x0018EE90(path, 0)`. |
| `0x007D1E20` | Look up that path through `0x00160800`; if absent, synchronously load through `0x00113620(path, 0)`. Store the handle at `0x00945910`. |
| `0x007D2010` | Require an already loaded archive through `0x00160870` and store its handle at `0x00945910`. |
| `0x007D1EA0` | Free each non-null handle in the four slots at `0x00945910..0x0094591C` through `0x00160000(handle, 1)` and clear its slot; also look up and free `ojmgmk`, `ojmgmt`, `ojmpkn`, and `ojmnkm`. Those four names occupy `0x1E`-byte entries at live `0x009133D0`. |

Both lookup functions normalize the supplied path through `0x001608F0`
before comparing archive names. `0x00160800` returns zero when absent;
`0x00160870` traps when absent. Neither increments an ownership counter in
its inspected body. `0x00160000` unlinks and destroys the archive and,
with argument 1, frees its allocation. Thus storing a handle is not evidence
of reference-counted archive ownership. The three index-taking overlay
helpers and resident `0x0028AC30` do not range-check the table index; they
only skip a null table pointer.

Resident manager `0x00287630` establishes this bounded switch/return path:

- State `0x12` tears down the running battle owner through `0x0027E5F0`.
  For a pending scene with nonzero context `+0x7C`, it saves current index
  `+0x61` into `+0x7D`, copies pending `+0x7B` to current `+0x61`, queues the
  selected archive at `0x00288D70`, commits the queue, and proceeds to state
  8. The release branch at `0x00288AB0` is conditional on `+0x7C == 0`, so
  this entry branch does not invoke it.
- State 8 waits for the loader and transition fence, then records the loaded
  archive through `0x007D2010` at `0x0028822C` before the next battle owner
  is constructed. Resident `0x002753C0` classifies current indices 20..26
  as context word `+0x5C == 2`; other indices become 1.
- The active-battle routine `0x00281520` can request return when that word
  is 2, its halfword `+0x08` is 5, context byte `+0x00` bit `0x20` is set,
  and both fighter checks through `0x001A76B0` return zero. It publishes the
  saved `+0x7D` into pending `+0x7B`, clears `+0x7C`, sets the request bit,
  and writes transition reason 11 at context `+0x960`.
- Manager state `0x0C`, when `+0x5C == 2`, frees the tracked summon archive
  at `0x002886BC`, restores `+0x61` from `+0x7D`, and looks up the saved
  stage archive through `0x007D2010` at `0x002886DC`. It reclassifies the
  current index, then calls the release helper again at `0x00288748`.
  The recorded lookup and release ordering is confirmed; this branch does
  not enqueue the saved archive again.

This proves selection, preload, publication, manager switching, and the
documented cleanup/restoration branches. The scene-record constructor below
takes the same table index. Its complete upstream object-binding path and
every indirect destruction path were not established by this trace; no
stronger archive-lifetime guarantee is inferred from these calls.

## NUN3 scene-record dispatch

The scene constructor begins at live `0x007C26C0` (preserved `FUN_007c2680`,
file `0x006EC0`) and takes the control object and the table index. It writes
the index to two optional global objects, then walks the records and jumps
through the 15-entry table at live `0x00929B90` (file `0x16E390`) using
`type >> 8`. After the walk it runs fixed setup calls. **Confirmed** handler
behavior:

| Category | Handler (live) | Confirmed behavior |
| ---: | --- | --- |
| 0 | inline | Strip the path to its basename, adopt the archive through `0x00160870` into control `+0x22C`, resolve `BLT_bg` and `BLT_obj` through `0x0015F440` into `+0x21C`/`+0x220`, and store the index at `+0x8C`. |
| 1 | `0x007C7180` | Parse seven tokens: RGB into `+0x1B8`, then four floats into `+0x1BC..+0x1C8`, and call resident `FUN_0010BF80`, which stores near/far distances and converts the two percentages to fog coefficients `(100 - p) * 2.55` with a linear ramp between the distances. This is the fog setup. |
| 2 | `0x007C7300` | Empty (`jr ra`); its retail tokens such as `0,-2750,800` have no effect. |
| 3 | `0x007C7CC0` | Thirteen explicit subtype branches; far-view/sky/effect objects enter the vector at control `+0x240`. The constructor also calls `0x007C3A40(index)` after each category-3 record. |
| 4 | `0x007C8900` | Only subtype 1: a base animation object enters `+0x24C`; its model becomes control `+0x228` if that field is still zero. |
| 5 | `0x007C8A10` | Sixty-eight subtype branches for animations, particle/deformation effects, and props; their objects enter `+0x258`. |
| 6 | `0x007CF7E0` | Fourteen subtype branches; transparent objects and frame animations enter `+0x288`. |
| 7 | `0x007CC810` | Seventeen subtype branches; creatures, flags, and other props enter `+0x264`. |
| 8 | `0x007CDCC0` | Twenty-one subtype branches; breakable/moving objects enter `+0x270`, including the multi-instance training-doll helper. |
| 9 | `0x007CF7D0` | Empty (`jr ra`); no retail table contains a category-9 record. |
| 10 | `0x007C6870` | Player records `プレイヤー１/２`; token 3 is `DMY_pp1_010` / `DMY_pp2_010`, resolved through `0x0015F440`. |
| 11 | `0x007C6910` | Front/back (`前`/`後`) line family; token 3 is `DMY_line_010` / `DMY_line_020` and token 5 is that family's node count. |
| 12 | none | Skipped by this constructor (type `0xC0A` in three stages). |
| 13 | `0x007C7310` | Lighting: record `+0x08` names the light animation (`ANM_stalig00` in every stage) and the handler formats `LGT_dis_%d` names. |
| 14 | `0x007C7870` | Front/back records whose token 5 is the number of `DMY_{f,b}_cl_N_*` lines. |

The subtype branches were read through their complete raw instruction
intervals. Every retail type in categories 3 through 8 has an explicit
construction branch. This is a construction census, not a
complete semantic decode of every object's update method:

| Category | Distinct retail types | Retail records | Vector header |
| ---: | ---: | ---: | --- |
| 3 | 8 | 92 | `+0x240` |
| 4 | 1 | 30 | `+0x24C` |
| 5 | 54 | 327 | `+0x258` |
| 6 | 4 | 52 | `+0x288` |
| 7 | 14 | 49 | `+0x264` |
| 8 | 19 | 116 | `+0x270` |

Counts include all 27 tables, including the seven summon-scene tables, and
count records rather than the potentially larger number of objects created
by a record. Each vector has count at header `+4` and pointer storage at
header `+8`; append uses live `0x007D2310`. At live `0x007C297C..0x007C29B0`,
the scene constructor points control `+0x294..+0x2AC` at the seven headers
`+0x240`, `+0x24C`, `+0x258`, `+0x264`, `+0x270`, `+0x27C`, and `+0x288`.

The common object constructor, live `0x007D8A60`, initializes the archive at
object `+4`, resource/model fields, subtype halfword `+0x20`, status `+0x24`,
update flag `+0x28`, and vtable `+0x34`. Its virtual initializer at live
`0x007D8B60` adopts the archive, constructs the record's optional animation
into model `+0x2C`, retains its name at `+0x0C`, and stores the supplied
initialization category at `+0x30`. The record category alone does not define
that stored value: for example, the `0x79B` flag branch supplies category 5,
and `0x601` explicitly stores subtype `0x12` rather than 1 at `+0x20`.

The seven draw loops in live `0x007D0500..0x007D098C` follow those header
pointers and call object vtable `+0x14` while object byte zero is clear.
The update loops in live `0x007D0990..0x007D0F44` call vtable `+0x10`; when
control `+0xC30` is nonzero they also consult object `+0x28`. This is a
conditional update gate, not an unconditional enable requirement. Object byte
zero must also be clear to reach the update callback. Base draw
live `0x007D05A0` submits model `+0x2C` through resident `0x00171640`.
Base destructor live `0x007D8AB0` releases models `+0x2C` and `+8` through
`0x0016CFE0` and optionally frees the object. Derived objects may own
additional arrays/controllers; this base path does not prove their entire
teardown.

Scene update live `0x007C24C0(control, category_mask)` first runs restriction
producer `0x007D1600`, then calls permission helper `0x007D1080(control, 1)`.
For argument 1 that helper returns true; the following control byte `+0x74`
is the effective whole-scene update gate in this entry. If clear, scene fade
`+0x70` changes by `0.05` toward zero or one according to byte `+0x6C`.
Category-mask bits `1/2/4/8/0x10/0x20/0x40` select the seven headers in their
documented order, with category 5 dispatched through control vtable `+0x18`.
Omitting a category prevents its object callbacks in this method.

Restriction producer `0x007D1600` clears `+0xC30` every invocation and builds
the following bitmask when the global battle context exists:

| Bit | Statically established condition |
| ---: | --- |
| 1 | Control byte `+0x74` is nonzero. |
| 2 | Battle context `+0xA2C` is non-null and its word `+0x34 == 1`. |
| 4 | Resident `0x0030FE70` returns nonzero; its complete retail body returns zero, so this branch does not set the bit. |
| 8 | The chained mode words equal `(5,0)` and the optional global owner's byte `+0x10` or one of halfwords `+0x9FE/+0x9F8/+0xAA6/+0xAA0` is nonzero. |
| `0x10` | `0x002B7D30(battle_context+0xAC0)` returns nonzero. |
| `0x20` | Another global owner's `+8` child is non-null and its word `+0x10 == 2`. |
| `0x40` | Battle context word `+0x960` is nonzero. |

The mode meanings of these conditions are not all named. With any nonzero
mask, an object with byte `+0x28 == 0` is skipped; nonzero values still enter
the ordinary byte-zero check. With a zero mask that opt-in byte is ignored.
The inspected category-8 construction branches set it to 1. Thus these
reactive objects opt into restricted updates, subject to the outer category
and scene gates. Their local counters remain invocation counts. Rotating-sky
`0x00805BE0` adds `0.98 * speed` directly per invocation, while shared frame
animation `0x00806B70` passes model `u16 +0x94` to `0x00171140`; neither
method derives seconds from elapsed wall-clock time.

The node-count tokens were checked against the archives: category 11 gives 2
and 18 `DMY_line_0x0` nodes for index 0, matching `S01`'s node counts, and
index 3's category 14 back count of 3 matches `S04`'s `DMY_b_cl_1_ewr`,
`DMY_b_cl_2_ewr`, and `DMY_b_cl_3_nor`. NUN3 `BATTLE.BIN` contains the same
`DMY_linemin01/02`, `DMY_linemax01/02`, and `DMY_%scl_%d_nor/ewr/mov` strings
as NA2 BTL.

The following labels/resources identify representative content. The stage
counts in this table concern the 20 normal tables; the construction census
above also includes summon scenes:

| Type | Normal tables | Example label (gloss) and resources |
| --- | ---: | --- |
| `0x301`, `0x38A`, `0x390`, `0x392` | 20, 8, 4, 3 | sky/far animations; `回る空` (rotating sky), `最遠景グレア` (far-view glare) |
| `0x401` | 20 | main stage animation `ANM_*are00` |
| `0x502` | 5 | `電線` (electric wire) with `DMY_dummy_010`/`020` endpoints |
| `0x526`, `0x528`, `0x582`, `0x583` | 8, 3, 9, 1 | swaying grass, leaves, and trees (`OBJ_eda_*`, `CMP_ki_*`) |
| `0x52B`, `0x52D`, `0x51B` | 8, 3, 6 | falling, rising, and blowing leaves (`CMP_*efe*`) |
| `0x579`, `0x57B`, `0x57D`, `0x587` | 1 each | water surface, rowing boat, mangrove, suspension bridge |
| `0x578` | 1 | `足跡` (footprints) |
| `0x595..0x59E` and other `0x5xx` | 1..2 | stage-specific effects (memorial water, hot-spring steam, waterfalls) |
| `0x601`, `0x690` | 7, 8 | `透過柱` transparent pillars with `DMY_*has*_hit` and a configured contact scalar; frame animations |
| `0x7xx` | 1..2 | stage creatures and props (toad, snake, spiders, fish, flags) |
| `0x81C`, `0x81D` | 20 | `訓練君` / `うっきー君` training dolls with `DMY_dd_010`/`DMY_pg_*` and break objects |
| `0x801..0x87C` | 1..5 | breakable props with `_n1`/`_d1`/`_n2` animations and `OBJ_bre_*` debris |

## NUN3 object parsers and concrete comparisons

All addresses in this subsection are live. NUN3's consecutive-NUL token
reader is `0x0018F190`; integer conversion is `0x00365310`, and float
conversion passes through `0x003652F8`/`0x003651D0`.

| NUN3 type | Parser | Confirmed fields or behavior |
| --- | --- | --- |
| `0x301` | `0x007D8C90` | Token 10 becomes a Boolean at object `+0x38` and is passed to model helper `0x00171D00`. This ordinary animation branch is distinct from rotating sky. |
| `0x38A` | `0x00805B60` | Token 10 is float angular speed `+0x38`; initial angle `+0x48` comes from `0x002B1D80(pi)`. Update `0x00805BE0` adds `0.98 * speed`, wraps around `±pi`, and applies the vector at `+0x40` to model `+0x2C`. |
| `0x390`, `0x590`, `0x690` | `0x00806B00` | The same constructor/parser handles all three categories. Nonzero integer token 10 divides the model's `u16 +0x94`; update `0x00806B70` advances that animation through `0x00171140`/`0x001715A0`. |
| `0x392` | `0x00806D70` | An effect controller at object `+0x38` receives token 7 as mode byte `+0x81`, token 8 as packed word `+0x84`, token 9 as float `+0x88`, and token 10 as packed word `+0x8C`. Up to three optional record resources become separate models; draw `0x00807090` submits them and the effect controller. |
| `0x502` | `0x007E65C0` | Record `+0x0C/+0x10` name the endpoint nodes; token 6 names the texture. Endpoints are ordered by component 0 and copied to `+0xE0/+0xF0`. Segment count is 15 at `+0x64`, with three allocated node arrays and segment/controller storage. |
| `0x601` | `0x007E90D0` | Token 3 resolves the hit/position node into `+0x80/+0xB0`; integer token 8 plus 150 becomes `+0xC8`. A collision controller is constructed at `+0x3C/+0x60`. Update `0x007E92B0` matches contact entries against both global fighters, divides the smaller positive contact scalar by `+0xC8`, and uses the resulting blend to write model frame `+0x88`. |
| `0x587` | `0x00803E10` | Token 5 is the segment count; token 7 is the model resource, 8/9 are floats at `+0x48/+0x4C`, and 10 becomes byte `+0x50`. Token 3 is the per-segment node-name stem, token 6 is the texture, and tokens 1/2 resolve the two endpoint nodes. Three arrays at `+0x3C/+0x40/+0x44` hold model and rope/helper elements. |
| `0x801`, `0x871`, and base paths of `0x803/0x813` | `0x007D8E40` | Integer token 0 is stored at `+0x78` and copied to `+0x74`; 3/4 resolve two position nodes, 5 is a byte count, 7 is the debris resource, 8/9 are integer-derived float dimensions, and 10 is integer `+0x94`. Record `+0x0C/+0x10` retain the later animation names. The parser constructs attack/contact controllers and optional debris; subtype-specific methods own later reactions. |
| `0x81C` | `0x007C2BD0` → `0x007DAFA0` | Integer token 5 controls a loop allocating `0x180`-byte training-doll objects. Each takes one `0x20`-byte entry from control's node array `+0x1D0`, stores subtype `0x1C`, runs the doll parser, determines its section through `0x007D1100`, and appends to the category-8 vector. One record can therefore construct several dolls. |

The category-3 follow-up `0x007C3A40(index)` prepares those doll nodes before
the later category-8 record. If control `+0x1D0` is null, it scans that
stage's entire record table for type `0x81C` and calls `0x007C2A70`. That
helper reads node-name stem token 3 and count token 5, allocates
`count * 0x20` bytes at `+0x1D0` and `count` flag bytes at `+0x1D4`, stores the count
as a halfword at `+0x6A`, and copies each resolved node's position into its
entry. Entry zero uses the stem unchanged; later entries use `%s_%d` at live
`0x00929BD0`, for example `DMY_dd_010_1`. All 20 retail tables containing a
training-doll record place a category-3 record before it. This establishes the
node-preparation dependency of training-doll construction.

## NUN3 reactive-object states and derived cleanup

All addresses here are live. These methods use vtable `+0x10` for update,
`+0x1C` for the contact-trigger callback, and `+0x18` for destruction. The
bounded set is types `0x801/0x871`, `0x803`, `0x813`, `0x81C`, and `0x81D`;
other category-8 subtypes are not covered by these state descriptions.

The shared prepass `0x007D9B40` tests global predicate `0x0030F870` and
contact-controller field `+0xC8` before running `0x007D9A40`. A resolved
fighter-like contact is rejected for descriptor `+0x10 & 0x00F00000`,
`+0x10 & 2`, or `+0x14 & 0x02000000`; acceptance sets byte `+0x38` and
unregisters receiver `+0xC0` through resident `0x00180000`. Update completion
clears the contact byte through `0x007D9A30`. The same prepass also produces
a triangular scalar from the global counter at `+0x198` and latches render
byte `+0x134` when receiver `+0xA8` is nonzero. The global predicate's full
mode meaning remains unresolved.

Base trigger `0x007D9700` accepts a nonzero contact byte while remaining
count `+0x78 != -1`. Count below 2 becomes `-1`, selects the record's
`+0x10` animation when present, enables optional debris `+0x90`, and
unregisters receiver `+0xA0`. A larger count loses one, selects record
`+0x0C` when present, and dispatches stage effect helper `0x007D4A20`.
Base update `0x007D9470` runs that callback, optional debris update, and model
advance. A positive count, nonzero halfword `+0x3A`, and animation completion
re-register receiver `+0xC0` through `0x0017FF80`. A broken count and completed
animation can reselect the later animation and seek to configured integer
`+0x94 << 8`; this is a selected pose, not a periodic increment. Types
`0x801` and `0x871` install the same base vtable `0x0068C6E0` and update.

Resident model advance `0x00171140` adds its second argument to model's
fixed-point position `+0xB0`, with 256 units per animation frame. The scoped
object methods normally pass model `u16 +0x94`; integer/fraction outputs are
`+0x98/+0x96`. The method clamps to `(frame_count - 1) * 256` and returns
completion, except that an animation flagged to loop can reset to zero and
return false. Model helper `0x00171D00(model, 3)` propagates parameter 3 to
effect/model children; it does not itself set a playback-loop flag. Object
transitions sometimes advance immediately after replacing an animation in
addition to the ordinary advance later in that invocation. These calls do
not establish one animation frame or one advance per scene update.

| Type / authored role | Update / additional method | Confirmed local state |
| --- | --- | --- |
| `0x803`, lanterns | `0x007DA150`; motion `0x007DA250` | Contact restores configured amplitude and sets field `+0x154` to 30. Contact entity `s16 +0x8E0 == 1` resets phase to 0, value 0 selects phase 36, and other values leave phase unchanged; a missing entity selects 0. Phase `+0x148` advances by 2; table samples scale amplitude `+0x144`. Each wrap multiplies amplitude by `0.6`, floors it at `0.05`, and re-registers the contact receiver only while count remains positive. The model transform receives the sample and `0.3 * sample` on two components. The trigger also retains contact side bit at `+0x13C`; its effect callback `0x007D9D90` selects one of three parameter paths from configuration byte `+0x158`. |
| `0x813`, wind bells | `0x007DA490`; motion `0x007DA590` | Contact resets phase, restores configured amplitude, and sets local field `+0x158` to 30. Phase advances by 2 through the same shared table. At its end amplitude decays by `0.6`, floors at `0.05`, and phase resets; a positive count permits receiver re-registration. The applied transform combines the sample with `0.3` times a resident scalar. That scalar's producer is not identified here. |
| `0x81D`, `うっきー君` | `0x007DADD0`; parser `0x007DACF0` | Uses the shared count/animation/contact sequence. Its parser sets contact shape `+0x18` to three times the float at object `+0x60` and adds 50 to shape `+0x1C`. This shape adjustment distinguishes it from the base object; no randomized doll-respawn delay is present in this update. |
| `0x81C`, `訓練君` | `0x007DB720`; reset `0x007DB5A0` | Adds delayed appearance, a separate animation sequence, and node-following reset, detailed below. |

Training-doll parser `0x007DAFA0` stores `D = 10 * integer(token 1)` at
`+0x168` and copies token 10 to sequence counter `+0x94/+0x164`. Reset
`0x007DB5A0` zeros elapsed counter `+0x15C`, sets delay `+0x160` to
`D - (R % trunc(0.4 * D))` using RNG `0x002B1CF0`, and restores that sequence
counter. This expression requires a nonzero divisor; the recovered example
uses token 1 = 10 and therefore `D = 100`.

While elapsed is below delay, the doll sets remaining count to `-1`, increments
elapsed once, and skips the contact/animation path. At equality it selects
hardcoded `ANM_anm_doll_a1`, advances it, restores the configured count, and
increments elapsed beyond equality. The later completion branches use
`ANM_anm_doll_n1` for positive sequence steps and `ANM_anm_doll_v1` at step
zero; they decrement the sequence counter and explicitly disable/re-enable
the contact receiver around selected transitions. A negative step or a broken
doll whose retained contact/debris conditions permit it schedules another
randomized delay. When scene index `+0x140 == 3`, a retained broken-contact
marker also calls resident `0x0030FCB0/0x0030FD30` with contact side byte;
the effect semantics of those two entries are not assigned here.

The doll retains its borrowed prepared-node entry at `+0x170`. Active updates
copy its position to the model, contact shapes, and optional debris with
component offsets `-100/+100` for the contact position. The parser's initial
non-node contact offset is `-150/+100`. The object does not own or free the
scene's node array. Its elapsed counter changes by one per eligible object
invocation; no seconds conversion is established by this method.

Derived virtual destructors are `0x00813700` (doll), `0x008137E0` (`うっきー君`),
`0x00813A80` (lantern), and `0x008139A0` (wind bell). Each resets derived
state, installs the base break vtable, and calls base cleanup `0x007D8D90`.
That cleanup destroys shape storage `+0x130`, optional debris/controller
`+0x90`, and unregisters both receivers. The destructor then destroys embedded
shape `+0xE0` and receivers `+0xC0/+0xA0`, calls common model cleanup
`0x007D8AB0`, and optionally frees itself. This proves their local derived
teardown; it does not free the borrowed node entry or stage archive, nor prove
all scene destruction entry paths.

## Parser-format differences

These comparisons establish concrete format differences. NA2 rotating-sky
parser resident `0x003986F0` takes resource/node names in tokens 0/1, float
scale in 2, initial integer angle in 3 (`-1` selects the random-angle path),
and speed in 4. NUN3 `0x38A` takes its animation from record `+8` and speed
from token 10. NA2 glare parser `0x00398C40` packs tokens 0..3 and 5..7 into
the effect's two color words, reads mode from 8, and reads floats from 4/9;
NUN3 `0x392` uses already-packed integer tokens instead.

NA2 wire parser live `0x006C84D0` takes both endpoints and texture from tokens
0/1/2. Its fifteen-interior-node setup and node-array initialization parallel
NUN3's wire, but NUN3 places endpoints in the fixed record and texture in token 6.
NA2's suspension-bridge token order, documented in
[Stages](stages.md#animated-and-breakable-background-evidence), differs from
NUN3's segment/model/endpoint positions. NA2 `ccBgTransObject` directly uses
token 4 as its radius and eases based on fighter distance; NUN3 `0x601` uses
token 8 plus 150 and collision-contact scalars. These are related scene
behaviors with different inputs and implementations, not interchangeable
record formats.

## Correspondence with NA2 records

**Confirmed:** every one of NUN3 `S01..S20` contains all node and resource
names that NA2's
[mandatory records](stages.md#resident-generic-factories-and-mandatory-records)
and [line builders](stages.md#line-construction) request: `DMY_pp1_010`,
`DMY_pp2_010`, both `DMY_line_010`/`DMY_line_020` pairs, the four
`DMY_linemin/max` nodes, `LGT_dis_0`, `ANM_stalig00`, `BLT_bg`, `BLT_obj`, and
`DMY_{f,b}_cl_N_{nor,ewr,mov}` lines using the same naming scheme.

**Supported:** NUN3 categories map onto the NA2
[factories](stages.md#bin_bgdata-records-and-factory-dispatch) by shared node
names, resource names, and token shapes:

| NUN3 record | NA2 record |
| --- | --- |
| category 0 archive and `BLT_bg`/`BLT_obj` | slot path table and factory 31 |
| category 1 fog | factory 10 (RGB plus four numbers; token order and units differ) |
| category 10 players | factories 33/34 |
| category 11 line nodes, token 5 | factories `0x23`/`0x24` (node count) |
| category 14 `cl` lines, token 5 | factories `0x25`/`0x26` (line count) |
| category 13 lighting | factory 18 `ccBgLightDistant` |
| rotating sky, glare | factories 8 `ccBgRotateSky`, 11 `ccBgGlareFilter` |
| swaying tree / grass, flags, wind bell, falling leaves | factories 5, 7, 6, 30, 108 |
| `0x601` transparent pillars | factory 40 `ccBgTransObject` |
| `0x81C` training doll, `0x8xx` breakables | factories 41 `ccBgBreakDollBattle`, 50/78/80/102 |
| electric wire, rowing boat, mangrove, suspension bridge, footprints, crane truck | factories 43, 82, 95, 68, 93, 83 |

The line-count correspondence is exact where the stage is shared: NUN3
index 8 (Tanzaku) has 14/14 `DMY_line` nodes and 8/9 `cl` lines, and NA2 `S24`
has 7/7 second-family records and 8/9 first-family records; NUN3 index 2
(Forest of Death) has 10/10 and 5/5, and NA2 `S09` has 5/5/5/5.
NUN3 parser comparisons above establish several shared responsibilities and
specific input differences. Other subtype correspondences in this table
remain supported by labels/resources; their complete token formats and
update-state equivalence have not been established.
