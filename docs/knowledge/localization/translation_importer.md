# NA2 and NUN5 text correspondence

Retail NA2 (`SLPS-25837`) text ownership and its official NUN5 English
counterparts: the executable records that select displayed strings, the record
families that join the two games, and the storage of packed messages.

## Research coverage

- **Assigned scope:** retail NA2 source slots, the executable record families
  and pointer fields that select displayed text, their homologous official NUN5
  records and English strings, and packed-message storage.
- **Exploration depth:** the Battle and Practice Settings, pause and quit-modal,
  Character Select, Ninja Song, Collection, Jutsu-selector, and Command Chart
  record paths were traced through the retail NA2 and NUN5 executables and data
  files. Memory-card source blocks, pointer entries, and English counterparts
  were inspected; supplied screenshots cover the format and creation failures
  and create-data confirmation. Other error and startup strings have static
  coverage only.
- **Confirmed coverage:** the documented menu, Practice, Ninja Song, Collection,
  Jutsu, Command Chart, packed-message, confirmation, and memory-card
  failure-message relationships are established.
- **Unresolved or untested:** records whose selecting executable path was not
  traced, and records without an exact source, homologous-record, or
  displayed-owner basis.
- **Deliberate exclusions and overlap:** memory-card message layout belongs to
  [Confirmation Font layouts](font/screen_layouts/confirmations.md#message-boundaries);
  Collection graphics and prompts belong to
  [Collection UI draw-path analysis](ui/collection.md).
- **Evidence limitations:** membership in a shared table or matching visible
  text does not prove that a particular executable record is selected.

## Shared modal and Character Select strings

Character Select reads its player-control option strings from the boot-ELF
table at `0x4B4150..0x4B41FF` and its return prompt from `0x4B4220`. NUN5's
English return prompt is `Return to Game Mode Screen?` at `TEXTENG.BIN`
`0x1DF0`.

The generic Yes/No modal uses boot-ELF `Yes` at `0x503110` and `No` at
`0x503118`. Collection's confirmation instead selects runtime slots
`0x00604568` and `0x00604570`, which are `SLPS_258.37` file offsets
`0x504668` (`No`) and `0x504670` (`Yes`). NUN5's English choices are `No` at
`SLES_556.05` `0x513E4C` and `Yes` at `0x513E50`.

The Mode Select return confirmation at boot-ELF `0x4B1E00` corresponds to NUN5
`Return to Title Screen?` at `TEXTENG.BIN` `0x1C90`. It is distinct from the
Save/Load and Character Select prompts, which have different sources and
capitalization.

## Settings string references

Battle Settings draw helper Ghidra `FUN_008801E0` loads labels through
runtime table `0x008BE160` (BTL file `0x20A260`) and values through an
indexed table of string-pointer arrays. In row order, the label array selects
the strings whose NUN5 English counterparts are `Time`, `Difficulty`, `Items`,
`Chakra`, `Ultimate Jutsu`, and `Handicap`. The defaults message is at BTL
`0x20A680`; NUN5 stores `Battle Settings returned to defaults.` at
`TEXTENG.BIN` `0xF260`.

Practice Settings draw `FUN_00882250` uses runtime label table `0x008BE6C0`
(file `0x20A7C0`) and value-array table `0x008BF380` (file `0x20B480`).
Label entries 10-16 at `0x20A7E8..0x20A800` select the seven displayed
Practice Settings labels in row order; value entries 10-16 at
`0x20B4A8..0x20B4C0` resolve their row-local value arrays. The value table
selects both BTL-owned arrays and resident ELF arrays, including the three
OFF/ON pairs at ELF file `0x505BC0`, `0x505BD0`, and `0x505BD8`. Rows that
display the same `Normal` text therefore select separate records.

The Linked Mode selector in resident `FUN_003B8F40` reads the two pointer
words at runtime `0x00604810` and `0x00604814`; the latter is ELF file
`0x504914` and selects the Auto string at file `0x504908`. These pointer
fields are distinct from the source text slots themselves. Raw overlay
offsets include the header; preserved Ghidra locations follow the
[shared address conventions](../game/files/file_identities.md#address-conventions).

### Battle and Practice quit confirmations

Paired Battle and Practice states for both return destinations show that the
BTL modal assembles its body from four independently selected strings:

`mode head + connective + destination + terminator`

The mode head is the Battle string at BTL `0x208CF0` or the Practice string at
`0x208D10`; the shared connective is at `0x208D80`, and the terminator at
`0x208DF0` ends the question. The destination is not the pause-menu label. The
modal selects separate short BTL slots at `0x208DA0` (`Character Select`) and
`0x208DC0` (`Game Mode Select`).

NUN5 expresses the same question as one template,
`Are you sure you want to quit %1 and return to %2?` at `TEXTENG.BIN` `0xA20`,
with destination strings `Character Select` at `0xA60` and `Game Mode Select`
at `0xA80`. The modal's choices use the generic Yes/No slots above.

## Ninja Song units

The NA2 arithmetic descriptor table begins at BTL file `0x20FEE0`. The
objective-6 descriptor at `0x20FF1C` selects unit index `2`; direct comparison
with NUN5 `FUN_0072E5B0` shows that the regional renderer instead resolves
localized resource selector `unit_index + 4`. The selected English text is
`timer counts` at `TEXTENG.BIN` `0x10538`, while NA2's live unit pointer table
selects the corresponding source slot at BTL `0x1E5BC0` through index `3`.
Objective 9's descriptor unit index `4` has no visible NUN5 unit.

## Command Chart and Jutsu records

Character Command Chart names are selected through 74 matching executable
record arrays. Each record is `0x54` bytes and stores its displayed-name pointer
at `+0x08`. Corresponding NA2 and NUN5 record indices identify homologous
records.

Ultimate and character-specific Jutsu names use a separate `0x14`-byte record
family, beginning in NA2 at `SLPS_258.37` `0x4AD3D0`. Its first word is the
localized-name pointer and the remaining four metadata words identify
homologous records across NA2 and NUN5. Matching all four metadata words
identifies the homolog; string order alone does not.

### Jutsu selector titles

The Jutsus selector does not consume the separate `0x14`-byte Ultimate/Jutsu
family despite the screen name. NA2 row compositor `FUN_006BCB30` resolves its
title through `FUN_00885F00` and the boot-ELF accessor at Ghidra
`0x00307C80`. That accessor indexes the pointer table at Ghidra `0x005A2320`,
loads a `0x54`-byte Command Chart record, and reads its displayed-name pointer
at `+0x08`. The NUN5 homolog follows `FUN_006CFE30` through `FUN_008A2E60`,
accessor `0x00312630`, and `FUN_00259290`. This trace distinguishes the
selector from both Collection strings and the metadata-owned `0x14` family.

The comparison used the retail NA2 resident ELF, NUN5 `SLES_556.05`, and NUN5
`PRG/TEXTENG.BIN` identified in
[Standard game file identities](../game/files/file_identities.md).
For each displayed row, bytes `+0x0C..+0x53` of the NA2 record identify its
NUN5 homolog independently of the localized pointer. `1000 Autumn Shower` is
the sole duplicate: two NA2 records share its exact source slot and match two
NUN5 records, and both NUN5 records resolve the same English string.

NUN5's English table root is at raw `TEXTENG.BIN` offset `0xF090`. Following
each homolog's `(group,index)` selector through that root gives the English
string below. Source slots and record addresses are raw executable file
offsets; English-string addresses are raw `TEXTENG.BIN` offsets.

| NUN5 English title | NA2 source | NA2 `0x54` record(s) | NUN5 `0x54` record(s) | NUN5 selector(s) | NUN5 string |
| --- | ---: | ---: | ---: | --- | ---: |
| `Temple of Nirvana Technique` | `0x49DE80` | `0x49DFAC` | `0x4A7FEC` | `31:3` | `0x7960` |
| `Water Style: Water Dragon Jutsu` | `0x337080` | `0x3372A4` | `0x349644` | `11:1` | `0x5140` |
| `Super Healing Medicine` | `0x33C0E0` | `0x33C37C` | `0x34E53C` | `12:3` | `0x64B0` |
| `Sacred Dance Shuriken` | `0x3413A0` | `0x3416DC` | `0x35363C` | `13:3` | `0x6700` |
| `Ninja Wolfsbane` | `0x34B9F0` | `0x34BCBC` | `0x35D8BC` | `15:3` | `0x6B00` |
| `Tunneling Fang ` | `0x351100` | `0x3513AC` | `0x362DDC` | `16:3` | `0x6D30` |
| `Earth Style: Sphere of Graves` | `0x36C220` | `0x36C4BC` | `0x37D44C` | `34:3` | `0x79C0` |
| `Giant Spider Drop` | `0x371200` | `0x37150C` | `0x38226C` | `35:3` | `0x7BA0` |
| `Explosive Destruction Formation` | `0x37B3C0` | `0x37B70C` | `0x38BFBC` | `37:3` | `0x8090` |
| `Water Style: Water Wall` | `0x39A980` | `0x39AC1C` | `0x3AAB3C` | `43:3` | `0x8BE0` |
| `Marauding Snakes` | `0x39FF80` | `0x3A02AC` | `0x3AFF7C` | `46:3` | `0x8DF0` |
| `Earth Style: Gushing Rock Mountain Cannonball` | `0x3C0630` | `0x3C086C` | `0x3CFA6C` | `52:3` | `0x9BA0` |
| `Naruto Uzumaki Combo Attack` | `0x3D9C40` | `0x3D9EA4` | `0x3E84D4` | `57:1` | `0xA6B0` |
| `Great Ball Rasengan` | `0x3D9C60` | `0x3D9F4C` | `0x3E857C` | `57:3` | `0x3F00` |
| `Killer Spring` | `0x3DF1C0` | `0x3DF47C` | `0x3ED8AC` | `58:3` | `0xA918` |
| `1000 Autumn Shower` | `0x3F5C30` | `0x3F5F1C` / `0x4462EC` | `0x403B1C` / `0x4520AC` | `62:3` / `77:3` | `0xB1E0` |
| `8 Trigrams Sky Palm` | `0x406B70` | `0x406DEC` | `0x4142EC` | `65:3` | `0x3230` |
| `Concealed Kunai Blast` | `0x40C650` | `0x40C9FC` | `0x419C1C` | `66:3` | `0xBB20` |
| `Explosive Style Shadow Conceal: Improvement` | `0x418A00` | `0x418C4C` | `0x425ADC` | `68:3` | `0xC070` |
| `Night Phoenix` | `0x41F0E0` | `0x41F3FC` | `0x42C04C` | `69:3` | `0xC238` |
| `Lightning Blade` | `0x424B40` | `0x424DEC` | `0x43186C` | `70:3` | `0xC4C0` |
| `Fire Style: Fire Ball Jutsu` | `0x42A0F0` | `0x42A39C` | `0x436C3C` | `71:3` | `0xC690` |
| `Water Style: Water Shark Shotgun Jutsu` | `0x42F5D0` | `0x42F8BC` | `0x43BF3C` | `72:3` | `0xC890` |
| `Beautiful Seasons` | `0x463D00` | `0x463F1C` | `0x46F32C` | `82:3` | `0xDB50` |
| `Heaven Defending Kick` | `0x46E6D0` | `0x46E9AC` | `0x4799FC` | `84:3` | `0xDF20` |
| `Ninja Art: Poison Fog` | `0x474140` | `0x47440C` | `0x47F25C` | `85:3` | `0xE160` |

### Moveset Ultimate and Jutsu titles

The Ultimate/Jutsu titles shown in the third slot of moveset specials grids
come from the `0x14`-byte family. The Granny Chiyo (Taijutsu) `0x4E`
unique-mode grid selects its ordinary moves from her alternate ordinary-move
block. An identical Collection title is a different executable record.

`Charge! Konohamaru Ninja Squad!` shows why the join needs all four metadata
words. The NA2 record selecting `SLPS_258.37` `0x4ADCD0` begins at `0x4AF380`
and has metadata bytes
`43 00 01 00 03 01 48 00 FF FF FF FF 23 00 00 00`. The identical tuple selects
the NUN5 record at `TEXTENG.BIN` `0x2CF50`, whose pointer resolves to
`<BLACK>Charge! Konohamaru <color0808C0>Ninja Squad<BLACK>!` at `0x112D0`. The
plain copy at `0x4D30` is selected by the separate Collection family. Retail
NA2 binaries contain native `<BLACK>` tokens.

The same join separates Temari's moveset title from its Collection copy. The
NA2 record at `SLPS_258.37` `0x4AF100` selects source slot `0x4AD970` and has
metadata bytes `2F 00 03 00 03 02 2B 00 FF FF FF FF 2D 00 00 00`. Its NUN5
homolog at `TEXTENG.BIN` `0x2CCD0` selects
`<BLACK>Cyclone Scythe <color0808C0>Jutsu` at `0x11280`; Collection instead
selects the plain copy at `0x4F30`. The terminal red span belongs to the
moveset record.

### Command Chart relationship strings

The Command Chart relationship selector is the pointer table at `BTL.BIN`
`0x2092D0`. Its indices 16-17 select `Charge-weak` and `Charge-strong`. The
displayed Command Chart `Charge` qualifier (BTL `0x2090B0`, NUN5
`SLES_556.05` `0x513EB0`) is a different record from the Practice
`Charge Chakra` title (BTL `0x2097D0`, NUN5 standalone `TEXTENG.BIN` `0xFB8`).
Likewise, Command Chart `While jumping` (BTL `0x209030`) is a different record
from the `(while jumping)` help string (BTL `0x209330`).

Command Chart move title `Air Strike Palm` (NA2 source `SLPS_258.37`
`0x406C30`) has a NUN5 record that selects `TEXTENG.BIN` `0xB9A0`, which stores
the visible text followed by byte `0x0A` and then NUL. NUN5's one-line title
consumer ignores that terminal LF after the visible text.

## Collection records

### Master roster and character plaques

NA2's Collection master roster is a 75-record, 12-byte table at `ETC.BIN`
`0x25948`: 74 character entries followed by the Diorama selector entry, whose
string is at `ETC.BIN` `0x25928`. Direct caller analysis establishes that every Collection
character plaque, including the common Figurine viewer, loads this master
table. The visible Diorama grid label comes from `HOME.CCS` artwork rather than
that selector string, and the short character-grid labels are also texture
artwork.

NA2's Japanese `Granny Chiyo` slot at `ETC.BIN` `0x251E0` is shared by several
record families, but the Collection plaque paths select it through
master-roster pointer field `0x25A68`. NUN5 selects `Granny Chiyo ` with a
terminal space at `TEXTENG.BIN` `0x518` there, while its primary unpadded
`Granny Chiyo` is at `0x508`.

The locked Movie placeholder is the NA2 string at `ETC.BIN` `0x2E738`; NUN5's
counterpart is `???` at `SLES_556.05` `0x513E48`.

### Collection Figure titles

Collection Figure animation titles form a separate executable namespace from
character moveset and Jutsu names. Similar English wording across those
namespaces does not mean they share a string. An article, noun, or qualifier
present in the Collection title may be absent from a moveset string, or vice
versa.

The Collection Figure table interleaves stable animation identifiers such as
`if...anm#` with its display strings in NA2 `ETC.BIN`. NUN5 retains the same
identifier sequence and stores the official Collection strings in
`TEXTENG.BIN`. The identifier owning an NA2 Collection slot therefore locates
the matching NUN5 Collection record, and that record selects the English
string.

For example, the Collection records for six Figure titles select
`Ninja Tool User` at `TEXTENG.BIN` `0x3310`, `Coercion` at `0x3728`,
`A Sharp Kick` at `0x3908`, `Giant Sword: Samehada` at `0x3980`,
`My Favorite` at `0x3A90`, and `Heaven Kick of Pain` at `0x3B90`. Shorter
lookalike strings such as `Tool User`, `Pressure`, `Sharp Kick`, `Samehada`,
`Favorite`, and `Heaven Kick` exist elsewhere but are not selected by these
records.

### Collection Ultimate titles

Collection Characters uses another Collection-owned title table for the
Ultimate Jutsu names shown beside the opponent list. It is separate from the
boot-ELF moveset records even when both records select identical English text.
The paired Opponents capture shows the first displayed triple through the
instantiated screen records:

| Title | NA2 ETC source | NA2 live record | NUN5 live record | NUN5 string |
| --- | --- | --- | --- | --- |
| `8 Trigrams 64 Palms` | `0x286C0` | `(0x6E,0x3E8,0x0F,0x006DC5C0)` at `0x00CE0208` | `(0x6E,0x3E8,0x0F,0x008F7DF0)` at `0x00C13588` | `TEXTENG.BIN` `0x40F0` |
| `8 Trigrams 361 Style` | `0x29470` | `(0x6F,0x7D0,0x10,0x006DD370)` at `0x00CE0218` | `(0x6F,0x7D0,0x10,0x008F8730)` at `0x00C13598` | `TEXTENG.BIN` `0x4A30` |
| `Last Resort: Eight Gates Assault` | `0x294B0` | `(0x70,0xBB8,0x11,0x006DD3B0)` at `0x00CE0228` | `(0x70,0xBB8,0x11,0x008F8750)` at `0x00C135A8` | `TEXTENG.BIN` `0x4A50` |

The corresponding immutable tables use 16-byte records with the string
pointer first and the same three metadata words. The screen instance rotates
the pointer to the final word without changing the metadata. The metadata
sequence, record order, and instantiated Collection ownership identify the
homolog; the matching English wording is only the result.

The complete Collection Ultimate table is established beyond those first three
live records. NA2 stores 168 records at `ETC.BIN` `0x29F7C`; NUN5 stores the
corresponding 168 records at `TEXTENG.BIN` `0x2BBBC`. Records `0..166` have
identical metadata triples in the same order, so each NUN5 record's pointer
selects the official English title for the NA2 record at that index. Record
`167` is the terminal `Crystal Ice Mirrors` entry: NA2 retains
`(0x39,0x04,0x006D8E98)` while NUN5 uses terminal metadata `(0xA8,0,0)`, but
both terminal records select that same title and their table position is
unambiguous.

Three valid NUN5 Collection records point into `SLES_556.05` rather than
`TEXTENG.BIN`: `IQ 200` at `SLES_556.05` `0x5140E8`, `Art` at `0x5140F0`, and
`Uwabami` at `0x5140F8`. Some selected strings carry otherwise invisible
trailing spaces.

### Collection Music and Voice titles

Collection Music rows keep their own sequence across the homologous Collection
tables. For example, the Collection record for 「巨悪現る」 selects the complete
official string `A Great Evil Appears` at `TEXTENG.BIN` `0x2F80`; `0x2F82` is
only the interior substring `Great Evil Appears`, not a separately selected
string.

Collection Voice is a third Collection-owned namespace. NA2 stores 154
12-byte records at `ETC.BIN` `0x2CF08`; NUN5 stores the homologous records at
`TEXTENG.BIN` `0x2A048`. Every record has the form
`(localized pointer, voice ID, type)`, and all 154 `(voice ID, type)` pairs
match in the same order. The NUN5 record at the matching index selects the
English Voice title, including pointers into `SLES_556.05`.

Three NA2 source strings occur in more than one Voice record. One duplicate
selects the same NUN5 text both times, while the others select different NUN5
titles: `The Match Begins` versus `Duel Start`, and `A Cinch` versus
`No Worries`. Two further Voice records share Japanese storage with another
Collection namespace: Figure `Myself` versus Voice `Me Myself`, and Ultimate
`Youth at Full Power!!` versus Voice `Youth at Full Power!`.

## NUN5 English markup

NUN5 uses paired byte-`0x40` delimiters as quotation markup in English display
strings. The raw records select `@White Picture@` at `TEXTENG.BIN` `0x3FF0`,
`@Dragon@` at `0x4030`, `@Wild Dog@` at `0xECD0`, `@Petal Shower@` at
`0xEF10`, and `@Divinity@` at `0xEF60`; NUN5's Collection and Command Chart
screens render those spans as quotation marks.

## Packed message structure

The retail loading-progress message starts at boot-ELF file `0x303E10`.
Its three consecutive source fragments occupy `0x303E10..0x303E22`,
`0x303E23..0x303E6B`, and `0x303E6C..0x303E8F`. The memory-card message
table contains one pointer to the first fragment at file `0x5030A4`, whose
value is runtime `0x00403D10`. An aligned pointer-word scan of the retail ELF,
BTL, and ETC files finds no direct pointers to the two continuation starts.

Some dialogs therefore contain consecutive NUL-terminated fragments inside one
fixed region, reached in order from the first fragment's pointer and followed
by the block terminator.

The retail repair-confirmation prompt uses the same packed form. Its two NA2
fragments start at boot-ELF file offsets `0x3044F0` and `0x30451E`, and the
message-table pointer at `0x5030F0` contains runtime address `0x004043F0` for
the first fragment. NUN5 stores the matching official English message at
`TEXTENG.BIN` `0x298C0`: `The Naruto Shippuden: Ultimate Ninja 5` and `data on
memory card (PS2)  in` form the corrupt-data statement, followed by `MEMORY
CARD slot 1 is corrupt!` and `Recover the data?`.

The surrounding retail save-error family uses the same tables. NA2's corrupt
notice at `0x304470` and load-failure notice at `0x3044B0` use pointer words
`0x5030E8` and `0x5030EC`; NUN5 supplies their English at `TEXTENG.BIN`
`0x29800` and `0x298B0`. Recovery progress occupies the consecutive NA2 slots
at `0x304550`, `0x304586`, and `0x3045CF`, reached through pointer word
`0x5030F4`, and matches NUN5 `TEXTENG.BIN` `0x29940`. The recovery-failed and
recovery-completed notices at NA2 `0x304600` and `0x304650` use pointer words
`0x5030F8` and `0x5030FC` and match NUN5 offsets `0x299E0` and `0x299F0`.

## Memory-card failure messages

NA2's format-failure message is at ELF file `0x304220` (runtime `0x00404120`),
referenced by the pointer at file `0x5030D0`. Its exact CP932 text is
`フォーマットに<ruby失敗|しっぱい>しました。`; the string and its zero padding occupy
48 bytes. NUN5's official English equivalent is `Format failed!` at
`TEXTENG.BIN` file `0x29528` (Ghidra `0x0091D1E8`).

NA2's save-data-creation failure is at ELF file `0x304360` (runtime
`0x00404260`), referenced by file `0x5030DC`. Its exact text is
`セーブ<ruby領域|りょういき>の<ruby作成|さくせい>に<ruby失敗|しっぱい>しました。` in a
96-byte padded slot. NUN5 stores `Creation of save data has failed.` at
`TEXTENG.BIN` file `0x29670` (Ghidra `0x0091D330`).

User screenshots identify both Japanese messages in the lower message panel.
Static bytes and cross-references establish the corresponding source slots and
pointers; the English bytes establish the official wording. This evidence does
not establish the cause of either operation's failure or the blank upper
dialog.

### Other memory-card messages

NA2's wrong-card-type block at ELF file `0x303A80` has two adjacent strings
within 96 bytes; it says the inserted card is not a PlayStation 2 memory card.
Its message pointer is at file `0x503084`, selected by worker status `7`.
NA2's classifier `FUN_001C20A0` returns `1` when the card-type field is neither
`0` nor `2`; worker `FUN_001E2140` turns that result into status `7`.
NUN5's classifier `FUN_001C6C10` has the same card-type branch, and worker
`FUN_001E7DF0` likewise chooses status `7`, except when worker field `+0x54`
is `2`, where it chooses status `6`.

NUN5's English message table at runtime `0x006C6890` is initialized from
fixed pointers. Instructions at `0x005E6810..0x005E682C` copy the pointer
at `0x0061480C` into status entries `5` and `6`, and the pointer at
`0x00614810` into entry `7`. Both pointers contain `0x0091CD60`, the runtime
address of `TEXTENG.BIN` file `0x29060` (Ghidra `0x0091CD20`). Getter
`FUN_003D3800` selects `table + language * 0xC0 + status * 4`.
The English message is `No memory card (PS2) is inserted in <br>MEMORY
CARD slot 1.<br>Please insert a memory card (PS2) in<br>MEMORY CARD slot 1.`
Thus the native English game shares this message between absent
and unsupported cards, although the Japanese wording distinguishes them.
Static code establishes the classification and lookup paths, and raw bytes
establish the initializer instructions and English text. This establishes the
static message selection; it does not add screen coverage for the wrong-card
condition.

NA2's card-slot selection at `0x303D50` occupies 80 bytes. NUN5's English
counterpart at `TEXTENG.BIN` `0x29230` is `Please select MEMORY CARD slot to save to.`
Ordinary load and save failures at NA2 `0x303ED0/0x304010` occupy 64 bytes
each; the corresponding NUN5 strings are `Load failed!` at `0x29320` and
`Save failed! ` at `0x29400`.

The insufficient-space/start-anyway block at NA2 `0x3047F0` contains six
fragments through `0x304955`, with zero padding through `0x304957`.
NUN5's complete counterpart is at `TEXTENG.BIN` `0x29AF0`. Both this message
and the absent-card startup message state a requirement of **103 KB** in NA2
and **102 KB** in NUN5. The ordinary lower notices and separate startup
caller are described in [confirmation layouts](font/screen_layouts/confirmations.md#message-boundaries).
These exact retail-byte comparisons establish text and storage, not complete
screen coverage.
