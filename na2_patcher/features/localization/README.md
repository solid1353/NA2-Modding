# Localization feature

This feature owns all declarative content for the accepted English localization
while reusable executable engines remain under `na2_patcher/modules/`.

- [Translation importer](#na2-translation-importer-canonical-t-id-rebuild)
- [String patcher](#string-patcher)
- [Resident Font renderer](#native-nun5-derived-font)
- [Texture patcher](#ui-texture-translation-module)
- [Binary patcher](#ui-translation-binary-patcher-patch-set)
- [Compact external strings](#compact-external-strings)
- [Native NUN5-derived font](#native-nun5-derived-font)
- [Regional menu input](#regional-menu-input)

The feature directory name declares its identity. Its module-named
subdirectories are the inputs that compose it; enabling Localization enables all
of them, and one aggregate profile pin covers their canonical inputs.

## NA2 translation importer (canonical T-ID rebuild)

This first-class `na2_patcher` module imports and validates strings for
**Narutimate Accel v2.28**, based on *Naruto Shippuuden: Narutimate Accel 2*.
It never writes BIN or ELF payloads. Profile builds pass its canonical in-memory
artifact to `string_patcher`, which applies profile output identity, derives
inline versus linked placement from encoded fit and pointer availability, and
compiles one shared `binary_patcher` package. There is no standalone export
command or file-backed inter-stage handoff.

### Mapping metadata

- Canonical `mappings.tsv` rows: `2,053`
- Canonical `mappings.tsv` SHA-256: `3351BF0F2F18135FD621506442E86014E00FA0BCE20B80D0759E6BBD690991E8`
- Retained task-local `rebuild.tsv` rows: `2,173` (`T1` through `T2173`)
- Retained `rebuild.tsv` SHA-256: `EA6D79AF9A955180498E93783E0F70AB9439E34B195806991D400686D79BD71C`

The hashes above are documentation, not a second executable manifest. Git
history and the aggregate Localization feature pin own content identity.
`mappings.tsv` owns the canonical executable donor translations, overrides,
and optional pointer inventory. The translation-free candidate inventory is
retained at `work/String translation/artifacts/diagnostic-rebuild/rebuild.tsv`
and supplied explicitly only to worker mapping-ID builds. It is not feature
content or profile-hashed. Normal builds import only `mappings.tsv`. Profile
`identity.json` owns the imported/output title declaration; `string_patcher`
applies its fixed coverage to the normal translation path.

### Source and target scope

Clean NA2 targets:

- `PRG/BTL.BIN`
- `PRG/ETC.BIN`
- `SLPS_258.37`

NUN5 donor references and donor text are retained in the table for review,
provenance, and executable translation. Normal builds do not read donor
binaries: the verified `donor` text in the table is the default translation.
A nonempty `replacement` is a user-editable override, and `prefix` is a
user-editable string prepended to the selected translation. Official donor text
and ordinary overrides remain complete. T30 uses the complete user-authored
`Ultimate` translation and the validated pointer at `NA2_BTL@0x209CB4`; encoded
fit therefore externalizes it automatically.

### Canonical and diagnostic tables

`mappings.tsv` is the canonical mapping table used by normal builds.
`display_context` is its human-readable page/filter key; rows are sorted by
that context, then by stable `id`.

The 16 columns are:

`id`, `enabled`, `display_context`, `source`, `donor`, `prefix`,
`replacement`, `display_basis`, `source_ref`, `donor_ref`, `mode`,
`capacity`, `transform`, `arguments`, `reference_refs`, `parent_mapping_id`

#### Stable IDs and enabled state

- `id` is a stable mapping identifier.
- `enabled=1` imports the row for downstream `string_patcher` composition.
- `enabled=0` retains the row without applying it.
- `mappings.tsv` is the only enabled-state source. Profile builds never rewrite it
  or inherit flags from external state.
- Changing an enabled flag changes the canonical module input and therefore
  requires an explicit profile hash update.
- The current evidence-scoped table contains only executable rows, so all
  current rows are enabled. Unconfirmed rows are absent instead of retained as
  disabled inventory.

The task-local `rebuild.tsv` is the complete retained diagnostic inventory. Its
human-readable columns come first:

`id`, `display_context`, `source`, `donor`, `prefix`, `replacement`,
`display_basis`, `source_ref`, `donor_ref`, `mode`, `capacity`, `transform`,
`arguments`, `reference_refs`, `parent_mapping_id`, `legacy_ids`

The initial table contains one row per distinct known clean source slot.
`donor`, `donor_ref`, `prefix`, `replacement`, `display_basis`, transforms,
and pointer fields begin empty; optional legacy `M` IDs are lookup aids only. Permanent
diagnostic IDs use unpadded `T1`, `T2`, ... and are never recycled or
renumbered. IDs increase in physical row order. The four 5-byte slots occupy
rows `T1` through `T4` so their complete tokens fit; the remaining initial rows
are sorted by `display_context`, then source location. Future candidates append
with the next permanent ID.

Canonical `mappings.tsv` contains `T#` rows confirmed visible by the paired
screenshot pass plus the explicit character-family exception, sorted by
`display_context` and numeric ID. Its cumulative first two passes have 752
unique enabled rows: 567 from the
hash-verified first-pass corpus and 185 from the second. The verified 74-table
Command Chart family adds 1,041 rows, including Naruto moves absent from the
captured 14-row subset. A subsequent missing-row audit adds another 260
policy-supported rows: 53 directly seen rows, 10 structurally inferred
siblings, and 197 character-family rows, for 2,053 total rows. Exact source,
source reference, mode, and capacity came from the retained diagnostic
inventory. T2042, T2045,
and T2050 use canonical parent IDs `T2011`, `T2043`, and `T2048`.
Paired screenshots correct three reference-table errors: T1956 uses `Off` at
`NUN5_SLES@0x513EF8`, T1957 uses `On` at `NUN5_SLES@0x513EFC`, and T2158 uses
`Warning` at `NUN5_SLES@0x513F38`.

Six Difficulty-family rows are matched by meaning: T27 `Simple`, T1983 `Easy`,
T28 `Normal`, T1984 `Hard`, T29 `Insane`, and T50 `Difficulty`. The full T50
label links through the exact pointer at `NA2_BTL@0x20A264`. T24 reuses the
official Jump-mode help text. Paired screens correct T637 to `Hidden Leaf
Village`, T638 to `Hidden Leaf Gate`, T744 to `Faint Unease`, and T767 to
`Silent Confidence`. T30 is the sole donorless row and uses user-authored
`Ultimate`, externalized through `NA2_BTL@0x209CB4`. Donor-backed rows otherwise
leave `replacement` blank and execute independently validated official donor
text. T1958, T2027, and T2033 retain the established Cross-confirm overrides.
This is an evidence-scoped English table, not a claim that uncaptured screens
are covered.

The canonical table closes every admitted multi-slot `<br>` message family.
T2011/T2041/T2042 cover all four save-progress message parts, while
T2014/T2015 cover both overwrite-confirmation parts. Import fails closed on
missing, duplicate, out-of-range, or inconsistent structured parts so a linked
first line cannot continue into an unrelated resident-payload string.

#### Modes

- `slot`: compile one replacement as a NUL-terminated string, inline when it
  fits or externally when it overflows and has validated pointer references.
- `sequence`: pack the `<NUL>`-delimited replacement fragments into one
  verified NA2 multi-string block. Sequences must fit inline.

Unresolved research does not belong in accepted executable `mappings.tsv`.
The retained task-local `rebuild.tsv` contains guarded source slots, not
executable translations or speculative donor claims.

There is no `shorten` or `pool` mapping mode. External placement is a
`string_patcher` build decision, not canonical mapping state.

#### References, text, overrides, and transforms

`source_ref` and `donor_ref` are adjacent provenance fields using
`SOURCE@OFFSET`, for example `NA2_BTL@0x1E2130` and
`NUN5_TEXTENG@0x29430`. `source` and `donor` are adjacent text fields: `source`
records the exact guarded clean NA2 text, while `donor` records the verified
official translation and is executable by default. `display_context` names the
screen and field where the row appears. `display_basis` begins with `seen:`,
`inferred:`, or `character:` and records why that row is admitted to the
executable table.

`replacement` is a user-editable override field and is normally blank. The
importer selects nonempty `replacement` or otherwise `donor`, applies the
declared transform, then prepends the user-editable `prefix`. For sequence rows,
the prefix is applied to the first resulting fragment. Most rows require no
transform.

`reference_refs` stores optional comma-separated pointer sites in the same
`SOURCE@OFFSET` form. `parent_mapping_id` lets a continuation row reuse its
containing mapping's pointer inventory. Canonical mappings do not carry log
reasons; generated patch records derive a concrete reason from the mapping ID
and whether the row used the official donor, an override, or a prefix.

### Output

Each profile build records the translation importer under:

`logs/na2_patcher/current_<run id>/<module id>/`

containing:

- `translation_imports.tsv`
- `translation_import_summary.json`

The generated import TSV contains exactly ten columns:

`import_id`, `group_id`, `path`, `offset`, `expected_hex`, `replacement_hex`,
`source_text`, `replacement_text`, `source_mapping_id`, `reason`

All ISO target paths inside the TSV remain ISO-root-relative. The profile-level module inventory also records only repository-relative paths.

`translation_import_summary.json` contains general and aggregate information:

- mapping version and selected targets;
- patch and mapping totals;
- active mapping coverage grouped by mode and display context;
- source and translated-file hashes.

The current table contains no disabled rows.

### Safety behavior

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

#### Exact slot boundaries

A text mapping's `capacity` must end inside zero padding belonging to that string. The module rejects a declared slot if any nonzero byte appears after the original NUL terminator within that capacity. This prevents a text write from zero-filling adjacent pointer tables or other structural data.

This check directly guards against both v28 regressions fixed in v29:

- `M0776` crossed from the `Credits` string into the Collection movie-pointer table at `SLPS + 0x2FFD1C`.
- `M0792` crossed from the difficulty-reset result string into the Options navigation table at `SLPS + 0x4B2BF0`.

Official Western text is decoded as Windows-1252. NA2 target strings are decoded as CP932 for inspection and markup adaptation. File sizes never change.

### Markup handling

The original NA2 target is authoritative for renderer-specific color forms:

- NUN5 `<WHITE>` becomes NA2 `<colorFFFFFF>` only where that target uses it.
- NUN5 `<BLACK>` remains `<BLACK>` or becomes `<color000000>` according to the verified target form.
- `<RED>` is retained only where the target supports it.
- Other shared color, icon, line-break, and control tags are preserved.

### Version 45 changes

#### Final-acceptance Shop category help

The matched final-acceptance slot-8 savestates show the Shop category screen
with the official NUN5 `Press <iconCROSS> to choose item.` help line and the
corresponding Current line still Japanese with a Circle-confirm glyph. Version
45 adds `M0530` for the exact clean source at `NA2_ETC@0x2F230` and retains the
exact official `Press <iconCIRCLE> to choose item.` donor at
`NUN5_TEXTENG@0x1490`.

The accepted regional Shop input map uses Cross to confirm, so the
user-editable `replacement` changes only that control token to
`<iconCROSS>`. This is the same evidence-backed policy already applied to the
separate Shop item-list row `M0537`; neither unobserved generic prompts nor
other Circle tokens are changed.

Version 45 contains 2,052 enabled mappings: 2,048 slots and four sequences.
`M0530` fits inline, so external placement remains 31 mappings and 33 pointer
edits, the generated string-only `PRG/228.BIN` remains 1,776 bytes, and the
compiled translation package contains 2,290 binary edits. `M0530` and `M0537`
are the two evidence-backed user overrides; there are no shortened, unresolved,
or prefixed rows.

### Version 44 changes

#### Final-acceptance Collection selector

The matched final-acceptance slot-1 savestates show the Collection ->
Characters screen with the official NUN5 `Opponent` selector label and the
same field still Japanese in Current. Version 44 adds `M0550` for the exact
clean source `<r対戦相手|たいせんあいて>` at `NA2_ETC@0x2EE50`, using the
exact official `Opponent` donor at `NUN5_TEXTENG@0x778` and the concrete
`Collection > Characters > selector label` display context.

The paired Current screen also shows `Flying Thunder God Jutsu` overflowing
the right panel while NUN5 wraps the same official text. `M0720` remains
unchanged: the translation itself is correct, and per-caller wrapping or
auto-fit belongs to the separate layout path rather than canonical string
content.

Version 44 contains 2,051 enabled mappings: 2,047 slots and four sequences.
`M0550` fits inline, so external placement remains 31 mappings and 33 pointer
edits, the generated `PRG/228.BIN` remains 1,776 bytes, and the compiled
translation package contains 2,288 binary edits. `M0537` remains the sole user
override; there are no shortened, unresolved, or prefixed rows.

### Version 43 changes

#### Cross-confirm Shop prompt

The paired Shop captures at checkpoints 046 through 049 show the official
NUN5 help line with a Cross glyph and clean NA2 with a Circle glyph. The
runtime-proven Shop input patches make Cross accept and Triangle cancel, so
retaining the literal `<iconCIRCLE>` donor markup in the rebuilt NA2 text would
describe the wrong control.

`M0537` keeps its exact clean source and official
`NUN5_TEXTENG@0x1550` donor, but now uses the explicit user override
`Select an item and press <iconCROSS> to buy.` Clean NA2 `PRG/ADV.BIN`
contains working `<iconCROSS>` markup, confirming that the target renderer
supports the requested token. The replacement is shorter than the official
donor and remains inline in the existing 112-byte slot.

The audit found two other clean NA2 `<iconCIRCLE>` cases and deliberately left
both untouched:

- `NA2_ETC@0x2F230` (`M0530`) is an alternate Shop instruction that did not
  appear in the supplied Shop captures and therefore remains outside the
  evidence-scoped executable table.
- `NA2_SLPS@0x4B31E0` is a standalone token used by `FUN_00390540` in an
  unclassified prompt renderer associated with the still-unclassified
  `ELF-M022` confirm handler. Its displayed action is not proven, so changing
  it globally could make another prompt inaccurate.

Version 43 contained 2,050 enabled mappings: 2,046 slots and four sequences.
`M0537` was the sole user override; there were no shortened, unresolved, or
prefixed rows. External placement remained 31 mappings and 33 pointer edits,
the generated `PRG/228.BIN` remained 1,776 bytes, and the compiled translation
package contained 2,287 binary edits.

### Version 42 changes

#### Final-acceptance Mode Select confirmation

The matched final-acceptance slot-2 savestates prove that the Mode Select
return confirmation uses the previously omitted `M0549` source at
`NA2_SLPS@0x4B1E00`. Version 42 restores that one row with the exact official
`NUN5_TEXTENG@0x1C90` donor, `Return to Title Screen?`, and the concrete
`Game Mode Select > return confirmation` display context.

This is deliberately separate from `M0804`, the Save/Load prompt whose
official donor uses lowercase `title screen`, and `M0557`, the shorter
Character Select source. The slot-2 Current capture translated the shared
`Yes` / `No` choices but retained this prompt in Japanese, which confirmed that
the missing source row—not the generic modal choices—was the defect.

Version 42 contained 2,050 enabled mappings: 2,046 slots and four sequences.
Every row had display metadata and no shortened, unresolved, prefixed, or
user-override rows. `M0549` fits inline, so the existing 31 external mappings,
33 pointer edits, and 1,776-byte `PRG/228.BIN` remained unchanged. The
compiled translation package contained 2,287 binary edits.

### Version 41 changes

#### Evidence-scoped from-scratch rebuild

Version 41 rebuilds the executable table from zero using the diagnostic
mapping-ID screenshots, the paired savestate library, exact clean NA2 bytes,
and the archived v40 table as reference rather than presumed coverage. Every
one of the 2,049 executable rows now declares a concrete `display_context` and
one stable evidence basis:

- `seen:` for strings visible in the diagnostic screenshots or paired
  savestates;
- `inferred:` for hidden members of a proven selector, running-help, or shared
  screen table;
- `character:` for structurally proven character names, Ultimate Jutsu names,
  Command Chart moves, figure-animation titles, and voice titles.

The rebuild retains 2,048 v40 rows, adds `M2247` for the confirmed Battle HUD
`MAX` label, and removes 124 previously active rows that had no confirmed
display location. Removed content includes the unvisited Ultimate Battle and
inventory blocks, unvisited alternate mode/shop branches, unused generic
choice slots, and the unmatched voice title `M0523`; those clean Japanese bytes
remain untouched.

Three incorrect character-family matches are corrected:

- plain Kankuro `M0246` now uses exact NUN5 `Kankuro` from
  `NUN5_SLES@0x513D88`, not `Kankuro (Classic)`;
- `M0521` now uses `Provocation` from `NUN5_TEXTENG@0x2B18`;
- `M0522` now uses `Contrasting Pair` from `NUN5_TEXTENG@0x2B30`.

All 2,049 source declarations exactly match the clean NA2 targets. All 2,049
donor declarations were independently checked against their NUL-terminated
NUN5 bytes after the specified fullwidth-ASCII normalization, with zero
mismatches. The table has 2,045 slots, four sequences, 32 pointer-inventory
rows, three parent-message rows, no prefixes, and no user overrides.

After project-title policy, 31 mappings are linked externally through 33
guarded pointer edits. The payload contains 29 logical rows at 28 distinct
strings, uses 1,470 encoded bytes, and produces a `0x6F0`-byte `PRG/228.BIN`
with SHA-256
`84DD5C72F4B7D7A472EE2E3C69FBB92621A806E04116D281ED734AE61F5D02EF`.
The compiled translation package contains 2,286 binary edits.

### Version 40 changes

#### User-editable translation schema

Version 40 makes the mapping table describe translation ownership directly.
The clean NA2 location is one `source_ref`; optional pointer sites are one
`reference_refs` list. Source and donor references are adjacent, as are source
and donor text. Historical per-row `reason` labels were removed because they
did not define executable mapping policy; generated patch logs now synthesize
specific reasons from stable mapping IDs.

The official donor is executable by default. `replacement` is blank unless the
user intentionally overrides that donor, and `prefix` is a separate
user-editable field prepended to the transformed result. The current 2,177-row
table keeps the same 2,172 enabled and five disabled mappings while using 2,176
blank replacements, one explicit override, 27 declared transforms, and no
current prefixes.

Focused importer and string-patcher validation reproduced the preceding
composition exactly: generated `PRG/228.BIN` remains `0x700` bytes with SHA-256
`36CFF1341AC14A5AC6DCE5D6640F4F082676CF576851E0BEAF393207C3EE16FB`,
and the compiled package remains 2,434 edits.

### Version 39 changes

#### Canonical-table and placement refactor

Version 39 consolidates mapping semantics, provenance, and pointer references
into one `mappings.tsv`. It removes the separate `references.tsv`, the four
disabled structural-byte rows, the `shorten` mode, and every `[S]` fallback.
The table now contains 2,177 mappings: 2,172 enabled and five disabled. Enabled
rows comprise 2,168 `slot` and four `sequence` mappings.

Every row stores its observed NA2 `source`, exact NUN5 `donor_ref` and `donor`,
and complete executable `replacement`. Source and donor fields are
informational. Historical donor transforms were materialized into replacement
text; only three parent-message `split_br` views remain.

After profile title policy is applied, `string_patcher` encodes each final
replacement. A slot that fits is compiled inline. An overflowing slot is linked
externally only when that same row declares validated pointer references;
otherwise the build fails. Sequences must fit inline. This makes placement a
deterministic build result rather than stored mapping state.

The current clean build derives 32 external mapping rows, 34 pointer edits, and
30 logical external messages at 29 distinct symbols. The one formerly
externalized mapping whose full replacement fits (`M0743`) is now inline.
Generated `PRG/228.BIN` is `0x700` bytes with SHA-256
`36CFF1341AC14A5AC6DCE5D6640F4F082676CF576851E0BEAF393207C3EE16FB`.
The compiled package remains 2,434 edits.

A committed-HEAD versus refactored byte-parity reconstruction confirmed that
no translated output changed. Target-file differences are limited to the new
inline `M0743` slot, removal of its old redirect, and shifted external pointer
addresses after that string left the compact pool. All other inline replacement
bytes match the preceding pipeline.

### Version 38 changes

#### Restore shared modal-label capitalization

Version 38 restores `M0566` and `M0799` to the exact official NUN5 donor text,
`No` and `Yes`. Runtime testing showed that the attempted uppercase forms did
not control the supplied startup prompt, and these slots are generic modal
labels rather than startup-specific presentation. Applying a global uppercase
transform here would therefore alter unrelated dialogs. The unused `uppercase`
transform is removed from the importer.

The v37 project-title policy remains unchanged: the six guarded title-bearing
mapping results still materialize `Narutimate Accel v2.28`.

The packaged v38 table contains 2,181 mappings: 2,172 enabled and 9 disabled.
Enabled rows comprise 2,135 `slot`, 4 `sequence`, and 33 `shorten` mappings.

### Version 37 changes

#### Project title presentation

Version 37 applies one exact, hash-pinned semantic policy after official-source
transforms and before inline or linked placement: the donor token
`Naruto Shippuden: Ultimate Ninja 5` becomes `Narutimate Accel v2.28`. The
guarded coverage is six final mapping results and seven donor-token occurrences:
`M0823`, `M0826`, `M0827`, `M0828`, `M0829`, and `M0832`. The full `M0823`
parent message is policy-resolved separately for the `M0825` continuation, so
both its inline prefix and linked complete message carry the project title.

Raw NUN5 templates remain available as provenance. `mappings.tsv` continues to
store source references and transforms rather than duplicated source/result
sentences; generated logs record the resolved text. Configuration pins the
exact donor token, output token, and expected coverage so source drift or
accidental expansion fails the build.

The supplied side-by-side runtime capture also confirms that the prompt overflow
is separate: NUN5 word-wraps inside donor `<br>` parts, while NA2 renders each
packed sequence fragment as one clipped line. Title shortening reduces that
overflow but does not replace the Font workstream's renderer/autofit fix.

The packaged v37 table still contains 2,181 mappings: 2,172 enabled and 9
disabled. Enabled rows comprise 2,135 `slot`, 4 `sequence`, and 33 `shorten`
mappings.

#### v37 build validation

A clean-source full in-memory plan was validated with all three targets:

- the v37 mappings hash, profile title-policy counts, and reference guards matched;
- 2,434 generated import rows and 2,172 applied text mappings;
- all six title-bearing results use `Narutimate Accel v2.28`;
- `M0566`/`M0799` resolved to `NO`/`YES` in v37 (reverted in v38);
- 31 logical external messages occupy 1,512 encoded bytes at 30 distinct symbols;
- generated `PRG/228.BIN` is `0x720` bytes with SHA-256
  `AD94B66F2916C0014A87D110F5807DC0F0F5D7E91615AE3F04EC970CFBA00E9F`.

### Version 36 changes

#### Executable-table cleanup and semantic guard

Version 36 removes all 59 non-executable `unresolved` rows. Fifty-seven carried
only `NO_VERIFIED_OFFICIAL_SOURCE_OFFSET`, one retained an obsolete disabled
dialog fragment, and one recorded the dynamic save-date renderer lead now
preserved in `docs/HYPOTHESES.md`.

`M1336` is also removed. It would have overwritten the clean identifier-like
value `pjrvspl0` at `SLPS_258.37 + 0x3C0660` with the literal NUN5 executable
placeholder `unknown`. No evidence proves that slot is display text, so the
clean NA2 bytes remain authoritative.

The importer no longer accepts an `unresolved` mode. It also fails closed when
placeholder donor text such as `unknown`, `placeholder`, or `dummy` would
replace identifier-like target data. Resolved source and replacement text stay
in generated logs; `mappings.tsv` continues to store source references and
transforms rather than duplicated strings.

The packaged v36 table contains 2,181 mappings: 2,172 enabled and 9 disabled.
Enabled rows comprise 2,135 `slot`, 4 `sequence`, and 33 `shorten` mappings.
The disabled rows are 5 retained `slot` mappings and 4 structural `bytes` rows.

#### v36 build validation

A clean-source full in-memory plan was validated with all three targets:

- mapping version 36 and its packaged hash matched;
- 2,436 generated import rows;
- 2,172 applied and changed text mappings;
- 33 shortened mappings and zero active structural patches;
- no `unresolved` rows or active identifier-to-placeholder replacements;
- unchanged `228.BIN` payload bytes and layout.

### Version 35 changes

#### Collection Movie exact-source rollback

`M0771` through `M0774` again copy their exact official NUN5 source strings
without an authored `<br>` transform. Version 34 incorrectly treated a
text/font fit issue as part of the Texture-patcher task and inserted line breaks that
were not present in the selected NUN5 bytes. Version 35 restores the prior
source-derived mappings exactly; any remaining overflow belongs to separate
text/font work and is outside the Texture-patcher scope.

#### v35 build validation

A clean-source full in-memory plan was validated with all three targets:

- mapping version 35 and the packaged mapping hash matched the README;
- 2,437 six-column TSV patch rows;
- 2,173 applied and changed text mappings;
- 33 shortened mappings;
- zero active structural patches;
- all four Collection Movie rows retained their exact NUN5 source strings and
  contained no authored `<br>` transform.

### Version 34 changes (superseded by v35)

#### Collection Movie line wrapping

Four exact official NUN5 movie titles already fit their original NA2 executable
slots but NA2 rendered each title as one clipped line. NUN5's `ETC.BIN`
contains an additional Movie-specific construction path using
`ccHomeIspMovie`; the NA2 homolog does not invoke that path. Porting the whole
overlay routine would also import unrelated object-layout and renderer-call
changes.

`M0771` through `M0774` used `insert_br_after_words` to preserve every word
from their existing exact NUN5 source references while reproducing the line
breaks visible in the official NUN5 screen:

- `Sealing Jutsu: Nine<br>Phantom Dragons`
- `People of Endless<br>Darkness`
- `Ninja Art: Beast<br>Scroll Replicas`
- `Fourth Awakened<br>Mode`

The transform accepts only a valid single-space word boundary. All four results
fit their existing fixed slots; no shortening, relocation, pointer rewrite,
overlay edit, or target-size change was used. Runtime review rejected this
authored text change, so v35 removes it.

#### v34 build validation

A clean-source full in-memory plan was validated with all three targets
selected:

- mapping version 34 and the packaged mapping hash matched the README;
- 2,439 six-column TSV patch rows;
- 2,173 applied and changed text mappings;
- 33 shortened mappings;
- zero active structural patches;
- all four Collection Movie replacements contained the declared `<br>` at the
  official word boundary and remained inside their original slots.

### Version 33 changes

#### Temari Collection voice-title resolution

The previously unresolved Temari voice title `姉の喜び` is now mapped to the exact official NUN5 title `Silent Confidence`. The user supplied the matching NUN5 Collection screenshot, and the binary source was verified at `PRG/TEXTENG.BIN + 0x24B0`.

`M0725` now applies an enabled `slot` mapping to `PRG/ETC.BIN + 0x2C750`. The 18-byte English string fits the original 32-byte zero-padded NA2 slot, so no shortening, relocation, pointer rewrite, or file-size change is required.

#### Packaged table totals

The packaged v33 table contains 2,241 mappings: 2,231 enabled and 10 disabled. Enabled rows comprise 2,136 `slot`, 4 `sequence`, 33 `shorten`, and 58 `unresolved` mappings. All four structural `bytes` rows remain disabled.

All script and generated-artifact path references remain relative. v33 adds no absolute path literals, patched payload files, relocation pools, pointer rewrites, or target-size changes.

#### v33 build validation

A clean-source full build was validated with all three targets selected:

- 2,437 six-column TSV patch rows;
- 2,173 applied text mappings;
- 33 shortened mappings;
- zero active structural patches;
- unchanged target file sizes;
- relative `translation_tsv` in `build_summary.json`;
- exact `M0725` patch at `PRG/ETC.BIN + 0x2C750`, replacing `<r姉|あね>の<r喜|よろこ>び` with `Silent Confidence`.

### Version 32 changes

#### Collection character-model animation pass

v32 traces the remaining Japanese mannequin/model animation labels through the per-character `if...anmN` identifiers shared by NA2 and NUN5. It adds or activates 35 verified mappings:

- 32 exact official names copied from `PRG/TEXTENG.BIN` or the NUN5 executable short-string table;
- `M0717` is activated as exact `Hey!` after its identifier match was confirmed;
- `[S]Long Time!` is used for `Long Time No See!`, which cannot fit Ino's 16-byte NA2 slot;
- `[S]Now` is used for `Now then...`, which cannot fit Kankuro's 8-byte executable slot.

This completes every untranslated Japanese model-animation label found in the supplied 54-screen v31 review set, including Naruto, Kakashi, Neji, Tenten, Shikamaru, Choji, Ino, Asuma, Kiba, Shino, Hinata, Kurenai, Kankuro, Temari, Chiyo, Itachi, Kisame, Deidara, Jiraiya, Tsunade, Shizune, Yamato, Orochimaru, Kabuto, and Sasuke entries.

#### Collection voice/audio title pass

v32 adds or activates 20 verified voice-title mappings by matching their position in the official NUN5 title sequence and, where applicable, the NUN5 executable's short-string copies. This includes the supplied Sai, Kakashi, Shikamaru, Choji, Shino, Kiba, Itachi, Orochimaru, Chiyo, Kabuto, Sasuke, and Sasori screenshots.

Two constrained slots use traceable shortening:

- `[S]Naru/Sasuke` for official `Naruto and Sasuke` in a 16-byte ETC slot;
- `[S]Task` for official `Assignment` in an 8-byte executable slot.

Temari's `姉の喜び` remained unresolved as `M0725` in v32 because no exact official NUN5 English source had yet been verified. It is resolved in v33 after the matching NUN5 screen and binary source were supplied.

#### Remaining Collection jutsu and shared battle-name gaps

v32 fills all 16 verified gaps in the Collection ultimate/special-jutsu sequence exposed by the screenshot set, including:

- `Facing the Sunset`;
- `My Rule: One` and `My Rule: Two`;
- `IQ 200` in both verified target copies;
- `Super Human Boulder 2`;
- `Sand Spear Funeral`;
- `Ten Puppets of Chikamatsu`;
- `Puppet: Iron Sand Cluster 2`;
- `Chakra Dissection Blade: Destroy`;
- `Partial Expansion Jutsu 2`;
- `Galium Spurium Dance 2`;
- `Summoning: Rashomon, Abyss 2`;
- `Tongue-Lash Combo 2`;
- `Raining Spider 2`;
- `Earth Style: Terra Shield 2`.

The battle-select/Command Chart shared strings `鹿蝶封結` and `涅槃精舎の術` are also mapped to exact NUN5 `Kachofuketsu` and `Temple of Nirvana Technique`.

No string is relocated and no pointer is rewritten. Every new exact mapping fits its original zero-padded slot; only the four explicitly marked `[S]` rows use manual shortening.

#### Packaged table totals

The packaged v32 table contains 2,241 mappings: 2,231 enabled and 10 disabled. Enabled rows comprise 2,135 `slot`, 4 `sequence`, 33 `shorten`, and 59 `unresolved` mappings. All four structural `bytes` rows remain disabled.

All script and generated-artifact path references remain relative. v32 adds no absolute path literals, patched payload files, relocation pools, or target-size changes.

#### v32 build validation

A clean-source full build was validated with all three targets selected:

- 2,436 six-column TSV patch rows;
- 2,172 applied text mappings;
- 33 shortened mappings;
- zero active structural patches;
- unchanged target file sizes;
- a relative ten-column import inventory in the profile module log;
- `M0745=1` and all new v32 IDs retaining their packaged enabled defaults.

### Version 31 changes

#### Character Command Chart expansion

v31 ports the character-specific Command Chart move names by matching the actual table structures instead of searching for isolated Japanese strings.

NA2 contains 74 verified command-record arrays in `SLPS_258.37`. Each record is `0x54` bytes and stores its displayed-name pointer at record offset `+0x08`. NUN5 contains the corresponding per-character pointer arrays in `PRG/TEXTENG.BIN`. The mapping data was expanded only where the NA2 record index and the corresponding NUN5 pointer-table index both reference nonblank text. The Naruto mappings introduced in v28-v30 served as the anchor and were reproduced exactly by this method before it was extended to the other characters.

This adds 1,041 new Command Chart mappings:

- 1,035 exact official NUN5 names that fit their original NA2 slots;
- 6 traceable `[S]` shortenings for the only command names that do not fit;
- no relocation pools, pointer rewrites, or writes beyond original zero-padded string slots.

Together with the 15 already-mapped Naruto entries, v31 covers 1,056 unique command-name targets across the 74 shared character tables. One table contains two NA2/NUN5 presence differences; those unmatched entries remain untouched rather than being guessed.

The six new shortened command names are:

- `[S]Fairy Tale is Real!!`
- `[S]Bamboo Shoot Thrust`
- `[S]Clover Boar`
- `[S]Anesth. Wt.`
- `[S]Clarity Rush`
- `[S]Inst. Blade`

#### Ultimate and character-specific jutsu expansion

Ultimate/special-jutsu records use a separate verified `0x14`-byte structure. The first word is the localized name pointer, while the remaining four metadata words are identical between NA2 and NUN5. Matching those four words identifies the official NUN5 name without relying on string order or manual translation.

v31 covers:

- 153 unique executable-side names in `SLPS_258.37`, including all discovered Naruto Ultimate Jutsu entries rather than only `Unchanging Relationship`;
- 146 verified duplicate names in `PRG/ETC.BIN`;
- 152 newly added SLPS mappings and 133 newly added ETC mappings;
- one shortened official name in each target: `[S]8 Trigrams Mountain Break` for `8 Trigrams Mountain Break Attack`.

Three older suffix-only ETC mappings are corrected to their complete official names:

- `64 Palms` becomes `8 Trigrams 64 Palms`;
- `Sand Burial` becomes `Giant Sand Burial`;
- `Wolf Fang` becomes `Wolf Fang Over Fang`.

Previously unresolved `M0718`, `M0719`, and `M0720` are now pointer-verified and active for `Lightning Blade, Single Sharpness`, `Ninja Art: Copy Jutsu`, and `Flying Thunder God Jutsu`.

Three record-selected NUN5 names contain decorative color tags while separate plain official copies also exist in `TEXTENG.BIN`. v31 references those plain official copies because the corresponding NA2 slots contain no verified color-tag form. No English wording is invented.

#### Packaged table totals

The packaged v31 table contains 2,180 mappings: 2,170 enabled and 10 disabled. Enabled rows comprise 2,066 `slot`, 4 `sequence`, 29 `shorten`, and 71 `unresolved` mappings. All four structural `bytes` rows remain disabled.

All generated paths remain relative. v31 adds no absolute script paths, no patched payload files, and no relocation behavior.

### Version 30 changes

#### Packed multi-string message blocks

Several NA2 dialogs are stored as consecutive NUL-terminated fragments inside one fixed-size region. Earlier mapping versions treated each fragment as an independent fixed slot and zero-filled the remainder of every original fragment. When an English fragment was shorter than the Japanese one, the inserted zero padding created an early empty string and stopped the renderer before later fragments.

v30 adds `sequence` mode for these verified blocks. A sequence mapping:

- reads exact parts from one official NUN5 string;
- writes the selected parts consecutively with one NUL terminator after each part;
- writes one additional NUL after the complete sequence;
- zero-fills only the unused tail of the whole verified block;
- never changes file size or writes outside the declared block.

Generated TSV annotations render the internal separators as `<NUL>` for readability. The literal characters `<NUL>` are not written into the game.

#### Memory-card dialog repairs

v30 replaces the broken fragment-by-fragment mappings with four packed sequence mappings:

- `M0857`, `SLPS + 0x3039E0`, exact NUN5 no-card notice from `NUN5_TEXTENG + 0x29060`:
  `No memory card (PS2) is inserted in <br>MEMORY CARD slot 1.<br>Please insert a memory card (PS2) in<br>MEMORY CARD slot 1.`
- `M0813`, `SLPS + 0x303C40`, the lower unformatted-card notice from parts 0 and 1 of `NUN5_TEXTENG + 0x291D0`:
  `The memory card (PS2) in <br>MEMORY CARD slot 1 is unformatted.`
- `M0816`, `SLPS + 0x303CE0`, the separate upper prompt from part 2 of `NUN5_TEXTENG + 0x291D0`:
  `Format memory card (PS2)?`
- `M0829`, `SLPS + 0x3046A0`, the exact startup no-card Yes/No prompt from `NUN5_TEXTENG + 0x29A10`:
  `No memory card (PS2) is inserted.<br>Please insert a memory card (PS2) in MEMORY CARD slot 1.<br>At least 102 KB of free space is necessary to save Naruto Shippuden: Ultimate Ninja 5 data. Start the game anyway?`

Retired fragment rows `M0814`, `M0815`, `M0817`, `M0830`, and `M0831` are removed. Obsolete external enabled-state files are no longer read; the canonical table is authoritative.

#### Naruto Ultimate Jutsu name

The visible `変わらない関係` entry is translated with the exact NUN5 name `Unchanging Relationship` from `NUN5_TEXTENG + 0x3F60`.

Both verified NA2 copies are covered:

- `M0858`: `ETC + 0x284C0`
- `M0859`: `SLPS + 0x4AE030`

#### Carried-forward repairs

v30 retains all v29 fixes: Options help-line pointer preservation, the first Theater entry restoration, `Charging Kick`, `Clone Jumping Explosion Hit`, relative generated paths, the `M0745` migration repair, original-slot text only, traceable `[S]` shortening, and no relocation pools or pointer redirects.

The packaged v30 table contains 854 mappings: 844 enabled and 10 disabled. Active mappings comprise 745 `slot` rows, 4 `sequence` rows, and 21 `shorten` rows. Seventy-four enabled `unresolved` entries remain documented but unapplied; all four structural `bytes` rows remain disabled.

### Rolling runtime issue log

This log persists unresolved visual/runtime findings across mapping versions. Entries implemented in the current module remain in the verification section until confirmed in-game.

#### Reverted in v38

- **Generic modal choice capitalization:** the v37 uppercase transforms on
  `M0566` and `M0799` did not affect the supplied startup prompt and were
  semantically wrong because the slots are shared modal labels. Version 38
  restores exact official NUN5 `No`/`Yes`; do not repeat the global transform.

#### Rejected in v34 and rolled back in v35

- **Collection Movie authored line breaks:** removed from `M0771` through
  `M0774`; any remaining fit issue is separate text/font work.

#### Implemented in v33, runtime verification required

- **Temari voice title:** verify `姉の喜び` now displays exact NUN5 `Silent Confidence` in the Collection character voice list.

#### Implemented in v32, runtime verification required

- **Collection character models:** verify the newly covered mannequin/model animation labels across the supplied roster screenshots, including the short `[S]Long Time!` and `[S]Now` entries.
- **Collection voice/audio lists:** verify the newly covered title entries, especially `[S]Naru/Sasuke` and `[S]Task`; Temari's previously unresolved final entry is covered by v33.
- **Collection jutsu lists:** verify all newly filled numbered/alternate moves, including My Rule 1/2, the second Human Boulder, Iron Sand Cluster, Rashomon, Tongue-Lash, Raining Spider, and Terra Shield entries.
- **Battle select and Command Chart:** verify `Kachofuketsu` and `Temple of Nirvana Technique` replace the two remaining Japanese names in the supplied screenshots.

#### Implemented in v31, runtime verification required

- **All character Command Charts:** verify character-specific move names across the roster, not only Naruto, and report any still-visible Japanese name with its character and screen position.
- **Ultimate Jutsu lists:** verify that each character's multiple Ultimate Jutsu names are translated, including Naruto entries beyond `Unchanging Relationship`.
- **Previously partial ETC names:** verify full `8 Trigrams 64 Palms`, `Giant Sand Burial`, and `Wolf Fang Over Fang` text where those copies are used.
- **New `[S]` entries:** verify the eight newly shortened target copies display completely and remain understandable.

#### Implemented in v30, runtime verification required

- **Standard no-card notice:** the lower dialog should show the complete exact NUN5 no-card and insertion message instead of mostly Japanese text.
- **Unformatted-card dialog:** the lower notice should show `The memory card (PS2) in MEMORY CARD slot 1 is unformatted.` and the upper prompt should show `Format memory card (PS2)?`.
- **Startup no-card Yes/No prompt:** the complete exact NUN5 prompt should appear instead of stopping after `No memory card (PS2) is inserted in`.
- **Naruto Command Chart:** `変わらない関係` should show `Unchanging Relationship`.

#### Carried from v29, runtime verification still required

- **Options, Difficulty Settings:** bottom blue help line should show `Set the Com strength for when in the Free Battle and Practice.`
- **Options, Control Settings:** bottom blue help line should show `Assign button controls.`
- **Collection Movie list:** first entry should show `Reunion Time I` in the correct list position.
- **Naruto Command Chart:** `特攻蹴撃` should show `Charging Kick`.
- **Naruto Command Chart:** `分身跳爆打` should show `Clone Jumping Explosion Hit`.

#### Open

- **Options main-screen graphical labels:** owned by the separate Texture-patcher and
  layout task; they remain outside this text module.
- **Collection Movie screen chrome:** graphical title/category and button assets
  are owned by the separate Texture-patcher task and remain outside this text module.
- **Command Chart chrome:** any remaining Japanese heading or back prompt that is graphical rather than string-backed remains outside current scope pending resource extraction.
- **Dynamic save date/time numerals:** the digits are generated by executable code and still require a verified renderer/code mapping; the lead is retained in `docs/HYPOTHESES.md`, not the executable mapping table.

PCSX2 application chrome, toolbar text, pause indicators, graphical controller prompts, and emulator toasts are not game translation issues and are not logged here.

### v35 test checklist

1. Build from a clean mapping-version-35 module and confirm the summary reports version 35.
2. Confirm `build_summary.json`, console output, scripts, and documentation contain only relative path references.
3. Preserve external enabled state and verify `M0745=1`; `M0725` must remain enabled and apply as a `slot` mapping.
4. Recheck all 54 supplied Collection screenshots and confirm every v32-covered model-animation, voice-title, and jutsu entry is English.
5. Confirm Temari's final voice-title entry displays exact NUN5 `Silent Confidence`.
6. Verify the four new shortened entries visibly retain `[S]` and fit their fixed slots: `Long Time!`, `Now`, `Naru/Sasuke`, and `Task`.
7. Verify `Kachofuketsu` appears in both the battle-select and Command Chart contexts using the shared target string.
8. Verify `Temple of Nirvana Technique` appears in the battle-select entry.
9. Recheck v29-v31 Options, Theater, save/load, memory-card, Naruto, and roster-wide Command Chart fixes for regressions.
10. Confirm the four long Collection Movie mappings copy their exact NUN5
    source strings and contain no authored `<br>`; text/font fit is outside
    this Texture-patcher task.
11. Generated TSV validation: exactly ten columns, fixed-size imports only,
    relative summary reference, no active overlap, unchanged target file sizes,
    and successful compilation/application through `string_patcher` and the
    current Font package.

### Integration expectations

- The reusable engine lives in `na2_patcher/modules/translation_importer/`; this feature-owned directory contains the live mappings and their documentation.
- Do not replace the integrated module by extracting a legacy builder archive over the project.
- Do not copy generated profile-log plans back into the module.
- Do not add patched `BTL.BIN`, `ETC.BIN`, or `SLPS_258.37` payloads to the importer or checkpoint commits; binary deliverables belong only in the frozen release archive.
- `string_patcher` owns conversion of imported rows into default-enabled BTL,
  ETC, and SLPS patches; `binary_patcher` owns guards, conflicts, writes, and logs.
- The profile orchestrator owns composition and ISO application. The importer
  must run immediately before its consuming `string_patcher` instance.

The module has no standalone CLI. Mapping `enabled` flags determine imported
targets, and enabling the Localization feature invokes the complete importer.

## String patcher

The generic module owns string placement policy. Localization has no
`string_patcher/` feature directory because it owns no local string declarations;
the importer artifact invokes the engine as a derived consumer. It accepts
validated in-memory rows, resolved source text, and references, compiles inline
imports, contributes external strings as named read-only-data fragments, and
declares symbolic pointer writes. The shared `payload_builder` chooses offsets
and constructs `PRG/228.BIN`; the composer resolves symbols; `binary_patcher`
owns byte guards, conflict handling, replacement, and logging. If Localization
later owns local declarations, it can add `string_patcher/strings.tsv` then.

The memory-card title is output identity and is therefore declared by the active
profile's `identity.json`; its evidence is documented in
`docs/knowledge/game/disc_identity.md`.

## UI texture translation module

This module derives the selected official English NUN5 UI containers directly
from the canonical NA2 and NUN5 sources and writes them into the unchanged NA2
`DATA/DATA.CVM` member ranges. No replacement CCS blobs are stored in Git.

### Safety and reproducibility

- `containers.tsv` pins every clean NA2 target and official NUN5 donor member.
- `mappings.tsv` records 210 reviewed texture relationships.
- `strategies.tsv` pins each derived fixed-size replacement hash and its
  decompressed CCS payload hash.
- All 96 derived replacements preserve their original NA2 member size and
  therefore do not move a `DATA.CVM` member or ISO extent. Their fixed ranges
  total 6,297,394 bytes.
- Ninety-two `whole` strategies import the complete NUN5 CCS payload so pixels,
  models, UVs, layout, and animation data remain coupled.
- `HOME.CCS` is a whole donor because its official collection headers,
  Previous Page/Play labels, button prompts, models, UVs, and layout must stay
  coupled. The former texture-only import clipped and displaced those labels.
- `MAPSEL1.CCS` is a whole donor because its stage-picture association/order,
  object layout, models, UVs, and labels must match NUN5 together. The stage
  picture pixels already matched; retaining NA2's structure caused the defect.
- Sixty-one character `3EYE/3???3PCT.CCS` containers import the complete
  official NUN5 Victory-name and ordinary-awakening artwork. Fifty-nine use
  complete donors because those are the only decoded visual changes. Haku and
  Shikamaru remain mapped fixed-capacity exceptions: Haku discards transparent
  canvas and uses seven nearest colors from its NUN5 palette; Shikamaru omits
  only its faintest donor antialias shade. No character texture blobs are
  stored. `UI-BTL-014` separately derives NA2's prebuilt name rectangles from
  the official NUN5 frame templates and English width table.
- `3EYE/ENDDEMO.CCS` is mapped so only the complete NUN5 `enddemo01` TEX/CLT
  pair, including the English `WINNER` emblem, replaces the corresponding NA2
  atlas. Its two unrelated background textures and target CCS structure remain
  unchanged.
- Mapped `copy` retains the first container-local TEX palette reference and
  validates paired component signatures before changing the target.
- `MODE2KDV.CCS` is a mapped capacity exception: it retains the NA2 portrait,
  palette, and lower 192 visual rows, then imports the donor's top 64 label rows
  through deterministic nearest-palette-index remapping.
- `CMN/GAUGE.CCS` supplies the shared regional UI atlas. In particular,
  `TEX_xpanel` replaces NA2's Circle/decision and Cross/back legends with
  NUN5's Cross/OK and Triangle/Back legends wherever the common panel is used.
- The NUN5 one-part `OUGI.CCS` layout also requires the paired,
  size-preserving `UI-BTL-001` semantic port in
  `na2_patcher/features/localization/binary_patcher/`.

The engine searches deterministic zlib encodings first. Twenty-eight
fixed-capacity members require Zopfli, and indexed-region translations use it
to avoid zlib-version-dependent replacement bytes;
`na2_patcher/requirements.txt` pins the verified `zopfli==0.4.3`
implementation. A normal build fails clearly instead of using different or
unpinned output bytes when that dependency is unavailable.

### Commands

Install the pinned patcher dependency:

```powershell
python -m pip install -r na2_patcher/requirements.txt
```

Derive and verify every pinned production replacement from the repository root:

```powershell
python -m na2_patcher.modules.texture_patcher.engine verify `
  --package na2_patcher/features/localization/texture_patcher
```

Regenerate the reviewed Victory rows and hashes after an intentional source or
strategy change:

```powershell
python scripts/research/ui_translation/generate_victory_texture_mappings.py --write
python scripts/research/ui_translation/generate_victory_layout_patch.py --write
```

Write a review-only generated extraction outside the source roots:

```powershell
python -m na2_patcher.modules.texture_patcher.engine preview `
  --package na2_patcher/features/localization/texture_patcher `
  --output "work/UI translation/temp/ui_texture_preview"
```

Changing a mapping, strategy, compressor version, or canonical source must
produce the exact pinned payload and replacement hashes or fail. Any intentional
hash change therefore requires explicit review and a profile-pin update; there
is no blob-authoring command or stored binary fallback.

### Evidence and tools

The investigation used the repository's extracted NA2, NUN5, and Brazilian
NUN6 sources; preserved Ghidra exports; a purpose-built CCS parser and texture
decoder; gzip/zlib and Zopfli 0.4.3; and CCSFileExplorerMSF 3.0.0.0 for
independent visual inspection. StudioCCS material under `@utils/old/` was used
as format evidence only; no untrusted historical utility was executed. The
reasoning, inventory, layout comparisons, and historical runtime evidence are
recorded in `docs/workstreams/ui_translation/plan.md`.

## UI translation binary-patcher patch set

This patch set holds size-preserving executable changes that are inseparable from
the NUN5 UI container import but do not belong inside `DATA.CVM`.

Its 108 guarded edits are donor-first: 63 copy bytes directly from canonical
NUN5 files (44 from the ELF, 14 from `BTL.BIN`, and five from `ETC.BIN`).
Another 24 store the exact values of NUN5's stage-width formula in NA2's
different inline-record layout. The remaining 21 are documented NA2-specific
ports where the equivalent NUN5 behavior has a different instruction or data
topology, or where NA2 intentionally needs a different value.

### UI-BTL-001: one-part OUGI label

NA2's Ultimate Jutsu banner uses two 64x64 label halves. The official English
NUN5 and Brazilian NUN6 versions both use one 128x64 label and one-part
construction behavior. The whole-container `OUGI.CCS` import supplies that
one-part model, UV, texture, and animation layout.

At BTL file offset `0xB5E80`, NA2 contains `02 00 42 2A`
(`slti v0,s2,2`). `UI-BTL-001` replaces it with `01 00 42 2A`
(`slti v0,s2,1`) to port the donor's one-part behavior into NA2's loop. The
canonical NUN5 ELF, BTL, ETC, and ADV files do not contain that exact four-byte
instruction, so this row correctly remains an authored semantic port rather
than claiming an arbitrary donor copy. It preserves the file size and is
runtime-proven with the imported one-part container.

Validate and inspect the planned edit from the repository root:

```powershell
python -m na2_patcher.modules.binary_patcher.engine validate `
  --package na2_patcher/features/localization/binary_patcher `
  --root na2=@source_na2

python -m na2_patcher.modules.binary_patcher.engine plan `
  --package na2_patcher/features/localization/binary_patcher `
  --root na2=@source_na2 `
  --patch UI-BTL-001
```

Evidence and the broader container/layout analysis are recorded in
`docs/workstreams/ui_translation/plan.md`.

### UI-BTL-002: localized stage-name rectangles and width fitting

NA2 and NUN5 store the same 24 `(stage_id, index)` pairs in the same order:

- NA2 BTL file offset `0x20FC10`: 24 records of 16 bytes, with an inline
  `(u, v, width, height)` rectangle after the two key words;
- NUN5 BTL file offset `0x215680`: 24 records of 8 bytes containing the two
  matching key words.

NUN5 obtains the localized rectangle separately through `FUN_003d4120`. Its
English language table is the 24-entry rectangle range at NUN5 ELF file offset
`0x4DDB90`. The NUN5 draw path also fits names wider than 214 pixels with
`min(1.0, 214.0 / width)`; copying only the rectangles would therefore preserve
the clipping visible in NA2.

`UI-BTL-002` reproduces the localized behavior without adding a jump or
overwriting a code cave. In the NA2 table, every second key word is exactly the
matched loop index. The selected-preview consumer at BTL file offset `0x606BC`
changes from loading that redundant word to `move s0,s1`. The small-thumbnail
consumer at `0x603B8` instead recovers the same index from the existing
`row * 16` byte offset with `srl a0,v1,4`. The freed word in each record stores
the precomputed single-precision NUN5 scale.

The original stage-name code initialized both axes to `1.0` by loading `f14`
and copying it to `f15`. At BTL file offset `0x61570`, the `mtc1` destination
changes from `f14` to `f15` so vertical scale stays at `1.0`; at `0x6157C`,
the former `mov.s f15,f14` becomes `lwc1 f14,4(v1)` so only horizontal scale
receives the precomputed fit. The remaining 24 rectangle fields are copied from
the hash-pinned NUN5 ELF table. Finally, the Random prompt and its companion
sprite at `0x61F40` and `0x61F64` copy NUN5's exact X=`260` instructions in
place of NA2's X=`300` instructions. NUN5 positions OK and Back at effective
X=`388`/`462` by applying regional `-12`/`-8` offsets to nominal
X=`400`/`470`. NA2 lacks those additions, and the NUN5 global loads are not
ABI-compatible with NA2, so two guarded same-register constants at
`0x61EF8`/`0x61F1C` reproduce the effective donor behavior.

The patch is 56 individually guarded edits: 24 rectangle rows copy NUN5's
English ELF table, 24 scale rows store the exact result of NUN5's width formula,
two rows copy NUN5's Random-position instructions, two rows adapt the effective
NUN5 OK/Back anchors, and four code rows adapt NA2's inline-record topology. A
temporary application verified that all 24
stage keys remain unchanged and match NUN5, every rectangle equals the official
English table, every scale equals the NUN5 formula, all changed bytes stay
inside declared ranges, and the 2,237,184-byte BTL size is unchanged. The user
then compared the integrated Slot 3 result with NUN5 and accepted Stage Select
as fixed, promoting `UI-BTL-002` to `runtime_proven`. A later guarded paired
Slot 5 capture proves the added OK/Back anchors match the NUN5 footer.

### UI-ELF-001: localized character-name atlas rectangles

The character-name renderers do not obtain their rectangles from
`CHARSEL1.CCS`. NA2 `FUN_0037d410` reads one 96-entry table at EE `0x005D4E70`
(ELF file offset `0x4D4F70`). NUN5's corresponding name helper
`FUN_0038c350` calls localized accessor `FUN_003d45d0`; language index zero in
the accessor's pointer table resolves to the official English range at EE
`0x005DDC50` (ELF file offset `0x4DDDD0`).

Each record is four signed 16-bit values `(u, v, width, height)`. Forty-four of
the 96 English records already match NA2; the other 52 change widths,
coordinates, or blank sentinels to match the imported English name atlases.
Copying the complete 768-byte English range is the minimal complete fix shared
by Character Select, VS, the battle HUD, and Battle Set. The edit is range-hash
guarded at both source and destination and preserves the ELF size.

The nearby NUN5 `FUN_0038c3a0` range at file offset `0x4DC120` is deliberately
not used. It is the separate uniform 38x46 character-portrait grid consumed by
NUN5's counterpart of NA2 `FUN_0037d470`. An earlier test build copied that
range and produced the stacked name fragments captured at runtime; the
localized accessor and call-site pairs disprove that source selection.

### UI-ELF-002: localized Options label rectangles

Importing the complete NUN5 `OPTION.CCS` is not sufficient by itself. The main
Options renderer supplies atlas rectangles from the boot ELF:

- NA2 `FUN_0038c160` reads five menu-label records at EE `0x005D52E0` and
  six difficulty-label records at EE `0x005D5310`;
- NUN5 `FUN_0039dba0` obtains the homologous English records through
  `FUN_003d43a0` and `FUN_003d43f0`, whose English tables begin at EE
  `0x005DDB90` and `0x005DDBC0`.

Both renderers use the same five screen positions and `0.9` scales. Their arrow
rectangle is also byte-identical. The remaining difference is the 96-byte
rectangle block: five menu labels, an eight-byte zero separator, and six
difficulty labels. `UI-ELF-002` copies that complete official English block from
NUN5 ELF file offset `0x4DDD10` to NA2 ELF file offset `0x4D53E0`. Source and
destination ranges are hash guarded and the ELF size is preserved.

### UI-ELF-003: difficulty-value sprite routing

The NUN5 rectangles alone fix the five main Options labels, but the widest
difficulty value still fragments unless it is drawn through the same alternate
sprite object used by NUN5. The homologous renderers differ in one predicate:

- NA2 `FUN_0038c160` selects the alternate object for indices `0` and `5`;
- NUN5 `FUN_0039dba0` selects it for indices `0`, `4`, and `5`.

At NA2 EE `0x0038C30C` (ELF file offset `0x28C40C`), `UI-ELF-003`
replaces the existing `index == 5` test with `index >= 4`, while retaining the
following `index == 0` test. For the renderer's proven valid domain `0..5`, the
resulting set is exactly `{0, 4, 5}`. The edit changes two instructions, keeps
the original branch targets and delay slots, and preserves the ELF size.

A paused, identity-checked PINE write matched the two original words exactly
and verified the eight-byte readback. After one redraw, the corrupt selected
value became a clean centered `INSANE`; captures of `HARD`, `EASY`, and
`SIMPLE` also rendered cleanly, including both arrow endpoints.

### UI-BTL-004: localized Practice Settings prompt layout

The VS-screen Practice Settings prompt needs both the English atlas rectangle
and the localized horizontal anchor. The corresponding renderers provide exact
cross-build evidence:

- NA2 `FUN_006c0cc0` uses the static rectangle `(1, 281, 112, 22)` at BTL
  file offset `0x20C9D8` and passes X=`60.0` at file offset `0xCFA0`;
- NUN5 `FUN_006d4170` calls localized accessor `FUN_003d46c0`, whose English
  table resolves to ELF file offset `0x4DE0E0`, and passes X=`100.0`.

`UI-BTL-004` copies the official NUN5 rectangle `(0, 280, 176, 24)` from its
ELF and copies the structurally equivalent `lui v0,0x42c8` instruction from
NUN5 BTL file offset `0xD500`. Both edits are exactly guarded, preserve BTL
size, and remain confined to the Practice Settings path.

The two edits were applied to a paused Current runtime and read back exactly.
After one redraw, the sprite object reported X=`276`, Y=`356`, size `176x24`,
and UV `(0,280)`. The archived screenshot shows the full label and Square icon
at the same bottom-left position as the NUN5 target.

### UI-BTL-005: localized VS confirmation labels, inputs, and prompts

The battle-confirmation Customize screen retains Japanese regional rectangle
tables even after importing the NUN5 VS texture container. `UI-BTL-005` copies
the exact English NUN5 rectangles for:

- `Customize Jutsu` and its Circle prompt;
- `Battle Settings` and its Square prompt;
- the two-arrow control;
- all three Jutsu input glyphs;
- the one-part `Jutsu1` and `Jutsu2` labels.

NUN5's Jutsu helper offsets its 62x26 label by 26 pixels and the three input
glyphs by 40 pixels. NA2's static draw path lacks those additions. A 16-byte
NA2 helper is installed in verified loaded zero padding at BTL file offset
`0x30`, the label path calls it at `0x9188`, and the two structurally equivalent
40-pixel accumulator instructions are copied from NUN5 BTL offsets `0x974C`
and `0x9750` into `0x91BC..0x91C3`. The localized 160x24 Battle Settings prompt
is drawn at the official X=`94` through the constant at `0xCFD8`.

NUN5 passes X=`260` for `Customize Jutsu`. The final guarded test proves that
this exact value is valid once the open-selector state is corrected: the full
Circle prompt remains on-screen and matches NUN5. `UI-BTL-005` therefore copies
only the X-immediate halfword from NUN5 BTL `0xD6A8` into NA2 `0xCF70`, keeping
NA2's required `v0` destination register rather than copying an incompatible
whole instruction.

The bottom legends use a separate boot-ELF table. NUN5 ELF `0x4DE9F0` contains
complete Cross/OK `(1,1,56,22)` and Triangle/Back `(1,25,64,22)` records; NA2
ELF `0x4D4790` contains two 70x22 regional records and its BTL wrapper draws an
additional glyph. The patch copies the complete 16-byte NUN5 table and disables
the redundant NA2 glyph arguments at BTL `0xD014` and `0xD038`.

Because NA2 and NUN5 advance that shared sprite differently, identical nominal
anchors do not produce identical raster positions. Two paired calibration runs
located the exact NA2-compatible constants: `400/470` rendered 15/10 pixels
right of NUN5, while `384/460` rendered 5/3 pixels left. NA2 `388/462`, written
at `0xCFFC` and `0xD020`, aligns both legends at `dx=0,dy=0`.

All 19 edits are byte-guarded. The final hidden, muted isolated run preserved
both Jutsu labels, the two-arrow and Circle controls, the full bottom prompts,
and the accepted open-selector arrows. The user accepted the NUN5-first paired
screen as perfect.

The earlier submenu-suppression wrapper remains rejected: NUN5 retains the
Jutsu1/Jutsu2 graphics beneath the open selector, while suppression removed
them and exposed unrelated atlas data. No such hook is retained.

This patch changes texture selection, placement, and submenu visibility only.
It does not change or evaluate command-name text or font rendering.

### UI-BTL-006: localized Round label layout

NA2 constructs `Round` from two Japanese 38x38 glyph rectangles at X=`216`,
Y=`44`, and scale `1.4`. NUN5 uses one English 94x30 rectangle at X=`256`,
Y=`24`, with scale `1.2` and a Y=`64` render constant.

`UI-BTL-006` copies the exact NUN5 rectangle from ELF file offset `0x4DE110`,
zeros the unused second-glyph record, ports the differently stored X/Y fields,
and copies the four structurally equivalent scale/render instruction ranges
from NUN5 BTL into NA2 offsets `0xCCB4`, `0xCD5C`, `0xCD64`, and `0xCDA4`.
Eight guarded live writes were read back exactly. The resulting one-part label
matches the paired NUN5 capture; small frame-to-frame outline differences are
the screen's normal pulsation.

### UI-BTL-007: localized open Jutsu-selector arrows

The open Jutsu selector is a separate state from the accepted closed
confirmation screen. NA2 `FUN_006bd4d0` incorrectly retains the two horizontal
draw calls used by its closed-state sibling and draws its green-arrow record
without rotation. NUN5 homolog `FUN_006d0850` omits both horizontal draws,
loads `+pi/2` and `-pi/2` for the upper and lower indicators, and clears the
sprite rotation after each draw.

The whole NUN5 VS texture import makes NA2's old `(139,257,38,22)` source
rectangle invalid: it samples lettering rather than the Japanese atlas's
downward triangle. Guarded live testing first copied NUN5's official
`(145,385,22,38)` right-facing source and wrote the exact NUN5 `+pi/2` and
`-pi/2` values into NA2's live sprite object. The rotation field read back
exactly, but both rendered arrows still pointed right. Persistent and
draw-scoped control-field transplants either had no effect or corrupted the
sprite, proving that this NA2 draw path does not consume NUN5's rotation mode.

The accepted correction keeps `VS.CCS` as a byte-for-byte whole NUN5 donor and
scopes the compatibility state to each arrow draw. BTL `0x9ABC..0x9B23`, which
held the unwanted horizontal blocks, now contains a branch plus a compact
helper; normal execution resumes at `0x9B38`, so the helper consumes no shared
header cave. The helper enables NA2 sprite mode 1, applies the lower flip when
the copied NUN5 angle is negative, draws the localized record, flushes while
mode 1 remains active, and then restores mode 0.

The four angle words and `(145,385,22,38)` rectangle are exact NUN5 copies.
Only the helper and its two call redirects are authored NA2-specific glue,
because leaving NUN5 mode state active damages unrelated objects and restoring
it before the flush discards the queued primitive. The final isolated capture
has matching upper/lower arrows, no horizontal arrows, no bottom fragment, and
no collateral label changes. The user accepted the paired result as perfect;
confidence and runtime status are verified. No label text, command text, font,
or gameplay-input data is changed.

### UI-BTL-008: localized command-list scroll arrows

Command Menu and Command Chart share the same scroll-indicator draw method:
NA2 `FUN_00878820` and NUN5 `FUN_00894f60`. Both render one `TEX_xselect`
record twice, rotating the first draw by pi for the opposite direction. Paired
Slots 5 and 6 reuse the same sprite object, so their green-garbage defect has
one data root rather than two independent layouts.

NA2 BTL offset `0x21D648` selects `(194,195,20,20)`, which samples green text
fragments from the imported NUN5 atlas. `UI-BTL-008` copies the exact NUN5 BTL
record `(1,225,20,22)` from `0x2214D8`, selecting the orange vertical-scroll
triangle. The existing positions and pulse are retained; small capture-to-
capture Y differences remain normal animation. The user verified the integrated
Current build on both Command Menu and Command Chart and accepted both screens
as good, promoting the shared correction to runtime-proven/verified.

Detailed function, address, side-effect, and negative-result evidence for both
patches is preserved in `docs/knowledge/localization/ui/battle.md`.

### UI-BTL-009: localized paired item-status labels

Paired item effects use two foreground rows, a shared bubble, and a three-rank
offset table. `UI-BTL-009` copies the official NUN5 records `0x8E..0x94` and
`0x9B..0x9C` plus the complete rank table. The remaining writes are an
NA2-specific ABI port: they add anisotropic sprite scaling, preserve NA2's
object layout, and reproduce the donor width normalization, centering, row
spacing, rotation, clamp, and common origin.

The patch was reconstructed from homologous boot-ELF and BTL functions and
validated against the accepted paired item checkpoint. Controller, foreground
labels, and white-bubble bounds match NUN5; a one-pixel top-edge difference is
normal pulse timing. Numeric, single, and fixed-status layouts are separate
classes. The pair helper now exposes explicit caller-owned anchor, row, and
angle-output arguments so the bounded numeric port can reuse it without
changing the pair result.

The same resident sprite renderer also owns the transition geometry used by
all four item classes. Its first NA2 port correctly preserved the NUN5 scale in
`f22` and alpha in `f21`, but the final centered-offset calculation still
negated `f21`. At partial alpha, that scaled each local half-width/half-height
offset and made the foreground appear to slide into and out of a stationary
bubble. `UI-BTL-009-30` copies NUN5's exact `neg.s f2,f22` instruction from
ELF file `0x284418` to NA2 file `0x2772F4`. Alpha continues to fade normally,
while local geometry remains constant; fully visible placement is unchanged.

### UI-BTL-010: localized numeric item-status labels

Numeric item effects share one class for Health, Chakra, Recovery, and their
one-, two-, and three-digit values. `UI-BTL-010` copies the complete official
NUN5 records `0x81`, `0x82`, and `0x8D`, then routes the NA2 numeric top and
lower label callers through the ABI-safe item helper with the donor anchors and
rotation behavior.

The six digit-position writes are an NA2-specific coordinate port, not literal
donor copies. NUN5 establishes a negative-50 X origin and adds
`14/23/32`, `18/28`, or `24`; the NA2 helper already represents that origin,
so the equivalent local constants are `-36/-27/-18`, `-32/-22`, and `-26`.
Literal NUN5 instructions would apply the origin twice. The final numeric Slot
3 checkpoint matches Health, Chakra, and Recovery against NUN5, while the
settled paired Slot 7 regression remains intact.

Detailed function boundaries, file/runtime mappings, reconstructed behavior,
side effects, evidence, and the rejected whole-function donor transplant are
preserved in `docs/knowledge/localization/ui/battle.md`.

### UI-BTL-011: localized single item-status labels

Single item effects use one foreground label and the same common bubble
controller as the paired and numeric classes. `UI-BTL-011` copies the complete
official NUN5 records `0x96..0x9A`. The object-code-to-record tables are already
identical in NA2 and NUN5, so no mapping data is authored or duplicated.

The remaining changes are a bounded NA2 ABI port. They replace NA2's regional
`(+33,+42)` foreground origin with NUN5's `(0,+33)` origin and set the
quarter-turn after resource lookup only for donor records `0x82` and `0x99`.
The homologous NA2 wrapper is retained; calling its lower renderer directly was
rejected because that uses a different argument contract. The shared scale
helper retains the accepted pair path while assigning the traced NUN5 single
scales: `1.90625` for code `0x09` and `1.0` for every other single label.

Paired Slot 10 proves simultaneous `Invisible` and `Substitution Jutsu`
placement. Slot 12 proves the same implementation for poison/status effects.
Both match NUN5 bubble bounds, label centers, and clipping at 640x480; remaining
differences are battle animation timing. Record `0x99` was not present in the
captured set, so its branch is statically verified from both complete draw
functions and the patch is runtime-proven with high confidence rather than
marked verified.

### UI-BTL-012: localized fixed item-status labels

The fixed two-label item class always draws records `0x8E` and `0x8D`. Those
official rectangles are already supplied by the donor-backed paired and numeric
item patches, so this patch adds no texture data or duplicate table copy.

NA2 placed the two records with fixed regional offsets `(+38,+11)` and
`(+18,+25)`. NUN5 centers each record from its live rectangle width and uses Y
offsets `+20` and `+37`. `UI-BTL-012` routes both NA2 draw sites through the
existing runtime-proven shared item-width helper, with zero X bias and local Y
biases `+2` and `+17` over that helper's established `+18/+20` row bases. The
fixed renderer ignores the helper's angle output, preserving its original
uniform draw path.

A controlled synthetic checkpoint changed the sole paired object in matched
Slot 7 to each game's real fixed-class vtable; the NUN5 object also received its
traced fixed scale. The resulting `Status Effect` / `Recovery` labels have the
same center relative to the white bubble in both games. The remaining whole
object delta is the expected one-frame pulse/update difference. Because the
checkpoint uses a transformed live object rather than a naturally spawned
fixed notification, the runtime-proven patch retains high confidence.

### UI-BTL-013: localized battle Mash prompt rectangles

The battle prompt object stores its main label ID at `+0x2F` and supplemental
controller-glyph IDs from `+0x30`. NUN5 routes main IDs below seven through a
regional boot-ELF accessor; NA2 directly indexes a Japanese seven-record table
inside `BTL.BIN`. With the NUN5 battle texture already imported, NA2's first
record samples the English Mash artwork vertically and clips it.

`UI-BTL-013` copies the complete 56-byte official NUN5 English table from boot
ELF offset `0x4DE630` to NA2 BTL offset `0x1DB730`. It is one exact guarded
donor edit: no literal replacement, code hook, object-layout change, or stored
asset is required. A paired guarded savestate test rendered both Mash labels
horizontally at the NUN5 positions.

The adjacent NA2 BTL range at `0x1DB770` is the controller-glyph table, not a
second copy of the main-label table. A rejected live test against that range
left Mash unchanged and corrupted the Cross panels, proving the semantic
boundary. Exact renderer functions, address mappings, object fields, records,
and negative evidence are preserved in
`docs/knowledge/localization/ui/battle.md`.

### UI-BTL-014: localized Victory character-name layouts

NA2 and NUN5 use homologous Victory update and draw functions, but their
rectangle-provider ABIs differ. NA2 BTL returns pointers to 24-byte prebuilt
Japanese records. NUN5 BTL selects one of two official frame templates and
fills its width from the localized boot-ELF table. For Naruto, NUN5 atlas
widths `156, 192` become renderer widths `154, 190`; NA2's records contain
`236, 173`.

`UI-BTL-014` keeps the NA2 pointer-return ABI and generates all 78 unique
compatible records from the exact NUN5 templates plus each English width minus
the renderer's two-pixel border. Zero-only NUN5 aliases remain untouched, and
all shared-pointer rows agree whenever they provide a nonzero width. Direct
donor copies cannot represent the synthesized records because they do not
exist as final data in NUN5. The generator verifies both ELFs and both BTL
files before updating the guarded replacements; no handwritten placement
permutation or stored binary asset is used.

The resident update, draw, and two-part centering code is instruction-level
equivalent across both games. A stale NA2 savestate resumes into a different
animation phase and texture replacement does not reconstruct its loaded CCS,
so that route is rejected as runtime acceptance. Exact function ranges,
file/runtime mappings, reconstruction, alias evidence, and the remaining
normal-entry runtime requirement are preserved in
`docs/knowledge/localization/ui/victory.md`.

### UI-BTL-015: localized settings footer anchors

The Battle and Practice Settings footers are rendered inside BTL rather than
by the shared resident Options functions. NA2 `FUN_008807a0` and
`FUN_00882250` draw Select at X=`230`, while the homologous NUN5
`FUN_0089d280` and `FUN_0089f130` draw both Select components at X=`200`.
`UI-BTL-015` therefore copies all four exact same-register NUN5 instructions.

NUN5 loads nominal X=`400`/`470` for OK/Back and then adds per-call runtime
offsets `-12`/`-8`. NA2 has no equivalent additions. Copying only the nominal
NUN5 instructions would leave the legends visibly too far right, so the two
NA2 call sites use authored effective anchors X=`388`/`462`. These are the same
NA2-compatible anchors already proven for the analogous confirmation footer.

The eight writes are confined to the two Settings draw functions. Guarded
task-owned slot-6 and slot-10 states rendered Select, OK, and Back at the NUN5
positions without changing the accepted Customize Jutsu footer. Exact function
ranges, file/runtime mappings, reconstructed behavior, and evidence are
preserved in `docs/knowledge/localization/ui/battle.md`.

### UI-BTL-016: localized Battle Results summary layout

The whole NUN5 `XNINKA.CCS` import supplies the English Battle Results artwork,
but NA2 retained Japanese result-label rectangles, moving-cloud widths, footer
records, title offset, and rank-stamp geometry. `UI-BTL-016` imports the
complete six-record NUN5 result table, paired title/cloud rectangles, Display
Details rectangle, and complete five-cloud motion/geometry table. The five
cloud positions, speeds, and heights were already equal; the NUN5 widths keep
each moving object inside the localized cloud strip instead of traversing
animated `Ninja Song` letters.

The shared five-value rank selector already reads the complete NUN5 English
rectangle table installed by `UI-ELF-004`. NA2 nevertheless drew the selected
record without a pivot at anchor `(animatedX + 90, rowY - 1)`. NUN5 centers the
same 1.35-scaled record and applies its effective X/Y compensation. NUN5's
localized accessors and helper are not ABI-compatible with NA2, so one authored
NA2 call-site port delegates the selected donor rectangle to resident helper
`FUN_0037BD00`. The resulting candidate sprite object's pivot, anchor, width,
and height fields match NUN5 bit-for-bit, but guarded Y and UV trials proved
that object is not the visible rank-label layer.

The visible layer samples the packed five-label column at X=`416..511`,
Y=`0..219` from the official NUN5 `XNINKA.CCS` atlas. NA2 renders that column
11 source rows too low. `UI-NINKA-001` therefore keeps the complete donor
container and applies `indexed_shift_region_up_11_416_0_96_220`. The transform
copies the complete region upward, clears only its vacated bottom rows, and
rejects the derivation unless every discarded top-row donor pixel is
transparent. A guarded task-owned `Outstanding!` texture-memory trial matches
the NUN5 placement. Per user instruction, no ISO was built for this canonical
change; all five rank values remain pending the next normal pipeline run and
user validation.

The remaining code edits use exact same-register NUN5 instructions where
possible. Display Details Y uses a compact NA2 sequence because the NUN5
language-accessor call cannot be copied, and the shared Next low half is
cleared after importing NUN5's integral anchor. A fresh hidden transition from
task-owned slot 1 proves the moving clouds, labels, footer, and stamp frame
without relying on an already-constructed stale screen. Complete function
ranges, file/runtime mappings, reconstruction, live object fields, side
effects, and negative evidence are preserved in
`docs/knowledge/localization/ui/battle.md`.

### UI-ETC-001: localized Shop label layout

Importing the complete NUN5 `SHOP.CCS` supplies the correct English atlas, but
NA2's Shop renderer still copies its Japanese currency rectangles from
`ETC.BIN`. The corresponding 24-byte tables are:

- NA2 ETC file offset `0x30300`, loaded at EE `0x006E4200`;
- NUN5 ETC file offset `0x292F0`, loaded at EE `0x006EFFF0` in NUN5.

The first eight-byte panel record is already identical. `UI-ETC-001` copies
only the remaining 16 bytes, replacing `(169,385,42,26)` and
`(213,385,18,26)` with NUN5's official full `Money` rectangle
`(169,385,62,26)` and `Ryo` rectangle `(321,449,30,22)`. It does not change the
money value or its formatting logic.

The rectangle range previously rendered both labels in full while preserving
the existing seven-digit `9999999` value. A later paired review established
that the three English labels still did not match NUN5 placement. Complete
homologous-function comparison now copies NUN5's exact Money X=`254`, Ryo
Y=`50`, and Bonus Game X=`105` instructions over NA2's X=`250`, Y=`48`, and
X=`100` constants. The money-value origin remains NA2-specific so its
seven-digit layout is not clipped.

The newer slot-7 comparison confirms the Bonus Game left anchor but exposes a
four-pixel right-edge crop. Both homologous renderers copy a second 16-byte
rectangle table: NA2 ETC `0x30340` contains icon `(129,137,22,22)` and label
`(129,161,122,22)`, while NUN5 ETC `0x29330` retains the identical icon and
widens the label to `(129,161,126,22)`. A fifth guarded NUN5 import copies that
complete table, preserving the anchor and extending only the missing right
edge. The user accepted the final paired Shop result on 2026-07-26.

The full file/runtime mapping, practical reconstruction, call relationships,
side effects, evidence, and rejected pulse-only interpretation are recorded in
`docs/knowledge/localization/ui/shop.md`.

### UI-ETC-002: localized Collection submenu layout

The whole NUN5 `HOME.CCS` import supplies the complete English `Previous Page`
and `Next Page` artwork. NA2 still draws those pixels through two ETC-owned
tables sized for its Japanese atlas: centers X=`100` and X=`220` at Y=`360`,
and two 118x24 source rectangles. NUN5's homologous tables use centers X=`87`
and X=`233` and two 144x24 rectangles. The narrower NA2 rectangle clips
`Previous Page` to `Previous Pa`.

`UI-ETC-002` copies both complete tables from NUN5: 32 placement bytes from
NUN5 ETC offset `0x281C0` to NA2 offset `0x2E930`, then 16 rectangle bytes from
NUN5 offset `0x29A60` to NA2 offset `0x30A80`. Both page controls remain paired
exactly as the original draw loop expects; no authored replacement bytes or
text/font changes are involved.

The imported NUN5 category titles have a separate mismatch. NA2's Characters
and Movie rectangles are 34 pixels high, crossing into the next 28-pixel NUN5
atlas row, while NA2's Music rectangle begins below the imported English Music
row. The NA2 and NUN5 placement vectors are already identical. Three exact
NUN5 ELF copies therefore replace only the source rectangles:

- Characters: `(1,1,192,34)` -> `(0,0,192,28)` at NA2 ETC `0x30490`;
- Movie: `(1,37,136,34)` -> `(0,28,96,28)` at NA2 ETC `0x30498`;
- Music: `(1,83,80,37)` -> `(0,56,96,28)` at NA2 ETC `0x304A0`.

Movie and Music also expose the common `Play` control. NA2 helper
`FUN_006b44b0` selects `(120,24,72,24)` from ETC offset `0x2E790`; with the
NUN5 HOME atlas this starts 24 pixels before the English control and displays
only `Pl...`. NUN5 homolog `FUN_006c7250` obtains `(144,24,72,24)` through
localized accessor `FUN_003d4210`. The sixth edit copies that exact record from
NUN5 ELF offset `0x4DDC70`. The adjacent Stop record remains unchanged because
it was not visible in the reviewed states.

A later paired character-viewer capture isolates the four lower controls. NA2
places Rotate, Move, Zoom In, and Zoom Out on one row at Y=`360`; NUN5's exact
four-record table places Zoom In/Zoom Out at Y=`339` and Move/Rotate at
Y=`364`. The NUN5 rectangle block also widens both Zoom labels from 108 to 112
pixels and moves Zoom Out to its English-atlas U coordinate. Edits seven and
eight copy the complete 64-byte position block and 32-byte rectangle block
from NUN5 ETC offsets `0x283D0` and `0x29A90` to NA2 ETC offsets `0x2EB40`
and `0x30AB0`. The separate accepted Back path remains untouched.

Static provenance and the draw-path
reconstruction and paired Characters/Movie/Music evidence are recorded in
`docs/knowledge/localization/ui/collection.md`. All eight operations derive bytes from
canonical NUN5 files and preserve ETC size. Runtime acceptance remains pending.

### UI-ELF-005: localized Mode Select layout

The whole NUN5 `MODESEL1.CCS` import supplies the English START artwork, but
NA2's static rectangle still selected only `(1,397,206,22)` and drew it at
X=`130`. That truncates the 254-pixel English label visible in preserved slot 1.
NUN5 `FUN_003972e0` obtains rectangle `(1,393,254,26)` from localized accessor
`FUN_003d4bc0` (English table entry at ELF offset `0x4DE318`) and draws it at
X=`150`.

`UI-ELF-005` copies that exact eight-byte rectangle into NA2 ELF offset
`0x504710`. The X constant at NA2 offset `0x285F28` is an authored
same-register port from `130` to `150`: the corresponding NUN5 instruction
writes `v1`, while NA2's following instruction consumes `v0`, so copying the
four instruction bytes verbatim would be incorrect.

The same paired slot showed OK and Back shifted right. NUN5 loads nominal
X=`400`/`470` and then applies signed regional offsets `-12`/`-8` before
calling its shared compositor. NA2 has no equivalent additions, so exact donor
loads would preserve the defect. Two additional guarded NA2 constants at ELF
offsets `0x285EE0` and `0x285F04` express the official effective anchors
X=`388`/`462` while retaining NA2's ABI.

All four edits preserve ELF size. A guarded task-owned slot-1 render placed
both prompts within +1 pixel X/Y of NUN5, the normal pulse-phase variance.
The user accepted the final Mode Select footer on 2026-07-26.
The complete function mapping, behavior reconstruction, side effects, and
donor-copy limitation are preserved in
`docs/knowledge/localization/ui/options.md`.

### UI-ELF-006: localized Controls Vibration-label rectangle

The whole NUN5 `CMN/GAUGE.CCS` import supplies the English `TEX_xmenu`
artwork, but NA2's boot-ELF table still selects the Japanese rectangle
`(1,69,42,22)` at file offset `0x4D53C0`. NUN5's localized table selects
`(64,88,64,20)` at file offset `0x4DEA28`.

`UI-ELF-006` copies that exact eight-byte NUN5 rectangle into the homologous
NA2 table. It changes only the graphical Vibration label selection; surrounding
OFF/On text and font rendering are outside scope. Both ranges are guarded and
the ELF size is preserved.

### UI-ELF-007: localized Character Select footer anchors

The complete NUN5 `CHARSEL1.CCS` import already supplies the English
`Select Color` and `Random` artwork. Their screen positions come from the
boot-ELF Character Select footer compositor:

- NA2 `FUN_003bc470` draws `Random` at X=`300` and `Select Color` at X=`160`;
- NUN5 homolog `FUN_003cf0d0` draws the same two records at X=`260` and
  X=`100`.

`UI-ELF-007` copies the two exact NUN5 `lui v0` instructions into NA2 ELF
offsets `0x2BC600` and `0x2BC624`. Both homologs use `v0` for these calls, so
no register adaptation or authored literal is needed. NUN5 also adds regional
offsets `-12`/`-8` to nominal OK/Back X=`400`/`470`; NA2 issues those separate
calls without the additions. Two authored same-register constants at NA2 ELF
offsets `0x2BC5B8` and `0x2BC5DC` therefore encode the equivalent effective
anchors X=`388`/`462`. Guarded patched copies of the preserved state were
rendered by the task-owned hidden clone: all four footer groups land at the
NUN5 positions within normal one-pixel pulse variance. Exact boundaries,
mappings, reconstruction, and runtime evidence are preserved in
`docs/knowledge/localization/ui/character_select.md`.

### UI-ELF-008: localized shared common prompts

The complete NUN5 `CMN/GAUGE.CCS` import supplies the English common-prompt
artwork, but NA2 `FUN_0037c980` still centers its case-4 Cancel prompt using
three Japanese rectangle widths totaling 182 logical pixels. NUN5 homolog
`FUN_0038bb10` uses localized records 6, 4, and 5 totaling 80 pixels around
the same caller anchor.

`UI-ELF-008` copies those three exact NUN5 records into the corresponding NA2
static slots: the localized Triangle icon, 56-pixel Cancel label, and empty
tail. The shared correction therefore applies to every case-4 common-prompt
caller rather than compensating only the Options screen. A guarded patched
copy of the preserved Options state rendered the final Cancel bounds within
one pixel of NUN5 in both axes, consistent with normal pulse timing.

Battle Results exposed the same shared compositor's record 2: NA2 retained a
70-pixel Next label while NUN5 uses the complete 66-pixel English record.
The fourth edit copies that exact NUN5 record; `UI-BTL-016` supplies its NUN5
screen anchor.

The Options-root caller also exposes the same regional footer-anchor difference
already proven on Mode Select and the two Settings screens. NUN5 loads nominal
OK/Back X=`400`/`470` and applies `-12`/`-8` before calling the shared
compositor; NA2 calls it with the unadjusted values. Two authored
same-register ports use the equivalent effective X=`388`/`462` values at NA2
ELF offsets `0x28C878` and `0x28C89C`. A guarded task-owned slot-1 render
matches the NUN5 prompt positions without changing the accepted Cancel
geometry or any text/font behavior.

The Collection state renderer is a separate consumer with a second nominal
Cross/Triangle position table. NA2 `FUN_006c8290` reads X=`380`/`460` from ETC
offsets `0x2F010`/`0x2F018`; NUN5 homolog `FUN_006dbaa0` reads the same nominal
values and applies the same regional `-12`/`-8` offsets before drawing.
Because the donor table itself is byte-identical, two authored ETC adaptations
store the equivalent effective X=`368`/`452` values in NA2. A guarded
task-owned Slot 2 render matches the NUN5 Collection-root footer.

Collection Music uses the different HOME action helper `FUN_006b44b0` and the
nominal table at ETC `0x2E7E0`. NUN5 homolog `FUN_006c7250` applies
state-specific localized geometry: Cross `-12`, width-derived Play `-24`, and
Triangle `-8`. Its GP-relative regional globals and language accessors are not
ABI-compatible with NA2, so `UI-ELF-008` ports the arithmetic through one
four-instruction tail-call wrapper in load-preserved MWO3 header padding,
redirects the helper's three compositor calls, and changes only the Play
label's local X offset from `-35` to `-59`. A guarded task-owned Slot 3 render
matches the NUN5 Play/Back anchors. The earlier Slot 2 failure of this helper
remains useful evidence that the two Collection footer families are distinct,
not evidence against the helper's actual HOME consumers.

Exact mappings, reconstruction, side effects, and runtime evidence are
preserved in `docs/knowledge/localization/ui/options.md`,
`docs/knowledge/localization/ui/collection.md`, and
`docs/knowledge/localization/ui/battle.md`.

### UI-ELF-009: shared Controls and Music footer anchors

The complete NUN5 common-UI import supplies the localized Select footer
artwork, but both NA2 Options renderers place the paired Select icon and legend
at X=`230`. Their NUN5 homologs place both calls at X=`200`:

- NA2 Controls `FUN_00388b90` / NUN5 `FUN_0039a450`;
- NA2 Music Options `FUN_0038a1f0` / NUN5 `FUN_0039bb00`.

`UI-ELF-009` copies all four exact NUN5 `lui v0,0x4348` anchor instructions
over the corresponding guarded NA2 `lui v0,0x4366` instructions. The broad
correction keeps each icon and legend paired, applies consistently to both
screens, and leaves vertical placement and internal spacing unchanged. Both
renderers also load nominal OK/Back X=`400`/`470` directly while their NUN5
homologs apply the same regional `-12`/`-8` offsets. Two authored
same-register constants in each renderer reproduce the effective donor anchors
X=`388`/`462` without copying ABI-incompatible GP-relative loads. Guarded
task-owned Music and Control Settings states reproduce both complete NUN5
footer placements.
The complete homolog mappings, reconstruction, runtime evidence, and rejected
wrong-table probe are preserved in
`docs/knowledge/localization/ui/options.md`.

Inspect all 27 UI companion patches together:

```powershell
python -m na2_patcher.modules.binary_patcher.engine validate `
  --package na2_patcher/features/localization/binary_patcher `
  --root na2=@source_na2 `
  --root nun5=@source_nun5

python -m na2_patcher.modules.binary_patcher.engine plan `
  --package na2_patcher/features/localization/binary_patcher `
  --root na2=@source_na2 `
  --root nun5=@source_nun5 `
  --patch UI-BTL-001 `
  --patch UI-BTL-002 `
  --patch UI-BTL-003 `
  --patch UI-BTL-004 `
  --patch UI-BTL-005 `
  --patch UI-BTL-006 `
  --patch UI-BTL-007 `
  --patch UI-BTL-008 `
  --patch UI-BTL-009 `
  --patch UI-BTL-010 `
  --patch UI-BTL-011 `
  --patch UI-BTL-012 `
  --patch UI-BTL-013 `
  --patch UI-BTL-014 `
  --patch UI-BTL-015 `
  --patch UI-BTL-016 `
  --patch UI-ETC-001 `
  --patch UI-ETC-002 `
  --patch UI-ELF-001 `
  --patch UI-ELF-002 `
  --patch UI-ELF-003 `
  --patch UI-ELF-004 `
  --patch UI-ELF-005 `
  --patch UI-ELF-006 `
  --patch UI-ELF-007 `
  --patch UI-ELF-008 `
  --patch UI-ELF-009
```

## Compact external strings

The integrated `string_patcher` externalizes only complete replacements whose
final encoded text exceeds the original slot and whose mapping declares
validated pointer references. Placement is recomputed at build time; the
canonical translation table contains no placement markers. T30's complete
`Ultimate` text is externalized through `NA2_BTL@0x209CB4`. The pipeline never
reads or patches `ADV.bin`.

The shared payload builder deterministically generates exactly one ISO
insertion:

- `PRG/228.BIN`: the resident MWO3 code/data image containing a return-only
  entry stub and the 30 distinct external string fragments selected by the
  current translation.

The translation importer resolves and validates the canonical mapping data and
pointer inventory once.
The consuming string patcher then:

1. encodes every final replacement and assigns fit-derived overflowing
   mappings to external storage while compiling every fitting mapping inline;
2. contributes the selected complete replacements as named payload fragments;
3. declares symbolic redirects for every inventoried use of those slots.

The payload builder packs all feature contributions, assigns addresses, emits
`228.BIN`, and owns the guarded ELF loader hook, load destination, and exact
linked memory reservation. The composer resolves string symbols before the
resulting fixed-size writes pass through `binary_patcher`.

All binary output is generated in memory by the importer, string patcher,
payload builder, composer, and binary patcher. No patched ELF, BIN, or ISO
payload is stored in Git.

### Canonical inputs

- `translation_importer/mappings.tsv` contains guarded source locations and
  text, executable official donor translations, optional user prefixes and
  overrides, and every optional pointer reference.
  Three continuation rows deliberately reuse their containing full-message
  pointer.
The retained task-local diagnostic inventory is outside this feature and is
supplied explicitly only to mapping-ID worker builds. Only `mappings.tsv` is
covered by the translation importer's contribution to the Localization
feature hash.
Payload-builder configuration is executable infrastructure rather than feature
data; engine code and documentation are excluded from the feature pin.

### Current linked layout

| Item | Value |
| --- | ---: |
| `228.BIN` load base | `0x008F3D00` |
| MOD entry | `0x008F3D40` |
| String pool start | `0x008F3E00` |
| `228.BIN` generated bytes | `0x700` |
| `228.BIN` SHA-256 | `02EB721CEBAA169B2FD7AEA9F8EFF60594EAE09F6347A3BF79E4FFE420237988` |
| Final resident boundary | `0x008F4400` |

Strings are resolved through the importer, encoded as CP1252 plus a terminator,
deduplicated by exact encoded bytes, contributed by symbol, and currently link
in stable mapping-ID order at four-byte-aligned offsets. Font functions are
contributed through `resident_patcher` and sort before the string pool. No
feature owns either set of offsets. The selected external strings contain 1,475
encoded bytes; T364 and T117 deliberately share one identical symbol.
Structured save-progress families preserve their original consecutive
NUL-terminated slots plus an empty terminator, preventing traversal into the
next payload message. The generated payload has no constructor range; the
infrastructure bootstrap loads it once and calls its documented return-only
entry.

### Safety properties

- exact mapping/ref counts and fit-derived placement coverage;
- fixed-length guarded edits only;
- deterministic fragment linking, symbol resolution, payloads, and pointer order;
- rejection of overlaps, stale original bytes, unexpected mappings, malformed
  references, changed source binaries, or memory-envelope overflow;
- no `FLIST` edit unless runtime testing later proves direct `cdrom0:\\PRG\\...`
  lookup insufficient.

The Project-owned ISO compositor is responsible for inserting the one path,
preserving ISO size, and verifying directory records, extents, payload hashes,
and the complete final tree.

## Native NUN5-derived font

This package starts from hash-verified clean NA2 and official NUN5 inputs. It
does not use `font_m01`, v22/v23, the rejected GF4C palette swap, or a whole
GF4 replacement as an implementation parent. The accepted build changes
`DATA/GF4.BIN` and `SLPS_258.37` without changing either file's size;
`DATA/GF4C.BIN` remains byte-identical to clean NA2.

Three Font components remain enabled by default when Localization is enabled:
the accepted native glyph component, the independent Character Select modal
alignment, and the call-local Save/Load ASCII numeric formatter. Three
autofit/layout components are retained in place but default-disabled for a
user-directed stage-by-stage reimplementation:

- `font_nun5_glyphs` installs native 14x20 NUN5 raster geometry and metrics
  for same-semantic English cells. Unsupported printable punctuation is
  reconstructed from clean NA2, preserving 95/95 printable-ASCII coverage.
  The shortened 123-cell secondary atlas is locally guarded. Its metric rows
  are packed into the value words of empty primary-map slots and decoded only
  by the secondary draw and measurement hooks. The normal glyph emitter keeps
  descriptor width on the primary/fullwidth path and uses descriptor height
  only for the secondary quad, restoring its intended 24x28 presentation
  without widening it.
- Retained, default-disabled `font_renderer_metrics` ports the shared NUN5 secondary tracking, ordinary
  ASCII-space, newline-advance, and logical-width behavior. Boxed callers use
  the same corrected denominator instead of reconstructing it independently.
  Pure printable ASCII uses the linked 95-entry proportional-width table;
  retained NUN5 runtime probes confirm Command Chart denominators `142`, `115`,
  and `440`.
- Retained, default-disabled `font_controls_auto_fit` reproduces NUN5's shrink-only Controls behavior.
  It keeps `Linked Attack` full width, fits the official
  `Ultimate Jutsu Prep` label, leaves `OFF` on the ordinary renderer, and
  shifts only the left and right labels for visible-ink centering. Its
  128-unit wrapper delegates measurement to `font_renderer_metrics`, and its
  local scale is restored immediately after every fitted call.
- `font_modal_alignment` loads independently measured X positions for the
  five character-select `Back to Game Mode Screen` rows while retaining the
  accepted local Y behavior. Its selected-path compensation prevents the
  shadow draw from shifting visible ink.
- `font_save_load_ascii_digits` replaces only the six fullwidth numeric-format
  calls in the Save/Load row renderer with NA2's existing ASCII `sprintf` and
  changes its two time separators to ASCII colon. It preserves NA2's current
  date order, timer math, and all unrelated numeric callers while matching
  NUN5's two-digit hour display and 99-hour cap.
- `font_battle_settings_ascii_digits` replaces only the ordinary numeric branch
  of the Battle Settings Time row with NA2's existing ASCII `sprintf`. Its
  adjacent exact guard preserves the separate value-100 infinity path and
  leaves the other five rows and every unrelated numeric caller unchanged.
- Retained, default-disabled `font_layout_wrappers` ports shared selected/unselected confirmation-choice
  placement, the 216-unit Practice pause-list fit and Y origin, Practice and
  Collection confirmation-body alignment, and the character-return body's
  centered 368-unit box. It also distinguishes the Command Chart 288-unit and
  Practice-title 352-unit containers while sharing their shrink-only fit
  implementation. Exact caller guards leave unrelated shared-wrapper users
  untouched.

Executable metric, fit, scale, and layout helpers are nine relocatable code
fragments plus one linked read-only metric table in `PRG/228.BIN`. Their eight
guarded ELF hook sites are resolved only after final payload placement. The
binary-patcher module retains only static renderer data, tracking, and local
alignment edits; it no longer installs executable code into ELF zero padding.
The shared UI wrapper keeps transient coordinates and saved renderer fields in
its own stack frame rather than the former global scratch record.

An independent `localization.font.v2.*` foundation is also retained
default-disabled and does not target any symbol above. Its separate generated
resident asset contains the accepted 95-entry width table, exact
printable-ASCII measurement with explicit `<br>`/newline recognition,
shrink-only scale preparation, horizontal/vertical box positioning, and five
renderer hooks guarded by one zero-initialized active-session pointer. Every
null-session branch restores the temporary `v0`/`v1` use and executes the
displaced NA2 instructions before resuming, so selecting the core alone cannot
alter a screen. Its generic call adapter prepares one caller-owned 104-byte
session, publishes it only around one native callback, and restores the prior
session pointer, renderer tracking, horizontal scale and callback result
through one cleanup path. No caller-family call site is redirected yet.

The retained auto-fit and layout components require `font_nun5_glyphs` because
their positions and fit decisions are tuned to its metrics. They otherwise
remain independent. Their fragments, relocations, hook declarations, generated
assets, and historical validation evidence remain canonical; setting
`default_enabled=0` removes them from normal composition without deleting the
implementation. With every resident Font row disabled, the resident engine
validates the retained package but contributes no Font fragments or hooks to
the shared payload.
The rejected shared `font_vertical_quad_height` component was removed from
executable inputs because it stretched both axes to 28x28. Its exact negative
result remains in `docs/knowledge/localization/font/README.md` and Git history;
the accepted secondary-only height helper is part of `font_nun5_glyphs`.

Matched Controls, Practice, Save/Load, and character-modal captures established
the historical rendering behavior before its resident relocation. The final
guarded Controls capture retained the accepted horizontal metrics, spacing,
bearings, and shrink-only fit while reducing the median height and center-Y
deltas against NUN5 to zero. The user accepted the font itself as almost
pixel-for-pixel. Fullwidth Shift-JIS Save/Load digits use a different glyph path
and were not a halfwidth-Latin parity target; the independent Save/Load
formatter patch now emits those six fields as ASCII instead. The user later
rejected the combined autofit/layout selection as unstable; only the font
itself, the independent Character Select modal alignment, and this call-local
formatter remain enabled while layout is rebuilt sequentially.

`scripts/research/localization/generate_font_assets.py` deterministically
regenerates and verifies the four native glyph/metric/decoder blobs from
configured `@source_na2/` and `@source_nun5/` inputs.
`scripts/research/localization/generate_font_renderer.py` deterministically
regenerates the resident renderer blob plus its fragment and relocation tables.
`scripts/research/localization/generate_save_load_ascii_digits.py`
deterministically generates and verifies the six Save/Load call replacements
and their local punctuation edit.
`scripts/research/localization/generate_battle_settings_ascii_digits.py`
deterministically generates and verifies the single Battle Settings Time call
replacement plus the untouched adjacent infinity branch.
Exact static and symbolic hooks, guards, replacement templates, and reasons are
recorded in the two module-owned `edits.tsv` files; confirmed evidence and
negative results are recorded in
`docs/knowledge/localization/font/README.md`.

## Regional menu input

The Localization feature owns these declarative `binary_patcher` patches for
the accepted menu, overlay, setup, stage, pause, result-tally, and audio input behavior.
`binary_patcher/` contains the guarded targets, default-enabled patches, edits,
evidence, and runtime classifications.
