# Translation importer knowledge

This document owns durable evidence and negative results behind the current
translation-importer contract. The current schema, inputs, output, and failure
behavior remain in the [feature document](../../features/localization/translation_importer.md).

## Mapping admission and evidence

Executable mappings are admitted only when their clean NA2 source, official
NUN5 donor, and display ownership are established. `display_context` identifies
the concrete screen and field. `display_basis` distinguishes rows exercised by
an exact maintained E2E suite (`e2e:<suite-name>`), directly seen rows without
maintained-suite coverage, hidden members inferred from a proven shared table,
and character-family rows established through matching structures.

An evidence-scoped rebuild removed unvisited alternate-mode, inventory,
generic-choice, and unmatched voice-title rows instead of treating historical
coverage as proof. Clean Japanese bytes remain authoritative when no verified
official source or display location exists.

The completed Collection batch records every proven owning suite when a row is
visible in more than one suite. Multiple `display_basis` entries use `|`, and
the importer counts each entry independently. Coverage counts can therefore
overlap without hiding a shared row from any suite. Generic shared strings such
as modal `Yes` and `No` remain `seen:` unless the exact table instance used by
Collection is proven.

| Display basis | Covered rows | Proven family |
| --- | ---: | --- |
| `e2e:collection/characters` | 31 | 30 shared common names plus the secondary Granny Chiyo plaque field |
| `e2e:collection/figures` | 132 | Common Figure names and animation titles, plus Diorama titles |
| `e2e:collection/misc` | 49 | Simulation, Movie, Music, quit, and locked-title rows |
| `e2e:collection/opponents` | 44 | Opponents-only character names and selector label |
| `e2e:collection/ultimates` | 161 | Collection-owned Ultimate Jutsu title table |
| `e2e:collection/voice` | 153 | Collection-owned Voice title table and aliases |

## Structural mapping families

Character Command Chart names are selected through 74 matching executable
record arrays. Each record is `0x54` bytes and stores its displayed-name pointer
at `+0x08`; a row is mapped only when the corresponding NA2 and NUN5 record
indices both identify nonblank text.

Ultimate and character-specific Jutsu names use a separate `0x14`-byte record.
Its first word is the localized-name pointer and the remaining four metadata
words identify homologous records across NA2 and NUN5. Matching those metadata
words is the evidence boundary; string order alone is insufficient. When a
record-selected NUN5 name contains decorative color tags but a separate plain
official copy exists, the plain copy is used for a plain NA2 slot.

### Collection display titles are not moveset names

Collection Figure animation titles form a separate executable namespace from
character moveset and Jutsu names. Similar English wording across those
namespaces is not evidence that they share a donor. In particular, an article,
noun, or qualifier present in the Collection title may be absent from a
moveset string, or vice versa.

The Collection Figure table interleaves stable animation identifiers such as
`if...anm#` with its display strings in NA2 `ETC.BIN`. NUN5 retains the same
identifier sequence and stores the official Collection strings in
`TEXTENG.BIN`. The stable join is therefore:

1. locate the identifier owning the NA2 Collection slot;
2. find that exact identifier in the NUN5 Collection sequence;
3. use the display string selected by that NUN5 record, including its exact
   NUN5 offset;
4. use a shared NUN5 string only when the Collection record itself selects it.

A global text search or suffix match is not a valid join. That rejected method
misidentified six Figure rows as `Tool User`, `Pressure`, `Sharp Kick`,
`Samehada`, `Favorite`, and `Heaven Kick`. Their Collection records instead
select `Ninja Tool User` at `NUN5_TEXTENG@0x3310`, `Coercion` at `0x3728`,
`A Sharp Kick` at `0x3908`, `Giant Sword: Samehada` at `0x3980`,
`My Favorite` at `0x3A90`, and `Heaven Kick of Pain` at `0x3B90`.

The converse rule applies to future moveset work: do not import a Collection
Figure offset merely because its wording resembles a move name. Establish the
moveset record family and its own homologous NUN5 selection first.

