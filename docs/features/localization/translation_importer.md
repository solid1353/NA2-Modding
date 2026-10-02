# NA2 translation importer

This first-class `na228_builder` module imports and validates strings for
**Narutimate Accel v2.28**, based on *Naruto Shippuuden: Narutimate Accel 2*.
The internal `localization.strings` patch owns its translation-importer input
and imported-title replacement. `features.localization: "en"` includes this
patch; `"jp"` does not import translated strings.
It never writes BIN or ELF payloads. Configuration builds pass its canonical in-memory
artifact to `string_patcher`, which applies selected semantic string patches, derives
inline versus linked placement from encoded fit and pointer availability, and
compiles one shared `binary_patcher` package. There is no standalone export
command or file-backed inter-stage handoff.

Retail record ownership and the official NUN5 counterparts behind the mappings
are in [NA2 and NUN5 text correspondence](../../knowledge/localization/translation_importer.md);
how the canonical rows use that evidence is recorded under
[Mapping evidence](#mapping-evidence).

## Mapping metadata

- Canonical `mappings.tsv` rows: `2,067`
- Canonical `mappings.tsv` SHA-256: `2720E276A595D86C78BF6BC063D5328874E9C824DE8832181407C74A03EC7FA0`

The hashes above are documentation, not a second executable manifest. Git
history and the builder's configuration-resource fingerprint own content identity.
`mappings.tsv` owns the canonical executable donor translations, user
overrides, and optional pointer inventory. Normal builds import only
`mappings.tsv`. The `localization.strings` patch in
`patches/localization/localization.json` also replaces the imported
`Naruto Shippuden: Ultimate Ninja 5` title with
`na228_builder/release/release_manifest.json`'s `title`.
Its guards require nine mappings and eleven occurrences. `string_patcher` applies
this operation before deciding inline or linked placement. It is independent
of the memory-card title and save-namespace settings.

## Source and target scope

Clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

NUN5 donor references and donor text are retained in the table for review,
provenance, and executable translation. Normal builds do not read donor
binaries: the verified `donor` text in the table is the default translation.
A nonempty `mod_string` hands the row's retail string to that
[mod string](mod_strings.md) in every language, and the importer skips it.
`prefix` is a user-editable string prepended to the translation. T1933, the
Mode Select return confirmation, T1904, the Command List Rebound condition, and
T2055 and T2237, the startup memory card prompts that state NA2's 103 KB
requirement, are owned by mod strings.
T2233 uses NUN5's verified status-7 donor, which shares the absent-card
warning used by T2035. Other rows use verified donors.
T30 uses the
exact `Ultimate` donor at `NUN5_TEXTENG@0xF208` and
the validated pointer at `NA2_BTL@0x209CB4`; encoded fit therefore externalizes
it automatically.

Treat PCSX2 operator overlays and the underlying game screen as separate
evidence. Compare NA2 and NUN5 memory-card formatting and data-creation flows by
meaning rather than assuming their screen sequences correspond one-to-one. Do
not replace identifiers, placeholders, or data of uncertain display purpose
with arbitrary text.

The translation importer owns game text and its mapping and reference data.
Font owns glyph rendering and fitting; `localization.ui` owns matching graphical
assets and their placement as one selection.

## Canonical mapping table

`@builder/patches/localization/strings/mappings.tsv` is the canonical mapping
table included by the English language choice and used by normal English builds.
`display_context` is its human-readable page/filter key; rows are sorted by
that context, then by stable `id`.

The 16 columns are:

`id`, `enabled`, `display_context`, `source`, `donor`, `prefix`,
`mod_string`, `display_basis`, `source_ref`, `reference_refs`, `donor_ref`,
`mode`, `capacity`, `transform`, `arguments`, `parent_mapping_id`

### Stable IDs and enabled state

- `id` is a stable mapping identifier.
- `enabled=1` imports the row for downstream `string_patcher` composition.
- `enabled=0` retains the row without applying it.
- `mappings.tsv` is the only enabled-state source. Configuration builds never rewrite it
  or inherit flags from external state.
- Changing an enabled flag changes the canonical module input and therefore
  requires an explicit configuration-resource hash update.
- The current evidence-scoped table contains only executable rows, so all
  current rows are enabled. Unconfirmed rows are absent instead of retained as
  disabled inventory.

Canonical `mappings.tsv` contains 2,067 enabled `T#` rows, sorted by
`display_context` and numeric ID. Exact source, source reference, mode, and
capacity are guarded by the canonical row declarations. The current maintained
E2E suites validate 1,887 unique rows. The remaining 180 rows have a blank
`display_basis`: they remain executable because they are established working
mappings, but they are explicitly unvalidated. Earlier screenshot, inference,
and structural-family labels were removed because only maintained E2E execution
validates a row. Every `prefix` value is blank. The nonempty `mod_string`
rows are T1904, T1933, T2055, and T2237.
The Jutsus suite selects 26 exact Command Chart records, including T260 plus 25
records also selected by Movesets. The Menus suite selects 30 exact Battle
Settings, Pause, confirmation, and Character Select rows.

Memory-card mappings store each native state's complete message as one
sequence. When a sequence exceeds its guarded source block, the patcher links
all its fragments together and redirects the declared message pointer. Its
final empty terminator prevents traversal into unrelated payload text.
T2052 includes the create-data question. T2036/T2037 and T2218/T2219 retain
NA2's separate unformatted-card and insufficient-space steps. T2231-T2237 cover
the additional failure, card-type, slot-selection, and start-anyway messages;
see the [source and donor evidence](../../knowledge/localization/translation_importer.md#memory-card-failure-messages).
Their `display_basis` remains blank because they lack maintained E2E coverage.
Paired screenshots correct three reference-table errors: T1956 uses `Off` at
`NUN5_SLES@0x513EF8`, T1957 uses `On` at `NUN5_SLES@0x513EFC`, and T2158 uses
`Warning` at `NUN5_SLES@0x513F38`.

Six Difficulty-family rows are matched by meaning: T27 `Simple`, T1983 `Easy`,
T28 `Normal`, T1984 `Hard`, T29 `Insane`, and T50 `Difficulty`. The full T50
label links through the exact pointer at `NA2_BTL@0x20A264`. T24 reuses the
official Jump-mode help text. Paired screens correct T637 to `Hidden Leaf
Village`, T638 to `Hidden Leaf Gate`, T744 to `Faint Unease`, and T767 to
`Silent Confidence`. The paired Practice comparison corrects T1920's
displayed title to the exact `Charge Chakra` donor at
`NUN5_TEXTENG@0xFB8`; the separate Command Chart T1926 row correctly retains
`Charge` at `NUN5_SLES@0x513EB0`. T30 uses the exact `Ultimate` donor at
`NUN5_TEXTENG@0xF208`, externalized through `NA2_BTL@0x209CB4`.
Donor text remains separate from the explicit overrides described above.
NUN5 stores visible quotation spans as paired `@...@` delimiters and uses the
semantic `<iconOK>` token for the confirm icon. The importer normalizes those
conventions centrally to ASCII quotation marks and NA2's `<iconCROSS>` token
before transforms or placement and rejects row-level overrides for either
family. T2194 declares literal-percent escaping for its printf-style consumer,
and T2195-T2198 use the restored formula-symbol normalization transform.
The maintained Ninja Song suite establishes 40 exact objective, index,
numeric/status, bonus, and formula-symbol rows. The paired Movie pass adds
the locked-title placeholder. This is an evidence-scoped English table, not a
claim that uncaptured screens are covered.

Structured `<br>` transforms validate complete donor-part coverage. The
unformatted-card notice and format question share one donor while preserving
separate source states. Whole-message sequences avoid splitting a relocated
message from its continuation.

### Symbol handling

Donor symbols use the importer's existing normalization before ordinary font
rendering. `NUN5_FORMULA_SYMBOLS` preserves `*`, `=`, `%`, and maps `·` to `.`.
`®` remains literal and uses the [existing donor-font import](font.md#maintenance-and-validation).

### Modes

- `slot`: compile one replacement as a NUL-terminated string, inline when it
  fits or externally when it overflows and has validated pointer references.
- `sequence`: pack the `<NUL>`-delimited replacement fragments into one
  verified NA2 multi-string block. Overflowing sequences link as a complete
  block when their message-pointer references are declared.

Unresolved research does not belong in accepted executable `mappings.tsv`.

There is no `shorten` or `pool` mapping mode. External placement is a
`string_patcher` build decision, not canonical mapping state.

### References, text, overrides, and transforms

`source_ref` and `donor_ref` are provenance fields using
`SOURCE@OFFSET`, for example `NA2_BTL@0x1E2130` and
`NUN5_TEXTENG@0x29430`. `source` and `donor` are adjacent text fields: `source`
records the exact guarded clean NA2 text, while `donor` records the verified
official translation and is executable by default. `display_context` names the
screen and field where the row appears. `display_basis` is a user-maintained
free-text column; the importer accepts blank or `|`-separated values without
assigning them validation semantics. By project convention, only an
`e2e:<suite-name>` entry records validation by an exact maintained E2E suite,
for example `e2e:collection/voice`. A blank value records that the row is
unvalidated. An E2E basis requires both ownership by the
exact executable family consumed by that suite and selection of that exact
record by the accepted capture plan; equal text or family membership alone is
not coverage. Coverage summaries count every entry independently, so a shared
row contributes to each proven suite.

The importer takes `donor`, applies the declared transform, then prepends the
user-editable `prefix`. For sequence rows,
the prefix is applied to the first resulting fragment. Most rows require no
transform. Paired `@...@` spans in official NUN5 donor text are decoded as
quotation marks by the importer before those operations, and NUN5's semantic
`<iconOK>` confirm token becomes NA2's `<iconCROSS>` token. The explicit
`escape_literal_percent` transform handles the Ninja Song printf consumer.
Formula symbols use the shared [symbol mapping](#symbol-handling).
Raw `donor` and `donor_ref` values remain unchanged as provenance.

`reference_refs` stores optional comma-separated pointer sites in the same
`SOURCE@OFFSET` form. `parent_mapping_id` lets a continuation row reuse its
containing mapping's pointer inventory. Canonical mappings do not carry log
reasons; generated patch records derive a concrete reason from the mapping ID
and whether the row used the official donor, an override, or a prefix.

Two or more `slot` rows may share a clean source slot only when exactly one is
the ordinary inline mapping and every alternate row owns pointer references.
Those pointer-specific aliases are always linked, even when their text would
fit inline, so one shared Japanese string can retain distinct official donor
selections at structurally distinct records. Aliases must declare identical
source text and capacity, and none may redirect the source slot itself.
An empty shared slot may instead contain only pointer-specific aliases; every
alias is linked and the empty inline storage remains untouched.

## Mapping evidence

The links below point to the retail records in
[NA2 and NUN5 text correspondence](../../knowledge/localization/translation_importer.md).

### E2E capture selection

An `e2e:` basis follows the executable record selected along a suite path, not
OCR or equal English.

#### Menus

The three Menus pages contain 14 capture states. Exact source-byte and donor-
byte checks against the retail NA2 and NUN5 files prove these 30 selected rows:

- Character Select consumes T418-T422 from the
  [boot-ELF option table](../../knowledge/localization/translation_importer.md#shared-modal-and-character-select-strings)
  and T423 from the return prompt.
- Battle Settings consumes the
  [label-pointer array](../../knowledge/localization/translation_importer.md#settings-string-references),
  which selects T6, T50, T7, T8, T1979, and T9 in row order. The recorded
  values are T56 `Unlimited`, T28 `Normal` for both Difficulty and Items, T34
  `Normal` for Chakra, and T1987 `Command`. The visible defaults message is T16.
- The recorded Battle pause list selects T57-T59, T62, T68, and T69. Similar
  unrecorded siblings such as T60 and T61 do not inherit Menus coverage.
- The [quit body](../../knowledge/localization/translation_importer.md#battle-and-practice-quit-confirmations)
  is assembled from T63, T66, and T67, with T2201 or T2202 as the selected
  destination. The generic Menus modal uses T1 `Yes` and T2024 `No`;
  Collection instead uses T2025 and T2026 at different boot-ELF slots and does
  not share this coverage.

The canonical `source_ref` and `donor_ref` fields on those 30 rows record every
exact verified NA2 and NUN5 offset. No Menus row uses a mod string or prefix,
and equal English in another executable family does not transfer this basis.

#### Practice

The three Practice pages contain 16 capture states. Retail-file validation
proves the declared NA2 source bytes and exact NUN5 donor bytes for these 55
selected rows:

- the Pause list selects T57-T59, T61-T62, and T68-T69;
- Control Settings selects T1949-T1957, excluding its defaults-status and
  instruction lines;
- the six Practice help pages select title records T1910-T1924, T1929-T1930,
  and T1932, without transferring coverage to their explanation records;
- Special Controls selects the exact boot-ELF T2203 `ON` and T2204 `OFF`
  slots;
- Practice Settings selects labels T1980, T53-T55, T1962, T17, and T1963,
  plus displayed values T28, T1994, T44, T1995, and T34;
- the quit modal is assembled from Practice head T64, T66-T67, destination
  T2201 or T2202, and the generic boot-ELF T1/T2024 Yes/No slots.

The [Practice label and value arrays](../../knowledge/localization/translation_importer.md#settings-string-references)
resolve the recorded labels and values in row order. This separates the exact
T28/T34 `Normal` records and distinguishes the Practice-owned T1920
`Charge Chakra` title from the Command Chart T1926 `Charge` record.

Long helper, status, and explanatory strings are outside the Practice
captures. T1880, T1959, the Practice explanations, and the Settings running-help
rows therefore receive no `e2e:practice` basis from these captures. All 55
admitted rows retain blank `prefix` and `mod_string` fields.

#### Ninja Song

The five Ninja Song states select these exact mapping groups:

- objective prose T70-T82 and T84-T86; T83 `Fulfill special objectives` is not
  selected by the plan and remains without E2E validation;
- item bonus T88 and health bonus T2194; the other bonus-template siblings are
  not displayed and do not inherit Ninja Song coverage;
- timer label T97 and objective indices T2174-T2189;
- N/A T2190 and formula symbols T2195-T2198.

T97 is the `timer counts` unit selected through NUN5's
[unit-index rule](../../knowledge/localization/translation_importer.md#ninja-song-units);
NA2's live unit pointer table reaches the imported T97 slot through index `3`.
Objective 9 has no visible NUN5 unit, so the renderer suppresses it rather than
displaying T2198 `%` as a unit.

T2191-T2193 are literal NA2 unit slots that this capture plan does not display;
they retain their historical basis and `empty` transforms. Every admitted
Ninja Song row keeps its exact `source_ref` and `donor_ref`, all `mod_string`
fields remain blank, and importer validation resolves the source and donor
bytes at those recorded offsets.

#### Collection

The accepted Collection plans contain 207 cases: 31 Characters, 43 Figures,
22 Misc, 19 Opponents, 61 Ultimates, and 31 Voice. Visible text identifies the
field being exercised, but exact `e2e:` membership comes from the executable
record selected along that suite path. The complete selection is reproducible
from these canonical ID sets:

- the 30 common-name rows T427-T443, T445-T447, T450-T454, and T522-T526,
  plus the pointer-specific Granny Chiyo row T2209, are selected by Characters,
  Figures, Opponents, Ultimates, and Voice;
- Figures additionally selects T530-T618 and the 12 Diorama-title rows T527
  and T619-T629;
- Misc selects T527, T619-T676, and the exact confirmation slots T2025-T2026;
- Opponents additionally selects T444, T448, T455-T495, T528, T116, T197, and
  T198;
- Ultimates additionally selects the legacy-name rows T457-T485 and every
  Collection Ultimate title T98-T258;
- Voice additionally selects T677-T824, T2158, and T2205-T2208.

Every accepted character plaque loads the
[Collection master roster](../../knowledge/localization/translation_importer.md#master-roster-and-character-plaques).
T2209 represents its Granny Chiyo pointer field; T449 is the separate primary
`Granny Chiyo` slot and therefore does not inherit Collection E2E membership.
The accepted Misc confirmation telemetry identifies the Collection
confirmation slots, T2025 `No` and T2026 `Yes`; their ordinary shared-modal
context does not prevent exact Misc ownership once the selected addresses are
known.

Three visually similar groups are explicitly outside accepted Collection text
coverage. T529 is the master-table Diorama selector, while the visible grid
label is `HOME.CCS` artwork; it retains structural Figure-identifier evidence
instead of `e2e:`. The short character-grid labels corresponding to T496-T521
are also texture artwork rather than those translation rows. T2200 is a valid
locked Movie placeholder seen in a paired capture, but every accepted Misc
Movie capture is unlocked, so the locked placeholder remains without Misc E2E
validation.

#### Jutsus

The Jutsus suite selects the 26
[Jutsu selector titles](../../knowledge/localization/translation_importer.md#jutsu-selector-titles)
in that table's row order: T260, T939, T954, T968, T996, T1011, T1082, T1096,
T1124, T1202, T1216, T1301, T1364, T1365, T1379, T1434, T1480, T1493, T1523,
T1533, T1551, T1566, T1580, T1727, T1750, and T1767. These 26 rows are the
complete displayed-title selection in the three-page suite.

#### Movesets

The accepted Movesets plans select 1,062 Command Chart title records. Three
valid `0x54` records remain mapped but do not own `e2e:movesets`: T260, T2210,
and T2211. T260 owns `e2e:jutsus`; T2210 and T2211 remain without E2E
validation. The added Granny Chiyo (Taijutsu) `0x4E` unique-mode grid selects
T1651-T1660 from her alternate ordinary-move block. T2210, T2211, and T260
belong to structurally valid extra four-record arrays, but the accepted plans
select other sibling records rather than those three. Their presence in the
Command Chart family is not Movesets capture evidence.

All 154 canonical rows in the `0x14`-byte Ultimate/Jutsu family are selected by
the specials grids. An identical Collection title is still a different
executable record and a different E2E owner.

Accepted grids select
[relationship-selector](../../knowledge/localization/translation_importer.md#command-chart-relationship-strings)
indices 1-15 and 18-22, which are T1881-T1893, T1925-T1926, and T1896-T1900:
exactly 20 rows. Indices 16-17 (`Charge-weak` and `Charge-strong`) are not
selected. T1880, T1894-T1895, T1901-T1924, and T1927-T1932 belong to other
help, Practice, or control consumers and do not inherit Movesets coverage. In
particular, the visible Command Chart `Charge` is T1926 rather than the
Practice-owned T1920; `While jumping` is T1886 rather than T1901
`(while jumping)`. All other table indices remain non-Movesets rows unless a
future accepted plan selects their exact records.

### Record joins and rejected matches

- A Command Chart row is mapped only when the corresponding NA2 and NUN5
  `0x54` record indices both identify nonblank text. That join establishes
  family membership and the exact donor; it does not by itself establish E2E
  selection.
- When a record-selected NUN5 Ultimate/Jutsu name contains decorative color
  tags but a separate plain official copy exists, the plain copy is used for a
  plain NA2 slot.
- The `0x14`-byte moveset records are joined only to their own NUN5 homologs.
  A Collection donor is never propagated into that family merely because the
  current text is equal, and the reverse is equally invalid. For
  `Charge! Konohamaru Ninja Squad!`, the plain Collection copy at
  `NUN5_TEXTENG@0x4D30` is not a valid moveset donor; the importer preserves
  the record-selected `<BLACK>` token when a target slot has no existing black
  form, while a target that already uses `<color000000>` still determines that
  local equivalent. Temari's terminal red span likewise belongs to the moveset
  record and must not be erased by the similar Collection title.
- Collection Figure rows join through the record identifier: locate the
  identifier owning the NA2 Collection slot, find that identifier in the NUN5
  Collection sequence, and use the display string and exact offset selected by
  that NUN5 record. A shared NUN5 string is used only when the Collection
  record itself selects it. A global text search or suffix match is not a valid
  join; that rejected method misidentified six Figure rows as `Tool User`,
  `Pressure`, `Sharp Kick`, `Samehada`, `Favorite`, and `Heaven Kick`.
- Do not import a Collection Figure offset into moveset work merely because its
  wording resembles a move name. Establish the moveset record family and its
  own homologous NUN5 selection first.
- The donor namespace is derived from the selected pointer's address range,
  not assumed from the table's containing file. An exhaustive comparison of
  the 168 Collection Ultimate pointers found 15 prior lookalike/duplicate
  selections; those rows now use the exact record-selected offsets, including
  otherwise invisible trailing spaces when the record points to them.
- Interior substring hits are invalid offsets even when their visible text
  appears plausible, as with the Collection Music title `A Great Evil Appears`.
- The Voice-table join found thirteen similarity-selected offsets that bypassed
  the Voice table: `Passion`, `Determination`, `The Joy of Growth`,
  `Me Myself`, `Youth at Full Power!`, `The Mystery Ninja`, `Gratitude`,
  `A Strong Man`, `The Third Kazekage`, `Duel Start`, `The Fifth Hokage`,
  `No Worries`, and `Admiration`. The first is visibly unchanged but still
  requires its exact record-selected SLES source. The remaining twelve explain
  the paired-screen wording and punctuation mismatches.
- The four Voice cases whose shared Japanese storage selects different NUN5
  titles cannot be represented by overwriting the shared slot globally. The
  canonical mappings keep one translation inline and link the alternate exact
  donor only from its owning 12-byte Voice record. Pointer-specific aliases are
  a placement consequence of the proven record join; their English still comes
  exclusively from `mappings.tsv` and exact NUN5 offsets.
- Collection character plaques map only pointer field `0x25A68` (T2209) to the
  exact secondary `Granny Chiyo ` donor. This preserves both official forms
  without a renderer string test or a global overwrite of the shared NA2 slot.
- The accepted NA2 atlas renders byte `0x40` literally, so the importer decodes
  every balanced NUN5 `@...@` span centrally before transforms or placement.
  Canonical rows retain the exact raw donor and offset and keep `mod_string`
  blank.
- T1486's donor at `NUN5_TEXTENG@0xB9A0` ends in a terminal LF that belongs to
  the selected donor record and remains in the canonical mapping. NA2 parity is
  owned by the Command Chart draw adapter, not by a translation override or an
  altered donor offset.
- Treating each fragment of a packed message as an independent zero-filled slot
  can insert an early empty string and hide later parts. Memory-card notices
  therefore use packed sequence mappings so every official fragment remains
  reachable in order, followed by the verified block terminator, without
  changing file size.

### Content and layout boundary

Canonical donor evidence preserves official wording. It does not insert
authored line breaks or shorten correct text merely to compensate for a
renderer defect. Text the mod rewrites belongs to a mod string linked by the
`mod_string` field and does not change the recorded donor.
Collection Movie line breaks added to four exact NUN5 titles were rejected and
removed; wrapping belongs to the Font caller path. Likewise, the correct
`Flying Thunder God Jutsu` mapping remains unchanged even if a particular
Collection panel needs wrapping.

Generic modal labels remain exact official `No` and `Yes`. A global uppercase
transform was rejected because those slots are shared and did not own the
startup-specific presentation that motivated the experiment. Graphical labels,
controller prompts, emulator chrome, placement, and atlas behavior remain
outside the translation importer.

NA2 states a 103 KB memory-card requirement where NUN5 states 102 KB; copying
the donor number would change the stated source-game requirement, so the
startup prompts that state it are owned by mod strings. The format-failure and
save-data-creation failure donors both fit their NA2 slots.

### Resolved mappings

- The BTL quit modal's T63/T64 mode heads resolve only through the donor's
  `%1`; including the text before `%2` duplicates T66 at runtime. This split
  produces all four NUN5 sentences without storing newlines in canonical
  mappings; draw-time wrapping remains renderer-owned.
- Collection's confirmed selector label uses official `Opponent`; its paired
  screen established that the missing mapping, not layout, caused the Japanese
  label.
- The Mode Select return confirmation's donor is official
  `Return to Title Screen?`; it is distinct from the Save/Load and Character
  Select prompts with different sources and capitalization.
- Temari's Collection voice title maps to official `Silent Confidence`, proven
  by the matching NUN5 screen and `TEXTENG.BIN` source.
- Plain Kankuro maps to `Kankuro`, not `Kankuro (Classic)`; structurally matched
  character families must not collapse distinct variants.

## Output

Each configuration build records the translation importer under:

`@logs/na228/builds/<build-id>/<module-id>/`

containing:

- `translation_imports.tsv`
- `translation_import_summary.json`

The generated import TSV contains exactly ten columns:

`import_id`, `group_id`, `path`, `offset`, `expected_hex`, `replacement_hex`,
`source_text`, `replacement_text`, `source_mapping_id`, `reason`

All ISO target paths inside the TSV remain ISO-root-relative. The configuration-level module inventory also records only repository-relative paths.

`translation_import_summary.json` contains general and aggregate information:

- mapping version and selected targets;
- patch and mapping totals;
- active mapping coverage grouped by mode and display context;
- source and translated-file hashes.

The current table contains no disabled rows.

## Safety behavior

Known clean-source SHA-1 values are always checked. Unknown source media is rejected before a plan is produced.

The module rejects malformed flags, duplicate IDs, missing or invalid display
metadata, invalid offsets, invalid source or donor references, source text that
does not exactly match the clean target, malformed pointer-reference lists,
malformed transforms, overlapping active mappings, unexpected structural
bytes, text exceeding its declared slot or sequence block, malformed target
sequences, invalid named-color conversion, and placeholder donor text that
would overwrite identifier-like NA2 data. Enabled bad mappings fail the build
instead of becoming silent runtime skips. Fullwidth ASCII-compatible donor,
prefix, override, and transform output is normalized to ASCII before encoding;
CP932 source guards are not normalized.

### Exact slot boundaries

A text mapping's `capacity` must end inside zero padding belonging to that string. The module rejects a declared slot if any nonzero byte appears after the original NUL terminator within that capacity. This prevents a text write from zero-filling adjacent pointer tables or other structural data.

This check directly guards against both v28 regressions fixed in v29:

- `M0776` crossed from the `Credits` string into the Collection movie-pointer table at `SLPS + 0x2FFD1C`.
- `M0792` crossed from the difficulty-reset result string into the Options navigation table at `SLPS + 0x4B2BF0`.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

## Markup handling

The original NA2 target is authoritative for renderer-specific color forms:

- NUN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- NUN5 `<BLACK>` adopts a target's existing `<color000000>` form; otherwise it
  remains the native `<BLACK>` token supported by clean NA2 binaries.
- `<RED>` is retained only where the target supports it.
- NUN5 `<iconOK>` becomes NA2 `<iconCROSS>` for the shared confirm semantic.
- Other shared color, icon, line-break, and control tags are preserved.


## Integration expectations

- The reusable engine lives in `@builder/infrastructure/modules/translation_importer/`; this feature-owned directory contains the live mappings and their documentation.
- Do not replace the integrated module by extracting a legacy builder archive over the project.
- Do not copy generated configuration-log plans back into the module.
- Do not add patched `BTL.BIN`, `ETC.BIN`, or `SLPS_258.37` payloads to the importer or checkpoint commits; binary deliverables belong only in the frozen release archive.
- `string_patcher` owns conversion of imported rows into enabled BTL,
  ETC, and SLPS patches; `binary_patcher` owns guards, conflicts, writes, and logs.
- The configuration orchestrator owns composition and ISO application and derives
  the in-memory string-patcher plan directly from the importer output.

The module has no standalone CLI. Mapping `enabled` flags determine imported
targets, and selecting English invokes the complete importer.

## Command Chart titles on action records

Each retail action record's name pointer at `+0x08` joins it to a Command
Chart mapping: a mapping's exact `reference_refs` record-field offset takes
precedence for shared source text; otherwise the pointed-to clean-ELF string
offset joins to `source_ref`. Record layout and owner identities belong to
[Substitution knowledge](../../knowledge/gameplay/substitution.md#attack-record-ownership-and-clean-elf-inventory).

All 1,065 Command Chart mappings resolve to 1,110 record instances: 1,057
mapping IDs name 1,102 instances in the 74 primary-roster tables, and the
remaining eight name records 1 and 3 of auxiliary owners `0x1A`, `0x1D`,
`0x1E`, and `0x1F`. Of the 1,065 mapping IDs, 1,022 name one record, 41 name
two, and two name three. An absent title means only that the record has no
mapping; it must not be given a move name by analogy.

The 1,110 named instances by substitution timing and predicate-block state
(a blocked count means the timing is not consulted):

| Effective timing | Unblocked named instances | Blocked named instances |
| ---: | ---: | ---: |
| `-3` | 3 | 1 |
| `-2` | 24 | 0 |
| `-1` | 252 | 84 |
| `0` | 609 | 9 |
| `1` | 115 | 0 |
| `2` | 13 | 0 |

Ninety mapping IDs have every instance blocked, while 92 have at least one
blocked instance. Six mapping IDs name records with different substitution
profiles, so a title alone does not identify one native record:

| Mapping/title | Distinct stock instances |
| --- | --- |
| T1506 Primary Lotus | Rock Lee `1`: effective `-1`; Might Guy `52`: effective `1` |
| T1507 Dynamic Entry | Rock Lee `3`: effective `-1`; Might Guy `40`: effective `0` |
| T885 Deer Drop | Shikamaru `25`: effective `-1`; classic Shikamaru `25`: effective `1` |
| T867 Sand Burial | Kazekage Gaara `35`: effective `2`, unblocked; classic Gaara `1`: effective `-1`, blocked `0x00008000` |
| T840 Chidori | current Sasuke `3` and classic Sasuke `3`: effective `-1`; Second Stage Sasuke `35`: effective `0` |
| T1141 Windmill | Hanabi `3`: effective `-1`, blocked `0x02008000`; Kimimaro `26`: effective `-1`, unblocked |