Collection Characters uses another Collection-owned title table for the
Ultimate Jutsu names shown beside the opponent list. It is separate from the
boot-ELF moveset records even when both records select identical English text.
Paired Opponents capture `0001` proves the first displayed triple through the
instantiated screen records:

| Title | NA2 ETC source | NA2 live record | NUN5 live record | Exact NUN5 donor |
| --- | --- | --- | --- | --- |
| `8 Trigrams 64 Palms` | `0x286C0` | `(0x6E,0x3E8,0x0F,0x006DC5C0)` at `0x00CE0208` | `(0x6E,0x3E8,0x0F,0x008F7DF0)` at `0x00C13588` | `TEXTENG.BIN` `0x40F0` |
| `8 Trigrams 361 Style` | `0x29470` | `(0x6F,0x7D0,0x10,0x006DD370)` at `0x00CE0218` | `(0x6F,0x7D0,0x10,0x008F8730)` at `0x00C13598` | `TEXTENG.BIN` `0x4A30` |
| `Last Resort: Eight Gates Assault` | `0x294B0` | `(0x70,0xBB8,0x11,0x006DD3B0)` at `0x00CE0228` | `(0x70,0xBB8,0x11,0x008F8750)` at `0x00C135A8` | `TEXTENG.BIN` `0x4A50` |

The corresponding immutable tables use 16-byte records with the string
pointer first and the same three metadata words. The screen instance rotates
the pointer to the final word without changing the metadata. This exact
metadata sequence, record order, and instantiated Collection ownership are the
join; the matching English wording is only the result.

The complete Collection Ultimate table is now established rather than inferred
from those first three live records. NA2 stores 168 records at `ETC.BIN`
`0x29F7C`; NUN5 stores the corresponding 168 records at `TEXTENG.BIN`
`0x2BBBC`. Records `0..166` have identical metadata triples in the same order,
so each NUN5 record's pointer is the canonical donor selection for the NA2
record at that index. Record `167` is the terminal `Crystal Ice Mirrors` entry:
NA2 retains `(0x39,0x04,0x006D8E98)` while NUN5 uses terminal metadata
`(0xA8,0,0)`, but both terminal records select that same title and their table
position is unambiguous.

Three valid NUN5 Collection records point into `SLES_556.05` rather than
`TEXTENG.BIN`: `IQ 200` at `NUN5_SLES@0x5140E8`, `Art` at `0x5140F0`, and
`Uwabami` at `0x5140F8`. The donor namespace must therefore be derived from the
selected pointer's address range, not assumed from the table's containing
file. An exhaustive comparison of the 168 selected pointers found 15 prior
lookalike/duplicate selections; those rows now use the exact record-selected
offsets. Exact selection includes otherwise invisible trailing spaces when the
Collection record points to them.

NUN5 uses paired byte-`0x40` delimiters as quotation markup in English display
strings. The raw records select `@White Picture@` at `TEXTENG.BIN` `0x3FF0`,
`@Dragon@` at `0x4030`, `@Wild Dog@` at `0xECD0`, `@Petal Shower@` at
`0xEF10`, and `@Divinity@` at `0xEF60`; paired Collection and Command Chart
captures render those spans as quotation marks. The accepted NA2 atlas renders
byte `0x40` literally, so the translation importer decodes every balanced
NUN5 `@...@` span centrally before transforms or placement. Canonical rows
retain the exact raw donor and offset, keep `replacement` blank, and cannot
declare a row-level override for this family.

Command Chart move title T1486 is a separate exact-record edge case: NUN5
`TEXTENG.BIN` `0xB9A0` stores `Air Strike Palm` followed by byte `0x0A` and
then NUL. That terminal LF belongs to the selected donor record and remains in
the canonical mapping. NUN5's one-line title consumer ignores it after the
visible text; NA2 parity is therefore owned by the Command Chart draw adapter,
not by a translation override or altered donor offset.

The separate NA2 boot-ELF mappings beginning at `SLPS_258.37` `0x4AD3D0`
belong to 20-byte moveset records: one localized-name pointer plus four
metadata words. Those records must continue to be joined to their own NUN5
homologs. A Collection donor must never be propagated into that family merely
because the current text is equal, and the reverse is equally invalid.

`Charge! Konohamaru Ninja Squad!` demonstrates why that join must include all
four metadata words. The NA2 record selecting `SLPS_258.37` `0x4ADCD0` begins
at `0x4AF380` and has metadata bytes
`43 00 01 00 03 01 48 00 FF FF FF FF 23 00 00 00`. The identical tuple selects
the NUN5 record at `TEXTENG.BIN` `0x2CF50`, whose pointer resolves to the exact
donor at `0x112D0`:
`<BLACK>Charge! Konohamaru <color0808C0>Ninja Squad<BLACK>!`. The plain copy at
`0x4D30` is selected by the separate Collection family and is not a valid
moveset donor. Clean NA2 binaries contain native `<BLACK>` tokens, so the
importer preserves that named token when a target slot has no existing black
form; a target that already uses `<color000000>` still determines that local
equivalent.

The same join separates Temari's moveset title from its Collection copy. The
NA2 record at `SLPS_258.37` `0x4AF100` selects source slot `0x4AD970` and has
metadata bytes `2F 00 03 00 03 02 2B 00 FF FF FF FF 2D 00 00 00`. Its exact
NUN5 homolog at `TEXTENG.BIN` `0x2CCD0` selects
`<BLACK>Cyclone Scythe <color0808C0>Jutsu` at `0x11280`; Collection instead
selects the plain copy at `0x4F30`. The terminal red span therefore belongs to
the moveset record and must not be erased by the similar Collection title.

The same namespace rule applies to Collection Music. Its rows preserve their
own sequence across the homologous Collection tables. For example, the
Collection record for 「巨悪現る」 selects the complete official string
`A Great Evil Appears` at `NUN5_TEXTENG@0x2F80`; `0x2F82` is merely the
interior substring `Great Evil Appears`, not a separately selected donor.
Interior substring hits are therefore invalid offsets even when their visible
text appears plausible.

Collection Voice is a third Collection-owned namespace. NA2 stores 154
12-byte records at `ETC.BIN` `0x2CF08`; NUN5 stores the homologous records at
`TEXTENG.BIN` `0x2A048`. Every record has the form
`(localized pointer, voice ID, type)`, and all 154 `(voice ID, type)` pairs
match in the same order. The exact donor for a Voice title is the pointer
selected by the NUN5 record at that matching index, including pointers into
`SLES_556.05`.

This join found thirteen similarity-selected offsets that bypassed the Voice
table: `Passion`, `Determination`, `The Joy of Growth`, `Me Myself`,
`Youth at Full Power!`, `The Mystery Ninja`, `Gratitude`, `A Strong Man`,
`The Third Kazekage`, `Duel Start`, `The Fifth Hokage`, `No Worries`, and
`Admiration`. The first is visibly unchanged but still requires its exact
record-selected SLES source. The remaining twelve explain the paired-screen
wording and punctuation mismatches.

Five shared-slot situations occur in the Voice table. Three NA2 source strings
occur in more than one Voice record: one duplicate selects the same NUN5 text
both times, while `The Match Begins` versus `Duel Start` and `A Cinch` versus
`No Worries` require Voice-record-specific aliases. Two additional Voice
records share Japanese storage with another Collection namespace: Figure
`Myself` versus Voice `Me Myself`, and Ultimate `Youth at Full Power!!` versus
Voice `Youth at Full Power!`. The four differing cases cannot be represented
by overwriting the shared Japanese slot globally. The canonical mappings
instead keep one translation inline and link the alternate exact donor only
from its owning 12-byte Voice record.
Pointer-specific aliases are a placement consequence of the proven record
join; their English still comes exclusively from `mappings.tsv` and exact
NUN5 offsets.

Collection character plaques demonstrate the same rule outside Voice. NA2's
Japanese `Granny Chiyo` slot at `ETC.BIN` `0x251E0` is shared by four record
families, but the Characters Collection pointer field at `0x25A68` corresponds
to NUN5's secondary localized-roster field. NUN5 selects `Granny Chiyo ` at
`TEXTENG.BIN` `0x518` there, while the primary field used by the other records
selects unpadded `Granny Chiyo` at `0x508`. Mapping only pointer field `0x25A68`
to the exact secondary donor preserves both official forms without a renderer
string test or a global overwrite of the shared NA2 slot.

## Packed message blocks

Some dialogs contain consecutive NUL-terminated fragments inside one fixed
region. Treating each fragment as an independent slot zero-filled the remainder
of the Japanese fragment and could insert an early empty string that hid later
parts. `sequence` mappings therefore write the selected official parts
consecutively, terminate each part, add one final NUL, and zero-fill only the
unused tail of the verified whole block. They never resize the target or write
outside that block.

## Placement and semantic guards

- A fitting slot is written inline.
- An overflowing slot is linked externally only when that same mapping owns
  validated pointer references; otherwise compilation fails.
- Sequence mappings must fit their declared block.
- Placeholder donor text such as `unknown`, `placeholder`, or `dummy` cannot
  overwrite identifier-like NA2 data.
- Source, donor, references, transforms, override, and prefix stay on the same
  stable mapping row. Generated logs derive their reasons from its stable ID.
- The official donor is executable by default. A replacement is present only
  for an intentional user-owned override.
- The project-title policy is hash- and coverage-pinned and replaces only its
  declared official donor token with `Narutimate Accel v2.28`.

## Content and layout boundary

Canonical mappings preserve official wording. They do not insert authored line
breaks or shorten correct text merely to compensate for a renderer defect.
Collection Movie line breaks added to four exact NUN5 titles were rejected and
removed; wrapping belongs to the Font caller path. Likewise, the correct
`Flying Thunder God Jutsu` mapping remains unchanged even if a particular
Collection panel needs wrapping.

Generic modal labels remain exact official `No` and `Yes`. A global uppercase
transform was rejected because those slots are shared and did not own the
startup-specific presentation that motivated the experiment. Graphical labels,
controller prompts, emulator chrome, placement, and atlas behavior remain
outside the translation importer.

## Durable resolved mappings

- Collection's confirmed selector label uses official `Opponent`; its paired
  screen established that the missing mapping, not layout, caused the Japanese
  label.
- The Mode Select return confirmation uses official
  `Return to Title Screen?`; it is distinct from Save/Load and Character Select
  prompts with different sources and capitalization.
- Temari's Collection voice title maps to official `Silent Confidence`, proven
  by the matching NUN5 screen and `TEXTENG.BIN` source.
- Plain Kankuro maps to `Kankuro`, not `Kankuro (Classic)`; structurally matched
  character families must not collapse distinct variants.
- Memory-card notices use packed sequence mappings so every official fragment
  remains reachable without changing file size.

### Battle and Practice quit confirmations

Paired Battle and Practice states for both return destinations prove that the
BTL modal assembles its body from four independently selected strings:

`mode head + connective + destination + terminator`

The mode head is T63 (`Battle`) or T64 (`Practice`), the shared connective is
T66, and T67 terminates the question. The destination is not the T68/T69 pause
menu label. The modal selects separate short BTL slots at `0x208DA0`
(`Character Select`) and `0x208DC0` (`Game Mode Select`), represented by T2201
and T2202. T63/T64 must resolve only through the donor's `%1`; including the
text before `%2` duplicates T66 at runtime. This split produces all four NUN5
sentences without storing newlines in canonical mappings; draw-time wrapping
remains renderer-owned.

Version-by-version counts, generated hashes, old runtime checklists, and
superseded issue logs remain in Git history rather than canonical
documentation.
